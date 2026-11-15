"""Independently coded and seeded holdout synthetic world generator.

This deliberately does not import the development DGP. The same declared
statistical experiment is implemented with independent vector operations,
independent PCG64DXSM streams and a distinct SHA256 seed namespace.
"""
from __future__ import annotations
import hashlib
import numpy as np

HOLDOUT_NAMESPACE = 'UNGA81-TEMPORAL-V2-HOLDOUT-20261015'


def independently_draw(years,mask,world,rep):
    if years not in (16,24,32) or mask not in ('near_census','stratified_2_of_3') or world not in (
        'iid_MAR','AR1_MAR','AR1_MNAR_audited','AR1_MNAR_no_audit','AR1_nugget_MNAR_audited'):
        raise ValueError('undeclared locked holdout scenario')
    payload=f'{HOLDOUT_NAMESPACE}/{world}/{mask}/{years}/{rep}'.encode('ascii')
    seed=int.from_bytes(hashlib.sha256(payload).digest()[:16],'little')
    g=np.random.Generator(np.random.PCG64DXSM(seed))
    beta=.2; correlation=0. if world=='iid_MAR' else .65
    slope=-1.25 if 'MNAR' in world else 0.
    independent_year_sd=.15 if world=='AR1_nugget_MNAR_audited' else 0.
    N=99; T=years
    post=(np.arange(T)>=T//2).astype(float)
    ar=g.standard_normal(T)
    ar[0]*=.20
    for t in range(1,T):ar[t]=correlation*ar[t-1]+.20*np.sqrt(1-correlation**2)*ar[t]
    ar=ar+g.standard_normal(T)*independent_year_sd
    # Affiliation effects are reused across years, not treated as independent speeches.
    actor_effect=.40*g.standard_normal(N)
    meeting_offsets=.12*g.standard_normal((T,12))
    meeting=np.empty((T,N),dtype=np.int64)
    for t in range(T):meeting[t,:]=(5*np.arange(N)+3*(t%3))%12
    y=beta*post[:,None]+actor_effect[None,:]+ar[:,None]+meeting_offsets[
        np.arange(T)[:,None],meeting]+.25*g.standard_normal((T,N))
    in_frame=np.ones((T,N),bool)
    for t in range(T):
        two=g.permutation(N)[:2]
        in_frame[t,two]=False
    source_selected=np.ones((T,12),bool)
    if mask=='stratified_2_of_3':
        for t in range(T):
            source_selected[t,:]=False
            for qtr in range(4):
                choices=g.permutation(3)[:2]+3*qtr
                source_selected[t,choices]=True
    is_sample=in_frame&np.take_along_axis(source_selected,meeting,axis=1)
    p_source=1.0 if mask=='near_census' else 2./3
    logits=1.2+slope*(y-beta*post[:,None])-.30*post[:,None]
    responder=is_sample & (g.uniform(size=(T,N))<1/(1+np.exp(-np.clip(logits,-25,25))))
    audit_p=0.0 if world=='AR1_MNAR_no_audit' else .4
    audit=is_sample & ~responder & (g.uniform(size=(T,N))<audit_p)
    values=np.full((T,N),np.nan)
    values[responder|audit]=y[responder|audit]
    visible=dict(value=values,frame=in_frame,included=is_sample,responded=responder,
                 audited=audit,meeting=meeting,post=post,
                 inclusion_probability=np.full((T,N),p_source),
                 audit_probability=np.full((T,N),audit_p),audit_independent=True)
    check=dict(beta=beta,rho=correlation,gamma=slope,nugget_sd=independent_year_sd,
               n_years=T,frame_total=int(in_frame.sum()),selected_total=int(is_sample.sum()),
               responded_total=int(responder.sum()),audited_total=int(audit.sum()))
    return visible,check
