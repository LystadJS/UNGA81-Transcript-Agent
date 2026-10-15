"""Predeclared development-only paired benchmark, not locked holdout."""
import argparse
import hashlib
import json
import math
import statistics
import time
from collections import Counter
from study import world, seeded
from temporal_ar1 import estimate_ar1
from profile_reml import profile_reml
from hierarchical_reml import fit as hierarchical_fit

SCENARIOS=(('balanced',24,4,False),('heterogeneous',24,4,True),('sparse',16,2,False))
METHODS=(('moment',estimate_ar1),('annual_profile',profile_reml),('hierarchical_profile',hierarchical_fit))
TRUE_RHO=.55

def run(worlds=30,grid=13,master=810081):
    report={}
    for name,years,meetings,misspecified in SCENARIOS:
        outcomes={label:[] for label,_ in METHODS}
        for index in range(worlds):
            rows=world(seeded(master,'hierarchical_compare_'+name,'development',index),
                       years=years,per_year=meetings,misspecified=misspecified)
            for label,fn in METHODS:
                start=time.perf_counter()
                result=fn(rows,grid_points=grid) if label=='hierarchical_profile' else fn(rows)
                elapsed=time.perf_counter()-start
                outcomes[label].append((result,elapsed))
        report[name]={}
        for label,attempts in outcomes.items():
            done=[x for x,_ in attempts if x['ready']]
            rhos=[x['rho'] for x in done]
            complete=[x for x in done if 'ci' in x]
            coverage=sum(x['ci'][0]<=TRUE_RHO<=x['ci'][1] for x in complete)
            failures=Counter(x.get('reason','unknown') for x,_ in attempts if not x['ready'])
            report[name][label]={
                'attempted':len(attempts),'accepted':len(done),'failed':len(attempts)-len(done),
                'failures':dict(sorted(failures.items())),
                'mean_rho':statistics.mean(rhos) if rhos else None,
                'bias':statistics.mean(rhos)-TRUE_RHO if rhos else None,
                'rmse':math.sqrt(sum((v-TRUE_RHO)**2 for v in rhos)/len(rhos)) if rhos else None,
                'interval_complete':len(complete),'interval_cover':coverage,
                'conditional_interval_coverage':coverage/len(complete) if complete else None,
                'elapsed_seconds':sum(t for _,t in attempts),
                'evaluations':sum(x.get('evaluations',0) for x,_ in attempts),
                'profile_grid_failures':sum(x.get('grid_failed',0) for x,_ in attempts),
            }
    return {'schema':'un.null-calibration.hierarchical-development-benchmark.v1',
            'master_seed':master,'worlds_per_scenario':worlds,'grid_points':grid,
            'truth_for_scoring_only':TRUE_RHO, 'synthetic_development_only':True,
            'scientific_ready':False, 'results':report,
            'limitations':['accepted-only recovery and coverage are selection-conditioned',
             'profile likelihood intervals ignore lexical representation and attendance selection',
             'not W1/W2 full-search reference null or PR57 confirmatory budget']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--worlds',type=int,default=30)
    p.add_argument('--grid',type=int,default=13);a=p.parse_args()
    report=run(a.worlds,a.grid)
    data=json.dumps(report,sort_keys=True,indent=2,allow_nan=False)
    print(data)
    print('receipt_sha256',hashlib.sha256(data.encode()).hexdigest())
