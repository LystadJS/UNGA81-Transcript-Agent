"""Independent developmental benchmark checks; no prospective holdout."""
from __future__ import annotations
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import numpy as np
from .v3_dependence_benchmark import (
    NAMESPACE, IdentificationFailure, development_seed, generate_response_development,
    gamma_year_score_sandwich, gamma_circular_block_score_bootstrap,
    covariance_fisher_information, generate_covariance_development,
    recovery_quasi_moments,
)
from .v3_dependence_study import run_development, GAMMA_WORLDS, COV_WORLDS, METHODS


class DependencyBenchmarkTests(unittest.TestCase):
    def observed(self, *, q=0.35, rho=0.65, response_sd=0.7, years=16, seed=13):
        return generate_response_development(years=years,rho=rho,
                 response_year_sd=response_sd,q=q,seed=seed)

    def test_new_development_namespace_and_determinism(self):
        self.assertIn("-DEV-",NAMESPACE)
        self.assertNotEqual(development_seed("panel1"), development_seed("panel2"))
        a,_=self.observed(seed=development_seed("repeat"))
        b,_=self.observed(seed=development_seed("repeat"))
        for key in ("value","included","responded","audited"):
            np.testing.assert_array_equal(a[key],b[key])
        self.assertNotIn("truth",a)
        self.assertEqual(np.sum(np.isfinite(a["value"]) & ~(a["responded"]|a["audited"])),0)

    def test_year_hac_bandwidths_and_no_ci_release(self):
        o,_=self.observed()
        methods=[gamma_year_score_sandwich(o,lag=lag) for lag in (0,1,2)]
        self.assertEqual(len({m["gamma"] for m in methods}),1)
        for m in methods:
            self.assertGreater(m["gamma_se_diagnostic"],0)
            self.assertTrue(np.isfinite(m["lag1_annual_gamma_score_correlation"]))
            self.assertFalse(m["interval_calibrated"])
            self.assertFalse(m["t16_inference_approved"])
            self.assertFalse(m["real_data_fit_authorized"])
        self.assertLess(methods[0]["gamma"],0)

    def test_circular_block_reproducible_and_unapproved(self):
        o,_=self.observed()
        one=gamma_circular_block_score_bootstrap(o,seed=development_seed("resample"))
        two=gamma_circular_block_score_bootstrap(o,seed=development_seed("resample"))
        self.assertEqual(one,two)
        self.assertEqual(one["block_years"],4)
        self.assertGreater(one["gamma_se_diagnostic"],0)
        self.assertFalse(one["response_selection_refitted"])
        self.assertFalse(one["interval_calibrated"])

    def test_no_audit_refused_all_methods(self):
        o,_=self.observed(q=0)
        for lag in (0,1,2):
            with self.assertRaisesRegex(IdentificationFailure,"audit absent"):
                gamma_year_score_sandwich(o,lag=lag)
        with self.assertRaisesRegex(IdentificationFailure,"audit absent"):
            gamma_circular_block_score_bootstrap(o,seed=1)

    def test_hidden_outcome_and_weight_corruption_refused(self):
        o,_=self.observed()
        missing=np.argwhere(o["included"]&~o["responded"]&~o["audited"])
        self.assertGreater(len(missing),0)
        o["value"][tuple(missing[0])]=99
        with self.assertRaisesRegex(IdentificationFailure,"hidden-outcome"):
            gamma_year_score_sandwich(o,lag=2)
        o,_=self.observed()
        picked=np.argwhere(o["included"]&~o["responded"])
        o["independent_audit_probability"][tuple(picked[0])]=0
        with self.assertRaisesRegex(IdentificationFailure,"audit positivity"):
            gamma_year_score_sandwich(o,lag=0)

    def test_bandwidth_and_block_budget_refused(self):
        o,_=self.observed()
        for lag in (3,-1,1.5):
            with self.assertRaisesRegex(IdentificationFailure,"bandwidth"):
                gamma_year_score_sandwich(o,lag=lag)
        for budget in (0,1000):
            with self.assertRaisesRegex(IdentificationFailure,"specification"):
                gamma_circular_block_score_bootstrap(o,seed=3,bootstrap_reps=budget)

    def test_year_noise_and_intrinsic_nugget_exactly_aliased(self):
        f=covariance_fisher_information(years=16,rho=0.65)
        self.assertEqual(f["unrestricted_rank"],3)
        self.assertEqual(f["unrestricted_parameter_count"],4)
        self.assertTrue(f["measurement_nugget_derivatives_identical"])
        self.assertFalse(f["finite_year_parameter_recovery_established"])
        self.assertFalse(f["real_data_fit_authorized"])
        self.assertGreater(f["fixed_external_noise_min_information"],0)

    def test_identification_degrades_near_rho_zero(self):
        small=covariance_fisher_information(years=16,rho=0.05)
        moderate=covariance_fisher_information(years=16,rho=0.65)
        self.assertGreater(small["fixed_external_noise_condition"],
                           100*moderate["fixed_external_noise_condition"])
        zero=covariance_fisher_information(years=16,rho=0.0)
        self.assertEqual(zero["unrestricted_rank"],2)
        self.assertEqual(zero["fixed_external_noise_min_information"],0.0)

    def test_feasible_nugget_moments_do_not_receive_truth(self):
        observed,evaluator=generate_covariance_development(
            years=32,rho=0.65,nugget_variance=.025,seed=development_seed("cov-fixture"))
        self.assertNotIn("true_rho",observed)
        self.assertNotIn("true_year_nugget_variance",observed)
        try:
            estimate=recovery_quasi_moments(observed)
        except IdentificationFailure as err:
            self.assertTrue(str(err))
        else:
            self.assertFalse(estimate["known_true_parameters_used_by_estimator"])
            self.assertFalse(estimate["inferential_eligibility"])

    def test_invalid_covariance_input_refused(self):
        with self.assertRaises(ValueError):
            covariance_fisher_information(years=5,rho=.65)
        with self.assertRaises(ValueError):
            covariance_fisher_information(years=16,rho=1)
        o,_=generate_covariance_development(years=16,rho=.65,nugget_variance=.025,seed=1)
        o["annual"][0]=np.nan
        with self.assertRaisesRegex(IdentificationFailure,"invalid exploratory"):
            recovery_quasi_moments(o)

    def test_complete_development_failure_accounting(self):
        summary,ledger=run_development(8)
        self.assertEqual(summary["gamma_panel_attempts"],len(GAMMA_WORLDS)*8)
        self.assertEqual(summary["gamma_method_attempts"],len(GAMMA_WORLDS)*len(METHODS)*8)
        self.assertEqual(summary["gamma_method_completed"]+summary["gamma_method_refusals"],
                         summary["gamma_method_attempts"])
        self.assertEqual(summary["covariance_panel_completed"]+summary["covariance_panel_refusals"],
                         len(COV_WORLDS)*8)
        self.assertEqual(len(ledger),summary["failure_ledger_count"])
        self.assertTrue(all("scenario" in entry and "replicate" in entry and "reason" in entry
                            for entry in ledger))
        self.assertFalse(summary["statistical_acceptance"])
        self.assertFalse(summary["year_nugget_identified"])
        self.assertEqual(summary["holdout_attempted"],0)
        no_audit=next(x for x in summary["gamma"] if x["scenario"]=="no_audit_T16")
        self.assertEqual(no_audit["completed"],0)
        self.assertEqual(no_audit["refused"],8)

    def test_holdout_and_real_cli_never_execute(self):
        runner="research.longitudinal.temporal_calibration_v2.v3_dependence_study"
        for phase in ("holdout","real"):
            with tempfile.TemporaryDirectory() as d:
                target=Path(d)/"must_not_exist"
                r=subprocess.run([sys.executable,"-m",runner,"--phase",phase,
                                  "--repetitions","8","--out",str(target)],
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=15)
                self.assertNotEqual(r.returncode,0)
                self.assertFalse(target.exists())

if __name__=="__main__":
    unittest.main()
