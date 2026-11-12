"""Independent Gaussian annual-mean REML for synthetic-only AR(1) diagnostics."""
import math
import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize_scalar
from collections import defaultdict

def profile_reml(rows, points=21):
    from temporal_ar1 import estimate_ar1
    pre = estimate_ar1(rows)
    if not pre['ready']:
        return {'ready': False, 'reason': pre['reason']}
    meetings = defaultdict(list)
    for row in rows: meetings[(row['year'], row['meeting'])].append(row)
    year_groups = defaultdict(list)
    for (year, meeting), rs in meetings.items():
        year_groups[year].append(sum(r['count'] for r in rs)/sum(r['length'] for r in rs))
    calendar = sorted(year_groups)
    yy=np.array([np.mean(year_groups[y]) for y in calendar])
    noise=np.array([np.var(year_groups[y],ddof=1)/len(year_groups[y]) for y in calendar]);noise=np.maximum(noise,1e-7)
    n=len(yy);gap=np.abs(np.subtract.outer(np.arange(n),np.arange(n)))
    ones=np.ones(n)
    def objective(rho, v):
        cov=v*(rho**gap)+np.diag(noise)
        try:
            L=cho_factor(cov,lower=True,check_finite=False)
            vinv_y=cho_solve(L,yy,check_finite=False)
            vinv_1=cho_solve(L,ones,check_finite=False)
            denom=ones@vinv_1
            if denom<=0:return math.inf
            resid=yy@vinv_y-(ones@vinv_y)**2/denom
            return float(np.log(np.diag(L[0])).sum()*2+np.log(denom)+resid+(n-1)*np.log(2*np.pi))/2
        except (ValueError,np.linalg.LinAlgError):return math.inf
    # Profile nuisance variance for each rho. Multimodal and boundary sensitivity explicit.
    grid=np.linspace(-.85,.85,points)
    prof=[];evals=0
    for rho in grid:
        result=minimize_scalar(lambda logv:objective(float(rho),math.exp(logv)),bounds=(-13,-1),method='bounded',options={'xatol':.018,'maxiter':55})
        evals+=result.nfev
        prof.append((float(rho),float(result.fun),math.exp(result.x)))
    best=min(prof,key=lambda x:x[1]);minimum=best[1]
    # Approximate 95% 1-df profile likelihood region by fixed grid.
    accepted=[v[0] for v in prof if 2*(v[1]-minimum)<=3.841458820694]
    if not accepted or best[0] in (grid[0],grid[-1]):
        return {'ready':False,'reason':'rho_boundary','evaluations':evals,'rho':best[0]}
    if accepted[0]==grid[0] or accepted[-1]==grid[-1]:
        return {'ready':False,'reason':'unbounded_profile_interval','evaluations':evals,'rho':best[0]}
    return {'ready':True,'rho':best[0],'year_variance':best[2], 'ci':[accepted[0],accepted[-1]],'evaluations':evals, 'grid_points':points}
