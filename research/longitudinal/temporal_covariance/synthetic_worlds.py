"""Independent synthetic historical meeting/year/actor generator.

No original UN document is loaded; meeting identifiers are integers, years are
relative T slots. Missingness and source probabilities follow preregistration.
"""
from __future__ import annotations
import hashlib
import numpy as np

N_ACTORS=99
MEETINGS_PER_YEAR=12
ACTOR_SD=.40
YEAR_SD=.20
MEETING_SD=.12
SPEECH_SD=.25
TRUE_BETA=.20


def fixed_seed(*items):
    b='|'.join(str(x) for x in items).encode()
    return int.from_bytes(hashlib.sha256(b).digest()[:8],byteorder='big')%2**32


def source_mask(T,mask,seed):
    if T not in (8,16,24) or mask not in ('near_census','two_stage'):
        raise ValueError("Invalid preregistered horizon or sampling design")
    rng=np.random.default_rng(fixed_seed('PV_sampling_design',seed,T,mask))
    meeting=np.fromfunction(lambda i,t:(7*i+3*t+(i//11))%12,
                            (N_ACTORS,T),dtype=int).astype(int)
    p=np.ones((N_ACTORS,T))
    selected=np.ones_like(p,dtype=bool)
    for t in range(T):
        # For near-census late-epoch panels, two fixed outcome-independent
        # missing actors per annual frame (not speech absences).
        dropped=rng.choice(N_ACTORS,size=2,replace=False)
        selected[dropped,t]=False
        if mask=='two_stage' and t<T//2:
            official=[]
            for q in range(4):
                official.extend(rng.choice(np.arange(q*3,(q+1)*3),
                                           size=2,replace=False).tolist())
            selected[:,t] &= np.isin(meeting[:,t],official)
            p[:,t]=2/3
        # p is the known meeting-stage inclusion probability, NOT the
        # unknown final source/response probability under MNAR.
    return meeting,p,selected


def draw_world(T,mask,world,replicate,master_seed=20261013,beta=TRUE_BETA):
    if world not in ('iid_year','serial_year','informative_selection'):
        raise ValueError("Unknown synthetic year-process/selection world")
    if not isinstance(replicate,int) or replicate<0:
        raise ValueError("Replicate index must be a nonnegative integer")
    rng=np.random.default_rng(fixed_seed('synthetic_independent_generator',
        master_seed,T,mask,world,replicate))
    meetings,p,include=source_mask(T,mask,master_seed)
    a=rng.normal(0,ACTOR_SD,(N_ACTORS,1))
    innovations=rng.normal(0,YEAR_SD,T)
    if world=='iid_year':
        u=innovations
    else:
        rho=.65
        u=np.empty(T);u[0]=innovations[0]
        for t in range(1,T):
            u[t]=rho*u[t-1]+np.sqrt(1-rho*rho)*innovations[t]
    m=rng.normal(0,MEETING_SD,(MEETINGS_PER_YEAR,T))
    e=rng.normal(0,SPEECH_SD,(N_ACTORS,T))
    post=np.r_[np.zeros(T//2),np.ones(T//2)]
    y=a+u[None,:]+m[meetings,np.arange(T)[None,:]]+e+beta*post[None,:]
    if world=='informative_selection':
        # Nonignorable second-stage text availability, unknown to estimator.
        # Probability explicitly depends on realized *outcome*, so first-stage
        # PV sampling weights alone cannot remove selective transcript loss.
        prob=1/(1+np.exp(-(1.65-1.35*y)))
        include &= rng.uniform(size=y.shape)<prob
    z=[];neff=[];source_response=[]
    for t in range(T):
        loc=include[:,t]
        if not np.any(loc):
            raise ValueError("No selected official sources for source-year")
        w=1/p[loc,t]
        z.append(float(np.dot(w,y[loc,t])/w.sum()))
        neff.append(float(w.sum()**2/np.dot(w,w)))
        source_response.append(int(loc.sum()))
    return {'year_means':np.asarray(z,dtype=float),
            'n_eff':np.asarray(neff,dtype=float),
            'accepted_per_year':source_response,
            'first_stage_inclusion':p,'final_include':include,
            'true_beta':float(beta),
            'true_rho':0 if world=='iid_year' else .65,
            'sampling_design':mask,'year_world':world,
            'informative_second_stage':world=='informative_selection',
            'true_covariance_not_given_to_estimator':True}
