"""Independent mathematical and source-safe regression tests for v3 integrated Markov."""
from __future__ import annotations
import itertools
import math
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
import numpy as np
from scipy.special import expit,logsumexp
from .v3_integrated_markov import (MODEL,NoIdentifiedFit,contract_counts,
    integrated_loglikelihood,estimate_integrated_response)
from .v3_partial_identification import (population_gamma_identification,
    audited_gamma_confidence_set,clopper_pearson)
from .v3_integrated_study import (SCENARIOS,METHODS,generate,run_development,seed)

class IntegratedResponseAndSharpPartialIdentification(unittest.TestCase):
    def test_integrated_forward_sum_equals_independent_latent_path_enumeration(self):
        counts=np.array([[2,4,1,3,5],[5,1,2,4,8],[1,3,3,2,4]],dtype=float)
        theta=np.array([-.35,-1.25,-.2,.65,.8,.82])
        a,g,mu,kappa,delta,stay=theta
        paths=[]
        for sequence in itertools.product((0,1),repeat=3):
            logpath=-math.log(2)
            for t,k in enumerate(sequence):
                if t>0:
                    logpath+=math.log(stay if k==sequence[t-1] else 1-stay)
                z=2*k-1
                py=expit(mu+kappa*z)
                pr0=expit(a+delta*z)
                pr1=expit(a+g+delta*z)
                r0,r1,au0,au1,unknown=counts[t]
                logpath+=(r0+au0)*math.log(1-py)+(r1+au1)*math.log(py)
                logpath+=r0*math.log(pr0)+r1*math.log(pr1)
                logpath+=au0*math.log(1-pr0)+au1*math.log(1-pr1)
                logpath+=unknown*math.log((1-py)*(1-pr0)+py*(1-pr1))
            paths.append(logpath)
        self.assertAlmostEqual(integrated_loglikelihood(counts,theta),
                              logsumexp(paths),places=10)

    def test_reproducible_development_and_truth_separation(self):
        a,t=generate(SCENARIOS[1],3)
        b,_=generate(SCENARIOS[1],3)
        self.assertEqual(seed('a'),seed('a'))
        self.assertNotEqual(seed('a'),seed('b'))
        np.testing.assert_array_equal(a['Y_observed'],b['Y_observed'])
        self.assertNotIn('true_gamma',a)
        self.assertEqual(t['true_gamma'],-1.25)
        self.assertTrue(np.isnan(a['Y_observed'][~(a['responded']|a['audited'])]).all())
        self.assertFalse(a['at_risk'][:2,:,0].any())
        self.assertEqual(a['model_contract'],MODEL)

    def test_full_year_integrated_likelihood_estimates_without_oracle(self):
        observed,_=generate(SCENARIOS[1],0)
        out=estimate_integrated_response(observed)
        self.assertTrue(np.isfinite(out['conditional_gamma_hat']))
        self.assertTrue(out['integrates_latent_serial_year_state_exactly'])
        self.assertTrue(out['integrates_missing_Y_for_unrecovered_nonrespondents'])
        self.assertTrue(out['nuisance_estimated_not_oracle'])
        self.assertTrue(out['model_is_finite_state_not_gaussian_ar1'])
        self.assertFalse(out['conditional_gamma_interval_calibrated'])
        self.assertFalse(out['real_fit_authorized'])
        self.assertEqual(out['v3_holdout_attempted'],0)
        self.assertNotIn('true_stay',out)

    def test_missing_audit_refuses_integrated_and_partial(self):
        observed,_=generate(SCENARIOS[5],0)
        for fn in (estimate_integrated_response,audited_gamma_confidence_set):
            with self.assertRaisesRegex(NoIdentifiedFit,'assumptions absent'):
                fn(observed)

    def test_weak_audit_refuses_without_inventing_missing_Y(self):
        observed,_=generate(SCENARIOS[4],0)
        for fn in (estimate_integrated_response,audited_gamma_confidence_set):
            with self.assertRaisesRegex(NoIdentifiedFit,'insufficient randomized'):
                fn(observed)

    def test_actor_year_dependence_refuses_assumed_conditional_iid(self):
        observed,_=generate(SCENARIOS[6],0)
        for fn in (estimate_integrated_response,audited_gamma_confidence_set):
            with self.assertRaisesRegex(NoIdentifiedFit,'assumptions absent'):
                fn(observed)

    def test_corrupt_hidden_outcome_refuses(self):
        observed,_=generate(SCENARIOS[1],0)
        hidden=np.argwhere(observed['included']&~observed['responded']&~observed['audited'])
        observed['Y_observed'][tuple(hidden[0])]=1
        with self.assertRaisesRegex(NoIdentifiedFit,'hidden truth leaked'):
            estimate_integrated_response(observed)

    def test_corrupt_meeting_pi_and_source_lineage_refuses(self):
        observed,_=generate(SCENARIOS[1],0)
        picked=tuple(np.argwhere(observed['included'])[0])
        observed['inclusion_probability'][picked]=0
        with self.assertRaisesRegex(NoIdentifiedFit,'sampling positivity'):
            contract_counts(observed)

    def test_no_audit_population_identification_is_the_entire_real_line(self):
        p=np.full(16,.7)
        out=population_gamma_identification(p)
        self.assertEqual(out['status'],'NO_FIT_UNRESTRICTED_MNAR')
        self.assertEqual(out['identified_lower'],-math.inf)
        self.assertEqual(out['identified_upper'],math.inf)
        self.assertFalse(out['real_fit_authorized'])

    def test_population_sharp_bounds_and_endpoints(self):
        p=np.full(16,.7)
        constraints=np.tile([.30,.50],(16,1))
        out=population_gamma_identification(p,constraints,
              population_moments_certified=True,independent_bounds_justified=True)
        self.assertEqual(out['status'],'POPULATION_SHARP_SET')
        self.assertAlmostEqual(out['identified_lower'],math.log(.7/.3),places=10)
        self.assertAlmostEqual(out['identified_upper'],2*math.log(.7/.3),places=10)
        self.assertFalse(out['finite_sample_uncertainty_included'])

    def test_population_constraints_cannot_be_fabricated(self):
        p=np.full(16,.7)
        with self.assertRaisesRegex(NoIdentifiedFit,'not justified'):
            population_gamma_identification(p,np.tile([.3,.5],(16,1)))

    def test_exact_binomial_cp_boundary_cases(self):
        self.assertEqual(clopper_pearson(0,10,.05)[0],0)
        self.assertEqual(clopper_pearson(10,10,.05)[1],1)
        self.assertGreater(clopper_pearson(3,10,.05)[1],3/10)

    def test_audited_gamma_confidence_set_is_source_assumption_conditional(self):
        observed,truth=generate(SCENARIOS[1],0)
        out=audited_gamma_confidence_set(observed)
        self.assertEqual(out['status'],'SYNTHETIC_CONDITIONAL_GAMMA_CONFIDENCE_SET')
        self.assertAlmostEqual(out['simultaneous_binomial_families']*
                               out['alpha_each_two_sided_binomial'],.1)
        self.assertLessEqual(out['gamma_lower'],truth['true_gamma'])
        self.assertGreaterEqual(out['gamma_upper'],truth['true_gamma'])
        self.assertFalse(out['independent_calendar_years_required'])
        self.assertFalse(out['repeated_actor_meeting_dependence_supported'])
        self.assertFalse(out['historical_original_source_audit_verified'])

    def test_mismatched_year_common_gamma_is_refused(self):
        p=np.r_[np.full(8,.85),np.full(8,.2)]
        bounds=np.tile([.45,.55],(16,1))
        out=population_gamma_identification(p,bounds,
           population_moments_certified=True,independent_bounds_justified=True)
        self.assertEqual(out['status'],'REFUSE_COMMON_GAMMA_MODEL_INCOMPATIBLE')

    def test_holdout_and_real_cli_never_create_outputs(self):
        module="research.longitudinal.temporal_calibration_v2.v3_integrated_study"
        with tempfile.TemporaryDirectory() as d:
            for phase in ("holdout","real"):
                target=Path(d)/phase
                result=subprocess.run([sys.executable,"-m",module,
                     "--phase",phase,"--repetitions","4",
                     "--out",str(target)],capture_output=True,text=True,timeout=20)
                self.assertNotEqual(result.returncode,0)
                self.assertFalse(target.exists())

    def test_full_new_development_attempt_accounting(self):
        report,failures=run_development(4)
        self.assertEqual(report['attempted_method_fits'],4*len(SCENARIOS)*len(METHODS))
        self.assertEqual(report['attempted_method_fits'],report['completed_method_fits']+report['refused_method_fits'])
        self.assertEqual(len(failures),report['failure_ledger_count'])
        self.assertEqual(report['v3_holdout_attempted'],0)
        self.assertEqual(report['original_source_bytes_read'],0)
        self.assertFalse(report['statistical_freeze_accepted'])
        self.assertTrue(all(x['method'] in METHODS and 0<=x['replicate']<4 for x in failures))
        for case in ('weak_audit_T16','no_audit_T16','actor_effect_stress_T16'):
            for row in (z for z in report['scenarios'] if z['scenario']==case):
                self.assertEqual(row['completed'],0)

if __name__=='__main__':
    unittest.main()
