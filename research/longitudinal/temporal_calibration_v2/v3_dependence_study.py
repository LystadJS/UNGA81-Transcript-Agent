"""New development-only benchmark; never opens v2 or prospective v3 holdout.

Run: python -m research.longitudinal.temporal_calibration_v2.v3_dependence_study \
  --phase development --repetitions 60 --out /tmp/unga81-v3-dependence-dev
All scenarios/repetitions are invented, evaluator truth is held outside fitting.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import platform
import numpy as np
from .v3_dependence_benchmark import (
    NAMESPACE, IdentificationFailure, development_seed, generate_response_development,
    gamma_year_score_sandwich, gamma_circular_block_score_bootstrap, covariance_fisher_information,
    generate_covariance_development, recovery_quasi_moments,
)

GAMMA_WORLDS = (
    ("iid_correct_T16",16,0.0,0.0,0.35),
    ("AR1_correct_T16",16,0.65,0.0,0.35),
    ("AR1_omitted_propensity_T16",16,0.65,0.7,0.35),
    ("AR1_omitted_propensity_T32",32,0.65,0.7,0.35),
    ("strong_AR1_omitted_T16",16,0.85,0.7,0.35),
    ("weak_audit_T16",16,0.65,0.7,0.015),
    ("no_audit_T16",16,0.65,0.7,0.0),
)
COV_WORLDS = tuple((f"T{T}_rho{rho}_nugget{nugget}",T,rho,nugget)
                   for T in (16,32) for rho in (0.05,0.65)
                   for nugget in (0.0,0.025))
METHODS=("year_score_lag0","year_score_lag1","year_score_lag2","circular_year_block4")
Z90=1.6448536269514722


def summarize_values(vals, reference, attempts):
    if not vals:
        return {"mean_bias":None,"rmse":None,"median":None,"completed":0}
    a=np.asarray(vals,dtype=float)
    return {"mean_bias":float(np.mean(a-reference)),
            "rmse":float(np.sqrt(np.mean((a-reference)**2))),
            "median":float(np.median(a)),"completed":len(vals)}


def run_development(repetitions:int) -> tuple[dict,list]:
    if type(repetitions) is not int or not 8<=repetitions<=120:
        raise ValueError("bounded development repetitions 8..120 required")
    failures=[]
    gamma=[]
    for name,T,rho,propensity_sd,q in GAMMA_WORLDS:
        successes=defaultdict(list)
        failed={method:Counter() for method in METHODS}
        panels_completed=panels_failed=0
        for rep in range(repetitions):
            obs,evaluator=generate_response_development(
                years=T,rho=rho,response_year_sd=propensity_sd,q=q,
                seed=development_seed(f"gamma|{name}|{rep}"))
            any_succeeded=False
            for method in METHODS:
                try:
                    if method=="circular_year_block4":
                        result=gamma_circular_block_score_bootstrap(
                            obs,seed=development_seed(f"bootstrap|{name}|{rep}"))
                    else:
                        result=gamma_year_score_sandwich(obs,lag=int(method[-1]))
                    se=result["gamma_se_diagnostic"]
                    successes[method].append({"se":se,"gamma":result["gamma"],
                        "hit":abs(result["gamma"]-evaluator["structural_gamma"])<=Z90*se,
                        "false_narrow":abs(result["gamma"]-evaluator["structural_gamma"])>Z90*se and 2*Z90*se<=0.5,
                        "lag1score":result.get("lag1_annual_gamma_score_correlation")})
                    any_succeeded=True
                except (IdentificationFailure,ValueError,ArithmeticError,np.linalg.LinAlgError) as err:
                    reason=f"{type(err).__name__}:{err}"
                    failed[method][reason]+=1
                    failures.append({"type":"gamma_method","scenario":name,"replicate":rep,
                                     "method":method,"reason":reason,
                                     "expected_nonidentification":q==0})
            if any_succeeded:panels_completed+=1
            else:panels_failed+=1
        for method in METHODS:
            rows=successes[method]
            if len(rows)+sum(failed[method].values())!=repetitions:
                raise RuntimeError("gamma method attempt conservation failed")
            g=summarize_values([v["gamma"] for v in rows],-1.25,repetitions)
            lag_values=[v["lag1score"] for v in rows if v["lag1score"] is not None]
            gamma.append({"scenario":name,"T":T,"year_rho":rho,
                "unmodeled_serial_response_intercept_sd":propensity_sd,
                "response_model_correctly_specified":propensity_sd==0,
                "audit_q":q,"method":method,"attempted":repetitions,
                "completed":len(rows),"refused":sum(failed[method].values()),
                "failure_reasons":dict(sorted(failed[method].items())),
                "gamma_bias_against_structural_truth":g["mean_bias"],
                "gamma_rmse_against_structural_truth":g["rmse"],
                "gamma_median":g["median"],
                "median_standard_error_diagnostic":float(np.median([v["se"] for v in rows])) if rows else None,
                "normal90_diagnostic_hit_per_completed":float(np.mean([v["hit"] for v in rows])) if rows else None,
                "diagnostic_false_narrow_per_attempt":float(sum(v["false_narrow"] for v in rows)/repetitions),
                "mean_lag1_gamma_score_correlation":float(np.mean(lag_values)) if lag_values else None,
                "confidence_interval_calibrated":False,
                "structural_gamma_point_identified_when_omitted_effect":False if propensity_sd>0 else None,
                "statistical_acceptance":False})
    covariance=[]
    for name,T,rho,nugget in COV_WORLDS:
        info=covariance_fisher_information(years=T,rho=rho,
                            year_nugget_variance=nugget)
        estimates=[];failed=Counter()
        for rep in range(repetitions):
            obs,evaluator=generate_covariance_development(
                years=T,rho=rho,nugget_variance=nugget,
                seed=development_seed(f"covariance|{name}|{rep}"))
            try:
                estimate=recovery_quasi_moments(obs)
                estimates.append(estimate)
            except (IdentificationFailure, ValueError, ArithmeticError, np.linalg.LinAlgError) as err:
                reason=f"{type(err).__name__}:{err}"
                failed[reason]+=1
                failures.append({"type":"covariance_panel","scenario":name,
                                 "replicate":rep,"methods":["within_era_quasi_moment"],
                                 "reason":reason,"expected_nonidentification":False})
        if len(estimates)+sum(failed.values())!=repetitions:
            raise RuntimeError("covariance attempt conservation failed")
        rh=summarize_values([v["rho_hat"] for v in estimates],rho,repetitions)
        nug=summarize_values([v["year_nugget_variance_hat"] for v in estimates],nugget,repetitions)
        measured=summarize_values([v["replicate_measurement_noise_hat"] for v in estimates],.12**2,repetitions)
        covariance.append({"scenario":name,"T":T,"true_rho_evaluator_only":rho,
            "true_year_nugget_variance_evaluator_only":nugget,
            "method":"within_era_quasi_moment","attempted":repetitions,
            "completed":len(estimates),"refused":sum(failed.values()),
            "failure_reasons":dict(sorted(failed.items())),
            "rho_bias_completed":rh["mean_bias"],"rho_rmse_completed":rh["rmse"],
            "nugget_bias_completed":nug["mean_bias"],"nugget_rmse_completed":nug["rmse"],
            "replicate_noise_bias_completed":measured["mean_bias"],
            "unrestricted_information_rank":info["unrestricted_rank"],
            "unrestricted_parameter_count":info["unrestricted_parameter_count"],
            "year_nugget_measurement_derivative_alias":info["measurement_nugget_derivatives_identical"],
            "external_fixed_information_min_eigenvalue":info["fixed_external_noise_min_information"],
            "external_fixed_information_condition":info["fixed_external_noise_condition"],
            "independent_external_nugget_recovery_established":False,
            "statistical_acceptance":False})
    summary={"schema":"un.w4.v3.dependence-development.v1",
         "stage":"DEVELOPMENT_ONLY_NOT_PREREGISTERED",
         "seed_namespace":NAMESPACE,"repetitions_per_scenario":repetitions,
         "gamma_scenarios":len(GAMMA_WORLDS),"covariance_scenarios":len(COV_WORLDS),
         "gamma_panel_attempts":len(GAMMA_WORLDS)*repetitions,
         "gamma_method_attempts":len(GAMMA_WORLDS)*repetitions*len(METHODS),
         "gamma_method_completed":sum(row["completed"] for row in gamma),
         "gamma_method_refusals":sum(row["refused"] for row in gamma),
         "gamma_panel_completed":sum(row["completed"] for row in gamma if row["method"]==METHODS[0]),
         "gamma_panel_refusals":sum(row["refused"] for row in gamma if row["method"]==METHODS[0]),
         "covariance_panel_attempts":len(COV_WORLDS)*repetitions,
         "covariance_panel_completed":sum(row["completed"] for row in covariance),
         "covariance_panel_refusals":sum(row["refused"] for row in covariance),
         "failure_ledger_count":len(failures),
         "gamma":gamma,"covariance":covariance,
         "holdout_attempted":0,"real_original_sources_read":0,
         "v2_thresholds_modified":False,"v3_thresholds_frozen":False,
         "fitted_year_gamma_intervals_approved":False,
         "year_nugget_identified":False,"statistical_acceptance":False,
         "real_fit_authorized":False}
    assert summary["gamma_method_attempts"]==summary["gamma_method_completed"]+summary["gamma_method_refusals"]
    assert summary["covariance_panel_attempts"]==summary["covariance_panel_completed"]+summary["covariance_panel_refusals"]
    assert len(failures)==summary["gamma_method_refusals"]+summary["covariance_panel_refusals"]
    return summary,failures


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase",required=True,choices=("development","holdout","real"))
    ap.add_argument("--repetitions",type=int,default=60)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    if args.phase!="development":
        ap.error("v3 confirmatory holdout and historical real fitting prohibited")
    if args.out.exists():
        ap.error("refusing overwrite of existing development receipts")
    summary,failures=run_development(args.repetitions)
    args.out.mkdir(parents=True,exist_ok=False)
    (args.out/"development_aggregate.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    (args.out/"development_failure_ledger.json").write_text(json.dumps(failures,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"stage":summary["stage"],"gamma_attempted":summary["gamma_panel_attempts"],
       "gamma_completed":summary["gamma_panel_completed"],
       "gamma_refused":summary["gamma_panel_refusals"],
       "gamma_method_refusals":summary["gamma_method_refusals"],
       "covariance_attempted":summary["covariance_panel_attempts"],
       "covariance_completed":summary["covariance_panel_completed"],
       "covariance_refused":summary["covariance_panel_refusals"],
       "failed_records":len(failures),"holdout_attempted":0},sort_keys=True))


if __name__=="__main__":
    main()
