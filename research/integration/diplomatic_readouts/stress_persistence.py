"""Reproduce synthetic restart/dual-authority compromise cases offline.

Fictional fixtures only. Generates no access or publication credentials.
Run: python stress_persistence.py --output /tmp/new-empty-directory
"""
from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tests"))
from test_synthetic_signatures import fixture, resign_custody, resign_revocation
from test_registry_preflight import WHEN
from persistent_revocation_review import (
    assert_no_authority, guarded_restart_verify, make_verified_state,
    write_state_rehearsal,
)


def _state(f, previous=None):
    return make_verified_state(
        f["snapshot"], f["policy"], f["events"], f["proposal"],
        f["custody"], f["revocation"], checked_at=WHEN,
        trust=f["trust"], previous=previous,
    )


def _test(path, pin, f):
    r = guarded_restart_verify(
        path, pin, f["snapshot"], f["policy"], f["events"], f["proposal"],
        f["custody"], f["revocation"], checked_at=WHEN, trust=f["trust"],
    )
    assert_no_authority(r)
    return r


def scenarios():
    with tempfile.TemporaryDirectory(prefix="unga-synthetic-revocation-") as directory:
        path = Path(directory) / "observer.synthetic.json"
        baseline = fixture()
        old_state = _state(baseline)
        old_pin = write_state_rehearsal(path, old_state)
        old_bytes = path.read_bytes()
        yield "fresh_pinned_restart", _test(path, old_pin, baseline)

        changed = fixture()
        changed["custody"]["key_id"] = changed["key_ids"]["rotation"]
        resign_custody(changed)
        changed["revocation"]["payload"]["sequence"] = 3
        changed["revocation"]["payload"]["revoked_key_ids"] = [
            changed["key_ids"]["custody"]]
        resign_revocation(changed)
        changed["trust"] = replace(changed["trust"], minimum_checkpoint_sequence=3)
        new_state = _state(changed, old_pin)
        new_pin = write_state_rehearsal(path, new_state, previous_pin=old_pin)
        yield "rotated_key_new_checkpoint_no_authority", _test(path, new_pin, changed)
        yield "old_signatures_replayed_against_new_pin", _test(path, new_pin, baseline)
        path.write_bytes(old_bytes)
        yield "old_disk_checkpoint_restored", _test(path, new_pin, baseline)
        path.unlink()
        yield "deleted_persistent_state", _test(path, new_pin, changed)

        # A fictional adversary controls both Ed25519 role keys; the independent
        # observer still retains the earlier witness head.
        collusion = fixture()
        collusion["custody"]["payload"]["issued_at"] = "2026-10-14T01:00:00Z"
        resign_custody(collusion)
        collusion["revocation"]["payload"]["observed_at"] = "2026-10-14T02:00:00Z"
        resign_revocation(collusion)
        path.write_bytes(old_bytes)
        yield "two_signers_compromised_pin_intact", _test(path, old_pin, collusion)

        # No cryptographic system can differentiate this scenario if the
        # attacker also controls the pin distribution and persistent state.
        path.unlink()
        synthetic_forged_pin = write_state_rehearsal(path, _state(collusion))
        yield "two_signers_and_observer_compromised_known_limit", _test(
            path, synthetic_forged_pin, collusion)
        yield "observer_pin_missing", _test(path, None, collusion)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    root = args.output
    if root.is_symlink() or root.exists() and (not root.is_dir() or any(root.iterdir())):
        parser.error("output must be a new or empty nonsymlink directory")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    cases = {}
    for name, value in scenarios():
        expected_positive = name in (
            "fresh_pinned_restart", "rotated_key_new_checkpoint_no_authority",
            "two_signers_and_observer_compromised_known_limit",
        )
        assert (value["status"] == "synthetic_checkpoint_consistent_no_authority") == expected_positive, name
        assert value["authorized"] is False and value["publication_eligible"] is False
        assert value["can_read_source"] is False and value["delivery_eligible"] is False
        assert set(value["gate_status"].values()) == {"NOT_RUN"}
        body = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
        (root / (name + ".json")).write_bytes(body)
        cases[name] = {"status": value["status"], "reason_codes": value["reason_codes"],
                       "sha256": sha256(body).hexdigest()}
        print(name, value["status"])
    manifest = {
        "schema": "un.synthetic-restart-compromise-demonstration.v0",
        "synthetic_only": True, "authority": "none", "authorized": False,
        "can_read_source": False, "publication_eligible": False,
        "delivery_eligible": False, "transcripts_opened": 0,
        "cases": cases,
        "known_limit": "dual_signers_plus_external_observer_compromise_can_forge_metadata_but_never_grant_access",
    }
    raw = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    (root / "manifest.json").write_bytes(raw)
    print("manifest_sha256", sha256(raw).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
