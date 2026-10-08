#!/usr/bin/env python3
"""Preregistered synthetic known-truth interval calibration; no UN source text.

R=600, B=199, seed=20261008, beta=.20. Source-availability masks and
country/meeting IDs are private inputs, never serialized to public reports.
Intervals on real diplomatic texts remain WITHHELD regardless of simulations.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.stats import t
R,B,SEED,BETA=600,199,20261008,.20
YEARS=list(range(2016,2024))


def design(grid,official,newly_verified=None):
    with open(grid,newline='',encoding='utf-8') as h:g=list(csv.DictReader(h))
    with open(official,newline='',encoding='utf-8') as h:
        idx={(r['iso3'],int(r['year'])):r for r in csv.DictReader(h)}
    actors=sorted({r['iso3'] for r in g})
    assert len(actors)==99 and len(g)==792
    positions={a:i for i,a in enumerate(actors)}
    verified=set(newly_verified or ())
    old=np.zeros((99,8),np.int8)
    expanded=np.zeros_like(old)
    meetings=np.full((99,8),-1,np.int16)
    mid={}
    for r in g:
        i=positions[r['iso3']];year=int(r['year']);j=YEARS.index(year)
        sym=r.get('original_official_meeting_symbol') or idx[(r['iso3'],year)]['UN_meeting_symbols']
        if sym:
            sym=sym.split(';')[0].strip()
            if sym not in mid:mid[sym]=len(mid)
            meetings[i,j]=mid[sym]
        observed=r['status']=='strong_original_PV_full_speech_correspondence'
        old[i,j]=int(observed)
        expanded[i,j]=int(observed or (r['iso3'],year) in verified)
    for mat in [old,expanded]:
        assert np.all(mat[:,:4].sum(axis=1)>=2) and np.all(mat[:,4:].sum(axis=1)>=2)
        assert np.all(mat.sum(axis=0)>0)
        assert np.all(meetings[mat.astype(bool)]>=0)
    return {'initial_P2_mask':old, 'expanded_PV_mask':expanded},meetings


def wilson(covered,n,z=1.95996398454):
    if not n:return [None,None]
    p=covered/n;zz=z*z;den=1+zz/n
    mid=(p+zz/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+zz/(4*n*n))/den
    return [mid-half,mid+half]


def actor_interval(values,mask):
    a=mask[:,:4].sum(axis=1);b=mask[:,4:].sum(axis=1)
    if (a==0).any() or (b==0).any():return None
    differences=((values[:,4:]*mask[:,4:]).sum(axis=1)/b
      -(values[:,:4]*mask[:,:4]).sum(axis=1)/a)
    se=differences.std(ddof=1)/math.sqrt(len(differences))
    h=t.ppf(.95,len(differences)-1)*se
    return float(differences.mean()-h),float(differences.mean()+h)


def year_interval(values,mask):
    means=(values*mask).sum(axis=0)/mask.sum(axis=0)
    a,b=means[:4],means[4:]
    va=a.var(ddof=1)/4;vb=b.var(ddof=1)/4
    denom=(va*va/3+vb*vb/3)
    if not denom:return None
    dof=(va+vb)**2/denom
    mid=b.mean()-a.mean();h=t.ppf(.95,dof)*math.sqrt(va+vb)
    return float(mid-h),float(mid+h)


def block_bootstrap(values,mask,rng):
    drawn=np.concatenate([rng.integers(0,4,(B,4)),rng.integers(4,8,(B,4))],axis=1)
    w=np.zeros((B,8),dtype=np.int16)
    for j in range(8):w[np.arange(B),drawn[:,j]]+=1
    d0=w[:,:4] @ mask[:,:4].T
    d1=w[:,4:] @ mask[:,4:].T
    good=(d0>0).all(axis=1)&(d1>0).all(axis=1)
    if good.sum()<math.ceil(.9*B):
        return None,int(good.sum()),int(B-good.sum())
    a=(w[:,:4] @ (values[:,:4]*mask[:,:4]).T)[good]/d0[good]
    b=(w[:,4:] @ (values[:,4:]*mask[:,4:]).T)[good]/d1[good]
    delta=(b-a).mean(axis=1)
    return tuple(map(float,np.quantile(delta,[.05,.95]))),int(good.sum()),int(B-good.sum())


def experiment(mask,meeting,world,replications=R):
    rng=np.random.default_rng(SEED+(world=='serial_year')*927)
    unique={int(x) for x in np.unique(meeting) if x>=0}
    assert len(unique)>=10
    stats={m:{'valid':0,'covered':0,'widths':[],'failed':0,'boot_valid':0,'boot_rejected':0}
      for m in ('naive_actor_t','year_welch_t','within_era_year_bootstrap')}
    for _ in range(replications):
        actor=rng.normal(0,.40,size=(99,1))
        if world=='iid_year':year=rng.normal(0,.20,size=(1,8))
        else:
            z=np.empty(8);z[0]=rng.normal(0,.20)
            for j in range(1,8):
                z[j]=.65*z[j-1]+math.sqrt(1-.65**2)*rng.normal(0,.20)
            year=z.reshape(1,8)
        effects=rng.normal(0,.12,size=max(unique)+1)
        meeting_effect=np.zeros((99,8))
        has=meeting>=0
        meeting_effect[has]=effects[meeting[has]]
        noise=rng.normal(0,.25,size=(99,8))
        x=actor+year+meeting_effect+noise+BETA*np.array([0]*4+[1]*4)[None,:]
        intervals={'naive_actor_t':actor_interval(x,mask),
                   'year_welch_t':year_interval(x,mask)}
        intervals['within_era_year_bootstrap'],valid,failed=block_bootstrap(x,mask,rng)
        stats['within_era_year_bootstrap']['boot_valid']+=valid
        stats['within_era_year_bootstrap']['boot_rejected']+=failed
        for method,ci in intervals.items():
            a=stats[method]
            if ci is None:a['failed']+=1;continue
            a['valid']+=1;a['covered']+=int(ci[0]<=BETA<=ci[1])
            a['widths'].append(ci[1]-ci[0])
    out={}
    for method,item in stats.items():
        n=item['valid'];p=item['covered']/n if n else None
        wil=wilson(item['covered'],n)
        out[method]={
          'attempted':replications,'evaluable':n,'withheld':item['failed'],
          'coverage':p,'covered':item['covered'],
          'wilson_95':wil,'mc_standard_error':math.sqrt(p*(1-p)/n) if n else None,
          'median_width':float(np.median(item['widths'])) if n else None,
          'bootstrap_attempts':B*replications if method=='within_era_year_bootstrap' else 0,
          'bootstrap_valid':item['boot_valid'] if method=='within_era_year_bootstrap' else None,
          'bootstrap_rejected':item['boot_rejected'] if method=='within_era_year_bootstrap' else None,
          'calibrated_only_in_declared_synthetic_DGP':bool(n>=570 and p is not None and
            abs(p-.9)<=.04 and wil[0]<=.9<=wil[1])}
    return out


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--private-grid',type=Path)
    parser.add_argument('--private-official-index',type=Path)
    parser.add_argument('--private-promotions',type=Path)
    parser.add_argument('--private-out',type=Path)
    parser.add_argument('--selftest',action='store_true')
    args=parser.parse_args()
    if args.selftest:
        meetings=np.tile(np.arange(8,dtype=np.int16),(99,1))
        mask=np.ones((99,8),dtype=np.int8)
        result=experiment(mask,meetings,'iid_year',8)
        assert result['year_welch_t']['attempted']==8
        assert result['naive_actor_t']['evaluable']==8
        print('PASS synthetic source-calibration shape / known-truth coverage machinery')
        return
    if not args.private_grid or not args.private_official_index or not args.private_out:
        parser.error('Private real source masks, meeting index, output required')
    added=None
    if args.private_promotions:
        added={(v['iso3'],int(v['year']))
          for v in json.loads(args.private_promotions.read_text())['promoted']}
    masks,meeting=design(args.private_grid,args.private_official_index,added)
    output={'schema':'un.w4.preregistered.synthetic-coverage.v1',
      'seed':SEED,'MonteCarlo_R':R,'inner_block_B':B,'true_beta':BETA,
      'nominal':.9,'year_processes':['iid_year','serial_year_AR1_0_65'],
      'selection_mask_is_fixed_from_P2_and_nonrandom':True,
      'calibrated_inference_for_actual_UN_data':False,
      'public_research_eligible':False,'masks':{}}
    for label,mask in masks.items():
        output['masks'][label]={
          'verified_observations':int(mask.sum()),
          'per_year':mask.sum(axis=0).tolist(),
          'results':{world:experiment(mask,meeting,world)
            for world in ('iid_year','serial_year')}}
    args.private_out.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'completed':True,'replications':R,'mask_obs':
      {k:v['verified_observations'] for k,v in output['masks'].items()},
      'release_eligible':False}))


if __name__=='__main__':main()
