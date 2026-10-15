"""V3 freeze candidate cannot imply protocol authorization."""
import unittest
from .v3_freeze_candidate import proposal_receipt

class FreezeCandidateSafety(unittest.TestCase):
    def test_candidate_hashes_and_no_authorization(self):
        r=proposal_receipt()
        self.assertEqual(len(r["source_sha256"]),27)
        self.assertTrue(all(len(v)==64 for v in r["source_sha256"].values()))
        self.assertEqual(r["status"],"UNAPPROVED_DESIGN_CANDIDATE_NOT_FROZEN")
        self.assertFalse(r["v3_acceptance_thresholds_locked"])
        self.assertFalse(r["holdout_run"])
        self.assertFalse(r["real_fit_authorized"])
        self.assertFalse(r["response_gamma_grouped_inference_validated"])
        self.assertFalse(r["externally_measured_year_process_nugget_available"])

if __name__=="__main__":
    unittest.main()
