"""Fresh-development-only integrated latent Markov vs conditional gamma set study.

No connection to v2 or v3 holdout code. Every failed fit is retained exactly.
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

from .v3_integrated_markov import MODEL, NoIdentifiedFit, estimate_integrated_response
from .v3_partial_identification import audited_gamma_confidence_set,population_gamma_identification

NAMESPACE='UNGA81-V3-EXACT-TWO-STATE-AND-CP-NEW-DEV-20261015'
# (name,T,state stay,outcome-state loading,response-state magnitude,
#  randomized independent audit rate,actor dependence,gamma slope change)
SCENARIOS=(
    ('iid_year_states_T16',16,.51,.0,.35,.45,False,False),
    ('correlated_states_T16',16,.82,.65,.80,.45,False,False),
    ('persistent_states_T16',16,.94,.65,.80,.45,False,False),
    ('correlated_states_T32',32,.82,.65,.80,.45,False,False),
    ('weak_audit_T16',16,.82,.65,.80,.025,False,False),
    ('no_audit_T16',16,.82,.65,.80,0.0,False,False),
    ('actor_effect_stress_T16',16,.82,.65,.80,.45,True,False),
    ('changing_gamma_stress_T16',16,.82,.65,.80,.45,False,True),
)
METHODS=('integrated_two_state_year_markov','formal_gamma_set_or_no_fit')
TRUE_GAMMA=-1.25

def seed(label):
    return int.from_bytes(hashlib.sha256((NAMESPACE+'|'+label).encode()).digest()[:8],'big')

def generate(case,rep):
    name,T,stay,kappa,delta,q,actor_stress,gamma_shift=case
    rng=np.random.default_rng(seed('synthetic|'+name+'|'+str(rep)))
    M,A=9,12
    shape=(T,M,A)
    y=np.full(shape,np.nan)
    incl=np.zeros(shape,bool);response=np.zeros(shape,bool);aud=np.zeros(shape,bool)
    risk=np.ones(shape,bool);risk[:2,:,0]=False
    pi=np.full(shape,2/3);audit_q=np.zeros(shape)
    actor=rng.normal(0,.8,A) if actor_stress else np.zeros(A)
    state=int(rng.integers(0,2))
    for t in range(T):
        if t>0 and rng.random()>stay:state=1-state
        z=2*state-1
        # Outcomes are IID across actor-meeting units conditional on year state
        # in the correctly specified synthetic model only.
        py=expit(-.2+kappa*z+actor[None,:])
        y_truth=(rng.random((M,A))<py).astype(float)
        gamma= -.35 if gamma_shift and t>=T//2 else TRUE_GAMMA
        pr=expit(-.4+gamma*y_truth+delta*z)
        selected=np.zeros(M,bool)
        for s in range(3):
            selected[rng.choice(np.arange(3*s,3*s+3),2,replace=False)]=True
        eligible=selected[:,None]&risk[t]
        r=(rng.random((M,A))<pr)&eligible
        a=(rng.random((M,A))<q)&eligible&~r
        incl[t]=eligible;response[t]=r;aud[t]=a
        audit_q[t][eligible&~r]=q
        obs=r|a
        y[t][obs]=y_truth[obs]
    return {
       'model_contract':MODEL,'synthetic_development_only':True,
       'Y_observed':y,'included':incl,'responded':response,'audited':aud,
       'at_risk':risk,'inclusion_probability':pi,'audit_probability':audit_q,
       'independent_randomized_outcome_audit':q>0,
       'original_meeting_selection_ignorable':True,
       'conditionally_iid_within_year':not actor_stress,
       'observed_outcome_type':'binary_synthetic_not_semantic_speech',
       'design_id':'fictional_two_of_three_meeting_probability_sampling',
    },{
       'true_gamma':None if gamma_shift else TRUE_GAMMA,
       'true_stay':stay,'true_outcome_loading':kappa,
       'true_response_state_magnitude':delta,
       'actor_dependence':actor_stress,'gamma_changed':gamma_shift,
    }

def run_development(repetitions=6):
    if type(repetitions) is not int or not 4<=repetitions<=18:
        raise ValueError('new development-only repetition limit 4..18')
    failures=[];out=[]
    for case in SCENARIOS:
        name,T,stay,kappa,delta,q,actor_stress,gamma_changed=case
        complete=defaultdict(list);err={m:Counter() for m in METHODS}
        for rep in range(repetitions):
            observed,evaluator=generate(case,rep)
            for method in METHODS:
                try:
                    if method=='integrated_two_state_year_markov':
                        fit=estimate_integrated_response(observed,maxiter=110)
                        entry={'gamma':fit['conditional_gamma_hat'],
                              'hit':None,'width':None,
                              'rho':2*fit['year_stay_probability_hat']-1,
                              'weak':fit['weakly_identified_year_nuisance'],
                              'nuisance_boundaries':fit['nuisance_boundary_parameters']}
                    elif method=='formal_gamma_set_or_no_fit':
                        if q==0:
                            # Unrestricted nonresponse outcome composition is
                            # nonidentifiable even with known respondent moments.
                            bound=population_gamma_identification(np.full(T,.7))
                            if bound['status']!='NO_FIT_UNRESTRICTED_MNAR':
                                raise RuntimeError('unaudited MNAR must be unidentified')
                            raise NoIdentifiedFit('NO_FIT_UNRESTRICTED_MNAR')
                        fit=audited_gamma_confidence_set(observed)
                        if not fit['status'].startswith('SYNTHETIC_CONDITIONAL_'):
                            raise NoIdentifiedFit('gamma partial confidence set refused: '+fit['status'])
                        truth=evaluator['true_gamma']
                        entry={'gamma':None,'rho':None,'weak':None,
                          'width':fit['gamma_width'],
                          'hit':fit['gamma_lower']<=truth<=fit['gamma_upper'] if truth is not None else None,
                          'nuisance_boundaries':None}
                    complete[method].append(entry)
                except (NoIdentifiedFit,ValueError,ArithmeticError,np.linalg.LinAlgError) as e:
                    reason=type(e).__name__+':'+str(e)
                    failures.append({'study':'integrated_vs_partial','scenario':name,
                         'replicate':rep,'method':method,'reason':reason,
                         'expected_refusal':q<=.025 or actor_stress})
                    err[method][reason]+=1
        for method in METHODS:
            fits=complete[method];refused=sum(err[method].values())
            assert len(fits)+refused==repetitions
            nums=[x['gamma'] for x in fits if x['gamma'] is not None]
            hits=[x['hit'] for x in fits if x['hit'] is not None]
            widths=[x['width'] for x in fits if x['width'] is not None]
            rhos=[x['rho'] for x in fits if x['rho'] is not None]
            out.append({'scenario':name,'T':T,'method':method,
                'attempted':repetitions,'completed':len(fits),'refused':refused,
                'failure_reasons':dict(sorted(err[method].items())),
                'gamma_bias_completed':float(np.mean(np.array(nums)-TRUE_GAMMA)) if nums and not gamma_changed else None,
                'gamma_rmse_completed':float(np.sqrt(np.mean((np.array(nums)-TRUE_GAMMA)**2))) if nums and not gamma_changed else None,
                'partial_gamma_hit_completed':float(np.mean(hits)) if hits else None,
                'median_gamma_set_width':float(np.median(widths)) if widths else None,
                'estimated_markov_rho_median':float(np.median(rhos)) if rhos else None,
                'weak_nuisance_rate':float(np.mean([x['weak'] for x in fits])) if method==METHODS[0] and fits else None,
                'bootstrap_or_Fisher_information_interval_approved':False,
                'empirical_source_fit_authorized':False})
    attempted=len(SCENARIOS)*len(METHODS)*repetitions
    result={'schema':'un.w4.v3.integrated-vs-partial.development.v1',
      'stage':'INDEPENDENT_NEW_SYNTHETIC_DEVELOPMENT_ONLY',
      'seed_namespace':NAMESPACE,'repetitions_per_scenario':repetitions,
      'attempted_method_fits':attempted,'completed_method_fits':attempted-len(failures),
      'refused_method_fits':len(failures),'failure_ledger_count':len(failures),
      'scenarios':out,'v3_holdout_attempted':0,'original_source_bytes_read':0,
      'v2_frozen_thresholds_modified':False,'statistical_freeze_accepted':False,
      'historical_fit_authorized':False}
    return result,failures

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--phase',required=True,choices=('development','holdout','real'))
    ap.add_argument('--repetitions',type=int,default=6)
    ap.add_argument('--out',required=True,type=Path)
    a=ap.parse_args()
    if a.phase!='development':ap.error('v3 holdout/real execution explicitly prohibited')
    if a.out.exists():ap.error('refusing to overwrite source-safe development receipt')
    summary,ledger=run_development(a.repetitions)
    a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'development_aggregate.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    (a.out/'failed_fits.json').write_text(json.dumps(ledger,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'attempted':summary['attempted_method_fits'],
           'completed':summary['completed_method_fits'],
           'refused':summary['refused_method_fits'],
           'holdout_attempted':0},sort_keys=True))
if __name__=='__main__':main()
