#!/usr/bin/env python3
"""Fixed-model country-name masking on the same saved provisional development IDs."""
from __future__ import annotations
import argparse, collections, csv, hashlib, json, re, sys, unicodedata
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import normalize as sk_normalize
from sklearn.metrics import adjusted_rand_score
from reference import (HERE, agreement, calculate, country_population, crossmeeting_knn, normalized, parents,
                       read, same_country, verify_saved_results, digest, canonical)
from compare import load_checkpoint, load_lexical
from encoder import LocalEncoder, load_cache, offline, sha, write_json

VERSION='un.country-name-masking.v1'
# Rule freeze: omit ambiguous single-word country names and demonyms; no ISO code aliases.
AMBIGUOUS={'georgia','jordan','chad','turkey','reunion','mayotte','jersey','guernsey','christmas island','norfolk island'}
REPLACEMENT='nation'


def aliases(registry: list[dict]) -> list[str]:
    choices=set()
    for row in registry:
        for item in [row.get('country'),*(row.get('aliases') or [])]:
            if not isinstance(item,str):continue
            item=unicodedata.normalize('NFKC',item).strip()
            lowered=item.casefold()
            if len(item)<4 or lowered in AMBIGUOUS or lowered==str(row.get('iso3','')).casefold():continue
            if not re.search(r'[A-Za-z]',item) or not re.fullmatch(r"[A-Za-zÀ-ž][A-Za-zÀ-ž\s’'.\-]+",item):continue
            if item.isupper() and len(item)<6:continue  # UN, USA, NATO, ISO3 etc.
            choices.add(item)
    choices.update(['U.S.','U.S.A.','United States','United Kingdom','People’s Republic of China'])
    return sorted(choices,key=lambda s:(-len(s),s.casefold()))


def matcher(words:list[str])->re.Pattern:
    if not words or len(words)>4000 or any(len(x)>120 for x in words):raise ValueError('Invalid frozen alias scope')
    return re.compile(r'(?<!\w)(?:'+'|'.join(re.escape(x) for x in words)+r')(?!\w)',re.IGNORECASE)


def mask_text(value: str, pattern: re.Pattern) -> tuple[str,list[dict]]:
    spans=[{'start':m.start(),'end':m.end(),'matched_alias':m.group(), 'original_span_sha256':sha(m.group().encode())} for m in pattern.finditer(value)]
    masked=pattern.sub(REPLACEMENT,value)
    if not spans and masked!=value:
        raise ValueError('Masking without a corresponding original text span')
    return masked,spans


def masked_rows(rows:list[dict],regex:re.Pattern)->tuple[list[dict],list[dict]]:
    output=[];audit=[]
    for row in rows:
        if row['split']!='development' or row['human_confirmed']:
            raise ValueError('Only provisional development rows may be masked')
        if sha(row['text'].encode())!=row['text_sha256']:
            raise ValueError('Original source text hash mismatch')
        text,spans=mask_text(row['text'],regex)
        new={**row,'text':text,'original_text_sha256':row['text_sha256'],'text_sha256':sha(text.encode())}
        output.append(new)
        audit.append({'id':row['id'],'parent_id':row['parent_id'],'meeting_id':row['meeting_id'],
                      'source_sha256':row['text_sha256'],'masked_sha256':new['text_sha256'],
                      'matches':len(spans),'spans':spans})
    if [(r['id'],r['parent_id']) for r in output]!=[(r['id'],r['parent_id']) for r in rows]:
        raise ValueError('Masking altered observation identity')
    return output,audit


def frozen_lexical(rows:list[dict],saved:dict,vectorizer_settings:dict)->np.ndarray:
    terms=saved['terms'].tolist()
    options={k:v for k,v in vectorizer_settings.items() if k in ('ngram_range','stop_words','strip_accents','lowercase','token_pattern')}
    if 'ngram_range' in options:options['ngram_range']=tuple(options['ngram_range'])
    cv=CountVectorizer(vocabulary={term:i for i,term in enumerate(terms)},dtype=np.float64,**options)
    X=cv.transform([r['text'] for r in rows]).tocsr().astype(np.float64)
    X.data=np.log(X.data)+1  # the frozen vectorizer uses sublinear_tf=True
    X=X.multiply(saved['idf']).tocsr()
    X=sk_normalize(X)
    return normalized(np.asarray(X @ saved['svd_components'].T))


