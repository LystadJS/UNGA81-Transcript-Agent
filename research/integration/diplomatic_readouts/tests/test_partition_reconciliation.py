"""Synthetic-only partition, restart, non-equivocation and signed-gossip tests."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import json
import sys
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from partition_reconciliation import (
    AUDIENCE, NO_PERMISSION, ZERO, CHECKPOINT_SCHEMA, EVENT_SCHEMA,
    DOMAIN_EVENT, DOMAIN_VOTE, DOMAIN_LOG, VOTE_SCHEMA, _canon,
    checkpoint_digest, new_signer_state, signer_state_digest,
    propose_signer_pins, signer_vote, Keyring, ObserverPin,
    new_gossip_state, gossip_state_digest, propose_gossip_pins, GossipPin,
    reconcile_gossip, assert_no_authority, vote_digest, SyntheticRefusal,
)

REGISTRY = sha256(b"fictional registry").hexdigest()
REVOCATION = sha256(b"fictional revocation").hexdigest()
AUDIT_TIP = sha256(b"fictional audit tip").hexdigest()
OBSERVERS = ("synthetic:observer-east", "synthetic:observer-west")


def hash_event(ev):
    from partition_reconciliation import _event_digest
    return _event_digest(ev)


def new_event(log, label, rev=REVOCATION):
    e = {"schema": EVENT_SCHEMA, "index": len(log) + 1,
         "event_id": label, "kind": "audit_observed",
         "registry_sha256": REGISTRY, "revocation_sha256": rev,
         "occurred_at": "2026-10-15T%02d:00:00Z" % min(len(log), 22),
         "previous_sha256": log[-1]["event_sha256"] if log else ZERO}
    e["event_sha256"] = hash_event(e)
    return e


def make_cp(log, epoch, prev=ZERO, rev=REVOCATION, seq=2):
    from partition_reconciliation import _log_digest
    return {"schema": CHECKPOINT_SCHEMA, "fixture_kind": "synthetic",
            "registry_id": "synthetic:registry", "registry_sha256": REGISTRY,
            "audit_tip_sha256": AUDIT_TIP, "revocation_sha256": rev,
            "revocation_sequence": seq, "epoch": epoch,
            "log_length": len(log), "log_sha256": _log_digest(log),
            "log_tip_sha256": log[-1]["event_sha256"],
            "previous_checkpoint_sha256": prev, "audience": AUDIENCE,
            "signed_at": "2026-10-15T12:00:00Z",
            "expires_at": "2026-10-16T12:00:00Z",
            "permission": NO_PERMISSION}


def synthetic_key(label):
    return Ed25519PrivateKey.from_private_bytes(sha256(("FAKE-TEST-KEY:" + label).encode()).digest())


def pub(key):
    return key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def fixture():
    ids = [f"synthetic:witness-{i}" for i in range(4)]
    keys = {x: synthetic_key(x) for x in ids}
    trust = Keyring(keys={x: pub(keys[x]) for x in ids}, expected_ids=frozenset(ids),
                    observers=frozenset(OBSERVERS))
    log = [new_event([], "synthetic:event-1")]
    log.append(new_event(log, "synthetic:event-2"))
    cp0 = make_cp(log, epoch=0)
    log.append(new_event(log, "synthetic:event-3"))
    cp1 = make_cp(log, epoch=1, prev=checkpoint_digest(cp0))
    state = {x: new_signer_state(x, cp0) for x in ids}
    pins = {x: propose_signer_pins(state[x], OBSERVERS) for x in ids}
    votes = {}
    for x in ids:
        votes[x], state[x] = signer_vote(state[x], pins[x], cp1, log, keys[x], trust)
    gossip = new_gossip_state(0, checkpoint_digest(cp0))
    gpins = propose_gossip_pins(gossip, trust)
    return {"ids": ids, "keys": keys, "trust": trust, "log": log,
            "cp0": cp0, "cp1": cp1, "votes": votes, "signer_states": state,
            "gossip": gossip, "gpins": gpins}


def sign_forged(cp, key, witness_id):
    """Only for red-team tests: deliberately bypasses honest signer state."""
    from partition_reconciliation import _vote_payload
    import base64
    payload = _vote_payload(cp, witness_id)
    sig = key.sign(DOMAIN_VOTE + _canon({"key_id": witness_id, "payload": payload}))
    return {"schema": VOTE_SCHEMA, "key_id": witness_id, "payload": payload,
            "signature_b64": base64.b64encode(sig).decode("ascii")}


class WitnessPartitionTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture()

    def deliver(self, ids, state=None, pins=None, votes=None):
        f = self.f
        return reconcile_gossip(state or f["gossip"], pins or f["gpins"],
                                [votes[x] for x in ids] if votes is not None
                                else [f["votes"][x] for x in ids], f["trust"])

    def assertSafe(self, receipt):
        assert_no_authority(receipt)
        self.assertIs(receipt["authorized"], False)
        self.assertIs(receipt["can_read_source"], False)
        self.assertIs(receipt["publication_eligible"], False)
        self.assertIs(receipt["delivery_eligible"], False)
        self.assertEqual(receipt["holdout_lock"]["transcripts_opened"], 0)
        self.assertEqual(set(receipt["gate_status"].values()), {"NOT_RUN"})

    def test_01_three_of_four_quorum_is_only_no_authority(self):
        _, r = self.deliver(self.f["ids"][:3])
        self.assertEqual(r["status"], "quorum_observed_no_authority")
        self.assertEqual(r["signed_hosts"], 3)
        self.assertSafe(r)

    def test_02_full_four_host_quorum(self):
        _, r = self.deliver(self.f["ids"])
        self.assertEqual(r["signed_hosts"], 4)
        self.assertSafe(r)

    def test_03_two_two_partitions_have_no_quorum(self):
        for ids in (self.f["ids"][:2], self.f["ids"][2:]):
            _, r = self.deliver(ids)
            self.assertEqual(r["status"], "pending_gossip")
            self.assertEqual(r["signed_hosts"], 2)
            self.assertSafe(r)

    def test_04_delayed_gossip_recovers_quorum(self):
        s, r = self.deliver(self.f["ids"][:2])
        self.assertEqual(r["status"], "pending_gossip")
        pins = propose_gossip_pins(s, self.f["trust"])
        s2, r2 = self.deliver(self.f["ids"][2:3], s, pins)
        self.assertEqual(r2["status"], "quorum_observed_no_authority")
        self.assertSafe(r2)
        self.assertEqual(len(s2["votes"]), 3)

    def test_05_same_vote_replay_idempotent(self):
        ids = self.f["ids"][:2]
        s, _ = self.deliver(ids)
        pins = propose_gossip_pins(s, self.f["trust"])
        s2, r2 = self.deliver(ids, s, pins)
        self.assertEqual(len(s2["votes"]), 2)
        self.assertEqual(r2["status"], "pending_gossip")

    def test_06_message_order_does_not_change_digest(self):
        s1, _ = self.deliver(self.f["ids"][:3])
        s2, _ = self.deliver(list(reversed(self.f["ids"][:3])))
        self.assertEqual(gossip_state_digest(s1, self.f["trust"]),
                         gossip_state_digest(s2, self.f["trust"]))

    def test_07_source_access_never_in_quorum_receipt(self):
        _, r = self.deliver(self.f["ids"])
        data = json.dumps(r)
        for forbidden in ('"source_url"', '"original_bytes": {', '"private_key"', '"transcript"'):
            self.assertNotIn(forbidden, data)
        self.assertSafe(r)

    def test_08_older_gossip_state_rolls_back_after_restart(self):
        s, _ = self.deliver(self.f["ids"][:2])
        pins = propose_gossip_pins(s, self.f["trust"])
        _, r = self.deliver(self.f["ids"][2:3], self.f["gossip"], pins)
        self.assertEqual(r["reason_codes"], ["gossip_state_rollback_or_fork"])

    def test_09_one_observer_missing_withholds(self):
        _, r = self.deliver(self.f["ids"][:3], pins=self.f["gpins"][:1])
        self.assertEqual(r["reason_codes"], ["gossip_observer_pins_missing"])

    def test_10_observer_disagreement_withholds(self):
        pins = (self.f["gpins"][0], replace(self.f["gpins"][1], snapshot_sha256="e"*64))
        _, r = self.deliver(self.f["ids"][:3], pins=pins)
        self.assertEqual(r["reason_codes"], ["gossip_state_rollback_or_fork"])

    def test_11_honest_signer_rejects_same_epoch_equivocation(self):
        f = self.f
        cp = deepcopy(f["cp1"])
        cp["audit_tip_sha256"] = "e"*64
        newpins = propose_signer_pins(f["signer_states"][f["ids"][0]], OBSERVERS)
        with self.assertRaisesRegex(SyntheticRefusal, "signer_non_equivocation_or_revocation_rollback"):
            signer_vote(f["signer_states"][f["ids"][0]], newpins, cp, f["log"],
                        f["keys"][f["ids"][0]], f["trust"])

    def test_12_honest_signer_rejects_old_epoch(self):
        f = self.f
        pins = propose_signer_pins(f["signer_states"][f["ids"][0]], OBSERVERS)
        with self.assertRaises(SyntheticRefusal):
            signer_vote(f["signer_states"][f["ids"][0]], pins,
                        f["cp0"], f["log"][:2], f["keys"][f["ids"][0]], f["trust"])

    def test_13_honest_signer_rejects_wrong_host_private_key(self):
        f = self.f
        id0 = f["ids"][0]
        pins = propose_signer_pins(f["signer_states"][id0], OBSERVERS)
        log2 = f["log"] + [new_event(f["log"], "synthetic:event-4")]
        cp2 = make_cp(log2, 2, checkpoint_digest(f["cp1"]))
        with self.assertRaisesRegex(SyntheticRefusal, "test_signer_key_untrusted"):
            signer_vote(f["signer_states"][id0], pins, cp2, log2,
                        f["keys"][f["ids"][1]], f["trust"])

    def test_14_honest_signer_advance_one_epoch(self):
        f = self.f
        id0 = f["ids"][0]
        pins = propose_signer_pins(f["signer_states"][id0], OBSERVERS)
        log2 = f["log"] + [new_event(f["log"], "synthetic:event-4")]
        cp2 = make_cp(log2, 2, checkpoint_digest(f["cp1"]))
        v2, s2 = signer_vote(f["signer_states"][id0], pins, cp2, log2,
                             f["keys"][id0], f["trust"])
        self.assertEqual(s2["epoch"], 2)
        self.assertEqual(s2["signed_vote_sha256"], vote_digest(v2))
        self.assertEqual(s2["checkpoint_sha256"], checkpoint_digest(cp2))

    def test_15_honest_signer_rejects_higher_epoch_skip(self):
        f = self.f
        id0 = f["ids"][0]
        pins = propose_signer_pins(f["signer_states"][id0], OBSERVERS)
        with self.assertRaises(SyntheticRefusal):
            signer_vote(f["signer_states"][id0], pins,
                        dict(f["cp1"], epoch=3), f["log"], f["keys"][id0], f["trust"])

    def test_16_honest_signer_refuses_changed_revocation_same_sequence(self):
        f = self.f
        id0 = f["ids"][0]
        pins = propose_signer_pins(f["signer_states"][id0], OBSERVERS)
        log2 = f["log"] + [new_event(f["log"], "synthetic:event-4", "f"*64)]
        cp2 = make_cp(log2, 2, checkpoint_digest(f["cp1"]), rev="f"*64, seq=2)
        with self.assertRaisesRegex(SyntheticRefusal, "signer_non_equivocation_or_revocation_rollback"):
            signer_vote(f["signer_states"][id0], pins, cp2, log2,
                        f["keys"][id0], f["trust"])

    def test_17_honest_signer_allows_sequence_advance(self):
        f = self.f
        id0 = f["ids"][0]
        pins = propose_signer_pins(f["signer_states"][id0], OBSERVERS)
        log2 = f["log"] + [new_event(f["log"], "synthetic:event-4", "f"*64)]
        cp2 = make_cp(log2, 2, checkpoint_digest(f["cp1"]), rev="f"*64, seq=3)
        _, s2 = signer_vote(f["signer_states"][id0], pins, cp2, log2,
                            f["keys"][id0], f["trust"])
        self.assertEqual(s2["revocation_sequence"], 3)
        self.assertEqual(s2["revocation_sha256"], "f"*64)

    def test_18_honest_signer_rejects_rewritten_log_prefix(self):
        f = self.f
        id0 = f["ids"][0]
        pins = propose_signer_pins(f["signer_states"][id0], OBSERVERS)
        old = [new_event([], "synthetic:evil-1")]
        old.append(new_event(old, "synthetic:event-2"))
        old.append(new_event(old, "synthetic:event-3"))
        old.append(new_event(old, "synthetic:event-4"))
        cp2 = make_cp(old, 2, checkpoint_digest(f["cp1"]))
        with self.assertRaisesRegex(SyntheticRefusal, "signer_log_prefix_fork_or_rollback"):
            signer_vote(f["signer_states"][id0], pins, cp2, old,
                        f["keys"][id0], f["trust"])

    def test_19_host_state_restart_with_original_pin_fails_after_advancement(self):
        f = self.f
        id0 = f["ids"][0]
        prior = new_signer_state(id0, f["cp0"])
        latestpins = propose_signer_pins(f["signer_states"][id0], OBSERVERS)
        with self.assertRaisesRegex(SyntheticRefusal, "signer_rollback_or_fork_detected"):
            from partition_reconciliation import _check_signer_pins
            _check_signer_pins(prior, latestpins, f["trust"])

    def test_20_honest_signer_can_restart_with_independently_pinned_latest(self):
        f = self.f
        id0 = f["ids"][0]
        restored = json.loads(json.dumps(f["signer_states"][id0]))
        pins = propose_signer_pins(f["signer_states"][id0], OBSERVERS)
        log2 = f["log"] + [new_event(f["log"], "synthetic:event-4")]
        cp2 = make_cp(log2, 2, checkpoint_digest(f["cp1"]))
        _, state2 = signer_vote(restored, pins, cp2, log2, f["keys"][id0], f["trust"])
        self.assertEqual(state2["epoch"], 2)

    def test_21_malicious_witness_double_sign_detected_from_delayed_gossip(self):
        f = self.f
        bad = deepcopy(f["cp1"])
        bad["audit_tip_sha256"] = "f"*64
        adversary = f["ids"][0]
        vbad = sign_forged(bad, f["keys"][adversary], adversary)
        s, r = self.deliver(f["ids"][:3])
        self.assertEqual(r["status"], "quorum_observed_no_authority")
        pins = propose_gossip_pins(s, f["trust"])
        s2, r2 = reconcile_gossip(s, pins, [vbad], f["trust"])
        self.assertEqual(r2["status"], "withheld")
        self.assertEqual(r2["reason_codes"], ["witness_equivocation_evidence"])
        self.assertTrue(r2["fork_evidence_sha256"])
        self.assertEqual(len(s2["equivocations"]), 1)
        self.assertSafe(r2)

    def test_22_gossip_equivocation_evidence_survives_restart(self):
        f = self.f
        bad = dict(f["cp1"], audit_tip_sha256="e"*64)
        actor = f["ids"][0]
        vbad = sign_forged(bad, f["keys"][actor], actor)
        s, _ = reconcile_gossip(f["gossip"], f["gpins"],
                                [f["votes"][actor], vbad], f["trust"])
        restored = json.loads(json.dumps(s))
        pins = propose_gossip_pins(s, f["trust"])
        s2, r = reconcile_gossip(restored, pins, [f["votes"][f["ids"][1]]], f["trust"])
        self.assertEqual(r["reason_codes"], ["witness_equivocation_evidence"])
        self.assertEqual(s2["equivocations"], s["equivocations"])

    def test_23_evidence_drop_detected_by_observer_pin(self):
        f = self.f
        bad = dict(f["cp1"], audit_tip_sha256="d"*64)
        actor = f["ids"][0]
        vbad = sign_forged(bad, f["keys"][actor], actor)
        s, _ = reconcile_gossip(f["gossip"], f["gpins"],
                                [f["votes"][actor], vbad], f["trust"])
        pins = propose_gossip_pins(s, f["trust"])
        forged = json.loads(json.dumps(s))
        forged["equivocations"] = []
        _, r = reconcile_gossip(forged, pins, [], f["trust"])
        self.assertEqual(r["reason_codes"], ["gossip_fork_evidence_incomplete_or_fabricated"])

    def test_24_gossip_corrupted_signature_withheld(self):
        f = self.f
        v = deepcopy(f["votes"][f["ids"][0]])
        v["signature_b64"] = "!"*88
        _, r = reconcile_gossip(f["gossip"], f["gpins"], [v], f["trust"])
        self.assertEqual(r["status"], "withheld")

    def test_25_two_conflicting_three_host_quorums_withhold(self):
        f = self.f
        b = dict(f["cp1"], audit_tip_sha256="e"*64)
        votes = [f["votes"][x] for x in f["ids"][:3]]
        votes += [sign_forged(b, f["keys"][x], x) for x in f["ids"][1:]]
        s, r = reconcile_gossip(f["gossip"], f["gpins"], votes, f["trust"])
        self.assertEqual(r["reason_codes"], ["witness_equivocation_evidence"])
        self.assertEqual(len(s["equivocations"]), 2)

    def test_26_two_attacker_hosts_cannot_get_honest_quorum(self):
        _, r = self.deliver(self.f["ids"][1:3])
        self.assertEqual(r["status"], "pending_gossip")

    def test_27_multiple_host_signed_forks_detected(self):
        f = self.f
        b = dict(f["cp1"], audit_tip_sha256="f"*64)
        forged = [sign_forged(b, f["keys"][x], x) for x in f["ids"][:2]]
        ids = f["ids"][:3]
        s, r = reconcile_gossip(f["gossip"], f["gpins"],
                                [f["votes"][x] for x in ids] + forged, f["trust"])
        self.assertEqual(r["status"], "withheld")
        self.assertEqual(len(s["equivocations"]), 2)

    def test_28_gossip_from_wrong_epoch_withheld(self):
        f = self.f
        bad = dict(f["cp1"], epoch=2)
        actor = f["ids"][0]
        vbad = sign_forged(bad, f["keys"][actor], actor)
        _, r = reconcile_gossip(f["gossip"], f["gpins"], [vbad], f["trust"])
        self.assertEqual(r["reason_codes"], ["gossip_wrong_parent_or_epoch"])

    def test_29_gossip_from_wrong_parent_withheld(self):
        f = self.f
        bad = dict(f["cp1"], previous_checkpoint_sha256="f"*64)
        actor = f["ids"][0]
        vbad = sign_forged(bad, f["keys"][actor], actor)
        _, r = reconcile_gossip(f["gossip"], f["gpins"], [vbad], f["trust"])
        self.assertEqual(r["reason_codes"], ["gossip_wrong_parent_or_epoch"])

    def test_30_signed_cross_audience_or_permission_withheld(self):
        f = self.f
        actor = f["ids"][0]
        for field, value in (("audience", "synthetic:another"),
                             ("permission", "source_read"),
                             ("fixture_kind", "private")):
            with self.subTest(field=field):
                vote = sign_forged(f["cp1"], f["keys"][actor], actor)
                vote["payload"][field] = value
                _, r = reconcile_gossip(f["gossip"], f["gpins"], [vote], f["trust"])
                self.assertEqual(r["status"], "withheld")

    def test_31_signer_state_extra_private_field_rejected(self):
        f = self.f
        actor = f["ids"][0]
        st = dict(f["signer_states"][actor], original_bytes="secret")
        with self.assertRaises(SyntheticRefusal):
            signer_state_digest(st)

    def test_32_gossip_duplicate_public_key_identity_rejected(self):
        f = self.f
        keys = dict(f["trust"].keys)
        keys[f["ids"][1]] = keys[f["ids"][0]]
        trust = replace(f["trust"], keys=keys)
        _, r = reconcile_gossip(f["gossip"], f["gpins"],
                                [f["votes"][f["ids"][0]]], trust)
        self.assertEqual(r["reason_codes"], ["witness_trust_invalid"])

    def test_33_gossip_evidence_cannot_be_invented_by_unpinned_state(self):
        f = self.f
        fake = dict(f["gossip"], equivocations=["d"*64])
        _, r = reconcile_gossip(fake, f["gpins"], [], f["trust"])
        self.assertEqual(r["status"], "withheld")

    def test_34_mutating_vote_under_valid_signature_rejected(self):
        f = self.f
        v = deepcopy(f["votes"][f["ids"][0]])
        v["payload"]["revocation_sha256"] = "f"*64
        _, r = reconcile_gossip(f["gossip"], f["gpins"], [v], f["trust"])
        self.assertEqual(r["reason_codes"], ["gossip_signature_invalid"])

    def test_35_invalid_host_alias_rejected(self):
        f = self.f
        v = deepcopy(f["votes"][f["ids"][0]])
        v["key_id"] = f["ids"][1]
        _, r = reconcile_gossip(f["gossip"], f["gpins"], [v], f["trust"])
        self.assertEqual(r["status"], "withheld")

    def test_36_duplicate_delivery_does_not_increase_quorum(self):
        f = self.f
        one = f["votes"][f["ids"][0]]
        s, r = reconcile_gossip(f["gossip"], f["gpins"], [one, one, one], f["trust"])
        self.assertEqual(r["status"], "pending_gossip")
        self.assertEqual(r["signed_hosts"], 1)
        self.assertEqual(len(s["votes"]), 1)

    def test_37_evidence_from_prior_gossip_is_not_cleared(self):
        f = self.f
        adversary = f["ids"][0]
        bad = sign_forged(dict(f["cp1"], audit_tip_sha256="a"*64),
                          f["keys"][adversary], adversary)
        s, r = reconcile_gossip(f["gossip"], f["gpins"],
                                [f["votes"][adversary], bad], f["trust"])
        self.assertTrue(s["equivocations"])
        pins = propose_gossip_pins(s, f["trust"])
        _, later = reconcile_gossip(s, pins, [f["votes"][f["ids"][1]]], f["trust"])
        self.assertEqual(later["status"], "withheld")
        self.assertEqual(later["fork_evidence_sha256"], r["fork_evidence_sha256"])

    def test_38_signed_vote_canonical_digest_deterministic(self):
        v = self.f["votes"][self.f["ids"][0]]
        self.assertEqual(vote_digest(v), vote_digest(deepcopy(v)))

    def test_39_empty_gossip_is_pending_no_authority(self):
        _, r = self.deliver([])
        self.assertEqual(r["status"], "pending_gossip")
        self.assertEqual(r["signed_hosts"], 0)
        self.assertSafe(r)

    def test_40_staged_original_multi_host_checkpoint_compatibility(self):
        # The existing checkpoint contract uses the same domain and JSON basis.
        try:
            from multi_host_witness import checkpoint_digest as accepted_digest
            from multi_host_witness import log_digest as accepted_log_digest
        except ImportError:
            self.skipTest("Full pinned PR89 source checkout needed for native interoperability")
        f = self.f
        self.assertEqual(checkpoint_digest(f["cp1"]), accepted_digest(f["cp1"]))
        from partition_reconciliation import _log_digest
        self.assertEqual(_log_digest(f["log"]), accepted_log_digest(f["log"]))


    def test_41_fork_evidence_list_rejected_even_with_self_generated_pins(self):
        f = self.f
        actor = f["ids"][0]
        bad = sign_forged(dict(f["cp1"], audit_tip_sha256="a"*64),
                          f["keys"][actor], actor)
        s, _ = reconcile_gossip(f["gossip"], f["gpins"],
                                [f["votes"][actor], bad], f["trust"])
        s["equivocations"] = []
        _, r = reconcile_gossip(s, f["gpins"], [], f["trust"])
        self.assertEqual(r["reason_codes"],
                         ["gossip_fork_evidence_incomplete_or_fabricated"])

    def test_42_gossip_extra_secret_key_rejected(self):
        f = self.f
        s = dict(f["gossip"], original_source_passage="private text")
        _, r = reconcile_gossip(s, f["gpins"], [], f["trust"])
        self.assertEqual(r["status"], "withheld")
        self.assertSafe(r)
        self.assertNotIn("private text", json.dumps(r))

    def test_43_schema_compatible_no_authority_receipts(self):
        from jsonschema import Draft202012Validator
        schema = json.loads((HERE / "partition_reconciliation.v0.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        _, good = self.deliver(self.f["ids"][:3])
        _, pending = self.deliver(self.f["ids"][:2])
        _, bad = self.deliver(self.f["ids"][:1], pins=self.f["gpins"][:1])
        for item in (good, pending, bad):
            self.assertEqual(list(validator.iter_errors(item)), [])
        upgraded = dict(good, publication_eligible=True)
        self.assertTrue(list(validator.iter_errors(upgraded)))
        upgraded = deepcopy(good)
        upgraded["gate_status"]["source_registry"] = "PASS"
        self.assertTrue(list(validator.iter_errors(upgraded)))

    def test_44_stress_repeatability_and_no_authority(self):
        from stress_partition import run, CASES
        a = run(iterations=36, seed=81081)
        b = run(iterations=36, seed=81081)
        self.assertEqual(a, b)
        self.assertEqual(a["failures"], 0)
        self.assertEqual(len(a["cases"]), len(CASES))
        self.assertFalse(a["authorized"])
        self.assertFalse(a["source_access"])
        self.assertFalse(a["publication_eligible"])
        self.assertEqual(a["transcripts_opened"], 0)

    def test_45_stress_invalid_controls_rejected(self):
        from stress_partition import run
        for iterations in (True, 0, -1, 17, 2001):
            with self.subTest(iterations=iterations):
                with self.assertRaises(ValueError):
                    run(iterations=iterations)
        for seed in (True, -1, 2**32):
            with self.subTest(seed=seed):
                with self.assertRaises(ValueError):
                    run(iterations=20, seed=seed)

    def test_46_compromised_witness_quorum_alone_is_never_authorization(self):
        f = self.f
        bad_cp = dict(f["cp1"], audit_tip_sha256="f"*64)
        corrupted = [sign_forged(bad_cp, f["keys"][x], x)
                     for x in f["ids"][:3]]
        # Three compromised witness signing keys can attest a forged checkpoint
        # digest that gossip alone does not resolve to validated source/log data.
        # An observed quorum is *never* source, review or release authority.
        _, receipt = reconcile_gossip(f["gossip"], f["gpins"], corrupted, f["trust"])
        self.assertEqual(receipt["status"], "quorum_observed_no_authority")
        self.assertSafe(receipt)


if __name__ == "__main__":
    unittest.main()
