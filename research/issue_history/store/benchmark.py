"""Reproducible synthetic store/export timings, not source-scale acceptance."""
import argparse
import json
import os
from pathlib import Path
import platform
import tempfile
import time
from .repository import IssueStore


def measure(size=1000):
    if type(size) is not int or not 1 <= size <= 50_000:
        raise ValueError("Fixture size must be 1..50000")
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        base = Path(directory)
        store = IssueStore(base / "fixture.sqlite")
        rows = [dict(id="synthetic-" + str(i), published_date=f"202{ i % 5}-01-01", body="SC" if i % 2 else "GA",
            family="synthetic", url="https://example.invalid/" + str(i), content_hash="a" * 64, access="public_approved", countries=["Example" + str(i % 193)]) for i in range(size)]
        try:
            def ingest():
                for source in rows:
                    revision = store.upsert_source(source)
                    store.put_observation(dict(id=source["id"] + "-position", source_id=source["id"], source_revision=revision,
                        country=source["countries"][0], date=source["published_date"], policy="humanitarian_access",
                        context="synthetic_context", stance="support", review_state="assistant_provisional", attribution="national"))
            times = {}
            for name, action in (("cold_ingest_seconds", ingest), ("warm_idempotent_ingest_seconds", ingest),
                ("cold_export_seconds", lambda: store.export_bundle(base / "public", "fixture", partition=True, max_rows=100)),
                ("warm_export_seconds", lambda: store.export_bundle(base / "public", "fixture", partition=True, max_rows=100))):
                started = time.perf_counter()
                action()
                times[name] = round(time.perf_counter() - started, 6)
            manifest = json.loads((base / "public" / "manifest.json").read_bytes())
            return {"schema": "un.issue-history.synthetic-benchmark.v1", "fixture_sources": size,
                "fixture_observations": size, "platform": platform.system(), "python": platform.python_version(),
                "logical_processors": os.cpu_count(), "shards": len(manifest["shards"]),
                "bytes": sum(s["bytes"] for s in manifest["shards"]), "measurements": times,
                "limitations": "Single local run; warm means repeated ledger operation, not browser cache. No network, real sources, extraction inference, model fitting, or report rendering measured."}
        finally:
            store.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=1000)
    args = parser.parse_args()
    print(json.dumps(measure(args.size), indent=2))
