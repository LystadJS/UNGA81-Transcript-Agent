"""Rebaseline a cursor only after read-only replay matches every prior output."""
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
from ..ingest.adapters import digest
from ..ingest.countries import map_country
from ..store import IssueStore, stable_id, canonical_bytes
from .csv_cli import Lines
from .vote_cli import file_hash


def review_cursor(*, source_file, database, checkpoint, receipt_file, family="ga"):
    if family != "ga":
        raise ValueError("Only the reviewed GA prefix replay is supported")
    from ..ingest.ga_votes import adapt, validate_headers
    checkpoint = Path(checkpoint)
    original = checkpoint.read_bytes()
    state = json.loads(original)
    old = state["identity"]
    if old["family"] != family or state["quarantined"] != 0:
        raise ValueError("Family mismatch or quarantined prefix requires separate review")
    if file_hash(source_file) != old["download_sha256"]:
        raise ValueError("Original downloaded bytes differ")
    registry_hash = map_country("USA", "placeholder")["country_registry_sha256"]
    if old["country_registry_sha256"] != registry_hash:
        raise ValueError("Country registry changed")
    current = {**old,"adapter_sha256":file_hash(adapt.__code__.co_filename),
        "source_hashes":{name:file_hash(Path(__file__).resolve().parents[1]/"ingest"/name) for name in ("countries.py","adapters.py")}}
    accepted = excluded = 0
    rolling_digest = hashlib.sha256()
    connection = sqlite3.connect(Path(database).resolve().as_uri()+"?mode=ro",uri=True)
    try:
        opener = gzip.open if str(source_file).endswith(".gz") else open
        with opener(source_file,"rt",encoding="utf-8-sig",newline="") as stream:
            reader = csv.DictReader(Lines(stream));validate_headers(reader.fieldnames)
            for _ in range(state["scanned"]):
                raw = next(reader)
                if not old["start"] <= raw["date"] <= old["end"]:
                    excluded += 1
                    continue
                row = adapt(raw)
                source_id = stable_id("un-vote-source","GA",row["resolution_id"],row["resolution_version"],row["stage"],row.get("country_code") or row["country_id"])
                evidence_id = stable_id("un-vote",source_id)
                found = connection.execute("SELECT r.payload,e.payload FROM sources s JOIN source_revisions r ON s.id=r.id AND s.revision=r.revision JOIN evidence e ON e.source_id=s.id AND e.source_revision=s.revision WHERE s.id=? AND e.id=? AND e.kind='vote'",(source_id,evidence_id)).fetchone()
                if not found:
                    raise ValueError("Missing current source/evidence identity")
                source,evidence = map(json.loads,found)
                if source["content_hash"] != digest(row) or source["download_sha256"] != old["download_sha256"]:
                    raise ValueError("Replayed normalized source digest differs")
                expected = dict(id=evidence_id,source_id=source_id,source_revision=source["revision"],country=row["country_id"],date=row["date"],policy="unbound",context=row["resolution_id"],vote=row["vote"],eligible=row.get("eligible"),resolution=row["resolution_id"],resolution_version=row["resolution_version"],stage=row["stage"])
                expected.update({key:row[key] for key in ("country_code","raw_vote_code","recorded_country_name","country_mapping_status","country_registry_sha256","adapter_version","recorded_resolution_symbol","modality","individual_vote_recorded") if key in row})
                if evidence != expected:
                    raise ValueError("Replayed evidence fields differ")
                rolling_digest.update(canonical_bytes([source_id,digest(row),evidence_id]))
                accepted += 1
            if stream.tell() != state["offset"]:
                raise ValueError("Replayed CSV offset differs")
        count = connection.execute("SELECT count(*) FROM evidence e JOIN source_revisions r ON e.source_id=r.id AND e.source_revision=r.revision WHERE e.kind='vote' AND json_extract(r.payload,'$.body')='GA'").fetchone()[0]
        if accepted != state["accepted"] or accepted != state["selected"] or excluded != state["out_of_window"] or count != accepted:
            raise ValueError("Replayed prefix counts differ")
    finally:
        connection.close()
    receipt = {"schema":"un.issue-history.cursor-rebaseline.v1","review_state":"engineering_replay_verified",
        "not_human_confirmation":True,"old_identity":old,"new_identity":current,"verified_rows":accepted,
        "excluded_rows":excluded,"source_rows_replayed":state["scanned"],"prefix_output_sha256":rolling_digest.hexdigest(),
        "old_cursor_sha256":hashlib.sha256(original).hexdigest(),"limitation":"A new verified baseline, not a claim about previously unrecorded helper hashes. No observations or issue agreement inferred."}
    backup = checkpoint.with_name(checkpoint.stem+"-pre-rebaseline.json")
    if backup.exists() and backup.read_bytes()!=original:
        raise ValueError("Conflicting rebaseline backup exists")
    IssueStore._atomic_write(backup,original)
    receipt_file = Path(receipt_file)
    IssueStore._atomic_write(receipt_file,canonical_bytes(receipt))
    if checkpoint.read_bytes()!=original:
        raise ValueError("Cursor changed during replay; no update")
    state["identity"] = current
    state["engineering_review"] = {"receipt_sha256":hashlib.sha256(canonical_bytes(receipt)).hexdigest(),"review_state":"engineering_replay_verified"}
    IssueStore._atomic_write(checkpoint,canonical_bytes(state))
    return receipt


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source-file","database","checkpoint","receipt-file"):
        parser.add_argument("--"+name,required=True)
    print(json.dumps(review_cursor(**vars(parser.parse_args())),indent=2))
