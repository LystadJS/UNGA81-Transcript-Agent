"""Fail-closed, offline source-bound representation pipeline (stdlib only).

No data is read automatically, and no network or transcript retrieval exists here.
The interface consumes an independently authenticated development/synthetic frame.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import math
import os
from pathlib import Path
from urllib.parse import urlsplit
import re
import tempfile
from typing import Any

SCHEMA = "un.semantic-representation.v1"
FRAME_SCHEMA = "un.semantic-input-frame.v1"
ALLOWED_SOURCE_SCHEMAS = {"synthetic.v1", "un.browser.corpus.v1", "un.passage-corpus.v1", "un.review.v1", "un.latent-comparison.v1"}
HASH_BASIS = {"synthetic", "utf8_response_text", "raw_response_bytes", "utf8_corpus_export", "canonical_source_text", "source_text_file_bytes"}
UNITS = {"synthetic", "source_segment", "passage", "reviewed_speech", "parent"}
SOURCE_STATUS = {"available", "unavailable", "missing_document", "missing_transcript"}
SHA_PATTERN = re.compile(r"^[0-9a-f]{64}$")
MAX_ROWS = 5000
MAX_TEXT = 100000


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(value: Any) -> str:
    return sha(canonical(value))


def _assert(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _hash(value: Any, label: str) -> None:
    _assert(isinstance(value, str) and bool(SHA_PATTERN.fullmatch(value)), label + " must be SHA256")


def _nonempty(value: Any, label: str) -> None:
    _assert(isinstance(value, str) and bool(value.strip()), label + " required")


def eligible(row: dict) -> bool:
    return row["source_status"] == "available" and not row["exclusion_reasons"]


def validate_frame(frame: dict) -> dict:
    """Verify declared source hashes, row eligibility and provenance; never infer identity."""
    _assert(isinstance(frame, dict) and frame.get("schema") == FRAME_SCHEMA, "frame schema mismatch")
    _assert(frame.get("split") in {"development", "synthetic"}, "holdout/restricted split forbidden")
    _assert(frame.get("source_schema") in ALLOWED_SOURCE_SCHEMAS, "unknown source schema")
    _assert(frame.get("source_hash_basis") in HASH_BASIS, "hash basis missing/unknown")
    if frame["split"] == "synthetic":
        _assert(frame["source_schema"] == "synthetic.v1" and frame["source_hash_basis"] == "synthetic", "synthetic lineage mismatch")
    else:
        _assert(frame["source_schema"] != "synthetic.v1" and frame["source_hash_basis"] != "synthetic", "development provenance mismatch")
    for k in ("source_sha256", "selection_sha256"):
        _hash(frame.get(k), k)
    for k in ("population", "source_group_unit", "weighting", "selection_policy", "duplicate_policy"):
        _nonempty(frame.get(k), k)
    _assert(frame.get("unit") in UNITS, "unknown unit")
    rows = frame.get("rows")
    _assert(isinstance(rows, list) and 1 <= len(rows) <= MAX_ROWS, "empty/oversized source population")
    _assert(type(frame.get("inventory_total")) is int and frame["inventory_total"] >= len(rows), "inventory denominator invalid")
    seen = set()
    for row in rows:
        _assert(isinstance(row, dict), "observation not an object")
        ident = row.get("id")
        _nonempty(ident, "observation id")
        _assert(ident not in seen, "duplicate source id")
        seen.add(ident)
        _nonempty(row.get("source_id"), "original source id")
        _hash(row.get("source_sha256"), "source document hash")
        _assert(row.get("unit") == frame["unit"], "observation unit mismatch")
        _assert(row.get("split", frame["split"]) == frame["split"], "row split mismatch")
        _assert(row.get("source_status") in SOURCE_STATUS, "source availability unknown")
        exclusions = row.get("exclusion_reasons")
        _assert(isinstance(exclusions, list) and all(isinstance(v, str) and v.strip() for v in exclusions), "exclusion reasons invalid")
        _assert(row.get("review_status") in {"verified", "unreviewed", "not_applicable", "uncertain"}, "review status missing")
        _assert(row.get("speech_id") is None or row["review_status"] == "verified", "unverified speech attribution")
        _assert(row.get("country") is None or isinstance(row["country"], str), "country is affiliation metadata")
        _assert(row.get("meeting_id") is None or isinstance(row["meeting_id"], str), "ambiguous meeting id")
        if row.get("source_url") is not None:
            _assert(isinstance(row["source_url"], str) and urlsplit(row["source_url"]).scheme == "https" and
                    bool(urlsplit(row["source_url"]).netloc), "non-HTTPS source URL")
        parent = row.get("parent_id")
        if parent is None:
            _assert(all(row.get(k) is None for k in ("parent_text_sha256", "parent_length", "start", "end")), "parent fields without parent")
        else:
            _nonempty(parent, "parent id")
            _hash(row.get("parent_text_sha256"), "parent hash")
            length = row.get("parent_length")
            start, end = row.get("start"), row.get("end")
            _assert(type(length) is int and length > 0, "missing parent bound")
            _assert(type(start) is int and type(end) is int and 0 <= start < end <= length, "invalid parent Unicode codepoint span")
        if eligible(row):
            text = row.get("text")
            _assert(isinstance(text, str) and bool(text.strip()) and len(text) <= MAX_TEXT, "missing/oversized eligible text")
            _hash(row.get("text_sha256"), "original observed text hash")
            _assert(sha(text.encode("utf-8")) == row["text_sha256"], "original UTF8 text hash mismatch; do not normalize")
            _assert(row.get("language") == "en" if frame["split"] == "development" else isinstance(row.get("language"), str), "language coverage unsupported")
        else:
            _assert(bool(exclusions) or row["source_status"] != "available", "excluded status requires a reason")
            _assert(isinstance(row.get("missing_reason"), str) and bool(row["missing_reason"].strip()), "unavailable/excluded reason required")
            _assert(row.get("text") is None, "excluded/unavailable content must not enter encoder")
            if row.get("text_sha256") is not None:
                _hash(row["text_sha256"], "excluded original text hash")
    selected = [row for row in rows if eligible(row)]
    return {"inventory":frame["inventory_total"], "frame_rows":len(rows), "eligible":len(selected),
            "excluded":sum(r["source_status"] == "available" and not eligible(r) for r in rows),
            "unavailable":sum(r["source_status"] != "available" for r in rows),
            "not_in_frame":frame["inventory_total"] - len(rows)}


def identity_rows(frame: dict) -> list[dict]:
    return [{k: row.get(k) for k in ("id", "source_id", "source_sha256", "text_sha256", "unit", "parent_id", "parent_text_sha256", "start", "end", "source_status", "exclusion_reasons", "missing_reason", "meeting_id", "source_family_id", "split")} for row in frame["rows"]]


def frame_identity(frame: dict) -> str:
    validate_frame(frame)
    return digest({k:frame[k] for k in ("schema", "split", "source_schema", "source_hash_basis", "source_sha256", "selection_sha256", "population", "unit", "source_group_unit", "weighting", "selection_policy", "duplicate_policy", "inventory_total")} | {"rows":identity_rows(frame)})


def representation_identity(frame: dict, model: dict, settings: dict, encoder_sha256: str) -> str:
    _assert(isinstance(model, dict) and model.get("schema") in {"un.semantic-model-lock.v1", "un.synthetic-model-lock.v1", "un.lexical-model-lock.v1"}, "invalid model lock")
    _nonempty(model.get("repository"), "model identifier")
    _nonempty(model.get("revision"), "model revision")
    _assert(isinstance(settings, dict) and settings.get("metric") == "cosine" and settings.get("pooling") in {"upstream_chunk_token_weighted", "fixture_token_weighted", "saved_lexical"}, "undeclared representation settings")
    _hash(encoder_sha256, "encoder source")
    return digest({"frame":frame_identity(frame), "model":model, "transform":settings,
                   "encoder_source_sha256":encoder_sha256, "pipeline_sha256":sha(Path(__file__).read_bytes())})


def _vector(vector: Any, dimensions: int | None = None) -> list[float]:
    _assert(isinstance(vector, (list, tuple)) and len(vector)>0, "empty vector")
    vals = [float(x) for x in vector]
    _assert(all(math.isfinite(x) for x in vals), "nonfinite vector")
    _assert(dimensions is None or len(vals) == dimensions, "representation dimensionality drift")
    norm = math.sqrt(sum(x*x for x in vals))
    _assert(norm > 1e-12, "zero vector")
    return [x/norm for x in vals]


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".atomic-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write(canonical(value).decode("utf-8") + "\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _cache_key(row: dict, frame: dict, representation: str) -> str:
    return digest({"representation": representation, "source_sha256":frame["source_sha256"],
                   "source_hash_basis":frame["source_hash_basis"], "selection_sha256":frame["selection_sha256"],
                   "id":row["id"], "text_sha256":row["text_sha256"], "source_id":row["source_id"],
                   "original_sha256":row["source_sha256"], "unit":row["unit"]})


def encode(frame: dict, model: dict, settings: dict, encoder: Any, cache_dir: Path, batch_size: int = 16) -> dict:
    """Encode only eligible rows, cache each vector independently, preserve failures.

    encoder.encode(batch,batch_size) -> (vectors, chunks, audit); no remote dependency here.
    """
    coverage = validate_frame(frame)
    _assert(type(batch_size) is int and 1 <= batch_size <= 32, "batch size outside envelope")
    _assert(model.get("schema") in {"un.synthetic-model-lock.v1", "un.semantic-model-lock.v1"},
            "only verified semantic or synthetic encoders may compute vectors")
    if model["schema"] == "un.semantic-model-lock.v1":
        try:
            from .local_model import model_identity as verified_model_identity
        except ImportError:
            from local_model import model_identity as verified_model_identity
        _assert(model == verified_model_identity(), "checkpoint manifest does not match immutable upstream")
    else:
        _assert(model.get("license") == "synthetic-test-only" and
                str(model.get("repository", "")).startswith("fixture-"), "synthetic test double must be clearly labeled")
    encoder_path = inspect.getsourcefile(type(encoder))
    _assert(bool(encoder_path) and Path(encoder_path).is_file(), "encoder source not available for hashing")
    encoder_sha256 = sha(Path(encoder_path).read_bytes())
    rep = representation_identity(frame, model, settings, encoder_sha256)
    rows = [r for r in frame["rows"] if eligible(r)]
    cache = Path(cache_dir)
    _assert(not cache.is_symlink(), "symlink cache root forbidden")
    cache.mkdir(parents=True,exist_ok=True)
    data: dict[str, dict] = {}
    pending = []
    hits = 0
    for row in rows:
        key = _cache_key(row, frame, rep)
        path = cache / (key + ".json")
        _assert(not path.is_symlink(), "symlink cache item forbidden")
        if path.exists():
            record = json.loads(path.read_text(encoding="utf-8"))
            _assert(record.get("key") == key and record.get("representation_id") == rep, "cache identity mismatch")
            _assert(digest(record.get("vector")) == record.get("vector_sha256"), "cache vector SHA256 corrupted")
            vals = _vector(record["vector"])
            _assert(all(abs(x-y) < 1e-10 for x,y in zip(vals,record["vector"])), "cache vector norm invalid")
            data[row["id"]] = record
            hits += 1
        else:
            pending.append((row,key,path))
    attempts = []
    failures = []
    expected_dim = None
    if data:
        expected_dim = len(next(iter(data.values()))["vector"])
        _assert(all(len(v["vector"]) == expected_dim for v in data.values()), "inconsistent cached dimensions")
    for i in range(0, len(pending), batch_size):
        batch = pending[i:i+batch_size]
        try:
            embeddings,chunks,audit = encoder.encode([dict(r, split=frame["split"]) for r,_,_ in batch], batch_size=batch_size)
            _assert(len(embeddings) == len(batch), "partial inference batch")
            _assert(isinstance(audit,dict) and audit.get("truncated_wordpieces") == 0, "token truncation not auditable")
            _assert(audit.get("passages") == len(batch), "batch denominator mismatch")
            _assert(isinstance(chunks,list) and audit.get("chunks") == len(chunks), "chunk ledger mismatch")
            records=[]
            for row,key,path in batch:
                j = len(records)
                vals = _vector(list(embeddings[j]), expected_dim)
                expected_dim = len(vals)
                owned = [c for c in chunks if c.get("id") == row["id"]]
                _assert(owned and all(type(c.get("token_start")) is int and type(c.get("token_end")) is int and c["token_end"]>c["token_start"] for c in owned), "missing chunk coverage")
                ordered = sorted(owned,key=lambda c:c["token_start"])
                _assert(ordered[0]["token_start"] == 0 and all(a["token_end"]==b["token_start"] for a,b in zip(ordered,ordered[1:])), "token coverage gap or overlap")
                _assert(all(c["token_end"]-c["token_start"]<=254 for c in ordered), "checkpoint token context exceeded")
                record = {"key":key, "representation_id":rep, "vector":vals, "vector_sha256":digest(vals),
                          "chunks":len(ordered), "token_count":ordered[-1]["token_end"],
                          "chunk_ledger_sha256":digest(ordered)}
                records.append((row,path,record))
            for row,path,record in records:
                _atomic_json(path,record)
                data[row["id"]]=record
            attempts.append({"attempt":len(attempts)+1,"status":"success","size":len(batch),"reason":None})
        except Exception as exc:
            attempts.append({"attempt":len(attempts)+1,"status":"failed","size":len(batch),"reason":type(exc).__name__+": "+str(exc)})
            failures.extend(row["id"] for row,_,_ in batch)
    results = []
    for row in frame["rows"]:
        record = data.get(row["id"])
        if record:
            results.append({"id":row["id"], "source_id":row["source_id"], "source_sha256":row["source_sha256"],
                            "text_sha256":row["text_sha256"], "unit":row["unit"], "status":"encoded", "vector":record["vector"],
                            "vector_sha256":record["vector_sha256"], "tokens":record["token_count"], "chunks":record["chunks"],
                            "meeting_id":row.get("meeting_id"),"parent_id":row.get("parent_id"),"source_family_id":row.get("source_family_id"),"reason":None})
        else:
            status = "not_fitted" if eligible(row) else "excluded" if row["source_status"] == "available" else "unavailable"
            results.append({"id":row["id"], "source_id":row["source_id"], "source_sha256":row["source_sha256"],
                            "text_sha256":row.get("text_sha256"), "unit":row["unit"], "status":status, "vector":None,
                            "vector_sha256":None,"tokens":None,"chunks":None,"meeting_id":row.get("meeting_id"),
                            "parent_id":row.get("parent_id"),"source_family_id":row.get("source_family_id"),
                            "reason": "inference failed" if row["id"] in failures else row["missing_reason"]})
    coverage |= {"encoded":len(data),"not_fitted":len(failures),"cache_hits":hits,"cache_misses":len(pending),
                 "attempted_batches":len(attempts),"successful_batches":sum(x["status"]=="success" for x in attempts),
                 "failed_batches":sum(x["status"]=="failed" for x in attempts)}
    _assert(coverage["encoded"]+coverage["not_fitted"]==coverage["eligible"], "attempt population ledger drift")
    return {"schema":SCHEMA, "representation_id":rep, "representation_basis_id":rep,
            "frame_sha256":frame_identity(frame),"source_schema":frame["source_schema"],
            "source_hash_basis":frame["source_hash_basis"], "source_sha256":frame["source_sha256"],
            "selection_sha256":frame["selection_sha256"], "split":frame["split"], "population":frame["population"],
            "unit":frame["unit"], "source_group_unit":frame["source_group_unit"],"weighting":frame["weighting"],
            "model":model,"settings":settings,"encoder_source_sha256":encoder_sha256,
            "pipeline_sha256":sha(Path(__file__).read_bytes()),"rows":results,"coverage":coverage,"failure_ledger":attempts,
            "publication_eligible":False,"evaluation_role":"engineering_only"}
