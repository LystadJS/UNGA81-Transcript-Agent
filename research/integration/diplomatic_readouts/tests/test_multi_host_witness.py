"""Independent synthetic multi-host audit and revocation witness stress tests.

Public test-only keys and fictitious metadata. All accepted outcomes are
strictly ZERO authority; no real-source network or private corpus operations.
"""
from __future__ import annotations

from dataclasses import replace, asdict
from copy import deepcopy
from hashlib import sha256
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from multi_host_witness import (
    AUDIENCE, DOMAIN_ATTEST, ATTESTATION_SCHEMA, CHECKPOINT_SCHEMA,
    WitnessTrust, WitnessObserverPin, new_log_event, log_digest,
    checkpoint_digest, propose_observer_pins, assert_no_authority,
    verify_multi_host,
)
from synthetic_signatures import REVOCATION_SCHEMA, content_digest, ZERO_PERMISSIONS
from test_synthetic_signatures import fixture as source_fixture, resign_revocation, resign_custody
from test_registry_preflight import WHEN

OBSERVER_IDS = ("synthetic:observer-east", "synthetic:observer-west")


def test_key(label: str) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(
        sha256(("PUBLIC FICTIONAL TEST KEY / " + label).encode()).digest())


def raw_public(key) -> bytes:
    return key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)


