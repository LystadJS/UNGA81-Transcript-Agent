"""Adversarial synthetic-only Ed25519 verification cases; no real sources/keys."""
from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from registry_preflight import event_digest, registry_digest
from private_source_contract import REQUIRED_GATES, proposal_digest
from synthetic_signatures import (
    CUSTODY_SCHEMA, REVOCATION_SCHEMA, DOMAINS, AUDIENCE, SIGNED_SCHEMA,
    ZERO_PERMISSIONS, SyntheticTrustAnchors, assert_zero_authority,
    content_digest, policy_digest, receipt_sha256, verify_synthetic_signatures,
)
from test_registry_preflight import fixtures, proposal_for, bind, WHEN


def test_signer(label):
    """Publicly reconstructible TEST-ONLY Ed25519 key; never use operationally."""
    raw = sha256(("NOT A SECRET / SYNTHETIC / " + label).encode()).digest()
    return Ed25519PrivateKey.from_private_bytes(raw)


def pub(key):
    return key.public_key().public_bytes(encoding=serialization.Encoding.Raw,
                                         format=serialization.PublicFormat.Raw)


def sign(payload, kid, key):
    schema = payload["schema"]
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False).encode("ascii")
    signature = key.sign(DOMAINS[schema] + raw)
    return {"schema": SIGNED_SCHEMA, "algorithm": "Ed25519", "key_id": kid,
            "payload": payload, "signature_b64": base64.b64encode(signature).decode("ascii")}


def fixture():
    snapshot, policy, events = fixtures()
    proposal = proposal_for(snapshot)
    custody_key = test_signer("custodian-alpha")
    rotation_key = test_signer("custodian-beta")
    revocation_key = test_signer("independent-revocation-root")
    custody_kid = "synthetic:custodian-alpha"
    rotation_kid = "synthetic:custodian-beta"
    revocation_kid = "synthetic:revocation-root"
    custody_payload = {
        "schema": CUSTODY_SCHEMA, "fixture_kind": "synthetic",
        "registry_id": snapshot["registry_id"],
        "registry_sha256": registry_digest(snapshot),
        "policy_sha256": policy_digest(policy),
        "proposal_sha256": proposal_digest(proposal),
        "audit_tip_sha256": events[-1]["event_sha256"],
        "purpose": "synthetic_metadata_preflight", "audience": AUDIENCE,
        "custodian_ref": policy["custodian_ref"],
        "issued_at": "2026-10-13T01:00:00Z", "expires_at": "2026-10-19T00:00:00Z",
        "permission": ZERO_PERMISSIONS,
    }
    revoke_payload = {
        "schema": REVOCATION_SCHEMA, "fixture_kind": "synthetic",
        "registry_id": snapshot["registry_id"], "sequence": 2,
        "observed_at": "2026-10-14T00:00:00Z",
        "expires_at": "2026-10-17T00:00:00Z",
        "revoked_key_ids": [], "audience": AUDIENCE,
        "purpose": "synthetic_revocation_verification",
        "issuer_ref": "synthetic:revocation-authority", "permission": ZERO_PERMISSIONS,
    }
    signed_custody = sign(custody_payload, custody_kid, custody_key)
    signed_revocation = sign(revoke_payload, revocation_kid, revocation_key)
    trust = SyntheticTrustAnchors(
        custodian_keys={custody_kid: pub(custody_key), rotation_kid: pub(rotation_key)},
        revocation_keys={revocation_kid: pub(revocation_key)},
        custodian_subjects={custody_kid: policy["custodian_ref"],
                            rotation_kid: policy["custodian_ref"]},
        expected_custodian_ref=policy["custodian_ref"],
        expected_revocation_issuer_ref="synthetic:revocation-authority",
        expected_registry_id=snapshot["registry_id"],
        expected_registry_sha256=registry_digest(snapshot),
        expected_proposal_sha256=proposal_digest(proposal),
        expected_checkpoint_sha256=content_digest(REVOCATION_SCHEMA, revoke_payload),
        minimum_checkpoint_sequence=2,
    )
    return {
        "snapshot": snapshot, "policy": policy, "events": events,
        "proposal": proposal, "custody": signed_custody, "revocation": signed_revocation,
        "trust": trust, "keys": {"custody": custody_key, "rotation": rotation_key,
                              "revocation": revocation_key},
        "key_ids": {"custody": custody_kid, "rotation": rotation_kid,
                    "revocation": revocation_kid},
    }


