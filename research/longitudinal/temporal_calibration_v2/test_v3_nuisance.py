"""V3 independent development-fixture controls, NOT confirmatory holdout."""
import unittest
import numpy as np
from .v3_prototype import simulate, safe_seed
from .v3_nuisance import (
    IdentificationFailure, response_gamma, replicate_nugget,
    nonstationarity_control,
)

class NuisanceDevelopmentTests(unittest.TestCase):
    def test_independent_audited_gamma_is_feasible(self):
        observed, evaluator = simulate(16, "census", "audited_mnar", .65, .15,
                                       safe_seed("gamma-dev-fixture-01"))
        self.assertNotIn("truth", observed)
        result = response_gamma(observed)
        self.assertTrue(result["converged"])
        self.assertGreater(result["independently_recovered"], 20)
        self.assertLess(result["gamma"], 0)
        self.assertFalse(result["grouped_interval_eligible"])
        self.assertFalse(result["real_data_fit_authorized"])

    def test_known_mar_negative_control(self):
        observed, _ = simulate(16, "census", "mar", 0., 0.,
                               safe_seed("gamma-dev-mar-control"))
        result = response_gamma(observed)
        self.assertLess(abs(result["gamma"]), .45)

    def test_no_randomized_outcome_audit_refuses(self):
        observed, _ = simulate(16, "census", "unaudited_mnar", .65, .15, 44)
        with self.assertRaisesRegex(IdentificationFailure,"audit absent"):
            response_gamma(observed)

    def test_missing_outcome_injected_refuses(self):
        observed, _ = simulate(16, "census", "audited_mnar", .65, .15, 44)
        hidden = np.argwhere(observed["included"] & ~observed["responded"] & ~observed["audited"])
        self.assertGreater(len(hidden), 0)
        observed["value"][tuple(hidden[0])] = 123.0
        with self.assertRaisesRegex(IdentificationFailure,"hidden-outcome"):
            response_gamma(observed)

    def test_q_positivity_refuses(self):
        observed, _ = simulate(16, "census", "audited_mnar", .65, .15, 44)
        nonresponse=np.argwhere(observed["included"] & ~observed["responded"])
        observed["independent_audit_probability"][tuple(nonresponse[0])] = 0.
        with self.assertRaisesRegex(IdentificationFailure,"audit positivity"):
            response_gamma(observed)

    def test_weak_audit_support_refuses(self):
        observed, _ = simulate(16, "census", "audited_mnar", .65, .15, 44)
        with self.assertRaisesRegex(IdentificationFailure,"insufficient"):
            response_gamma(observed,min_recovered=100000)

    def test_independent_replicate_noise_is_not_calendar_nugget(self):
        rng=np.random.default_rng(safe_seed("measurement-dev-01"))
        latent=rng.normal(size=24)
        receipt=dict(independent_replicate_provenance=True,
                     same_latent_year_quantity=True,years=list(range(24)),
                     first=(latent+rng.normal(scale=.2,size=24)).tolist(),
                     second=(latent+rng.normal(scale=.2,size=24)).tolist())
        result=replicate_nugget(receipt)
        self.assertTrue(result["estimated_from_replicates"])
        self.assertGreater(result["measurement_noise_variance"],0)
        self.assertFalse(result["year_process_nugget_identified"])
        self.assertFalse(result["external_year_nugget_eligible"])

    def test_replication_not_independent_refuses(self):
        receipt=dict(independent_replicate_provenance=False,
                     same_latent_year_quantity=True,years=list(range(16)),
                     first=[1.]*16,second=[1.]*16)
        with self.assertRaisesRegex(IdentificationFailure,"provenance"):
            replicate_nugget(receipt)

    def test_replicate_duplicate_year_and_mean_shift_refuse(self):
        rng=np.random.default_rng(123)
        receipt=dict(independent_replicate_provenance=True,
                     same_latent_year_quantity=True,years=list(range(16)),
                     first=rng.normal(size=16).tolist(),
                     second=rng.normal(size=16).tolist())
        receipt["years"][1]=0
        with self.assertRaisesRegex(IdentificationFailure,"duplicate"):
            replicate_nugget(receipt)
        receipt["years"][1]=1
        receipt["first"]=[x+20 for x in receipt["first"]]
        with self.assertRaisesRegex(IdentificationFailure,"systematic bias"):
            replicate_nugget(receipt)

    def test_nonstationarity_alarm_on_variance_shift(self):
        rng=np.random.default_rng(97)
        annual=np.r_[rng.normal(scale=.03,size=8),
                      rng.normal(scale=2.,size=8)]
        out=nonstationarity_control(annual)
        self.assertTrue(out["variance_shift_alarm"])
        self.assertFalse(out["stationarity_verified"])
        self.assertFalse(out["inference_authorized"])

    def test_nonstationarity_small_series_refused(self):
        with self.assertRaisesRegex(IdentificationFailure,"insufficient"):
            nonstationarity_control(np.ones(8))

    def test_no_false_stationarity_certification(self):
        out=nonstationarity_control(np.random.default_rng(3).normal(size=16))
        self.assertTrue(out["descriptive_only"])
        self.assertFalse(out["stationarity_verified"])

if __name__ == "__main__":
    unittest.main()
