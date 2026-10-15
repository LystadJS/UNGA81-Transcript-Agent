"""Deterministic synthetic witness partitions, restart/equivocation stress.

No network, original sources, approval actions, operational cryptographic keys,
transcript bytes or publication. The test signing keys are PUBLICLY RECONSTRUCTIBLE.
Run from repository root: python research/integration/diplomatic_readouts/stress_partition.py
    --iterations 360 --seed 81081 --output /tmp/fresh-partition-qa
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tests"))
from test_partition_reconciliation import fixture, sign_forged, make_cp, new_event, OBSERVERS
from partition_reconciliation import (
    assert_no_authority, checkpoint_digest, new_signer_state,
    signer_vote, propose_signer_pins, propose_gossip_pins,
    reconcile_gossip, new_gossip_state, vote_digest, SyntheticRefusal,
)

CASES = (
    "partition_two_two_pending",
    "partition_three_one_quorum_no_authority",
    "delayed_gossip_pending_then_quorum",
    "duplicate_delivery_pending",
    "reversed_message_order_quorum",
    "single_equivocating_signer_detected",
    "conflicting_overlapping_quorums_detected",
    "two_corrupt_signers_cannot_form_quorum",
    "observer_pin_rollback_withheld",
    "observer_pin_fork_withheld",
    "signer_restart_rollback_rejected",
    "valid_witness_restart_advances",
    "invalid_signed_vote_refused",
    "wrong_parent_replay_refused",
    "same_sequence_revocation_rewrite_refused",
    "delayed_equivocation_evidence_persists",
    "compromised_keys_and_replaced_pins_known_limit",
    "permission_escalation_refused",
)


def _receipt_or_failure(f, payloads, *, state=None, pins=None):
    return reconcile_gossip(state if state is not None else f["gossip"],
                            pins if pins is not None else f["gpins"],
                            payloads, f["trust"])


def execute_case(case, rotation):
    f = fixture()
    ids = f["ids"]
    votes = f["votes"]
    if case == "partition_two_two_pending":
        part = (ids[:2], ids[2:])[rotation % 2]
        _, r = _receipt_or_failure(f, [votes[x] for x in part]); expected = "pending_gossip"
    elif case == "partition_three_one_quorum_no_authority":
        part = [ids[(rotation + n) % 4] for n in range(3)]
        _, r = _receipt_or_failure(f, [votes[x] for x in part]); expected = "quorum_observed_no_authority"
    elif case == "delayed_gossip_pending_then_quorum":
        s, pending = _receipt_or_failure(f, [votes[x] for x in ids[:2]])
        assert pending["status"] == "pending_gossip"
        _, r = _receipt_or_failure(f, [votes[ids[2]]], state=s,
                                   pins=propose_gossip_pins(s, f["trust"]))
        expected = "quorum_observed_no_authority"
    elif case == "duplicate_delivery_pending":
        _, r = _receipt_or_failure(f, [votes[ids[0]]] * 3); expected = "pending_gossip"
    elif case == "reversed_message_order_quorum":
        part = [ids[(rotation + n) % 4] for n in range(3)]
        _, r = _receipt_or_failure(f, [votes[x] for x in reversed(part)])
        expected = "quorum_observed_no_authority"
    elif case == "single_equivocating_signer_detected":
        witness = ids[rotation % 4]
        fork = sign_forged(dict(f["cp1"], audit_tip_sha256="f"*64), f["keys"][witness], witness)
        _, r = _receipt_or_failure(f, [votes[witness], fork]); expected = "withheld"
    elif case == "conflicting_overlapping_quorums_detected":
        cp = dict(f["cp1"], audit_tip_sha256="f"*64)
        malicious = [sign_forged(cp, f["keys"][x], x) for x in ids[1:]]
        _, r = _receipt_or_failure(f, [votes[x] for x in ids[:3]] + malicious)
        expected = "withheld"
    elif case == "two_corrupt_signers_cannot_form_quorum":
        _, r = _receipt_or_failure(f, [votes[x] for x in ids[:2]])
        expected = "pending_gossip"
    elif case == "observer_pin_rollback_withheld":
        s, _ = _receipt_or_failure(f, [votes[x] for x in ids[:2]])
        _, r = _receipt_or_failure(f, [votes[ids[2]]],
                                   pins=propose_gossip_pins(s, f["trust"]))
        expected = "withheld"
    elif case == "observer_pin_fork_withheld":
        pins = (f["gpins"][0], replace(f["gpins"][1], snapshot_sha256="f"*64))
        _, r = _receipt_or_failure(f, [votes[x] for x in ids[:3]], pins=pins)
        expected = "withheld"
    elif case == "signer_restart_rollback_rejected":
        from partition_reconciliation import _check_signer_pins
        old = new_signer_state(ids[0], f["cp0"])
        try:
            _check_signer_pins(old, propose_signer_pins(f["signer_states"][ids[0]], OBSERVERS),
                               f["trust"])
        except SyntheticRefusal:
            r = {"status": "withheld"}
        else:
            r = {"status": "invalid_unexpected_accept"}
        expected = "withheld"
    elif case == "valid_witness_restart_advances":
        state = json.loads(json.dumps(f["signer_states"][ids[0]]))
        log2 = f["log"] + [new_event(f["log"], "synthetic:event-4")]
        cp2 = make_cp(log2, 2, checkpoint_digest(f["cp1"]))
        v, s = signer_vote(state, propose_signer_pins(f["signer_states"][ids[0]], OBSERVERS),
                           cp2, log2, f["keys"][ids[0]], f["trust"])
        assert s["epoch"] == 2 and s["signed_vote_sha256"] == vote_digest(v)
        _, r = _receipt_or_failure(f, [votes[x] for x in ids[:3]])
        expected = "quorum_observed_no_authority"
    elif case == "invalid_signed_vote_refused":
        v = deepcopy(votes[ids[0]])
        v["payload"]["revocation_sha256"] = "d"*64
        _, r = _receipt_or_failure(f, [v]); expected = "withheld"
    elif case == "wrong_parent_replay_refused":
        v = sign_forged(dict(f["cp1"], previous_checkpoint_sha256="b"*64),
                        f["keys"][ids[0]], ids[0])
        _, r = _receipt_or_failure(f, [v]); expected = "withheld"
    elif case == "same_sequence_revocation_rewrite_refused":
        state = f["signer_states"][ids[0]]
        log2 = f["log"] + [new_event(f["log"], "synthetic:event-4", rev="d"*64)]
        cp2 = make_cp(log2, 2, checkpoint_digest(f["cp1"]), rev="d"*64, seq=2)
        try:
            signer_vote(state, propose_signer_pins(state, OBSERVERS), cp2, log2,
                        f["keys"][ids[0]], f["trust"])
        except SyntheticRefusal:
            r = {"status": "withheld"}
        else:
            r = {"status": "invalid_unexpected_accept"}
        expected = "withheld"
    elif case == "delayed_equivocation_evidence_persists":
        malicious = sign_forged(dict(f["cp1"], audit_tip_sha256="b"*64),
                                f["keys"][ids[0]], ids[0])
        s, _ = _receipt_or_failure(f, [votes[ids[0]], malicious])
        restored = json.loads(json.dumps(s))
        _, r = _receipt_or_failure(f, [votes[ids[1]]], state=restored,
                                   pins=propose_gossip_pins(s, f["trust"]))
        expected = "withheld"
    elif case == "compromised_keys_and_replaced_pins_known_limit":
        # Complete compromise means a fabricated alternative trust context can
        # verify its own narrative. The result still cannot grant source access.
        f2 = fixture()
        cp2 = dict(f2["cp1"], audit_tip_sha256="e"*64)
        crafted = [sign_forged(cp2, f2["keys"][x], x) for x in ids[:3]]
        _, r = _receipt_or_failure(f2, crafted)
        expected = "quorum_observed_no_authority"
    elif case == "permission_escalation_refused":
        cp2 = dict(f["cp1"], permission="read_original")
        state = new_signer_state(ids[0], f["cp0"])
        try:
            signer_vote(state, propose_signer_pins(state, OBSERVERS), cp2,
                        f["log"], f["keys"][ids[0]], f["trust"])
        except SyntheticRefusal:
            r = {"status": "withheld"}
        else:
            r = {"status": "invalid_unexpected_accept"}
        expected = "withheld"
    else:
        raise ValueError("unknown synthetic scenario")
    assert r["status"] == expected, (case, expected, r["status"])
    if "authority" in r:
        assert_no_authority(r)
    return expected


def run(iterations=360, seed=81081):
    if type(iterations) is not int or iterations < len(CASES) or iterations > 2000:
        raise ValueError("iterations must be bounded and include every scenario")
    if type(seed) is not int or seed < 0 or seed >= 2**32:
        raise ValueError("seed must be a bounded unsigned integer")
    rng = random.Random(seed)
    scenarios = list(CASES)
    results = {name: {"attempted": 0, "failures": 0,
                      "expected": ("quorum_observed_no_authority" if name in (
                          "partition_three_one_quorum_no_authority", "delayed_gossip_pending_then_quorum",
                          "reversed_message_order_quorum", "valid_witness_restart_advances",
                          "compromised_keys_and_replaced_pins_known_limit") else
                          "pending_gossip" if name in (
                          "partition_two_two_pending", "duplicate_delivery_pending",
                          "two_corrupt_signers_cannot_form_quorum") else "withheld")}
               for name in CASES}
    for i in range(iterations):
        name = scenarios[i] if i < len(CASES) else rng.choice(scenarios)
        try:
            state = execute_case(name, rotation=rng.randrange(4))
            ok = state == results[name]["expected"]
        except (ValueError, AssertionError, TypeError, KeyError):
            ok = False
        results[name]["attempted"] += 1
        if not ok:
            results[name]["failures"] += 1
    return {
        "schema": "un.synthetic-witness-partition-stress.v0",
        "synthetic_only": True, "seed": seed, "iterations": iterations,
        "cases": results, "failures": sum(v["failures"] for v in results.values()),
        "authority": "none", "authorized": False, "source_access": False,
        "publication_eligible": False, "delivery_eligible": False,
        "transcripts_opened": 0, "security_certified": False,
        "residual_risk": "full_key_and_observer_compromise_not_detectable",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=81081)
    parser.add_argument("--iterations", type=int, default=360)
    args = parser.parse_args(argv)
    root = args.output
    if root.is_symlink() or (root.exists() and (not root.is_dir() or any(root.iterdir()))):
        parser.error("output must be a fresh empty nonsymlink directory")
    result = run(iterations=args.iterations, seed=args.seed)
    assert result["failures"] == 0, "synthetic stress failures detected"
    root.mkdir(parents=True, mode=0o700, exist_ok=True)
    payload = (json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    (root / "manifest.json").write_bytes(payload)
    print("cases", len(result["cases"]), "iterations", result["iterations"],
          "failures", result["failures"], "manifest_sha256", sha256(payload).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
