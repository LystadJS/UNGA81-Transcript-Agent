#!/usr/bin/env python3
"""Production-shaped synthetic UN pipeline acceptance. NEVER accepts live transcript input.

Generates 37 fictitious UN-shape meeting records, invokes the unchanged Node
source contract and Python machine review, performs pinned real ONNX inference
on fabricated text, and applies the already-sealed synthetic evaluator. It is
neither a real holdout evaluator nor authorization to construct one.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess, sys, tempfile, unicodedata
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'machine_review'))
sys.path.insert(0,str(HERE.parent/'semantic_review'))
from encoder import LocalEncoder, normalized, offline, verify_model
from compare import vectorize_probes
from reference import (parents as aggregate_parents, read, digest, crossmeeting_knn,
    agreement, blocks, coverage, shuffle_within, permuted_neighbor_agreement, empirical_p, country_population, same_country, holm)
from holdout_dryrun import (verify_frozen_lock,evaluate_fixture,SCHEMA)
import review as machine

SCHEMA_OUT='un.production-shaped-synthetic-acceptance.v1'
FAKE_DATE='2099-01-05'
PREFIX='synthetic_fixture_/meeting_'


def validate_artificial_corpus(corpus:dict) -> None:
    """Restrict the *already constructed* corpus to exclusively fabricated records."""
    if corpus.get('schema')!='un.passage-corpus.v1' or corpus['frame']['holdout_state']!='reserved_not_downloaded':
        raise ValueError('Not a synthetic production-shaped corpus')
    rows=corpus['parents'];meetings=corpus['coverage']
    if len(meetings)!=37 or len({m['meeting_id'] for m in meetings})!=37:
        raise ValueError('Exactly 37 fabricated meeting rows required')
    if set(corpus['frame']['plan']['development_dates'])!={FAKE_DATE}:
        raise ValueError('Real dates are prohibited')
    for m in meetings:
        if not re.fullmatch(r'synthetic_fixture_/meeting_\d\d',m['meeting_id']) or m['date']!=FAKE_DATE or m['split']!='development':
            raise ValueError('Non-synthetic meeting or date')
    for p in rows:
        if not re.fullmatch(r'synthetic_fixture_/meeting_\d\d#\d+',p['id']) or p['date']!=FAKE_DATE or p['split']!='development' or p['review_status']!='pending' or p['speech_id'] is not None:
            raise ValueError('Real or human-reviewed source entered synthetic test')
        if not p['source_url'].startswith('https://transcripts.un.org/en/synthetic_fixture_/meeting_'):
            raise ValueError('Unsafe source link in fixture')
    for src in corpus['source_bundle']['sources']:
        if not re.fullmatch(r'synthetic_fixture_/meeting_\d\d',src['meeting_id']):
            raise ValueError('Unexpected source bundle identity')
    if corpus['counts']['reserved_meetings']!=1 or corpus['counts']['meetings']!=37:
        raise ValueError('Fake fixture incorrectly structured')


def machine_populations(corpus:dict):
    groups=collections.defaultdict(list)
    for r in corpus['parents']:groups[r['meeting_id']].append(r)
    annotations=[]
    for rs in groups.values():
        for i,r in enumerate(rs):
            annotations.append(machine.classify(r,rs[i-1] if i else None,rs[i+1] if i+1<len(rs) else None))
    ledger={'schema':machine.SCHEMA,'source_bundle_sha256':corpus['source_bundle']['sha256'],
            'corpus_sha256':corpus['sha256'],'annotations':annotations}
    output=machine.selections(corpus,ledger)
    if len(output)!=len(corpus['passages']) or any(r['human_confirmed'] or r['machine_status']!='provisional' for r in output):
        raise ValueError('Synthetic machine review violated immutable row population')
    return output,annotations


def get_saved(checkpoint:Path,results:Path,lock:dict):
    a=checkpoint/'final-analysis/strict_lsa64_k10.npz'
    b=results/'strict_semantic_pca64_k10.npz'
    if digest(a.read_bytes())!=lock['saved_lexical_model_sha256'] or digest(b.read_bytes())!=lock['saved_semantic_pca_model_sha256']:
        raise ValueError('Frozen fitted model hashes differ from sealed protocol')
    with np.load(a,allow_pickle=False) as x:lex={k:v.copy() for k,v in x.items()}
    with np.load(b,allow_pickle=False) as x:sem={k:v.copy() for k,v in x.items()}
    if lex['svd_components'].shape!=(64,len(lex['terms'])) or sem['pca_components'].shape!=(64,384) or sem['centers'].shape!=(10,64):
        raise ValueError('Unexpected frozen transform dimensions')
    return lex,sem


def source_status(corpus:dict)->dict:
    coverage=corpus['coverage']
    statuses=dict(collections.Counter(m['status'] for m in coverage))
    return {'all_meetings':len(coverage),'statuses':statuses,'missing_or_failed':sum(m['status']!='collected' for m in coverage),
            'non_english_source_parents':sum(p['language']!='en' for p in corpus['parents']),
            'timestamp_flagged_source_parents':sum(p['timestamps_flagged'] for p in corpus['parents']),
            'unknown_country_source_parents':sum(p['country'] is None for p in corpus['parents']),
            'genres':dict(collections.Counter(m['genre'] for m in coverage)),
            'all_observed_partitions_accounted':all(x['observed_code_points']==x['partitioned_code_points'] for x in corpus['parent_coverage']),
            'source_failure_count':sum(m['status']=='failed' for m in coverage)}


def artificial_model_eval(corpus,checkpoint:Path,results:Path,model_dir:Path,lock:dict)->dict:
    rows,annotations=machine_populations(corpus)
    strict=[r for r in rows if r['strict_eligible']]
    if len(strict)<lock['predeclared_eligibility_gates']['min_eligible_parents']:
        raise ValueError('Fixture unexpectedly has insufficient strict passage observations')
    lex,sem=get_saved(checkpoint,results,lock)
    # Cross-development exact reuse is prohibited even for artificial test rows.
    train=json.loads((checkpoint/'final-review/provisional-corpus.json').read_text())['records']
    training_hashes={r['normalized_text_sha256'] for r in train}
    training_source_hashes={r['raw_sha256'] for r in train}
    synthetic_normalized={hashlib.sha256(' '.join(unicodedata.normalize('NFKC',r['text']).split()).encode()).hexdigest() for r in strict}
    if training_hashes & synthetic_normalized or any(r['raw_sha256'] in training_source_hashes for r in strict):
        raise ValueError('Synthetic input unexpectedly reproduces a development source family or exact normalized text')
    prior=read(checkpoint/'final-analysis/plan.json')
    # Reuse the saved, fitted vocabulary+IDF+SVD. This is transform ONLY, never fit.
    lexical,zero=vectorize_probes([r['text'] for r in strict],lex,prior)
    model_lock=read(HERE.parent/'semantic_review/model-lock.json')
    verify_model(model_dir,model_lock)
    encoder=LocalEncoder(model_dir,model_lock)
    semantic,chunks,token_audit=encoder.encode(strict,batch_size=16)
    if not np.isfinite(lexical).all() or zero or token_audit['truncated_wordpieces']:
        raise ValueError('Unexpected zero-vector or dropped tokens; fail closed')
    projected=normalized((semantic-sem['pca_mean'])@sem['pca_components'].T)
    centers=sem['centers']
    predicted=np.argmin(np.sum((projected[:,None,:]-centers[None,:,:])**2,axis=2),axis=1)
    # Primary metric is on *raw* 384D MiniLM vectors versus frozen 64D lexical.
    meta,L,S=aggregate_parents(strict,lexical,semantic,[197,365])
    id_to_fake={f'synthetic_fixture_/meeting_{i:02d}':f'SYNTHETIC-MEETING-{i:02d}' for i in range(37)}
    statuses={id_to_fake[m['meeting_id']]:('unavailable' if m['status']=='inventory_unavailable' else m['status']) for m in corpus['coverage']}
    _,_,S64=aggregate_parents(strict,lexical,projected,[197,365])
    fixture={'schema':SCHEMA,'synthetic':True,'fake_dates_only':True,'input_kind':'generated_nontext_vectors',
      'meetings':[{'meeting_id':f'SYNTHETIC-MEETING-{i:02d}','date':'1900-01-01','status':statuses[f'SYNTHETIC-MEETING-{i:02d}']} for i in range(37)],
      'parents':[{'parent_id':f'SYNTHETIC-PARENT-{r["parent_id"].rsplit("_",1)[-1].split("#")[0]}-{i:04d}',
        'meeting_id':id_to_fake[r['meeting_id']], 'role':r['role'], 'genre':r['genre'],
        'country':r['country'], 'length_bin':r['length_bin'], 'split':'synthetic','source_kind':'synthetic_only'} for i,r in enumerate(meta)],
      'lexical':L,'semantic':S64,'seed':82631,'variant':'production_shaped_fabricated'}
    # Check parent IDs already meet *synthetic* guard. Test source integrity at the Node parser layer.
    result=evaluate_fixture(fixture,lock,draws=999)
    # The historical synthetic-only evaluator assumes same-width 64D matrices.
    # The frozen scientific primary instead compares lexical 64D to *raw*
    # semantic 384D. Independently exercise that dimensionality without changing
    # the historical lock or mislabeling the 64D evaluator's proxy as the primary.
    knL=crossmeeting_knn(L,meta,15)
    knS=crossmeeting_knn(S,meta,15)
    observed=agreement(knL,knS)
    rng=np.random.default_rng(read(HERE/'plan.json')['seed'])
    strata=blocks(meta,('meeting_id','length_bin'))
    samples=np.array([permuted_neighbor_agreement(knL,knS,shuffle_within(strata,len(meta),rng)) for _ in range(999)])
    ci,repeat_known,nc=country_population(meta)
    secondary=None
    if len(repeat_known)>=150 and nc>=20:
        cgroups=blocks(repeat_known,('meeting_id','length_bin'))
        if coverage(cgroups,len(repeat_known))['movable_fraction']>=lock['predeclared_eligibility_gates']['min_movable_fraction']:
            cn=crossmeeting_knn(S[ci],repeat_known,15)
            labels=np.asarray([r['country'] for r in repeat_known]);cobs=same_country(cn,labels)
            crng=np.random.default_rng(read(HERE/'plan.json')['seed']+1)
            cdraws=np.asarray([same_country(cn,labels[shuffle_within(cgroups,len(repeat_known),crng)]) for _ in range(999)])
            secondary={'observed':cobs,'nominal_p':empirical_p(cobs,cdraws),'known_repeated_country_parents':len(repeat_known),'repeated_countries':nc}
    nominal=empirical_p(observed,samples)
    adjusted=holm([nominal,secondary['nominal_p']])[0] if secondary is not None else min(1.0,2*nominal)
    empty_downloads=[m['meeting_id'] for m in fixture['meetings'] if m['status']=='collected' and not any(r['meeting_id']==m['meeting_id'] for r in fixture['parents'])]
    reasons=['collected_synthetic_meetings_lack_strict_eligible_rows'] if empty_downloads else []
    gates=lock['predeclared_eligibility_gates']
    if len(meta)<gates['min_eligible_parents'] or len({r['meeting_id'] for r in meta})<gates['min_distinct_meetings'] or coverage(strata,len(meta))['movable_fraction']<gates['min_movable_fraction']:
        reasons.append('frozen_coverage_requirement_not_met')
    excess=float(observed-samples.mean())
    passes=bool(excess>0 and excess>=lock['replication_floor_excess'] and adjusted<=gates['max_familywise_alpha'])
    raw_check={'synthetic':True,'lexical_dimensions':L.shape[1], 'semantic_dimensions':S.shape[1],
        'observed':observed,'conditional_null_mean':float(samples.mean()),'excess':excess,
        'nominal_p':nominal,'holm_primary_p':adjusted,'effect_floor':lock['replication_floor_excess'],
        'movable_fraction':coverage(strata,len(meta))['movable_fraction'],
        'crossmeeting_queries':len(meta),'secondary':secondary,'frozen_transform':True,
        'decision':'INCONCLUSIVE_SYNTHETIC' if reasons else ('SYNTHETIC_GATE_WOULD_PASS' if passes else 'SYNTHETIC_GATE_WOULD_NOT_PASS'),
        'withheld_reasons':reasons,'real_holdout_metric':False}
    return {'strict_passages':len(strict),'strict_parent_units':len(meta),
      'strict_meetings':len({r['meeting_id'] for r in strict}),'unresolved_speech_count':len(meta),
      'machine_annotations':len(annotations),'human_confirmations':0,
      'frozen_lexical_features':len(lex['idf']),'frozen_lexical_dimensions':lexical.shape[1],
      'frozen_semantic_input_dimensions':semantic.shape[1], 'frozen_semantic_dimensions':projected.shape[1],
      'frozen_centroid_predictions':len(predicted), 'distinct_predicted_clusters':len(set(predicted.tolist())),
      'model_refitted':False,'all_tokens_accounted':token_audit['truncated_wordpieces']==0,
      'wordpieces':token_audit['wordpieces'],'token_chunks':token_audit['chunks'],
      'zero_vector_count':len(zero),'source_leakage_overlap_count':0,'synthetic_gate':result,'raw_384d_geometry_check':raw_check,
      'evaluator_limit':'Historical synthetic evaluator requires same-width 64D inputs; locked primary raw semantic is 384D. New raw dimensional check is separate and synthetic-only.'}


def run(checkpoint:Path,results:Path,model:Path|None=None)->dict:
    lock=verify_frozen_lock()
    with tempfile.TemporaryDirectory(prefix='un_synthetic_source_') as directory:
        dest=Path(directory)/'fixture'
        subprocess.run(['node',str(HERE/'synthetic_un_fixture.cjs'),str(dest)],check=True,stdout=subprocess.DEVNULL,
                       env=None)
        corpus=json.loads((dest/'corpus.json').read_text())
        validate_artificial_corpus(corpus)
        # Invoke the unchanged production re-derivation (not a mocked parser).
        corpus=machine.read_verified(dest/'corpus.json')
        coverage=source_status(corpus)
        summary={'schema':SCHEMA_OUT,'synthetic':True,'source_parser':'real_production_corpus_contract_v1',
          'source_hashes_validated':True,'fixture_corpus_sha256':corpus['sha256'],
          'source_coverage':coverage,'source_parents':len(corpus['parents']),'source_passages':len(corpus['passages']),
          'frozen_protocol_sha256':lock['sha256'],'authorized_real_source_access':False,
          'reserved_meetings_opened':0,'reserved_meeting_requests':0,'real_holdout_evaluation':False,
          'recorded_source_identity':'artificial_only_not_real_un_provenance',
          'limitations':['Synthetic metadata/JSON structure cannot verify actual future upstream schema or live access',
                         'An observed segment is not a verified complete speech; no person identifier is inferred',
                         'The existing synthetic-only gate is not a production evaluator']}
        if model is None:
            rows,annotations=machine_populations(corpus)
            strict=[r for r in rows if r['strict_eligible']]
            summary['review_only']={'annotations':len(annotations),'strict_passages':len(strict),
                'strict_parent_units':len({r['parent_id'] for r in strict}),
                'strict_meetings':len({r['meeting_id'] for r in strict}),
                'human_confirmations':0}
            summary['full_frozen_inference']='NOT_RUN_REQUIRES_PINNED_LOCAL_MODEL_AND_SAVED_DEVELOPMENT_ARRAYS'
        else:
            with offline() as attempts:
                summary['inference']=artificial_model_eval(corpus,checkpoint,results,model,lock)
                if attempts:raise ValueError('Network attempt inside synthetic inference')
            summary['full_frozen_inference']='PASS_SYNTHETIC_ONLY'
        return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--saved-development-models',type=Path)
    parser.add_argument('--saved-semantic-models',type=Path)
    parser.add_argument('--pinned-local-encoder',type=Path)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError('Refuse to overwrite acceptance result')
    if any(x is not None for x in [args.saved_development_models,args.saved_semantic_models,args.pinned_local_encoder]) and not all(x is not None for x in [args.saved_development_models,args.saved_semantic_models,args.pinned_local_encoder]):
        raise ValueError('Full inference requires all three saved model paths; no fallback allowed')
    result=run(args.saved_development_models,args.saved_semantic_models,args.pinned_local_encoder)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['full_frozen_inference'],'source_parents':result['source_parents'],
                      'heldout_opened':0,'synthetic':True}))

if __name__=='__main__':main()
