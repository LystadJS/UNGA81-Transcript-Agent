#!/usr/bin/env python3
"""Development-only, parent-level conditional references. No holdout loader or network use."""
from __future__ import annotations
import argparse, collections, copy, hashlib, json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'semantic_review'))
from compare import load_checkpoint, load_lexical, previous_review
from encoder import canonical, load_cache, normalized, offline

SCHEMA = 'un.development-reference-results.v1'
LOCK_SCHEMA = 'un.heldout-evaluation-lock.v1'


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, value: dict) -> None:
    with path.open('x', encoding='utf-8') as file:
        json.dump(value, file, indent=2, ensure_ascii=False, allow_nan=False)
        file.write('\n')


def seal(value: dict) -> dict:
    return {**value, 'sha256': digest(canonical(value))}


def verify_seal(value: dict, schema: str) -> None:
    if value.get('schema') != schema or value.get('sha256') != digest(canonical({k:v for k,v in value.items() if k != 'sha256'})):
        raise ValueError('Frozen lock schema or integrity mismatch')


def validate_plan(plan: dict, evaluation: dict) -> None:
    if plan.get('schema') != 'un.development-nuisance-reference-plan.v1' or evaluation.get('schema') != 'un.heldout-evaluation-plan.v1':
        raise ValueError('Unexpected plan version')
    if plan.get('split') != 'development_only' or plan.get('holdout_access') is not False or evaluation.get('state') != 'frozen_protocol_no_holdout_access_or_evaluation':
        raise ValueError('Holdout access is prohibited')
    if plan.get('holdout_meetings') != 37 or evaluation.get('holdout_count') != 37:
        raise ValueError('Frozen holdout size differs')
    if plan.get('declared_tests') != [
        {'id':'lexical_semantic_crossmeeting_agreement','target':'mean_parent_level_fraction_of_identical_15_crossmeeting_neighbors','shuffle':'semantic_parent_vectors_within_meeting_length_bin','tail':'greater'},
        {'id':'recorded_country_recurrence','target':'mean_parent_level_fraction_of_same_recorded_country_among_15_crossmeeting_semantic_neighbors','shuffle':'known_repeated_country_labels_within_meeting_length_bin','tail':'greater'}]:
        raise ValueError('Declared reference family changed')
    if plan.get('permutations') != 999 or plan.get('neighbors') != 15 or plan.get('nuisance',{}).get('length_bin_upper_edges') != [197,365]:
        raise ValueError('Fixed Monte Carlo or length-nuisance contract changed')
    if evaluation.get('holdout_dates') != ['2026-10-05','2026-10-06'] or evaluation.get('authorization_required') != 'separate_explicit_authorization_to_access_reserved_content':
        raise ValueError('Held-out authorization contract changed')


def verify_saved_results(result_dir: Path) -> dict:
    manifest = read(result_dir / 'SHA256.json')
    if not manifest or not all('/' not in name and name != 'SHA256.json' and digest((result_dir/name).read_bytes()) == h for name,h in manifest.items()):
        raise ValueError('Saved semantic result hash mismatch')
    return manifest



def contextual_override_audit(checkpoint: Path, corpus: dict, rows: list[dict]) -> dict:
    ledger=read(checkpoint/'final-review/machine-review.json')
    raw=copy.deepcopy(ledger)
    changed=0
    for annotation in raw['annotations']:
        if annotation.get('baseline_rule_type'):
            changed+=1
            annotation['suggested_type']=annotation['baseline_rule_type']
            annotation['annotation_method']='deterministic_full_text_rules'
    unmodified=previous_review.selections(corpus,raw)
    if len(unmodified)!=len(rows) or any(a['id']!=b['id'] for a,b in zip(unmodified,rows)):
        raise ValueError('Baseline versus annotated observations differ')
    strict_delta=sum(a['strict_eligible']!=b['strict_eligible'] for a,b in zip(unmodified,rows))
    return {'contextual_annotations':changed,'strict_membership_changes':strict_delta,
            'inclusive_membership_changes':sum(a['inclusive_eligible']!=b['inclusive_eligible'] for a,b in zip(unmodified,rows)),
            'meaning':'Machine-only contextual edits are never human approvals; held-out sources receive no contextual overrides.'}


