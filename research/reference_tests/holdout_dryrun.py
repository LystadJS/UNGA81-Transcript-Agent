#!/usr/bin/env python3
"""Synthetic-only gate rehearsal for sealed held-out protocol; no real holdout reader exists."""
from __future__ import annotations
import argparse, collections, json, re
from pathlib import Path
import numpy as np
from reference import (HERE, read, verify_seal, digest, canonical, blocks, coverage, country_population,
                       normalized, crossmeeting_knn, agreement, permuted_neighbor_agreement,
                       shuffle_within, same_country, empirical_p, holm)
from encoder import offline

SCHEMA='un.synthetic-heldout-dryrun.v1'
RESULT='un.heldout-dryrun-result.v1'


def verify_frozen_lock() -> dict:
    saved=read(HERE/'evaluation-lock.json')
    verify_seal(saved,'un.heldout-evaluation-lock.v1')
    if saved['holdout_state']!='reserved_not_downloaded' or saved['reserved_meetings']!=37 or saved['evaluation_executed']:
        raise ValueError('Frozen holdout authorization fence broken')
    for field,path in [('reference_plan_sha256',HERE/'plan.json'),('evaluation_plan_sha256',HERE/'evaluation_plan.json')]:
        if saved[field]!=digest(path.read_bytes()):raise ValueError('Frozen plan integrity changed')
    if saved['authorization_required']!='separate_explicit_authorization_to_access_reserved_content':
        raise ValueError('Missing future explicit authorization requirement')
    return saved


def fixture(seed:int=82631, variant:str='nominal') -> dict:
    if variant not in {'nominal','insufficient','all_unavailable','correlated'}:raise ValueError('Unknown synthetic exercise')
    rng=np.random.default_rng(seed)
    meetings=[{'meeting_id':f'SYNTHETIC-MEETING-{i:02d}','date':'1900-01-01',
               'status':'unavailable' if variant=='all_unavailable' or i>=35 else ('failed' if i in (31,32) else 'collected')}
              for i in range(37)]
    rows=[]
    if variant!='all_unavailable':
        for mid,m in enumerate(meetings):
            if m['status']!='collected':continue
            for j in range(4 if variant=='insufficient' else 24):
                country=f'SYNTHETIC-COUNTRY-{j%28:02d}' if j%11!=0 else None
                row={'parent_id':f'SYNTHETIC-PARENT-{mid:02d}-{j:02d}','meeting_id':m['meeting_id'],
                     'role':['delegate','official','journalist'][j%3],'genre':['GA','HRC'][mid%2],
                     'country':country,'length_bin':j%3,'split':'synthetic','source_kind':'synthetic_only'}
                rows.append(row)
    dim=64
    latent=rng.normal(size=(len(rows),dim))
    if variant=='correlated':
        # One shared synthetic nuisance factor; not a claim about diplomatic content.
        sem=normalized(latent+0.04*rng.normal(size=latent.shape))
    else:
        sem=normalized(rng.normal(size=latent.shape))
    lex=normalized(latent)
    return {'schema':SCHEMA,'synthetic':True,'fake_dates_only':True,'input_kind':'generated_nontext_vectors',
            'meetings':meetings,'parents':rows,'lexical':lex,'semantic':sem,'seed':seed,'variant':variant}


def check_fixture(fixture_data:dict,lock:dict):
    if fixture_data.get('schema')!=SCHEMA or fixture_data.get('synthetic') is not True or fixture_data.get('input_kind')!='generated_nontext_vectors':
        raise ValueError('Synthetic-only dry run. Actual transcripts and source data prohibited')
    if set(fixture_data)!={'schema','synthetic','fake_dates_only','input_kind','meetings','parents','lexical','semantic','seed','variant'}:
        raise ValueError('Unexpected key: refuse text, transcript URLs, or external rows')
    meetings=fixture_data['meetings'];rows=fixture_data['parents']
    if len(meetings)!=37 or len({x['meeting_id'] for x in meetings})!=37:
        raise ValueError('Every synthetic meeting must be accounted for exactly once')
    for x in meetings:
        if not re.fullmatch(r'SYNTHETIC-MEETING-\d\d',x['meeting_id']) or x['date']!='1900-01-01' or x['status'] not in {'collected','failed','unavailable'} or set(x)!={'meeting_id','date','status'}:
            raise ValueError('Actual or malformed meeting identity cannot enter the dry run')
    byid={m['meeting_id']:m for m in meetings}
    if len({r['parent_id'] for r in rows})!=len(rows):raise ValueError('Duplicate synthetic parents')
    for r in rows:
        if set(r)!={'parent_id','meeting_id','role','genre','country','length_bin','split','source_kind'} or not r['parent_id'].startswith('SYNTHETIC-PARENT-') or r['split']!='synthetic' or r['source_kind']!='synthetic_only' or r['meeting_id'] not in byid or byid[r['meeting_id']]['status']!='collected' or r['length_bin'] not in [0,1,2]:
            raise ValueError('Non-synthetic or wrongly attributed input row')
    A=np.asarray(fixture_data['lexical']);B=np.asarray(fixture_data['semantic'])
    if A.shape!=B.shape or A.shape!=(len(rows),64) or not np.isfinite(A).all() or not np.isfinite(B).all():
        raise ValueError('Invalid fixed synthetic vector matrix')
    if lock['reserved_meetings']!=len(meetings):raise ValueError('Sealed count changed')