def frozen_semantic(raw:np.ndarray,saved:dict)->np.ndarray:
    Z=normalized((np.asarray(raw,dtype=np.float64)-saved['pca_mean'])@saved['pca_components'].T)
    if Z.shape[1]!=64:raise ValueError('Unexpected pinned PCA dimension')
    return Z


def centroid_assign(Z:np.ndarray,centers:np.ndarray)->np.ndarray:
    return np.argmin(((Z[:,None,:]-centers[None,:,:])**2).sum(axis=2),axis=1)


def execute(checkpoint:Path,sem_results:Path,model_dir:Path,out:Path):
    if out.exists():raise FileExistsError('Use new masking output directory')
    plan=read(HERE/'plan.json')
    with offline() as attempts:
        corpus,allrows,_=load_checkpoint(checkpoint)
        if corpus['sha256']!=plan['development_corpus_sha256'] or corpus['frame']['sha256']!=plan['development_frame_sha256']:
            raise ValueError('Frozen source checkpoint changed')
        verify_saved_results(sem_results)
        strict=[r for r in allrows if r['strict_eligible']]
        if len(strict)!=1641 or any(r['split']!='development' for r in strict):raise ValueError('Unexpected selected development population')
        lex=load_lexical(checkpoint,'strict_lsa64_k10',strict)
        with np.load(sem_results/'strict_semantic_pca64_k10.npz',allow_pickle=False) as source:
            sem={k:source[k].copy() for k in source.files}
        if sem['ids'].tolist()!=[r['id'] for r in strict] or sem['text_hashes'].tolist()!=[r['text_sha256'] for r in strict]:raise ValueError('Semantic fit/source mismatch')
        names=aliases(corpus['source_bundle']['registry']);regex=matcher(names)
        masked,audit=masked_rows(strict,regex)
        baseline=read(checkpoint/'final-analysis/plan.json')
        original_lex=frozen_lexical(strict,lex,baseline['vectorizer'])
        if not np.allclose(original_lex,lex['normalized_lsa'],rtol=0,atol=1e-8):
            raise ValueError('Unmasked frozen lexical reconstruction differs')
        newlex=frozen_lexical(masked,lex,baseline['vectorizer'])
        lock=read(HERE.parent/'semantic_review/model-lock.json')
        encoder=LocalEncoder(model_dir,lock)
        masked_sem,chunks,encoder_audit=encoder.encode(masked,batch_size=16)
        projected=frozen_semantic(masked_sem,sem)
        orig_raw,_=load_cache(sem_results/'embedding-cache',[r for r in allrows if r['baseline_eligible']],lock)
        look={r['id']:i for i,r in enumerate([r for r in allrows if r['baseline_eligible']])}
        original_sem=orig_raw[[look[r['id']] for r in strict]]
        if not np.allclose(frozen_semantic(original_sem,sem),sem['geometry'],atol=1e-6,rtol=0):
            raise ValueError('Frozen semantic transform not reconstructible')
        parent,L0,S0=parents(strict,lex['normalized_lsa'],original_sem,plan['nuisance']['length_bin_upper_edges'])
        meta,L1,S1=parents(masked,newlex,masked_sem,plan['nuisance']['length_bin_upper_edges'])
        if any((x['parent_id'],x['meeting_id'],x['length_bin'])!=(y['parent_id'],y['meeting_id'],y['length_bin']) for x,y in zip(parent,meta)):
            # Masked tokenizer word counts are explicitly NOT allowed to redefine null blocks.
            raise ValueError('Masking changed frozen original nuisance-stratum contract')
        baseline_result,_=calculate(parent,L0,S0,plan)
        masked_result,_=calculate(parent,L1,S1,plan)
        lab0=centroid_assign(sem['geometry'],sem['centers'])
        lab1=centroid_assign(projected,sem['centers'])
        if not np.array_equal(lab0,sem['labels']):raise ValueError('Saved semantic center labels inconsistent')
        # No fit or recalibration of PCA, LSA, IDF, centroids, null length bins or thresholds.
        ci,cm,_=country_population(parent)
        observed_names={'schema':VERSION,'status':'development_masking_complete',
          'provisional_passages':len(strict),'source_parents':len(parent),'meeting_count':len({x['meeting_id'] for x in parent}),
          'alias_policy':'english_and_latin_registry_aliases_ge4_no_iso3_ambiguous_exclusions_and_declared_US_abbreviations; no_demonyms',
          'alias_count':len(names),'matching_passages':sum(bool(a['matches']) for a in audit),
          'matching_parents':len({a['parent_id'] for a in audit if a['matches']}),
          'replacements':sum(a['matches'] for a in audit),
          'masked_token_coverage':encoder_audit,
          'original_observed_crossmeeting_overlap':baseline_result['primary']['observed'],
          'masked_observed_crossmeeting_overlap':masked_result['primary']['observed'],
          'original_recorded_country_neighbor_share':baseline_result['secondary']['observed'],
          'masked_recorded_country_neighbor_share':masked_result['secondary']['observed'],
          'original_primary_null_mean':baseline_result['primary']['reference_mean'],
          'masked_primary_null_mean':masked_result['primary']['reference_mean'],
          'masked_primary_p_holm':masked_result['primary']['holm_adjusted_p'],
          'original_country_null_mean':baseline_result['secondary']['reference_mean'],
          'masked_country_null_mean':masked_result['secondary']['reference_mean'],
          'masked_country_p_holm':masked_result['secondary']['holm_adjusted_p'],
          'saved_semantic_kmeans_prediction_ari':float(adjusted_rand_score(lab0,lab1)),
          'saved_semantic_prediction_changes':int(np.count_nonzero(lab0!=lab1)),
          'passage_cosine_semantic_mean':float(np.mean(np.sum(original_sem*masked_sem,axis=1))),
          'mask_comparison_only':True,'not_stance_or_coalition':True,
          'heldout_opened':0,'human_approvals':0,
          'retraining_or_recalibration':False}
        if attempts:raise RuntimeError('Blocked network attempted')
    out.mkdir(parents=True)
    write_json(out/'mask-policy.json',{'schema':VERSION,'aliases':names,'exclusions':sorted(AMBIGUOUS),'replacement':REPLACEMENT,'source_registry_sha256':corpus['source_bundle']['registry_sha256'],'plan_sha256':digest((HERE/'plan.json').read_bytes())})
    write_json(out/'mask-audit.json',audit)
    write_json(out/'masked-chunks.json',chunks)
    np.savez_compressed(out/'masked-geometry.npz',ids=np.array([r['id'] for r in strict]),original_hashes=np.array([r['text_sha256'] for r in strict]),masked_hashes=np.array([r['text_sha256'] for r in masked]),lexical=newlex,semantic_raw=masked_sem,semantic_pca64=projected,semantic_predicted_labels=lab1)
    write_json(out/'sensitivity.json',observed_names)
    manifest={'schema':'un.masked-comparison-manifest.v1',
              'original_corpus_sha256':corpus['sha256'],
              'original_semantic_input_manifest_sha256':digest((sem_results/'SHA256.json').read_bytes()),
              'strict_source_ids_sha256':digest(canonical([(r['id'],r['text_sha256']) for r in strict])),
              'masked_ids_sha256':digest(canonical([(r['id'],r['text_sha256']) for r in masked])),
              'original_model_lock_sha256':digest((HERE.parent/'semantic_review/model-lock.json').read_bytes()),
              'implementation_sha256':digest(Path(__file__).read_bytes()),
              'files':{name:digest((out/name).read_bytes()) for name in
                       ['mask-policy.json','mask-audit.json','masked-chunks.json','masked-geometry.npz','sensitivity.json']},
              'holdout_transcripts_opened':0}
    write_json(out/'manifest.json',manifest)
    print(json.dumps({'status':'PASS','masked_passages':observed_names['matching_passages'],'heldout_opened':0}))
    return observed_names

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['checkpoint','semantic_results','model_dir','output']:parser.add_argument(name,type=Path)
    a=parser.parse_args();execute(a.checkpoint,a.semantic_results,a.model_dir,a.output)