def parents(rows: list[dict], lexical: np.ndarray, semantic: np.ndarray, edges: list[int]) -> tuple[list[dict], np.ndarray, np.ndarray]:
    if len(rows) != len(lexical) or len(rows) != len(semantic) or any(r['split'] != 'development' or r['human_confirmed'] for r in rows):
        raise ValueError('Parent aggregation requires matching provisional development passages')
    groups: dict[str,list[int]] = collections.defaultdict(list)
    for index,row in enumerate(rows):
        groups[row['parent_id']].append(index)
    output, lex, sem = [], [], []
    for parent, indices in groups.items():
        source = rows[indices[0]]
        if any(rows[i]['meeting_id'] != source['meeting_id'] or rows[i]['country'] != source['country'] or rows[i]['machine_actor_role'] != source['machine_actor_role'] for i in indices):
            raise ValueError('A source parent crosses meeting, actor role or attribution')
        tokens = np.asarray([max(1, int(rows[i]['tokens'])) for i in indices], dtype=np.float64)
        length = int(tokens.sum())
        output.append({'parent_id':parent, 'meeting_id':source['meeting_id'], 'country':source['country'], 'role':source['machine_actor_role'],
                       'genre':source['genre'], 'length':length, 'length_bin':int(np.searchsorted(edges,length,side='right')),
                       'count':len(indices), 'passage_ids_sha256':digest(canonical([(rows[i]['id'],rows[i]['text_sha256']) for i in indices]))})
        lex.append(np.average(lexical[indices],axis=0,weights=tokens))
        sem.append(np.average(semantic[indices],axis=0,weights=tokens))
    return output, normalized(np.stack(lex)), normalized(np.stack(sem))


def blocks(meta: list[dict], keys: tuple[str,...]) -> list[np.ndarray]:
    partition = collections.defaultdict(list)
    for i,row in enumerate(meta):
        partition[tuple(row[key] for key in keys)].append(i)
    return [np.asarray(indices,dtype=int) for _,indices in sorted(partition.items(),key=lambda x:str(x[0]))]


def coverage(groups: list[np.ndarray], size: int) -> dict:
    movable = sum(len(g) for g in groups if len(g)>1)
    return {'blocks':len(groups),'singletons':sum(len(g)==1 for g in groups), 'movable':movable,
            'movable_fraction':float(movable/size) if size else 0.0}


def shuffle_within(groups: list[np.ndarray], size: int, rng: np.random.Generator) -> np.ndarray:
    assignment = np.arange(size)
    for g in groups:
        if len(g)>1:
            assignment[g] = rng.permutation(g)
    return assignment


def crossmeeting_knn(geometry: np.ndarray, meta: list[dict], k: int) -> np.ndarray:
    if len(meta) != len(geometry) or not (1 <= k < len(meta)) or not np.isfinite(geometry).all():
        raise ValueError('Invalid cross-meeting neighborhood request')
    similarity = normalized(geometry) @ normalized(geometry).T
    meetings = np.asarray([r['meeting_id'] for r in meta])
    similarity[meetings[:,None] == meetings[None,:]] = -np.inf
    if np.any(np.isfinite(similarity).sum(axis=1)<k):
        raise ValueError('Insufficient cross-meeting neighbors')
    return np.argsort(-similarity,axis=1,kind='stable')[:,:k]


