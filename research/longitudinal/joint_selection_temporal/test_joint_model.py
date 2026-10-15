"""Source-free redaction, numerics, two-phase identification and independent RNG controls."""
from __future__ import annotations
import unittest
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from joint_model import fit_observed,interval,NotIdentified,FitFailure,_temporal_reml
from synthetic_dev import generate
from heldout_world import independently_generate

class JointSourceTests(unittest.TestCase):
    def test_dev_replay_and_two_generator_independence(self):
        x,truth=generate(16,'stratified_2_of_3','AR1_MNAR_audited',2)
        xx,t2=generate(16,'stratified_2_of_3','AR1_MNAR_audited',2)
        self.assertTrue(np.array_equal(x['response'],xx['response']))
        self.assertTrue(np.array_equal(np.isnan(x['y']),np.isnan(xx['y'])))
        self.assertEqual(truth,t2)
        h=independently_generate(16,'stratified_2_of_3','AR1_MNAR_audited',2)
        self.assertFalse(np.array_equal(x['response'],h['observed']['response']))
        self.assertEqual(h['truth']['gamma'],-1.25)
    def test_masks_no_unobserved_outcome_leak(self):
        x,_=generate(16,'near_census','AR1_MNAR_audited',4)
        hidden=~(x['selected']&(x['response']|x['audited']))
        self.assertTrue(np.all(np.isnan(x['y'][hidden])))
        tampered=dict(x);tampered['y']=x['y'].copy();tampered['y'][0,0]=7
        if hidden[0,0]:
            with self.assertRaisesRegex(FitFailure,'leaked'):
                fit_observed(tampered)
        self.assertTrue(fit_observed(x)['true_rho_not_provided'])
    def test_no_phase2_audit_abstains_even_with_visible_responders(self):
        x,_=generate(16,'near_census','AR1_MNAR_no_audit',1)
        with self.assertRaises(NotIdentified):
            fit_observed(x)
    def test_false_independence_of_audit_refused(self):
        x,_=generate(16,'near_census','AR1_MNAR_audited',1)
        x['audit_randomized_independently_before_outcome_release']=False
        with self.assertRaises(NotIdentified):
            fit_observed(x)
    def test_actual_source_mode_requires_audit_provenance(self):
        x,_=generate(16,'near_census','AR1_MNAR_audited',1)
        x['mode']='real'
        with self.assertRaises(NotIdentified):
            fit_observed(x)
    def test_source_meeting_probability_and_two_per_quartile(self):
        d=independently_generate(16,'stratified_2_of_3','iid_MAR',0)['observed']
        meeting=np.fromfunction(lambda i,j:(7*i+3*j+i//11)%12,(99,16),dtype=int)
        for j in range(16):
            self.assertTrue(np.allclose(d['meeting_pi'][:,j],2/3))
            for group in range(4):
                sel={int(meeting[i,j]) for i in range(99)
                    if d['selected'][i,j] and 3*group<=meeting[i,j]<3*group+3}
                self.assertEqual(len(sel),2)
    def test_beta0_and_02_common_random_numbers(self):
        a,_=generate(16,'near_census','iid_MAR',4,beta=0)
        b,_=generate(16,'near_census','iid_MAR',4,beta=.20)
        self.assertTrue(np.array_equal(a['response'],b['response']))
        sel=a['selected']&a['response']
        self.assertLess(np.max(np.abs((b['y']-a['y'])[sel]-
            np.broadcast_to(np.r_[np.zeros(8),np.ones(8)*.2],(99,16))[sel])),1e-10)
    def test_temporal_gls_equivalent_independent_cholesky(self):
        y=np.linspace(-.1,.4,16)+np.sin(np.arange(16))*.1
        n=np.linspace(40,80,16)
        x=_temporal_reml(y,n)
        rho=x['rho'];nug=x['nugget']
        ar=rho**np.abs(np.subtract.outer(np.arange(16),np.arange(16)))
        cov=(1-nug)*ar+nug*np.diag(99/n)
        L=np.linalg.cholesky(cov)
        A=np.column_stack([np.ones(16),np.r_[np.zeros(8),np.ones(8)]])
        wA=np.linalg.solve(L,A);wy=np.linalg.solve(L,y)
        coef=np.linalg.lstsq(wA,wy,rcond=None)[0]
        self.assertAlmostEqual(x['beta'],coef[1],places=10)
    def test_independent_identifiable_data_fit_keeps_covariance_unknown(self):
        for world in ('iid_MAR','AR1_MAR','AR1_MNAR_audited'):
            x,truth=generate(16,'near_census',world,5)
            fit=fit_observed(x)
            self.assertIn(fit['rho'],(-.20,-.10,0.,.10,.20,.35,.50,.60,.65,.75,.85,.92))
            self.assertTrue(fit['true_selection_gamma_not_provided'])
            self.assertGreater(fit['audited_missing_n'],0)
            ci=interval(fit)
            self.assertLess(ci.lower,ci.upper)

if __name__=='__main__':unittest.main(verbosity=2)
