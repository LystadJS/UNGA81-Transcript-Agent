"""Deterministic synthetic multi-host witness/fork/rollback stress harness.

No real source records, original transcripts, signing keys or authorizations in
exports. Repeated runs with the same scenario count/seed are byte-identical.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tests"))
from test_multi_host_witness import (  # noqa: E402
    fictional_fixture, inspect, attest, resign_host, OBSERVER_IDS, new_log_event,
    log_digest, checkpoint_digest, propose_observer_pins,
)
from synthetic_signatures import REVOCATION_SCHEMA, content_digest

ATTACKS = (
    "valid_quorum", "insufficient_quorum", "duplicate_host", "two_observer_fork",
    "stale_epoch_replay", "fork_gossip", "wrong_audience", "tampered_attestation",
    "audit_prefix_rewrite", "source_checkpoint_substitution", "compromised_quorum_and_pins",
    "valid_four_host_quorum", "bad_clock", "revoked_source_checkpoint_replacement",
)
POSITIVES = {"valid_quorum", "valid_four_host_quorum", "compromised_quorum_and_pins"}


def mutate(f: dict, kind: str) -> None:
    ids = f["ids"]
    cp = f["checkpoint"]
    if kind == "valid_quorum":
        return
    if kind == "valid_four_host_quorum":
        resign_host(f, ids)
    elif kind == "insufficient_quorum":
        f["attestations"] = f["attestations"][:2]
    elif kind == "duplicate_host":
        f["attestations"][2] = deepcopy(f["attestations"][0])
    elif kind == "two_observer_fork":
        a, b = f["pins"]
        f["pins"] = (a, replace(b, checkpoint_sha256="a"*64))
    elif kind == "stale_epoch_replay":
        f["pins"] = propose_observer_pins(cp, OBSERVER_IDS)
    elif kind == "fork_gossip":
        other = deepcopy(cp)
        other["log_sha256"] = "a"*64
        f["gossip"] = [attest(other, ids[3], f["keys"][ids[3]])]
    elif kind == "wrong_audience":
        cp["audience"] = "synthetic:unrelated"
        resign_host(f)
    elif kind == "tampered_attestation":
        f["attestations"][0]["signature_b64"] = f["attestations"][1]["signature_b64"]
    elif kind == "audit_prefix_rewrite":
        orig = f["log"]
        new = []
        for i, event in enumerate(orig):
            new.append(new_log_event(new,
                                     "synthetic:rewritten-genesis" if i == 0 else event["event_id"],
                                     event["kind"], event["registry_sha256"],
                                     event["revocation_sha256"], event["occurred_at"]))
        f["log"] = new
        cp["log_sha256"] = log_digest(new)
        cp["log_tip_sha256"] = new[-1]["event_sha256"]
        resign_host(f)
    elif kind == "source_checkpoint_substitution":
        cp["revocation_sha256"] = "d" * 64
        resign_host(f)
    elif kind == "compromised_quorum_and_pins":
        # Expected vulnerability: all source signers, >=3 witness signers and
        # both independent observer pins compromised. Still NO access authority.
        src = f["source"]
        from test_synthetic_signatures import resign_revocation
        src["revocation"]["payload"]["observed_at"] = "2026-10-14T03:00:00Z"
        resign_revocation(src)
        rev = content_digest(REVOCATION_SCHEMA, src["revocation"]["payload"])
        cloned = []
        for i, row in enumerate(f["log"][:2]):
            cloned.append(new_log_event(cloned, "synthetic:forged-host-%s" % (i+1),
                                        row["kind"], src["trust"].expected_registry_sha256,
                                        rev, row["occurred_at"]))
        old = deepcopy(cp)
        old.update(epoch=0, log_length=2, log_sha256=log_digest(cloned),
                   log_tip_sha256=cloned[-1]["event_sha256"], revocation_sha256=rev)
        f["pins"] = propose_observer_pins(old, OBSERVER_IDS)
        cloned.append(new_log_event(cloned, "synthetic:forged-host-3",
                                    "audit_observed", src["trust"].expected_registry_sha256,
                                    rev, "2026-10-15T01:00:00Z"))
        f["log"] = cloned
        cp.update(revocation_sha256=rev,
                  previous_checkpoint_sha256=checkpoint_digest(old),
                  log_sha256=log_digest(cloned),
                  log_tip_sha256=cloned[-1]["event_sha256"])
        resign_host(f)
    elif kind == "bad_clock":
        cp["expires_at"] = "2026-10-15T02:01:00Z"
        resign_host(f)
    elif kind == "revoked_source_checkpoint_replacement":
        f["source"]["revocation"]["payload"]["sequence"] = 4
        from test_synthetic_signatures import resign_revocation
        resign_revocation(f["source"])
    else:
        raise ValueError("unrecognized synthetic attack")


def simulate(iterations: int = 280, seed: int = 81081) -> dict:
    if type(iterations) is not int or not 28 <= iterations <= 2048:
        raise ValueError("iterations must be an integer in [28,2048]")
    if type(seed) is not int or seed < 0 or seed > 2**31:
        raise ValueError("synthetic deterministic seed invalid")
    rng = random.Random(seed)
    seen = {name: {"attempted": 0, "expected": "no_authority" if name in POSITIVES else "withheld", "failures": 0}
            for name in ATTACKS}
    order = list(ATTACKS) * (iterations // len(ATTACKS)) + list(ATTACKS)[:iterations % len(ATTACKS)]
    rng.shuffle(order)
    for kind in order:
        f = fictional_fixture()
        mutate(f, kind)
        out = inspect(f)
        want = "synthetic_quorum_consistent_no_authority" if kind in POSITIVES else "withheld"
        seen[kind]["attempted"] += 1
        if out["status"] != want or out["authority"] != "none" or out["can_read_source"] is not False or out["publication_eligible"] is not False:
            seen[kind]["failures"] += 1
    failures = sum(x["failures"] for x in seen.values())
    if failures:
        raise AssertionError("synthetic witness stress failed: " + str(failures))
    return {"schema": "un.synthetic-multi-host-witness-stress.v0",
            "fixture_kind": "synthetic", "seed": seed, "iterations": iterations,
            "source_access_granted": False, "authorized": False,
            "publication_eligible": False, "delivery_eligible": False,
            "transcripts_opened": 0, "failures": failures,
            "expected_limitations": ["full_compromise_of_quorum_and_observer_pins_cannot_be_detected",
                                     "synthetic_observer_pins_are_not_authenticated_real_services",
                                     "append_only_checked_only_against_independently_pinned_prefix"],
            "cases": seen}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=280)
    parser.add_argument("--seed", type=int, default=81081)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    target = args.output
    if target.is_symlink() or (target.exists() and (not target.is_dir() or any(target.iterdir()))):
        parser.error("output must be a new or empty nonsymlink directory")
    receipt = simulate(args.iterations, args.seed)
    target.mkdir(mode=0o700, parents=True, exist_ok=True)
    raw = (json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    (target / "stress-manifest.json").write_bytes(raw)
    print("cases", len(receipt["cases"]), "iterations", receipt["iterations"],
          "failures", receipt["failures"], "manifest_sha256", sha256(raw).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
