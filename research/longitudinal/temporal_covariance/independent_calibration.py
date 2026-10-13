"""Independent known-truth calibration runner for estimated year covariance.

Synthetic-only. Two code paths: independent generator in synthetic_worlds.py,
covariance analysis in temporal_covariance.py. Reports failures, bias, RMSE,
coverage, Wilson uncertainty, practical interval widths, provenance identities.
No historical UN source text, speaker identity, government position or CI release.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import defaultdict
from pathlib import Path
import numpy as np
from temporal_covariance import (fit_year_covariance,welch_years,
      interval_contains,grid_identity,annual_gls,RHO_GRID,NUGGET_GRID)
from synthetic_worlds import draw_world,source_mask,TRUE_BETA
from scipy.linalg import solve_triangular
from scipy.stats import t as student_t

R=300
SEED=20261013
MASKS=('near_census','two_stage')
WORLDS=('iid_year','serial_year','informative_selection')
TVALUES=(8,16,24)
NOMINAL=.90

def wilson(k,n):
 if not n:return [None,None]
 z=1.959963984540054;p=k/n;d=1+z*z/n
 center=(p+z*z/(2*n))/d
 span=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
 return [center-span,center+span]

def summary(values,known_rho):
 out={'attempted':R,'evaluable':len(values),'failed':R-len(values),'rho_bias':None,
      'rho_rmse':None,'rho_boundary_fraction':None,'mean_nugget':None,
      'rho_point_reliable':False}
 if values:
  rho=np.asarray([r['rho'] for r in values])
  out.update({'rho_bias':float(rho.mean()-known_rho),
              'rho_rmse':float(np.sqrt(np.mean((rho-known_rho)**2))),
              'rho_boundary_fraction':float(np.mean([r['rho_boundary'] for r in values])),
              'mean_nugget':float(np.mean([r['lambda'] for r in values]))})
  out['rho_point_reliable']=bool(len(values)>=285 and abs(out['rho_bias'])<=.1
      and out['rho_rmse']<=.25 and out['rho_boundary_fraction']<.05)
 return out

def evaluate_scenario(T,mask,world,replications=R):
 results={name:{'covered':0,'valid':0,'widths':[],'point_errors':[],
                 'failure_kinds':defaultdict(int)}
          for name in ('year_welch','estimated_AR1_REML','covariance_family_envelope')}
 fit=[]
 output_failures=[]
 for rep in range(replications):
  try:
   draw=draw_world(T,mask,world,rep,SEED,TRUE_BETA)
   y=draw['year_means'];neff=draw['n_eff']
   model=fit_year_covariance(y,neff)
   ci={'year_welch':welch_years(y),
       'estimated_AR1_REML':model['estimated_interval'],
       'covariance_family_envelope':model['covariance_grid_envelope']}
   fit.append({'rho':model['fit_rho'],'lambda':model['fit_nugget'],
               'rho_boundary':model['rho_at_boundary']})
   for name,i in ci.items():
    require=all(math.isfinite(k) for k in (i.lower,i.upper,i.width,i.beta))
    if not require or i.lower>i.upper: raise ValueError('Bad '+name+' interval')
    a=results[name];a['valid']+=1
    a['covered']+=int(interval_contains(i,TRUE_BETA))
    a['widths'].append(i.width)
    a['point_errors'].append(i.beta-TRUE_BETA)
  except (FloatingPointError,ValueError,np.linalg.LinAlgError,ZeroDivisionError) as e:
   kind=type(e).__name__
   output_failures.append({'replicate':rep,'type':kind})
   for name,a in results.items():a['failure_kinds'][kind]+=1
 report=[]
 covsummary=summary(fit,0 if world=='iid_year' else .65)
 for name,x in results.items():
  n=x['valid'];p=x['covered']/n if n else None
  w=wilson(x['covered'],n)
  calibrated=bool(n>=285 and p is not None and abs(p-.9)<=.04 and
    w[0]<=.90<=w[1])
  median_width=float(np.median(x['widths'])) if x['widths'] else None
  report.append({'years':T,'era_years':T//2,'source_mask':mask,'year_world':world,
    'method':name,'attempted':replications,'evaluable':n,'failed':replications-n,
    'nominal':.90,'covered':x['covered'],'coverage':p,
    'coverage_mc_se':math.sqrt(p*(1-p)/n) if n else None,
    'Wilson95_low':w[0],'Wilson95_high':w[1],
    'median_interval_width':median_width,
    'point_bias':float(np.mean(x['point_errors'])) if n else None,
    'impractically_wide_over_0_8':bool(median_width is not None and median_width>.8),
    'passes_synthetic_DGP_calibration':calibrated,
    'estimated_rho_mean':covsummary['rho_bias']+(0 if world=='iid_year' else .65) if n else None,
    'estimated_rho_bias':covsummary['rho_bias'],
    'estimated_rho_RMSE':covsummary['rho_rmse'],
    'estimated_rho_grid_boundary_fraction':covsummary['rho_boundary_fraction'],
    'estimated_nugget_mean':covsummary['mean_nugget'],
    'rho_point_reliability_pass':covsummary['rho_point_reliable'],
    'true_rho_used_by_generator_only':0 if world=='iid_year' else .65,
    'true_sigma2_given_to_estimator':False,
    'sampling_design_probability_model_known':mask=='two_stage',
    'MNAR_selected_speech_nonresponse_model_known_to_estimator':False,
    'source_selection_generalizable_to_actual_UN':False,
    'actual_UN_CI_eligible':False})
 return report,output_failures

def selftest():
 from temporal_covariance import covariance_shape
 d=draw_world(8,'two_stage','iid_year',0,SEED)
 d0=draw_world(8,'two_stage','iid_year',0,SEED)
 assert np.array_equal(d['year_means'],d0['year_means'])
 assert (d['n_eff']<=99).all() and (d['n_eff']>2).all()
 C=covariance_shape(8,.65,.25,d['n_eff'])
 chol=np.linalg.cholesky(C)
 X=np.column_stack([np.ones(8),np.r_[np.zeros(4),np.ones(4)]])
 whitening=solve_triangular(chol,X,lower=True)
 wy=solve_triangular(chol,d['year_means'],lower=True)
 coef=np.linalg.lstsq(whitening,wy,rcond=None)[0]
 fit=annual_gls(d['year_means'],d['n_eff'],.65,.25)
 assert abs(fit['beta']-coef[1])<1e-10
 assert np.isfinite(fit['reml'])
 for true_effect in (0.,.20):
  paired=draw_world(8,'near_census','iid_year',3,SEED,true_effect)
  assert np.all(np.isfinite(paired['year_means']))
 # With noninformative selection, changing only beta by 0.20 moves each
 # late-year observed mean by exactly 0.20.
 a=draw_world(8,'near_census','iid_year',3,SEED,0)
 b=draw_world(8,'near_census','iid_year',3,SEED,.20)
 assert np.max(np.abs((b['year_means']-a['year_means'])-np.r_[np.zeros(4),np.ones(4)*.20]))<1e-10
 tiny,fail=evaluate_scenario(8,'near_census','iid_year',4)
 assert len(tiny)==3 and all(r['evaluable']==4 for r in tiny)
 print('PASS: independent Cholesky GLS, frozen RNG, source weights, beta0 shift, finite covariance, synthetic calibration smoke')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--selftest',action='store_true')
 p.add_argument('--out',type=Path)
 p.add_argument('--replications',type=int,default=R)
 a=p.parse_args()
 if a.selftest:return selftest()
 if a.out is None or a.out.exists() or a.replications!=R:
  raise ValueError('Frozen R=300 preregistration and non-existing output dir required')
 a.out.mkdir(parents=True)
 rows=[];fails=[]
 for T in TVALUES:
  for mask in MASKS:
   for world in WORLDS:
    block,failed=evaluate_scenario(T,mask,world,R)
    rows+=block
    fails += [{'years':T,'source_mask':mask,'year_world':world,**x} for x in failed]
    print('DONE',T,mask,world,'evaluable',[x['evaluable'] for x in block],
       'coverage',[round(x['coverage'],3) if x['coverage'] else None for x in block],flush=True)
 with (a.out/'synthetic_covariance_calibration.csv').open('x',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 overall={'schema':'un.w4.extended_temporal_covariance.synthetic_calibration.v1',
   'audit_date':'2026-10-13','R_per_scenario':R,'scenarios':18,'panels_attempted':R*18,
   'method_attempts':R*18*3,'failures_recorded':len(fails),
   'seed':SEED,'nominal_coverage':.9,'source_mask_worlds':list(MASKS),'dependence_worlds':list(WORLDS),
   'horizons_years':list(TVALUES),'known_true_beta':TRUE_BETA,'gls_nuisance_estimated_not_oracle':True,
   'criteria':{'min_evaluable':285,'max_coverage_error':.04,'Wilson_interval_must_include_nominal':True,
               'rho_abs_bias_max':.10,'rho_rmse_max':.25,'rho_boundary_rate_max_exclusive':.05,
               'median_width_over_0_8_flagged':True},
   'grid':grid_identity(),
   'passed_methods_by_world':{world:{name:sum(x['passes_synthetic_DGP_calibration'] for x in rows
      if x['year_world']==world and x['method']==name) for name in
       ('year_welch','estimated_AR1_REML','covariance_family_envelope')} for world in WORLDS},
   'rho_point_reliability_pass_scenarios':sum(x['rho_point_reliability_pass'] for x in rows if x['method']=='estimated_AR1_REML'),
   'all_source_data_simulated_only':True,'actual_year_covariance_estimated_from_UN_data':False,
   'actual_inference_eligible':False,'person_identity_verified':False,'publication_eligible':False,
   'reserved_2026_meetings_accessed':0}
 (a.out/'synthetic_covariance_aggregate.json').write_text(json.dumps(overall,indent=2)+'\n')
 (a.out/'failed_simulations.json').write_text(json.dumps(fails,indent=2)+'\n')
 print(json.dumps({k:overall[k] for k in ['scenarios','panels_attempted','failures_recorded','passed_methods_by_world','rho_point_reliability_pass_scenarios','actual_inference_eligible']},indent=2))
if __name__=='__main__':main()
