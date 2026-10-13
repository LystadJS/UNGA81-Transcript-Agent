"""Frozen synthetic development DGP; strictly separate from independent holdout.

No real UN source text, speaker IDs or historical features. Hidden Y is masked
before any estimator call; true beta/gamma/rho only returned to calibration driver.
"""
from __future__ import annotations
import hashlib
import numpy as np
from scipy.special import expit

SD_COUNTRY=.40
SD_YEAR=.20
SD_MEETING=.12
SD_SPEECH=.25
TRUE_BETA=.20
N_COUNTRY=99
N_MEETINGS=12
Q_AUDIT=.40
GAMMA_MNAR=-1.25

def _seed(T,design,world,rep):
    source=f'UNGA81-JOINT-DEV-20261013|{T}|{design}|{world}|{rep}'
    return int.from_bytes(hashlib.sha256(source.encode()).digest()[:8],'big')


def generate(T,design,world,rep,beta=TRUE_BETA):
    if T not in (16,24,32) or design not in ('near_census','stratified_2_of_3') or world not in (
        'iid_MAR','AR1_MAR','AR1_MNAR_audited','AR1_MNAR_no_audit'):
        raise ValueError('Not a preregistered synthetic world')
    rng=np.random.default_rng(_seed(T,design,world,rep))
    actors=np.arange(N_COUNTRY)[:,None]
    years=np.arange(T)[None,:]
    group=((7*actors+3*years+actors//11)%N_MEETINGS).astype(int)
    chosen=np.ones((N_COUNTRY,T),dtype=bool)
    pi=np.ones((N_COUNTRY,T),dtype=float)
    for yr in range(T):
        dropped=rng.choice(N_COUNTRY,size=2,replace=False)
        chosen[dropped,yr]=False
        if design=='stratified_2_of_3':
            valid=[]
            for q in range(4):
                valid.extend(rng.choice(np.arange(q*3,(q+1)*3),2,replace=False).tolist())
            chosen[:,yr]&=np.isin(group[:,yr],valid)
            pi[:,yr]=2/3
    country=rng.normal(0,SD_COUNTRY,(N_COUNTRY,1))
    innovation=rng.normal(0,SD_YEAR,T)
    true_rho=0 if world=='iid_MAR' else .65
    time=np.empty(T)
    time[0]=innovation[0]
    for yr in range(1,T):
        time[yr]=true_rho*time[yr-1]+np.sqrt(1-true_rho**2)*innovation[yr]
    meeting_shock=rng.normal(0,SD_MEETING,(N_MEETINGS,T))
    noise=rng.normal(0,SD_SPEECH,(N_COUNTRY,T))
    post=np.r_[np.zeros(T//2),np.ones(T//2)]
    full=(beta*post[None,:]+country+time[None,:]+meeting_shock[group,years]+noise)
    gamma=GAMMA_MNAR if 'MNAR' in world else 0.
    score=1.20 + gamma*(full-beta*post[None,:])-.30*post[None,:]
    response=(rng.uniform(size=full.shape)<expit(score))&chosen
    q=0. if world=='AR1_MNAR_no_audit' else Q_AUDIT
    audit=(rng.uniform(size=full.shape)<q)&chosen&~response
    observed=chosen&(response|audit)
    y=np.full_like(full,np.nan)
    y[observed]=full[observed]
    frame={'y':y,'selected':chosen,'meeting_pi':pi,'response':response,
           'audited':audit,'audit_probability':q,
           'first_stage_probability_known':True,
           'audit_randomized_independently_before_outcome_release':q>0,
           'mode':'synthetic'}
    truth={'beta':float(beta),'rho':float(true_rho),'gamma':float(gamma),
           'selected':int(chosen.sum()),'ordinary_responded':int(response.sum()),
           'audited_nonresponse':int(audit.sum()),
           'N_unavailable_to_estimator':int(np.isnan(y).sum()),'years':T}
    return frame,truth
