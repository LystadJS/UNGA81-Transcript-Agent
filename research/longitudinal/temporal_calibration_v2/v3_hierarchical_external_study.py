"""Fresh, source-free, *development-only* hierarchical response/external-scale study.

No previous v2/v3 holdout or source files opened. Synthetic generating truth
returns only to evaluator, not estimation. Every failed method attempt is
reported by exact scenario/method/replicate/reason. Never authorizes real fit.
"""
from __future__ import annotations
import argparse
from collections import defaultdict,Counter
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.special import expit
from .v3_nuisance import IdentificationFailure
from .v3_serial_partial import estimate_serial_response
from .v3_hierarchical_external import (
    SOURCE_SCHEMA, ALPHA_TOTAL, hierarchical_conditional_gamma,
    bonferroni_continuous_covariance,external_scale_upper)
from .v3_finite_year_continuous import verify_continuous_bound

NAMESPACE="UNGA81-V3-HIERARCHICAL-EXTERNAL-NEW-DEV-20261015"
GAMMA_WORLDS=(
    ("iid_T16",16,0.0,0.0,0.0,.4,False),
    ("correlated_years_T16",16,.65,.75,.60,.4,False),
    ("correlated_years_T32",32,.65,.75,.60,.4,False),
    ("weak_audit_T16",16,.65,.75,.60,.02,False),
    ("missing_outcome_audit_T16",16,.65,.75,.60,0.0,False),
    ("changing_gamma_T16",16,.65,.75,.60,.4,True))
COV_WORLDS=(
    ("matched_external_T16",16,.65,.35,.075,False,False,False,False),
    ("strong_year_rho_T16",16,.85,.70,.11,False,False,False,False),
    ("outside_rho_T16",16,.92,.35,.075,False,False,False,False),
    ("shifted_external_population_T16",16,.65,.35,.075,True,False,False,False),
    ("dependent_external_worlds_T16",16,.65,.35,.075,False,True,False,False),
    ("biased_annual_T16",16,.65,.35,.075,False,False,True,False),
    ("nongaussian_T16",16,.65,.35,.075,False,False,False,True))
GAMMA_METHODS=("pooled","conditional_year_FE","hierarchical_AR1_EB")
COV_METHODS=("continuous_wide","continuous_narrow")
TRUE_GAMMA=-1.25
TRUE_BETA=.20
Z90=1.6448536269514722


def seed(label):
    return int.from_bytes(hashlib.sha256((NAMESPACE+"|"+label).encode()).digest()[:8],"big")


