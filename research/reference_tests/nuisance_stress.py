#!/usr/bin/env python3
"""Additional development-only genre/role/speaker-proxy sensitivity and versioned alias audit.

Reads only saved development files and saved semantic arrays; no holdout loader.
The optional v2 masking run uses a pinned local model, never alters the frozen v1.
"""
from __future__ import annotations
import argparse, collections, json, hashlib, sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'machine_review'))
sys.path.insert(0,str(HERE.parent/'semantic_review'))
from compare import load_checkpoint, load_lexical
from encoder import LocalEncoder, offline, normalized
from reference import parents as aggregate_parents,digest,crossmeeting_knn,country_population
from mask_sensitivity import aliases,matcher,masked_rows,frozen_lexical

VERSION='un.nuisance-stress-sensitivity.v1'
SENSITIVITY_ONLY={'island','thai'}
FORMULAS=('thank you','technical assistance','international cooperation','distinguished','human rights','on behalf of','members of the council','we call on')


def conditional_knn(vectors:np.ndarray,meta:list[dict],criteria:tuple[str,...],k:int=15):
    """Reject queries with insufficient eligible candidates; never fill with same-meeting neighbors."""
    V=normalized(np.asarray(vectors,dtype=np.float64))
    sim=V@V.T
    np.fill_diagonal(sim,-np.inf)
    identities=[r['meeting_id'] for r in meta]
    for i,r in enumerate(meta):
        for j,s in enumerate(meta):
            if identities[i]==identities[j] or any(r[c]==s[c] for c in criteria):sim[i,j]=-np.inf
    eligible=np.sum(np.isfinite(sim),axis=1)
    query=np.flatnonzero(eligible>=k)
    nearest=np.argsort(-sim[query],axis=1,kind='stable')[:,:k]
    return query,nearest,eligible


def share_categories(indices,neighbor_indices,meta,key):
    if len(indices)==0:return None
    value=[int(meta[i][key]==meta[j][key]) for i,nn in zip(indices,neighbor_indices) for j in nn]
    return float(np.mean(value))


def control(meta,L,S,S_mask):
    output={}
    for blocked in ((),('genre',),('role',),('genre','role')):
        label='cross_meeting' if not blocked else 'exclude_shared_'+'_'.join(blocked)
        q,a,pool=conditional_knn(S,meta,blocked)
        if len(q):
            lq,b,_=conditional_knn(L,meta,blocked)
            if not np.array_equal(q,lq):raise ValueError('Unequal conditional query denominator')
            overlap=float(np.mean([len(set(x)&set(y))/15 for x,y in zip(a,b)]))
            _,am,_=conditional_knn(S_mask,meta,blocked)
            if len(am)!=len(a):raise ValueError('Masked denominator differs from source')
            mask_overlap=float(np.mean([len(set(x)&set(y))/15 for x,y in zip(b,am)]))
        else:overlap=mask_overlap=None
        output[label]={'queries':len(q),'total':len(meta),'eligible_pair_count':len(q)*15,
            'min_candidate_pool':int(min(pool)), 'lexical_semantic_overlap':overlap,
            'lexical_masked_semantic_overlap':mask_overlap,'source_genre_share':share_categories(q,a,meta,'genre'),
            'source_role_share':share_categories(q,a,meta,'role')}
    return output