def evaluate_fixture(fixture_data:dict,lock:dict,draws:int=999) -> dict:
    verify_seal(lock,'un.heldout-evaluation-lock.v1');check_fixture(fixture_data,lock)
    if draws!=999:raise ValueError('Frozen 999-reassignment procedure only')
    rows=fixture_data['parents'];meetings=fixture_data['meetings']
    gates=lock['predeclared_eligibility_gates'];k=gates['min_crossmeeting_neighbors']
    available=[m for m in meetings if m['status']=='collected']
    report={'schema':RESULT,'synthetic':True,'state':'dry_run_only_never_real_holdout_evaluation',
      'locked_protocol_sha256':lock['sha256'],'seed':fixture_data['seed'],'variant':fixture_data['variant'],
      'all_meetings':len(meetings),'source_status_counts':dict(collections.Counter(m['status'] for m in meetings)),
      'parents':len(rows),'represented_meetings':len({r['meeting_id'] for r in rows}),
      'source_substitution':False,'model_training':False,'reserved_transcripts_requested':0,'reserved_transcripts_opened':0,
      'human_approval':False,'actual_replication_claim':False}
    reasons=[]
    if len(rows)<gates['min_eligible_parents']:reasons.append('eligible_parent_count_below_gate')
    if report['represented_meetings']<gates['min_distinct_meetings']:reasons.append('represented_meeting_count_below_gate')
    if any(m['status']=='collected' and not any(r['meeting_id']==m['meeting_id'] for r in rows) for m in meetings):
        reasons.append('downloaded_meeting_without_eligible_parents')
    groups=blocks(rows,('meeting_id','length_bin'))
    c=coverage(groups,len(rows));report['strata_coverage']=c
    if c['movable_fraction']<gates['min_movable_fraction']:reasons.append('insufficient_exchangeable_source_units')
    if rows and min(sum(r['meeting_id']!=x['meeting_id'] for r in rows) for x in rows)<k:
        reasons.append('insufficient_cross_meeting_neighbor_pool')
    if reasons:
        return {**report,'decision':'INCONCLUSIVE_SYNTHETIC','withheld_reasons':reasons,'primary':None,'secondary':None}
    A=np.asarray(fixture_data['lexical']);B=np.asarray(fixture_data['semantic'])
    ak=crossmeeting_knn(A,rows,k);bk=crossmeeting_knn(B,rows,k)
    observed=agreement(ak,bk)
    samples=np.empty(draws);rng=np.random.default_rng(read(HERE/'plan.json')['seed'])
    for i in range(draws):samples[i]=permuted_neighbor_agreement(ak,bk,shuffle_within(groups,len(rows),rng))
    excess=float(observed-samples.mean());p=empirical_p(observed,samples)
    primary={'observed':observed,'null_mean':float(samples.mean()),'excess':excess,'nominal_p':p,'replication_floor':lock['replication_floor_excess']}
    ci,cm,ncountries=country_population(rows)
    secondary=None
    if len(cm)>=150 and ncountries>=20 and coverage(blocks(cm,('meeting_id','length_bin')),len(cm))['movable_fraction']>=gates['min_movable_fraction']:
        labels=np.asarray([r['country'] for r in cm]);cb=blocks(cm,('meeting_id','length_bin'));kn=crossmeeting_knn(B[ci],cm,k)
        obs=same_country(kn,labels);null=np.empty(draws);rng=np.random.default_rng(read(HERE/'plan.json')['seed']+1)
        for i in range(draws):null[i]=same_country(kn,labels[shuffle_within(cb,len(cm),rng)])
        secondary={'observed':obs,'null_mean':float(null.mean()),'nominal_p':empirical_p(obs,null),'eligible_country_parents':len(cm),'repeated_countries':ncountries}
    else:
        reasons.append('secondary_country_test_not_assessable')
    if secondary is not None:
        adj=holm([p,secondary['nominal_p']]);primary['holm_p']=adj[0];secondary['holm_p']=adj[1]
    else:primary['holm_p']=min(1.0,2*p) # conservative family-size 2; never reduce multiplicity on missing secondary
    passes=bool(excess>0 and excess>=lock['replication_floor_excess'] and primary['holm_p']<=gates['max_familywise_alpha'])
    return {**report,'decision':'SYNTHETIC_GATE_WOULD_PASS' if passes else 'SYNTHETIC_GATE_WOULD_NOT_PASS',
            'withheld_reasons':reasons,'primary':primary,'secondary':secondary,
            'interpretation':'Simulated geometry only. This output cannot support claims about the 37 reserved meetings.'}



