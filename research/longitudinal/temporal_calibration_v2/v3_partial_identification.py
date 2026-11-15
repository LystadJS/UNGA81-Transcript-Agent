"""V3 source-safe formal population identification / finite-sample gamma-set alternatives.

The estimand is a common conditional within-calendar-year *binary-outcome*
response log odds ratio gamma. No-audit unrestricted MNAR identifies the
entire real line and MUST return NO_FIT.

With known population respondent-positive proportions and defended bounds on
missing-positive proportions, the interval is sharp under a common-gamma logit
response model and free annual intercepts. With independently randomized
missing-outcome audits, Clopper-Pearson intervals with Bonferroni allocation over
all 2*T strata yield an honest conservative gamma confidence set *conditional*
on IID Bernoulli outcomes within year and defensible original sampling/audit q.
No original-source audit supports these assumptions for real UN transcripts.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.special import logit
from scipy.stats import beta
from .v3_integrated_markov import contract_counts,NoIdentifiedFit

def population_gamma_identification(respondent_positive, missing_positive_bounds=None,
                                    *, population_moments_certified=False,
                                    independent_bounds_justified=False):
    """Sharp population conditional gamma bounds; not sampling uncertainty."""
    p=np.asarray(respondent_positive,dtype=float)
    if p.ndim!=1 or not len(p) in (16,24,32) or not np.isfinite(p).all() or np.any((p<=0)|(p>=1)):
        raise NoIdentifiedFit('valid known population respondent-outcome proportions required')
    if missing_positive_bounds is None:
        return {'status':'NO_FIT_UNRESTRICTED_MNAR','identified_lower':-math.inf,
                'identified_upper':math.inf,'point_identified':False,
                'requires_independent_missing_outcome_audit_or_defended_bounds':True,
                'real_fit_authorized':False,'v3_holdout_attempted':0}
    if population_moments_certified is not True or independent_bounds_justified is not True:
        raise NoIdentifiedFit('independent external missing-outcome bounds not justified')
    bounds=np.asarray(missing_positive_bounds,float)
    if bounds.shape!=(len(p),2) or not np.isfinite(bounds).all() or \
       np.any(bounds[:,0]<0) or np.any(bounds[:,1]>1) or np.any(bounds[:,0]>bounds[:,1]):
        raise NoIdentifiedFit('invalid missing-outcome population bounds')
    lows=[];highs=[]
    for respondent,(a,b) in zip(p,bounds):
        lows.append(float(logit(respondent)-logit(b)))
        highs.append(float(logit(respondent)-logit(a)))
    lower=max(lows);upper=min(highs)
    return {'status':'POPULATION_SHARP_SET' if lower<=upper else 'REFUSE_COMMON_GAMMA_MODEL_INCOMPATIBLE',
            'identified_lower':float(lower),'identified_upper':float(upper),
            'year_bounds':[{'lower':x,'upper':y} for x,y in zip(lows,highs)],
            'point_identified':bool(lower==upper and np.isfinite(lower)),
            'continuous_year_parameter_intersection':True,
            'validity_requires_known_population_moments':True,
            'finite_sample_uncertainty_included':False,
            'real_fit_authorized':False,'v3_holdout_attempted':0}

def clopper_pearson(k,n,two_sided_alpha):
    if type(k) is not int or type(n) is not int or not (0<=k<=n) or n<=0 or \
       not (0<two_sided_alpha<1):
        raise NoIdentifiedFit('invalid exact binomial confidence data')
    a=two_sided_alpha
    lower=0.0 if k==0 else float(beta.ppf(a/2,k,n-k+1))
    upper=1.0 if k==n else float(beta.ppf(1-a/2,k+1,n-k))
    return lower,upper

def audited_gamma_confidence_set(observed, *, family_alpha=.1):
    """Simultaneous exact-binomial confidence set for common conditional gamma.

    Conditional on any path of serially dependent latent calendar-year states,
    both respondent Y and independently audited nonrespondent Y are binomial
    samples *within each year*, by the synthetic IID data contract. Bonferroni
    across 2*T stratum proportions does not require independent years.
    Repeated actor/meeting clustering can violate within-year IID: fail closed.
    """
    if family_alpha!=.1:
        raise NoIdentifiedFit('unapproved family-wise error budget')
    counts=contract_counts(observed)
    T=len(counts)
    alpha_each=family_alpha/(2*T)
    lows=[];highs=[];data=[]
    for t,(r0,r1,a0,a1,unrecovered) in enumerate(counts):
        n_resp=int(r0+r1);n_aud=int(a0+a1)
        p_low,p_high=clopper_pearson(int(r1),n_resp,alpha_each)
        m_low,m_high=clopper_pearson(int(a1),n_aud,alpha_each)
        lower=float(logit(p_low)-logit(m_high))
        upper=float(logit(p_high)-logit(m_low))
        lows.append(lower);highs.append(upper)
        data.append({'year_index':t,'respondents':n_resp,
            'audited_nonrespondents':n_aud,'unrecovered_nonrespondents':int(unrecovered),
            'respondent_positive':int(r1),'audit_positive':int(a1),
            'gamma_lower':lower,'gamma_upper':upper})
    lo=max(lows);hi=min(highs)
    if lo>hi:
        status='REFUSE_INCOMPATIBLE_COMMON_CONDITIONAL_GAMMA'
    elif not np.isfinite(lo) or not np.isfinite(hi):
        status='NO_FIT_UNINFORMATIVE_GAMMA_SET'
    else:
        status='SYNTHETIC_CONDITIONAL_GAMMA_CONFIDENCE_SET'
    return {'status':status,'gamma_lower':float(lo),'gamma_upper':float(hi),
        'gamma_width':float(hi-lo) if lo<=hi else None,
        'per_year_sample_counts_and_bounds':data,
        'distinct_calendar_years':T,'simultaneous_binomial_families':2*T,
        'alpha_each_two_sided_binomial':alpha_each,'family_alpha':family_alpha,
        'conditional_binomial_CP_valid_under_declared_iid_source_design':True,
        'independent_calendar_years_required':False,
        'repeated_actor_meeting_dependence_supported':False,
        'historical_original_source_audit_verified':False,
        'marginal_gamma_identified':False,
        'real_fit_authorized':False,'v3_holdout_attempted':0}