def resign_custody(f):
    f["custody"] = sign(f["custody"]["payload"], f["custody"]["key_id"],
                        f["keys"]["rotation"] if f["custody"]["key_id"] == f["key_ids"]["rotation"]
                        else f["keys"]["custody"])


def resign_revocation(f):
    f["revocation"] = sign(f["revocation"]["payload"], f["key_ids"]["revocation"],
                           f["keys"]["revocation"])
    f["trust"] = replace(f["trust"], expected_checkpoint_sha256=content_digest(
        REVOCATION_SCHEMA, f["revocation"]["payload"]))


class SyntheticSignatureTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture()

    def verify(self, *, when=WHEN):
        f = self.f
        return verify_synthetic_signatures(
            f["snapshot"], f["policy"], f["events"], f["proposal"],
            f["custody"], f["revocation"], checked_at=when, trust=f["trust"])

    def denial(self, reason):
        r = self.verify()
        self.assertEqual(r["status"], "withheld")
        self.assertEqual(r["reason_codes"], [reason])
        self.assertIsNone(r["registry_sha256"])
        self.assertFalse(r["signature_verified"])
        self.assertFalse(r["authorized"])
        assert_zero_authority(r)

    def test_01_positive_crypto_verification_is_not_authorization(self):
        r = self.verify()
        self.assertEqual(r["status"], "synthetic_signatures_verified_no_authority")
        self.assertEqual(r["registry_sha256"], self.f["trust"].expected_registry_sha256)
        self.assertTrue(r["signature_verified"])
        self.assertTrue(r["revocation_verified"])
        self.assertEqual(set(r["gate_status"]), set(REQUIRED_GATES))
        self.assertEqual(set(r["gate_status"].values()), {"NOT_RUN"})
        for key in ("authorized", "can_read_source", "can_issue_review", "statistical_eligible",
                    "publication_eligible", "delivery_eligible"):
            self.assertFalse(r[key])
        self.assertEqual(r["holdout_lock"]["transcripts_opened"], 0)
        assert_zero_authority(r)

    def test_02_repeat_deterministic_digest(self):
        self.assertEqual(receipt_sha256(self.verify()), receipt_sha256(self.verify()))

    def test_03_custody_payload_tamper(self):
        self.f["custody"]["payload"]["policy_sha256"] = "a" * 64
        self.denial("invalid_ed25519_signature")

    def test_04_revocation_payload_tamper(self):
        self.f["revocation"]["payload"]["observed_at"] = "2026-10-14T01:00:00Z"
        self.denial("invalid_ed25519_signature")

    def test_05_signature_bit_flip(self):
        raw = bytearray(base64.b64decode(self.f["custody"]["signature_b64"]))
        raw[2] ^= 64
        self.f["custody"]["signature_b64"] = base64.b64encode(raw).decode()
        self.denial("invalid_ed25519_signature")

    def test_06_invalid_base64(self):
        self.f["custody"]["signature_b64"] = "!@#"
        self.denial("invalid_signature_encoding")

    def test_07_short_signature(self):
        self.f["revocation"]["signature_b64"] = base64.b64encode(b"foo").decode()
        self.denial("invalid_signature_encoding")

    def test_08_algorithm_downgrade(self):
        self.f["custody"]["algorithm"] = "none"
        self.denial("unsupported_signature_algorithm_or_identity")

    def test_09_unknown_custodian_key(self):
        self.f["custody"]["key_id"] = "synthetic:outside-trust"
        self.denial("untrusted_signature_key")

    def test_10_revocation_root_not_custodian_key(self):
        self.f["revocation"]["key_id"] = self.f["key_ids"]["custody"]
        self.denial("untrusted_signature_key")

    def test_11_same_public_material_cannot_fill_both_trust_roles(self):
        f = self.f
        f["trust"] = replace(f["trust"], revocation_keys={
            f["key_ids"]["revocation"]: pub(f["keys"]["custody"])})
        self.denial("independent_revocation_signer_required")

    def test_12_no_trust(self):
        self.f["trust"] = None
        self.denial("independent_trust_anchor_missing_or_invalid")

    def test_13_wrong_expected_registry_hash(self):
        self.f["trust"] = replace(self.f["trust"], expected_registry_sha256="b"*64)
        self.denial("externally_pinned_source_or_proposal_mismatch")

    def test_14_wrong_expected_proposal(self):
        self.f["trust"] = replace(self.f["trust"], expected_proposal_sha256="b"*64)
        self.denial("externally_pinned_source_or_proposal_mismatch")

    def test_15_checkpoint_rollback_against_pinned_digest(self):
        self.f["trust"] = replace(self.f["trust"], expected_checkpoint_sha256="b"*64)
        self.denial("revocation_checkpoint_not_externally_pinned")

    def test_16_revocation_sequence_highwater_rejects_old_signed_log(self):
        self.f["trust"] = replace(self.f["trust"], minimum_checkpoint_sequence=3)
        self.denial("revocation_checkpoint_invalid_or_rollback")

    def test_17_expired_revocation(self):
        self.f["revocation"]["payload"]["expires_at"] = "2026-10-14T00:00:00Z"
        resign_revocation(self.f)
        self.denial("revocation_checkpoint_expired_or_future")

    def test_18_future_revocation(self):
        self.f["revocation"]["payload"]["observed_at"] = "2026-10-16T00:00:00Z"
        resign_revocation(self.f)
        self.denial("revocation_checkpoint_expired_or_future")

    def test_19_expired_attestation(self):
        self.f["custody"]["payload"]["expires_at"] = "2026-10-14T00:00:00Z"
        resign_custody(self.f)
        self.denial("custody_signature_expired_or_future")

    def test_20_future_attestation(self):
        self.f["custody"]["payload"]["issued_at"] = "2026-10-16T00:00:00Z"
        resign_custody(self.f)
        self.denial("custody_signature_expired_or_future")

    def test_21_extended_attestation_beyond_policy(self):
        self.f["custody"]["payload"]["expires_at"] = "2026-10-25T00:00:00Z"
        resign_custody(self.f)
        self.denial("custody_signature_expired_or_future")

    def test_22_attestation_bound_to_policy(self):
        self.f["custody"]["payload"]["policy_sha256"] = "c" * 64
        resign_custody(self.f)
        self.denial("custody_signature_binding_mismatch")

    def test_23_attestation_bound_to_exact_registry_audit_tip(self):
        self.f["custody"]["payload"]["audit_tip_sha256"] = "c" * 64
        resign_custody(self.f)
        self.denial("custody_signature_binding_mismatch")

    def test_24_attestation_bound_to_original_proposal(self):
        self.f["custody"]["payload"]["proposal_sha256"] = "c" * 64
        resign_custody(self.f)
        self.denial("custody_signature_binding_mismatch")

    def test_25_cross_audience_replay(self):
        self.f["custody"]["payload"]["audience"] = "synthetic:another-project"
        resign_custody(self.f)
        self.denial("signed_payload_scope_invalid")

    def test_26_wrong_attested_purpose(self):
        self.f["custody"]["payload"]["purpose"] = "synthetic_other_purpose"
        resign_custody(self.f)
        self.denial("custody_signature_binding_mismatch")

    def test_27_extra_signed_source_content_rejected(self):
        self.f["custody"]["payload"]["source_text"] = "DONT_EXPORT_PRIVATE"
        resign_custody(self.f)
        self.denial("signed_payload_not_closed")
        self.assertNotIn("DONT_EXPORT_PRIVATE", json.dumps(self.verify()))

    def test_28_revoked_custodian_key(self):
        self.f["revocation"]["payload"]["revoked_key_ids"] = [self.f["key_ids"]["custody"]]
        resign_revocation(self.f)
        self.denial("custodian_key_revoked")

    def test_29_revoked_revocation_key(self):
        self.f["revocation"]["payload"]["revoked_key_ids"] = [self.f["key_ids"]["revocation"]]
        resign_revocation(self.f)
        self.denial("revocation_signer_revoked")

    def test_30_revocation_key_rotation_unrevoked_new_key(self):
        self.f["custody"]["key_id"] = self.f["key_ids"]["rotation"]
        resign_custody(self.f)
        self.f["revocation"]["payload"]["revoked_key_ids"] = [self.f["key_ids"]["custody"]]
        resign_revocation(self.f)
        self.assertEqual(self.verify()["status"], "synthetic_signatures_verified_no_authority")
        self.assertFalse(self.verify()["can_read_source"])

    def test_31_old_rotated_key_rejected_after_signed_revocation(self):
        self.f["revocation"]["payload"]["revoked_key_ids"] = [self.f["key_ids"]["custody"]]
        resign_revocation(self.f)
        self.denial("custodian_key_revoked")

    def test_32_duplicate_revoked_keys_rejected(self):
        self.f["revocation"]["payload"]["revoked_key_ids"] = [self.f["key_ids"]["custody"]]*2
        resign_revocation(self.f)
        self.denial("revocation_checkpoint_invalid_or_rollback")

    def test_33_unsorted_revoked_keys_rejected(self):
        self.f["revocation"]["payload"]["revoked_key_ids"] = [self.f["key_ids"]["revocation"], self.f["key_ids"]["custody"]]
        resign_revocation(self.f)
        self.denial("revocation_checkpoint_invalid_or_rollback")

    def test_34_bool_sequence_rejected(self):
        self.f["revocation"]["payload"]["sequence"] = True
        resign_revocation(self.f)
        self.denial("revocation_checkpoint_invalid_or_rollback")

    def test_35_custody_registry_digest_tamper(self):
        self.f["snapshot"]["records"][0]["raw_sha256"] = "f" * 64
        self.denial("underlying_registry_preflight_withheld")

    def test_36_real_source_split_rejected_even_if_signed(self):
        self.f["snapshot"]["fixture_kind"] = "private_development"
        self.denial("underlying_registry_preflight_withheld")

    def test_37_requested_publication_rejected_even_if_signed(self):
        self.f["policy"]["permissions"]["publish"] = True
        self.denial("underlying_registry_preflight_withheld")

    def test_38_reserved_holdout_read_rejected_even_if_signed(self):
        self.f["snapshot"]["holdout_lock"]["transcripts_opened"] = 1
        self.denial("underlying_registry_preflight_withheld")

    def test_39_registry_event_revoked_rejected_even_with_independent_key(self):
        self.f["events"][1]["kind"] = "revoked"
        self.denial("underlying_registry_preflight_withheld")

    def test_40_untrusted_extra_signed_field_rejected(self):
        self.f["revocation"]["network"] = "on"
        self.denial("signed_envelope_not_closed")

    def test_41_validation_receipt_escalation_rejected(self):
        out = self.verify()
        out["can_read_source"] = True
        with self.assertRaisesRegex(Exception, "signature_receipt_authority_escalation"):
            assert_zero_authority(out)

    def test_42_result_never_contains_source_text_or_keys(self):
        text = json.dumps(self.verify(), sort_keys=True)
        self.assertNotIn("raw_sha256", text)
        self.assertNotIn('"original_bytes": {', text)
        self.assertNotIn("signature_b64", text)
        self.assertNotIn("custodian-alpha", text)
        self.assertNotIn("records", text)

    def test_43_tampered_base_preflight_denominator(self):
        self.f["snapshot"]["population"]["eligible"] = 0
        self.denial("underlying_registry_preflight_withheld")

    def test_44_key_id_cannot_change_without_changing_signature(self):
        self.f["custody"]["key_id"] = self.f["key_ids"]["rotation"]
        self.denial("invalid_ed25519_signature")

    def test_45_malformed_numeric_timestamp(self):
        self.f["revocation"]["payload"]["observed_at"] = 2
        resign_revocation(self.f)
        self.denial("signed_timestamp_invalid")

    def test_47_custodian_identity_changed_but_signature_valid(self):
        self.f["custody"]["payload"]["custodian_ref"] = "synthetic:imposter"
        resign_custody(self.f)
        self.denial("custody_signature_binding_mismatch")

    def test_48_externally_pinned_custodian_identity_mismatch(self):
        self.f["trust"] = replace(self.f["trust"], expected_custodian_ref="synthetic:other")
        self.denial("independent_custodian_identity_binding_missing")

    def test_49_custodian_subject_key_binding_required(self):
        self.f["trust"] = replace(self.f["trust"], custodian_subjects={})
        self.denial("independent_custodian_identity_binding_missing")

    def test_50_revocation_issuer_identity_mismatch(self):
        self.f["revocation"]["payload"]["issuer_ref"] = "synthetic:untrusted-issuer"
        resign_revocation(self.f)
        self.denial("revocation_checkpoint_invalid_or_rollback")

    def test_51_revocation_predates_last_audit_action(self):
        self.f["revocation"]["payload"]["observed_at"] = "2026-10-12T00:00:00Z"
        resign_revocation(self.f)
        self.denial("revocation_checkpoint_predates_audit_tip")

    def test_52_long_lived_revocation_not_accepted(self):
        self.f["revocation"]["payload"]["expires_at"] = "2026-11-20T00:00:00Z"
        resign_revocation(self.f)
        self.denial("revocation_checkpoint_expired_or_future")

    def test_53_portable_json_schema_validates_signed_envelopes(self):
        from jsonschema import Draft202012Validator
        root = HERE.parent
        schema = json.loads((root / "signed_metadata.v0.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        v = Draft202012Validator(schema)
        self.assertEqual(list(v.iter_errors({"custody":self.f["custody"],
                                             "revocation":self.f["revocation"]})), [])
        invalid = deepcopy(self.f["custody"])
        invalid["payload"]["authority"] = "grant"
        self.assertNotEqual(list(v.iter_errors({"custody":invalid,
                                               "revocation":self.f["revocation"]})), [])

    def test_54_portable_json_schema_validates_closed_zero_authority_receipt(self):
        from jsonschema import Draft202012Validator
        schema = json.loads((HERE.parent / "synthetic_signatures.v0.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        v = Draft202012Validator(schema)
        valid = self.verify()
        self.assertEqual(list(v.iter_errors(valid)), [])
        invalid = deepcopy(valid)
        invalid["publication_eligible"] = True
        self.assertNotEqual(list(v.iter_errors(invalid)), [])
        invalid = deepcopy(valid)
        invalid["gate_status"]["source_registry"] = "PASS"
        self.assertNotEqual(list(v.iter_errors(invalid)), [])

    def test_55_benchmark_validates_positive_receipt_but_not_latency_gate(self):
        from benchmark_signatures import benchmark
        b=benchmark(iterations=20,warmup=2)
        self.assertFalse(b["authorized"])
        self.assertFalse(b["publication_eligible"])
        self.assertEqual(b["receipt_sha256"],receipt_sha256(self.verify()))
        self.assertGreater(b["metadata_preflight"]["median_ms"],0)
        self.assertGreater(b["ed25519_revocation_preflight"]["p95_ms"],0)

    def test_56_benchmark_refuses_invalid_iteration_controls(self):
        from benchmark_signatures import benchmark
        for count in (True, -1, 0, 19, 100001):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):benchmark(iterations=count)

    def test_46_revocation_signer_wrong_attestation_role(self):
        self.f["custody"]["key_id"] = self.f["key_ids"]["revocation"]
        self.denial("untrusted_signature_key")


if __name__ == "__main__":
    unittest.main()
