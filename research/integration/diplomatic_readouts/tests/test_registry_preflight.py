"""Synthetic-only negative controls for private registry metadata preflight."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from private_source_contract import make_proposal
from registry_preflight import (  # noqa: E402
    LOCK, ZERO, RECEIPT_SCHEMA, event_digest, registry_digest, receipt_digest,
    assert_no_authority, preflight, PreflightWithheld,
)

WHEN = "2026-10-15T13:00:00Z"


def fake_hash(label):
    return sha256(("synthetic-only:" + label).encode("utf-8")).hexdigest()


def fixtures():
    record = {
        "id": "synthetic:source1", "parent_id": "synthetic:parent1",
        "source_family_id": "synthetic:family1", "meeting_id": "synthetic:meeting1",
        "event_date": "2026-10-01", "source_status": "available",
        "exclusion_code": None, "missing_reason": None,
        "raw_sha256": fake_hash("original bytes"),
        "text_sha256": fake_hash("unicode text"),
        "representation_id": "synthetic:representation1", "offset_basis": "unicode_codepoints",
        "classification": "synthetic_only",
    }
    unknown = {**record, "id": "synthetic:source2", "parent_id": None,
               "source_family_id": "synthetic:family2", "meeting_id": "synthetic:meeting2",
               "source_status": "unavailable", "missing_reason": "synthetic:not_collected",
               "raw_sha256": None, "text_sha256": None, "representation_id": None,
               "offset_basis": None}
    snap = {
        "schema": "un.private-source-registry.metadata.v0", "fixture_kind": "synthetic",
        "registry_id": "synthetic:registry1", "registry_revision": 1,
        "previous_registry_sha256": None, "recorded_at": "2026-10-11T00:00:00Z",
        "source_schema": "synthetic.v1", "source_hash_basis": "synthetic",
        "source_sha256": fake_hash("cohort source"), "selection_sha256": fake_hash("selection"),
        "records": [record, unknown],
        "population": {"total_in_frame": 3, "observations_total": 2,
                       "eligible": 1, "excluded": 0, "unavailable": 1, "unobserved": 1},
        "holdout_lock": dict(LOCK),
    }
    digest = registry_digest(snap)
    policy = {
        "schema": "un.private-source-registry.custody-intent.v0", "fixture_kind": "synthetic",
        "registry_id": snap["registry_id"], "registry_sha256": digest,
        "custodian_ref": "synthetic:custodian", "reviewer_ref": "synthetic:reviewer",
        "issuer_ref": "synthetic:issuer", "purpose": "synthetic_metadata_preflight",
        "issued_at": "2026-10-12T00:00:00Z", "expires_at": "2026-10-20T00:00:00Z",
        "revocation_sequence": 2, "attestation": "unverified_metadata_consistency_only",
        "requested_scopes": ["synthetic_metadata_inventory"],
        "permissions": {k: False for k in (
            "read_source_bytes", "read_reserved", "write_registry",
            "issue_reviewer_decision", "approve_statistics", "publish", "send_mail")},
    }
    events = []
    for i, (kind, actor, time) in enumerate((
        ("registered", "synthetic:custodian", "2026-10-12T00:00:00Z"),
        ("metadata_checked", "synthetic:reviewer", "2026-10-13T00:00:00Z")), 1):
        entry = {"index": i, "event_id": f"synthetic:event{i}", "kind": kind,
                 "actor_ref": actor, "occurred_at": time, "registry_sha256": digest,
                 "previous_sha256": events[-1]["event_sha256"] if events else ZERO}
        entry["event_sha256"] = event_digest(entry)
        events.append(entry)
    return snap, policy, events


def proposal_for(snapshot):
    """Existing v0 source lineage and inclusive-exclusion count convention."""
    counts = snapshot["population"]
    envelope = {
        "schema": "un.parallel-analysis.v1", "publication_eligible": False,
        "evaluation_role": "engineering_only",
        "producer": {"fixture_kind": "synthetic"},
        "cohort": {"split": "synthetic", "total_in_frame": counts["total_in_frame"]},
        "upstream": {"source_schema": snapshot["source_schema"],
                     "source_hash_basis": snapshot["source_hash_basis"],
                     "source_sha256": snapshot["source_sha256"],
                     "selection_sha256": snapshot["selection_sha256"]},
        "coverage": {"observations_total": counts["observations_total"],
                     "eligible": counts["eligible"],
                     "excluded": counts["excluded"] + counts["unavailable"],
                     "unavailable_sources": counts["unavailable"]},
    }
    return make_proposal(envelope, fake_hash("source envelope"))


def bind(snapshot, policy, events):
    """Rebind *synthetic consistency digests*, never confer authorization."""
    policy["registry_sha256"] = registry_digest(snapshot)
    previous = ZERO
    for i, entry in enumerate(events, 1):
        entry["index"] = i
        entry["registry_sha256"] = policy["registry_sha256"]
        entry["previous_sha256"] = previous
        entry["event_sha256"] = event_digest({k: v for k, v in entry.items()
                                               if k != "event_sha256"})
        previous = entry["event_sha256"]
    policy["revocation_sequence"] = len(events)


class RegistryPreflightTests(unittest.TestCase):
    def setUp(self):
        self.snapshot, self.policy, self.events = fixtures()
        self.proposal = proposal_for(self.snapshot)

    def check(self):
        return preflight(self.snapshot, self.policy, self.events, checked_at=WHEN, proposal=self.proposal)

    def deny(self, expected):
        output = self.check()
        self.assertEqual(output["metadata_status"], "withheld")
        self.assertIn(expected, output["reason_codes"])
        self.assertEqual(output["authority"], "none")
        self.assertFalse(output["authorized"])
        self.assertFalse(output["publication_eligible"])
        self.assertIsNone(output["population"])
        self.assertIsNone(output["registry_sha256"])
        assert_no_authority(output)

    def test_01_consistent_is_not_authorized(self):
        receipt = self.check()
        self.assertEqual(receipt["metadata_status"], "metadata_consistent")
        self.assertFalse(receipt["authorized"])
        self.assertFalse(receipt["can_read_source"])
        self.assertEqual(receipt["holdout_lock"], LOCK)
        self.assertEqual(len(receipt["gate_status"]), 13)
        self.assertEqual(set(receipt["gate_status"].values()), {"NOT_RUN"})
        assert_no_authority(receipt)

    def test_02_replay_stable_digest(self):
        self.assertEqual(receipt_digest(self.check()), receipt_digest(self.check()))

    def test_03_no_private_source_rows_exported(self):
        data = json.dumps(self.check(), sort_keys=True)
        self.assertNotIn("synthetic:source1", data)
        self.assertNotIn("synthetic:custodian", data)
        self.assertNotIn("synthetic:reviewer", data)
        self.assertNotIn("source_url", data)

    def test_04_reject_private_passage_injection(self):
        self.snapshot["records"][0]["private_excerpt"] = "secret"
        self.deny("source_record_not_closed")
        self.assertNotIn("secret", json.dumps(self.check()))

    def test_05_reject_url_path_credentials(self):
        for key in ("source_url", "file_path", "api_token"):
            with self.subTest(key=key):
                snap, policy, events = fixtures()
                snap[key] = "DO_NOT_LOG"
                r = preflight(snap, policy, events, checked_at=WHEN, proposal=proposal_for(snap))
                self.assertEqual(r["metadata_status"], "withheld")
                self.assertNotIn("DO_NOT_LOG", json.dumps(r))

    def test_06_mismatched_snapshot_binding(self):
        self.policy["registry_sha256"] = fake_hash("forged")
        self.deny("custody_binding_invalid")

    def test_07_corrupt_original_hash_syntax(self):
        self.snapshot["records"][0]["raw_sha256"] = "garbage"
        bind(self.snapshot, self.policy, self.events)
        self.deny("available_source_metadata_invalid")

    def test_08_source_classification_must_be_synthetic(self):
        self.snapshot["records"][0]["classification"] = "restricted"
        bind(self.snapshot, self.policy, self.events)
        self.deny("non_synthetic_material_forbidden")

    def test_09_no_real_registry(self):
        self.snapshot["fixture_kind"] = "private_development"
        bind(self.snapshot, self.policy, self.events)
        self.deny("real_registry_forbidden")

    def test_10_duplicate_id(self):
        self.snapshot["records"][1]["id"] = "synthetic:source1"
        bind(self.snapshot, self.policy, self.events)
        self.deny("source_id_duplicate_or_invalid")

    def test_11_missing_source_not_issue_absence(self):
        receipt = self.check()
        self.assertEqual(receipt["population"]["unavailable"], 1)
        self.assertEqual(receipt["population"]["unobserved"], 1)
        self.assertEqual(receipt["population"]["eligible"], 1)

    def test_12_unavailable_must_lack_pretend_text(self):
        self.snapshot["records"][1]["text_sha256"] = fake_hash("invented unavailable")
        bind(self.snapshot, self.policy, self.events)
        self.deny("unavailable_source_metadata_invalid")

    def test_13_population_double_count(self):
        self.snapshot["population"]["excluded"] = 1
        bind(self.snapshot, self.policy, self.events)
        self.deny("population_accounting_invalid")

    def test_14_population_record_mismatch(self):
        self.snapshot["population"]["eligible"] = 0
        self.snapshot["population"]["excluded"] = 1
        bind(self.snapshot, self.policy, self.events)
        self.deny("record_population_mismatch")

    def test_15_reserved_dates_rejected(self):
        self.snapshot["records"][0]["event_date"] = "2026-10-05"
        bind(self.snapshot, self.policy, self.events)
        self.deny("reserved_dates_forbidden")

    def test_16_reserved_lock_cannot_change(self):
        self.snapshot["holdout_lock"]["transcripts_opened"] = 1
        bind(self.snapshot, self.policy, self.events)
        self.deny("reserved_holdout_lock_violation")

    def test_17_custody_permission_escalation(self):
        self.policy["permissions"]["read_source_bytes"] = True
        self.deny("custody_permission_escalation")

    def test_18_publication_request_denied(self):
        self.policy["permissions"]["publish"] = True
        self.deny("custody_permission_escalation")

    def test_19_expired_policy(self):
        self.policy["expires_at"] = "2026-10-14T00:00:00Z"
        self.deny("custody_expired_or_future")

    def test_20_future_issued_at(self):
        self.policy["issued_at"] = "2026-10-16T00:00:00Z"
        self.deny("custody_expired_or_future")

    def test_21_stale_revocation_feed(self):
        self.policy["revocation_sequence"] = 1
        self.deny("revocation_ledger_stale")

    def test_22_revocation_event(self):
        e = {"index": 3, "event_id": "synthetic:revoked", "kind": "revoked",
             "actor_ref": "synthetic:custodian", "occurred_at": "2026-10-14T00:00:00Z",
             "registry_sha256": self.policy["registry_sha256"],
             "previous_sha256": self.events[-1]["event_sha256"]}
        e["event_sha256"] = event_digest(e)
        self.events.append(e)
        self.policy["revocation_sequence"] = 3
        self.deny("registry_or_custody_revoked")

    def test_23_chain_gap(self):
        self.events[1]["index"] = 4
        self.deny("audit_sequence_or_registry_mismatch")

    def test_24_tampered_event_hash(self):
        self.events[1]["event_sha256"] = fake_hash("forgery")
        self.deny("audit_hash_chain_invalid")

    def test_25_time_order(self):
        self.events[1]["occurred_at"] = "2026-10-11T00:00:00Z"
        bind(self.snapshot, self.policy, self.events)
        self.deny("audit_time_order_invalid")

    def test_26_duplicate_event_id(self):
        self.events[1]["event_id"] = self.events[0]["event_id"]
        bind(self.snapshot, self.policy, self.events)
        self.deny("audit_sequence_or_registry_mismatch")

    def test_27_future_event(self):
        self.events[1]["occurred_at"] = "2026-10-16T00:00:00Z"
        bind(self.snapshot, self.policy, self.events)
        self.deny("audit_time_order_invalid")

    def test_28_wrong_custodian(self):
        self.events[0]["actor_ref"] = "synthetic:other"
        bind(self.snapshot, self.policy, self.events)
        self.deny("audit_custodian_mismatch")

    def test_29_no_review_gate_issue(self):
        receipt = self.check()
        self.assertEqual(receipt["gate_status"]["owner_review"], "NOT_RUN")
        self.assertEqual(receipt["gate_status"]["statistical_identification"], "NOT_RUN")
        self.assertEqual(receipt["gate_status"]["d1_publication"], "NOT_RUN")

    def test_30_receipt_tamper_rejected(self):
        r = self.check()
        for key, value in (("authorized", True), ("publication_eligible", True),
                           ("can_read_source", True), ("delivery_eligible", True)):
            t = deepcopy(r)
            t[key] = value
            with self.subTest(key=key), self.assertRaises(PreflightWithheld):
                assert_no_authority(t)

    def test_31_gate_status_escalation_rejected(self):
        r = self.check()
        r["gate_status"]["privacy"] = "PASS"
        with self.assertRaises(PreflightWithheld):
            assert_no_authority(r)

    def test_32_unknown_receipt_field_rejected(self):
        r = self.check()
        r["private_source_payload"] = "secret"
        with self.assertRaises(PreflightWithheld):
            assert_no_authority(r)

    def test_33_invalid_types_fail_closed(self):
        for bad in ([], "malformed", None, {"weird": [1]}, {"records": None}):
            with self.subTest(bad=str(bad)[:25]):
                r = preflight(bad, self.policy, self.events, checked_at=WHEN)
                self.assertEqual(r["metadata_status"], "withheld")
                assert_no_authority(r)

    def test_34_reviewer_identity_does_not_approve(self):
        self.policy["reviewer_ref"] = self.policy["custodian_ref"]
        bind(self.snapshot, self.policy, self.events)
        self.events[1]["actor_ref"] = self.policy["reviewer_ref"]
        bind(self.snapshot, self.policy, self.events)
        r = self.check()
        self.assertEqual(r["metadata_status"], "metadata_consistent")
        self.assertFalse(r["can_issue_review"])

    def test_35_no_private_record_export_when_revoked(self):
        self.policy["revocation_sequence"] += 1
        r = self.check()
        self.assertNotIn("synthetic:source", json.dumps(r))
        self.assertNotIn("synthetic:custodian", json.dumps(r))
        self.assertEqual(r["holdout_lock"], LOCK)

    def test_37_reserved_lock_rejects_bool_int_conflation(self):
        self.snapshot["holdout_lock"]["access_granted"] = 0
        bind(self.snapshot, self.policy, self.events)
        self.deny("reserved_holdout_lock_violation")
        snap, policy, events = fixtures()
        receipt = preflight(snap, policy, events, checked_at=WHEN, proposal=proposal_for(snap))
        receipt["holdout_lock"]["reserved_meetings"] = 37.0
        with self.assertRaises(PreflightWithheld):
            assert_no_authority(receipt)

    def test_38_boolean_event_index_rejected(self):
        self.events[0]["index"] = True
        self.deny("audit_sequence_or_registry_mismatch")

    def test_39_population_receipt_tampering_rejected(self):
        self.snapshot, self.policy, self.events = fixtures()
        self.proposal = proposal_for(self.snapshot)
        receipt = self.check()
        receipt["population"]["unavailable"] = 0
        with self.assertRaises(PreflightWithheld):
            assert_no_authority(receipt)

    def test_40_missing_prior_design_proposal_withheld(self):
        result = preflight(self.snapshot, self.policy, self.events, checked_at=WHEN)
        self.assertEqual(result["reason_codes"], ["existing_private_proposal_invalid"])
        assert_no_authority(result)

    def test_41_changed_source_digest_vs_design_proposal_withheld(self):
        self.snapshot["source_sha256"] = fake_hash("other selection")
        bind(self.snapshot, self.policy, self.events)
        self.deny("existing_private_proposal_population_or_lineage_mismatch")

    def test_42_denominator_crosswalk_requires_missing_in_exclusions(self):
        self.proposal["population"]["unavailable_sources"] = 0
        self.deny("existing_private_proposal_population_or_lineage_mismatch")

    def test_43_proposal_cannot_escalate_statistical_gate(self):
        self.proposal["gate_status"]["statistical_identification"] = "PASS"
        self.deny("existing_private_proposal_invalid")

    def test_44_self_certified_source_release_denied(self):
        self.proposal["authorized"] = True
        self.deny("existing_private_proposal_invalid")

    def test_36_expected_schema_consistency(self):
        # No external dependency for the runtime. If jsonschema is installed,
        # independently check the emitted synthetic-only public receipt.
        schema_path = HERE.parent / "registry_preflight.v0.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        r = self.check()
        self.assertEqual(schema["properties"]["schema"]["const"], RECEIPT_SCHEMA)
        self.assertEqual(set(schema["required"]), set(r))
        input_schema = json.loads((HERE.parent / "registry_preflight_input.v0.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(set(input_schema["required"]), {"snapshot", "policy", "events", "checked_at"})
        try:
            import jsonschema
        except ImportError:
            return
        v = jsonschema.Draft202012Validator(schema)
        v.validate(r)
        packet = {"snapshot": self.snapshot, "policy": self.policy, "events": self.events, "checked_at": WHEN}
        jsonschema.Draft202012Validator(input_schema).validate(packet)
        packet["private_original_text"] = "DO_NOT_COPY"
        self.assertTrue(list(jsonschema.Draft202012Validator(input_schema).iter_errors(packet)))
        self.policy["expires_at"] = "2026-10-14T00:00:00Z"
        v.validate(self.check())


if __name__ == "__main__":
    unittest.main()
