"""Independent synthetic V3 DEVELOPMENT benchmark; no confirmatory holdout.

The independent generator returns estimator-visible observations and separate
truth to the evaluator. Every numeric refusal has an exact method/replicate key.
Neither this module nor imported code can fit historical transcripts.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from scipy.special import expit
from scipy.stats import t as student_t
from .v3_nuisance import IdentificationFailure
from .v3_serial_partial import GAMMA_METHODS, estimate_serial_response, covariance_union, independent_measurement_bounds

NAMESPACE="UNGA81-V3-SERIAL-PARTIAL-NEW-DEV-20261015-NO-HOLDOUT"
GAMMA_CASES=(
    ("correct_iid_T16",16,0.0,0.0,0.0,0.35),
    ("serial_independent_T16",16,0.65,0.8,0.0,0.35),
    ("serial_correlated_T16",16,0.65,0.8,0.7,0.35),
    ("serial_correlated_T32",32,0.65,0.8,0.7,0.35),
    ("weak_audit_T16",16,0.65,0.8,0.7,0.025),
    ("no_audit_T16",16,0.65,0.8,0.7,0.0),
)
COV_CASES=(
    ("stationary_T16_rho065",16,0.65,0.025,False,False),
    ("strong_rho_T16",16,0.85,0.025,False,False),
    ("near_zero_rho_T16",16,0.05,0.025,False,False),
    ("stationary_T32_rho065",32,0.65,0.025,False,False),
    ("nonstationary_T16",16,0.65,0.025,True,False),
    ("shared_measurement_error_T16",16,0.65,0.025,False,True),
)
COV_METHODS=("wide", "narrow", "externally_constrained")
Z90=1.6448536269514722


def seed(label):
    return int.from_bytes(hashlib.sha256((NAMESPACE+'|'+label).encode()).digest()[:8],'big')


def generate_gamma(case,rep):
    name,T,rho,sd,correlation,q=case
    rng=np.random.default_rng(seed(f'gamma|{name}|{rep}'))
    nmeet,nactor=9,12
    shape=(T,nmeet,nactor)
    y=np.full(shape,np.nan)
    included=np.zeros(shape,bool)
    responded=np.zeros(shape,bool)
    audited=np.zeros(shape,bool)
    at_risk=np.ones(shape,bool)
    pi=np.full(shape,2/3)
    q_array=np.zeros(shape)
    at_risk[:2,:,0]=False
    actor=rng.normal(0,.3,nactor)
    year_y=year_r=0.0
    for t in range(T):
        z1,z2=rng.standard_normal(2)
        year_y = rho*year_y + math.sqrt(1-rho*rho)*.20*z1
        year_r = rho*year_r + math.sqrt(1-rho*rho)*sd*(correlation*z1+math.sqrt(1-correlation**2)*z2)
        picked=np.zeros(nmeet,bool)
        for h in range(3):
            picked[rng.choice(np.arange(h*3,h*3+3),size=2,replace=False)]=True
        meeting_effect=rng.normal(0,.11,nmeet)
        eps=rng.normal(0,.3,(nmeet,nactor))
        truth=.20*(t>=T//2)+year_y+meeting_effect[:,None]+actor[None,:]+eps
        legal=picked[:,None]&at_risk[t]
        included[t]=legal
        p=expit(-.35 - 1.25*truth + year_r)
        r=(rng.random((nmeet,nactor))<p)&legal
        responded[t]=r
        aud=(rng.random((nmeet,nactor))<q)&legal&~r
        audited[t]=aud
        q_array[t][legal&~r]=q
        observed=r|aud
        y[t][observed]=truth[observed]
    return {
        'value':y,'included':included,'responded':responded,'audited':audited,
        'inclusion_probability':pi,'independent_audit_probability':q_array,
        'at_risk':at_risk,'independent_audit_provenance':q>0,
        'years':T,'design_id':'development_two_per_original_meeting_stratum',
    },{'gamma_true':-1.25,'response_year_sd':sd,'corr_innovations':correlation}


def generate_covariance(case,rep):
    name,T,rho,nugget,nonstationary,shared_measurement=case
    rng=np.random.default_rng(seed(f'covariance|{name}|{rep}'))
    latent=np.zeros(T)
    previous=0.0
    for t in range(T):
        previous=rho*previous+math.sqrt(1-rho*rho)*rng.normal(0,.20)
        latent[t]=previous
    innovation=rng.normal(0,math.sqrt(nugget),T)
    if nonstationary: innovation[T//2:]*=3
    sd_error=.12
    annual=latent+innovation+rng.normal(0,sd_error,T)
    annual[T//2:]+=.2
    independent_latent=rng.normal(size=32)
    shared=rng.normal(0,.2,32) if shared_measurement else np.zeros(32)
    a=independent_latent+shared+rng.normal(0,sd_error,32)
    b=independent_latent+shared+rng.normal(0,sd_error,32)
    observed={'annual':annual,'first_replicate':a,'second_replicate':b,
        'independent_pair_provenance':not shared_measurement}
    target_lambda=(nugget+sd_error**2)/(.04+nugget+sd_error**2)
    evaluator={'true_beta':.2,'rho':rho,'nugget':nugget,
               'lambda_effective':target_lambda,
               'stationary':not nonstationary}
    return observed,evaluator


def covariance_measured_noise_check(observed):
    if observed['independent_pair_provenance'] is not True:
        raise IdentificationFailure('external replicate source errors correlated')
    a,b=observed['first_replicate'],observed['second_replicate']
    if len(a)<16 or len(b)!=len(a) or not np.isfinite(a+b).all():
        raise IdentificationFailure('invalid independent replicate measurement calibration')
    return float(np.var(a-b,ddof=1)/2)


def _summary_fit(values,true):
    arr=np.array(values,float)
    return dict(bias=float(np.mean(arr-true)),rmse=float(np.sqrt(np.mean((arr-true)**2)))) if len(arr) else dict(bias=None,rmse=None)


def development_study(repetitions=30):
    if type(repetitions) is not int or not 8<=repetitions<=60:
        raise ValueError('development-only fixed 8..60 repetitions, no holdout')
    ledger=[]; gamma_rows=[]; covariance_rows=[]
    for case in GAMMA_CASES:
        name,T,rho,sd,correlation,q=case
        completed=defaultdict(list);failed={method:Counter() for method in GAMMA_METHODS}
        for rep in range(repetitions):
            observed, truth=generate_gamma(case,rep)
            for method in GAMMA_METHODS:
                try:
                    fit=estimate_serial_response(observed,method,lag=2)
                    hit=(fit['se_diagnostic'] is not None and
                         abs(fit['gamma_hat']-truth['gamma_true'])<=Z90*fit['se_diagnostic'])
                    completed[method].append({'gamma':fit['gamma_hat'],
                        'se':fit['se_diagnostic'],'rho':fit['rho_year_propensity_hat'],
                        'hit':hit,'miss_narrow':fit['se_diagnostic'] is not None and not hit and
                             2*Z90*fit['se_diagnostic']<=.6})
                except (IdentificationFailure,ValueError,np.linalg.LinAlgError) as e:
                    reason=type(e).__name__+':'+str(e)
                    failed[method][reason]+=1
                    ledger.append({'study':'response','scenario':name,'replicate':rep,
                                   'method':method,'reason':reason,
                                   'expected_refusal':q==0})
        for method in GAMMA_METHODS:
            vals=completed[method]; f=failed[method]
            assert len(vals)+sum(f.values())==repetitions
            metric=_summary_fit([v['gamma'] for v in vals],-1.25)
            diagnostic=[v for v in vals if v['se'] is not None]
            gamma_rows.append({'scenario':name,'T':T,'year_propensity_rho':rho,
                'response_year_sd':sd,'latent_year_outcome_response_correlation':correlation,
                'q':q,'method':method,'attempted':repetitions,'completed':len(vals),
                'failed':sum(f.values()),'fail_reasons':dict(sorted(f.items())),
                'gamma_bias_completed':metric['bias'],'gamma_rmse_completed':metric['rmse'],
                'gamma_se_diagnostic_median':float(np.median([v['se'] for v in diagnostic])) if diagnostic else None,
                'normal90_diagnostic_hit_completed':float(np.mean([v['hit'] for v in diagnostic])) if diagnostic else None,
                'false_confidence_narrow_per_attempt':sum(v['miss_narrow'] for v in vals)/repetitions,
                'estimated_ar1_year_intercept_rho_median':float(np.median([v['rho'] for v in vals]))
                    if method=='estimated_ar1_year_effects' and vals else None,
                'interval_calibrated':False,'statistical_acceptance':False})
    for case in COV_CASES:
        name,T,rho,nugget,nonstationary,shared=case
        complete=defaultdict(list);failed={method:Counter() for method in COV_METHODS}
        for rep in range(repetitions):
            observed,truth=generate_covariance(case,rep)
            for method in COV_METHODS:
                try:
                    external_est=covariance_measured_noise_check(observed)
                    bounds=independent_measurement_bounds(observed['first_replicate'],
                        observed['second_replicate'],source_independent=observed['independent_pair_provenance'])
                    fit=covariance_union(observed['annual'],alternative=method,
                        measurement_noise_lower_bound=(bounds['variance_lower']
                            if method=='externally_constrained' else None))
                    # Truth inclusion checked in evaluator ONLY; never an input to fit.
                    true_nuisance_within_range=(min(fit['rho_assumed_grid'])<=truth['rho']<=max(fit['rho_assumed_grid'])
                         and min(fit['effective_nugget_fraction_assumed_grid'])<=truth['lambda_effective']
                         <=max(fit['effective_nugget_fraction_assumed_grid']))
                    complete[method].append({'hit':fit['lower']<=truth['true_beta']<=fit['upper'],
                       'width':fit['width'],'profile_fraction':fit['profile_weak_support_count']/fit['grid_attempted'],
                       'externally_measured_error_estimate':external_est,
                       'nuisance_grid_rejections':fit['grid_rejected_by_external_noise'],
                       'truth_in_assumed_range':true_nuisance_within_range})
                except (IdentificationFailure,ValueError,np.linalg.LinAlgError) as e:
                    reason=type(e).__name__+':'+str(e)
                    failed[method][reason]+=1
                    ledger.append({'study':'covariance','scenario':name,'replicate':rep,
                                   'method':method,'reason':reason,
                                   'expected_refusal':shared})
        for method in COV_METHODS:
            vals=complete[method];f=failed[method]
            assert len(vals)+sum(f.values())==repetitions
            covariance_rows.append({'scenario':name,'T':T,'true_rho_evaluator_only':rho,
              'true_nugget_variance_evaluator_only':nugget,'nonstationary_stress':nonstationary,
              'replicate_independence_violated':shared,'method':method,
              'attempted':repetitions,'completed':len(vals),'failed':sum(f.values()),
              'fail_reasons':dict(sorted(f.items())),
              'sensitivity_envelope_hit_completed':float(np.mean([v['hit'] for v in vals])) if vals else None,
              'median_union_width':float(np.median([v['width'] for v in vals])) if vals else None,
              'mean_nuisance_profile_support_fraction':float(np.mean([v['profile_fraction'] for v in vals])) if vals else None,
              'mean_external_noise_rejected_nuisance_grid_points':float(np.mean([v['nuisance_grid_rejections'] for v in vals])) if vals else None,
              'evaluator_true_nuisance_in_assumed_range_fraction':float(np.mean([v['truth_in_assumed_range'] for v in vals])) if vals else None,
              'frequentist_coverage_calibrated':False,'statistical_acceptance':False})
    expected_gamma=len(GAMMA_CASES)*len(GAMMA_METHODS)*repetitions
    expected_cov=len(COV_CASES)*len(COV_METHODS)*repetitions
    gamma_fail=sum(x['failed'] for x in gamma_rows)
    cov_fail=sum(x['failed'] for x in covariance_rows)
    assert len(ledger)==gamma_fail+cov_fail
    return {'schema':'un.w4.v3.serial-partial-development.v1',
        'stage':'DEVELOPMENT_ONLY_UNFROZEN','seed_namespace':NAMESPACE,
        'repetitions_per_scenario':repetitions,'response_attempted':expected_gamma,
        'response_completed':expected_gamma-gamma_fail,'response_failed':gamma_fail,
        'covariance_attempted':expected_cov,'covariance_completed':expected_cov-cov_fail,
        'covariance_failed':cov_fail,'failure_ledger_count':len(ledger),
        'gamma':gamma_rows,'covariance':covariance_rows,'v3_holdout_attempted':0,
        'v2_files_modified':False,'real_original_transcripts_read':0,
        'freeze_approved':False,'statistical_acceptance':False,
        'empirical_fit_authorized':False},ledger


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--phase',required=True,choices=('development','holdout','real'))
    ap.add_argument('--repetitions',type=int,default=30)
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    if args.phase!='development':ap.error('v3 holdout and real fitting prohibited')
    if args.out.exists():ap.error('refusing overwrite of completed synthetic receipt')
    metrics,failures=development_study(args.repetitions)
    args.out.mkdir(parents=True,exist_ok=False)
    (args.out/'development_metrics.json').write_text(json.dumps(metrics,sort_keys=True,indent=2)+'\n')
    (args.out/'development_failures.json').write_text(json.dumps(failures,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'response_attempted':metrics['response_attempted'],
      'response_completed':metrics['response_completed'],'response_failed':metrics['response_failed'],
      'covariance_attempted':metrics['covariance_attempted'],
      'covariance_completed':metrics['covariance_completed'],
      'covariance_failed':metrics['covariance_failed'],
      'failed_records':metrics['failure_ledger_count'],'holdout_attempted':0},sort_keys=True))

if __name__=='__main__':main()
