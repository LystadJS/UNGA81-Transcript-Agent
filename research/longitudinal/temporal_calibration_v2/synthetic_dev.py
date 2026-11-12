"""Development-only synthetic DGP. No private speech text or real source records."""
from __future__ import annotations
import hashlib
import numpy as np

DEV_NAMESPACE = 'UNGA81-TEMPORAL-V2-DEV-20261015'
BETATRUE=0.20


def seed_for(years,mask,world,rep):
    text=f'{DEV_NAMESPACE}|{years}|{mask}|{world}|{rep}'.encode('ascii')
    return int.from_bytes(hashlib.sha256(text).digest()[:8],'big')


def draw(years,mask,world,rep):
    if years not in (16,24,32) or mask not in ('near_census','stratified_2_of_3') or world not in (
        'iid_MAR','AR1_MAR','AR1_MNAR_audited','AR1_MNAR_no_audit','AR1_nugget_MNAR_audited'):
        raise ValueError('undeclared synthetic experiment scenario')
    rng=np.random.default_rng(seed_for(years,mask,world,rep))
    n=99; m=12
    post=np.r_[np.zeros(years//2),np.ones(years//2)]
    rho=0.0 if world=='iid_MAR' else .65
    gamma=-1.25 if 'MNAR' in world else 0.0
    nugget=.15 if world=='AR1_nugget_MNAR_audited' else 0.0
    shocks=np.empty(years)
    shocks[0]=rng.normal(scale=.20)
    for t in range(1,years):
        shocks[t]=rho*shocks[t-1]+rng.normal(scale=.20*np.sqrt(1-rho**2))
    shocks += rng.normal(scale=nugget,size=years)
    actor=rng.normal(0,.40,n)
    meeting_shocks=rng.normal(0,.12,(years,m))
    meetings=(np.arange(n)[None,:]*5+3*(np.arange(years)[:,None]%3))%m
    baseline=actor[None,:]+shocks[:,None]+meeting_shocks[np.arange(years)[:,None],meetings]
    Y=BETATRUE*post[:,None]+baseline+rng.normal(0,.25,(years,n))
    frame=np.ones((years,n),dtype=bool)
    for t in range(years):frame[t,rng.choice(n,size=2,replace=False)]=False
    source=np.zeros((years,m),dtype=bool)
    if mask=='near_census':source[:]=True
    else:
        for t in range(years):
            for k in range(4): source[t,rng.choice(np.arange(3*k,3*k+3),size=2,replace=False)]=True
    inc=frame&source[np.arange(years)[:,None],meetings]
    pmeet=1.0 if mask=='near_census' else 2/3
    selection_probability=np.full(Y.shape,pmeet)
    rate=1/(1+np.exp(-np.clip(1.20+gamma*(Y-BETATRUE*post[:,None])-.30*post[:,None],-25,25)))
    resp=inc & (rng.random(Y.shape)<rate)
    q=0.0 if world=='AR1_MNAR_no_audit' else .4
    audit=inc & ~resp & (rng.random(Y.shape)<q)
    seen=np.where(resp|audit,Y,np.nan)
    observed={'value':seen,'frame':frame,'included':inc,'responded':resp,'audited':audit,
              'meeting':meetings,'post':post,'inclusion_probability':selection_probability,
              'audit_probability':np.full(Y.shape,q),'audit_independent':True}
    return observed, {'beta':BETATRUE,'rho':rho,'gamma':gamma,'nugget_sd':nugget,'n_years':years,
                      'frame_total':int(frame.sum()),'selected_total':int(inc.sum()),
                      'responded_total':int(resp.sum()),'audited_total':int(audit.sum())}
