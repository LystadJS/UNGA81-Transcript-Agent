"""New development-only checks for serial response and covariance sensitivity."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
import numpy as np
from .v3_nuisance import IdentificationFailure
from .v3_serial_partial import (estimate_serial_response, covariance_union,
                                 independent_measurement_bounds)
from .v3_serial_partial_study import (seed, generate_gamma, generate_covariance,
                                       GAMMA_CASES, COV_CASES, development_study,
                                       GAMMA_METHODS, COV_METHODS)

class NewProspectiveDevelopmentTests(unittest.TestCase):
    def test_disjoint_new_seed_and_no_truth_leakage(self):
        a,truth=generate_gamma(GAMMA_CASES[2],3)
        b,_=generate_gamma(GAMMA_CASES[2],3)
        self.assertEqual(seed('repeat'),seed('repeat'))
        self.assertNotEqual(seed('repeat'),seed('different'))
        np.testing.assert_array_equal(a['value'],b['value'])
        self.assertNotIn('gamma_true',a)
        self.assertEqual(truth['gamma_true'],-1.25)
        self.assertTrue(np.isnan(a['value'][~(a['responded']|a['audited'])]).all())
        self.assertFalse(a['at_risk'][:2,:,0].any())

    def test_year_fixed_effects_estimate_not_oracle(self):
        o,truth=generate_gamma(GAMMA_CASES[2],8)
        f=estimate_serial_response(o,'year_fixed_effects')
        self.assertTrue(np.isfinite(f['gamma_hat']))
        self.assertGreater(f['se_diagnostic'],0)
        self.assertFalse(f['interval_calibrated'])
        self.assertFalse(f['real_fit_authorized'])
        self.assertFalse(f['structural_gamma_recovery_established'])

    def test_estimated_year_ar1_not_generator_true_rho(self):
        o,_=generate_gamma(GAMMA_CASES[1],2)
        result=estimate_serial_response(o,'estimated_ar1_year_effects')
        self.assertIsNotNone(result['rho_year_propensity_hat'])
        self.assertTrue(0<=result['rho_year_propensity_hat']<=.9)
        self.assertTrue(result['year_intercepts_not_observed_truth'])
        self.assertFalse(result['interval_calibrated'])

    def test_no_audit_refusal_every_gamma_family(self):
        o,_=generate_gamma(GAMMA_CASES[-1],1)
        for method in GAMMA_METHODS:
            with self.assertRaisesRegex(IdentificationFailure,'no independent missing-outcome audit'):
                estimate_serial_response(o,method)

    def test_hidden_transcript_outcome_tamper_refused(self):
        o,_=generate_gamma(GAMMA_CASES[0],1)
        hidden=np.argwhere(o['included'] &~o['responded'] &~o['audited'])
        self.assertGreater(len(hidden),0)
        o['value'][tuple(hidden[0])]=999
        with self.assertRaisesRegex(IdentificationFailure,'leaked'):
            estimate_serial_response(o,'year_fixed_effects')

    def test_missing_independent_audit_probability_refused(self):
        o,_=generate_gamma(GAMMA_CASES[0],1)
        index=tuple(np.argwhere(o['included'] &~o['responded'])[0])
        o['independent_audit_probability'][index]=0
        with self.assertRaisesRegex(IdentificationFailure,'positivity'):
            estimate_serial_response(o,'year_fixed_effects')

    def test_observed_development_point_bias_improvement_not_approval(self):
        # Development evidence only: correlated year shocks show pooled
        # response model is misspecified; FE separates year propensities.
        v,_=development_study(16)
        pooled=next(x for x in v['gamma'] if x['scenario']=='serial_correlated_T16'
                    and x['method']=='pooled_logit')
        fixed=next(x for x in v['gamma'] if x['scenario']=='serial_correlated_T16'
                   and x['method']=='year_fixed_effects')
        self.assertGreater(pooled['completed'],0)
        self.assertLess(abs(fixed['gamma_bias_completed']),abs(pooled['gamma_bias_completed']))
        self.assertFalse(fixed['interval_calibrated'])

    def test_nested_sensitivity_envelopes_are_not_confidence_intervals(self):
        o,_=generate_covariance(COV_CASES[0],2)
        wide=covariance_union(o['annual'],alternative='wide')
        narrow=covariance_union(o['annual'],alternative='narrow')
        self.assertLessEqual(wide['lower'],narrow['lower']+1e-12)
        self.assertGreaterEqual(wide['upper'],narrow['upper']-1e-12)
        self.assertFalse(wide['frequentist_coverage_calibrated'])
        self.assertFalse(wide['nuisance_parameters_estimated'])
        self.assertFalse(wide['real_fit_authorized'])

    def test_external_replicate_bounds_condition_not_nugget_truth(self):
        o,_=generate_covariance(COV_CASES[0],2)
        measured=independent_measurement_bounds(o['first_replicate'],
              o['second_replicate'],source_independent=o['independent_pair_provenance'])
        wide=covariance_union(o['annual'],alternative='wide')
        conditioned=covariance_union(o['annual'],alternative='externally_constrained',
                                     measurement_noise_lower_bound=measured['variance_lower'])
        self.assertLessEqual(wide['lower'],conditioned['lower']+1e-12)
        self.assertGreaterEqual(wide['upper'],conditioned['upper']-1e-12)
        self.assertGreater(conditioned['grid_rejected_by_external_noise'],0)
        self.assertFalse(measured['intrinsic_year_nugget_identified'])
        self.assertFalse(conditioned['frequentist_coverage_calibrated'])

    def test_correlated_external_measurements_refuse_every_envelope(self):
        o,_=generate_covariance(COV_CASES[-1],1)
        with self.assertRaisesRegex(IdentificationFailure,'independence not verified'):
            independent_measurement_bounds(o['first_replicate'],o['second_replicate'],
                                           source_independent=o['independent_pair_provenance'])

    def test_external_calibration_absent_and_bad_support_refused(self):
        o,_=generate_covariance(COV_CASES[0],2)
        with self.assertRaisesRegex(IdentificationFailure,'external measurement lower bound'):
            covariance_union(o['annual'],alternative='externally_constrained')
        with self.assertRaisesRegex(IdentificationFailure,'incompatible with covariance grid'):
            covariance_union(o['annual'],alternative='externally_constrained',
                             measurement_noise_lower_bound=100)
        with self.assertRaises(IdentificationFailure):
            covariance_union(o['annual'][:4])

    def test_full_attempt_accounting_and_refusals(self):
        result,ledger=development_study(8)
        self.assertEqual(result['response_attempted'],8*len(GAMMA_CASES)*len(GAMMA_METHODS))
        self.assertEqual(result['covariance_attempted'],8*len(COV_CASES)*len(COV_METHODS))
        self.assertEqual(result['response_attempted'],result['response_completed']+result['response_failed'])
        self.assertEqual(result['covariance_attempted'],result['covariance_completed']+result['covariance_failed'])
        self.assertEqual(len(ledger),result['failure_ledger_count'])
        self.assertEqual(result['failure_ledger_count'],result['response_failed']+result['covariance_failed'])
        self.assertFalse(result['freeze_approved'])
        self.assertFalse(result['statistical_acceptance'])
        self.assertEqual(result['v3_holdout_attempted'],0)
        for method in GAMMA_METHODS:
            case=next(x for x in result['gamma'] if x['scenario']=='no_audit_T16' and x['method']==method)
            self.assertEqual(case['failed'],8)
        for method in COV_METHODS:
            case=next(x for x in result['covariance'] if x['scenario']=='shared_measurement_error_T16' and x['method']==method)
            self.assertEqual(case['failed'],8)

    def test_holdout_real_cli_are_impossible(self):
        runner='research.longitudinal.temporal_calibration_v2.v3_serial_partial_study'
        with tempfile.TemporaryDirectory() as d:
            for phase in ('holdout','real'):
                output=Path(d)/phase
                proc=subprocess.run([sys.executable,'-m',runner,'--phase',phase,
                            '--repetitions','8','--out',str(output)],
                            capture_output=True,text=True,timeout=20)
                self.assertNotEqual(proc.returncode,0)
                self.assertFalse(output.exists())

if __name__=='__main__':unittest.main()