def attest(cp: dict, host_id: str, key: Ed25519PrivateKey) -> dict:
    signed = json.dumps({"key_id": host_id, "payload": cp}, sort_keys=True,
                        separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return {"schema": ATTESTATION_SCHEMA, "key_id": host_id,
            "payload": deepcopy(cp),
            "signature_b64": base64.b64encode(key.sign(DOMAIN_ATTEST + signed)).decode("ascii")}


def fictional_fixture():
    source = source_fixture()
    trust = source["trust"]
    registry_sha = trust.expected_registry_sha256
    revoke_sha = content_digest(REVOCATION_SCHEMA, source["revocation"]["payload"])
    log = []
    for id_, kind, when in (
        ("synthetic:event1", "registry_checked", "2026-10-14T01:00:00Z"),
        ("synthetic:event2", "revocation_checkpoint", "2026-10-14T02:00:00Z"),
    ):
        log.append(new_log_event(log, id_, kind, registry_sha, revoke_sha, when))
    cp0 = {"schema": CHECKPOINT_SCHEMA, "fixture_kind": "synthetic",
           "registry_id": trust.expected_registry_id,
           "registry_sha256": registry_sha,
           "audit_tip_sha256": trust.expected_audit_tip_sha256,
           "revocation_sha256": revoke_sha,
           "revocation_sequence": source["revocation"]["payload"]["sequence"],
           "epoch": 0, "log_length": len(log), "log_sha256": log_digest(log),
           "log_tip_sha256": log[-1]["event_sha256"],
           "previous_checkpoint_sha256": "0"*64,
           "audience": AUDIENCE, "signed_at": "2026-10-14T02:15:00Z",
           "expires_at": "2026-10-15T02:15:00Z",
           "permission": ZERO_PERMISSIONS}
    observer_pins = propose_observer_pins(cp0, OBSERVER_IDS)
    log.append(new_log_event(log, "synthetic:event3", "audit_observed",
                             registry_sha, revoke_sha, "2026-10-15T01:00:00Z"))
    cp = deepcopy(cp0)
    cp.update(epoch=1, previous_checkpoint_sha256=checkpoint_digest(cp0),
              log_length=len(log), log_sha256=log_digest(log),
              log_tip_sha256=log[-1]["event_sha256"],
              signed_at="2026-10-15T02:00:00Z", expires_at="2026-10-16T02:00:00Z")
    ids = [f"synthetic:witness-{i}" for i in range(4)]
    keys = {kid: test_key(kid) for kid in ids}
    witness_trust = WitnessTrust(public_keys={k: raw_public(keys[k]) for k in ids},
                                 expected_host_ids=frozenset(ids),
                                 observer_ids=frozenset(OBSERVER_IDS))
    attestations = [attest(cp, kid, keys[kid]) for kid in ids[:3]]
    return dict(source=source, log=log, checkpoint=cp, pins=observer_pins,
                witness_trust=witness_trust, keys=keys, ids=ids,
                attestations=attestations, gossip=[])


def inspect(f):
    src = f["source"]
    out = verify_multi_host(src["snapshot"], src["policy"], src["events"],
                            src["proposal"], src["custody"], src["revocation"],
                            checked_at=WHEN, source_trust=src["trust"],
                            witness_trust=f["witness_trust"],
                            observer_pins=f["pins"], log_entries=f["log"],
                            checkpoint=f["checkpoint"],
                            attestations=f["attestations"], gossip=f["gossip"])
    assert_no_authority(out)
    return out


def resign_host(f, ids=None):
    ids = f["ids"][:3] if ids is None else ids
    f["attestations"] = [attest(f["checkpoint"], kid, f["keys"][kid]) for kid in ids]


class MultiHostSyntheticTests(unittest.TestCase):
    def setUp(self):
        self.f = fictional_fixture()

    def withhold(self, reason=None):
        out = inspect(self.f)
        self.assertEqual(out["status"], "withheld")
        self.assertEqual(set(out["gate_status"].values()), {"NOT_RUN"})
        if reason:
            self.assertEqual(out["reason_codes"], [reason])
        self.assertFalse(out["can_read_source"])
        self.assertIsNone(out["checkpoint_sha256"])
        return out

    def test_01_quorum_three_of_four_is_only_synthetic_consistency(self):
        x = inspect(self.f)
        self.assertEqual(x["status"], "synthetic_quorum_consistent_no_authority")
        self.assertEqual(x["quorum_size"], 3)
        self.assertEqual(x["epoch"], 1)
        for name in ("can_read_source", "can_issue_review", "statistical_eligible",
                     "authorized", "delivery_eligible", "publication_eligible"):
            self.assertIs(x[name], False)
        self.assertEqual(x["holdout_lock"]["transcripts_opened"], 0)

    def test_02_all_four_witnesses_valid(self):
        resign_host(self.f, self.f["ids"])
        self.assertEqual(inspect(self.f)["quorum_size"], 4)

    def test_03_two_witnesses_cannot_form_quorum(self):
        self.f["attestations"] = self.f["attestations"][:2]
        self.withhold("witness_insufficient_quorum")

    def test_04_same_signer_repeated_cannot_form_quorum(self):
        self.f["attestations"][2] = deepcopy(self.f["attestations"][0])
        self.withhold("witness_duplicate_host")

    def test_05_missing_observer_denied(self):
        self.f["pins"] = self.f["pins"][:1]
        self.withhold("observer_pins_missing")

    def test_06_two_observers_disagree_on_tip(self):
        pins = self.f["pins"]
        self.f["pins"] = (pins[0], replace(pins[1], log_tip_sha256="f"*64))
        self.withhold("observer_checkpoint_fork_detected")

    def test_07_observer_relabel_denied(self):
        pins = self.f["pins"]
        self.f["pins"] = (pins[0], replace(pins[1], observer_id="synthetic:impostor"))
        self.withhold("observer_identity_mismatch")

    def test_08_fork_rewrite_old_log_prefix_detected(self):
        row = self.f["log"][0]
        row["event_id"] = "synthetic:rewritten"
        # We intentionally do not amend hashes, which must also be rejected.
        self.withhold("witness_log_integrity_invalid")

    def test_09_valid_rehashed_old_prefix_cannot_replace_pinned_prefix(self):
        f = self.f
        fork = []
        for i, row in enumerate(f["log"]):
            event_id = "synthetic:forked-genesis" if i == 0 else row["event_id"]
            fork.append(new_log_event(fork, event_id, row["kind"], row["registry_sha256"],
                                      row["revocation_sha256"], row["occurred_at"]))
        f["log"] = fork
        f["checkpoint"]["log_sha256"] = log_digest(fork)
        f["checkpoint"]["log_tip_sha256"] = fork[-1]["event_sha256"]
        resign_host(f)
        self.withhold("witness_log_prefix_fork_or_rollback")

    def test_10_host_attestation_signature_tamper(self):
        self.f["attestations"][1]["signature_b64"] = self.f["attestations"][0]["signature_b64"]
        self.withhold("witness_signature_invalid")

    def test_11_host_id_alias_without_resigning(self):
        self.f["attestations"][0]["key_id"] = self.f["ids"][3]
        self.withhold("witness_signature_invalid")

    def test_12_checkpoint_host_specific_split_view(self):
        self.f["attestations"][0]["payload"]["log_tip_sha256"] = "f"*64
        self.withhold("witness_signature_invalid")

    def test_13_separate_signed_fork_gossip_detected(self):
        f = self.f
        divergent = deepcopy(f["checkpoint"])
        divergent["log_tip_sha256"] = "e"*64
        f["gossip"] = [attest(divergent, f["ids"][3], f["keys"][f["ids"][3]])]
        self.withhold("witness_gossip_fork_detected")

    def test_14_gossip_corrupted_signature_refused(self):
        f = self.f
        v = deepcopy(f["attestations"][0])
        v["signature_b64"] = "X"*88
        f["gossip"] = [v]
        self.withhold("witness_signature_invalid")

    def test_15_signed_checkpoint_wrong_registry(self):
        f = self.f
        f["checkpoint"]["registry_sha256"] = "f"*64
        resign_host(f)
        self.withhold("witness_checkpoint_binding_mismatch")

    def test_16_signed_checkpoint_wrong_revocation(self):
        f = self.f
        f["checkpoint"]["revocation_sha256"] = "f"*64
        resign_host(f)
        self.withhold("witness_checkpoint_binding_mismatch")

    def test_17_replay_epoch_denied_even_if_resigned_by_three(self):
        f = self.f
        f["checkpoint"]["epoch"] = 0
        resign_host(f)
        self.withhold("witness_checkpoint_binding_mismatch")

    def test_18_observer_state_restored_from_old_checkpoint_is_refused(self):
        f = self.f
        next_pins = propose_observer_pins(f["checkpoint"], OBSERVER_IDS)
        f["pins"] = next_pins  # now independent hosts persisted epoch 1
        # Reusing same old signed epoch 1 cannot advance to epoch 2.
        self.withhold("witness_log_prefix_fork_or_rollback")

    def test_19_next_epoch_valid_append_extension(self):
        f = self.f
        f["pins"] = propose_observer_pins(f["checkpoint"], OBSERVER_IDS)
        f["log"].append(new_log_event(f["log"], "synthetic:event4", "audit_observed",
                                      f["checkpoint"]["registry_sha256"],
                                      f["checkpoint"]["revocation_sha256"],
                                      "2026-10-15T02:30:00Z"))
        previous = deepcopy(f["checkpoint"])
        f["checkpoint"].update(epoch=2, log_length=len(f["log"]),
                               log_sha256=log_digest(f["log"]),
                               log_tip_sha256=f["log"][-1]["event_sha256"],
                               previous_checkpoint_sha256=checkpoint_digest(previous),
                               signed_at="2026-10-15T03:00:00Z", expires_at="2026-10-16T03:00:00Z")
        resign_host(f)
        x = inspect(f)
        self.assertEqual(x["epoch"], 2)
        self.assertEqual(x["log_length"], 4)
        self.assertFalse(x["authorized"])

    def test_20_observer_fork_blocks_valid_new_epoch(self):
        f = self.f
        base_pins = propose_observer_pins(f["checkpoint"], OBSERVER_IDS)
        f["pins"] = (base_pins[0], replace(base_pins[1], checkpoint_sha256="a"*64))
        self.withhold("observer_checkpoint_fork_detected")

    def test_21_checkpoint_expiry(self):
        f = self.f
        f["checkpoint"]["expires_at"] = "2026-10-15T02:30:00Z"
        resign_host(f)
        self.withhold("witness_checkpoint_time_invalid")

    def test_22_freshness_beyond_one_day_denied(self):
        f = self.f
        f["checkpoint"]["expires_at"] = "2026-10-20T00:00:00Z"
        resign_host(f)
        self.withhold("witness_checkpoint_time_invalid")

    def test_23_trust_key_material_shared_with_custody_denied(self):
        f = self.f
        ids = f["ids"]
        keys = dict(f["witness_trust"].public_keys)
        keys[ids[0]] = next(iter(f["source"]["trust"].custodian_keys.values()))
        f["witness_trust"] = replace(f["witness_trust"], public_keys=keys)
        self.withhold("witness_role_key_collision")

    def test_24_trust_duplicate_witness_public_key_denied(self):
        f = self.f
        ids = f["ids"]
        keys = dict(f["witness_trust"].public_keys)
        keys[ids[1]] = keys[ids[0]]
        f["witness_trust"] = replace(f["witness_trust"], public_keys=keys)
        self.withhold("independent_witness_trust_missing")

    def test_25_compromise_two_witness_keys_cannot_fake_quorum(self):
        f = self.f
        divergent = deepcopy(f["checkpoint"])
        divergent["log_tip_sha256"] = "a"*64
        f["attestations"] = [attest(divergent, k, f["keys"][k]) for k in f["ids"][:2]]
        self.withhold("witness_insufficient_quorum")

    def test_26_both_custodian_and_revocation_signers_cannot_rewrite_honest_witness_tip(self):
        f = self.f
        source = f["source"]
        source["custody"]["payload"]["issued_at"] = "2026-10-14T01:00:00Z"
        resign_custody(source)
        source["revocation"]["payload"]["observed_at"] = "2026-10-14T03:00:00Z"
        resign_revocation(source)
        # Even though both signatures are now internally valid, independent
        # audit/revocation pins in observers and witness commitments are not.
        self.withhold("witness_revocation_log_tip_mismatch")

    def test_27_full_compromise_of_pins_plus_quorum_is_undetectable_but_still_no_access(self):
        # If the attacker also rewrites both independent observer states and
        # holds three synthetic witness private keys, forged history can appear
        # consistent. That is a LIMITATION, not a successful security defense.
        f = self.f
        src = f["source"]
        src["revocation"]["payload"]["observed_at"] = "2026-10-14T03:00:00Z"
        resign_revocation(src)
        revhash = content_digest(REVOCATION_SCHEMA, src["revocation"]["payload"])
        fake_log = []
        for id_, kind, when in (
            ("synthetic:forged1", "registry_checked", "2026-10-14T01:00:00Z"),
            ("synthetic:forged2", "revocation_checkpoint", "2026-10-14T02:00:00Z"),
        ):
            fake_log.append(new_log_event(fake_log, id_, kind,
                                          src["trust"].expected_registry_sha256,
                                          revhash, when))
        old = deepcopy(f["checkpoint"])
        old["epoch"] = 0
        old["log_length"] = 2
        old["log_sha256"] = log_digest(fake_log)
        old["log_tip_sha256"] = fake_log[-1]["event_sha256"]
        old["revocation_sha256"] = revhash
        f["pins"] = propose_observer_pins(old, OBSERVER_IDS)
        fake_log.append(new_log_event(fake_log, "synthetic:forged3", "audit_observed",
                                      src["trust"].expected_registry_sha256,
                                      revhash, "2026-10-15T01:00:00Z"))
        f["log"] = fake_log
        f["checkpoint"].update(revocation_sha256=revhash,
                                previous_checkpoint_sha256=checkpoint_digest(old),
                                log_length=3, log_sha256=log_digest(fake_log),
                                log_tip_sha256=fake_log[-1]["event_sha256"])
        resign_host(f)  # adversary holds witness quorum and pins too
        out = inspect(f)
        self.assertEqual(out["status"], "synthetic_quorum_consistent_no_authority")
        self.assertIs(out["can_read_source"], False)
        self.assertIs(out["publication_eligible"], False)

    def test_28_missing_prefix_event_is_rejected(self):
        f = self.f
        f["log"] = f["log"][1:]
        self.withhold("witness_log_integrity_invalid")

    def test_29_duplicate_event_id_is_rejected(self):
        f = self.f
        f["log"][2]["event_id"] = f["log"][0]["event_id"]
        f["log"][2]["event_sha256"] = __import__("multi_host_witness").event_digest(f["log"][2])
        self.withhold("witness_log_integrity_invalid")

    def test_30_cross_audience_message_is_rejected(self):
        f = self.f
        f["checkpoint"]["audience"] = "synthetic:other-audience"
        resign_host(f)
        self.withhold("witness_checkpoint_binding_mismatch")

    def test_31_insufficient_log_freshness(self):
        f = self.f
        f["log"][2]["occurred_at"] = "2026-10-16T01:00:00Z"
        self.withhold("witness_log_integrity_invalid")

    def test_32_replayed_observer_pin_type_confusion(self):
        f = self.f
        f["pins"] = (replace(f["pins"][0], epoch=True), f["pins"][1])
        self.withhold("observer_pin_invalid")

    def test_33_result_cannot_be_escalated(self):
        x = inspect(self.f)
        x["authorized"] = True
        with self.assertRaises(Exception):
            assert_no_authority(x)

    def test_34_source_data_not_in_receipt(self):
        out = json.dumps(inspect(self.f), sort_keys=True)
        for bad in ("signature_b64", "raw_sha256", '"original_bytes": {', "source_url"):
            self.assertNotIn(bad, out)

    def test_35_observer_pin_roundtrip_across_process(self):
        f = self.f
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "observer-pins.json"
            path.write_text(json.dumps([asdict(p) for p in f["pins"]]), encoding="utf-8")
            script = ("import json,sys;from multi_host_witness import WitnessObserverPin,anchor_digest;"
                      "p=[WitnessObserverPin(**v) for v in json.load(open(sys.argv[1]))];"
                      "print(anchor_digest(p[0]) == anchor_digest(p[1]))")
            env = dict(os.environ, PYTHONPATH=str(HERE))
            process = subprocess.run([sys.executable,"-c",script,str(path)],env=env,
                                     capture_output=True,text=True,timeout=10)
            self.assertEqual(process.returncode,0,process.stderr)
            self.assertEqual(process.stdout.strip(),"True")

    def test_36_signed_fork_observer_gossip_same_epoch_refused(self):
        f = self.f
        different = deepcopy(f["checkpoint"])
        different["epoch"] = f["checkpoint"]["epoch"]
        different["log_sha256"] = "b"*64
        f["gossip"] = [attest(different, f["ids"][0], f["keys"][f["ids"][0]])]
        self.withhold("witness_gossip_fork_detected")


    def test_37_closed_portable_receipt_schema(self):
        from jsonschema import Draft202012Validator
        schema=json.loads((HERE / "multi_host_witness_receipt.v0.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        validator=Draft202012Validator(schema)
        good=inspect(self.f)
        self.assertFalse(list(validator.iter_errors(good)))
        fail=deepcopy(good)
        fail["authorized"] = True
        self.assertTrue(list(validator.iter_errors(fail)))
        self.f["attestations"] = self.f["attestations"][:2]
        rejected=inspect(self.f)
        self.assertFalse(list(validator.iter_errors(rejected)))

    def test_38_seeded_fourteen_attack_stress_replay(self):
        from stress_multi_host import simulate
        a=simulate(iterations=28,seed=8123)
        b=simulate(iterations=28,seed=8123)
        self.assertEqual(a,b)
        self.assertEqual(a["failures"],0)
        self.assertEqual(len(a["cases"]),14)
        self.assertEqual(sum(v["attempted"] for v in a["cases"].values()),28)
        self.assertFalse(a["authorized"])
        self.assertEqual(a["transcripts_opened"],0)

    def test_39_stress_iteration_controls_reject_bool_and_overrun(self):
        from stress_multi_host import simulate
        for invalid in (True, False, 27, 2049, 0, -1):
            with self.subTest(value=invalid):
                with self.assertRaises(ValueError):
                    simulate(iterations=invalid)

    def test_40_unpinned_prefix_cannot_be_substituted_in_place(self):
        f=self.f
        changed=[]
        for i,e in enumerate(f["log"]):
            changed.append(new_log_event(changed,
                                         ("synthetic:edited-start" if i==0 else e["event_id"]),
                                         e["kind"],e["registry_sha256"],
                                         e["revocation_sha256"],e["occurred_at"]))
        f["log"]=changed
        f["checkpoint"]["log_sha256"]=log_digest(changed)
        f["checkpoint"]["log_tip_sha256"]=changed[-1]["event_sha256"]
        resign_host(f)
        self.withhold("witness_log_prefix_fork_or_rollback")


    def test_41_same_sequence_revocation_checkpoint_rewrite_requires_new_epoch_proof(self):
        f=self.f
        src=f["source"]
        src["revocation"]["payload"]["observed_at"]="2026-10-14T03:00:00Z"
        from test_synthetic_signatures import resign_revocation
        resign_revocation(src)
        new_sha=content_digest(REVOCATION_SCHEMA,src["revocation"]["payload"])
        # Both source signers and the witness quorum can be compromised;
        # two unchanged observer pins still constrain the old sequence.
        new_row=new_log_event(f["log"][:2],"synthetic:event3","audit_observed",
                              src["trust"].expected_registry_sha256,
                              new_sha,"2026-10-15T01:00:00Z")
        f["log"][-1]=new_row
        f["checkpoint"].update(revocation_sha256=new_sha,
                                log_sha256=log_digest(f["log"]),
                                log_tip_sha256=new_row["event_sha256"])
        resign_host(f)
        self.withhold("revocation_same_sequence_rewrite")


if __name__ == "__main__":
    unittest.main()
