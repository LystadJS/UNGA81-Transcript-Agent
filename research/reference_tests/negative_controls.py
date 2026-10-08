#!/usr/bin/env python3
"""Development-only confounding controls. Metadata is never diplomatic content."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
from reference import (HERE, blocks, calculate, coverage, crossmeeting_knn, country_population,
                       normalized, parents, read, verify_seal, verify_saved_results, digest, canonical)
from reference import shuffle_within
from encoder import load_cache, offline
from compare import load_checkpoint, load_lexical

CONTROL_SCHEMA='un.nuisance-negative-controls.v1'


def fixed_code(value: str, dim: int, seed: int) -> np.ndarray:
    """Hash-based deterministic feature vector; contains no transcript text."""
    h=hashlib.sha256(f'{seed}:{value}'.encode()).digest()
    rng=np.random.default_rng(int.from_bytes(h[:8],'big'))
    return rng.normal(size=dim)


def make_nuisance_vectors(meta: list[dict], dim: int, seed: int, include_country: bool=False) -> np.ndarray:
    if not meta or not 16<=dim<=512 or any(r.get('length_bin') not in (0,1,2) for r in meta):
        raise ValueError('Invalid nuisance-only observation contract')
    vectors=[]
    for row in meta:
        # Only source metadata and a deterministic fixed codebook, NEVER original language or latent vectors.
        v=(2*fixed_code('role:'+str(row['role']),dim,seed)
           +2*fixed_code('genre:'+str(row['genre']),dim,seed)
           +fixed_code('lengthbin:'+str(row['length_bin']),dim,seed)
           +.75*fixed_code('date_group:'+str(row['meeting_id']),dim,seed))
        if include_country and row.get('country'):
            v+=4*fixed_code('recorded_country:'+str(row['country']),dim,seed)
        vectors.append(v)
    return normalized(np.stack(vectors))


def negative_controls(meta: list[dict], reference_plan: dict, seed: int=92711) -> dict:
    # The paired metadata-only geometry emulates a data leak shared by two feature families.
    if len(meta)<200 or len({r['meeting_id'] for r in meta})<8:
        raise ValueError('Development-only controls require the original source population')
    result={}
    for label,with_country in [('source_metadata_only',False),('metadata_with_recorded_country_leakage',True)]:
        l=make_nuisance_vectors(meta,64,seed,with_country)
        s=make_nuisance_vectors(meta,384,seed,with_country)
        # The embedding dimensions deliberately have separate random codebooks. Shared
        # metadata may induce apparent stable structure even with NO policy text.
        fit,draws=calculate(meta,l,s,reference_plan)
        result[label]={'input':'metadata_codebook_only; zero token/text/model features',
                       'includes_recorded_country':with_country,
                       'primary':fit['primary'], 'secondary':fit['secondary'],
                       'nuisance_blocks':fit['nuisance_blocks'],
                       'country_rows':fit['country_parent_rows'],
                       'not_a_heldout_or_political_signal':True}
    return {'schema':CONTROL_SCHEMA,'status':'executed_development_only',
            'source_parents':len(meta),'reference_plan_sha256':digest((HERE/'plan.json').read_bytes()),
            'control_seed':seed,'result':result,'holdout_opened':0,
            'interpretation':'Synthetic metadata-only associations are nuisance confounding demonstrations, never genuine policy signals.'}


def load_meta(checkpoint:Path,semantic_results:Path):
    p=read(HERE/'plan.json')
    with offline() as attempts:
        corpus,allrows,_=load_checkpoint(checkpoint)
        if corpus['sha256']!=p['development_corpus_sha256'] or corpus['frame']['sha256']!=p['development_frame_sha256']:
            raise ValueError('Frozen development corpus hash mismatch')
        verify_saved_results(semantic_results)
        baseline=[r for r in allrows if r['baseline_eligible']]
        strict=[r for r in allrows if r['strict_eligible']]
        if (len(strict),len(baseline))!=(1641,2057) or any(r['split']!='development' for r in strict):
            raise ValueError('Unfrozen or held-out population')
        vectors,_=load_cache(semantic_results/'embedding-cache',baseline,read(HERE.parent/'semantic_review/model-lock.json'))
        indices={r['id']:i for i,r in enumerate(baseline)}
        sem=vectors[[indices[r['id']] for r in strict]]
        lex=load_lexical(checkpoint,'strict_lsa64_k10',strict)['normalized_lsa']
        meta,_,_=parents(strict,lex,sem,p['nuisance']['length_bin_upper_edges'])
        if attempts:raise RuntimeError('Blocked network attempted')
    return meta


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('checkpoint',type=Path);a.add_argument('semantic_results',type=Path);a.add_argument('output',type=Path)
    args=a.parse_args()
    if args.output.exists():raise FileExistsError('Negative-control output exists; no overwrite')
    with offline() as attempts:
        meta=load_meta(args.checkpoint,args.semantic_results)
        result=negative_controls(meta,read(HERE/'plan.json'))
        if attempts:raise RuntimeError('Negative controls unexpectedly attempted network access')
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'PASS','source_parents':len(meta),'controls':list(result['result']),'holdout_opened':0}))

if __name__=='__main__':main()
