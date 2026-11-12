"""Development-only temporal-identification diagnostics; no v3 holdout or real fit.

Two separately generated synthetic tasks:
* Gamma: conditional audited-response pseudo-score, year-cluster L0 versus
  Bartlett year-score HAC L1/L2. No nominal CI certification at T=16.
* Covariance: demonstrate exact nugget/measurement observational aliasing,
  externally estimated replicate measurement variance, and finite-T rho
  quasi-moment nonidentification. True DGP parameters reach evaluator only.

Neither task imports or modifies v2 code, its results, or source records.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import math
import numpy as np
from scipy.special import expit
from .v3_nuisance import IdentificationFailure, response_gamma

NAMESPACE = "UNGA81-V3-DEPENDENCE-DEV-20261015-NO-HOLDOUT"
SYNTHETIC_ONLY = True


def development_seed(label: str) -> int:
    return int.from_bytes(hashlib.sha256((NAMESPACE + "|" + label).encode()).digest()[:8], "big")


def generate_response_development(*, years: int, rho: float, response_year_sd: float,
                                  q: float, seed: int) -> tuple[dict, dict]:
    """Independent generator, deliberately distinct from v3_prototype.simulate.

    A serial year response shock is an omitted-logit intercept; when nonzero,
    fitted gamma generally targets a pseudo-true value, not structural gamma.
    """
    if years not in (16, 24, 32) or rho not in (0.0, 0.65, 0.85):
        raise ValueError("unsupported synthetic development horizon/dependence")
    if response_year_sd not in (0.0, 0.7) or q not in (0.0, 0.35, 0.015):
        raise ValueError("unsupported development-only response design")
    rng = np.random.default_rng(seed)
    meetings, actors = 9, 12
    shape = (years, meetings, actors)
    outcome = np.full(shape, np.nan)
    included = np.zeros(shape, dtype=bool)
    responded = np.zeros(shape, dtype=bool)
    audited = np.zeros(shape, dtype=bool)
    inclusion_pi = np.full(shape, 2/3, dtype=float)
    audit_pi = np.zeros(shape, dtype=float)
    at_risk = np.ones(shape, dtype=bool)
    actor_effect = rng.normal(0, 0.3, actors)
    previous_outcome = 0.0
    previous_response = 0.0
    for t in range(years):
        previous_outcome = rho*previous_outcome + math.sqrt(1-rho**2)*rng.normal(0,0.28)
        previous_response = rho*previous_response + math.sqrt(1-rho**2)*rng.normal(0,response_year_sd)
        # Three independently selected original-meeting strata, two of three.
        selected = set()
        for group in range(3):
            selected.update(int(k) for k in rng.choice(np.arange(3*group,3*group+3),2,replace=False))
        for m in range(meetings):
            meeting_effect = rng.normal(0, 0.13)
            if m not in selected:
                continue
            for a in range(actors):
                if a == 0 and t < 2:  # a structural preadmission non-opportunity
                    at_risk[t,m,a] = False
                    continue
                included[t,m,a] = True
                y = (0.2*(t>=years//2) + previous_outcome + actor_effect[a] +
                     meeting_effect + rng.normal(0,0.36))
                p = expit(-0.35 - 1.25*y + previous_response)
                if rng.random() < p:
                    responded[t,m,a] = True
                    outcome[t,m,a] = y
                else:
                    audit_pi[t,m,a] = q
                    if rng.random() < q:
                        audited[t,m,a] = True
                        outcome[t,m,a] = y
    # Structural indicator must agree with selected original meetings.
    at_risk[:2, :, 0] = False
    data = {
        "value": outcome, "included": included, "responded": responded,
        "audited": audited, "inclusion_probability": inclusion_pi,
        "independent_audit_probability": audit_pi, "at_risk": at_risk,
        "independent_audit_provenance": q > 0,
        "design_id": "invented_stratified_two_of_three",
    }
    # Generating truth is never part of the observed object or estimator call.
    return data, {"structural_gamma": -1.25,
                  "year_response_intercept_sd": response_year_sd,
                  "year_response_rho": rho}


def gamma_year_score_sandwich(observed: dict, *, lag: int = 0, min_years: int = 16) -> dict:
    """Bartlett year-score HAC (L>0), L=0 independent-year cluster diagnostic.

    A year-score HAC is an asymptotic pseudo-parameter variance diagnostic, NOT
    a valid T=16 confidence interval, independent audit design variance, or
    causal/structural gamma uncertainty under omitted year response shocks.
    """
    if type(lag) is not int or lag not in (0, 1, 2):
        raise IdentificationFailure("unapproved year-score lag bandwidth")
    fitted = response_gamma(observed)
    y = np.asarray(observed["value"], float)
    r = np.asarray(observed["responded"],bool)
    a = np.asarray(observed["audited"],bool)
    pi = np.asarray(observed["inclusion_probability"],float)
    q = np.asarray(observed["independent_audit_probability"],float)
    T = y.shape[0]
    if T < min_years or T < 4*(lag+1):
        raise IdentificationFailure("insufficient year blocks for HAC bandwidth")
    observed_mask = r | a
    vals = y[observed_mask]
    X = np.stack((np.ones(len(vals)), vals),axis=1)
    w = 1/pi[observed_mask]
    a_rows = a[observed_mask]
    w[a_rows] /= q[observed_mask][a_rows]
    yy = r[observed_mask].astype(float)
    p = expit(fitted["intercept"]+fitted["gamma"]*vals)
    Hessian = (X.T*(w*p*(1-p)))@X
    if np.linalg.eigvalsh(Hessian)[0]<=1e-10 or np.linalg.cond(Hessian)>1e10:
        raise IdentificationFailure("unstable gamma bread information")
    raw_scores = X*(w*(yy-p))[:,None]
    yr_ids = np.broadcast_to(np.arange(T)[:,None,None],y.shape)[observed_mask]
    annual = np.zeros((T,2),float)
    np.add.at(annual,yr_ids,raw_scores)
    if (np.linalg.norm(annual,axis=1)>0).sum()<T:
        raise IdentificationFailure("missing annual gamma score support")
    s = annual - annual.mean(axis=0)
    meat = s.T@s
    for k in range(1,lag+1):
        G = s[k:].T@s[:-k]
        meat += (1-k/(lag+1))*(G+G.T)
    meat *= T/(T-1)
    bread_inv = np.linalg.inv(Hessian)
    covariance = bread_inv@meat@bread_inv
    covariance = (covariance+covariance.T)/2
    eig = np.linalg.eigvalsh(covariance)
    if not np.all(np.isfinite(eig)) or eig[0]<-1e-9 or covariance[1,1]<=0:
        raise IdentificationFailure("nonpositive year-score HAC covariance")
    gamma_se = float(np.sqrt(covariance[1,1]))
    gamma_annual_lag1 = float(np.corrcoef(s[1:,1],s[:-1,1])[0,1])
    if not np.isfinite(gamma_annual_lag1):
        raise IdentificationFailure("degenerate annual gamma score dependence")
    return {"gamma":fitted["gamma"], "gamma_se_diagnostic":gamma_se,
            "method":"independent_year_cluster" if lag==0 else f"bartlett_hac_lag{lag}",
            "bandwidth_years":lag,"lag1_annual_gamma_score_correlation":gamma_annual_lag1,
            "years":int(T),"respondents":fitted["observed_respondents"],
            "audited":fitted["independently_recovered"],
            "interval_calibrated":False,"structural_gamma_identified_under_omitted_year_effect":False,
            "t16_inference_approved":False,"real_data_fit_authorized":False}


def gamma_circular_block_score_bootstrap(observed: dict, *, seed: int,
                                         block_years: int = 4,
                                         bootstrap_reps: int = 160) -> dict:
    """Linearized circular moving-year-block score bootstrap (diagnostic only).

    Resamples consecutive *whole annual score groups*, never actors/speeches as
    independent temporal observations. Does NOT re-estimate source/audit weights
    or response selection in each draw; finite T and bias remain unresolved.
    """
    if type(seed) is not int or block_years != 4 or not 80<=bootstrap_reps<=400:
        raise IdentificationFailure("unapproved block-bootstrap development specification")
    fitted = response_gamma(observed)
    y = np.asarray(observed["value"],float)
    r = np.asarray(observed["responded"],bool)
    a = np.asarray(observed["audited"],bool)
    pi = np.asarray(observed["inclusion_probability"],float)
    q = np.asarray(observed["independent_audit_probability"],float)
    T=y.shape[0]
    if T<16 or T < 4*block_years:
        raise IdentificationFailure("too few calendar years for circular block bootstrap")
    visible=r|a
    vals=y[visible]
    X=np.stack((np.ones(len(vals)),vals),axis=1)
    w=1/pi[visible]
    w[a[visible]]/=q[visible][a[visible]]
    labels=r[visible].astype(float)
    p=expit(fitted["intercept"]+fitted["gamma"]*vals)
    bread=(X.T*(w*p*(1-p)))@X
    if np.linalg.eigvalsh(bread)[0]<=1e-10 or np.linalg.cond(bread)>1e10:
        raise IdentificationFailure("block-bootstrap gamma information singular")
    raw=X*(w*(labels-p))[:,None]
    ids=np.broadcast_to(np.arange(T)[:,None,None],y.shape)[visible]
    score=np.zeros((T,2))
    np.add.at(score,ids,raw)
    score-=score.mean(axis=0)
    rng=np.random.default_rng(seed)
    changes=[]
    influence=np.linalg.inv(bread)[1]
    for _ in range(bootstrap_reps):
        starts=rng.integers(0,T,size=math.ceil(T/block_years))
        indices=np.concatenate([(s+np.arange(block_years))%T for s in starts])[:T]
        changes.append(float(influence@score[indices].sum(axis=0)))
    se=float(np.std(changes,ddof=1))
    if not np.isfinite(se) or se<=1e-10:
        raise IdentificationFailure("degenerate moving-year-block score bootstrap")
    return {"gamma":fitted["gamma"],"gamma_se_diagnostic":se,
            "method":"circular_year_block4","block_years":block_years,
            "bootstrap_reps":bootstrap_reps,"years":T,
            "interval_calibrated":False,"response_selection_refitted":False,
            "structural_gamma_identified_under_omitted_year_effect":False,
            "t16_inference_approved":False,"real_data_fit_authorized":False}


def covariance_fisher_information(*, years: int, rho: float,
                                  process_variance: float=0.04,
                                  year_nugget_variance: float=0.025,
                                  measurement_noise_variance: float=0.0144) -> dict:
    """Expected Gaussian covariance curvature, not an empirical estimator.

    Unconstrained observation-only year-nugget/measurement effects enter as
    exactly the same I(T): their score derivatives coincide and are not jointly
    identifiable for ANY T. The 3-parameter Fisher spectrum assumes genuinely
    external measurement noise is fixed, and does not prove reliable recovery.
    """
    if years not in (16,24,32,48) or not (0<=rho<.95) or min(
        process_variance,year_nugget_variance,measurement_noise_variance)<0 or process_variance==0:
        raise ValueError("invalid covariance information design")
    d = np.abs(np.subtract.outer(np.arange(years),np.arange(years)))
    R = rho**d
    dR = np.zeros_like(R)
    if rho>0:
        dR[d>0] = d[d>0] * rho**(d[d>0]-1)
    else:
        dR[d==1]=1.0
    I = np.eye(years)
    cov = process_variance*R+(year_nugget_variance+measurement_noise_variance)*I
    # Dimensionless coordinates: process amplitude, rho, year nugget, measurement noise.
    # Nugget and measurement have identical covariance derivatives identically.
    deriv = [process_variance*R, process_variance*dR, process_variance*I,
             process_variance*I]
    inv_d = [np.linalg.solve(cov,dC) for dC in deriv]
    fisher = np.array([[0.5*np.trace(A@B) for B in inv_d] for A in inv_d])
    ev_unfixed = np.linalg.eigvalsh(fisher)
    ev_fixed = np.linalg.eigvalsh(fisher[:3,:3])
    if ev_fixed[-1]<=0:
        raise ValueError("degenerate expected covariance information")
    return {"years":years,"rho":rho,
            "unrestricted_rank":int(np.linalg.matrix_rank(fisher,tol=1e-10)),
            "unrestricted_parameter_count":4,
            "unrestricted_min_eigenvalue":float(ev_unfixed[0]),
            "measurement_nugget_derivatives_identical":bool(np.array_equal(deriv[2],deriv[3])),
            "fixed_external_noise_min_information":float(ev_fixed[0]),
            "fixed_external_noise_condition":float(ev_fixed[-1]/ev_fixed[0]) if ev_fixed[0]>1e-12 else None,
            "fixed_external_noise_identification_only_local":True,
            "finite_year_parameter_recovery_established":False,
            "real_data_fit_authorized":False}


def generate_covariance_development(*, years: int, rho:float,
                                    nugget_variance:float,seed:int) -> tuple[dict,dict]:
    if years not in (16,32) or rho not in (0.05,0.65) or nugget_variance not in (0.0,0.025):
        raise ValueError("unsupported covariance development cell")
    rng = np.random.default_rng(seed)
    process = np.empty(years)
    previous=0.0
    for t in range(years):
        previous = rho*previous + math.sqrt(1-rho*rho)*rng.normal(0,0.2)
        process[t] = previous
    process += rng.normal(0,math.sqrt(nugget_variance),size=years)
    measurement_sd=0.12
    annual=process+rng.normal(0,measurement_sd,size=years)
    annual[years//2:] +=0.2
    # External 24-pair replicate sample is from DIFFERENT invented years.
    independent_reference=rng.normal(size=24)
    rep1=independent_reference+rng.normal(0,measurement_sd,size=24)
    rep2=independent_reference+rng.normal(0,measurement_sd,size=24)
    data={"annual":annual,"replicate_first":rep1,"replicate_second":rep2}
    evaluator={"true_rho":rho,"true_year_nugget_variance":nugget_variance,
               "true_measurement_noise_variance":measurement_sd**2}
    return data,evaluator


def recovery_quasi_moments(observed:dict)->dict:
    """Failure-accounted exploratory lag-moment diagnostic, NEVER an accepted fit.

    Demeans each era from observed outcomes, not from generating truth. Lag 1/2
    moments are computed WITHIN eras only; 16 years offer few usable pairs.
    """
    annual=np.asarray(observed["annual"],float)
    first=np.asarray(observed["replicate_first"],float)
    second=np.asarray(observed["replicate_second"],float)
    T=len(annual)
    if T not in (16,32) or first.shape != (24,) or second.shape!=(24,) or not np.all(
        np.isfinite(np.r_[annual,first,second])):
        raise IdentificationFailure("invalid exploratory covariance observation")
    d=first-second
    noise_est=float(np.var(d,ddof=1)/2)
    if not (0<=noise_est<.20):
        raise IdentificationFailure("external replicate variance unsupported")
    middle=T//2
    a=annual[:middle]-annual[:middle].mean()
    b=annual[middle:]-annual[middle:].mean()
    c0=float(np.mean(np.r_[a*a,b*b]))
    c1=float((np.sum(a[1:]*a[:-1])+np.sum(b[1:]*b[:-1]))/(T-2))
    c2=float((np.sum(a[2:]*a[:-2])+np.sum(b[2:]*b[:-2]))/(T-4))
    if c1<=1e-6 or c2<=1e-6:
        raise IdentificationFailure("nonpositive lag moments; AR1/nugget not identified")
    rho_hat=c2/c1
    if not (0.02<rho_hat<0.95):
        raise IdentificationFailure("rho moment ratio outside allowable support")
    proc_hat=c1/rho_hat
    nugget_hat=c0-noise_est-proc_hat
    if proc_hat<=0 or nugget_hat <0:
        raise IdentificationFailure("negative implied variance component")
    return {"rho_hat":float(rho_hat),"year_nugget_variance_hat":float(nugget_hat),
            "replicate_measurement_noise_hat":noise_est,
            "known_true_parameters_used_by_estimator":False,
            "fit_family":"exploratory_within_era_quasi_moment",
            "inferential_eligibility":False}
