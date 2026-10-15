"""Independent synthetic holdout generator; NO dependency on development DGP.

Source meeting assignment, inclusion, Gaussian shocks and response observation
are implemented independently. The test seed namespace is locked separately
before calibration, and the estimator sees only redacted observed outcomes.
"""
from __future__ import annotations
import hashlib
import numpy as np
from scipy.special import expit

def _rng(years,mask,scenario,repetition):
    key=('UNGA81-JOINT-HOLDOUT-20261014::'+str(years)+'::'+mask+'::'+
         scenario+'::'+str(repetition)).encode('utf8')
    return np.random.Generator(np.random.PCG64(
        int.from_bytes(hashlib.sha256(key).digest()[:8],'little')))

def independently_generate(T,mask,scenario,repetition,effect=.20):
    assert T in (16,24,32)
    assert mask in ('near_census','stratified_2_of_3')
    assert scenario in ('iid_MAR','AR1_MAR','AR1_MNAR_audited','AR1_MNAR_no_audit')
    rand=_rng(T,mask,scenario,repetition)
    membership=np.zeros((99,T),dtype=bool)
    meeting_label=np.empty((99,T),dtype=int)
    probabilities=np.ones((99,T))
    for yr in range(T):
        active=np.ones(99,dtype=bool)
        active[rand.permutation(99)[:2]]=False
        meeting_label[:,yr]=((np.arange(99)*7+3*yr+np.arange(99)//11)%12)
        if mask=='stratified_2_of_3':
            sampled=set()
            for quartile in range(4):
                options=list(range(quartile*3,quartile*3+3))
                sampled.update(rand.choice(options,size=2,replace=False).tolist())
            active &= np.array([m in sampled for m in meeting_label[:,yr]])
            probabilities[:,yr].fill(2/3)
        membership[:,yr]=active
    country_offsets=rand.standard_normal((99,1))*.40
    temporal=np.empty(T)
    rho=.0 if scenario=='iid_MAR' else .65
    yearly_white_noise=rand.standard_normal(T)*.20
    temporal[0]=yearly_white_noise[0]
    for yr in range(1,T):
        temporal[yr]=rho*temporal[yr-1]+np.sqrt(1-rho*rho)*yearly_white_noise[yr]
    meeting_noise=rand.standard_normal((12,T))*.12
    word_choice_noise=rand.standard_normal((99,T))*.25
    period=(np.arange(T)>=T//2).astype(float)
    latent=country_offsets+temporal.reshape((1,T))+effect*period.reshape((1,T))
    latent=latent+np.take_along_axis(meeting_noise.T,meeting_label.T,axis=1).T+word_choice_noise
    response_effect=0 if scenario in ('iid_MAR','AR1_MAR') else -1.25
    ordinary_chance=expit(1.20+response_effect*(latent-effect*period[None,:])-.30*period[None,:])
    responded=(rand.random((99,T))<ordinary_chance)&membership
    q=.0 if scenario=='AR1_MNAR_no_audit' else .4
    audited=(rand.random((99,T))<q)&membership&~responded
    reveal=responded|audited
    masked=np.full((99,T),np.nan)
    masked[reveal]=latent[reveal]
    return {
        'observed':{'y':masked,'selected':membership,'meeting_pi':probabilities,
                    'response':responded,'audited':audited,'audit_probability':q,
                    'first_stage_probability_known':True,'mode':'synthetic',
                    'audit_randomized_independently_before_outcome_release':q>0},
        'truth':{'beta':float(effect),'rho':float(rho),'gamma':float(response_effect),
                 'n_source':int(membership.sum()),'n_responding':int(responded.sum()),
                 'n_phase2':int(audited.sum()),'hidden_outcome_count':int(np.isnan(masked).sum())}
    }