def agreement(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        raise ValueError('Neighborhood shape mismatch')
    return float(np.equal(a[:,:,None],b[:,None,:]).any(axis=2).mean())


def permuted_neighbor_agreement(lex_knn: np.ndarray, sem_knn: np.ndarray, mapping: np.ndarray) -> float:
    # mapping[i] is the old semantic vector now assigned to parent i; no vectors refit.
    inverse = np.argsort(mapping)
    shuffled = inverse[sem_knn[mapping]]
    return agreement(lex_knn,shuffled)


def country_population(meta: list[dict]) -> tuple[list[int],list[dict],int]:
    history = collections.defaultdict(set)
    for row in meta:
        if row['country']:
            history[row['country']].add(row['meeting_id'])
    eligible = {country for country,ms in history.items() if len(ms)>=2}
    indices = [i for i,row in enumerate(meta) if row['country'] in eligible]
    return indices,[meta[i] for i in indices],len(eligible)


def same_country(neighbors: np.ndarray, labels: np.ndarray) -> float:
    return float((labels[:,None] == labels[neighbors]).mean())


def empirical_p(observed: float, draws: np.ndarray) -> float:
    if not len(draws) or not np.isfinite(draws).all():
        raise ValueError('Reference draws missing/nonfinite')
    return float((1+np.count_nonzero(draws >= observed-1e-12))/(len(draws)+1))


def holm(p_values: list[float]) -> list[float]:
    order = np.argsort(p_values)
    adjusted = [0.0]*len(p_values)
    maximum = 0.0
    for rank,i in enumerate(order):
        maximum = max(maximum, min(1.0, (len(p_values)-rank)*p_values[int(i)]))
        adjusted[int(i)] = float(maximum)
    return adjusted


def reference_stat(observed: float, null: np.ndarray, label: str) -> dict:
    return {'id':label,'observed':float(observed),'reference_mean':float(null.mean()),
            'reference_sd':float(null.std(ddof=1)),'reference_q05':float(np.quantile(null,.05)),
            'reference_q50':float(np.quantile(null,.50)),'reference_q95':float(np.quantile(null,.95)),
            'excess_above_reference_mean':float(observed-null.mean()), 'nominal_monte_carlo_p':empirical_p(observed,null),
            'permutations':len(null),'inference':'development-only conditional permutation; validity depends on within-block exchangeability'}


def calculate(meta: list[dict], lexical: np.ndarray, semantic: np.ndarray, plan: dict) -> tuple[dict,dict[str,np.ndarray]]:
    gates=plan['gates'];n=len(meta);count_meetings=len({r['meeting_id'] for r in meta});k=plan['neighbors']
    if n<gates['min_parent_units'] or count_meetings<gates['min_meetings']:
        raise ValueError('Not enough distinct development source groups')
    basic=blocks(meta,('meeting_id','length_bin'))
    rich=blocks(meta,('meeting_id','length_bin','role'))
    base_coverage=coverage(basic,n);rich_coverage=coverage(rich,n)
    if min(base_coverage['movable_fraction'],rich_coverage['movable_fraction']) < gates['min_movable_fraction']:
        raise ValueError('Null has insufficient exchangeable source parents')
    lexical_knn=crossmeeting_knn(lexical,meta,k)
    semantic_knn=crossmeeting_knn(semantic,meta,k)
    observed=agreement(lexical_knn,semantic_knn)
    reps=plan['permutations']
    draws=np.empty(reps);rich_draws=np.empty(reps)
    r0=np.random.default_rng(plan['seed']);r1=np.random.default_rng(plan['seed']+2)
    for i in range(reps):
        draws[i]=permuted_neighbor_agreement(lexical_knn,semantic_knn,shuffle_within(basic,n,r0))
        rich_draws[i]=permuted_neighbor_agreement(lexical_knn,semantic_knn,shuffle_within(rich,n,r1))
    primary=reference_stat(observed,draws,plan['declared_tests'][0]['id'])
    primary['rich_block_reference_q95']=float(np.quantile(rich_draws,.95))
    primary['rich_block_reference_mean']=float(rich_draws.mean())
    ci,cm,distinct=country_population(meta)
    if len(cm)<gates['min_known_repeated_country_parents'] or distinct<gates['min_repeated_countries']:
        raise ValueError('Known repeated-country source count below declared gate; no country p-value')
    second_neighbors=crossmeeting_knn(semantic[ci],cm,k)
    labels=np.asarray([r['country'] for r in cm]);country_blocks=blocks(cm,('meeting_id','length_bin'))
    country_cov=coverage(country_blocks,len(cm))
    if country_cov['movable_fraction']<gates['min_movable_fraction']:
        raise ValueError('Country reference lacks sufficient within-stratum swaps')
    observed_country=same_country(second_neighbors,labels)
    country_draws=np.empty(reps);rng=np.random.default_rng(plan['seed']+1)
    for i in range(reps):
        shuffled=labels[shuffle_within(country_blocks,len(cm),rng)]
        country_draws[i]=same_country(second_neighbors,shuffled)
    secondary=reference_stat(observed_country,country_draws,plan['declared_tests'][1]['id'])
    raw_p=[primary['nominal_monte_carlo_p'],secondary['nominal_monte_carlo_p']]
    for result,adjusted in zip([primary,secondary],holm(raw_p)):
        result['holm_adjusted_p']=adjusted
        result['conditional_reference_exceeded_at_alpha_005']=adjusted <= plan['alpha']
        result['establishes_nonrandom_diplomatic_alignment']=False
    return ({'schema':SCHEMA,'status':'completed_provisional_development_reference','source_parents':n,
            'passages_selected':sum(r['count'] for r in meta),'represented_meetings':count_meetings,
            'unit_definition':plan['unit'],'length_bin_upper_edges':plan['nuisance']['length_bin_upper_edges'],
            'nuisance_blocks':base_coverage,'richer_role_blocks':rich_coverage,'country_parent_rows':len(cm),
            'repeated_recorded_countries':distinct,'country_blocks':country_cov,
            'primary':primary,'secondary':secondary,'alpha_familywise':plan['alpha'],
            'limits':['Exploratory: primary representations and features were developed on these same observations.',
                      'Parent means aggregate technical passages from source segments; no verified speech boundaries.',
                      'Exchangeability within meeting/length (even with role sensitivity) is an assumption, not proven.',
                      'Recorded affiliation may be missing or unreliable; same-country neighbors need not share policy views.',
                      'Conditioned null tests neither establish clusters exist nor demonstrate geopolitical nonrandomness.',
                      'The planned holdout was not opened, encoded, fit, scored or inspected.']},
           {'overlap_null':draws,'overlap_role_null':rich_draws,'recorded_country_null':country_draws})


def freeze(frame: dict, checkpoint: Path, result_dir: Path, outcomes: dict, reference_plan: dict, evaluation_plan: dict) -> dict:
    heldout=[m for m in frame['meetings'] if m['split']=='holdout']
    if len(heldout)!=37 or any(m['date'] not in evaluation_plan['holdout_dates'] for m in heldout):
        raise ValueError('Held-out metadata frame differs; no text should be opened')
    if frame['holdout_state']!='reserved_not_downloaded':
        raise ValueError('Held-out content state is not unopened')
    plan_path=HERE/'plan.json';eval_path=HERE/'evaluation_plan.json';model_path=HERE.parent/'semantic_review/model-lock.json'
    lex=checkpoint/'final-analysis/strict_lsa64_k10.npz'
    sem=result_dir/'strict_semantic_pca64_k10.npz'
    raw=result_dir/'strict_semantic_raw384_k10.npz'
    # Only hashes/IDs from the frozen public metadata frame; held-out text is not loaded.
    return seal({'schema':LOCK_SCHEMA,'version':'1.0.0','holdout_state':'reserved_not_downloaded',
                 'reserved_meetings':37,'reserved_dates':evaluation_plan['holdout_dates'],
                 'reserved_identifiers_sha256':digest(canonical(sorted((m['meeting_id'],m['date']) for m in heldout))),
                 'frame_sha256':frame['sha256'], 'source_corpus_sha256':reference_plan['development_corpus_sha256'],
                 'reference_plan_sha256':digest(plan_path.read_bytes()),'evaluation_plan_sha256':digest(eval_path.read_bytes()),
                 'reference_implementation_sha256':digest(Path(__file__).read_bytes()),
                 'semantic_comparison_implementation_sha256':digest((HERE.parent/'semantic_review/compare.py').read_bytes()),
                 'semantic_encoder_implementation_sha256':digest((HERE.parent/'semantic_review/encoder.py').read_bytes()),
                 'machine_review_implementation_sha256':digest((HERE.parent/'machine_review/review.py').read_bytes()),
                 'semantic_model_lock_sha256':digest(model_path.read_bytes()),
                 'saved_lexical_model_sha256':digest(lex.read_bytes()),
                 'saved_semantic_pca_model_sha256':digest(sem.read_bytes()),
                 'saved_raw_semantic_sha256':digest(raw.read_bytes()),
                 'reference_aggregate_sha256':digest(canonical(outcomes)),
                 'development_excess_overlap':outcomes['primary']['excess_above_reference_mean'],
                 'replication_floor_excess':max(0.0,outcomes['primary']['excess_above_reference_mean']*0.5),
                 'predeclared_eligibility_gates':evaluation_plan['replication_gate'],
                 'fixed_controls_and_metrics':evaluation_plan['transforms'],
                 'no_holdout_acquisition_performed':True,'human_review_state':'provisional_only',
                 'evaluation_executed':False,'authorization_required':evaluation_plan['authorization_required'],
                 'prohibitions':evaluation_plan['prohibited']})


def run(checkpoint: Path,result_dir: Path,out: Path) -> dict:
    plan=read(HERE/'plan.json');evaluation=read(HERE/'evaluation_plan.json');validate_plan(plan,evaluation)
    if out.exists():raise FileExistsError('Choose a new output directory; no overwriting')
    with offline() as attempts:
        corpus,allrows,_=load_checkpoint(checkpoint)
        if corpus['sha256']!=plan['development_corpus_sha256'] or corpus['frame']['sha256']!=plan['development_frame_sha256']:
            raise ValueError('Original development source/frame mismatch')
        if len([m for m in corpus['frame']['meetings'] if m['split']=='holdout'])!=37:
            raise ValueError('Reserved metadata frame changed')
        checked=verify_saved_results(result_dir)
        if read(result_dir/'input-lock.json')['model_lock']!=read(HERE.parent/'semantic_review/model-lock.json'):
            raise ValueError('Pinned model lock mismatch')
        overrides=contextual_override_audit(checkpoint,corpus,allrows)
        if overrides['strict_membership_changes'] != 0:
            raise ValueError('Contextual machine overrides alter the frozen strict selection; freeze a separate sensitivity protocol')
        baseline=[r for r in allrows if r['baseline_eligible']]
        strict=[r for r in allrows if r['strict_eligible']]
        if (len(baseline),len(strict))!=(2057,1641):raise ValueError('Provisional population altered')
        E,_=load_cache(result_dir/'embedding-cache',baseline,read(HERE.parent/'semantic_review/model-lock.json'))
        by_id={r['id']:i for i,r in enumerate(baseline)}
        sem=E[[by_id[r['id']] for r in strict]]
        with np.load(result_dir/'strict_semantic_raw384_k10.npz',allow_pickle=False) as archive:
            if archive['ids'].tolist()!=[r['id'] for r in strict] or archive['text_hashes'].tolist()!=[r['text_sha256'] for r in strict]:
                raise ValueError('Saved semantic source identity differs')
            if not np.array_equal(normalized(sem.astype(np.float64)),archive['geometry']):
                raise ValueError('Semantic cache and saved raw geometry differ')
        lexical=load_lexical(checkpoint,'strict_lsa64_k10',strict)['normalized_lsa']
        meta,L,S=parents(strict,lexical,sem,plan['nuisance']['length_bin_upper_edges'])
        reference,draws=calculate(meta,L,S,plan)
        reference.update({'development_corpus_sha256':corpus['sha256'],'frame_sha256':corpus['frame']['sha256'],
                          'model_revision':plan['semantic_revision'],'heldout_transcripts_opened':0,
                          'human_confirmations':0,'plan_sha256':digest((HERE/'plan.json').read_bytes()),
                          'semantic_saved_manifest_sha256':digest((result_dir/'SHA256.json').read_bytes()),
                          'parent_identity_digest':digest(canonical(meta)),
                          'contextual_override_audit':overrides})
        sealed_reference=seal(reference)
        heldout_lock=freeze(corpus['frame'],checkpoint,result_dir,reference,plan,evaluation)
        verify_seal(heldout_lock,LOCK_SCHEMA)
        if attempts:raise RuntimeError('Network attempted during reference execution')
    out.mkdir(parents=True)
    save(out/'reference.json',sealed_reference)
    save(out/'evaluation-lock.json',heldout_lock)
    save(out/'plans.json',{'development':plan,'evaluation':evaluation})
    if any(np.asarray(x).dtype.hasobject for x in draws.values()):raise ValueError('Unsafe numeric archive')
    np.savez_compressed(out/'reference-draws.npz',**draws)
    return {'status':'PASS','development_parent_units':len(meta),'reference_p':reference['primary']['holm_adjusted_p'],
            'country_p':reference['secondary']['holm_adjusted_p'],'holdout_transcripts_opened':0,
            'protocol_sha256':heldout_lock['sha256']}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkpoint',type=Path)
    parser.add_argument('semantic_results',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    print(json.dumps(run(args.checkpoint,args.semantic_results,args.output),indent=2))


if __name__=='__main__':main()
