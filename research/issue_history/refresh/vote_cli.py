"""Private bounded normalized-vote ingestion, without invented issue bindings.

An approved format adapter must produce normalized rows first. The downloaded
source file's exact digest and path are retained privately for reproduction.
No bundles are published by this command.
"""
import argparse
import hashlib
import gzip
import json
from pathlib import Path
from ..ingest.adapters import vote_record, digest
from ..ingest.runner import run_batch
from ..store import IssueStore, stable_id, canonical_bytes


def file_hash(path):
    result = hashlib.sha256()
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def ingest_votes(*, normalized_file, source_file, expected_sha256, database,
                 checkpoint, provenance_file, body="GA", limit=500, year=None):
    if body not in ("GA", "SC") or type(limit) is not int or not 1 <= limit <= 500:
        raise ValueError("Choose GA or SC and a bounded limit of 1..500")
    if file_hash(source_file) != expected_sha256:
        raise ValueError("Downloaded source digest mismatch")
    normalized_path = Path(normalized_file)
    if normalized_path.stat().st_size > 5_000_000:
        raise ValueError("Normalized shard exceeds private staging bound")
    rows = json.loads(normalized_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or len(rows) > 500:
        raise ValueError("Normalized shard must contain at most 500 records")
    for row in rows:
        if year is not None and not str(row.get("date", "")).startswith(str(year) + "-"):
            raise ValueError("Row outside declared year shard")
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    store = IssueStore(database)
    try:
        def persist(row):
            source_id = stable_id("un-vote-source", body, row["resolution_id"], row["resolution_version"], row["stage"], row.get("country_code") or row["country_id"])
            revision = store.upsert_source({"id": source_id, "published_date": row["date"], "body": body,
                "family": "un_recorded_vote", "url": row["source_url"], "content_hash": digest(row), "access": "private",
                "countries": [row["country_id"]], "hash_scope": "normalized_vote_metadata", "download_sha256": expected_sha256})
            store.put_vote({"id": stable_id("un-vote", source_id), "source_id": source_id, "source_revision": revision,
                "country": row["country_id"], "date": row["date"], "policy": "unbound", "context": row["resolution_id"],
                "vote": row["vote"], "eligible": row.get("eligible"), "resolution": row["resolution_id"],
                "resolution_version": row["resolution_version"], "stage": row["stage"],
                **{key: row[key] for key in ("country_code", "raw_vote_code", "recorded_country_name", "country_mapping_status", "country_registry_sha256", "adapter_version", "recorded_resolution_symbol", "modality", "individual_vote_recorded") if key in row}})
        checkpoint_path = Path(checkpoint)
        previous = json.loads(checkpoint_path.read_text(encoding="utf-8")) if checkpoint_path.exists() else None
        with store.transaction():
            state = run_batch(rows, vote_record, persist, previous, limit=limit)
        # Commit before advancing cursor; a crash between these steps safely
        # retries idempotent rows rather than skipping uncommitted records.
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        store._atomic_write(checkpoint_path, canonical_bytes(state))
        provenance = {"schema": "un.issue-history.private-ingest.v1", "body": body, "year": year,
            "download_sha256": expected_sha256, "normalized_sha256": file_hash(normalized_file),
            "input_records": len(rows), "coverage": state["coverage"], "complete": state["complete"],
            "policy_binding": "withheld_unbound", "publication": "private_only",
            "limitations": "Bounded shard coverage only; votes are not statements or inferred issue positions."}
        path = Path(provenance_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        store._atomic_write(path, canonical_bytes(provenance))
        return provenance
    finally:
        store.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("normalized-file", "source-file", "expected-sha256", "database", "checkpoint", "provenance-file"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--body", choices=("GA", "SC"), default="GA")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--year", type=int)
    print(json.dumps(ingest_votes(**vars(parser.parse_args())), indent=2))
