#!/usr/bin/env python3
"""Versioned development-only dependency sensitivity. No holdout reader, fit, or stance claim."""
from __future__ import annotations
import argparse, collections, hashlib, json, re, sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'semantic_review'))
from encoder import offline
from compare import load_checkpoint, load_lexical
from reference import parents, verify_saved_results
from holdout_dryrun import verify_frozen_lock
PLAN={
 'schema':'un.dependency-controls-plan.v1','k':15,'development_only':True,'holdout_access':False,
 'series':'Recorded GA committee/body, HRC session, treaty/briefing path; asset events unknown. Institutional series is an agenda proxy, NOT an agenda item.',
 'speaker':'Only explicit speaker.id is an observed identifier. Affiliation+function is a coarse separate proxy and requires BOTH fields. Unknown is never a shared identity.',
 'formula':'Three prespecified procedural phrases only; substantive human rights/technical assistance phrases are NOT called boilerplate.',
 'scenarios':['baseline','different_series','different_speaker_proxy','different_series_and_proxy','different_procedural_formula','cap_two_neighbors_per_meeting'],
 'coverage':'Report eligible queries/pairs, same-query baseline, equal-meeting means, and missing control metadata. No restricted-cohort rate compared to full-cohort rate as a causal effect.',
 'inference':'Descriptive sensitivity only. No p-value, speaker-independent performance, or calibrated political-null claim.'}
PHRASES=('thank you','on behalf of','distinguished delegates')
def clean(value):
    value=' '.join(str(value or '').casefold().split())
    return None if value in {'','unknown','none','n/a','not available'} else value

def series(mid,body=None):
    parts=mid.split('/')
    if parts[0]=='ga':
        return 'ga:'+parts[1] if len(parts)>1 and re.fullmatch(r'c\d+',parts[1]) else 'ga:plenary'
    if parts[0]=='hrc' and len(parts)>1:return 'hrc:'+parts[1]
    if parts[0]=='briefing' and len(parts)>1:return ':'.join(parts[:2])
    if parts[0]=='asset':return None
    return 'body:'+clean(body) if clean(body) else None

def enrich(meta,corpus,rows):
    src={p['id']:p for p in corpus['parents']};texts=collections.defaultdict(list)
    for r in rows:texts[r['parent_id']].append(r['text'])
    output=[]
    for r in meta:
        p=src[r['parent_id']];sp=p.get('speaker_metadata') or {}
        aff=clean(sp.get('affiliation_full') or sp.get('affiliation'));fn=clean(sp.get('function'))
        text=' '.join(texts[r['parent_id']]).casefold()
        output.append({**r,'series':series(r['meeting_id'],p.get('body')),
            'speaker_id':clean(sp.get('id')),
            'speaker_proxy':json.dumps([aff,fn],ensure_ascii=False) if aff and fn else None,
            'formula':tuple(i for i,phrase in enumerate(PHRASES) if phrase in text)})
    return output

def neighbors(V,meta,scenario='baseline',k=15):
    """Exact cosine retrieval, stable-ID tie breaks; never backfill excluded candidates."""
    if scenario not in PLAN['scenarios'] or len({r['parent_id'] for r in meta})!=len(meta):raise ValueError('Scenario or duplicate identity')
    V=np.asarray(V,dtype=float)
    if V.ndim!=2 or len(V)!=len(meta) or not np.isfinite(V).all() or k<1:raise ValueError('Invalid geometry')
    norms=np.linalg.norm(V,axis=1)
    if np.any(norms<=0):raise ValueError('Zero vectors require explicit abstention before retrieval')
    sim=(V/norms[:,None])@(V/norms[:,None]).T
    all_nn={};pool={};unknown_queries=0
    for i,r in enumerate(meta):
        required=[]
        if scenario in {'different_series','different_series_and_proxy'}:required.append('series')
        if scenario in {'different_speaker_proxy','different_series_and_proxy'}:required.append('speaker_proxy')
        if any(r.get(key) is None for key in required):unknown_queries+=1;pool[i]=0;continue
        eligible=[]
        for j,s in enumerate(meta):
            if r['meeting_id']==s['meeting_id']:continue
            if any(s.get(key) is None or r[key]==s[key] for key in required):continue
            if scenario=='different_procedural_formula' and set(r['formula'])&set(s['formula']):continue
            eligible.append(j)
        pool[i]=len(eligible)
        ranked=sorted(eligible,key=lambda j:(-sim[i,j],meta[j]['parent_id']))
        selected=[];counts=collections.Counter()
        for j in ranked:
            mid=meta[j]['meeting_id']
            if scenario=='cap_two_neighbors_per_meeting' and counts[mid]>=2:continue
            selected.append(j);counts[mid]+=1
            if len(selected)==k:break
        if len(selected)==k:all_nn[i]=selected
    return all_nn,{'queries':len(all_nn),'total':len(meta),'pairs':len(all_nn)*k,
        'unknown_control_queries':unknown_queries,'insufficient_queries':len(meta)-len(all_nn)-unknown_queries,
        'min_unconstrained_candidate_pool':min(pool.values(),default=0),
        'assessable_pool_min':min((pool[i] for i in all_nn),default=None),
        'assessable_pool_median':float(np.median([pool[i] for i in all_nn])) if all_nn else None,
        'uniform_overlap_expected':float(np.mean([k/pool[i] for i in all_nn])) if all_nn and scenario!='cap_two_neighbors_per_meeting' else None,
        'uniform_reference_note':'Independent uniform k-subsets from each eligible pool; descriptive geometry baseline, not a political null. Not computed for meeting-cap selection.'}

