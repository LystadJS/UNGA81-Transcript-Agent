"""Separate, newly seeded v3 finite-year DEVELOPMENT simulations only.

Generator and evaluator are distinct; no v2 simulation or holdout code imported.
All failed estimator / bootstrap attempts are retained in the result ledger.
The CLI refuses future holdout and real-data modes.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from scipy.special import expit

from .v3_nuisance import IdentificationFailure
from .v3_serial_partial import estimate_serial_response
from .v3_finite_year_continuous import (
    finite_year_block_refit, continuous_contrast_sensitivity,
    verify_continuous_bound, Z90)

NAMESPACE="UNGA81-V3-FINITEYEAR-CONTINUOUS-NEW-DEV-20261015"
GAMMA_WORLDS=(
    ("iid_year_T16",16,0.0,0.0,0.0,.40,False),
    ("serial_response_T16",16,.65,.75,.55,.40,False),
    ("serial_response_T32",32,.65,.75,.55,.40,False),
    ("changing_gamma_T16",16,.65,.75,.55,.40,True),
    ("weak_outcome_audit_T16",16,.65,.75,.55,.025,False),
    ("no_outcome_audit_T16",16,.65,.75,.55,0.0,False))
COV_WORLDS=(
    ("inside_rho065_T16",16,.65,.35,.075,0.0,False),
    ("inside_boundary_T16",16,.85,.70,.115,0.0,False),
    ("outside_rho_T16",16,.92,.35,.075,0.0,False),
    ("outside_scale_T16",16,.65,.35,.30,0.0,False),
    ("year_nonstationary_T16",16,.65,.35,.075,0.0,True),
    ("biased_annual_mean_T16",16,.65,.35,.075,.20,False),
    ("inside_rho065_T32",32,.65,.35,.075,0.0,False))
GAMMA_METHODS=("hac_lag2","year_block4","year_block8")
COV_METHODS=("declared_continuous_wide","declared_continuous_narrow")
GAMMA_TRUTH=-1.25

def seed(label):
    return int.from_bytes(hashlib.sha256((NAMESPACE+"|"+label).encode()).digest()[:8],"big")

def generate_response(case,rep):
    name,T,rho,year_sd,correlation,q,heterogeneous=case
    rng=np.random.default_rng(seed(f"response|{name}|{rep}"))
    meetings,actors=9,14
    shape=(T,meetings,actors)
    data={k:np.zeros(shape,dtype=bool) for k in ("included","responded","audited","at_risk")}
    data["value"]=np.full(shape,np.nan)
    data["inclusion_probability"]=np.full(shape,2/3)
    data["independent_audit_probability"]=np.zeros(shape)
    data["at_risk"][:]=True
    data["at_risk"][:2,:,0]=False
    actor=rng.normal(0,.25,actors)
    previous_response=previous_outcome=0.
    for t in range(T):
        z1,z2=rng.normal(size=2)
        previous_outcome=rho*previous_outcome+math.sqrt(1-rho*rho)*.23*z1
        previous_response=rho*previous_response+math.sqrt(1-rho*rho)*year_sd*(
            correlation*z1+math.sqrt(1-correlation*correlation)*z2)
        chosen=np.zeros(meetings,bool)
        for group in range(3):
            chosen[rng.choice(np.arange(3*group,3*group+3),2,replace=False)]=True
        y=(.2*(t>=T//2)+previous_outcome+
           rng.normal(0,.12,meetings)[:,None]+actor[None,:]+
           rng.normal(0,.33,(meetings,actors)))
        available=chosen[:,None]&data["at_risk"][t]
        data["included"][t]=available
        gamma_t=-.35 if heterogeneous and t>=T//2 else GAMMA_TRUTH
        probability=expit(-.30+gamma_t*y+previous_response)
        responded=(rng.random((meetings,actors))<probability)&available
        audited=(rng.random((meetings,actors))<q)&available&~responded
        data["responded"][t]=responded
        data["audited"][t]=audited
        data["independent_audit_probability"][t][available&~responded]=q
        data["value"][t][responded|audited]=y[responded|audited]
    data["independent_audit_provenance"]=q>0
    data["design_id"]="invented_original_meeting_stratified_2_of_3"
    truth={"common_conditional_gamma":None if heterogeneous else GAMMA_TRUTH,
           "year_response_rho":rho,"response_year_sd":year_sd,
           "heterogeneous_gamma":heterogeneous}
    return data,truth


def generate_covariance(case,rep):
    name,T,rho,lam,scale,selection_bias,nonstationary=case
    rng=np.random.default_rng(seed(f"covariance|{name}|{rep}"))
    ar=rho**np.abs(np.subtract.outer(np.arange(T),np.arange(T)))
    if nonstationary:
        # Different year-level diagonal variance after the era boundary
        diag=np.r_[np.ones(T//2),np.full(T-T//2,3.0)]
        C=scale*((1-lam)*ar+lam*np.diag(diag))
    else:
        C=scale*((1-lam)*ar+lam*np.eye(T))
    sample=rng.multivariate_normal(np.zeros(T),C)
    sample[T//2:]+=.20+selection_bias
    return {"annual":sample,"external_upper":.12,
            "independent_scale_provenance":True}, {
                "rho":rho,"lam":lam,"scale":scale,"beta":.20,
                "selection_bias":selection_bias,"nonstationary":nonstationary}


def _metric(fits,true):
    if true is None or not fits:
        return dict(bias=None,rmse=None,diagnostic_hit_fraction=None)
    gamma=np.asarray([v["gamma"] for v in fits])
    included=[v["hit"] for v in fits if v["hit"] is not None]
    return dict(bias=float(np.mean(gamma-true)),
                rmse=float(np.sqrt(np.mean((gamma-true)**2))),
                diagnostic_hit_fraction=float(np.mean(included)) if included else None)


def run_development(repetitions:int=12,bootstrap_reps:int=20):
    if type(repetitions) is not int or not 6<=repetitions<=24:
        raise ValueError("new development repetitions must be 6..24")
    if type(bootstrap_reps) is not int or not 12<=bootstrap_reps<=40:
        raise ValueError("bounded finite-year bootstrap repetitions must be 12..40")
    results_gamma=[];results_cov=[];failures=[]
    gamma_attempts=gamma_done=gamma_refused=bootstrap_attempts=bootstrap_done=bootstrap_failed=0
    for case in GAMMA_WORLDS:
        name,T,rho,year_sd,corr,q,heterogeneous=case
        fits=defaultdict(list);errors={m:Counter() for m in GAMMA_METHODS}
        for r in range(repetitions):
            observed,truth=generate_response(case,r)
            for method in GAMMA_METHODS:
                gamma_attempts+=1
                try:
                    if method=="hac_lag2":
                        outcome=estimate_serial_response(observed,"year_fixed_effects",lag=2)
                        gamma=float(outcome["gamma_hat"])
                        se=float(outcome["se_diagnostic"])
                        lo,hi=gamma-Z90*se,gamma+Z90*se
                        child_attempts=child_completed=child_failed=0
                    else:
                        block=4 if method=="year_block4" else 8
                        outcome=finite_year_block_refit(
                            observed,seed=seed(f"bootstrap|{name}|{r}|{method}"),
                            repetitions=bootstrap_reps,block_years=block)
                        child_attempts=outcome["attempted"]
                        child_completed=outcome["completed"]
                        child_failed=outcome["failed"]
                        bootstrap_attempts+=child_attempts
                        bootstrap_done+=child_completed
                        bootstrap_failed+=child_failed
                        for x in outcome["failure_ledger"]:
                            failures.append({"study":"response_bootstrap",
                                "scenario":name,"replicate":r,"method":method,
                                "bootstrap_rep":x["attempt"],"reason":x["reason"],
                                "expected_refusal":False})
                        if outcome["status"].startswith("REFUSED"):
                            raise IdentificationFailure(outcome["status"])
                        gamma=outcome["gamma_hat"]
                        lo,hi=outcome["diagnostic_low"],outcome["diagnostic_high"]
                        se=outcome["gamma_se_diagnostic"]
                    if not (np.isfinite(gamma) and np.isfinite(lo) and np.isfinite(hi) and hi>=lo):
                        raise IdentificationFailure("nonfinite finite-year gamma diagnostic")
                    hit=(lo<=truth["common_conditional_gamma"]<=hi) if truth["common_conditional_gamma"] is not None else None
                    fits[method].append({"gamma":gamma,"se":se,"width":hi-lo,"hit":hit})
                    gamma_done+=1
                except (IdentificationFailure,ValueError,ArithmeticError,np.linalg.LinAlgError) as exc:
                    reason=type(exc).__name__+":"+str(exc)
                    errors[method][reason]+=1
                    gamma_refused+=1
                    failures.append({"study":"response_method","scenario":name,
                        "replicate":r,"method":method,"reason":reason,
                        "expected_refusal":q==0 or method=="year_block8" and T==16})
        for method in GAMMA_METHODS:
            f=fits[method]
            assert len(f)+sum(errors[method].values())==repetitions
            m=_metric(f,truth["common_conditional_gamma"])
            results_gamma.append({
                "scenario":name,"years":T,"method":method,"attempted":repetitions,
                "completed":len(f),"failed":sum(errors[method].values()),
                "failure_reasons":dict(sorted(errors[method].items())),
                "gamma_bias_completed":m["bias"],"gamma_rmse_completed":m["rmse"],
                "diagnostic90_hit_fraction_completed":m["diagnostic_hit_fraction"],
                "median_width":float(np.median([v["width"] for v in f])) if f else None,
                "heterogeneous_conditional_gamma":heterogeneous,
                "calibrated_interval":False,"inferential_acceptance":False})
    for case in COV_WORLDS:
        name,T,rho,lam,scale,bias,nonstationary=case
        fit=defaultdict(list);errors={m:Counter() for m in COV_METHODS}
        for r in range(repetitions):
            obs,truth=generate_covariance(case,r)
            for method in COV_METHODS:
                try:
                    args=({"rho_range":(0,.65),"nugget_fraction_range":(0,.4)}
                          if method=="declared_continuous_narrow" else
                          {"rho_range":(0,.85),"nugget_fraction_range":(0,.7)})
                    bound=continuous_contrast_sensitivity(
                        obs["annual"],**args,
                        external_total_scale_upper=obs["external_upper"],
                        external_independent_provenance=obs["independent_scale_provenance"])
                    evaluation=verify_continuous_bound(bound,rho=truth["rho"],
                          lam=truth["lam"],variance_scale=truth["scale"])
                    model_ok=not nonstationary and bias==0
                    inside=evaluation["assumptions_hold"] and model_ok
                    if inside and not evaluation["variance_bounded"]:
                        raise IdentificationFailure("analytical continuous variance bound violated")
                    fit[method].append({"hit":bound["lower"]<=truth["beta"]<=bound["upper"],
                        "width":bound["width"],"assumptions_hold":inside,
                        "variance_bounded":evaluation["variance_bounded"],
                        "conditional_math_bound":bound["termwise_bound_guaranteed_for_all_continuous_rho"]})
                except (IdentificationFailure,ValueError,ArithmeticError,np.linalg.LinAlgError) as exc:
                    reason=type(exc).__name__+":"+str(exc)
                    errors[method][reason]+=1
                    failures.append({"study":"covariance_method","scenario":name,
                        "replicate":r,"method":method,"reason":reason,"expected_refusal":False})
        for method in COV_METHODS:
            vals=fit[method]
            results_cov.append({"scenario":name,"years":T,"method":method,
                "attempted":repetitions,"completed":len(vals),
                "failed":sum(errors[method].values()),
                "failure_reasons":dict(sorted(errors[method].items())),
                "diagnostic90_hit_fraction":float(np.mean([v["hit"] for v in vals])) if vals else None,
                "median_width":float(np.median([v["width"] for v in vals])) if vals else None,
                "assumptions_hold_fraction":float(np.mean([v["assumptions_hold"] for v in vals])) if vals else None,
                "mathematical_variance_bound_verified_given_assumptions":all(
                    v["variance_bounded"] is True for v in vals if v["assumptions_hold"]),
                "empirical_coverage_calibrated":False,"scientific_acceptance":False})
    cov_attempts=len(COV_WORLDS)*len(COV_METHODS)*repetitions
    cov_failed=sum(r["failed"] for r in results_cov)
    assert gamma_attempts==gamma_done+gamma_refused
    assert bootstrap_attempts==bootstrap_done+bootstrap_failed
    assert len(failures)==gamma_refused+bootstrap_failed+cov_failed
    return {"schema":"un.w4.v3.finite-year-continuous.development.v1",
        "stage":"NEW_DEVELOPMENT_ONLY_NO_CONFIRMATORY_HOLDOUT",
        "seed_namespace":NAMESPACE,"repetitions_per_scenario":repetitions,
        "bootstrap_draws_per_method_attempt":bootstrap_reps,
        "gamma_method_attempted":gamma_attempts,"gamma_method_completed":gamma_done,
        "gamma_method_refused":gamma_refused,
        "gamma_bootstrap_attempted":bootstrap_attempts,
        "gamma_bootstrap_completed":bootstrap_done,"gamma_bootstrap_failed":bootstrap_failed,
        "covariance_method_attempted":cov_attempts,
        "covariance_method_completed":cov_attempts-cov_failed,
        "covariance_method_refused":cov_failed,
        "failure_ledger_entries":len(failures),
        "gamma_scenarios":results_gamma,"covariance_scenarios":results_cov,
        "v2_thresholds_modified":False,"v3_holdout_attempted":0,
        "real_original_sources_opened":0,"statistical_acceptance":False,
        "real_fit_authorized":False},failures


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase",choices=("development","holdout","real"),required=True)
    parser.add_argument("--repetitions",type=int,default=12)
    parser.add_argument("--bootstrap",type=int,default=20)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if args.phase!="development":
        parser.error("confirmatory v3 holdout and real data fitting prohibited")
    if args.out.exists():
        parser.error("refusing to overwrite completed synthetic development receipt")
    result,ledger=run_development(args.repetitions,args.bootstrap)
    args.out.mkdir(parents=True,exist_ok=False)
    (args.out/"aggregate.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (args.out/"failures.json").write_text(json.dumps(ledger,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"gamma_attempted":result["gamma_method_attempted"],
        "gamma_completed":result["gamma_method_completed"],
        "gamma_refused":result["gamma_method_refused"],
        "bootstrap_failures":result["gamma_bootstrap_failed"],
        "covariance_attempted":result["covariance_method_attempted"],
        "covariance_refused":result["covariance_method_refused"],
        "failure_ledger_entries":len(ledger),"v3_holdout_attempted":0},sort_keys=True))

if __name__=="__main__":
    main()
