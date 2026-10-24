"""Private resumable CSV ledger ingestion; never publishes or binds vote policy."""
import argparse
import csv
import datetime as dt
import json
import gzip
import shutil
from pathlib import Path
from ..store import IssueStore, stable_id, canonical_bytes
from ..ingest.adapters import digest
from .vote_cli import file_hash


class Lines:
    def __init__(self, stream):
        self.stream = stream
    def __iter__(self):
        return self
    def __next__(self):
        line = self.stream.readline()
        if not line:
            raise StopIteration
        return line


def ingest_csv(*, source_file, expected_sha256, database, checkpoint, provenance_file,
               start, end, family="ga", max_batches=20, batch_size=500, min_free_bytes=209_715_200):
    if family == "ga":
        from ..ingest.ga_votes import adapt, validate_headers
    elif family == "sc":
        from ..ingest.un_sc_csv import adapt, validate_headers
    else:
        raise ValueError("Unknown source family")
    dt.date.fromisoformat(start); dt.date.fromisoformat(end)
    if start > end or type(batch_size) is not int or not 1 <= batch_size <= 500 or type(max_batches) is not int or not 1 <= max_batches <= 1000:
        raise ValueError("Invalid date/batch bounds")
    if file_hash(source_file) != expected_sha256:
        raise ValueError("Downloaded source digest mismatch")
    from ..ingest.countries import map_country
    identity = dict(download_sha256=expected_sha256, family=family, start=start, end=end,
        adapter_sha256=file_hash(adapt.__code__.co_filename),
        source_hashes={name:file_hash(Path(__file__).resolve().parents[1]/"ingest"/name)
            for name in ("countries.py", "adapters.py")},
        country_registry_sha256=map_country("USA", "recorded placeholder")["country_registry_sha256"])
    checkpoint = Path(checkpoint)
    state = json.loads(checkpoint.read_text(encoding="utf-8")) if checkpoint.exists() else {
        "schema":"un.issue-history.csv-cursor.v1", "identity":identity, "offset":None,
        "scanned":0, "selected":0, "accepted":0, "out_of_window":0, "quarantined":0, "quarantine_sample":[], "complete":False}
    if state.get("identity") != identity:
        raise ValueError("CSV checkpoint input/window changed")
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    provenance_path = Path(provenance_file)
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    store = IssueStore(database)
    try:
        opener = gzip.open if str(source_file).endswith(".gz") else open
        storage_blocked = False
        with opener(source_file, "rt", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(Lines(stream))
            validate_headers(reader.fieldnames)
            if state["offset"] is not None:
                stream.seek(state["offset"])
            batches = 0
            while not state["complete"] and batches < max_batches:
                # Five MB bounds the next small metadata batch's transient
                # journal/growth, retaining the configured operating reserve.
                if shutil.disk_usage(Path(database).parent).free < min_free_bytes + 5_000_000:
                    storage_blocked = True
                    break
                batch = []
                while len(batch) < batch_size:
                    try:
                        raw = next(reader)
                    except StopIteration:
                        state["complete"] = True
                        break
                    state["scanned"] += 1
                    date = raw.get("date", "")
                    try:
                        dt.date.fromisoformat(date)
                        if not start <= date <= end:
                            state["out_of_window"] += 1
                            continue
                        state["selected"] += 1
                        batch.append(adapt(raw))
                    except (ValueError, TypeError, KeyError):
                        state["quarantined"] += 1
                        if len(state["quarantine_sample"]) < 100:
                            state["quarantine_sample"].append({"row":state["scanned"],"sha256":digest(raw),"reason":"adapter_rejected"})
                with store.transaction():
                    for row in batch:
                        body = family.upper()
                        source_id = stable_id("un-vote-source", body, row["resolution_id"], row["resolution_version"], row["stage"], row.get("country_code") or row["country_id"])
                        revision = store.upsert_source({"id":source_id,"published_date":row["date"],"body":body,
                            "family":"un_recorded_vote","url":row["source_url"],"content_hash":digest(row),"access":"private",
                            "countries":[row["country_id"]],"hash_scope":"normalized_vote_metadata","download_sha256":expected_sha256})
                        store.put_vote({"id":stable_id("un-vote",source_id),"source_id":source_id,"source_revision":revision,
                            "country":row["country_id"],"date":row["date"],"policy":"unbound","context":row["resolution_id"],
                            "vote":row["vote"],"eligible":row.get("eligible"),"resolution":row["resolution_id"],
                            "resolution_version":row["resolution_version"],"stage":row["stage"],
                            **{key:row[key] for key in ("country_code","raw_vote_code","recorded_country_name","country_mapping_status","country_registry_sha256","adapter_version","recorded_resolution_symbol","modality","individual_vote_recorded") if key in row}})
                state["accepted"] += len(batch)
                state["offset"] = stream.tell()
                store._atomic_write(checkpoint, canonical_bytes(state))
                batches += 1
        provenance = {"schema":"un.issue-history.private-csv-ingest.v1",**identity,
            **{key:state[key] for key in ("scanned","selected","accepted","out_of_window","quarantined","complete")},
            "publication":"private_only","policy_binding":"withheld_unbound",
            "storage_reserve_reached":storage_blocked,"minimum_free_bytes":min_free_bytes,
            "free_bytes":shutil.disk_usage(Path(database).parent).free,
            "limitations":"Selected date-window rows only. Non-voting codes remain unknown; no issue position inferred. Coverage excludes unrecorded/failed/procedural votes absent from source dataset."}
        store._atomic_write(provenance_path, canonical_bytes(provenance))
        return provenance
    finally:
        store.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source-file","expected-sha256","database","checkpoint","provenance-file","start","end"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--family",choices=("ga","sc"),default="ga")
    parser.add_argument("--max-batches",type=int,default=20)
    parser.add_argument("--batch-size",type=int,default=500)
    parser.add_argument("--min-free-bytes",type=int,default=209715200)
    print(json.dumps(ingest_csv(**vars(parser.parse_args())),indent=2))
