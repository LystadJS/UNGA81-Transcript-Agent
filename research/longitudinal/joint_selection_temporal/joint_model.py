"""Joint two-phase transcript-selection and serial-year covariance research model.

Identifies response-on-unobserved-outcome ONLY with known-probability, independent
random audits of initially missing speech outcomes. No audit => explicit refusal.
Year-effect AR1, nugget and scale are estimated by profile REML, never oracle.
No original UN documents or political positions are loaded by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.special import expit
from scipy.stats import t

RHO_GRID=(-.20,-.10,0.,.10,.20,.35,.50,.60,.65,.75,.85,.92)
NUGGET_GRID=(0.,.20,.40,.60,.80,1.)
AUDIT_PROBABILITY=.40
RIDGE=1e-5
LOGIT_MAX_ITER=30
LOGIT_TOL=1e-7

class NotIdentified(ValueError): pass
class FitFailure(ValueError): pass

@dataclass(frozen=True)
class Interval:
    lower: float
    upper: float
    beta: float
    se: float
    width: float
    multiplier: float


def _design_joint(frame):
    """Use stage-one meeting weights plus independently audited nonresponse."""
    yy=np.asarray(frame["y"],float)
    T=yy.shape[1]
    selected=np.asarray(frame["selected"],bool)
    meeting_pi=np.asarray(frame["meeting_pi"],float)
    response=np.asarray(frame["response"],bool)
    audited=np.asarray(frame["audited"],bool)
    q=float(frame["audit_probability"])
    if yy.shape!=(99,T) or T not in (16,24,32):
        raise FitFailure("Unapproved affiliation/year population")
    if any(z.shape!=yy.shape for z in (selected,meeting_pi,response,audited)):
        raise FitFailure("Different source-frame or selection dimensions")
    if not np.all(np.isfinite(yy)) or np.any(meeting_pi<=0) or np.any(meeting_pi>1):
        raise FitFailure("Invalid source probability or nonfinite hidden outcome")
    if np.any(response&~selected) or np.any(audited&(~selected|response)):
        raise FitFailure("Invalid transcript/audit nesting")
    if q==0:
        raise NotIdentified("Selection on unobserved transcript text not identified without independent randomized nonresponse audit")
    if not (abs(q-AUDIT_PROBABILITY)<1e-12 and
            frame.get("audit_randomized_independently_before_outcome_release",False)):
        raise NotIdentified("No identified phase-II random audit with recorded probability")
    if frame.get("mode")=="real" and not frame.get("random_audit_provenance_verified",False):
        raise NotIdentified("Real historical source text does not have an authenticated random nonresponse audit")
    if not frame.get("first_stage_probability_known",False):
        raise NotIdentified("Source-meeting inclusion probabilities not verified")
    zyear=[];neff=[];valid=[];weighted_y=[];weighted_r=[];weighted_post=[]
    for year in range(T):
        s=selected[:,year];r=s&response[:,year];miss=s&~response[:,year];a=miss&audited[:,year]
        if not np.any(s) or not np.any(r):
            raise FitFailure("Empty first-stage or responding source-year")
        wm=1/meeting_pi[s,year]
        wr=1/meeting_pi[r,year]
        source_response=float(wr.sum()/wm.sum())
        mean_r=float(np.dot(wr,yy[r,year])/wr.sum())
        if np.any(miss):
            if not np.any(a):raise FitFailure("Nonresponding source-year has no independent audited texts")
            wa=1/(meeting_pi[a,year]*q)
            mean_m=float(np.dot(wa,yy[a,year])/wa.sum())
        else:
            mean_m=0.
            wa=np.array([],dtype=float)
        zyear.append(source_response*mean_r+(1-source_response)*mean_m)
        effweights=np.r_[wr,wa]
        neff.append(float(effweights.sum()**2/np.dot(effweights,effweights)))
        # Weighted logistic response model observes all responders and a known
        # probability sample of nonresponders. No unobserved Y is used.
        weighted_y.extend(yy[r,year].tolist())
        weighted_r.extend([1]*int(np.sum(r)))
        weighted_post.extend([year>=T//2]*int(np.sum(r)))
        weighted_y.extend(yy[a,year].tolist())
        weighted_r.extend([0]*int(np.sum(a)))
        weighted_post.extend([year>=T//2]*int(np.sum(a)))
        valid.append((wr,wa,year,np.asarray(r),np.asarray(a)))
    # Build the original person/year weights in a separate pass to prevent
    # any mismatch between outcome rows and response weights.
    logistic_weights=[]
    for wr,wa,year,r,a in valid:
        logistic_weights.extend(wr.tolist())
        logistic_weights.extend(wa.tolist())
    return {"years":np.asarray(zyear),"neff":np.asarray(neff),
            "logit_y":np.asarray(weighted_y),
            "logit_r":np.asarray(weighted_r,float),
            "logit_post":np.asarray(weighted_post,float),
            "logit_weights":np.asarray(logistic_weights)}


def _selection_logit(data):
    """Weighted audited two-phase response likelihood; beta and gamma unknown."""
    X=np.column_stack([np.ones(len(data["logit_y"])),data["logit_y"],data["logit_post"]])
    r=data["logit_r"];w=data["logit_weights"]
    if len(r)<300 or np.sum(r==0)<25 or np.sum(r==1)<100:
        raise FitFailure("Insufficient independently audited response support")
    if not (np.all(w>0) and np.all(np.isfinite(w))):
        raise FitFailure("Invalid phase-II inverse audit probability")
    theta=np.zeros(3)
    h=np.eye(3)
    converged=False
    for iteration in range(LOGIT_MAX_ITER):
        score=X@theta
        p=expit(np.clip(score,-35,35))
        grad=X.T@(w*(r-p))-RIDGE*theta
        v=w*p*(1-p)
        h=X.T@(v[:,None]*X)+RIDGE*np.eye(3)
        try:step=np.linalg.solve(h,grad)
        except np.linalg.LinAlgError as exc:raise FitFailure("Selection information singular") from exc
        # Newton step limiting is locked; not adaptive scenario tuning.
        magnitude=float(np.max(np.abs(step)))
        if magnitude>2:step*=2/magnitude
        theta+=step
        if magnitude<LOGIT_TOL:
            converged=True;break
    if not converged:
        # Gradient-score convergence protects against a spurious last Newton
        # step without silently calling failed fits successful.
        p=expit(np.clip(X@theta,-35,35))
        grad=X.T@(w*(r-p))-RIDGE*theta
        converged=bool(np.linalg.norm(grad,ord=np.inf)<.0001)
    if not converged:raise FitFailure("Selection weighted logistic MLE did not converge")
    try:
        cov=np.linalg.inv(h)
    except np.linalg.LinAlgError as exc:raise FitFailure("Selection covariance singular") from exc
    return {"selection_gamma":float(theta[1]),"selection_intercept":float(theta[0]),
            "selection_period":float(theta[2]),"gamma_se_model":float(np.sqrt(cov[1,1])),
            "selection_n":len(r),"audited_missing_n":int(np.sum(r==0)),
            "selection_converged":True}


def _temporal_reml(years,effective):
    y=np.asarray(years,float);n=np.asarray(effective,float);T=len(y)
    if T not in (16,24,32) or n.shape!=(T,) or np.any(n<2) or np.any(n>99):
        raise FitFailure("Invalid year count or source-effective denominator")
    X=np.column_stack([np.ones(T),np.r_[np.zeros(T//2),np.ones(T//2)]])
    lag=np.abs(np.subtract.outer(np.arange(T),np.arange(T)))
    best=None;fits=0
    for rho in RHO_GRID:
      ar=rho**lag
      for nugget in NUGGET_GRID:
        C=(1-nugget)*ar+nugget*np.diag(99/n)
        try:
            chol,lower=cho_factor(C,lower=True,check_finite=False)
            invX=cho_solve((chol,lower),X,check_finite=False)
            information=X.T@invX
            invinfo=np.linalg.inv(information)
            coeff=invinfo@(X.T@cho_solve((chol,lower),y,check_finite=False))
            resid=y-X@coeff
            sse=float(resid@cho_solve((chol,lower),resid,check_finite=False))
            sig2=max(1e-12,sse/(T-2))
            diag=np.diag(chol)
            logdet=2*np.log(diag).sum()
            sign,ldinfo=np.linalg.slogdet(information)
            if sign<=0 or not np.isfinite(sig2):continue
            loss=float(logdet+ldinfo+(T-2)*np.log(sig2))
            se=float(np.sqrt(sig2*invinfo[1,1]))
            if not np.isfinite(loss) or se<=0:continue
            fits+=1
            if best is None or loss<best["reml_objective"]:
                best={"rho":float(rho),"nugget":float(nugget),"sigma2":float(sig2),
                      "reml_objective":loss,"beta":float(coeff[1]),"se":se}
        except (np.linalg.LinAlgError,ValueError,FloatingPointError):
            continue
    if not best:raise FitFailure("All temporal covariance candidates failed")
    best["rho_at_grid_end"]=best["rho"] in (RHO_GRID[0],RHO_GRID[-1])
    best["nugget_at_grid_end"]=best["nugget"] in (NUGGET_GRID[0],NUGGET_GRID[-1])
    best["covariance_candidates_fitted"]=fits
    best["year_neff_min"]=float(n.min())
    best["year_neff_median"]=float(np.median(n))
    return best


def estimate_joint(frame):
    """Returns selection-and-time covariance fit only with randomized missing-text audits."""
    dat=_design_joint(frame)
    selection=_selection_logit(dat)
    temporal=_temporal_reml(dat["years"],dat["neff"])
    temporal.update(selection)
    temporal["true_rho_not_provided"]=True
    temporal["true_selection_gamma_not_provided"]=True
    temporal["selection_audit_required"]=True
    return temporal


def interval(fit,multiplier=None):
    T=int(fit["year_neff_count"]) if "year_neff_count" in fit else None
    if T is None:
        # fit reports T in the caller's scenario record, never from a true DGP
        raise FitFailure("Observed year count required to determine interval cutoff")
    if T not in (16,24,32):raise FitFailure("Invalid annual horizon")
    base=float(t.ppf(.95,T-3))
    cutoff=max(base,float(multiplier)) if multiplier is not None else base
    half=cutoff*fit["se"]
    return Interval(fit["beta"]-half,fit["beta"]+half,fit["beta"],fit["se"],2*half,cutoff)


def fit_observed(frame):
    fit=estimate_joint(frame)
    fit["year_neff_count"]=len(frame["y"][0])
    return fit
