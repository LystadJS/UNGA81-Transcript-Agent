"""Independent linear-algebra audit of the temporal covariance grid search.

No UN text. Reimplements GLS and profile-REML by Cholesky whitening, rather than
calling temporal_covariance.annual_gls or its precomputed inverse matrices.
"""
import math
import unittest
import numpy as np
from scipy.linalg import solve_triangular
from scipy.stats import t as student_t
from synthetic_worlds import draw_world,source_mask
from temporal_covariance import fit_year_covariance,RHO_GRID,NUGGET_GRID

def independent_exact_solution(y,n,rho,lam):
    T=len(y)
    idx=np.arange(T)
    A=(1-lam)*rho**np.abs(idx[:,None]-idx[None,:])
    A+=lam*np.diag(99/np.asarray(n))
    L=np.linalg.cholesky(A)
    X=np.column_stack([np.ones(T),np.r_[np.zeros(T//2),np.ones(T//2)]])
    q=solve_triangular(L,X,lower=True)
    z=solve_triangular(L,y,lower=True)
    S=np.linalg.inv(q.T@q)
    beta=S@(q.T@z)
    residual=z-q@beta
    sig2=max(1e-12,float(residual@residual/(T-2)))
    information=np.linalg.slogdet(q.T@q)[1]
    loss=2*np.log(np.diag(L)).sum()+information+(T-2)*np.log(sig2)
    return (float(loss),float(beta[1]),float(sig2*S[1,1]))

def verify_one(T,mask,world,rep):
    z=draw_world(T,mask,world,rep,20261013)
    y=z['year_means']; n=z['n_eff']
    candidate=[]
    for rho in RHO_GRID:
        for lam in NUGGET_GRID:
            candidate.append((rho,lam,*independent_exact_solution(y,n,rho,lam)))
    best=min(candidate,key=lambda row:row[2])
    fit=fit_year_covariance(y,n)
    assert (fit['fit_rho'],fit['fit_nugget'])==best[:2],(T,mask,world,rep,best,fit)
    assert abs(fit['reml_objective']-best[2])<1e-9
    assert abs(fit['estimated_interval'].beta-best[3])<1e-9
    half=student_t.ppf(.95,T-3)*math.sqrt(best[4])
    assert abs(fit['estimated_interval'].lower-(best[3]-half))<1e-9
    assert abs(fit['estimated_interval'].upper-(best[3]+half))<1e-9
    q=student_t.ppf(.95,T-2)
    lowers=[x[3]-q*math.sqrt(x[4]) for x in candidate]
    uppers=[x[3]+q*math.sqrt(x[4]) for x in candidate]
    assert abs(fit['covariance_grid_envelope'].lower-min(lowers))<1e-9
    assert abs(fit['covariance_grid_envelope'].upper-max(uppers))<1e-9

class TemporalCovarianceIndependentTests(unittest.TestCase):
    def test_frozen_cholesky_reml_and_envelope_72_fixtures(self):
        cases=0
        for T in (8,16,24):
            for mask in ('near_census','two_stage'):
                for world in ('iid_year','serial_year','informative_selection'):
                    for rep in (0,1,3,7):
                        verify_one(T,mask,world,rep)
                        cases+=1
        self.assertEqual(cases,72)
    def test_first_stage_two_meetings_per_quartile_and_weights(self):
        for T in (8,16,24):
            meeting,p,available=source_mask(T,'two_stage',20261013)
            for year in range(T//2):
                for q in range(4):
                    # Fixed actor-to-meeting mapping can leave a sampled meeting
                    # without an actor in some sparse designs; here 99 actors
                    # distribute over 12 meetings, so all 8 draws occur.
                    included={int(meeting[i,year]) for i in range(99)
                              if available[i,year] and q*3<=meeting[i,year]<(q+1)*3}
                    self.assertEqual(len(included),2)
                self.assertTrue(np.allclose(p[:,year],2/3))
            self.assertTrue(np.allclose(p[:,T//2:],1))
    def test_frozen_rho_estimator_never_receives_truth(self):
        d=draw_world(16,'two_stage','serial_year',0,20261013)
        assert d['true_rho']==.65
        m=fit_year_covariance(d['year_means'],d['n_eff'])
        self.assertTrue(m['all_parameters_estimated_not_oracle'])
        self.assertIn(m['fit_rho'],RHO_GRID)
        self.assertIn(m['fit_nugget'],NUGGET_GRID)
        self.assertFalse(hasattr(m['estimated_interval'],'true_rho'))
    def test_refusal_of_bad_year_identity_or_denominator(self):
        d=draw_world(16,'near_census','iid_year',2,20261013)
        n=d['n_eff'].copy()
        n[0]=101
        with self.assertRaisesRegex(ValueError,'Unverifiable source-year'):
            fit_year_covariance(d['year_means'],n)
        with self.assertRaises(ValueError):
            fit_year_covariance(d['year_means'][:7],n[:7])

if __name__=='__main__':
    unittest.main(verbosity=2)
