"""Prospective red-team regressions for the synthetic-only v0 signature contract.

These are adversarial fictional tests. No source access, authentic private keys,
real identities, review decisions or release permissions are involved.
"""
from __future__ import annotations

from dataclasses import replace
from copy import deepcopy
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from registry_preflight import event_digest
from synthetic_signatures import verify_synthetic_signatures, assert_zero_authority
from test_synthetic_signatures import fixture, pub, resign_custody, resign_revocation, sign
from test_registry_preflight import WHEN


class SyntheticTrustAdversaries(unittest.TestCase):
    def setUp(self):
        self.f = fixture()

    def evaluate(self):
        f = self.f
        value = verify_synthetic_signatures(
            f["snapshot"], f["policy"], f["events"], f["proposal"],
            f["custody"], f["revocation"], checked_at=WHEN, trust=f["trust"])
        assert_zero_authority(value)
        return value

    def denial(self):
        self.assertEqual(self.evaluate()["status"], "withheld")

    def test_01_revoked_custodian_key_id_alias_cannot_evade_revocation(self):
        f = self.f
        old = f["key_ids"]["custody"]
        alias = "synthetic:duplicate-custodian-alias"
        keys = dict(f["trust"].custodian_keys)
        keys[alias] = keys[old]  # deliberately same public bytes
        subjects = dict(f["trust"].custodian_subjects)
        subjects[alias] = f["trust"].expected_custodian_ref
        f["trust"] = replace(f["trust"], custodian_keys=keys, custodian_subjects=subjects)
        f["revocation"]["payload"]["revoked_key_ids"] = [old]
        resign_revocation(f)
        f["custody"]["key_id"] = alias  # signature bytes unchanged
        self.denial()

    def test_02_revoked_revocation_signer_alias_cannot_evade_revocation(self):
        f = self.f
        old = f["key_ids"]["revocation"]
        alias = "synthetic:duplicate-revocation-alias"
        keys = dict(f["trust"].revocation_keys)
        keys[alias] = keys[old]  # deliberately same public bytes
        f["trust"] = replace(f["trust"], revocation_keys=keys)
        f["revocation"]["payload"]["revoked_key_ids"] = [old]
        resign_revocation(f)
        f["revocation"]["key_id"] = alias  # signature bytes unchanged
        self.denial()

    def test_03_compromised_custody_key_cannot_rewrite_audit_history(self):
        f = self.f
        # An attacker controls *only* the synthetic custodian key and can
        # recompute unsigned log hashes and the custody signature. It does not
        # possess the separately pinned revocation signer's private key.
        ev = f["events"][-1]
        ev["event_id"] = "synthetic:rewritten-event"
        ev["event_sha256"] = event_digest({k: v for k, v in ev.items()
                                           if k != "event_sha256"})
        f["custody"]["payload"]["audit_tip_sha256"] = ev["event_sha256"]
        resign_custody(f)
        self.denial()

    def test_04_trust_configuration_must_not_reuse_ids_across_roles(self):
        f = self.f
        revocation_id = f["key_ids"]["revocation"]
        keys = dict(f["trust"].custodian_keys)
        keys[revocation_id] = pub(f["keys"]["rotation"])
        subjects = dict(f["trust"].custodian_subjects)
        subjects[revocation_id] = f["trust"].expected_custodian_ref
        f["trust"] = replace(f["trust"], custodian_keys=keys,
                              custodian_subjects=subjects)
        self.denial()

    def test_05_compromised_revocation_signer_cannot_roll_back_pinned_revocations(self):
        f = self.f
        old = f["key_ids"]["custody"]
        f["revocation"]["payload"]["revoked_key_ids"] = [old]
        resign_revocation(f)  # checkpoint was independently pinned after revocation
        f["revocation"]["payload"]["revoked_key_ids"] = []
        f["revocation"] = sign(f["revocation"]["payload"],
                                f["key_ids"]["revocation"],
                                f["keys"]["revocation"])
        # The attacker has the revocation private key but not the independently
        # persisted digest/high-water. A replacement signed checkpoint is denied.
        self.denial()

    def test_06_revocation_signature_binds_independent_audit_tip(self):
        f = self.f
        f["revocation"]["payload"]["audit_tip_sha256"] = "f" * 64
        resign_revocation(f)
        self.denial()

    def test_07_revocation_signature_binds_independent_policy_digest(self):
        f = self.f
        f["revocation"]["payload"]["policy_sha256"] = "e" * 64
        resign_revocation(f)
        self.denial()

    def test_08_revocation_signature_binds_independent_registry_digest(self):
        f = self.f
        f["revocation"]["payload"]["registry_sha256"] = "d" * 64
        resign_revocation(f)
        self.denial()

    def test_09_compromised_custodian_cannot_resign_changed_policy(self):
        f = self.f
        f["policy"]["reviewer_ref"] = "synthetic:alternate-reviewer"
        # Reconstruct the synthetic second audit action to pass the unsigned
        # continuity check while retaining the original, externally pinned roots.
        f["events"][1]["actor_ref"] = f["policy"]["reviewer_ref"]
        ev = f["events"][1]
        ev["event_sha256"] = event_digest({k: v for k, v in ev.items()
                                           if k != "event_sha256"})
        f["custody"]["payload"]["policy_sha256"] = __import__(
            "synthetic_signatures").policy_digest(f["policy"])
        f["custody"]["payload"]["audit_tip_sha256"] = ev["event_sha256"]
        resign_custody(f)
        self.denial()

    def test_10_valid_rotation_still_only_reports_no_authority(self):
        f = self.f
        f["custody"]["key_id"] = f["key_ids"]["rotation"]
        resign_custody(f)
        f["revocation"]["payload"]["revoked_key_ids"] = [f["key_ids"]["custody"]]
        resign_revocation(f)
        result = self.evaluate()
        self.assertEqual(result["status"],
                         "synthetic_signatures_verified_no_authority")
        self.assertFalse(result["authorized"])
        self.assertFalse(result["can_read_source"])
        self.assertFalse(result["publication_eligible"])
        self.assertEqual(set(result["gate_status"].values()), {"NOT_RUN"})

    def test_11_signed_payload_never_allows_custody_role_change(self):
        f = self.f
        f["custody"]["key_id"] = f["key_ids"]["revocation"]
        self.denial()

    def test_12_revocation_checkpoint_must_reject_source_scope_expansion(self):
        f = self.f
        f["revocation"]["payload"]["permission"] = "read_un_original_source"
        resign_revocation(f)
        self.denial()

    def test_13_independent_checkpoint_highwater_blocks_old_state(self):
        f = self.f
        f["trust"] = replace(f["trust"], minimum_checkpoint_sequence=4)
        self.denial()


if __name__ == "__main__":
    unittest.main()
