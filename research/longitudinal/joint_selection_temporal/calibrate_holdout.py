"""Independently seeded, locked holdout calibration of joint selection/AR1 model.

Invoked only AFTER the development critical-value receipt was frozen. Imports
independently written heldout_world rather than synthetic_dev. Every attempted,
successful, nonconvergent and expected nonidentified panel is recorded.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.stats import t as student_t
from heldout_world import independently_generate
from joint_model import fit_observed,interval,NotIdentified,FitFailure

TVALUES=(16,24,32)
MASKS=('near_census','stratified_2_of_3')
WORLDS=('iid_MAR','AR1_MAR','AR1_MNAR_audited','AR1_MNAR_no_audit')
H=240
TARGET=.90


def wilson(success,total):
    if total<=0:return (None,None)
    z=1.959963984540054
    p=success/total
    denom=1+z*z/total
    mid=(p+z*z/(2*total))/denom
    rad=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/denom
    return (float(mid-rad),float(mid+rad))


def moment_stats(entries,parameter,true_value):
    errors=np.asarray([e[parameter]-true_value for e in entries],float)
    if not len(errors):return {'bias':None,'rmse':None}
    return {'bias':float(errors.mean()),'rmse':float(np.sqrt(np.mean(errors**2)))}


def check_one(T,mask,world,frozen):
    expected_nonidentifiable=(world=='AR1_MNAR_no_audit')
    attempts=[]
    successes=[]
    absent=[]
    for rep in range(H):
        datum=independently_generate(T,mask,world,rep)
        frame=datum['observed']
        real_truth=datum['truth']  # known truth is held only by evaluator
        try:
            fit=fit_observed(frame)
            if expected_nonidentifiable:
                absent.append({'replicate':rep,'type':'UNSAFE_FIT_NO_RANDOM_AUDIT'})
                continue
            base=interval(fit)
            calibrated=interval(fit,frozen['results'][str(T)]['locked_cutoff'])
            if not all(math.isfinite(z) for z in (fit['beta'],fit['se'],
                    fit['rho'],fit['selection_gamma'],calibrated.lower,calibrated.upper)):
                raise FitFailure('Nonfinite locked test result')
            successes.append({
                'replicate':rep,'beta':fit['beta'],'se':fit['se'],
                'rho':fit['rho'],'rho_boundary':fit['rho_at_grid_end'],
                'nugget':fit['nugget'],'selection_gamma':fit['selection_gamma'],
                'n_audited_missing':fit['audited_missing_n'],
                'year_n_eff_min':fit['year_neff_min'],
                'base_contains':base.lower<=real_truth['beta']<=base.upper,
                'calibrated_contains':calibrated.lower<=real_truth['beta']<=calibrated.upper,
                'base_width':base.width,'calibrated_width':calibrated.width})
        except NotIdentified as e:
            absent.append({'replicate':rep,'type':'EXPECTED_NO_AUDIT_ABSTAIN'
                           if expected_nonidentifiable else 'UNEXPECTED_NONIDENTIFICATION'})
        except (FitFailure,np.linalg.LinAlgError,FloatingPointError,ValueError) as e:
            absent.append({'replicate':rep,'type':type(e).__name__})
    if expected_nonidentifiable:
        return [
         {'years':T,'source_mask':mask,'world':world,'interval_method':'ABSTAIN_NO_IDENTIFICATION',
          'attempted':H,'evaluated':0,'failed':sum(x['type']!='EXPECTED_NO_AUDIT_ABSTAIN' for x in absent),
          'expected_identification_refusals':sum(x['type']=='EXPECTED_NO_AUDIT_ABSTAIN' for x in absent),
          'unsafe_fit_count':sum(x['type']=='UNSAFE_FIT_NO_RANDOM_AUDIT' for x in absent),
          'coverage':None,'covered':None,'Wilson95_lower':None,'Wilson95_upper':None,
          'coverage_MC_SE':None,'median_width':None,'p90_width':None,
          'mean_rho':None,'rho_bias':None,'rho_RMSE':None,'rho_boundary_fraction':None,
          'mean_gamma':None,'gamma_bias':None,'gamma_RMSE':None,
          'median_year_n_eff_min':None,
          'passes_holdout_coverage':False,'passes_rho_recovery':False,
          'passes_gamma_recovery':False,'joint_temporal_inference_eligible':False}
        ],absent
    out=[]
    count=len(successes)
    rho_truth=0. if world=='iid_MAR' else .65
    gamma_truth=-1.25 if 'MNAR' in world else 0.
    rho=moment_stats(successes,'rho',rho_truth)
    gamma=moment_stats(successes,'selection_gamma',gamma_truth)
    rb=float(np.mean([p['rho_boundary'] for p in successes])) if count else None
    rho_accepted=bool(count>=228 and abs(rho['bias'])<=.12 and
                      rho['rmse']<=.25 and rb<.05)
    gam_accepted=bool(count>=228 and
        (world!='AR1_MNAR_audited' or
         (abs(gamma['bias'])<=.20 and gamma['rmse']<=.45)))
    for label in ('base','calibrated'):
        tally=sum(bool(p[f'{label}_contains']) for p in successes)
        frac=tally/count if count else None
        bounds=wilson(tally,count)
        widths=[p[f'{label}_width'] for p in successes]
        median=float(np.median(widths)) if widths else None
        coverage_pass=bool(count>=228 and abs(frac-TARGET)<=.05 and
            bounds[0]<=TARGET<=bounds[1])
        out.append({
          'years':T,'source_mask':mask,'world':world,'interval_method':label,
          'attempted':H,'evaluated':count,'failed':H-count,'expected_identification_refusals':0,
          'unsafe_fit_count':0,'covered':tally,'coverage':frac,
          'Wilson95_lower':bounds[0],'Wilson95_upper':bounds[1],
          'coverage_MC_SE':float(np.sqrt(frac*(1-frac)/count)) if count else None,
          'median_width':median,'p90_width':float(np.quantile(widths,.90)) if widths else None,
          'impractically_broad_over_point8':bool(median is not None and median>.8),
          'mean_rho':float(np.mean([p['rho'] for p in successes])) if count else None,
          'rho_bias':rho['bias'],'rho_RMSE':rho['rmse'],'rho_boundary_fraction':rb,
          'mean_gamma':float(np.mean([p['selection_gamma'] for p in successes])) if count else None,
          'gamma_bias':gamma['bias'],'gamma_RMSE':gamma['rmse'],
          'median_year_n_eff_min':float(np.median([p['year_n_eff_min'] for p in successes])) if count else None,
          'passes_holdout_coverage':coverage_pass,'passes_rho_recovery':rho_accepted,
          'passes_gamma_recovery':gam_accepted,
          'joint_temporal_inference_eligible':coverage_pass and rho_accepted and gam_accepted
          and not bool(median is not None and median>.8)})
    return out,absent


def evaluate(frozen):
    if frozen.get('schema')!='un.w4.joint_source_selection.development_cutoffs.v1' or \
      frozen.get('master_seed_namespace','UNGA81-JOINT-DEV-20261013')!='UNGA81-JOINT-DEV-20261013' or \
      frozen.get('holdout_inspected') is not False or frozen.get('R')!=120:
        raise ValueError('Unapproved development calibration or inspected holdout')
    if set(frozen['results'])!={'16','24','32'}:
        raise ValueError('Frozen horizons or multipliers changed')
    for T in TVALUES:
        q=frozen['results'][str(T)]
        if not (q['usable_development_panels']>=650 and
                q['locked_cutoff']>=student_t.ppf(.95,T-3)-1e-10):
            raise ValueError('Insufficient development calibration or invalid cutoff')
    records=[];failures=[]
    for T in TVALUES:
      for mask in MASKS:
        for world in WORLDS:
          res,why=check_one(T,mask,world,frozen)
          records.extend(res)
          for item in why:failures.append({'years':T,'source_mask':mask,'world':world,**item})
          print('HOLDOUT',T,mask,world,
            'n',res[0]['evaluated'],'coverage',[
               round(x['coverage'],3) if x['coverage'] is not None else None for x in res],
            'rho RMSE',round(res[0]['rho_RMSE'],3) if res[0]['rho_RMSE'] is not None else None,flush=True)
    return records,failures


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--frozen-development',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError('Independent holdout output must not be overwritten')
    raw=a.frozen_development.read_bytes()
    frozen=json.loads(raw)
    a.out.mkdir(parents=True)
    records,failures=evaluate(frozen)
    with (a.out/'independent_holdout_scenarios.csv').open('x',encoding='utf-8',newline='') as f:
        fields=sorted(set(k for x in records for k in x))
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
    (a.out/'holdout_exclusion_ledger.json').write_text(json.dumps(failures,indent=2)+'\n')
    identifying=[x for x in records if x['interval_method']=='calibrated']
    unaudited=[x for x in records if x['interval_method']=='ABSTAIN_NO_IDENTIFICATION']
    horizon16=[x for x in identifying if x['years']==16]
    holdout_pass=bool(len(horizon16)==6 and all(x['joint_temporal_inference_eligible'] for x in horizon16)
       and all(x['expected_identification_refusals']==240 and
         x['unsafe_fit_count']==0 for x in unaudited))
    summary={
       'schema':'un.w4.joint_selection_serial_dependence.independent_holdout.v1',
       'preregistration_date':'2026-10-13','holdout_seed_namespace':'UNGA81-JOINT-HOLDOUT-20261014',
       'development_receipt_sha256':hashlib.sha256(raw).hexdigest(),
       'horizons':[16,24,32],'worlds':list(WORLDS),'masks':list(MASKS),
       'scenarios':24,'holdout_panels_attempted':24*H,
       'expected_MNAR_no_audit_abstentions':6*H,
       'actual_MNAR_no_audit_abstentions':sum(x['expected_identification_refusals'] for x in unaudited),
       'unsafe_no_audit_fits':sum(x['unsafe_fit_count'] for x in unaudited),
       'identifiable_methods_reported':['base','calibrated'],
       'identifiable_scenarios':18,
       'calibrated_coverage_scenarios_passed':sum(x['passes_holdout_coverage'] for x in identifying),
       'rho_point_reliability_scenarios_passed':sum(x['passes_rho_recovery'] for x in identifying),
       'gamma_MNAR_audited_scenarios_passed':sum(x['passes_gamma_recovery'] for x in identifying if x['world']=='AR1_MNAR_audited'),
       'horizon_16_all_preregistered_numerical_gates_passed':holdout_pass,
       'actual_random_audit_of_UN_missing_outcomes_verified':False,
       'cross_2008_2023_frozen_source_comparability_accepted':False,
       'new_real_2008_2023_representation_fitted':False,
       'actual_UN_temporal_inference_eligible':False,
       'country_political_stance_estimated':False,
       'publication_eligible':False,'heldout_2026_meeting_sources_opened':0,
       'limitations':['Independent holdout is still from a known synthetic DGP, not observed real UN year processes.',
                      'Temporal covariance uses finite T and a fixed family; even interval coverage passes cannot identify real MNAR without a source-random audit.',
                      'Country/meeting/year selection and source text genre/corpus drift remain real empirical gates.']}
    (a.out/'independent_holdout_aggregate.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k in (
        'holdout_panels_attempted','expected_MNAR_no_audit_abstentions',
        'actual_MNAR_no_audit_abstentions','unsafe_no_audit_fits',
        'calibrated_coverage_scenarios_passed','rho_point_reliability_scenarios_passed',
        'gamma_MNAR_audited_scenarios_passed',
        'horizon_16_all_preregistered_numerical_gates_passed',
        'new_real_2008_2023_representation_fitted')},indent=2))


if __name__=='__main__':main()
