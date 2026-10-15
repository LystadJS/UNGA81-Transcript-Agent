"""Finite-T gamma block-refit and continuous covariance bound acceptance tests.

Only new artificial development worlds. No v2 engine import or v3 holdout.
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
import numpy as np
from .v3_nuisance import IdentificationFailure
from .v3_finite_year_continuous import (
    finite_year_block_refit,continuous_covariance_upper,
    continuous_contrast_sensitivity, verify_continuous_bound)
from .v3_finite_year_study import (
    GAMMA_WORLDS,COV_WORLDS,GAMMA_METHODS,COV_METHODS,
    generate_response,generate_covariance,run_development)

class FiniteYearAndContinuousTests(unittest.TestCase):
    def test_new_generator_reproducible_and_blinds_truth(self):
        one,t=generate_response(GAMMA_WORLDS[0],2)
        two,_=generate_response(GAMMA_WORLDS[0],2)
        np.testing.assert_array_equal(one["value"],two["value"])
        self.assertNotIn("common_conditional_gamma",one)
        self.assertFalse(one["at_risk"][:2,:,0].any())
        self.assertTrue(np.isnan(one["value"][~(one["responded"]|one["audited"])]).all())
        self.assertEqual(t["common_conditional_gamma"],-1.25)

    def test_block_bootstrap_refits_whole_years_and_remains_unapproved(self):
        observed,_=generate_response(GAMMA_WORLDS[0],2)
        out=finite_year_block_refit(observed,seed=4281,repetitions=12,block_years=4)
        self.assertEqual(out["attempted"],12)
        self.assertEqual(out["completed"]+out["failed"],12)
        self.assertTrue(out["status"].startswith("DEVELOPMENT") or out["status"].startswith("REFUSED"))
        self.assertFalse(out["t16_interval_calibrated"])
        self.assertFalse(out["real_fit_authorized"])
        self.assertFalse(out["holdout_attempted"])

    def test_block8_refuses_16_years(self):
        observed,_=generate_response(GAMMA_WORLDS[0],2)
        with self.assertRaisesRegex(IdentificationFailure,"insufficient whole-year"):
            finite_year_block_refit(observed,seed=3,repetitions=12,block_years=8)

    def test_no_outcome_audit_refuses_before_bootstrap(self):
        observed,_=generate_response(GAMMA_WORLDS[-1],1)
        with self.assertRaises(IdentificationFailure):
            finite_year_block_refit(observed,seed=2,repetitions=12)

    def test_continuous_bound_conservative_over_interior_points(self):
        b=continuous_covariance_upper(years=16,rho_range=(0,.85),
             nugget_fraction_range=(0,.7),external_total_scale_upper=.12,
             external_independent_provenance=True)
        self.assertTrue(b["termwise_bound_guaranteed_for_all_continuous_rho"])
        for rho in np.linspace(0,.85,17):
            for lam in np.linspace(0,.7,15):
                z=verify_continuous_bound(b,rho=float(rho),lam=float(lam),
                                           variance_scale=.12)
                self.assertTrue(z["assumptions_hold"])
                self.assertTrue(z["variance_bounded"])
        self.assertFalse(b["empirical_coverage_calibrated"])
        self.assertFalse(b["real_fit_authorized"])

    def test_continuous_bound_wide_contains_narrow_under_fixed_scale(self):
        common=dict(years=16,external_total_scale_upper=.12,
                    external_independent_provenance=True)
        wide=continuous_covariance_upper(**common,rho_range=(0,.85),
                         nugget_fraction_range=(0,.7))
        narrow=continuous_covariance_upper(**common,rho_range=(0,.65),
                         nugget_fraction_range=(0,.4))
        self.assertGreaterEqual(wide["upper_variance"],narrow["upper_variance"]-1e-12)

    def test_external_bound_absent_or_invalid_refuses(self):
        with self.assertRaisesRegex(IdentificationFailure,"upper bound absent"):
            continuous_covariance_upper(years=16,rho_range=(0,.85),
              nugget_fraction_range=(0,.7),external_total_scale_upper=.12,
              external_independent_provenance=False)
        with self.assertRaises(IdentificationFailure):
            continuous_covariance_upper(years=16,rho_range=(-.2,.85),
              nugget_fraction_range=(0,.7),external_total_scale_upper=.12,
              external_independent_provenance=True)
        with self.assertRaises(IdentificationFailure):
            continuous_covariance_upper(years=16,rho_range=(0,.85),
              nugget_fraction_range=(0,.7),external_total_scale_upper=None,
              external_independent_provenance=True)

    def test_dgp_outside_assumptions_is_reported_not_certified(self):
        b=continuous_covariance_upper(years=16,rho_range=(0,.85),
               nugget_fraction_range=(0,.7),external_total_scale_upper=.12,
               external_independent_provenance=True)
        self.assertFalse(verify_continuous_bound(b,rho=.92,lam=.35,variance_scale=.075)["assumptions_hold"])
        self.assertFalse(verify_continuous_bound(b,rho=.65,lam=.35,variance_scale=.30)["assumptions_hold"])

    def test_guaranteed_bound_is_conditional_and_never_real_certified(self):
        obs,truth=generate_covariance(COV_WORLDS[0],5)
        b=continuous_contrast_sensitivity(obs["annual"],rho_range=(0,.85),
               nugget_fraction_range=(0,.7),external_total_scale_upper=.12,
               external_independent_provenance=True)
        self.assertTrue(b["conditional_gaussian_coverage_if_assumptions_hold"])
        self.assertFalse(b["unconditional_frequentist_coverage_claim"])
        self.assertFalse(b["source_selection_bias_included"])
        self.assertFalse(b["assumed_scale_upper_externally_certified_by_model"])
        self.assertFalse(b["real_fit_authorized"])
        self.assertTrue(np.isfinite(b["width"]))

    def test_complete_development_attempt_and_failure_ledger(self):
        result,ledger=run_development(repetitions=6,bootstrap_reps=12)
        self.assertEqual(result["gamma_method_attempted"],6*len(GAMMA_WORLDS)*len(GAMMA_METHODS))
        self.assertEqual(result["covariance_method_attempted"],6*len(COV_WORLDS)*len(COV_METHODS))
        self.assertEqual(result["gamma_method_completed"]+result["gamma_method_refused"],
                         result["gamma_method_attempted"])
        self.assertEqual(result["gamma_bootstrap_completed"]+result["gamma_bootstrap_failed"],
                         result["gamma_bootstrap_attempted"])
        self.assertEqual(result["covariance_method_completed"]+result["covariance_method_refused"],
                         result["covariance_method_attempted"])
        self.assertEqual(len(ledger),result["failure_ledger_entries"])
        self.assertEqual(len(ledger),result["gamma_method_refused"]+
            result["gamma_bootstrap_failed"]+result["covariance_method_refused"])
        self.assertFalse(result["statistical_acceptance"])
        self.assertEqual(result["v3_holdout_attempted"],0)
        no_audit=[x for x in result["gamma_scenarios"] if x["scenario"]=="no_outcome_audit_T16"]
        self.assertEqual(len(no_audit),3)
        self.assertTrue(all(x["completed"]==0 and x["failed"]==6 for x in no_audit))
        refused_block8=[x for x in result["gamma_scenarios"]
              if x["years"]==16 and x["method"]=="year_block8"]
        self.assertTrue(all(x["completed"]==0 for x in refused_block8))
        for x in result["gamma_scenarios"]:
            self.assertFalse(x["calibrated_interval"])

    def test_no_holdout_or_real_cli(self):
        module="research.longitudinal.temporal_calibration_v2.v3_finite_year_study"
        with tempfile.TemporaryDirectory() as tmp:
            for phase in ("holdout","real"):
                p=Path(tmp)/phase
                proc=subprocess.run([sys.executable,"-m",module,"--phase",phase,
                     "--out",str(p)],capture_output=True,text=True,timeout=15)
                self.assertNotEqual(proc.returncode,0)
                self.assertFalse(p.exists())

if __name__=="__main__":
    unittest.main()