def generate_response(case,rep):
    name,T,rho,propensity_sd,correlation,q,slope_shift=case
    rng=np.random.default_rng(seed(f"response|{name}|{rep}"))
    meetings,actors=9,16
    shape=(T,meetings,actors)
    data={
        "value":np.full(shape,np.nan),"included":np.zeros(shape,bool),
        "responded":np.zeros(shape,bool),"audited":np.zeros(shape,bool),
        "at_risk":np.ones(shape,bool),
        "inclusion_probability":np.full(shape,2/3),
        "independent_audit_probability":np.zeros(shape)
    }
    data["at_risk"][:2,:,0]=False
    actor=rng.normal(0,.30,actors)
    year_out=year_resp=0.0
    for t in range(T):
        eps1,eps2=rng.normal(size=2)
        year_out=rho*year_out+math.sqrt(1-rho**2)*.25*eps1
        year_resp=rho*year_resp+math.sqrt(1-rho**2)*propensity_sd*(
            correlation*eps1+math.sqrt(1-correlation**2)*eps2)
        meetings_selected=np.zeros(meetings,bool)
        for group in range(3):
            meetings_selected[rng.choice(np.arange(3*group,3*group+3),2,replace=False)]=True
        true_y=(.2*(t>=T//2)+year_out+rng.normal(0,.12,meetings)[:,None]+
                actor[None,:]+rng.normal(0,.34,(meetings,actors)))
        eligible=meetings_selected[:,None]&data["at_risk"][t]
        data["included"][t]=eligible
        gamma= (-.40 if slope_shift and t>=T//2 else TRUE_GAMMA)
        prob=expit(-.35+gamma*true_y+year_resp)
        responded=(rng.random((meetings,actors))<prob)&eligible
        audited=(rng.random((meetings,actors))<q)&eligible&~responded
        data["responded"][t]=responded
        data["audited"][t]=audited
        data["independent_audit_probability"][t][eligible&~responded]=q
        data["value"][t][responded|audited]=true_y[responded|audited]
    data.update(independent_audit_provenance=q>0,
                design_id="synthetic_hierarchical_meeting_strata_2_of_3")
    evaluator={"conditional_gamma":None if slope_shift else TRUE_GAMMA,
               "true_year_rho":rho,"true_year_propensity_sd":propensity_sd,
               "gamma_changed":bool(slope_shift)}
    return data,evaluator


def generate_external_covariance(case,rep):
    name,T,rho,lam,scale,wrong_population,dependent_external,bias,non_gaussian=case
    rng=np.random.default_rng(seed(f"covariance|{name}|{rep}"))
    lag=np.abs(np.subtract.outer(np.arange(T),np.arange(T)))
    C=scale*((1-lam)*rho**lag+lam*np.eye(T))
    if non_gaussian:
        # Same covariance scale, but non-Gaussian heavy-tailed year observations.
        standardized=rng.multivariate_normal(np.zeros(T),C)
        multiplier=math.sqrt(3.0)/math.sqrt(float(rng.chisquare(3)))
        y=standardized*multiplier
    else:
        y=rng.multivariate_normal(np.zeros(T),C)
    y[T//2:]+=TRUE_BETA+(.2 if bias else 0)
    independent_worlds=40
    # Each external calibration anchor comes from an independent synthetic
    # world with the SAME marginal annual-year variance (if matched).
    # Historical diplomatic sources have no such demonstrated calibration.
    calibration_scale=scale*(1.8 if wrong_population else 1.0)
    calibration=rng.normal(0,math.sqrt(calibration_scale),independent_worlds)
    if dependent_external:
        calibration[:]=calibration[0]
    receipt={"schema":SOURCE_SCHEMA,
        "synthetic_development_only":True,
        "independent_world_samples":not dependent_external,
        "same_year_quantity":True,"independent_gaussian":True,
        "same_scale_population":not wrong_population,
        "same_representation":True,"same_year_definition":True,
        "design_id":"fictional_calendar_year_scalar_v3",
        "values":calibration.tolist()}
    observation={"annual":y,"external_calibration":receipt}
    evaluator={"beta":TRUE_BETA,"rho":rho,"lambda":lam,"scale":scale,
               "calibration_assumptions_true":not wrong_population and not dependent_external,
               "target_gaussian":not non_gaussian,
               "annual_unbiased":not bias}
    return observation,evaluator


def _estimate_summary(gammas, truth):
    if not gammas or truth is None:
        return {"bias":None,"rmse":None}
    diff=np.asarray(gammas)-truth
    return {"bias":float(diff.mean()),"rmse":float(np.sqrt(np.mean(diff**2)))}


def development_study(repetitions=8):
    if type(repetitions) is not int or not 6<=repetitions<=20:
        raise ValueError("bounded synthetic development repetitions must be 6..20")
    failures=[];gamma_rows=[];cov_rows=[]
    for case in GAMMA_WORLDS:
        name,T,rho,propensity_sd,correlation,q,change=case
        complete=defaultdict(list);refusals={name:Counter() for name in GAMMA_METHODS}
        for rep in range(repetitions):
            obs,truth=generate_response(case,rep)
            for method in GAMMA_METHODS:
                try:
                    if method=="pooled":
                        result=estimate_serial_response(obs,"pooled_logit",lag=2)
                        gamma=result["gamma_hat"];se=None;nuisance=None
                    elif method=="conditional_year_FE":
                        result=estimate_serial_response(obs,"year_fixed_effects",lag=2)
                        gamma=result["gamma_hat"];se=result["se_diagnostic"];nuisance=None
                    else:
                        result=hierarchical_conditional_gamma(obs)
                        gamma=result["gamma_hat"];se=result["gamma_hessian_se_diagnostic"]
                        nuisance=result
                    if not np.isfinite(gamma) or (se is not None and (not np.isfinite(se) or se<=0)):
                        raise IdentificationFailure("nonfinite conditional gamma fit")
                    hit=None if se is None or truth["conditional_gamma"] is None else \
                        bool(abs(gamma-truth["conditional_gamma"])<=Z90*se)
                    complete[method].append({"gamma":float(gamma),"se":se,"hit":hit,
                        "rho":nuisance["year_rho_hat"] if nuisance else None,
                        "weak":nuisance["nuisance_weakly_identified"] if nuisance else None,
                        "boundary":nuisance["nuisance_on_boundary"] if nuisance else None})
                except (IdentificationFailure,ValueError,ArithmeticError,np.linalg.LinAlgError) as exc:
                    reason=type(exc).__name__+":"+str(exc)
                    refusals[method][reason]+=1
                    failures.append({"study":"gamma","scenario":name,"replicate":rep,
                        "method":method,"reason":reason,"expected_nonidentification":q==0})
        for method in GAMMA_METHODS:
            fits=complete[method]
            nfailed=sum(refusals[method].values())
            assert len(fits)+nfailed==repetitions
            m=_estimate_summary([f["gamma"] for f in fits],None if change else TRUE_GAMMA)
            hits=[f["hit"] for f in fits if f["hit"] is not None]
            rho_values=[f["rho"] for f in fits if f["rho"] is not None]
            gamma_rows.append({"scenario":name,"T":T,"method":method,
                "response_q":q,"attempted":repetitions,"completed":len(fits),
                "refused":nfailed,"failure_reasons":dict(sorted(refusals[method].items())),
                "gamma_bias_completed":m["bias"],"gamma_rmse_completed":m["rmse"],
                "uncalibrated_90_shape_hit":float(np.mean(hits)) if hits else None,
                "median_se_diagnostic":float(np.median([f["se"] for f in fits
                                         if f["se"] is not None])) if hits else None,
                "rho_hat_median":float(np.median(rho_values)) if rho_values else None,
                "weak_nuisance_profile_rate":float(np.mean([f["weak"] for f in fits]))
                    if method=="hierarchical_AR1_EB" and fits else None,
                "nuisance_boundary_rate":float(np.mean([f["boundary"] for f in fits]))
                    if method=="hierarchical_AR1_EB" and fits else None,
                "gamma_interval_calibrated":False,"empirical_inference_authorized":False})
    for case in COV_WORLDS:
        name,T,rho,lam,scale,wrong_source,dependent_source,bias,heavy=case
        successes=defaultdict(list);refusals={name:Counter() for name in COV_METHODS}
        for rep in range(repetitions):
            obs,truth=generate_external_covariance(case,rep)
            for method in COV_METHODS:
                try:
                    rhorange=(0,.85) if method=="continuous_wide" else (0,.65)
                    nugrange=(0,.70) if method=="continuous_wide" else (0,.40)
                    outcome=bonferroni_continuous_covariance(
                        obs["annual"],obs["external_calibration"],
                        rho_range=rhorange,nugget_fraction_range=nugrange,
                        target_design_id="fictional_calendar_year_scalar_v3")
                    assumptions=bool(truth["calibration_assumptions_true"] and
                        truth["target_gaussian"] and truth["annual_unbiased"] and
                        rhorange[0]<=truth["rho"]<=rhorange[1] and
                        nugrange[0]<=truth["lambda"]<=nugrange[1] and
                        truth["scale"]<=outcome["scale_upper"])
                    successes[method].append({"hit":outcome["lower"]<=truth["beta"]<=outcome["upper"],
                        "width":outcome["width"],"scale_upper":outcome["scale_upper"],
                        "all_conditions_hold":assumptions,
                        "scale_upper_covered_truth":truth["scale"]<=outcome["scale_upper"]})
                except (IdentificationFailure,ValueError,ArithmeticError,np.linalg.LinAlgError) as exc:
                    reason=type(exc).__name__+":"+str(exc)
                    refusals[method][reason]+=1
                    failures.append({"study":"covariance","scenario":name,
                        "replicate":rep,"method":method,"reason":reason,
                        "expected_nonidentification":wrong_source or dependent_source})
        for method in COV_METHODS:
            values=successes[method];nfailed=sum(refusals[method].values())
            assert len(values)+nfailed==repetitions
            cov_rows.append({"scenario":name,"T":T,"method":method,
                "attempted":repetitions,"completed":len(values),"refused":nfailed,
                "failure_reasons":dict(sorted(refusals[method].items())),
                "diagnostic_beta_hit_rate":float(np.mean([v["hit"] for v in values])) if values else None,
                "median_interval_width":float(np.median([v["width"] for v in values])) if values else None,
                "evaluator_all_assumptions_hold_fraction":float(np.mean([v["all_conditions_hold"] for v in values])) if values else None,
                "external_upper_covers_true_scale_rate":float(np.mean([v["scale_upper_covered_truth"] for v in values])) if values else None,
                "empirical_scale_source_authenticated":False,
                "unconditional_coverage_approved":False})
    gamma_attempted=len(GAMMA_WORLDS)*len(GAMMA_METHODS)*repetitions
    covariance_attempted=len(COV_WORLDS)*len(COV_METHODS)*repetitions
    gamma_failed=sum(r["refused"] for r in gamma_rows)
    covariance_failed=sum(r["refused"] for r in cov_rows)
    assert len(failures)==gamma_failed+covariance_failed
    return {"schema":"un.w4.v3.hierarchical-external-development.v1",
        "stage":"NEW_SYNTHETIC_DEVELOPMENT_ONLY_UNAPPROVED",
        "namespace":NAMESPACE,"repetitions_per_scenario":repetitions,
        "gamma_method_attempted":gamma_attempted,
        "gamma_method_completed":gamma_attempted-gamma_failed,
        "gamma_method_refused":gamma_failed,
        "covariance_method_attempted":covariance_attempted,
        "covariance_method_completed":covariance_attempted-covariance_failed,
        "covariance_method_refused":covariance_failed,
        "failure_ledger_entries":len(failures),
        "gamma_scenarios":gamma_rows,"covariance_scenarios":cov_rows,
        "v3_holdout_attempted":0,"real_original_source_files_read":0,
        "v2_frozen_gates_modified":False,
        "statistical_freeze_accepted":False,
        "real_fit_authorized":False},failures


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase",required=True,choices=("development","holdout","real"))
    ap.add_argument("--repetitions",type=int,default=8)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    if args.phase!="development":
        ap.error("no v3 holdout or real-data entry point")
    if args.out.exists():
        ap.error("refusing overwrite of completed development evidence")
    result,ledger=development_study(args.repetitions)
    args.out.mkdir(parents=True,exist_ok=False)
    (args.out/"aggregate.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    (args.out/"failed_fits.json").write_text(json.dumps(ledger,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"gamma_attempts":result["gamma_method_attempted"],
          "gamma_refused":result["gamma_method_refused"],
          "covariance_attempts":result["covariance_method_attempted"],
          "covariance_refused":result["covariance_method_refused"],
          "failure_ledger":len(ledger),"holdout_attempted":0},sort_keys=True))


if __name__=="__main__":
    main()
