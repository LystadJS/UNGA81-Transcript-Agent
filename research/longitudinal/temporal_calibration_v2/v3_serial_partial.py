"""V3 DEVELOPMENT ONLY: year-effect logistic response and covariance sensitivity sets.

Synthetic/untrusted observations only. No real-source interface, no holdout runner,
no frozen-v2 imports. Gamma intervals and covariance unions are diagnostics,
NOT calibrated inference, point identification, or empirical authorization.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import t as student_t, chi2
from .v3_nuisance import IdentificationFailure, response_gamma

GAMMA_METHODS = ("pooled_logit", "year_fixed_effects", "estimated_ar1_year_effects")
RHO_WIDE = (-0.20, 0.0, 0.25, 0.50, 0.70, 0.85)
RHO_NARROW = (0.0, 0.25, 0.50, 0.70)
NUGGET_WIDE = (0.0, 0.20, 0.45, 0.70)
NUGGET_NARROW = (0.0, 0.20, 0.45)


def _design(observed):
    if observed.get("independent_audit_provenance") is not True:
        raise IdentificationFailure("no independent missing-outcome audit")
    required=("value", "included", "responded", "audited", "at_risk",
              "inclusion_probability", "independent_audit_probability")
    if any(k not in observed for k in required):
        raise IdentificationFailure("missing audited response design")
    y, s, r, a, at_risk, pi, q=(np.asarray(observed[k]) for k in required)
    if y.ndim!=3 or any(v.shape!=y.shape for v in (s,r,a,at_risk,pi,q)):
        raise IdentificationFailure("invalid source-year/meeting/actor dimensions")
    if any(v.dtype.kind!='b' for v in (s,r,a,at_risk)):
        raise IdentificationFailure("invalid original meeting/response indicators")
    if np.any((r|a)&~s) or np.any(r&a) or np.any(s&~at_risk):
        raise IdentificationFailure("response/audit/original-meeting lineage conflict")
    if np.any(s&((pi<=0)|(pi>1)|~np.isfinite(pi))):
        raise IdentificationFailure("meeting selection positivity absent")
    missing=s&~r
    if np.any(missing&((q<=0)|(q>1)|~np.isfinite(q))):
        raise IdentificationFailure("independent outcome-audit positivity absent")
    visible=r|a
    if np.any(~np.isfinite(y[visible])) or np.any(np.isfinite(y[~visible])):
        raise IdentificationFailure("missing transcript truth leaked into observed outcomes")
    T=y.shape[0]
    if T not in (16,24,32):
        raise IdentificationFailure("unsupported independent calendar-year count")
    if not np.all((r.reshape(T,-1).sum(axis=1)>=5)&
                  (a.reshape(T,-1).sum(axis=1)>=3)):
        raise IdentificationFailure("year-specific response and recovered-outcome support absent")
    vals=y[visible]
    labels=r[visible].astype(float)
    w=1/pi[visible]
    audit=a[visible]
    w[audit]/=q[visible][audit]
    if not np.isfinite(w).all() or w.max()/w.min()>1e4:
        raise IdentificationFailure("two-stage weights unstable")
    group=np.broadcast_to(np.arange(T)[:,None,None],y.shape)[visible]
    return vals,labels,w,group,T


def _fit_years(vals,labels,w,group,T, *, rho=None, penalty=0.0):
    """Weighted year intercept logit; optional AR1 penalty on inferred year effects.

    Parameter gamma is not penalized; AR1 smoothing rho estimated from the
    observed independent-audit year-fixed-effect fit, never generator truth.
    """
    center=np.average(vals,weights=w)
    scale=float(np.sqrt(np.average((vals-center)**2,weights=w)))
    if scale<1e-7:
        raise IdentificationFailure("outcome variation insufficient")
    xs=(vals-center)/scale
    counts=np.bincount(group,weights=w*labels,minlength=T)
    totals=np.bincount(group,weights=w,minlength=T)
    if np.any(counts<=0) or np.any(counts>=totals):
        raise IdentificationFailure("within-year response overlap absent")
    init=np.zeros(T+1)
    init[:T]=np.log(counts/(totals-counts))
    # Q penalty acts only on annual intercept deviations from the time mean.
    Q=np.eye(T)
    if rho is not None:
        if not (0<=rho<=.9) or penalty<0:
            raise IdentificationFailure("invalid prospective year-effect penalty")
        for t in range(1,T):
            row=np.zeros(T);row[t]=1;row[t-1]=-rho
            Q+=np.outer(row,row)
        C=np.eye(T)-np.ones((T,T))/T
        Q=C@Q@C

    def fn(theta):
        eta=theta[group]+theta[-1]*xs
        logloss=float(np.sum(w*(np.logaddexp(0,eta)-labels*eta)))
        p=expit(eta)
        res=w*(p-labels)
        grad=np.zeros(T+1)
        np.add.at(grad,group,res)
        grad[-1]=float(np.sum(res*xs))
        if penalty:
            logloss+=.5*penalty*float(theta[:T]@Q@theta[:T])
            grad[:T]+=penalty*(Q@theta[:T])
        return logloss,grad
    fitted=minimize(fn,init,method="L-BFGS-B",jac=True,
                    options={"maxiter":220,"ftol":1e-11,"gtol":1e-6})
    if not fitted.success and np.max(np.abs(fitted.jac))>1e-3:
        raise IdentificationFailure("annual response propensity optimizer did not converge")
    theta=fitted.x
    gamma=float(theta[-1]/scale)
    alphas=theta[:T]-theta[-1]*center/scale
    p=expit(theta[group]+theta[-1]*xs)
    # Conditional profile information for standardized within-year slope.
    W=w*p*(1-p)
    h_aa=np.bincount(group,weights=W,minlength=T)
    h_ag=np.bincount(group,weights=W*xs,minlength=T)
    h_gg=float(np.sum(W*xs*xs))
    if penalty:
        hessian=np.diag(h_aa)+penalty*Q
        try:
            conditional=h_gg-h_ag@np.linalg.solve(hessian,h_ag)
        except np.linalg.LinAlgError as e:
            raise IdentificationFailure("singular year-effect information") from e
    else:
        conditional=h_gg-float(np.sum(h_ag*h_ag/h_aa))
    if conditional<=1e-7:
        raise IdentificationFailure("gamma not identifiable after year effects")
    # Year-level score, with conditional nuisance projection (fixed effects
    # intercept scores vanish at exact MLE, but not for penalized model).
    raw_scores=np.bincount(group,weights=w*(labels-p)*xs,minlength=T)
    year_scores=np.bincount(group,weights=w*(labels-p),minlength=T)
    if penalty:
        profile=raw_scores-h_ag@np.linalg.solve(hessian,np.eye(T))@np.diag(year_scores)
        # Diagonal of projection above yields a vector of annual gamma scores.
    else:
        profile=raw_scores-h_ag*year_scores/h_aa
    profile-=np.mean(profile)
    profile*=scale  # Convert standardized gamma scores to native-outcome slope units.
    return {"gamma_hat":gamma,"intercept_by_year":alphas,"profile_scores":profile,
            "information":conditional*scale*scale,"optimizer_success":bool(fitted.success),
            "max_gradient":float(np.max(np.abs(fitted.jac))),"year_count":T,
            "estimated_from_audited_outcomes_only":True}


def _score_hac(fit, lag):
    score=fit["profile_scores"]
    T=len(score)
    meat=float(score@score)
    for k in range(1,lag+1):
        meat+=2*(1-k/(lag+1))*float(score[k:]@score[:-k])
    meat*=T/(T-1)
    if not math.isfinite(meat) or meat<=1e-11:
        raise IdentificationFailure("nonpositive serial gamma score long-run variance")
    se=math.sqrt(meat)/fit["information"]
    if not math.isfinite(se) or se<=0:
        raise IdentificationFailure("gamma HAC uncertainty unavailable")
    return float(se)


def estimate_serial_response(observed, method, *, lag=2):
    """Development-only point and diagnostic SE, NEVER eligible T16 inference."""
    if method not in GAMMA_METHODS or lag not in (0,1,2):
        raise IdentificationFailure("unknown response propensity candidate")
    vals,labels,w,year,T=_design(observed)
    if method=="pooled_logit":
        p=response_gamma(observed)
        return {"gamma_hat":p["gamma"],"method":method,
                "rho_year_propensity_hat":None,"se_diagnostic":None,
                "year_intercepts_estimated":False,"interval_calibrated":False,
                "holdout_executed":False,"real_fit_authorized":False}
    base=_fit_years(vals,labels,w,year,T)
    rho_hat=None
    fit=base
    if method=="estimated_ar1_year_effects":
        alphas=base["intercept_by_year"]
        demean=alphas-alphas.mean()
        denom=float(np.sum(demean[:-1]**2))
        if denom<1e-10:
            raise IdentificationFailure("serial-year propensity unidentifiable")
        rho_hat=float(np.clip(np.sum(demean[1:]*demean[:-1])/denom,0,.9))
        fit=_fit_years(vals,labels,w,year,T,rho=rho_hat,penalty=6.0)
    se=_score_hac(fit,lag)
    return {"gamma_hat":fit["gamma_hat"],"method":method,
            "rho_year_propensity_hat":rho_hat,
            "se_diagnostic":se,"lag_years":lag,
            "year_intercepts_estimated":True,
            "year_intercepts_not_observed_truth":True,
            "interval_calibrated":False,
            "structural_gamma_recovery_established":False,
            "independent_years_assumed":False,
            "holdout_executed":False,"real_fit_authorized":False}


def independent_measurement_bounds(first,second,*,source_independent:bool,confidence:float=.90):
    """Normal-replicate measurement variance interval, never year-process nugget.

    Assumes two conditionally independent, equal-variance, Gaussian measurement
    errors on a common latent value in externally sampled independent pairs.
    Calibration certainty is conditional on all assumptions and source provenance.
    """
    if source_independent is not True:
        raise IdentificationFailure("external replicate independence not verified")
    if confidence!=.90:
        raise IdentificationFailure("unsupported external replicate confidence")
    a,b=np.asarray(first,float),np.asarray(second,float)
    if a.ndim!=1 or b.shape!=a.shape or len(a)<16 or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise IdentificationFailure("insufficient independent Gaussian measurement pairs")
    difference=a-b
    variance=float(np.var(difference,ddof=1)/2)
    if not math.isfinite(variance) or variance<=0:
        raise IdentificationFailure("replicate measurement variance nonpositive")
    df=len(a)-1
    lower=float(df*variance/chi2.ppf(.95,df))
    upper=float(df*variance/chi2.ppf(.05,df))
    return {"variance_estimate":variance,"variance_lower":lower,"variance_upper":upper,
            "pairs":len(a),"independent_gaussian_assumed":True,
            "intrinsic_year_nugget_identified":False,
            "empirical_fit_authorized":False}


def covariance_union(annual, *, alternative="wide",measurement_noise_lower_bound=None):
    """Union of hypothetical GLS 90%-shaped intervals over fixed nuisance grid.

    This is a *sensitivity envelope*, not an unconditional frequentist CI or
    proof true nuisance covariance belongs to declared bounds. All nuisance
    values are explicit assumptions; scale and beta estimated from annual data.
    """
    x=np.asarray(annual,dtype=float)
    if x.ndim!=1 or len(x) not in (16,24,32) or not np.all(np.isfinite(x)):
        raise IdentificationFailure("insufficient valid annual source-year observations")
    if alternative not in ("wide","narrow","externally_constrained"):
        raise IdentificationFailure("unsupported prospective covariance sensitivity set")
    T=len(x);nuisance_rho=RHO_NARROW if alternative=="narrow" else RHO_WIDE
    nuisance_nug=NUGGET_NARROW if alternative=="narrow" else NUGGET_WIDE
    if alternative=="externally_constrained" and (measurement_noise_lower_bound is None or
            not isinstance(measurement_noise_lower_bound,(int,float)) or
            not math.isfinite(measurement_noise_lower_bound) or measurement_noise_lower_bound<=0):
        raise IdentificationFailure("independent external measurement lower bound required")
    X=np.column_stack((np.ones(T),np.arange(T)>=T//2))
    lag=np.abs(np.subtract.outer(np.arange(T),np.arange(T)))
    crit=float(student_t.ppf(.95,T-3))
    intervals=[];profiles=[];rejected_by_external=0
    for rho in nuisance_rho:
        for lam in nuisance_nug:
            C=(1-lam)*rho**lag+lam*np.eye(T)
            try:
                W=np.linalg.solve(C,X)
                V=np.linalg.inv(X.T@W)
                beta=V@W.T@x
                residual=x-X@beta
                scale=float(residual@np.linalg.solve(C,residual)/(T-2))
                se=math.sqrt(max(scale*V[1,1],0))
                if scale<=1e-10 or se<=0 or not math.isfinite(se):
                    raise IdentificationFailure("degenerate source-year covariance likelihood")
                ll=float(np.linalg.slogdet(C)[1]+np.linalg.slogdet(X.T@W)[1]
                         +(T-2)*math.log(scale))
            except np.linalg.LinAlgError as e:
                raise IdentificationFailure("singular nuisance covariance grid") from e
            if alternative=="externally_constrained" and scale*lam < measurement_noise_lower_bound:
                rejected_by_external += 1
                continue
            intervals.append((float(beta[1]-crit*se),float(beta[1]+crit*se)))
            profiles.append((rho,lam,ll))
    if not intervals:
        raise IdentificationFailure("external measurement bounds incompatible with covariance grid")
    low=min(a for a,_ in intervals)
    high=max(b for _,b in intervals)
    best=min(z[2] for z in profiles)
    weak=sum(z[2]<=best+2.71 for z in profiles)
    return {"alternative":alternative,"lower":low,"upper":high,"width":high-low,
            "rho_assumed_grid":list(nuisance_rho),"effective_nugget_fraction_assumed_grid":list(nuisance_nug),
            "grid_attempted":len(nuisance_rho)*len(nuisance_nug),"grid_completed":len(intervals),
            "grid_rejected_by_external_noise":rejected_by_external,
            "external_measurement_bound_used":alternative=="externally_constrained",
            "profile_weak_support_count":weak,"nuisance_parameters_estimated":False,
            "annual_scale_estimated":True,"partial_identification_sensitivity_only":True,
            "frequentist_coverage_calibrated":False,"real_fit_authorized":False,
            "holdout_executed":False}
