"""Observed-variance temporal covariance estimation for year-level discourse contrasts.

Research only. Requires source-verified annual outcome arrays supplied privately,
never reads private UN transcripts, never returns policy positions or a release gate.
Covariance family Sigma=sigma²[(1-lambda) AR1(rho) + lambda diag(99/n_eff)].
Both rho and lambda are estimated via grid-profile REML; sigma² is *estimated*
from the observed restricted quadratic. A separate grid envelope is a
conservatism diagnostic, NOT a generally proven source-selection-valid CI.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
import math
import numpy as np
from scipy.stats import t as student_t

RHO_GRID=(-.15,0.,.15,.30,.45,.60,.65,.75,.85,.90)
NUGGET_GRID=(0.,.10,.25,.50,.75,1.)
GRID=((rho,lam) for rho in RHO_GRID for lam in NUGGET_GRID)
EPS=1e-12

@dataclass(frozen=True)
class Interval:
    lower: float
    upper: float
    beta: float
    width: float
    status: str="descriptive_synthetic_only"


def covariance_shape(T:int, rho:float, nugget:float, effective):
    if not (8<=T<=24 and T%2==0 and -.95<rho<.95 and 0<=nugget<=1):
        raise ValueError("Unapproved year horizon/covariance")
    e=np.asarray(effective,dtype=float)
    if e.shape!=(T,) or not np.all(np.isfinite(e)) or np.any(e<=0) or np.any(e>99+1e-7):
        raise ValueError("Invalid year-effective source sample sizes")
    ar=rho**np.abs(np.subtract.outer(np.arange(T),np.arange(T)))
    return (1-nugget)*ar+nugget*np.diag(99/np.maximum(1.,e))


def annual_gls(y, effective, rho, nugget):
    """Independent exact GLS algebra for a candidate *fixed* covariance shape."""
    y=np.asarray(y,float)
    T=len(y)
    C=covariance_shape(T,rho,nugget,effective)
    X=np.column_stack([np.ones(T),np.r_[np.zeros(T//2),np.ones(T//2)]])
    Vi=np.linalg.inv(C)
    Xi=X.T@Vi
    information=Xi@X
    S=np.linalg.inv(information)
    coeff=S@Xi@y
    resid=y-X@coeff
    sse=float(resid@Vi@resid)
    sigma2=max(EPS,sse/(T-2))
    var=sigma2*S[1,1]
    ld_c=np.linalg.slogdet(C)
    ld_info=np.linalg.slogdet(information)
    if ld_c[0]<=0 or ld_info[0]<=0 or not np.isfinite(sse):
        raise ValueError("Non-positive temporal covariance or information")
    reml=float(ld_c[1]+ld_info[1]+(T-2)*np.log(sigma2))
    return {'beta':float(coeff[1]),'scale2':sigma2,
            'variance_beta':float(var),'reml':reml,
            'rho':float(rho),'nugget':float(nugget)}


@lru_cache(maxsize=4096)
def _cache_matrices(T,effective_tuple):
    e=np.array(effective_tuple,float)
    X=np.column_stack([np.ones(T),np.r_[np.zeros(T//2),np.ones(T//2)]])
    result=[]
    for rho in RHO_GRID:
      for lam in NUGGET_GRID:
        V=covariance_shape(T,rho,lam,e)
        Vi=np.linalg.inv(V)
        U=Vi@X
        S=np.linalg.inv(X.T@U)
        B=S@U.T
        P=Vi-U@S@U.T
        ld=np.linalg.slogdet(V)[1]+np.linalg.slogdet(X.T@U)[1]
        result.append((rho,lam,B[1],P,S[1,1],ld))
    return (np.array([(v[0],v[1]) for v in result]),
            np.array([v[2] for v in result]),
            np.array([v[3] for v in result]),
            np.array([v[4] for v in result]),
            np.array([v[5] for v in result]))


def fit_year_covariance(year_means, effective_n):
    y=np.asarray(year_means,dtype=float)
    n=np.asarray(effective_n,dtype=float)
    T=len(y)
    if T not in (8,16,24) or n.shape!=(T,) or not np.all(np.isfinite(y)):
        raise ValueError("Bad year aggregation or undeclared horizon")
    if np.any(n<2) or np.any(n>99+1e-7):raise ValueError("Unverifiable source-year denominator")
    # Actual observed effective counts, cache rounded to 10 significant decimals,
    # preserving the declared inverse-inclusion weighting without inventing dates.
    key=tuple(np.round(n,10).tolist())
    pairs,B,P,scales,ld=_cache_matrices(T,key)
    betas=B@y
    sse=np.einsum('i,kij,j->k',y,P,y,optimize=True)
    s2=np.maximum(EPS,sse/(T-2))
    loss=ld+(T-2)*np.log(s2)
    vbeta=np.maximum(EPS,s2*scales)
    j=int(np.argmin(loss))
    quantile_est=student_t.ppf(.95,T-3)
    quantile_envelope=student_t.ppf(.95,T-2)
    estimated=Interval(float(betas[j]-quantile_est*math.sqrt(vbeta[j])),
                       float(betas[j]+quantile_est*math.sqrt(vbeta[j])),
                       float(betas[j]),float(2*quantile_est*math.sqrt(vbeta[j])))
    lowers=betas-quantile_envelope*np.sqrt(vbeta)
    uppers=betas+quantile_envelope*np.sqrt(vbeta)
    env=Interval(float(np.min(lowers)),float(np.max(uppers)),
                 float(betas[j]),float(np.max(uppers)-np.min(lowers)))
    return {'fit_rho':float(pairs[j,0]),'fit_nugget':float(pairs[j,1]),
            'fit_sigma2':float(s2[j]),'reml_objective':float(loss[j]),
            'rho_at_boundary':bool(j//len(NUGGET_GRID) in (0,len(RHO_GRID)-1)),
            'nugget_at_boundary':bool(j%len(NUGGET_GRID) in (0,len(NUGGET_GRID)-1)),
            'estimated_interval':estimated,'covariance_grid_envelope':env,
            'all_parameters_estimated_not_oracle':True,
            'population_time_blocks':T,'year_effective_n_min':float(n.min())}


def welch_years(year_means):
    y=np.asarray(year_means,dtype=float)
    T=len(y); a,b=y[:T//2],y[T//2:]
    if T not in (8,16,24) or not np.all(np.isfinite(y)):
        raise ValueError("Welch year block needs 8/16/24 valid chronological years")
    s1=float(a.var(ddof=1)/len(a));s2=float(b.var(ddof=1)/len(b))
    s=s1+s2
    if s<=1e-14:raise ValueError("Nonidentifiable year-variance contrast")
    df=s*s/(s1*s1/(len(a)-1)+s2*s2/(len(b)-1)) if s1>0 or s2>0 else 1
    beta=float(b.mean()-a.mean());half=student_t.ppf(.95,df)*math.sqrt(s)
    return Interval(beta-half,beta+half,beta,2*half)


def interval_contains(ci,true_beta):
    return bool(ci.lower<=true_beta<=ci.upper)


def grid_identity():
    return {'rho_grid':list(RHO_GRID),'nugget_grid':list(NUGGET_GRID),
            'number_shapes':len(RHO_GRID)*len(NUGGET_GRID),
            'temporal_nuisance_estimation':'grid_profile_REML',
            'reference_years_are_not_independent_speeches':True,
            'publication_eligible':False}
