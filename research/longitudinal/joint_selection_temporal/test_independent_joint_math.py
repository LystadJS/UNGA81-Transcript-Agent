"""Independent numerical checks of frozen joint-selection and covariance algebra.

No heldout calibration or real source text in these tests.
"""
from __future__ import annotations
import unittest
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from scipy.optimize import minimize
from scipy.special import expit
from joint_model import (_design_joint,_selection_logit,_temporal_reml,
    RHO_GRID,NUGGET_GRID,RIDGE)
from synthetic_dev import generate


def direct_gls(y,n,rho,nugget):
    T=len(y);age=np.arange(T)
    V=(1-nugget)*(rho**np.abs(age[:,None]-age[None,:]))
    V+=nugget*np.diag(99/n)
    L=np.linalg.cholesky(V)
    X=np.c_[np.ones(T),np.r_[np.zeros(T//2),np.ones(T//2)]]
    wX=np.linalg.solve(L,X);wy=np.linalg.solve(L,y)
    covariance=np.linalg.inv(wX.T@wX)
    coef=np.linalg.lstsq(wX,wy,rcond=None)[0]
    residual=wy-wX@coef
    sig2=max(1e-12,np.dot(residual,residual)/(T-2))
    objective=2*np.log(np.diag(L)).sum()+np.linalg.slogdet(wX.T@wX)[1]+(T-2)*np.log(sig2)
    return objective,coef[1],np.sqrt(sig2*covariance[1,1])


class IndependentModelMath(unittest.TestCase):
    def test_all_grid_candidates_cholesky_correct_minima(self):
        checked=0
        for T in (16,24,32):
            for world in ('iid_MAR','AR1_MNAR_audited'):
                frame,_=generate(T,'stratified_2_of_3',world,8)
                data=_design_joint(frame)
                z=data['years'];n=data['neff']
                independent=[]
                for rho in RHO_GRID:
                    for q in NUGGET_GRID:
                        independent.append((rho,q,*direct_gls(z,n,rho,q)))
                optimal=min(independent,key=lambda x:x[2])
                native=_temporal_reml(z,n)
                self.assertEqual((native['rho'],native['nugget']),optimal[:2])
                self.assertAlmostEqual(native['reml_objective'],optimal[2],places=8)
                self.assertAlmostEqual(native['beta'],optimal[3],places=8)
                self.assertAlmostEqual(native['se'],optimal[4],places=8)
                checked+=len(independent)
        self.assertEqual(checked,432)
    def test_logistic_random_audit_coefficients_independent_solver(self):
        for world in ('iid_MAR','AR1_MNAR_audited'):
            frame,_=generate(24,'stratified_2_of_3',world,5)
            data=_design_joint(frame)
            native=_selection_logit(data)
            obs=data['logit_r'];w=data['logit_weights']
            X=np.c_[np.ones(len(obs)),data['logit_y'],data['logit_post']]
            def objective(theta):
                eta=X@theta
                loss=np.sum(w*(np.logaddexp(0,eta)-obs*eta))+.5*RIDGE*np.dot(theta,theta)
                grad=X.T@(w*(expit(eta)-obs))+RIDGE*theta
                return float(loss),grad
            result=minimize(objective,np.zeros(3),jac=True,method='L-BFGS-B',
                options={'gtol':1e-8,'maxiter':800,'maxls':50})
            self.assertTrue(np.isfinite(result.fun))
            self.assertAlmostEqual(native['selection_gamma'],result.x[1],delta=1e-3)
    def test_failing_selection_due_to_leaked_outcomes_refused(self):
        frame,_=generate(16,'near_census','AR1_MNAR_audited',11)
        frame['y'][:,:]=3.0
        from joint_model import fit_observed,FitFailure
        with self.assertRaisesRegex(FitFailure,'leaked'):
            fit_observed(frame)

if __name__=='__main__':unittest.main(verbosity=2)
