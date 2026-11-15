"""Independent development-only hierarchical response/external-variance diagnostics.

No real source/holdout imports and no statistical acceptance from engineering tests.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
import numpy as np
from .v3_nuisance import IdentificationFailure
from .v3_hierarchical_external import (
    estimate_year_effects_covariance,hierarchical_conditional_gamma,
    external_scale_upper,bonferroni_continuous_covariance,
    ALPHA_TOTAL,ALPHA_CALIBRATION,ALPHA_CONTRAST)
from .v3_hierarchical_external_study import (
    GAMMA_WORLDS,COV_WORLDS,GAMMA_METHODS,COV_METHODS,
    seed,generate_response,generate_external_covariance,development_study)

class HierarchicalExternalTests(unittest.TestCase):
    def test_fresh_development_seed_and_blinded_observations(self):
        self.assertEqual(seed("test"),seed("test"))
        self.assertNotEqual(seed("test"),seed("other"))
        one,truth=generate_response(GAMMA_WORLDS[1],1)
        two,_=generate_response(GAMMA_WORLDS[1],1)
        np.testing.assert_array_equal(one["value"],two["value"])
        self.assertNotIn("conditional_gamma",one)
        self.assertEqual(truth["conditional_gamma"],-1.25)
        self.assertTrue(np.isnan(one["value"][~(one["responded"]|one["audited"])]).all())
        self.assertFalse(one["at_risk"][:2,:,0].any())

    def test_hierarchical_nuisance_is_observed_fit_not_oracle(self):
        one,_=generate_response(GAMMA_WORLDS[0],3)
        try:
            result=hierarchical_conditional_gamma(one)
        except IdentificationFailure as err:
            self.assertTrue(str(err))
        else:
            self.assertTrue(np.isfinite(result["gamma_hat"]))
            self.assertGreater(result["gamma_hessian_se_diagnostic"],0)
            self.assertTrue(result["nuisance_estimated_not_oracle"])
            self.assertTrue(result["estimation_is_two_stage"])
            self.assertGreaterEqual(result["nuisance_profile_gap"],0)
            self.assertFalse(result["gamma_interval_calibrated"])
            self.assertFalse(result["real_fit_authorized"])
            self.assertEqual(result["holdout_attempted"],0)

    def test_hierarchical_profile_succeeds_for_invented_annual_intercepts(self):
        rng=np.random.default_rng(1)
        annual=np.r_[rng.normal(0,.4,8),rng.normal(.2,.4,8)]
        result=estimate_year_effects_covariance(annual,np.full(16,.025))
        self.assertTrue(result["nuisance_estimated_from_observed_year_intercepts"])
        self.assertIn(result["rho_hat"],(0.,.35,.7,.88))
        self.assertGreaterEqual(result["profile_fits_available"],2)
        self.assertFalse(result["nuisance_recovery_certified"])

    def test_no_audit_mnar_and_hidden_outcome_refused(self):
        absent,_=generate_response(GAMMA_WORLDS[4],2)
        with self.assertRaises(IdentificationFailure):
            hierarchical_conditional_gamma(absent)
        observed,_=generate_response(GAMMA_WORLDS[0],2)
        mask=np.argwhere(observed["included"]&~observed["responded"]&~observed["audited"])
        self.assertGreater(len(mask),0)
        observed["value"][tuple(mask[0])]=1000
        with self.assertRaisesRegex(IdentificationFailure,"leaked"):
            hierarchical_conditional_gamma(observed)

    def test_invalid_annual_covariance_receipt_refused(self):
        with self.assertRaises(IdentificationFailure):
            estimate_year_effects_covariance(np.ones(8),np.ones(8))
        with self.assertRaises(IdentificationFailure):
            estimate_year_effects_covariance(np.zeros(16),np.zeros(16))

    def test_external_independent_scale_receipt_and_alpha_allocation(self):
        observed,truth=generate_external_covariance(COV_WORLDS[0],4)
        external=external_scale_upper(observed["external_calibration"],
                                      target_design_id="fictional_calendar_year_scalar_v3")
        self.assertGreater(external["variance_upper"],external["variance_estimate"])
        self.assertEqual(external["independent_world_count"],40)
        self.assertAlmostEqual(ALPHA_CALIBRATION+ALPHA_CONTRAST,ALPHA_TOTAL)
        self.assertFalse(external["externally_authenticated_real_world"])
        self.assertFalse(external["real_fit_authorized"])

    def test_bonferroni_continuous_gaussian_bound_is_assumption_conditional(self):
        observed,truth=generate_external_covariance(COV_WORLDS[0],4)
        f=bonferroni_continuous_covariance(observed["annual"],observed["external_calibration"],
                  rho_range=(0,.85),nugget_fraction_range=(0,.70),
                  target_design_id="fictional_calendar_year_scalar_v3")
        self.assertTrue(f["conditional_90_bound_if_all_assumptions_hold"])
        self.assertGreater(f["critical_value"],1.6448536269514722)
        self.assertFalse(f["historical_source_scale_verified"])
        self.assertFalse(f["statistical_freeze_accepted"])
        self.assertEqual(f["holdout_attempted"],0)

    def test_external_population_shift_and_dependency_rejected(self):
        for cell in (COV_WORLDS[3],COV_WORLDS[4]):
            observed,_=generate_external_covariance(cell,0)
            with self.assertRaisesRegex(IdentificationFailure,"provenance or comparability"):
                external_scale_upper(observed["external_calibration"],
                                     target_design_id="fictional_calendar_year_scalar_v3")

    def test_unknown_population_label_and_fake_real_receipt_rejected(self):
        observed,_=generate_external_covariance(COV_WORLDS[0],1)
        with self.assertRaisesRegex(IdentificationFailure,"mismatch"):
            external_scale_upper(observed["external_calibration"],
                                 target_design_id="unrealistic_real_population")
        data=dict(observed["external_calibration"])
        data["synthetic_development_only"]=False
        with self.assertRaisesRegex(IdentificationFailure,"contract absent"):
            external_scale_upper(data,target_design_id="fictional_calendar_year_scalar_v3")

    def test_no_external_scale_or_source_fingerprint_is_not_fabricated(self):
        observed,_=generate_external_covariance(COV_WORLDS[0],0)
        receipt=dict(observed["external_calibration"])
        receipt["independent_world_samples"]=False
        with self.assertRaises(IdentificationFailure):
            bonferroni_continuous_covariance(observed["annual"],receipt,
                 rho_range=(0,.85),nugget_fraction_range=(0,.70),
                 target_design_id="fictional_calendar_year_scalar_v3")

    def test_development_all_failures_retained_and_no_release(self):
        summary,ledger=development_study(6)
        self.assertEqual(summary["gamma_method_attempted"],6*len(GAMMA_WORLDS)*len(GAMMA_METHODS))
        self.assertEqual(summary["covariance_method_attempted"],6*len(COV_WORLDS)*len(COV_METHODS))
        self.assertEqual(summary["gamma_method_attempted"],
             summary["gamma_method_completed"]+summary["gamma_method_refused"])
        self.assertEqual(summary["covariance_method_attempted"],
             summary["covariance_method_completed"]+summary["covariance_method_refused"])
        self.assertEqual(len(ledger),summary["failure_ledger_entries"])
        self.assertEqual(len(ledger),summary["gamma_method_refused"]+summary["covariance_method_refused"])
        self.assertEqual(summary["v3_holdout_attempted"],0)
        self.assertEqual(summary["real_original_source_files_read"],0)
        self.assertFalse(summary["statistical_freeze_accepted"])
        for method in GAMMA_METHODS:
            row=next(z for z in summary["gamma_scenarios"]
                 if z["scenario"]=="missing_outcome_audit_T16" and z["method"]==method)
            self.assertEqual(row["completed"],0)
        for method in COV_METHODS:
            for case in ("shifted_external_population_T16","dependent_external_worlds_T16"):
                row=next(z for z in summary["covariance_scenarios"]
                         if z["scenario"]==case and z["method"]==method)
                self.assertEqual(row["completed"],0)

    def test_holdout_and_real_modes_rejected_without_files(self):
        module="research.longitudinal.temporal_calibration_v2.v3_hierarchical_external_study"
        with tempfile.TemporaryDirectory() as d:
            for phase in ("holdout","real"):
                target=Path(d)/phase
                x=subprocess.run([sys.executable,"-m",module,"--phase",phase,
                    "--out",str(target)],capture_output=True,text=True,timeout=20)
                self.assertNotEqual(x.returncode,0)
                self.assertFalse(target.exists())

if __name__=="__main__":
    unittest.main()
