#!/usr/bin/env python3
"""Read-only independent audit of frozen development sources; never opens holdout transcripts."""
import json,hashlib,collections,itertools,re
from pathlib import Path
import numpy as np


def read(p):return json.loads(Path(p).read_text())
def hash_bytes(b):return hashlib.sha256(b).hexdigest()
def norm(x):
    a=np.asarray(x,dtype=np.float64)
    z=np.linalg.norm(a,axis=1,keepdims=True)
    if (z==0).any():raise ValueError('zero vector')
    return a/z

def knn(a,meetings,k=15):
    sim=norm(a)@norm(a).T
    m=np.asarray(meetings)
    sim[m[:,None]==m[None,:]]=-np.inf
    if np.min(np.sum(np.isfinite(sim),axis=1))<k:raise ValueError('Insufficient eligible neighbors')
    return np.argsort(-sim,axis=1,kind='stable')[:,:k]

def shared(a,b):
    if a.shape!=b.shape:raise ValueError('mismatch')
    return np.mean([len(set(rowa)&set(rowb))/len(rowa) for rowa,rowb in zip(a,b)])

def category_match(neighbors,categories,nonnull=False):
    c=np.asarray(categories,dtype=object)
    hits=[]
    for i,ns in enumerate(neighbors):
        if nonnull and c[i] is None:continue
        for j in ns:
            if nonnull and c[j] is None:continue
            hits.append(c[i]==c[j])
    return {'share':float(np.mean(hits)) if hits else None,'pairs':len(hits)}

def expected_category(meetings,categories):
    # unweighted per-query chance of category equality under uniform eligible cross-meeting choice
    n=len(meetings);cat=np.asarray(categories,dtype=object);met=np.asarray(meetings)
    return float(np.mean([np.mean(cat[np.arange(n)[met!=met[i]]]==cat[i]) for i in range(n)]))

