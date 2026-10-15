"""Fail-closed independent freeze review tests; synthetic and source-free."""
import unittest
from unittest.mock import patch
from . import v3_coordinator_preflight as audit

class CoordinatorPreflightTests(unittest.TestCase):
    def test_unapproved_identification_disposition(self):
        result=audit.review_candidate()
        self.assertEqual(result["status"],"NOT_ACCEPTED_FOR_STATISTICAL_FREEZE")
        self.assertFalse(result["approved"])
        self.assertFalse(result["v3_holdout_authorized"])
        self.assertFalse(result["real_fit_authorized"])
        self.assertEqual(result["gates"]["source_hash_integrity"],"PASS")
        self.assertEqual(result["gates"]["year_serial_dependence_aware_gamma_interval"],
                         "FAIL_NOT_IDENTIFIED")
        self.assertEqual(result["gates"]["year_process_nugget_external_identification"],
                         "FAIL_NOT_IDENTIFIED")
    def test_source_set_cannot_be_silently_incomplete(self):
        with patch.object(audit,"proposal_receipt") as p:
            p.return_value={"source_sha256":{}}
            with self.assertRaisesRegex(ValueError,"completeness"):
                audit.review_candidate()
    def test_tampered_receipt_hash_rejected(self):
        from .v3_freeze_candidate import proposal_receipt
        receipt=proposal_receipt()
        receipt["source_sha256"]["v3_nuisance.py"]="0"*64
        with patch.object(audit,"proposal_receipt",return_value=receipt):
            with self.assertRaisesRegex(ValueError,"hash mismatch"):
                audit.review_candidate()
    def test_no_status_can_implicitly_unblock_statistical_fit(self):
        receipt=audit.review_candidate()
        self.assertTrue(all(value != "PASS" for key,value in receipt["gates"].items()
                            if key in ("year_serial_dependence_aware_gamma_interval",
                                       "year_process_nugget_external_identification",
                                       "independent_holdout_producer_and_seeds")))
if __name__=="__main__":
    unittest.main()
