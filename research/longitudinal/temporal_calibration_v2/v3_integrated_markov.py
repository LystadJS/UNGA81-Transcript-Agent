"""Prospective v3 DEVELOPMENT ONLY: exact finite-state integrated response likelihood.

Synthetic binary outcomes Y and response R with latent two-state Markov
calendar-year propensity U. The conditional response logit slope is gamma;
original meeting sampling must be ignorable, and a genuinely randomized
missing-Y audit with known q is mandatory. Missing nonrespondent outcomes are
integrated, never imputed. The latent Markov year state is exactly summed by
the forward algorithm, rather than estimated then plugged in.

This is NOT a Gaussian AR1 likelihood or validated real UN source estimator.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit,logsumexp

MODEL='un.w4.v3.synthetic-two-state-integrated-markov.v1'
BOUNDS=((-3,3),(-3.5,.5),(-3,3),(-2.5,2.5),(.08,2.2),(.51,.96))
PARAMS=('response_intercept','conditional_gamma','outcome_intercept',
        'outcome_state_loading','response_state_magnitude','year_stay_probability')

class NoIdentifiedFit(ValueError):
    pass

def contract_counts(observed):
    if not isinstance(observed,dict) or observed.get('model_contract')!=MODEL or \
       observed.get('synthetic_development_only') is not True:
        raise NoIdentifiedFit('synthetic integrated model contract absent')
    if observed.get('independent_randomized_outcome_audit') is not True or \
       observed.get('original_meeting_selection_ignorable') is not True or \
       observed.get('conditionally_iid_within_year') is not True:
        raise NoIdentifiedFit('source/audit/conditional-iid identification assumptions absent')
    keys=('Y_observed','included','responded','audited','at_risk',
          'inclusion_probability','audit_probability')
    if any(k not in observed for k in keys):
        raise NoIdentifiedFit('incomplete original meeting/audit source contract')
    y=np.asarray(observed['Y_observed'],dtype=float)
    incl,resp,aud,risk=[np.asarray(observed[k]) for k in ('included','responded','audited','at_risk')]
    pi,q=[np.asarray(observed[k],dtype=float) for k in ('inclusion_probability','audit_probability')]
    if y.ndim!=3 or any(a.shape!=y.shape for a in (incl,resp,aud,risk,pi,q)) or \
       y.shape[0] not in (16,24,32):
        raise NoIdentifiedFit('invalid year-meeting-actor dimensions')
    if any(a.dtype.kind!='b' for a in (incl,resp,aud,risk)):
        raise NoIdentifiedFit('invalid original meeting/response indicators')
    if np.any((resp|aud)&~incl) or np.any(resp&aud) or np.any(incl&~risk):
        raise NoIdentifiedFit('original meeting/speech response lineage failure')
    if np.any(incl&((pi<=0)|(pi>1)|~np.isfinite(pi))):
        raise NoIdentifiedFit('original meeting sampling positivity missing')
    missing=incl&~resp
    if np.any(missing&((q<=0)|(q>1)|~np.isfinite(q))):
        raise NoIdentifiedFit('independent missing-outcome audit positivity missing')
    visible=resp|aud
    if np.any(~np.isfinite(y[visible])) or np.any(np.isfinite(y[~visible])) or \
       np.any((y[visible]!=0)&(y[visible]!=1)):
        raise NoIdentifiedFit('binary observed outcomes violated or hidden truth leaked')
    T=y.shape[0]
    counts=np.zeros((T,5),dtype=float) # respondent Y=0/1, audit Y=0/1, unrecovered
    for t in range(T):
        active=incl[t]
        if np.any(missing[t]) and not np.allclose(q[t][missing[t]],q[t][missing[t]][0]):
            raise NoIdentifiedFit('audit probability varies within year contrary to state-only outcome model')
        counts[t,0]=int(np.sum(resp[t]&(y[t]==0)))
        counts[t,1]=int(np.sum(resp[t]&(y[t]==1)))
        counts[t,2]=int(np.sum(aud[t]&(y[t]==0)))
        counts[t,3]=int(np.sum(aud[t]&(y[t]==1)))
        counts[t,4]=int(np.sum(active&~resp[t]&~aud[t]))
        if int(counts[t,0]+counts[t,1])<5 or int(counts[t,2]+counts[t,3])<3:
            raise NoIdentifiedFit('insufficient randomized missing-outcome recovery within year')
        if int(np.sum(active))!=int(np.sum(counts[t])):
            raise NoIdentifiedFit('year source sampling accounting mismatch')
    return counts

def integrated_loglikelihood(counts,theta):
    """Exact integrated marginal observed-data likelihood via Markov forward sum.

    Sampling pi and audit q factors are conditioned upon because both are
    known, independent of Y (conditional on response/year) in this synthetic
    experiment. Missing Y for (R=0,A=0) is summed over binary outcomes.
    """
    if counts.ndim!=2 or counts.shape[1]!=5:
        raise ValueError('bad synthetic observed-count tensor')
    alpha,gamma,mu,kappa,delta,stay=theta
    if not (0<stay<1 and delta>=0):
        return -np.inf
    states=np.array([-1.,1.])
    py=expit(mu+kappa*states)
    pr0=expit(alpha+delta*states)
    pr1=expit(alpha+gamma+delta*states)
    eps=1e-12
    py=np.clip(py,eps,1-eps);pr0=np.clip(pr0,eps,1-eps);pr1=np.clip(pr1,eps,1-eps)
    pmissing=(1-py)*(1-pr0)+py*(1-pr1)
    n_r0,n_r1,n_a0,n_a1,n_u=counts.T
    emission=(np.outer(n_r0+n_a0,np.log1p(-py))+
       np.outer(n_r1+n_a1,np.log(py))+
       np.outer(n_r0,np.log(pr0))+
       np.outer(n_r1,np.log(pr1))+
       np.outer(n_a0,np.log1p(-pr0))+
       np.outer(n_a1,np.log1p(-pr1))+
       np.outer(n_u,np.log(pmissing)))
    log_trans=np.log(np.array([[stay,1-stay],[1-stay,stay]]))
    log_alpha=np.full(2,-math.log(2))+emission[0]
    for e in emission[1:]:
        log_alpha=e+logsumexp(log_alpha[:,None]+log_trans,axis=0)
    return float(logsumexp(log_alpha))

def estimate_integrated_response(observed, *, maxiter=110):
    """Fit six nuisance/interest parameters from exactly integrated observed data.

    Multi-start and finite-difference joint curvature are development diagnostics.
    The continuous-Gaussian AR1/random actor or original source audit model is
    NOT fitted or validated; no inferential interval is certified.
    """
    if type(maxiter) is not int or maxiter not in (80,110,160):
        raise NoIdentifiedFit('unapproved development optimization limit')
    counts=contract_counts(observed)
    starts=((-0.4,-1.1,-0.25,0.3,0.5,0.65),
            (-0.2,-1.5,0.0,0.8,1.0,0.84))
    attempts=[]
    for i,start in enumerate(starts):
        opt=minimize(lambda p:-integrated_loglikelihood(counts,p),
                     np.asarray(start,dtype=float),method='L-BFGS-B',bounds=BOUNDS,
                     options={'maxiter':maxiter,'ftol':1e-10,'gtol':1e-5})
        if np.isfinite(opt.fun):
            attempts.append((float(opt.fun),i,opt))
    if not attempts:
        raise NoIdentifiedFit('integrated response likelihood had no finite optimizer candidate')
    attempts.sort(key=lambda z:z[0])
    loss,index,best=attempts[0]
    if (not best.success) and float(np.max(np.abs(best.jac)))>0.03:
        raise NoIdentifiedFit('integrated response likelihood failed optimizer convergence')
    if abs(best.x[1]-BOUNDS[1][0])<.002 or abs(best.x[1]-BOUNDS[1][1])<.002:
        raise NoIdentifiedFit('conditional gamma reached identification boundary')
    at_boundary=[name for p,name,(lo,hi) in zip(best.x,PARAMS,BOUNDS)
                 if abs(p-lo)<.015 or abs(p-hi)<.015]
    second_gap=float(attempts[1][0]-loss) if len(attempts)>1 else None
    # Numerical agreement between starts is not evidence of identification.
    # Inspect joint likelihood curvature while retaining weak nuisance flags.
    theta=np.asarray(best.x,dtype=float)
    h=np.full(len(theta),.002);h[-1]=.001
    f=lambda x:-integrated_loglikelihood(counts,x)
    f0=f(theta);H=np.zeros((len(theta),len(theta)))
    for i in range(len(theta)):
        u=np.zeros(len(theta));u[i]=h[i]
        H[i,i]=(f(theta+u)+f(theta-u)-2*f0)/(h[i]**2)
        for j in range(i):
            v=np.zeros(len(theta));v[j]=h[j]
            H[i,j]=(f(theta+u+v)-f(theta+u-v)-f(theta-u+v)+f(theta-u-v))/(4*h[i]*h[j])
            H[j,i]=H[i,j]
    eigenvalues=np.linalg.eigvalsh((H+H.T)/2)
    cond=float(eigenvalues[-1]/eigenvalues[0]) if eigenvalues[0]>0 else None
    weak=bool(at_boundary or eigenvalues[0]<=.01 or cond is not None and cond>1e4)
    return {'method':'exact_two_state_year_markov_integrated_response',
            'conditional_gamma_hat':float(best.x[1]),
            'nuisance_estimated_not_oracle':True,
            'year_stay_probability_hat':float(best.x[5]),
            'latent_response_variance_delta_hat':float(best.x[4]**2),
            'outcome_state_loading_hat':float(best.x[3]),
            'estimated_parameters':{k:float(v) for k,v in zip(PARAMS,best.x)},
            'negative_loglikelihood':loss,'optimizer_success':bool(best.success),
            'optimizer_multistart_count':len(starts),
            'optimizer_finite_candidates':len(attempts),
            'multistart_optimizer_agreement_gap':second_gap,
            'joint_curvature_min_eigenvalue':float(eigenvalues[0]),
            'joint_curvature_condition':cond,
            'nuisance_boundary_parameters':at_boundary,
            'weakly_identified_year_nuisance':weak,
            'integrates_missing_Y_for_unrecovered_nonrespondents':True,
            'integrates_latent_serial_year_state_exactly':True,
            'model_is_finite_state_not_gaussian_ar1':True,
            'source_selection_model_integrated':False,
            'year_actor_meeting_dependence_integrated':False,
            'conditional_gamma_interval_calibrated':False,
            'statistical_freeze_accepted':False,'real_fit_authorized':False,
            'v3_holdout_attempted':0}