def run(checkpoint: Path, semantic_results: Path, mask_results: Path, repository: Path, output: Path):
    CHECK=checkpoint
    SEM=semantic_results
    MASK=mask_results
    REPO=repository
    OUT=output
    if OUT.exists():
        raise FileExistsError('Use a new output directory; no overwrite')
    OUT.mkdir(parents=True)
    corpus=read(CHECK/'original/corpus.json')
    record=read(CHECK/'final-review/provisional-corpus.json')
    frame=corpus['frame'];lock=read(REPO/'research/reference_tests/evaluation-lock.json')
    assert frame['sha256']==lock['frame_sha256']
    assert corpus['sha256']==lock['source_corpus_sha256']
    # Bind the independent scorer to the exact artifacts named in the historic
    # evaluation lock; never accept a swapped fit under the original source IDs.
    sha_file=lambda f:hash_bytes(Path(f).read_bytes())
    assert sha_file(CHECK/'final-analysis/strict_lsa64_k10.npz')==lock['saved_lexical_model_sha256']
    assert sha_file(SEM/'strict_semantic_raw384_k10.npz')==lock['saved_raw_semantic_sha256']
    assert sha_file(SEM/'strict_semantic_pca64_k10.npz')==lock['saved_semantic_pca_model_sha256']
    saved_mask=read(MASK/'manifest.json')
    assert saved_mask['original_corpus_sha256']==corpus['sha256']
    for name,value in saved_mask['files'].items():
        assert '/' not in name and '\\' not in name and sha_file(MASK/name)==value, 'Masked derivative hash mismatch'
    assert frame['holdout_state']=='reserved_not_downloaded'
    reserved=[m for m in frame['meetings'] if m['split']=='holdout']
    assert len(reserved)==37
    assert not any(p['split']!='development' for p in corpus['parents'])
    assert not any(p['split']!='development' for p in record['records'])
    assert len(corpus['parents'])==1293 and len(corpus['passages'])==2596
    # Verify raw text hashes and exact codepoint offsets independently against originals.
    source_by_id={p['id']:p for p in corpus['parents']}
    assert len(source_by_id)==len(corpus['parents'])
    text_errors=[];span_errors=[]
    for p in corpus['parents']:
        if hash_bytes(p['text'].encode('utf-8'))!=p['text_sha256']:text_errors.append(p['id'])
    for p in corpus['passages']:
        raw=source_by_id[p['parent_id']]['text']
        if p['text'] != ''.join(list(raw)[p['parent_start']:p['parent_end']]) or hash_bytes(p['text'].encode('utf8'))!=p['text_sha256']:span_errors.append(p['id'])
    rows=[r for r in record['records'] if r['strict_eligible']]
    assert len(rows)==1641
    assert all(r['split']=='development' and not r['human_confirmed'] for r in rows)
    with np.load(CHECK/'final-analysis/strict_lsa64_k10.npz',allow_pickle=False) as z:
        assert z['ids'].tolist()==[r['id'] for r in rows]
        lex=z['normalized_lsa'].copy()
    with np.load(SEM/'strict_semantic_raw384_k10.npz',allow_pickle=False) as z:
        assert z['ids'].tolist()==[r['id'] for r in rows]
        assert z['text_hashes'].tolist()==[r['text_sha256'] for r in rows]
        sem=z['geometry'].copy()
    with np.load(MASK/'masked-geometry.npz',allow_pickle=False) as z:
        assert z['ids'].tolist()==[r['id'] for r in rows]
        assert z['original_hashes'].tolist()==[r['text_sha256'] for r in rows]
        masked_sem=z['semantic_raw'].copy()
        masked_lex=z['lexical'].copy()

    indices=collections.defaultdict(list)
    for i,r in enumerate(rows):indices[r['parent_id']].append(i)
    meta=[];Plex=[];Psem=[];Pmasked=[];Pmaskedlex=[]
    for pid,idx in indices.items():
        parts=[rows[i] for i in idx]
        first=parts[0]
        assert all(p['meeting_id']==first['meeting_id'] and p['country']==first['country'] and p['machine_actor_role']==first['machine_actor_role'] for p in parts)
        weights=np.asarray([max(1,r['tokens']) for r in parts],dtype=float)
        Plex.append(np.average(lex[idx],axis=0,weights=weights));Psem.append(np.average(sem[idx],axis=0,weights=weights));Pmasked.append(np.average(masked_sem[idx],axis=0,weights=weights));Pmaskedlex.append(np.average(masked_lex[idx],axis=0,weights=weights))
        src=source_by_id[pid]
        meta.append({'id':pid,'meeting':first['meeting_id'],'date':first['date'],'genre':first['genre'],'country':first['country'],
                     'role':first['machine_actor_role'],'tokens':int(weights.sum()),'passages':len(idx),
                     'affiliation':(src['speaker_metadata'].get('affiliation_full') or src['speaker_metadata'].get('affiliation') or None),
                     'function':src['speaker_metadata'].get('function')})
    assert len(meta)==523
    Plex=norm(np.stack(Plex));Psem=norm(np.stack(Psem));Pmasked=norm(np.stack(Pmasked));Pmaskedlex=norm(np.stack(Pmaskedlex))
    meet=[r['meeting'] for r in meta]; genre=[r['genre'] for r in meta];roles=[r['role'] for r in meta]
    kl=knn(Plex,meet);ks=knn(Psem,meet);km=knn(Pmasked,meet);kml=knn(Pmaskedlex,meet)
    main_overlap=shared(kl,ks);mask_overlap=shared(kl,km);both_masked_overlap=shared(kml,km)
    country_count=collections.defaultdict(set)
    for r in meta:
        if r['country']:country_count[r['country']].add(r['meeting'])
    repeated={c for c,v in country_count.items() if len(v)>=2}
    repeated_idx=[i for i,r in enumerate(meta) if r['country'] in repeated]
    rm=[meta[i] for i in repeated_idx]
    rc=[r['country'] for r in rm]
    rmeet=[r['meeting'] for r in rm]
    ksc=knn(Psem[repeated_idx],rmeet);kmc=knn(Pmasked[repeated_idx],rmeet)
    orig_share=category_match(ksc,rc); masked_share=category_match(kmc,rc)
    # Same-country signal under different-genre-only neighbors, with proper denominators.
    def conditional_neighbors(a, meta, condition, k=15):
        m=[r['meeting'] for r in meta];sim=norm(a)@norm(a).T
        for i in range(len(meta)):
            for j in range(len(meta)):
                if m[i]==m[j] or not condition(meta[i],meta[j]):sim[i,j]=-np.inf
        elig=np.isfinite(sim).sum(axis=1)
        selected=np.flatnonzero(elig>=k)
        return np.argsort(-sim[selected],axis=1,kind='stable')[:,:k],selected,elig

    def matched_conditional(a,meta,condition,key,k=15):
        nn,selected,elig=conditional_neighbors(a,meta,condition,k)
        hits=[]
        for ii,i in enumerate(selected):
            for j in nn[ii]:hits.append(meta[i][key]==meta[j][key])
        return {'eligible_queries':int(len(selected)), 'total_queries':len(meta), 'pair_count':len(hits),
                'share':float(np.mean(hits)) if hits else None, 'min_candidate_pool':int(np.min(elig))}

    country_crossgenre_original=matched_conditional(Psem[repeated_idx],rm,lambda a,b: a['genre']!=b['genre'],'country')
    country_crossgenre_masked=matched_conditional(Pmasked[repeated_idx],rm,lambda a,b: a['genre']!=b['genre'],'country')
    # Finer nuisance measures without inferred speaker identity.
    meeting_counts=collections.Counter(meet);genre_counts=collections.Counter(genre);role_counts=collections.Counter(roles)
    known=sum(r['country'] is not None for r in meta)
    repeated_recorded_affiliations=collections.defaultdict(set)
    for r in meta:
        if r['affiliation']:repeated_recorded_affiliations[r['affiliation']].add(r['meeting'])
    repeated_aff={k for k,ms in repeated_recorded_affiliations.items() if len(ms)>1}
    nontext_duplicate_across_meet=collections.defaultdict(set)
    for p in corpus['parents']:
        nontext_duplicate_across_meet[p['text_sha256']].add(p['meeting_id'])
    crossmeeting_dup=sum(len(ms)>1 for ms in nontext_duplicate_across_meet.values())
    # Formation of index may be concentrated in one meeting -- inspect per meeting.
    by_meeting=[]
    for m,count in meeting_counts.most_common():
        indices_m=[i for i,r in enumerate(meta) if r['meeting']==m]
        by_meeting.append({'meeting':m,'parents':count,'share':count/len(meta),'genre':meta[indices_m[0]]['genre'],
                           'country_known':sum(meta[i]['country'] is not None for i in indices_m),
                           'type_role_breakdown':dict(collections.Counter(meta[i]['role'] for i in indices_m))})

    # Institution/procedure boilerplate indicator, source language retained for audit only (not published).
    pattern=re.compile(r'(?i)\b(?:mr\.?\s+president|madam\s+president|human\s+rights\s+council|thank\s+you|distinguished\s+delegates|general\s+assembly|united\s+nations|item\s+\d+|draft\s+resolution|agenda\s+item)\b')
    boiler=[bool(pattern.search(' '.join(rows[i]['text'] for i in indices[r['id']]))) for r in meta]

    # Check leave-one-meeting-out retrieval as a sensitivity diagnostic, with no refitting.
    lo=[]
    for excluded in sorted(set(meet)):
        keep=[i for i,m in enumerate(meet) if m!=excluded]
        if len(set(meet[i] for i in keep))<8:continue
        common=[meet[i] for i in keep]
        lo.append({'excluded_meeting':excluded,'remaining_parents':len(keep),
                   'overlap':shared(knn(Plex[keep],common),knn(Psem[keep],common))})
    query_scores=np.array([len(set(a)&set(b))/len(a) for a,b in zip(kl,ks)])
    means=[]
    for m in sorted(set(meet)):
        ix=[i for i,v in enumerate(meet) if v==m]
        means.append({'meeting_id':m,'parent_count':len(ix),'mean_overlap':float(query_scores[ix].mean())})
    # Check complete source bundles for held-out row/file contamination (metadata permitted).
    reserved_status=collections.Counter('available_in_original_inventory' if m['has_transcript'] else 'unavailable_in_original_inventory' for m in reserved)
    reserved_genre=collections.Counter((m['genre'],bool(m['has_transcript'])) for m in reserved)
    reserved_speakers_looked_up=False
    strict_hashes={source_by_id[p]['text_sha256'] for p in indices}
    strict_cross_meeting_dups=collections.defaultdict(set)
    for p in indices:
        strict_cross_meeting_dups[source_by_id[p]['text_sha256']].add(source_by_id[p]['meeting_id'])
    mask_audit=read(MASK/'mask-audit.json')
    alias_use=collections.Counter(s['matched_alias'].casefold() for x in mask_audit for s in x['spans'])
    # All errors returned as counts; no transcript material is included.

    result={
     'schema':'un.independent-readonly-audit.v1','scope':'saved development-only evidence and frozen metadata; NO reserved transcript access',
     'sealed_lock_sha256':lock['sha256'],
     'integrity':{'source_parent_hash_errors':len(text_errors),'source_passage_span_errors':len(span_errors),
                  'source_parents':len(source_by_id),'partitions':len(corpus['passages']),
                  'strict_passages':len(rows),'strict_parents':len(meta),'strict_meetings':len(meeting_counts),
                  'reserved_metadata_meetings':len(reserved),'holdout_text_records_opened':0},
     'source_concentration':{'by_meeting':by_meeting,'top_meeting_parent_share':by_meeting[0]['share'],
                             'top_three_meeting_parent_share':sum(x['share'] for x in by_meeting[:3]),
                             'by_genre':dict(genre_counts),'by_role':dict(role_counts),
                             'country_missing_parents':len(meta)-known,'known_country_parents':known,
                             'countries_represented_in_two_meetings':len(repeated),
                             'country_subset_parents':len(rm),
                             'recorded_affiliation_values_multiple_meetings':len(repeated_aff),
                             'exact_parent_text_hash_families_across_meetings':crossmeeting_dup,
                             'strict_crossmeeting_exact_duplicate_families':sum(len(m)>1 for m in strict_cross_meeting_dups.values()),
                             'mask_alias_generic_island_uses':alias_use.get('island',0),
                             'mask_alias_thai_uses':alias_use.get('thai',0),
                             'source_metadata_has_distinct_speaker_identifier':False,
                             'boilerplate_pattern_presence':sum(boiler),'boilerplate_pattern_fraction':float(np.mean(boiler))},
     'independent_kinship':{'crossmeeting_lexical_semantic_overlap':main_overlap,
         'crossmeeting_lexical_masked_semantic_overlap':mask_overlap,
         'crossmeeting_masked_lexical_masked_semantic_overlap':both_masked_overlap,
         'crossmeeting_semantic_same_genre':category_match(ks,genre),
         'crossmeeting_masked_semantic_same_genre':category_match(km,genre),
         'random_baseline_same_genre':expected_category(meet,genre),
         'crossmeeting_semantic_same_role':category_match(ks,roles),
         'random_baseline_same_role':expected_category(meet,roles),
         'country_repeated_subset_semantic':orig_share,'country_repeated_subset_masked_semantic':masked_share,
         'country_repeated_subset_cross_genre_original':country_crossgenre_original,
         'country_repeated_subset_cross_genre_masked':country_crossgenre_masked,
         'equal_meeting_mean_crossrep_overlap':float(np.mean([x['mean_overlap'] for x in means])),
         'per_meeting_crossrep_overlap_range':[float(min(x['mean_overlap'] for x in means)),float(max(x['mean_overlap'] for x in means))],
         'leave_one_meeting_out_overlap_range':[float(min(x['overlap'] for x in lo)),float(max(x['overlap'] for x in lo))],
         'leave_one_meeting_out_detailed':lo},
     'evaluation_readiness':{
         'real_holdout_input_path':'not_implemented',
         'holdout_inventory_status_counts':dict(reserved_status),
         'reserved_genre_available_counts':[{ 'genre':gen, 'available':available,'meetings':count} for (gen,available),count in sorted(reserved_genre.items())],
         'synthetic_smoke_only':True,
         'speech_identity':'unverified',
         'speaker_identity':'unobservable_from_cached_transcript_metadata',
         'holdout_role_genre_and_attribution_coverage':'unknown_before_access',
         'development_definitional_independence':'not_established',
         'historical_frozen_protocol_modified':False,
         'holdout_transcript_access_authorized':False
     },
     'method_note':'Descriptive independent direct cosine nearest neighbors over whole-source weighted passage aggregates. Aggregation matches declared definition; not independent source acquisition or human annotation.'}
    (OUT/'independent-audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=True)+'\n')
    print('AUDIT_INTEGRITY',json.dumps(result['integrity'],sort_keys=True))
    print('CONCENTRATION',json.dumps({k:v for k,v in result['source_concentration'].items() if k!='by_meeting'},sort_keys=True))
    print('TOP_MEETINGS',json.dumps(by_meeting[:5]))
    print('KNN',json.dumps(result['independent_kinship'],sort_keys=True))

    return result

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Independent read-only development nuisance audit; never accesses reserved transcripts')
    parser.add_argument('development_checkpoint',type=Path)
    parser.add_argument('semantic_results',type=Path)
    parser.add_argument('masked_results',type=Path)
    parser.add_argument('repository_root',type=Path)
    parser.add_argument('new_output_directory',type=Path)
    a=parser.parse_args()
    run(a.development_checkpoint,a.semantic_results,a.masked_results,a.repository_root,a.new_output_directory)