def exercise_frozen_transforms(synthetic:dict,lock:dict,checkpoint:Path,semantic_results:Path) -> dict:
    """Pass data-free synthetic feature counts/embeddings through saved transforms (NO fitting)."""
    from scipy.sparse import csr_matrix
    from reference import digest
    check_fixture(synthetic,lock)
    lexical_path=checkpoint/'final-analysis/strict_lsa64_k10.npz'
    semantic_path=semantic_results/'strict_semantic_pca64_k10.npz'
    if digest(lexical_path.read_bytes())!=lock['saved_lexical_model_sha256'] or digest(semantic_path.read_bytes())!=lock['saved_semantic_pca_model_sha256']:
        raise ValueError('Frozen development transform hashes do not match evaluation lock')
    with np.load(lexical_path,allow_pickle=False) as source:
        lexical={k:source[k].copy() for k in source.files}
    with np.load(semantic_path,allow_pickle=False) as source:
        semantic={k:source[k].copy() for k in source.files}
    if lexical['svd_components'].shape!=(64,len(lexical['idf'])) or semantic['pca_components'].shape!=(64,384) or semantic['centers'].shape!=(10,64):
        raise ValueError('Frozen model feature or centroid schema unexpected')
    rng=np.random.default_rng(int(synthetic['seed']))
    n=len(synthetic['parents'])
    if not n:return {'status':'not_assessable_empty_synthetic_fixture','synthetic':True}
    # Invent feature counts only from the preexisting vocabulary dimension; NO transcript text.
    nnz=12;cols=rng.integers(0,len(lexical['idf']),size=(n,nnz));data=np.ones(n*nnz)
    sparse=csr_matrix((data,(np.repeat(np.arange(n),nnz),cols.ravel())),shape=(n,len(lexical['idf'])))
    sparse=sparse.multiply(lexical['idf']).tocsr()
    from sklearn.preprocessing import normalize as sklearn_normalize
    sparse=sklearn_normalize(sparse)
    l=normalized(np.asarray(sparse@lexical['svd_components'].T))
    raw=rng.normal(size=(n,384))
    s=normalized((raw-semantic['pca_mean'])@semantic['pca_components'].T)
    # The saved semantic centers are used for prediction, never updated or fit.
    predictions=np.argmin(((s[:,None,:]-semantic['centers'][None,:,:])**2).sum(axis=2),axis=1)
    synthetic['lexical']=l;synthetic['semantic']=s
    return {'status':'PASS_SYNTHETIC_TRANSFORM_SMOKE','synthetic':True,'frozen_lexical_features':len(lexical['idf']),
            'lexical_components':l.shape[1],'semantic_input_dimensions':384,'semantic_components':s.shape[1],
            'semantic_predictions':int(len(predictions)),'distinct_semantic_labels':int(len(set(predictions.tolist()))),
            'used_frozen_center_predictions':True,'model_retrained':False,'holdout_opened':0}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('output',type=Path);p.add_argument('--variant',choices=['nominal','correlated','insufficient','all_unavailable'],default='nominal')
    p.add_argument('--exercise-frozen-transforms',nargs=2,metavar=('DEVELOPMENT_CHECKPOINT','SAVED_SEMANTIC_RESULTS'))
    a=p.parse_args()
    if a.output.exists():raise FileExistsError('Choose a new output path')
    with offline() as attempts:
        lock=verify_frozen_lock()
        simulation=fixture(variant=a.variant)
        smoke=exercise_frozen_transforms(simulation,lock,*(Path(x) for x in a.exercise_frozen_transforms)) if a.exercise_frozen_transforms else None
        result=evaluate_fixture(simulation,lock)
        if smoke is not None:result['synthetic_transform_smoke']=smoke
        if attempts:raise RuntimeError('Network access attempted in synthetic-only mode')
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'decision':result['decision'],'synthetic':True,'holdout_opened':0}))

if __name__=='__main__':main()
