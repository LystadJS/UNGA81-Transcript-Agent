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
from test_synthetic_signatures import fixture, pub, resign_custody, resign_revocation
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


if __name__ == "__main__":
    unittest.main()