def overlap(A,B,queries,k):
    return float(np.mean([len(set(A[i])&set(B[i]))/k for i in queries])) if queries else None

def meeting_mean(A,B,queries,meta,k):
    grouped=collections.defaultdict(list)
    for i in queries:grouped[meta[i]['meeting_id']].append(len(set(A[i])&set(B[i]))/k)
    return float(np.mean([np.mean(v) for v in grouped.values()])) if grouped else None

def calculate(meta,L,S,k=15):
    baseL,_=neighbors(L,meta,'baseline',k);baseS,_=neighbors(S,meta,'baseline',k)
    out=[]
    for scenario in PLAN['scenarios']:
        a,coverage=neighbors(L,meta,scenario,k);b,_=neighbors(S,meta,scenario,k)
        q=sorted(set(a)&set(b));baseq=[i for i in q if i in baseL and i in baseS]
        if q!=baseq:raise ValueError('Restricted query unexpectedly lacks baseline')
        out.append({'scenario':scenario,**coverage,'overlap':overlap(a,b,q,k),
            'same_query_baseline':overlap(baseL,baseS,q,k),
            'overlap_minus_uniform':overlap(a,b,q,k)-coverage['uniform_overlap_expected'] if q and coverage['uniform_overlap_expected'] is not None else None,
            'equal_meeting_overlap':meeting_mean(a,b,q,meta,k),
            'equal_meeting_same_query_baseline':meeting_mean(baseL,baseS,q,meta,k)})
    return out

def run(checkpoint,semantic,output):
    if output.exists():raise FileExistsError('No overwrite of sensitivity evidence')
    lock=verify_frozen_lock()
    with offline() as attempts:
        corpus,allrows,_=load_checkpoint(checkpoint)
        rows=[r for r in allrows if r['strict_eligible']]
        if len(rows)!=1641 or any(r['date'] not in {'2026-10-01','2026-10-02'} for r in rows):raise ValueError('Frozen development cohort changed')
        verify_saved_results(semantic)
        lex=load_lexical(checkpoint,'strict_lsa64_k10',rows)
        path=semantic/'strict_semantic_raw384_k10.npz'
        if hashlib.sha256(path.read_bytes()).hexdigest()!=lock['saved_raw_semantic_sha256']:raise ValueError('Semantic model digest changed')
        with np.load(path,allow_pickle=False) as a:
            if a['ids'].tolist()!=[r['id'] for r in rows] or a['text_hashes'].tolist()!=[r['text_sha256'] for r in rows]:raise ValueError('Source order or hashes changed')
            meta,L,S=parents(rows,lex['normalized_lsa'],a['geometry'],[197,365])
        meta=enrich(meta,corpus,rows)
        comparisons=calculate(meta,L,S)
        leave_series=[]
        for group in sorted({r['series'] for r in meta if r['series']}):
            ix=[i for i,r in enumerate(meta) if r['series']!=group]
            m=[meta[i] for i in ix];a,cov=neighbors(L[ix],m);b,_=neighbors(S[ix],m)
            q=sorted(set(a)&set(b))
            leave_series.append({'excluded_series':group,'remaining_parents':len(m),'remaining_meetings':len({r['meeting_id'] for r in m}),
                'queries':len(q),'overlap':overlap(a,b,q,15),'note':'Recomputed retrieval only; no representation refit or independent test'})
        # Parallel source-only country recurrence rates with honest pair denominators.
        crows=[]
        for scenario in PLAN['scenarios']:
            nn,cov=neighbors(S,meta,scenario)
            pairs=[(i,j) for i,ns in nn.items() for j in ns if meta[i]['country'] and meta[j]['country']]
            crows.append({'scenario':scenario,'known_country_pairs':len(pairs),'all_pairs':cov['pairs'],
                'same_country_share':float(np.mean([meta[i]['country']==meta[j]['country'] for i,j in pairs])) if pairs else None,
                'different_population_from_historical_repeated_country_test':True})
        counts=collections.Counter(r['speaker_proxy'] for r in meta if r['speaker_proxy'])
        history=collections.defaultdict(set)
        for r in meta:
            if r['speaker_proxy']:history[r['speaker_proxy']].add(r['meeting_id'])
        result={'schema':'un.dependency-controls-results.v1','plan':PLAN,'source_corpus_sha256':corpus['sha256'],
            'frozen_evaluation_lock_sha256':lock['sha256'],'parents':len(meta),'strict_passages':len(rows),
            'speaker_id_observed':sum(r['speaker_id'] is not None for r in meta),
            'complete_proxy_parents':sum(r['speaker_proxy'] is not None for r in meta),
            'cross_meeting_proxy_values':sum(len(v)>1 for v in history.values()),
            'largest_proxy_parents':max(counts.values(),default=0),
            'series_known_parents':sum(r['series'] is not None for r in meta),
            'series_counts':dict(collections.Counter(r['series'] or 'unknown' for r in meta)),
            'formula_parent_counts':{phrase:sum(i in r['formula'] for r in meta) for i,phrase in enumerate(PHRASES)},
            'comparisons':comparisons,'leave_one_series_out':leave_series,'country_pair_sensitivity':crows,
            'network_attempts':len(attempts),'reserved_transcripts_opened':0,'model_refitted':False,
            'interpretation':'Series and affiliation/function are proxies, not observed agenda items or verified persons. Descriptive sensitivity; original lock and cohort unchanged.'}
        if attempts:raise ValueError('Network attempt')
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf8') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('checkpoint',type=Path);p.add_argument('semantic',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(run(a.checkpoint,a.semantic,a.output),indent=2))
