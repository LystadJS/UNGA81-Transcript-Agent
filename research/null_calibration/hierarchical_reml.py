"""Development-only hierarchical meeting/year Gaussian REML candidate.

Uses observed synthetic meeting prevalences (not generating covariance inputs).
Jointly estimates meeting variance, stationary year variance, and AR(1) rho.
This is a restricted covariance proxy, NOT the source/selection-aware W1/W2 null.
"""
from collections import defaultdict
import math
import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize
from temporal_ar1 import estimate_ar1

VERSION = 'un.null-calibration.hierarchical-reml.v1'


def design(rows, minimum_years=16):
    gate = estimate_ar1(rows, minimum_years=minimum_years)
    if not gate['ready']:
        return {'ready': False, 'reason': gate['reason']}
    buckets = defaultdict(list)
    for r in rows:
        buckets[(r['year'],r['meeting'])].append(r)
    keys = sorted(buckets)
    years = sorted({k[0] for k in keys})
    means=[]; noise=[]
    for key in keys:
        sub=buckets[key]; total=sum(x['length'] for x in sub)
        p=sum(x['count'] for x in sub)/total
        means.append(p)
        noise.append(max(1e-8,p*(1-p)/total))
    return {'ready':True, 'y':np.asarray(means), 'noise':np.asarray(noise),
            'year':np.asarray([k[0]-years[0] for k in keys],dtype=int),
            'years':len(years), 'meetings':len(keys), 'preliminary':gate}


def objective(data, rho, log_variances):
    if not (-.95 < rho < .95):return math.inf
    vm,vy=np.exp(np.asarray(log_variances,dtype=float))
    if not all(np.isfinite([vm,vy])): return math.inf
    y,noise,year=data['y'],data['noise'],data['year']
    gap=np.abs(year[:,None]-year[None,:])
    V=vy*np.power(rho,gap)+np.diag(noise+vm)
    try:
        factor=cho_factor(V,lower=True,check_finite=False)
        ones=np.ones(len(y))
        a=cho_solve(factor,ones,check_finite=False)
        z=cho_solve(factor,y,check_finite=False)
        denom=ones@a
        if denom<=0:return math.inf
        quad=y@z-(ones@z)**2/denom
        ld=2*sum(np.log(np.diag(factor[0])))
        value=.5*(ld+np.log(denom)+quad+(len(y)-1)*np.log(2*np.pi))
        return float(value) if np.isfinite(value) else math.inf
    except (ValueError,np.linalg.LinAlgError,FloatingPointError):
        return math.inf


def fit(rows, grid_points=17, minimum_years=16, maxiter=65):
    data=design(rows,minimum_years=minimum_years)
    if not data['ready']:return data
    if grid_points<7:raise ValueError('too few predeclared grid points')
    grid=np.linspace(-.8,.8,grid_points)
    center=data['preliminary']
    start=[math.log(max(1e-5,center['meeting_sd']**2)),math.log(max(1e-5,center['year_sd']**2))]
    points=[]; evaluations=0
    for rho in grid:
        result=minimize(lambda v:objective(data,float(rho),v),start,method='L-BFGS-B',
                        bounds=[(-14,-1.4),(-14,-1.4)],options={'maxiter':maxiter,'ftol':1e-8})
        evaluations+=result.nfev
        if not result.success or not math.isfinite(result.fun):
            points.append({'rho':float(rho),'status':'failed','reason':str(result.message),'nll':None})
            continue
        points.append({'rho':float(rho),'status':'converged','nll':float(result.fun),
                       'variances':list(np.exp(result.x))})
    valid=[x for x in points if x['status']=='converged']
    base={'evaluations':evaluations,'grid_attempted':grid_points,'grid_converged':len(valid),
          'grid_failed':grid_points-len(valid),'years':data['years'],'meetings':data['meetings'],
          'method':'joint_meeting_year_reml', 'publication_eligible':False}
    if len(valid)!=grid_points:
        return dict(base,ready=False,reason='incomplete_profile',profile=points)
    best=min(valid,key=lambda x:x['nll']); minimum=best['nll']
    accepted=[x['rho'] for x in valid if 2*(x['nll']-minimum)<=3.841458820694]
    if best['rho'] in (grid[0],grid[-1]):
        return dict(base,ready=False,reason='rho_boundary',rho=best['rho'])
    if not accepted or accepted[0]==grid[0] or accepted[-1]==grid[-1]:
        return dict(base,ready=False,reason='unbounded_profile_interval',rho=best['rho'])
    return dict(base,ready=True,rho=best['rho'],ci=[accepted[0],accepted[-1]],
                meeting_variance=best['variances'][0],year_variance=best['variances'][1],
                profile_minimum=minimum,parameter_interval_coverage_certified=False)