def run(checkpoint:Path,sem_results:Path,mask_dir:Path,model_dir:Path|None,output:Path):
    if output.exists():raise FileExistsError('Results exist: never overwrite original sensitivity')
    corpus,allrows,_=load_checkpoint(checkpoint)
    strict=[r for r in allrows if r['strict_eligible']]
    if len(strict)!=1641 or any(r['split']!='development' or r['human_confirmed'] for r in strict):
        raise ValueError('Development population changed')
    lex=load_lexical(checkpoint,'strict_lsa64_k10',strict)
    with np.load(sem_results/'strict_semantic_raw384_k10.npz',allow_pickle=False) as data:
        if data['ids'].tolist()!=[r['id'] for r in strict] or data['text_hashes'].tolist()!=[r['text_sha256'] for r in strict]:
            raise ValueError('Semantic source identities not equal')
        S=data['geometry'].copy()
    prior=json.loads((mask_dir/'manifest.json').read_text())
    if prior['original_corpus_sha256']!=corpus['sha256'] or any('/' in k or digest((mask_dir/k).read_bytes())!=v for k,v in prior['files'].items()):
        raise ValueError('Prior masking artifact tampered')
    with np.load(mask_dir/'masked-geometry.npz',allow_pickle=False) as data:
        if data['ids'].tolist()!=[r['id'] for r in strict] or data['original_hashes'].tolist()!=[r['text_sha256'] for r in strict]:
            raise ValueError('Mask v1 changed population')
        maskS=data['semantic_raw'].copy()
        prior_masked_hashes=data['masked_hashes'].tolist()
    meta,L,Psem=aggregate_parents(strict,lex['normalized_lsa'],S,[197,365]);_,_,Pmask=aggregate_parents(strict,lex['normalized_lsa'],maskS,[197,365])
    parent_ids={p['id']:p for p in corpus['parents']}
    # An affiliation+function pair is a REPEATED SOURCE METADATA PROXY, not a person ID.
    proxies=[]
    for m in meta:
        src=parent_ids[m['parent_id']]
        speaker=src.get('speaker_metadata') or {}
        affiliation=(str(speaker.get('affiliation_full') or speaker.get('affiliation') or '').casefold().strip())
        fn=(str(speaker.get('function') or '').casefold().strip())
        proxies.append(affiliation+'|'+fn if affiliation or fn else None)
    meta=[{**m,'affiliation_function_proxy':proxy} for m,proxy in zip(meta,proxies)]
    _,kn,_=conditional_knn(Psem,meta,())
    proxy_pairs=sum(1 for i,neighbors in enumerate(kn) for j in neighbors if proxies[i] and proxies[i]==proxies[j])
    proxy_nonmissing=sum(1 for i,neighbors in enumerate(kn) for j in neighbors if proxies[i] and proxies[j])
    proxy_group=collections.defaultdict(set)
    for r,p in zip(meta,proxies):
        if p:proxy_group[p].add(r['meeting_id'])
    repeated_proxy_groups=sum(len(v)>1 for v in proxy_group.values())
    texts=collections.defaultdict(list)
    for r in strict:texts[r['parent_id']].append(r['text'])
    phrase_counts={formula:sum(formula in ' '.join(texts[m['parent_id']]).casefold() for m in meta) for formula in FORMULAS}
    alias_v1=aliases(corpus['source_bundle']['registry'])
    alias_v2=[a for a in alias_v1 if a.casefold() not in SENSITIVITY_ONLY]
    if not len(alias_v2)<len(alias_v1):raise ValueError('Alias sensitivity changed upstream unexpectedly')
    original_alias_matches={name:sum(len(list(matcher([name]).finditer(r['text']))) for r in strict) for name in SENSITIVITY_ONLY}
    result={'schema':VERSION,'kind':'development_only_versioned_sensitivity','real_holdout_transcripts_opened':0,
        'source_corpus_sha256':corpus['sha256'],'strict_passages':len(strict),'observed_source_parents':len(meta),
        'genre_role_controls':control(meta,L,Psem,Pmask),
        'metadata_proxy':{'proxy_type':'recorded affiliation+recorded function; not verified speaker identity',
            'non_missing_source_parents':sum(x is not None for x in proxies),
            'repeated_across_meetings_proxy_values':repeated_proxy_groups,
            'same_proxy_neighbor_share_when_both_recorded':proxy_pairs/proxy_nonmissing if proxy_nonmissing else None,
            'neighbor_pairs_with_both_recorded':proxy_nonmissing,
            'confirmed_person_identity_count':None},
        'institutional_formula_occurrence_by_source_parent':phrase_counts,
        'mask_v2_policy':{'version':'un.country-alias-masking-sensitivity.v2',
            'historical_v1_unchanged':True,'v1_alias_count':len(alias_v1),'v2_alias_count':len(alias_v2),
            'excluded_aliases':sorted(SENSITIVITY_ONLY),'excluded_alias_occurrences_in_strict_passages':original_alias_matches,
            'purpose':'Remove generic island and ambiguous demonym Thai from the registry-derived country-name mask. No claim of comprehensive entity removal.',
            'original_source_text_edited':False}}
    if model_dir is not None:
        masked,events=masked_rows(strict,matcher(alias_v2))
        previously_masked,previous_events=masked_rows(strict,matcher(alias_v1))
        if [r['text_sha256'] for r in previously_masked]!=prior_masked_hashes:
            raise ValueError('Previous v1 masked array hashes do not match original rows')
        changed=[i for i,(new,old) in enumerate(zip(masked,previously_masked)) if new['text_sha256']!=old['text_sha256']]
        token_audit={'changed_passages':sum(r['text_sha256']!=a['text_sha256'] for r,a in zip(masked,strict)),
            'alias_replacements':sum(e['matches'] for e in events)}
        E=np.asarray(maskS,dtype=np.float32).copy()
        audit={'wordpieces':0,'chunks':0,'truncated_wordpieces':0}
        if changed:
            with offline() as network_attempts:
                partial,chunks,audit=LocalEncoder(model_dir,json.loads((HERE.parent/'semantic_review/model-lock.json').read_text())).encode([masked[i] for i in changed],batch_size=16)
                if network_attempts:raise ValueError('Unexpected network')
            E[changed]=partial
        if not np.isfinite(E).all():raise ValueError('Incomplete masked v2 embedding coverage')
        token_audit['reused_from_verified_v1_passages']=len(masked)-len(changed)
        token_audit['reencoded_changed_passages']=len(changed)
        token_audit['full_passage_coverage_count']=len(masked)
        lex_v2=frozen_lexical(masked,lex,json.loads((checkpoint/'final-analysis/plan.json').read_text())['vectorizer'])
        meta_v2,Plex_v2,Psem_v2=aggregate_parents(masked,lex_v2,E,[197,365])
        if [r['parent_id'] for r in meta_v2]!=[r['parent_id'] for r in meta]:
            raise ValueError('Mask v2 altered parent identifiers')
        country_idx,known,_=country_population(meta)
        labels=[meta[i]['country'] for i in country_idx]
        mknown=[meta[i] for i in country_idx]
        def cshare(x):
            _,nn,_=conditional_knn(x[country_idx],mknown,())
            return float(np.mean([labels[i]==labels[j] for i,n in enumerate(nn) for j in n]))
        result['mask_v2_reencoding']={**token_audit,'reencoded_wordpieces':audit['wordpieces'],
            'reencoded_chunks':audit['chunks'],'truncated_wordpieces':audit['truncated_wordpieces'],
            'same_country_neighbor_share_original':cshare(Psem),
            'same_country_neighbor_share_v1':cshare(Pmask),
            'same_country_neighbor_share_v2':cshare(Psem_v2),
            'same_source_passage_identifiers':True,
            'no_refitting':True,'human_approval_created':False}
        output.mkdir(parents=True)
        np.savez_compressed(output/'masked-v2-vectors.npz',ids=np.array([r['id'] for r in masked]),
            orig_text_hashes=np.array([r['text_sha256'] for r in strict]),masked_text_hashes=np.array([r['text_sha256'] for r in masked]),
            semantic_raw=E,lexical_lsa=lex_v2)
        (output/'masked-v2-audit.json').write_text(json.dumps(events,ensure_ascii=False)+'\n')
    else:output.mkdir(parents=True);result['mask_v2_reencoding']={'status':'not_run_encoder_asset_not_supplied'}
    (output/'nuisance-summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('checkpoint',type=Path);p.add_argument('semantic_results',type=Path)
    p.add_argument('original_mask_results',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--pinned-local-encoder',type=Path)
    a=p.parse_args();r=run(a.checkpoint,a.semantic_results,a.original_mask_results,a.pinned_local_encoder,a.output)
    print(json.dumps({'status':'PASS_DEVELOPMENT_SENSITIVITY','parents':r['observed_source_parents'],
      'reencoded':r['mask_v2_reencoding'].get('same_country_neighbor_share_v2') is not None,
      'real_holdout_opened':0}))

if __name__=='__main__':main()
