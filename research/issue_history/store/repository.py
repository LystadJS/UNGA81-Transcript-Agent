"""SQLite evidence ledger and atomic, source-free browser bundle exporter.

The ledger is a maintainer component. Browsers consume its read-only exports.
Source revisions are immutable; corrections invalidate dependent artifacts.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import re
from contextlib import contextmanager


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def stable_id(kind, *parts):
    return kind + ":" + hashlib.sha256(canonical_bytes(parts)).hexdigest()


def _date(value):
    if not isinstance(value, str) or dt.date.fromisoformat(value).isoformat() != value:
        raise ValueError("Expected ISO calendar date")
    return value


class IssueStore:
    SCHEMA_VERSION = 1

    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self._write_depth = 0
        self.db.execute("PRAGMA foreign_keys=ON")
        self.migrate()

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        """Batch idempotent writes atomically without per-record disk commits."""
        if self._write_depth:
            self._write_depth += 1
            try:
                yield
            finally:
                self._write_depth -= 1
        else:
            self._write_depth = 1
            try:
                with self.db:
                    yield
            finally:
                self._write_depth = 0

    def backup(self, destination):
        """Create a consistent rollback copy before a future schema upgrade."""
        target = sqlite3.connect(destination)
        try:
            self.db.backup(target)
        finally:
            target.close()

    def migrate(self):
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version > self.SCHEMA_VERSION:
            raise ValueError("Database schema is newer than this application")
        if version == 0:
            self.db.executescript("""
            BEGIN;
            CREATE TABLE sources(id TEXT PRIMARY KEY, revision TEXT NOT NULL);
            CREATE TABLE source_revisions(id TEXT NOT NULL, revision TEXT NOT NULL, payload TEXT NOT NULL,
                PRIMARY KEY(id,revision));
            CREATE TABLE evidence(id TEXT PRIMARY KEY, kind TEXT NOT NULL, source_id TEXT NOT NULL,
                source_revision TEXT NOT NULL, payload TEXT NOT NULL,
                FOREIGN KEY(source_id,source_revision) REFERENCES source_revisions(id,revision));
            CREATE TABLE artifacts(id TEXT PRIMARY KEY, kind TEXT NOT NULL, valid INTEGER NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE dependencies(artifact_id TEXT NOT NULL REFERENCES artifacts(id), dependency_id TEXT NOT NULL,
                PRIMARY KEY(artifact_id,dependency_id));
            CREATE TABLE memberships(country TEXT NOT NULL, body TEXT NOT NULL, starts TEXT NOT NULL,
                ends TEXT, eligible INTEGER NOT NULL, PRIMARY KEY(country,body,starts));
            PRAGMA user_version=1;
            COMMIT;
            """)

    def _invalidate(self, dependency_id):
        # Transitive invalidation also covers cached reports depending on models.
        pending, visited = [dependency_id], set()
        while pending:
            dep = pending.pop()
            if dep in visited:
                continue
            visited.add(dep)
            children = [r[0] for r in self.db.execute("SELECT artifact_id FROM dependencies WHERE dependency_id=?", (dep,))]
            for child in children:
                self.db.execute("UPDATE artifacts SET valid=0 WHERE id=?", (child,))
            pending.extend(children)

    def upsert_source(self, source):
        required = ("id", "published_date", "body", "family", "url", "content_hash", "access")
        if any(not source.get(k) for k in required):
            raise ValueError("Source identity, date, provenance and access are required")
        _date(source["published_date"])
        if "countries" in source and (not isinstance(source["countries"], list) or any(not isinstance(c, str) or not c.strip() for c in source["countries"])):
            raise ValueError("Recorded countries must be explicit nonempty identifiers")
        if source["access"] not in ("private", "reference_only", "public_approved"):
            raise ValueError("Unknown publication access")
        if len(source["content_hash"]) != 64 or any(c not in "0123456789abcdef" for c in source["content_hash"]):
            raise ValueError("Expected SHA-256 content hash")
        payload = dict(source)
        payload.pop("revision", None)
        revision = hashlib.sha256(canonical_bytes(payload)).hexdigest()
        payload["revision"] = revision
        with self.transaction():
            previous = self.db.execute("SELECT revision FROM sources WHERE id=?", (source["id"],)).fetchone()
            self.db.execute("INSERT OR IGNORE INTO source_revisions VALUES(?,?,?)", (source["id"], revision, canonical_bytes(payload).decode()))
            if previous and previous[0] != revision:
                self._invalidate(source["id"])
                for row in self.db.execute("SELECT id FROM evidence WHERE source_id=?", (source["id"],)):
                    self._invalidate(row[0])
            self.db.execute("INSERT INTO sources VALUES(?,?) ON CONFLICT(id) DO UPDATE SET revision=excluded.revision", (source["id"], revision))
        return revision

    def _put_evidence(self, kind, item):
        for key in ("id", "source_id", "source_revision", "country", "date", "policy", "context"):
            if not item.get(key):
                raise ValueError("Missing evidence field: " + key)
        _date(item["date"])
        current = self.db.execute("SELECT revision FROM sources WHERE id=?", (item["source_id"],)).fetchone()
        if not current or current[0] != item["source_revision"]:
            raise ValueError("Evidence must reference the current source revision")
        if kind == "observation":
            if item.get("stance") not in ("support", "oppose", "qualified", "conflicting", "unknown"):
                raise ValueError("Invalid explicit position")
            if item.get("review_state") not in ("assistant_provisional", "owner_confirmed", "unreviewed"):
                raise ValueError("Explicit review state required")
            if item.get("attribution") not in ("national", "collective", "unclear"):
                raise ValueError("Explicit attribution required")
        elif item.get("vote") not in ("yes", "no", "abstain", "absent", "not_eligible", "unknown"):
            raise ValueError("Invalid vote category")
        if kind == "vote" and any(not item.get(k) for k in ("resolution", "resolution_version", "stage")):
            raise ValueError("Resolution version and voting stage required")
        if kind == "vote":
            if item["stage"] not in ("adopted_resolution", "adopted_decision", "draft_resolution", "amendment", "procedural"):
                raise ValueError("Invalid voting stage")
            if (item["stage"] == "adopted_decision") != item["resolution"].startswith("A/DEC/"):
                raise ValueError("Adopted decisions require an explicit A/DEC symbol")
            if item.get("eligible") is not None and type(item["eligible"]) is not bool:
                raise ValueError("Invalid voting eligibility")
            if item["vote"] == "not_eligible" and item.get("eligible") is not False:
                raise ValueError("Non-eligibility requires explicit evidence")
            if item["vote"] in ("yes", "no", "abstain", "absent") and item.get("eligible") is not True:
                raise ValueError("Vote requires explicit eligibility")
        encoded = canonical_bytes(item).decode()
        with self.transaction():
            old = self.db.execute("SELECT payload FROM evidence WHERE id=?", (item["id"],)).fetchone()
            if old and old[0] != encoded:
                self._invalidate(item["id"])
            self.db.execute("INSERT INTO evidence VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET kind=excluded.kind,source_id=excluded.source_id,source_revision=excluded.source_revision,payload=excluded.payload", (item["id"], kind, item["source_id"], item["source_revision"], encoded))

    def put_observation(self, item):
        self._put_evidence("observation", item)

    def put_vote(self, item):
        self._put_evidence("vote", item)

    def put_membership(self, country, body, starts, ends=None, eligible=True):
        _date(starts)
        if ends is not None and _date(ends) < starts:
            raise ValueError("Membership ends before it begins")
        with self.transaction():
            exact = self.db.execute("SELECT ends,eligible FROM memberships WHERE country=? AND body=? AND starts=?", (country, body, starts)).fetchone()
            if exact and exact[0] == ends and exact[1] == int(eligible):
                return
            overlap = self.db.execute("SELECT 1 FROM memberships WHERE country=? AND body=? AND starts<=? AND COALESCE(ends,'9999-12-31')>=?", (country, body, ends or "9999-12-31", starts)).fetchone()
            if overlap:
                raise ValueError("Overlapping eligibility intervals")
            self.db.execute("INSERT INTO memberships VALUES(?,?,?,?,?)", (country, body, starts, ends, int(eligible)))

    def put_artifact(self, kind, payload, dependencies):
        artifact_id = stable_id(kind, payload, sorted(set(dependencies)))
        valid = True
        for dep in dependencies:
            artifact = self.db.execute("SELECT valid FROM artifacts WHERE id=?", (dep,)).fetchone()
            evidence = self.db.execute("SELECT e.source_revision,s.revision FROM evidence e JOIN sources s ON e.source_id=s.id WHERE e.id=?", (dep,)).fetchone()
            source = self.db.execute("SELECT 1 FROM sources WHERE id=?", (dep,)).fetchone()
            if artifact:
                valid = valid and bool(artifact[0])
            elif evidence:
                valid = valid and evidence[0] == evidence[1]
            elif not source:
                raise ValueError("Artifact dependency does not exist: " + dep)
        with self.transaction():
            self.db.execute("INSERT OR IGNORE INTO artifacts VALUES(?,?,?,?)", (artifact_id, kind, int(valid), canonical_bytes(payload).decode()))
            for dep in set(dependencies):
                self.db.execute("INSERT OR IGNORE INTO dependencies VALUES(?,?)", (artifact_id, dep))
        return artifact_id

    def artifact_valid(self, artifact_id):
        row = self.db.execute("SELECT valid FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
        return bool(row and row[0])

    def put_policy_binding(self, binding, *, published_date, body):
        """Keep reviewed resolution relevance separate from country vote rows.

        Assistant provisional is preserved; this does not infer clause agreement
        or mutate unbound votes. Binding documents remain private by default.
        """
        from ..ingest.adapters import bind_resolution
        validated = bind_resolution(binding)
        if not binding.get("source_sha256") or not binding.get("source_anchor"):
            raise ValueError("Binding requires exact document hash and anchor")
        source_id = stable_id("un-resolution-document", validated["resolution_id"], validated["resolution_version"])
        with self.transaction():
            revision = self.upsert_source({"id":source_id,"published_date":published_date,"body":body,
                "family":"un_resolution_document","url":binding["source_url"],
                "content_hash":binding["source_sha256"],"access":"private"})
            return self.put_artifact("resolution_policy_binding", {**validated,"source_id":source_id,
                "source_revision":revision,"publication":"private_only"}, [source_id])

    def export_bundle(self, directory, snapshot_id, coverage=None, *, partition=False, max_rows=1000, max_bytes=2_000_000):
        """Publish immutable content file first, then atomically replace manifest.

        Every exported row uses an allowlist: private text/review notes never pass.
        Access approval is necessary but does not certify evidence correctness.
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        sources = []
        allowed = {}
        for row in self.db.execute("SELECT r.payload FROM sources s JOIN source_revisions r ON s.id=r.id AND s.revision=r.revision ORDER BY s.id"):
            item = json.loads(row[0])
            if item["access"] != "public_approved":
                continue
            allowed[item["id"]] = item["revision"]
            sources.append({k: item[k] for k in ("id", "revision", "published_date", "body", "family", "url", "content_hash")})
            if "countries" in item:
                sources[-1]["countries"] = sorted(set(item["countries"]))
        roster_groups = {}
        for source in sources:
            key = (source["published_date"], source["body"], source["family"])
            group = roster_groups.setdefault(key, {"date":key[0], "body":key[1], "family":key[2], "countries":set(), "source_ids":set()})
            group["countries"].update(source.get("countries", []))
            group["source_ids"].add(source["id"])
        roster = [{"date":g["date"], "body":g["body"], "family":g["family"], "countries":sorted(g["countries"]), "source_count":len(g["source_ids"])}
                  for _,g in sorted(roster_groups.items())]
        observations, votes = [], []
        versions = {"ontology_version":set(), "extractor_version":set()}
        for row in self.db.execute("SELECT kind,payload FROM evidence ORDER BY id"):
            item = json.loads(row["payload"])
            if allowed.get(item["source_id"]) != item["source_revision"]:
                continue
            keys = ["id", "source_id", "source_revision", "country", "date", "policy", "context"]
            keys += ["stance", "review_state", "attribution"] if row["kind"] == "observation" else ["vote", "resolution", "resolution_version", "stage", "eligible"]
            (observations if row["kind"] == "observation" else votes).append({k: item[k] for k in keys})
            if row["kind"] == "observation":
                for key in versions:
                    value = item.get(key, "legacy")
                    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value):
                        raise ValueError("Version identities must be bounded safe identifiers")
                    versions[key].add(value)
                    if key in item:
                        observations[-1][key] = value
                # Codes only: never export free-form notes or quoted qualifications.
                for key in ("qualification_codes", "unresolved"):
                    if key in item:
                        value = item[key]
                        if key == "unresolved" and type(value) is not bool:
                            raise ValueError("unresolved must be boolean")
                        if key == "qualification_codes" and (not isinstance(value, list) or any(not isinstance(code, str) or not code.replace("_", "").isalnum() for code in value)):
                            raise ValueError("Qualification codes must be identifiers")
                        observations[-1][key] = value
        memberships = [dict(r) for r in self.db.execute("SELECT * FROM memberships ORDER BY country,body,starts")]
        safe_coverage = {k: coverage[k] for k in ("status", "expected", "retrieved", "verified", "unavailable", "excluded") if coverage and k in coverage}
        for key, value in safe_coverage.items():
            if key == "status":
                if not isinstance(value, str) or not value.replace("_", "").isalnum():
                    raise ValueError("Coverage status must be an identifier")
            elif type(value) is not int or value < 0:
                raise ValueError("Coverage counts must be nonnegative integers")
        def make_bundle(ss, oo, vv, mm, rr=None):
            return {"schema": "un.issue-history.shard.v1", "snapshot_id": snapshot_id, "sources": ss,
                "observations": oo, "votes": vv, "memberships": mm, "roster": rr or [], "coverage": safe_coverage or {"status": "not_assessed"}}
        chunks = [("all", make_bundle(sources, observations, votes, memberships, roster), {})]
        if partition:
            if type(max_rows) is not int or max_rows < 1 or type(max_bytes) is not int or max_bytes < 256:
                raise ValueError("Invalid shard bounds")
            source_map = {s["id"]: s for s in sources}
            groups = {}
            used = set()
            for kind, items in (("observations", observations), ("votes", votes)):
                for item in items:
                    source = source_map[item["source_id"]]
                    key = (item["policy"], item["date"][:4], source["body"])
                    groups.setdefault(key, []).append((kind, item))
                    used.add(source["id"])
            for source in sources:
                if source["id"] not in used:
                    groups.setdefault(("_coverage", source["published_date"][:4], source["body"]), []).append(("sources", source))
            for member in memberships:
                groups.setdefault(("_eligibility", "all", member["body"]), []).append(("memberships", member))
            for group in roster:
                groups.setdefault(("_roster", group["date"][:4], group["body"]), []).append(("roster", group))
            chunks = []
            for key, units in sorted(groups.items()):
                current = make_bundle([], [], [], [])
                index = 0
                def add_unit(target, kind, item):
                    result = {**target, **{k: list(target[k]) for k in ("sources", "observations", "votes", "memberships", "roster")}}
                    result[kind].append(item)
                    if kind in ("observations", "votes"):
                        source = source_map[item["source_id"]]
                        if not any(s["id"] == source["id"] for s in result["sources"]):
                            result["sources"].append(source)
                    return result
                for kind, item in units:
                    candidate = add_unit(current, kind, item)
                    count = sum(len(candidate[k]) for k in ("sources", "observations", "votes", "memberships", "roster"))
                    if count > max_rows or len(canonical_bytes(candidate)) > max_bytes:
                        if not any(current[k] for k in ("sources", "observations", "votes", "memberships", "roster")):
                            raise ValueError("Single evidence unit exceeds shard bounds")
                        chunks.append((stable_id("shard", key, index), current, {"policy": key[0], "year": key[1], "body": key[2]}))
                        index += 1
                        candidate = add_unit(make_bundle([], [], [], []), kind, item)
                        if sum(len(candidate[k]) for k in ("sources", "observations", "votes", "memberships", "roster")) > max_rows or len(canonical_bytes(candidate)) > max_bytes:
                            raise ValueError("Single evidence unit exceeds shard bounds")
                    current = candidate
                chunks.append((stable_id("shard", key, index), current, {"policy": key[0], "year": key[1], "body": key[2]}))
            if not chunks:
                chunks = [("empty", make_bundle([], [], [], []), {})]
        payloads = []
        shard_refs = []
        for shard_id, bundle, dimensions in chunks:
            content = canonical_bytes(bundle)
            digest = hashlib.sha256(content).hexdigest()
            filename = "bundle-" + digest + ".json"
            payloads.append((filename, content))
            shard_refs.append({"id": shard_id, "url": filename, "sha256": digest, "bytes": len(content), **dimensions})
        manifest = {"schema": "un.issue-history.manifest.v1", "snapshot_id": snapshot_id,
                    "shards": shard_refs, "versions": {k:sorted(v) or ["legacy"] for k,v in versions.items()},
                    "counts": {"sources": len(sources), "observations": len(observations), "votes": len(votes)}}
        if partition:
            manifest["selection_protocol"] = "policy-year-body-v1"
        frozen = directory / ("snapshot-" + hashlib.sha256(str(snapshot_id).encode()).hexdigest() + ".json")
        if frozen.exists() and frozen.read_bytes() != canonical_bytes(manifest):
            raise ValueError("A snapshot identifier cannot be reused for changed content")
        for filename, content in payloads:
            self._atomic_write(directory / filename, content)
        self._atomic_write(frozen, canonical_bytes(manifest))
        self._atomic_write(directory / "manifest.json", canonical_bytes(manifest))
        return manifest

    @staticmethod
    def _atomic_write(path, data):
        fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
