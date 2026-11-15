"""Development-only v3 nuisance estimation and falsification controls.

No access to oracle truth, historical sources, or confirmatory holdout.
Imported observations must have independently randomized missing-outcome audits.
"""
from __future__ import annotations
import hashlib
import numpy as np
from scipy.special import expit

class IdentificationFailure(ValueError):
    pass

def response_gamma(observed: dict, *, min_recovered=20, max_condition=1e8):
    """Weighted conditional logit of response R on recovered outcome Y.

    Inclusion probabilities enter as 1/pi. Nonresponders are subsampled by
    randomized, documented q, so their response=0 likelihood contribution is
    weighted 1/(pi*q). Responders contribute 1/pi. This is pseudo-likelihood;
    sandwich/grouped uncertainty is NOT implemented. No confidence interval.
    """
    if observed.get("independent_audit_provenance") is not True:
        raise IdentificationFailure("independent randomized missing-outcome audit absent")
    required=("value","included","responded","audited","at_risk",
              "inclusion_probability","independent_audit_probability")
    if any(k not in observed for k in required):
        raise IdentificationFailure("incomplete observation design")
    y,s,r,a,risk,pi,q=(np.asarray(observed[k]) for k in required)
    if not all(x.shape==y.shape for x in (s,r,a,risk,pi,q)) or y.ndim!=3:
        raise IdentificationFailure("invalid observation dimensions")
    if any(x.dtype!=np.bool_ for x in (s,r,a,risk)):
        raise IdentificationFailure("invalid design indicators")
    if np.any((r|a)&~s) or np.any(r&a) or np.any(s&~risk):
        raise IdentificationFailure("response/audit lineage incompatible")
    if np.any(s&((pi<=0)|(pi>1)|~np.isfinite(pi))):
        raise IdentificationFailure("meeting inclusion positivity violated")
    if np.any((s&~r)&((q<=0)|(q>1)|~np.isfinite(q))):
        raise IdentificationFailure("randomized audit positivity violated")
    if np.any(~np.isfinite(y[r|a])) or np.any(np.isfinite(y[~(r|a)])):
        raise IdentificationFailure("hidden-outcome leak or invalid observed values")
    if np.sum(a)<min_recovered or np.sum(r)<min_recovered:
        raise IdentificationFailure("insufficient independently recovered response strata")
    use=r|a
    v=y[use].astype(float)
    labels=r[use].astype(float)
    weights=1/pi[use]
    weights[~labels.astype(bool)]/=q[use][~labels.astype(bool)]
    if not np.all(np.isfinite(weights)) or np.max(weights)/np.min(weights)>1e4:
        raise IdentificationFailure("response propensity weights unstable")
    mean=np.average(v,weights=weights)
    scale=np.sqrt(np.average((v-mean)**2,weights=weights))
    if scale<1e-8:
        raise IdentificationFailure("outcome slope unidentified: negligible outcome variation")
    x=np.column_stack((np.ones(len(v)),(v-mean)/scale))
    # Stable Newton likelihood with guaranteed line-search descent.
    b=np.zeros(2)
    for iteration in range(100):
        p=expit(x@b)
        gradient=x.T@(weights*(labels-p))
        hessian=(x.T*(weights*p*(1-p)))@x
        eig=np.linalg.eigvalsh(hessian)
        if eig[0]<=0 or eig[-1]/eig[0]>max_condition:
            raise IdentificationFailure("response likelihood singular / weak positivity")
        step=np.linalg.solve(hessian,gradient)
        current=float(np.sum(weights*(labels*np.log(np.clip(p,1e-15,1))+
                    (1-labels)*np.log(np.clip(1-p,1e-15,1)))))
        fraction=1.0
        for _ in range(25):
            trial=b+fraction*step
            pt=expit(x@trial)
            candidate=float(np.sum(weights*(labels*np.log(np.clip(pt,1e-15,1))+
                              (1-labels)*np.log(np.clip(1-pt,1e-15,1)))))
            if candidate>=current-1e-9:
                break
            fraction*=0.5
        else:
            raise IdentificationFailure("response likelihood failed line search")
        b=trial
        if np.max(np.abs(fraction*step))<1e-8:
            break
    else:
        raise IdentificationFailure("response likelihood did not converge")
    return dict(intercept=float(b[0]-b[1]*mean/scale),
                gamma=float(b[1]/scale),converged=True,
                observed_respondents=int(np.sum(r)),
                independently_recovered=int(np.sum(a)),
                observations_in_fit=int(np.sum(use)),
                weighted_design=True,grouped_interval_eligible=False,
                real_data_fit_authorized=False)

def replicate_nugget(receipt: dict):
    """Estimate replicate measurement-noise variance, *not* year-shock nugget.

    A validated independent replicate pair at each distinct year is needed;
    apparent calendar-year nugget is not identified by this measurement alone.
    """
    if receipt.get("independent_replicate_provenance") is not True:
        raise IdentificationFailure("independent replicate measurement provenance absent")
    if receipt.get("same_latent_year_quantity") is not True:
        raise IdentificationFailure("replicates are not measurements of the same quantity")
    a=np.asarray(receipt.get("first",[]),dtype=float)
    b=np.asarray(receipt.get("second",[]),dtype=float)
    years=np.asarray(receipt.get("years",[]))
    if a.ndim!=1 or b.shape!=a.shape or years.shape!=a.shape or len(a)<8:
        raise IdentificationFailure("insufficient independent replicate pairs")
    if len(set(years.tolist()))!=len(years) or not np.all(np.isfinite(a+b)):
        raise IdentificationFailure("duplicate years or nonfinite replicate")
    difference=a-b
    # Requires mean-zero independent replicate errors of equal variance.
    bias=float(np.mean(difference))
    if abs(bias)>0.5*np.std(difference,ddof=1):
        raise IdentificationFailure("replicate systematic bias conflicts with equal-noise design")
    variance=float(np.var(difference,ddof=1)/2)
    return dict(measurement_noise_variance=variance,
                paired_years=len(a),estimated_from_replicates=True,
                year_process_nugget_identified=False,
                external_year_nugget_eligible=False,
                real_data_fit_authorized=False)

def nonstationarity_control(annual, *, expected_break=None):
    """Exploratory split innovation check; never a calibrated hypothesis test."""
    x=np.asarray(annual,float)
    if x.ndim!=1 or len(x)<16 or not np.all(np.isfinite(x)):
        raise IdentificationFailure("insufficient annual data")
    if expected_break is None:
        expected_break=len(x)//2
    if not isinstance(expected_break,int) or not 4<=expected_break<=len(x)-4:
        raise IdentificationFailure("invalid declared contrast boundary")
    # Remove the predeclared two-era level contrast before checking dispersion.
    residual=np.r_[x[:expected_break]-np.mean(x[:expected_break]),
                   x[expected_break:]-np.mean(x[expected_break:])]
    left=residual[:expected_break]
    right=residual[expected_break:]
    v1=float(np.var(left,ddof=1))
    v2=float(np.var(right,ddof=1))
    ratio=float(max(v1,v2)/max(min(v1,v2),1e-12))
    # Prespecified descriptive alarm, not a p-value or formal stationarity test.
    alarm=bool(ratio>4)
    return dict(variance_ratio=ratio,variance_shift_alarm=alarm,
                descriptive_only=True,stationarity_verified=False,
                inference_authorized=False,years=len(x))
