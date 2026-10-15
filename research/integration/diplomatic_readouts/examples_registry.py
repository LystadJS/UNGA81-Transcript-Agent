"""Generate invented registry preflight receipts, never real source metadata.

Usage: python examples_registry.py --output /tmp/new-synthetic-registry-examples
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tests"))
from test_registry_preflight import WHEN, fixtures, bind, proposal_for  # synthetic test data only
from registry_preflight import (LOCK, event_digest, preflight, assert_no_authority,
                                receipt_digest)


def cases():
    snapshot, policy, events = fixtures()
    yield "consistent_metadata_not_authorized", snapshot, policy, events

    snapshot, policy, events = fixtures()
    snapshot["records"][0]["raw_sha256"] = "invalid"
    bind(snapshot, policy, events)
    yield "corrupt_source_hash", snapshot, policy, events

    snapshot, policy, events = fixtures()
    policy["expires_at"] = "2026-10-14T00:00:00Z"
    yield "expired_custody", snapshot, policy, events

    snapshot, policy, events = fixtures()
    policy["permissions"]["read_reserved"] = True
    yield "reserved_access_escalation", snapshot, policy, events

    snapshot, policy, events = fixtures()
    snapshot["population"]["eligible"] = 0
    snapshot["population"]["excluded"] = 1
    bind(snapshot, policy, events)
    yield "population_mismatch", snapshot, policy, events

    snapshot, policy, events = fixtures()
    event = {"index": 3, "event_id": "synthetic:revocation", "kind": "revoked",
             "actor_ref": "synthetic:custodian", "occurred_at": "2026-10-14T00:00:00Z",
             "registry_sha256": policy["registry_sha256"],
             "previous_sha256": events[-1]["event_sha256"]}
    event["event_sha256"] = event_digest(event)
    events.append(event)
    policy["revocation_sequence"] = 3
    yield "revoked_custody", snapshot, policy, events

    snapshot, policy, events = fixtures()
    snapshot["holdout_lock"]["transcripts_opened"] = 1
    bind(snapshot, policy, events)
    yield "reserved_holdout_tamper", snapshot, policy, events


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    root = args.output
    repo_root = HERE.parents[2]
    if root.resolve().is_relative_to(repo_root.resolve()):
        parser.error("output must be outside the Git checkout")
    if root.is_symlink() or root.exists() and (not root.is_dir() or any(root.iterdir())):
        parser.error("output must be new or empty and not a symlink")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    states = {}
    for name, snapshot, policy, events in cases():
        result = preflight(snapshot, policy, events, checked_at=WHEN, proposal=proposal_for(snapshot))
        assert_no_authority(result)
        payload = (json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        with (root / (name + ".json")).open("xb") as stream:
            stream.write(payload)
        states[name] = {"metadata_status": result["metadata_status"],
                        "receipt_sha256": sha256(payload).hexdigest(),
                        "reason_codes": result["reason_codes"]}
        print(name, result["metadata_status"])
    assert len(states) == 7
    assert states["consistent_metadata_not_authorized"]["metadata_status"] == "metadata_consistent"
    assert all(entry["metadata_status"] == "withheld" for name, entry in states.items()
               if name != "consistent_metadata_not_authorized")
    manifest = {"schema": "un.private-source-registry.synthetic-examples.v0",
                "synthetic_only": True, "authorized": False,
                "publication_eligible": False, "delivery_eligible": False,
                "transcripts_opened": 0, "cases": states}
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with (root / "manifest.json").open("xb") as stream:
        stream.write(manifest_bytes)
    print("manifest_sha256", sha256(manifest_bytes).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
