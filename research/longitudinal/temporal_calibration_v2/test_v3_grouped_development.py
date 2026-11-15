"""New seeded development-only diagnostics; no v3 holdout."""
import unittest
import numpy as np
from .v3_prototype import simulate, safe_seed
from .v3_nuisance import IdentificationFailure
from .v3_grouped_development import grouped_gamma_diagnostic, paired_measurement_experiment

class GroupedDevelopmentTests(unittest.TestCase):
    def test_grouped_gamma_reports_uncalibrated_year_dependence(self):
        o,_=simulate(16,"census","audited_mnar",.65,.15,safe_seed("new-grouped-gamma-dev"))
        r=grouped_gamma_diagnostic(o)
        self.assertEqual(r["distinct_calendar_years"],16)
        self.assertLess(r["gamma"],0)
        self.assertGreater(r["gamma_year_cluster_se"],0)
        for field in ("interval_calibrated","interval_eligible","independent_years_verified",
                      "serial_year_dependence_accounted_for","real_data_fit_authorized"):
            self.assertFalse(r[field])

    def test_gamma_no_independent_audit_refused(self):
        o,_=simulate(16,"census","unaudited_mnar",.65,.15,77)
        with self.assertRaises(IdentificationFailure):grouped_gamma_diagnostic(o)

    def test_gamma_fewer_year_blocks_refused(self):
        o,_=simulate(16,"census","audited_mnar",.65,.15,77)
        with self.assertRaisesRegex(IdentificationFailure,"calendar-year"):
            grouped_gamma_diagnostic(o,min_years=17)

    def test_external_noise_experiment_is_reproducible(self):
        one=paired_measurement_experiment(seed=safe_seed("external-measure-dev"),repetitions=24)
        two=paired_measurement_experiment(seed=safe_seed("external-measure-dev"),repetitions=24)
        self.assertEqual(one,two)
        self.assertEqual(one["attempted"],24)
        self.assertGreater(one["completed"],0)
        self.assertLess(abs(one["estimate_bias"]),.05)
        self.assertFalse(one["calendar_year_nugget_recovered"])
        self.assertFalse(one["statistical_acceptance"])
        self.assertEqual(one["holdout_attempted"],0)

    def test_shared_error_stress_refuses_independent_replicates(self):
        r=paired_measurement_experiment(seed=safe_seed("shared-error-dev"),
                                        repetitions=12,shared_sd=.3)
        self.assertEqual(r["completed"],0)
        self.assertEqual(r["refused"],12)
        self.assertFalse(r["independent_replicate_assumption"])

    def test_unbounded_or_invalid_calibration_refused(self):
        for args in (dict(seed=1,repetitions=500),dict(seed=1,years=3),
                     dict(seed=1,error_sd=0),dict(seed=1,shared_sd=-1)):
            with self.assertRaises(ValueError):
                paired_measurement_experiment(**args)

if __name__=="__main__":
    unittest.main()
