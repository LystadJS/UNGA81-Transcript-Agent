import unittest
import numpy as np
from calibration import Design, covariance, generate, identifiable, estimate_year_covariance, metadata_compatible, real_fit

class SyntheticTests(unittest.TestCase):
    def test_covariance_positive_definite(self):
        for rho in (0, .65, -.5):
            self.assertGreater(np.linalg.eigvalsh(covariance(16, rho, .3)).min(), 0)
    def test_determinism(self):
        d = Design(16, .65, .2, .3, 1.0)
        self.assertEqual(generate(d, 42), generate(d, 42))
        self.assertNotEqual(generate(d, 42), generate(d, 43))
    def test_mnar_without_audit_refused(self):
        rows = generate(Design(16, .65, .2, 0, 2), 7)
        self.assertFalse(identifiable(rows)[0])
    def test_sparse_year_refusal(self):
        with self.assertRaisesRegex(ValueError, "insufficient"):
            estimate_year_covariance(np.ones(16))
    def test_incompatible_cohorts_refused(self):
        a = dict(schema_version="v1", source_design_id="a", population_hash="a",
                 representation_fingerprint="a", year_definition="calendar",
                 sampling_frame_hash="a")
        b = dict(a, source_design_id="b")
        with self.assertRaisesRegex(ValueError, "incompatible"):
            metadata_compatible(a,b)
    def test_real_fit_forbidden(self):
        with self.assertRaises(PermissionError):
            real_fit()
if __name__ == "__main__":
    unittest.main()
