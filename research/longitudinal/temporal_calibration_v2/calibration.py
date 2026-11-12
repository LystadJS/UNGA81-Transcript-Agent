"""Compatibility and standalone numerical sanity helpers (synthetic-only).

The primary registered simulation is inference.py + run_study.py. This module
preserves the initial PR #68 API for existing synthetic regression tests.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class Design:
    years: int
    rho: float
    nugget: float
    audit_probability: float
    response_slope: float = 0.0


def validate(d):
    if d.years < 8 or not (-.95 < d.rho < .95) or d.nugget < 0:
        raise ValueError('invalid temporal design')
    if not 0 <= d.audit_probability <= 1:
        raise ValueError('invalid independent audit probability')


def covariance(t, rho, nugget, scale=1.):
    if t < 2 or not (-.95 < rho < .95) or nugget < 0 or scale <= 0:
        raise ValueError('invalid synthetic covariance')
    lag=np.abs(np.subtract.outer(np.arange(t),np.arange(t)))
    return scale*(rho**lag+nugget*np.eye(t))


def generate(d,seed,meetings=8,speeches=12):
    """Return only visible outcomes; hidden true values remain inaccessible."""
    validate(d)
    rng=np.random.default_rng(seed)
    shocks=rng.multivariate_normal(np.zeros(d.years),covariance(d.years,d.rho,d.nugget))
    result=[]
    for year in range(d.years):
        for meeting in range(meetings):
            included=bool(rng.random()<.5)
            m=rng.normal(scale=.35)
            for speech in range(speeches):
                latent=shocks[year]+m+rng.normal()
                p=1/(1+np.exp(-np.clip(-.4+d.response_slope*latent,-30,30)))
                responded=included and bool(rng.random()<p)
                audited=included and not responded and bool(rng.random()<d.audit_probability)
                result.append({'year':year,'meeting':meeting,'speech':speech,
                     'inclusion_probability':.5,'included':included,
                     'responded':responded,'audited':audited,
                     'audit_probability':d.audit_probability,
                     'outcome':float(latent) if (responded or audited) else None})
    return result


def identifiable(rows):
    if not rows or any(r['inclusion_probability']<=0 for r in rows):
        return False,'missing original meeting positivity'
    missing=[r for r in rows if r['included'] and not r['responded']]
    if any(r.get('audit_probability',0)<=0 for r in missing):
        return False,'outcome-dependent response unidentified without independent audit'
    if missing and not any(r['audited'] for r in missing):
        return False,'no audited missing outcome support'
    return True,'synthetic-only second-phase audit; empirical verification required'


def estimate_year_covariance(annual,ridge=.1):
    """Uncalibrated ratio-of-lags *diagnostic*, not the registered v2 estimator."""
    x=np.asarray(annual,float)
    if x.ndim!=1 or len(x)<24 or not np.all(np.isfinite(x)):
        raise ValueError('insufficient independent calendar years for covariance recovery')
    z=x-x.mean();v=float(np.mean(z*z))
    if v<1e-10:raise ValueError('degenerate annual variance')
    lag1=float(np.mean(z[1:]*z[:-1]));lag2=float(np.mean(z[2:]*z[:-2]))
    if lag1<=0 or lag2<=0:raise ValueError('AR1 and year nugget not separately identified by moments')
    rho=float(np.clip(lag2/lag1,.01,.9)); ar_scale=lag1/rho
    return {'rho':(1-ridge)*rho,'nugget':max(0.,v/max(ar_scale,1e-10)-1),
            'scale':ar_scale,'candidate_calibrated':False}


def metadata_compatible(a,b):
    fields=('schema_version','source_design_id','population_hash',
            'representation_fingerprint','year_definition','sampling_frame_hash')
    if not all(isinstance(x.get(k),str) and x[k] for x in (a,b) for k in fields):
        raise ValueError('incomplete source-comparability metadata')
    if any(a[k]!=b[k] for k in fields):
        raise ValueError('incompatible source cohorts; pooling refused')
    return True  # Metadata equality only; NOT empirical fit/source authentication.


def real_fit(*_args,**_kwargs):
    raise PermissionError('Real historical inference is unconditionally prohibited')
