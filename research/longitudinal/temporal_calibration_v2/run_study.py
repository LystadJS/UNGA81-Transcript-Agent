"""Independently seeded synthetic development/holdout, frozen before holdout.

Development emits critical values; commit that receipt *before* using --phase holdout.
All known truth remains in the evaluation loop. fit_panel sees observed arrays only.
This command has no empirical inputs, real-fitting mode, or production output.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import numpy as np
import scipy
from scipy.stats import t as student_t
from inference import METHODS,NotIdentified,FitFailure,fit_panel,RHO_GRID,NUGGET_GRID
from synthetic_dev import draw,DEV_NAMESPACE
from synthetic_holdout import independently_draw,HOLDOUT_NAMESPACE

T_VALUES=(16,24,32)
MASKS=('near_census','stratified_2_of_3')
WORLDS=('iid_MAR','AR1_MAR','AR1_MNAR_audited','AR1_MNAR_no_audit',
        'AR1_nugget_MNAR_audited')
DEVELOPMENT_REPS=120
HOLDOUT_REPS=240
ALPHA=.10
# PRESERVED FROM ORIGINAL PR #62: not revised using new holdout observations.
ACCEPTANCE={'min_holdout_completion_rate':.95,'target_coverage':.90,
            'max_coverage_deviation':.05,'wilson_interval_must_include_nominal':True,
            'max_absolute_rho_bias':.12,'max_rho_rmse':.25,
            'max_rho_boundary_fraction':.05,'max_absolute_gamma_bias':.20,
            'max_gamma_rmse':.45,'max_median_interval_width':.80}
CODE_FILES=('inference.py','synthetic_dev.py','synthetic_holdout.py','run_study.py')
SCHEMA='un.w4.temporal_calibration_v2.frozen_development.v1'


def digest_file(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_hashes():
    directory=Path(__file__).resolve().parent
    return {name:digest_file(directory/name) for name in CODE_FILES}


def wilson(k,n):
    if n==0:return (None,None)
    z=1.959963984540054
    p=k/n; denom=1+z*z/n
    mid=(p+z*z/(2*n))/denom
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
    return (float(mid-half),float(mid+half))


def _metric(x,true):
    if not x:return {'bias':None,'rmse':None}
    e=np.asarray(x,float)-true
    return {'bias':float(e.mean()),'rmse':float(np.sqrt(np.mean(e*e)))}


def _make_summary(years,mask,world,method,phase,run_list,failures,frozen=None):
    n=len(run_list); attempted=DEVELOPMENT_REPS if phase=='development' else HOLDOUT_REPS
    expected_no_audit=world=='AR1_MNAR_no_audit'
    rr=[x[method] for x in run_list]
    rho_true=0.0 if world=='iid_MAR' else .65
    gamma_true=-1.25 if 'MNAR' in world else 0.
    gamma=_metric([x['gamma'] for x in run_list],gamma_true)
    rho=_metric([v['rho_hat'] for v in rr],rho_true) if method!='iid_year' else {'bias':None,'rmse':None}
    default=float(student_t.ppf(.95,years-3))
    critical=(frozen or {}).get('critical_values',{}).get(str(years),{}).get(method,default)
    critical=float(critical)
    cover0=sum(int(v['beta_hat']-default*v['se']<=x['truth_beta']<=v['beta_hat']+default*v['se'])
               for v,x in zip(rr,run_list))
    cover=sum(int(v['beta_hat']-critical*v['se']<=x['truth_beta']<=v['beta_hat']+critical*v['se'])
               for v,x in zip(rr,run_list))
    width=[2*critical*v['se'] for v in rr]
    misses=[not(v['beta_hat']-critical*v['se']<=x['truth_beta']<=v['beta_hat']+critical*v['se'])
            for v,x in zip(rr,run_list)]
    mc=float(math.sqrt((cover/n)*(1-cover/n)/n)) if n else None
    ci=wilson(cover,n)
    boundary=sum(v['rho_boundary'] for v in rr)/n if n and method!='iid_year' else None
    profile=sum(v['weakly_identified_rho'] for v in rr)/n if n and method!='iid_year' else None
    rho_ok=bool(method!='iid_year' and rho['bias'] is not None and
        abs(rho['bias'])<=ACCEPTANCE['max_absolute_rho_bias'] and
        rho['rmse']<=ACCEPTANCE['max_rho_rmse'] and
        boundary<ACCEPTANCE['max_rho_boundary_fraction'])
    gamma_ok=bool(n and (not 'MNAR' in world or
       (abs(gamma['bias'])<=ACCEPTANCE['max_absolute_gamma_bias'] and
        gamma['rmse']<=ACCEPTANCE['max_gamma_rmse'])))
    coverage_ok=bool(phase=='holdout' and n>=math.ceil(attempted*.95) and
      abs(cover/n-.90)<=.05 and ci[0]<=.90<=ci[1])
    practical_ok=bool(n and np.median(width)<=ACCEPTANCE['max_median_interval_width'])
    results={
      'phase':phase,'years':years,'mask':mask,'world':world,'method':method,
      'attempted':attempted,'completed':n,'support_failures':sum(failures.values())-
          failures.get('EXPECTED_NO_AUDIT_NONIDENTIFICATION',0),
      'expected_no_audit_abstentions':failures.get('EXPECTED_NO_AUDIT_NONIDENTIFICATION',0),
      'unsafe_unidentified_fits':sum(x.get('unsafe',False) for x in run_list) if expected_no_audit else 0,
      'failure_reasons':dict(sorted(failures.items())),
      'nominal_covered':cover0,'nominal_coverage':float(cover0/n) if n else None,
      'calibrated_covered':cover,'calibrated_coverage':float(cover/n) if n else None,
      'coverage_MC_SE':mc,'wilson95_low':ci[0],'wilson95_high':ci[1],
      'critical_value':critical,'median_width':float(np.median(width)) if n else None,
      'p90_width':float(np.quantile(width,.9)) if n else None,
      'false_confidence_count':sum(bool(m) and w<=.80 for m,w in zip(misses,width)),
      'false_confidence_rate_per_attempt':float(sum(bool(m) and w<=.80 for m,w in zip(misses,width))/attempted),
      'beta_bias':_metric([v['beta_hat'] for v in rr],.20)['bias'],
      'beta_rmse':_metric([v['beta_hat'] for v in rr],.20)['rmse'],
      'rho_bias':rho['bias'],'rho_rmse':rho['rmse'],
      'rho_boundary_rate':boundary,'weakly_identified_profile_fraction':profile,
      'gamma_bias':gamma['bias'],'gamma_rmse':gamma['rmse'],
      'year_effective_n_min_median':float(np.median([x['year_neff_min'] for x in run_list])) if n else None,
      'year_meeting_delete_var_median':float(np.median([x['meeting_var_median'] for x in run_list])) if n else None,
      'median_frame_opportunities':float(np.median([x['frame_total'] for x in run_list])) if n else None,
      'median_original_meeting_sample_speeches':float(np.median([x['selected_total'] for x in run_list])) if n else None,
      'median_verified_responders':float(np.median([x['responded_total'] for x in run_list])) if n else None,
      'median_random_audit_observed':float(np.median([x['audited_total'] for x in run_list])) if n else None,
      'passes_coverage':coverage_ok,'passes_rho_recovery':rho_ok,
      'passes_gamma_recovery':gamma_ok,'practical_width':practical_ok,
      'statistical_acceptance':bool(coverage_ok and rho_ok and gamma_ok and practical_ok),
      'real_fit_authorized':False,
    }
    return results


def evaluate(phase,frozen=None):
    H=DEVELOPMENT_REPS if phase=='development' else HOLDOUT_REPS
    generator=draw if phase=='development' else independently_draw
    summaries=[]; failure_ledger=[]; for_cutoffs=defaultdict(list)
    for T in T_VALUES:
      for mask in MASKS:
       for world in WORLDS:
        successes=[]; failures=Counter()
        for r in range(H):
            observed,truth=generator(T,mask,world,r)
            try:
                fit=fit_panel(observed)
                if world=='AR1_MNAR_no_audit':
                    failures['UNSAFE_FIT_WITHOUT_AUDIT']+=1
                    continue
                record={'truth_beta':truth['beta'],'gamma':fit['annual']['gamma'],
                    'year_neff_min':float(fit['annual']['year_effective_n'].min()),
                    'meeting_var_median':float(np.median(fit['annual']['annual_meeting_delete_variance'])),
                    'frame_total':truth['frame_total'],'selected_total':truth['selected_total'],
                    'responded_total':truth['responded_total'],'audited_total':truth['audited_total']}
                for method in METHODS:
                    v=fit['methods'][method]
                    if not math.isfinite(v['beta_hat']) or not math.isfinite(v['se']) or v['se']<=0:
                        raise FitFailure('nonfinite fitted effect or standard error')
                    record[method]=v
                    for_cutoffs[(T,method)].append(abs((v['beta_hat']-truth['beta'])/v['se']))
                successes.append(record)
            except NotIdentified as err:
                label=('EXPECTED_NO_AUDIT_NONIDENTIFICATION' if world=='AR1_MNAR_no_audit'
                       else 'UNEXPECTED_NONIDENTIFICATION:'+str(err))
                failures[label]+=1
                failure_ledger.append({'years':T,'mask':mask,'world':world,'replicate':r,'reason':label})
            except (FitFailure,ValueError,ArithmeticError,np.linalg.LinAlgError) as err:
                label=f'{type(err).__name__}:{str(err)}'
                failures[label]+=1
                failure_ledger.append({'years':T,'mask':mask,'world':world,'replicate':r,'reason':label})
        for method in METHODS:
            summaries.append(_make_summary(T,mask,world,method,phase,successes,failures,frozen))
        print(f'{phase:11s} T={T} {mask:17s} {world:26s} '+
              f'attempted={H}, success={len(successes)}, missing={sum(failures.values())}',flush=True)
    return summaries,failure_ledger,for_cutoffs


def frozen_receipt(summaries,cutoffs):
    critical={}
    for T in T_VALUES:
        critical[str(T)]={}
        for method in METHODS:
            values=cutoffs[(T,method)]
            if len(values)<500:
                raise ValueError(f'INSUFFICIENT DEVELOPMENT SUPPORT T={T} {method}: {len(values)}')
            critical[str(T)][method]=float(max(student_t.ppf(.95,T-3),np.quantile(values,.9)))
    receipt={
        'schema':SCHEMA,'study_status':'DEVELOPMENT_ONLY_UNTIL_FROZEN_COMMIT',
        'development_seed_namespace':DEV_NAMESPACE,'holdout_seed_namespace':HOLDOUT_NAMESPACE,
        'development_panels_per_scenario':DEVELOPMENT_REPS,
        'locked_holdout_panels_per_scenario':HOLDOUT_REPS,
        'years':list(T_VALUES),'masks':list(MASKS),'worlds':list(WORLDS),
        'models':list(METHODS),'nugget_grid':list(NUGGET_GRID),'rho_grid':list(RHO_GRID),
        'acceptance_thresholds':ACCEPTANCE,'frozen_code_hashes':code_hashes(),
        'development_attempted_panels':len(T_VALUES)*len(MASKS)*len(WORLDS)*DEVELOPMENT_REPS,
        'development_completed_identifiable_panels':sum(r['completed'] for r in summaries if r['method']==METHODS[0]),
        'development_expected_nonidentification':sum(r['expected_no_audit_abstentions'] for r in summaries if r['method']==METHODS[0]),
        'critical_values':critical,'holdout_inspected_at_freeze':False,
        'frozen_original_W4_thresholds_preserved':True,
        'source_audit_or_real_inference_authorized':False,
        'thresholds_may_not_change_after_holdout':True}
    return receipt


def validate_frozen(r):
    if (r.get('schema')!=SCHEMA or r.get('holdout_inspected_at_freeze') is not False or
            r.get('development_seed_namespace')!=DEV_NAMESPACE or
            r.get('holdout_seed_namespace')!=HOLDOUT_NAMESPACE):
        raise ValueError('missing or previously inspected frozen development identity')
    if r.get('frozen_code_hashes')!=code_hashes():
        raise ValueError('code hashes differ from prespecified frozen development producer')
    if (r.get('acceptance_thresholds')!=ACCEPTANCE or r.get('models')!=list(METHODS) or
            r.get('years')!=list(T_VALUES) or r.get('masks')!=list(MASKS) or
            r.get('worlds')!=list(WORLDS) or r.get('rho_grid')!=list(RHO_GRID) or
            r.get('nugget_grid')!=list(NUGGET_GRID) or
            r.get('locked_holdout_panels_per_scenario')!=HOLDOUT_REPS):
        raise ValueError('post-freeze method/scenario/threshold mutation refused')
    if (r.get('development_completed_identifiable_panels',0)<2000 or
            r.get('development_expected_nonidentification')!=len(T_VALUES)*len(MASKS)*DEVELOPMENT_REPS):
        raise ValueError('insufficient development support / no-audit abstentions')
    for T in T_VALUES:
        for method in METHODS:
            v=r.get('critical_values',{}).get(str(T),{}).get(method)
            if not isinstance(v,(int,float)) or not np.isfinite(v) or v<student_t.ppf(.95,T-3):
                raise ValueError('invalid post-development locked critical value')


def store(out,summaries,failures,receipt=None):
    out.mkdir(parents=True,exist_ok=False)
    (out/'synthetic_scenario_aggregate.json').write_text(json.dumps(summaries,indent=2,sort_keys=True)+'\n')
    (out/'synthetic_failure_ledger.json').write_text(json.dumps(failures,indent=2,sort_keys=True)+'\n')
    if receipt is not None:
        (out/'frozen_development_candidate.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    summary={
      'phase':summaries[0]['phase'],'scenarios':len(T_VALUES)*len(MASKS)*len(WORLDS),
      'methods':list(METHODS),'panels_attempted':sum(s['attempted'] for s in summaries if s['method']==METHODS[0]),
      'panels_completed':sum(s['completed'] for s in summaries if s['method']==METHODS[0]),
      'expected_no_audit_abstentions':sum(s['expected_no_audit_abstentions'] for s in summaries if s['method']==METHODS[0]),
      'unexpected_failures':sum(s['support_failures'] for s in summaries if s['method']==METHODS[0]),
      'unsafe_no_audit_fits':sum(s['unsafe_unidentified_fits'] for s in summaries if s['method']==METHODS[0]),
      'pass_recovery_scenarios':{method:sum(s['passes_rho_recovery'] for s in summaries if s['method']==method)
                                 for method in METHODS},
      'pass_coverage_scenarios':{method:sum(s['passes_coverage'] for s in summaries if s['method']==method)
                                 for method in METHODS},
      'statistical_acceptance':False,
      'independent_real_source_selection_audit':False,
      'new_real_2008_2023_model_fit':False,
      'empirical_publication_eligible':False,
      'numpy_version':np.__version__,'scipy_version':scipy.__version__,
      'python_version':platform.python_version(),'code_hashes':code_hashes(),
      'sensitivity_note':'Known DGP contrasts are distinct from unverifiable real source selection and 64D discourse movement.'}
    if summaries[0]['phase']=='holdout':
        # Exactly declared T16, both source designs, all identifiable stress worlds.
        t16=[x for x in summaries if x['years']==16 and x['world']!='AR1_MNAR_no_audit']
        summary['synthetic_T16_candidate_families_passing']=sorted({method for method in METHODS
            if all(x['statistical_acceptance'] for x in t16 if x['method']==method)})
    (out/'aggregate_receipt.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    return summary


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--phase',choices=('development','holdout'),required=True)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--frozen',type=Path)
    ap.add_argument('--frozen-sha256')
    args=ap.parse_args()
    if args.out.exists():raise SystemExit('Refusing to overwrite existing synthetic receipts')
    if args.phase=='development':
        if args.frozen or args.frozen_sha256:raise SystemExit('Development must not read holdout/frozen receipt')
        scenarios,failures,calibration=evaluate('development')
        frozen=frozen_receipt(scenarios,calibration)
        summary=store(args.out,scenarios,failures,frozen)
        print('Development receipt SHA256:',digest_file(args.out/'frozen_development_candidate.json'))
    else:
        if not args.frozen or not args.frozen_sha256 or len(args.frozen_sha256)!=64:
            raise SystemExit('Locked development file and exact precommitted SHA256 are mandatory')
        if digest_file(args.frozen)!=args.frozen_sha256:
            raise SystemExit('Frozen development bytes do not match precommitted SHA256')
        frozen=json.loads(args.frozen.read_text())
        validate_frozen(frozen)
        scenarios,failures,_=evaluate('holdout',frozen)
        summary=store(args.out,scenarios,failures)
    print(json.dumps(summary,indent=2,sort_keys=True))

if __name__=='__main__':main()
