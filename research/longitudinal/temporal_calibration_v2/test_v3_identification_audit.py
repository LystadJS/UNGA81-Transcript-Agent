"""Source-free prospective v3 statistical identification refusal regressions."""
import copy
import json
from pathlib import Path
import unittest
from .v3_freeze_candidate import proposal_receipt
from .v3_identification_audit import (
    conditional_vs_marginal_gamma, no_audit_mnar_counterexample,
    year_nugget_measurement_alias, nuisance_grid_truth_witness,
    independent_freeze_decision,
)

ROOT=Path(__file__).resolve().parent


class ProspectiveIdentificationTests(unittest.TestCase):
    def test_conditional_gamma_is_not_marginal_gamma(self):
        result=conditional_vs_marginal_gamma()
        self.assertAlmostEqual(result["conditional_gamma"],-1.25)
        self.assertAlmostEqual(result["marginal_logit_contrast"],-0.7948343916886047,places=10)
        self.assertGreater(result["absolute_difference"],.4)
        self.assertFalse(result["identical_estimand"])
        self.assertFalse(result["real_fit_authorized"])

    def test_no_audit_observed_data_allow_opposing_gamma(self):
        x=no_audit_mnar_counterexample()
        estimates=[v["compatible_gamma"] for v in x["candidates"]]
        self.assertGreater(estimates[0],0)
        self.assertLess(estimates[1],0)
        self.assertTrue(x["observed_data_indistinguishable"])
        self.assertFalse(x["gamma_point_identified"])
        self.assertEqual(x["candidates"][0]["observed_response_rate"],
                         x["candidates"][1]["observed_response_rate"])

    def test_identical_covariance_different_diagonal_components(self):
        c=year_nugget_measurement_alias()
        self.assertEqual(c["first_variance_decomposition"],[.025,.0144])
        self.assertAlmostEqual(c["second_variance_decomposition"][0],.015)
        self.assertLess(c["max_absolute_covariance_difference"],1e-14)
        self.assertFalse(c["intrinsic_nugget_identified_from_annual_covariance"])
        self.assertFalse(c["finite_year_recovery_certified"])

    def test_covariance_alias_persists_with_more_years(self):
        for years in (16,24,32,48):
            c=year_nugget_measurement_alias(years=years)
            self.assertLess(c["max_absolute_covariance_difference"],1e-14)

    def test_development_narrow_grid_excludes_true_nugget(self):
        w=nuisance_grid_truth_witness()
        self.assertGreater(w["evaluator_true_effective_diagonal_fraction"],.49)
        self.assertEqual(w["assumed_narrow_lambda_max"],.45)
        self.assertFalse(w["true_nuisance_in_narrow_range"])
        self.assertFalse(w["true_covariance_is_grid_point"])
        self.assertTrue(w["finite_discrete_grid_is_not_continuous_identification_region"])

    def test_development_envelopes_not_frequentist_certification(self):
        w=nuisance_grid_truth_witness()
        self.assertTrue(w["observed_beta_sensitivity_hit_does_not_validate_nuisance_set"])

    def test_independent_candidate_must_refuse_freeze(self):
        candidate=proposal_receipt()
        config=json.loads((ROOT/"v3_design_proposal.json").read_text())
        decision=independent_freeze_decision(candidate,config)
        self.assertEqual(decision["status"],"STATISTICAL_FREEZE_NOT_ACCEPTED")
        self.assertEqual(decision["year_fixed_effects_estimand"],
                         "CONDITIONAL_WITHIN_YEAR_LOGIT_GAMMA_ONLY")
        for field in ("marginal_gamma_identified","serial_year_gamma_interval_calibrated",
                      "intrinsic_calendar_nugget_identified","empirical_fit_authorized",
                      "holdout_executed","coordinator_merge_authorized"):
            self.assertFalse(decision[field],field)

    def test_mutating_candidate_to_authorize_holdout_refuses(self):
        cfg=json.loads((ROOT/"v3_design_proposal.json").read_text())
        receipt=proposal_receipt()
        cfg["holdout_authorized"]=True
        with self.assertRaisesRegex(ValueError,"holdout execution"):
            independent_freeze_decision(receipt,cfg)

    def test_mutating_candidate_to_release_real_fit_refuses(self):
        cfg=json.loads((ROOT/"v3_design_proposal.json").read_text())
        receipt=proposal_receipt()
        receipt["real_fit_authorized"]=True
        with self.assertRaisesRegex(ValueError,"empirical fitting"):
            independent_freeze_decision(receipt,cfg)

    def test_coordinator_decision_evidence_conserves_attempts(self):
        evidence=json.loads((ROOT/"v3_identification_decision.json").read_text())
        self.assertEqual(evidence["decision"],"STATISTICAL_FREEZE_NOT_ACCEPTED")
        num=evidence["numerical_development"]
        self.assertEqual(num["gamma_completed"]+num["gamma_refused"],num["gamma_method_attempts"])
        self.assertEqual(num["covariance_completed"]+num["covariance_refused"],num["covariance_attempts"])
        self.assertEqual(num["gamma_refused"]+num["covariance_refused"],num["all_failed_fit_ids_retained"])
        self.assertEqual(num["correlated_year_T16"]["year_FE_diagnostic_true_hits"],25)
        self.assertEqual(num["correlated_year_T16"]["year_FE_diagnostic_fit_denominator"],29)
        self.assertFalse(evidence["v3_holdout_executed"])
        self.assertFalse(evidence["real_inference_authorized"])
        self.assertFalse(evidence["pr_merge_authorized"])
        self.assertEqual(evidence["gates"]["continuous_partial_identification_set"],"NOT_IMPLEMENTED")
        self.assertEqual(evidence["reviewer_approval_record"],
                         "NONE_NO_INDEPENDENT_HUMAN_STATISTICIAN_SIGNOFF")

    def test_nonfinite_designs_refuse(self):
        with self.assertRaises(ValueError):
            conditional_vs_marginal_gamma(gamma=float("nan"))
        with self.assertRaises(ValueError):
            no_audit_mnar_counterexample(missing_positive_fractions=(0.0,.8))
        with self.assertRaises(ValueError):
            year_nugget_measurement_alias(transfer=.1)
        with self.assertRaises(ValueError):
            nuisance_grid_truth_witness(process_variance=-1)

if __name__=="__main__":
    unittest.main()
