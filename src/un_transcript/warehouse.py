"""Production transcript ledger; raw bytes and historical revisions are immutable.

This database is deliberately separate from the frozen research ledgers. A source
revision binds the original response, its normalized segments and the meeting
metadata. Predictions never replace source text or claim human verification.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import tempfile
from datetime import date, datetime
from contextlib import contextmanager
from urllib.parse import urlparse


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else canonical(value).encode("utf-8")).hexdigest()


def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError("An ISO timestamp with timezone is required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include timezone")
    return parsed


def _https(value):
    p = urlparse(value)
    if p.scheme != "https" or not p.hostname or p.username or p.password:
        raise ValueError("A credential-free HTTPS source URL is required")
    return value


class Warehouse:
    """One SQLite writer, durable source files and foreign-key checked evidence."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.raw_directory = self.path.parent / "raw"
        self.raw_directory.mkdir(exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=30)
        self.db.row_factory = sqlite3.Row
        self._transaction_depth = 0
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=30000")
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            self.db.close()
            raise ValueError("Unsupported warehouse schema version")
        if version == 0:
            # Never adopt a research or unrelated database merely because its
            # user_version is zero.
            if self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
                self.db.close()
                raise ValueError("Refusing to initialize a nonempty unrelated database")
            self.db.executescript("""
                BEGIN;
                CREATE TABLE warehouse_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                INSERT INTO warehouse_meta VALUES('schema','un.transcript-warehouse.v1');
                CREATE TABLE meetings(
                    meeting_id TEXT PRIMARY KEY,
                    current_revision TEXT REFERENCES source_revisions(revision_id));
                CREATE TABLE source_revisions(
                    revision_id TEXT PRIMARY KEY, meeting_id TEXT NOT NULL REFERENCES meetings(meeting_id),
                    source_id TEXT NOT NULL, raw_sha256 TEXT NOT NULL, raw_path TEXT NOT NULL,
                    byte_count INTEGER NOT NULL CHECK(byte_count>=0), retrieved_at TEXT NOT NULL,
                    date TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL,
                    source_url TEXT NOT NULL, json_url TEXT NOT NULL, headers_json TEXT NOT NULL,
                    normalization_version TEXT NOT NULL);
                CREATE TABLE actors(
                    actor_id TEXT PRIMARY KEY, speaker TEXT NOT NULL, country TEXT NOT NULL,
                    capacity TEXT NOT NULL CHECK(capacity IN ('unknown','national','collective')),
                    group_name TEXT NOT NULL);
                CREATE TABLE segments(
                    revision_id TEXT NOT NULL REFERENCES source_revisions(revision_id),
                    segment_id TEXT NOT NULL, actor_id TEXT NOT NULL REFERENCES actors(actor_id),
                    ordinal INTEGER NOT NULL, text TEXT NOT NULL, text_sha256 TEXT NOT NULL,
                    language TEXT NOT NULL, json_pointer TEXT NOT NULL, start_offset INTEGER,
                    end_offset INTEGER, PRIMARY KEY(revision_id,segment_id), UNIQUE(revision_id,ordinal));
                CREATE TABLE collection_runs(
                    run_id TEXT PRIMARY KEY, config_json TEXT NOT NULL, started_at TEXT NOT NULL,
                    finished_at TEXT, status TEXT NOT NULL);
                CREATE TABLE coverage(
                    run_id TEXT NOT NULL REFERENCES collection_runs(run_id), meeting_id TEXT NOT NULL,
                    status TEXT NOT NULL, detail TEXT NOT NULL,
                    PRIMARY KEY(run_id,meeting_id));
                CREATE TABLE issues(
                    issue_id TEXT NOT NULL, version TEXT NOT NULL, label TEXT NOT NULL,
                    definition TEXT NOT NULL, PRIMARY KEY(issue_id,version));
                CREATE TABLE predictions(
                    prediction_id TEXT PRIMARY KEY, revision_id TEXT NOT NULL,
                    segment_id TEXT NOT NULL, issue_id TEXT NOT NULL, issue_version TEXT NOT NULL,
                    model_version TEXT NOT NULL, stance TEXT, status TEXT NOT NULL,
                    confidence REAL, probabilities_json TEXT NOT NULL, created_at TEXT NOT NULL,
                    interpretability_status TEXT NOT NULL, payload_json TEXT NOT NULL,
                    FOREIGN KEY(revision_id,segment_id) REFERENCES segments(revision_id,segment_id),
                    FOREIGN KEY(issue_id,issue_version) REFERENCES issues(issue_id,version));
                CREATE TABLE evidence(
                    prediction_id TEXT NOT NULL REFERENCES predictions(prediction_id),
                    start_offset INTEGER NOT NULL, end_offset INTEGER NOT NULL,
                    quote TEXT NOT NULL, PRIMARY KEY(prediction_id,start_offset,end_offset));
                CREATE TABLE inventory_receipts(
                    receipt_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES collection_runs(run_id),
                    date TEXT NOT NULL, page INTEGER NOT NULL, source_url TEXT NOT NULL,
                    raw_sha256 TEXT NOT NULL, raw_path TEXT NOT NULL, byte_count INTEGER NOT NULL,
                    retrieved_at TEXT NOT NULL, headers_json TEXT NOT NULL);
                CREATE TABLE source_evidence(
                    evidence_id TEXT PRIMARY KEY, revision_id TEXT NOT NULL, segment_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY(revision_id,segment_id) REFERENCES segments(revision_id,segment_id));
                CREATE TABLE issue_candidates(
                    candidate_id TEXT PRIMARY KEY, revision_id TEXT NOT NULL, segment_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY(revision_id,segment_id) REFERENCES segments(revision_id,segment_id));
                CREATE TABLE analytical_results(
                    result_id TEXT PRIMARY KEY, run_id TEXT REFERENCES collection_runs(run_id),
                    created_at TEXT NOT NULL, payload_json TEXT NOT NULL);
                CREATE TABLE model_releases(
                    model_version TEXT PRIMARY KEY, acceptance_sha256 TEXT NOT NULL,
                    receipt_json TEXT NOT NULL);
                CREATE INDEX segments_actor ON segments(actor_id);
                CREATE INDEX predictions_source ON predictions(revision_id,segment_id);
                PRAGMA user_version=1;
                COMMIT;
            """)
        elif self.db.execute("SELECT value FROM warehouse_meta WHERE key='schema'").fetchone()[0] != "un.transcript-warehouse.v1":
            self.db.close()
            raise ValueError("Not a production transcript warehouse")

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        if self._transaction_depth:
            yield
        else:
            self._transaction_depth += 1
            try:
                with self.db:
                    yield
            finally:
                self._transaction_depth -= 1

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _store_raw(self, raw):
        sha = digest(raw)
        target = self.raw_directory / (sha + ".json")
        if target.exists():
            if target.read_bytes() != raw:
                raise ValueError("Stored raw source digest mismatch")
        else:
            fd, temporary = tempfile.mkstemp(prefix=".raw-", dir=self.raw_directory)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, target)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        return sha, target.relative_to(self.path.parent).as_posix()

    def ingest(self, meeting: dict, raw: bytes, segments: list[dict], retrieved_at: str, headers: dict | None = None):
        """Commit a complete revision; errors never advance the current pointer.

        Caller must parse all segments before calling. Supplied segment IDs are
        revision-local, not assertions of stable speeches across revised sources.
        """
        if not isinstance(raw, bytes) or not isinstance(segments, list):
            raise ValueError("Original bytes and a complete segment list are required")
        _timestamp(retrieved_at)
        meta = {k: meeting.get(k) for k in ("meeting_id", "date", "title", "body", "source_url", "json_url")}
        if any(not isinstance(v, str) or not v for v in meta.values()):
            raise ValueError("Complete meeting identity and metadata are required")
        if date.fromisoformat(meta["date"]).isoformat() != meta["date"]:
            raise ValueError("Meeting date must be ISO format")
        _https(meta["source_url"]); _https(meta["json_url"])
        normalized = []
        seen = set()
        for ordinal, item in enumerate(segments):
            text = item.get("text")
            pointer = item.get("json_pointer", "/transcript/data/" + str(ordinal))
            language = item.get("language", "unknown")
            capacity = item.get("capacity", "unknown")
            if not isinstance(text, str) or not isinstance(pointer, str) or not pointer.startswith("/"):
                raise ValueError("Each segment needs original text and a JSON pointer")
            if not isinstance(language, str) or not language or capacity not in ("unknown", "national", "collective"):
                raise ValueError("Invalid segment language or capacity")
            actor = {k: item.get(k) or "" for k in ("speaker", "country", "group_name")}
            if any(not isinstance(v, str) for v in actor.values()):
                raise ValueError("Actor metadata must be text")
            actor["capacity"] = capacity
            if capacity == "national" and not actor["country"]:
                raise ValueError("National capacity requires a recorded country")
            if capacity == "collective" and not actor["group_name"]:
                raise ValueError("Collective capacity requires a recorded group")
            start, end = item.get("start"), item.get("end")
            if (start is None) != (end is None) or start is not None and (type(start) is not int or type(end) is not int or start < 0 or end < start):
                raise ValueError("Segment offsets must be a nonnegative half-open pair")
            segment_id = item.get("segment_id") or "segment:" + digest([meta["meeting_id"], pointer])
            if not isinstance(segment_id, str) or segment_id in seen:
                raise ValueError("Duplicate or invalid segment ID")
            seen.add(segment_id)
            normalized.append(dict(segment_id=segment_id, ordinal=ordinal, text=text,
                language=language, json_pointer=pointer, start=start, end=end, **actor))
        raw_sha, raw_path = self._store_raw(raw)
        source_id = "source:" + digest([meta["meeting_id"], meta["json_url"]])
        revision = "revision:" + digest([meta, raw_sha, normalized, "un.normalized-segments.v1"])
        # Only response identity/cache headers are retained, never authorization
        # or cookies supplied by a network library.
        safe_headers = {str(k).lower(): str(v) for k, v in (headers or {}).items()
                        if str(k).lower() in ("etag", "last-modified", "content-type")}
        with self.transaction():
            current = self.db.execute("SELECT r.revision_id,r.retrieved_at FROM meetings m JOIN source_revisions r ON r.revision_id=m.current_revision WHERE m.meeting_id=?", (meta["meeting_id"],)).fetchone()
            exists = self.db.execute("SELECT 1 FROM source_revisions WHERE revision_id=?", (revision,)).fetchone()
            if current and current["revision_id"] == revision:
                return revision
            if exists:
                raise ValueError("Historical revision replay cannot replace the current source")
            if current and _timestamp(retrieved_at) < _timestamp(current["retrieved_at"]):
                raise ValueError("Older retrieval cannot replace the current source")
            self.db.execute("INSERT OR IGNORE INTO meetings(meeting_id) VALUES(?)", (meta["meeting_id"],))
            self.db.execute("INSERT INTO source_revisions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (revision,meta["meeting_id"],source_id,raw_sha,raw_path,len(raw),retrieved_at,
                 meta["date"],meta["title"],meta["body"],meta["source_url"],meta["json_url"],canonical(safe_headers),"un.normalized-segments.v1"))
            for item in normalized:
                actor = {k: item[k] for k in ("speaker", "country", "capacity", "group_name")}
                actor_id = "actor:" + digest(actor)
                self.db.execute("INSERT OR IGNORE INTO actors VALUES(?,?,?,?,?)", (actor_id,actor["speaker"],actor["country"],actor["capacity"],actor["group_name"]))
                self.db.execute("INSERT INTO segments VALUES(?,?,?,?,?,?,?,?,?,?)", (revision,item["segment_id"],actor_id,item["ordinal"],item["text"],digest(item["text"].encode()),item["language"],item["json_pointer"],item["start"],item["end"]))
            self.db.execute("UPDATE meetings SET current_revision=? WHERE meeting_id=?", (revision,meta["meeting_id"]))
        return revision

    def start_run(self, run_id, config: dict, started_at):
        _timestamp(started_at)
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("Run ID required")
        with self.transaction():
            self.db.execute("INSERT INTO collection_runs VALUES(?,?,?,NULL,'running')", (run_id,canonical(config),started_at))

    def finish_run(self, run_id, status, finished_at):
        _timestamp(finished_at)
        if status not in ("complete", "completed", "partial", "failed", "cancelled", "success"):
            raise ValueError("Unknown final run status")
        with self.transaction():
            row = self.db.execute("SELECT started_at,status FROM collection_runs WHERE run_id=?", (run_id,)).fetchone()
            if not row or row["status"] != "running" or _timestamp(finished_at) < _timestamp(row["started_at"]):
                raise ValueError("Only a running run can finish after its start")
            self.db.execute("UPDATE collection_runs SET status=?,finished_at=? WHERE run_id=?", (status,finished_at,run_id))

    def record_coverage(self, run_id, meeting_id, status, detail=""):
        if not isinstance(status, str) or not status or not isinstance(meeting_id, str) or not meeting_id:
            raise ValueError("Coverage requires meeting identity and status")
        with self.transaction():
            self.db.execute("INSERT INTO coverage VALUES(?,?,?,?) ON CONFLICT(run_id,meeting_id) DO UPDATE SET status=excluded.status,detail=excluded.detail", (run_id,meeting_id,status,detail))

    def current_segments(self):
        return [dict(row) for row in self.db.execute("""
            SELECT s.*,r.meeting_id,r.date,r.title,r.body,r.source_url,r.raw_sha256,r.raw_sha256 AS source_hash,
                   a.speaker,a.country,a.capacity,a.group_name
            FROM segments s JOIN source_revisions r USING(revision_id)
            JOIN meetings m ON m.current_revision=s.revision_id
            JOIN actors a USING(actor_id) ORDER BY r.date,r.meeting_id,s.ordinal
        """)]

    def upsert_issue(self, issue):
        values = tuple(issue.get(k) for k in ("issue_id", "version", "label", "definition"))
        if any(not isinstance(v, str) or not v for v in values):
            raise ValueError("Versioned issue ID, label and definition required")
        with self.transaction():
            old = self.db.execute("SELECT * FROM issues WHERE issue_id=? AND version=?", values[:2]).fetchone()
            if old and tuple(old) != values:
                raise ValueError("Issue definitions are immutable; increment version")
            self.db.execute("INSERT OR IGNORE INTO issues VALUES(?,?,?,?)", values)

    def add_prediction(self, item):
        """Persist model output privately with exact source evidence; never certify it."""
        row = dict(item)
        revision = row.get("revision_id", row.get("source_revision"))
        segment = self.db.execute("SELECT text FROM segments WHERE revision_id=? AND segment_id=?", (revision,row.get("segment_id"))).fetchone()
        if not segment:
            raise ValueError("Prediction source segment does not exist")
        if not self.db.execute("SELECT 1 FROM meetings WHERE current_revision=?", (revision,)).fetchone():
            raise ValueError("Cannot add a prediction for a superseded source")
        stances = ("strongly_oppose", "oppose", "neutral", "support", "strongly_support")
        status = row.get("status", "unvalidated")
        if status not in ("unvalidated", "abstained", "validated") or row.get("stance") not in (*stances, None):
            raise ValueError("Invalid stance or prediction status")
        if status == "abstained" and row.get("stance") is not None:
            raise ValueError("Abstention is not a stance")
        if status != "abstained" and row.get("stance") is None:
            raise ValueError("A classified prediction requires a stance")
        confidence = row.get("confidence")
        if confidence is not None and (isinstance(confidence,bool) or not isinstance(confidence,(int,float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1):
            raise ValueError("Confidence must be finite and between zero and one")
        probabilities = row.get("probabilities") or {}
        if isinstance(probabilities,list):
            if len(probabilities) != len(stances):
                raise ValueError("Five stance probabilities required")
            probabilities = dict(zip(stances,probabilities))
        if not isinstance(probabilities,dict):
            raise ValueError("Probabilities must be a mapping or five-class list")
        if probabilities and (set(probabilities) != set(stances) or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0 <= v <= 1 for v in probabilities.values()) or abs(sum(probabilities.values())-1)>1e-5):
            raise ValueError("Probabilities must cover all five stances and sum to one")
        evidence = row.get("evidence", [])
        if status != "abstained" and not evidence:
            raise ValueError("A stance requires source evidence")
        checked = []
        for span in evidence:
            start, end = span.get("start"), span.get("end")
            if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(segment["text"]) or segment["text"][start:end] != span.get("quote"):
                raise ValueError("Evidence offsets must reproduce exact source wording")
            checked.append((start,end,span["quote"]))
        created_at = row.get("created_at")
        _timestamp(created_at)
        for field in ("issue_id", "issue_version", "model_version", "segment_id"):
            if not isinstance(row.get(field),str) or not row[field]:
                raise ValueError("Missing prediction identity: " + field)
        interpretation = row.get("interpretability_status","clear" if row.get("stance") else "withheld")
        payload = [revision,row["segment_id"],row["issue_id"],row["issue_version"],row["model_version"],row.get("stance"),status,confidence,probabilities,sorted(checked),interpretation]
        pid = "prediction:" + digest(payload)
        with self.transaction():
            self.db.execute("INSERT OR IGNORE INTO predictions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (pid,revision,row["segment_id"],row["issue_id"],row["issue_version"],row["model_version"],row.get("stance"),status,confidence,canonical(probabilities),created_at,interpretation,canonical(row)))
            for start,end,quote in checked:
                self.db.execute("INSERT OR IGNORE INTO evidence VALUES(?,?,?,?)", (pid,start,end,quote))
        return pid

    def record_inventory(self, run_id, entry):
        raw = entry.get("raw")
        if not isinstance(raw,bytes):
            raise ValueError("Inventory must retain exact response bytes")
        retrieved = entry.get("retrieved_at")
        _timestamp(retrieved)
        day = entry.get("date",entry.get("day"))
        if date.fromisoformat(day).isoformat() != day:
            raise ValueError("Invalid inventory date")
        page = entry.get("page",1)
        if type(page) is not int or page < 1:
            raise ValueError("Invalid inventory page")
        url = _https(entry.get("source_url",entry.get("url","")))
        sha, path = self._store_raw(raw)
        declared = entry.get("sha256",entry.get("raw_sha256"))
        if declared is not None and declared != sha:
            raise ValueError("Inventory digest mismatch")
        headers = {str(k).lower():str(v) for k,v in (entry.get("headers") or {}).items()
                   if str(k).lower() in ("etag","last-modified","content-type")}
        rid = "inventory:"+digest([run_id,day,page,url,sha])
        with self.transaction():
            self.db.execute("INSERT OR IGNORE INTO inventory_receipts VALUES(?,?,?,?,?,?,?,?,?,?)",
                (rid,run_id,day,page,url,sha,path,len(raw),retrieved,canonical(headers)))
        return rid

    def record_analysis(self, analysis, created_at=None, run_id=None):
        """Atomically store reproducible private analysis and acceptance bindings.

        The model runtime verifies artifacts and owner release before returning
        an accepted receipt. Merely storing predictions cannot publish them.
        """
        created_at = created_at or analysis.get("generated_at")
        _timestamp(created_at)
        with self.transaction():
            for issue in analysis.get("issues",[]):
                self.upsert_issue(issue)
            model = analysis.get("model_status",{})
            if model.get("accepted") is True:
                version = model.get("model_version",model.get("model_id"))
                sha = model.get("acceptance_sha256")
                if not isinstance(version,str) or not version or model.get("release_approved") is not True or not isinstance(sha,str) or not re_full_sha(sha):
                    raise ValueError("Accepted model requires hash-bound release approval")
                old = self.db.execute("SELECT acceptance_sha256 FROM model_releases WHERE model_version=?",(version,)).fetchone()
                if old and old[0] != sha:
                    raise ValueError("Model release is immutable; use a new version")
                self.db.execute("INSERT OR IGNORE INTO model_releases VALUES(?,?,?)",(version,sha,canonical(model)))
                self.db.execute("INSERT INTO warehouse_meta VALUES('active_model',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(version,))
            else:
                # Historical accepted outputs remain inspectable privately, but
                # a missing/invalid current model never silently republishes them.
                self.db.execute("INSERT INTO warehouse_meta VALUES('active_model','') ON CONFLICT(key) DO UPDATE SET value='' ")
            for table,id_key,items in (("source_evidence","evidence_id",analysis.get("evidence",[])),("issue_candidates","candidate_id",analysis.get("issue_candidates",[]))):
                for item in items:
                    revision = item.get("revision_id",item.get("source_id"))
                    segment_id = item.get("segment_id")
                    source = self.db.execute("SELECT s.text FROM segments s JOIN meetings m ON m.current_revision=s.revision_id WHERE s.revision_id=? AND s.segment_id=?",(revision,segment_id)).fetchone()
                    if not source:
                        raise ValueError("Analysis must bind a current source segment")
                    for span in item.get("spans",[]):
                        a,b = span.get("start"),span.get("end")
                        if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(source[0]):
                            raise ValueError("Analysis evidence span is outside its segment")
                    identifier = item.get(id_key) or id_key+":"+digest(item)
                    old = self.db.execute("SELECT payload_json FROM "+table+" WHERE "+id_key+"=?",(identifier,)).fetchone()
                    if old and old[0] != canonical(item):
                        raise ValueError("Analysis identity collision")
                    self.db.execute("INSERT OR IGNORE INTO "+table+" VALUES(?,?,?,?)",(identifier,revision,segment_id,canonical(item)))
            for prediction in analysis.get("predictions",[]):
                self.add_prediction({**prediction,"created_at":prediction.get("created_at",created_at)})
            for result in analysis.get("analytical_results",[]):
                rid = "result:"+digest([run_id,result])
                self.db.execute("INSERT OR IGNORE INTO analytical_results VALUES(?,?,?,?)",(rid,run_id,created_at,canonical(result)))
        return {"predictions":len(analysis.get("predictions",[])),"issue_candidates":len(analysis.get("issue_candidates",[])),"analytical_results":len(analysis.get("analytical_results",[]))}


def re_full_sha(value):
    return len(value)==64 and all(c in "0123456789abcdef" for c in value)
