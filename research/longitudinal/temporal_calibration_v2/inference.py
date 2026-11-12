"""Synthetic-only source-weighted annual contrasts and feasible temporal covariance.

All estimated nuisance parameters come from visible (responded/audited) data.
Source/missing outcome states are distinct; real fitting is prohibited.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
import math
import numpy as np
from scipy.stats import t as student_t

RHO_GRID = (-0.20, 0.0, 0.10, 0.25, 0.40, 0.55, 0.70, 0.85, 0.92)
NUGGET_GRID = (0.0, 0.20, 0.40, 0.60, 0.80)
METHODS = ("iid_year", "ar1_constrained", "ar1_nugget_ridge")

class NotIdentified(ValueError):
    """Required original design or randomized second-stage outcomes unavailable."""

class FitFailure(ValueError):
    """Selected design has insufficient numerical support to estimate a contrast."""


def _require(flag: bool, message: str):
    if not flag:
        raise FitFailure(message)


def _visible_observations(obs):
    """Reject truth leakage, partial auditing, and invalid source design metadata."""
    needed = {"value", "frame", "included", "responded", "audited", "meeting", "post",
              "inclusion_probability", "audit_probability", "audit_independent"}
    if not isinstance(obs, dict) or (needed - set(obs)):
        raise NotIdentified("incomplete declared original-meeting/audit design")
    if any(k in obs for k in ("truth", "latent_outcome", "true_beta", "true_rho", "true_gamma")):
        raise NotIdentified("truth and hidden outcomes must not enter feasible estimator")
    y = np.asarray(obs["value"], dtype=float)
    _require(y.ndim == 2 and y.shape[0] in (8,16,24,32,48,64) and
             20 <= y.shape[1] <= 500, "insufficient synthetic time-series shape")
    booleans = {k: np.asarray(obs[k]) for k in ("frame","included","responded","audited")}
    if any(v.shape != y.shape or v.dtype != bool for v in booleans.values()):
        raise FitFailure("invalid source/response/audit masks")
    frame, inc, resp, audited = (booleans[k] for k in ("frame","included","responded","audited"))
    if np.any(inc & ~frame) or np.any(resp & ~inc) or np.any(audited & (~inc | resp)):
        raise NotIdentified("impossible source-selection/response/audit lineage")
    if not np.array_equal(np.isfinite(y), resp | audited):
        raise NotIdentified("hidden/missing outcomes present, or audited outcome missing")
    meeting = np.asarray(obs["meeting"])
    post = np.asarray(obs["post"])
    pi = np.asarray(obs["inclusion_probability"])
    q = np.asarray(obs["audit_probability"])
    if meeting.shape != y.shape or not np.issubdtype(meeting.dtype,np.integer) or np.any(meeting<0):
        raise NotIdentified("invalid meeting lineage")
    if post.shape != (len(y),) or not np.array_equal(post,np.r_[np.zeros(len(y)//2),np.ones(len(y)//2)]):
        raise FitFailure("non-comparable chronological period design")
    if pi.shape != y.shape or not np.all(np.isfinite(pi)) or np.any(pi<=0) or np.any(pi>1):
        raise NotIdentified("unknown or invalid first-stage inclusion probability")
    if q.shape != y.shape or not np.all(np.isfinite(q)) or np.any(q<0) or np.any(q>1):
        raise NotIdentified("unknown randomized verification probability")
    if not obs["audit_independent"]:
        raise NotIdentified("second-phase assignment not independently authenticated")
    if np.any(inc & ~resp & (q<=0)):
        raise NotIdentified("potential MNAR outcomes without randomized nonresponse audits")
    if np.any(audited & (q<=0)):
        raise NotIdentified("false random-audit provenance")
    if np.any(inc & ~resp & ~audited) and not np.any(audited):
        raise NotIdentified("missing transcript outcomes have no audited support")
    return y,frame,inc,resp,audited,meeting,pi,q,post


def _weighted_logit_gamma(y, inc, resp, audited, pi, q, post):
    """Weighted two-phase outcome-dependent response logistic via Newton IRLS."""
    seen = resp | audited
    rows = np.nonzero(seen)
    yy = y[seen]
    if len(yy) < 30 or (resp[seen].sum() < 10) or (audited[seen].sum() < 10):
        raise FitFailure("too few independently audited missing outcomes for response model")
    xs = np.column_stack((np.ones(len(yy)), yy, np.broadcast_to(post[:,None],y.shape)[seen]))
    ww = 1 / pi[seen] / np.where(resp[seen],1, q[seen])
    label = resp[seen].astype(float)
    coef = np.zeros(3)
    ridge = 1e-5
    converged = False
    for _ in range(30):
        zz = np.clip(xs@coef,-25,25)
        p = 1 / (1+np.exp(-zz))
        grad = xs.T@(ww*(label-p)) - ridge*coef
        h = xs.T@((ww*p*(1-p))[:,None]*xs) + ridge*np.eye(3)
        try:
            step = np.linalg.solve(h,grad)
        except np.linalg.LinAlgError as ex:
            raise FitFailure("response logistic ill-conditioned") from ex
        coef = np.clip(coef+step,-30,30)
        if np.max(np.abs(step)) < 1e-7:
            converged=True
            break
    if not converged:
        raise FitFailure("response likelihood did not converge in 30 Newton steps")
    return float(coef[1])


def _stratified_mean(mask, y, inc, resp, audited, pi, q):
    sampling = mask & inc
    w = 1/pi[sampling]
    if len(w)<15:
        raise FitFailure("too few sampled speech units")
    labels = resp[sampling]
    if labels.sum()<5 or (~labels).sum()<3:
        raise FitFailure("insufficient source response strata")
    values = y[sampling]
    audit_mask = audited[sampling] & ~labels
    if audit_mask.sum()<1:
        raise FitFailure("no independently randomized nonresponder support")
    a = float(w[labels].sum())
    b = float(w[~labels].sum())
    pR = a/(a+b)
    meanR = float(np.sum(w[labels]*values[labels])/a)
    audit_weights=w[audit_mask]/q[sampling][audit_mask]
    meanNR=float(np.sum(audit_weights*values[audit_mask])/np.sum(audit_weights))
    used=np.where(labels,w,np.where(audit_mask,w/q[sampling],0))
    effective=float((used.sum()**2)/max(1e-16, np.sum(used**2)))
    return pR*meanR+(1-pR)*meanNR,effective


def fit_annual(obs):
    y,frame,inc,resp,audited,meeting,pi,q,post = _visible_observations(obs)
    gamma = _weighted_logit_gamma(y,inc,resp,audited,pi,q,post)
    means=[]; variance=[]; neff=[]; meetings=[]
    for t in range(len(y)):
        all_rows=frame[t]
        mu,n=_stratified_mean(all_rows,y[t],inc[t],resp[t],audited[t],pi[t],q[t])
        chosen=np.unique(meeting[t][inc[t]])
        if len(chosen)<6:
            raise FitFailure("fewer than six independently selected meetings")
        delete=[]
        for m in chosen:
            try:
                v,_=_stratified_mean(all_rows&(meeting[t]!=m),y[t],inc[t],resp[t],audited[t],pi[t],q[t])
                delete.append(v)
            except FitFailure:
                pass
        if len(delete)<5:
            raise FitFailure("insufficient complete leave-one-meeting sensitivity")
        # Conditional leave-one-original-meeting sensitivity; not a certified design variance.
        j=np.asarray(delete)
        v=float((len(j)-1)/len(j)*np.sum((j-j.mean())**2))
        means.append(mu);variance.append(v);neff.append(n);meetings.append(int(len(chosen)))
    return {"annual_means":np.asarray(means),"annual_meeting_delete_variance":np.asarray(variance),
            "year_effective_n":np.asarray(neff),"selected_meetings_per_year":np.asarray(meetings),
            "gamma":gamma,"years":len(means)}


@lru_cache(maxsize=8)
def _grid_precompute(T):
    x=np.column_stack((np.ones(T),np.r_[np.zeros(T//2),np.ones(T//2)]))
    lag=np.abs(np.subtract.outer(np.arange(T),np.arange(T)))
    combos = [(rho,lam) for rho in RHO_GRID for lam in NUGGET_GRID]
    Bs=[]; Ps=[]; Ss=[]; lds=[]
    for rho,lam in combos:
        C=(1-lam)*rho**lag+lam*np.eye(T)
        vi=np.linalg.inv(C)
        xi=x.T@vi@x
        inv=np.linalg.inv(xi)
        B=inv@x.T@vi
        P=vi-vi@x@inv@x.T@vi
        ld=np.linalg.slogdet(C)[1]+np.linalg.slogdet(xi)[1]
        Bs.append(B[1]);Ps.append(P);Ss.append(inv[1,1]);lds.append(ld)
    return (np.asarray(combos),np.asarray(Bs),np.asarray(Ps),np.asarray(Ss),np.asarray(lds))


def estimate_covariance(annual, method):
    """Finite-year profile-REML candidate: estimates rho, nugget and marginal scale.

    IID, AR1-only, and ridge-regularized AR1+nugget are explicit distinct
    model assumptions. The year-nugget is unidentifiable when lambda=1 and
    therefore lambda is limited to 0.8; profile ambiguity is reported.
    """
    x=np.asarray(annual,dtype=float)
    T=len(x)
    if T not in (8,16,24,32,48,64) or np.any(~np.isfinite(x)) or method not in METHODS:
        raise FitFailure("invalid year observations or covariance family")
    combos,B,P,S,ld = _grid_precompute(T)
    betas=B@x
    sse=np.sum((P@x)*x[None,:],axis=1)
    variance=np.maximum(1e-12,sse/(T-2))
    losses=ld+(T-2)*np.log(variance)
    if method=="iid_year":
        allowed=np.array([r==0 and l==0 for r,l in combos])
    elif method=="ar1_constrained":
        allowed=np.array([l==0 for r,l in combos])
    else:
        allowed=np.ones(len(combos),dtype=bool)
        # Predeclared complexity regularization (equivalent to penalized REML).
        losses=losses+1.0*combos[:,1]**2+0.3*(combos[:,0]/0.92)**2
    if not np.any(allowed):
        raise FitFailure("no valid covariance family")
    losses=np.where(allowed,losses,np.inf)
    k=int(np.argmin(losses))
    rho,lam=map(float,combos[k])
    se=float(np.sqrt(max(1e-12,variance[k]*S[k])))
    cutoff=float(student_t.ppf(.95,T-3))
    by_rho=[]
    for r in RHO_GRID:
        eligible=(combos[:,0]==r)&allowed
        if eligible.any():by_rho.append((r,float(np.min(losses[eligible]))))
    mind=min(v for _,v in by_rho)
    within=[r for r,v in by_rho if v<=mind+2.71]
    profile_width=float(max(within)-min(within))
    return {"method":method,"beta_hat":float(betas[k]),"se":se,"rho_hat":rho,
            "nugget_fraction_hat":lam,"year_scale_hat":float(variance[k]),
            "rho_boundary":rho in (RHO_GRID[0],RHO_GRID[-1]),
            "nugget_boundary":lam in (NUGGET_GRID[0],NUGGET_GRID[-1]),
            "weakly_identified_rho":profile_width>=0.5,
            "rho_profile_support_width":profile_width,
            "interval_nominal_low":float(betas[k]-cutoff*se),
            "interval_nominal_high":float(betas[k]+cutoff*se),
            "nuisance_estimated_not_oracle":True}


def fit_panel(observed):
    """Never accepts source bytes, missing outcomes, generating rho or truth beta."""
    annual=fit_annual(observed)
    return {"annual":annual,
            "methods":{method:estimate_covariance(annual["annual_means"],method) for method in METHODS}}


def oracle_gls(annual, true_rho, true_sigma2, true_nugget2=0.0):
    """KNOWN-PARAMETER ORACLE, ONLY for independent controlled numerical tests.

    Not called by fit_panel or any development/holdout feasible simulation.
    """
    y=np.asarray(annual,dtype=float)
    T=len(y)
    if T<8 or T%2 or not (-.95<true_rho<.95) or true_sigma2<=0 or true_nugget2<0:
        raise ValueError("invalid known-parameter oracle")
    X=np.column_stack((np.ones(T),np.r_[np.zeros(T//2),np.ones(T//2)]))
    C=true_sigma2*(true_rho**np.abs(np.subtract.outer(np.arange(T),np.arange(T))))+true_nugget2*np.eye(T)
    W=np.linalg.solve(C,X)
    S=np.linalg.inv(X.T@W)
    beta=S@X.T@np.linalg.solve(C,y)
    se=float(np.sqrt(S[1,1]))
    return {"beta_hat":float(beta[1]),"se":se,"interval_low":float(beta[1]-1.6448536269514722*se),
            "interval_high":float(beta[1]+1.6448536269514722*se),"oracle":True}


def real_fit(*_args,**_kwargs):
    raise PermissionError("Real 2008–2023 fitting is prohibited in calibration v2")
