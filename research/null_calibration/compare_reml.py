"""Paired synthetic moment versus reduced annual-mean REML recovery comparison."""
import json
import time
import math
import statistics
from collections import Counter
from study import world, seeded
from temporal_ar1 import estimate_ar1
from profile_reml import profile_reml

def run(count=50, years=24, meetings=4, mis=False):
    out={k:{'estimated':[],'covered':0,'ci_complete':0,'failures':Counter(),'runtime':0,'evaluations':0}
         for k in ('moments','profile_reml')}
    for i in range(count):
        rows=world(seeded(810081,'profile_reml_misspecified' if mis else 'profile_reml','development',i),
                   years=years,per_year=meetings,misspecified=mis)
        for name,fn in (('moments',estimate_ar1),('profile_reml',profile_reml)):
            t=time.perf_counter()
            f=fn(rows)
            out[name]['runtime']+=time.perf_counter()-t
            out[name]['evaluations']+=f.get('evaluations',0)
            if not f['ready']:
                out[name]['failures'][f['reason']]+=1
            else:
                out[name]['estimated'].append(f['rho'])
                if 'ci' in f:
                    out[name]['ci_complete']+=1
                    out[name]['covered']+=f['ci'][0]<=.55<=f['ci'][1]
    for name,d in out.items():
        a=d.pop('estimated')
        d['failures']=dict(d['failures'])
        d['attempted']=count
        d['converged']=len(a)
        d['mean_rho']=statistics.mean(a) if a else None
        d['bias']=d['mean_rho']-.55 if a else None
        d['rmse']=math.sqrt(sum((x-.55)**2 for x in a)/len(a)) if a else None
        d['conditional_coverage']=d['covered']/d['ci_complete'] if d['ci_complete'] else None
        d['seconds_per_attempt']=d['runtime']/count
    return {'scenario':{'worlds':count,'years':years,'meetings_per_year':meetings,'misspecified':mis},
            'truth_scoring_only':.55,'methods':out}

if __name__=='__main__':
    for y,m,mis in [(24,4,False),(24,4,True),(16,2,False)]:
        print(json.dumps(run(50,y,m,mis),sort_keys=True))
