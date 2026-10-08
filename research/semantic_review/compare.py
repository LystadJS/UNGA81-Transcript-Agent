"""Source-bound comparison with the saved lexical baseline; no holdout loader."""
from __future__ import annotations
import argparse, collections, csv, importlib.metadata, json, platform, resource, sys, time, warnings
from pathlib import Path
import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer, TfidfTransformer
from sklearn.metrics import adjusted_rand_score, adjusted_mutual_info_score, silhouette_score
from threadpoolctl import threadpool_limits
from encoder import (LocalEncoder, canonical, check_rows, load_cache, normalized, offline,
                     save_cache, sha, write_json)

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'machine_review'))
import review as previous_review
from analysis import weights


def csv_file(path: Path, rows: list[dict]) -> None:
    if rows:
        with path.open('x', newline='', encoding='utf8') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def arrays(path: Path, **values) -> None:
    if any(np.asarray(x).dtype.hasobject for x in values.values()):
        raise ValueError('Object arrays prohibited')
    np.savez_compressed(path, **values)


def load_checkpoint(root: Path) -> tuple[dict, list[dict], dict]:
    manifest = json.loads((root / 'SHA256.json').read_text())
    for name, h in manifest.items():
        path = root / name
        if not path.resolve().is_relative_to(root.resolve()) or not path.is_file() or sha(path.read_bytes()) != h:
            raise ValueError('Checkpoint integrity failure: ' + name)
    corpus = previous_review.read_verified(root / 'original/corpus.json')
    if corpus['sha256'] != 'e8fb980cf638e2aef39d0ca3564836c6120201a059e806ccaaee3fd5cc4f593e':
        raise ValueError('This comparison requires the frozen October development corpus')
    ledger_path = root / 'final-review/machine-review.json'
    if sha(ledger_path.read_bytes()) != 'bc2ebf0f0072c31b3a4a0a66b7dc2a999699c2739baa27ca1cbcac0843da79c8':
        raise ValueError('Machine review changed; freeze a new comparison explicitly')
    ledger = json.loads(ledger_path.read_text())
    previous_review.validate_ledger(corpus, ledger)
    rows = previous_review.selections(corpus, ledger)
    provisional = json.loads((root / 'final-review/provisional-corpus.json').read_text())
    if rows != provisional['records'] or any(r['human_confirmed'] for r in rows):
        raise ValueError('Provisional population differs or falsely claims human review')
    if any(r['split'] != 'development' for r in rows) or corpus['frame']['holdout_state'] != 'reserved_not_downloaded':
        raise ValueError('Invalid split or holdout state')
    return corpus, rows, manifest


def load_lexical(root: Path, name: str, rows: list[dict]) -> dict:
    with np.load(root / 'final-analysis' / (name + '.npz'), allow_pickle=False) as archive:
        saved = {k: v.copy() for k, v in archive.items()}
    if saved['ids'].tolist() != [r['id'] for r in rows]:
        raise ValueError('Lexical reference usable IDs/order differ; comparison withheld')
    if not np.isfinite(saved['normalized_lsa']).all():
        raise ValueError('Invalid lexical geometry')
    return saved


def fit_geometry(E: np.ndarray, dimensions: int | None) -> tuple[np.ndarray, dict]:
    if E.ndim != 2 or not np.isfinite(E).all():
        raise ValueError('Invalid embedding matrix')
    if dimensions is None:
        return normalized(E.astype(np.float64)), {}
    if not 2 <= dimensions < min(E.shape):
        raise ValueError('Insufficient rank for requested PCA; no dimension clamping')
    model = PCA(n_components=dimensions, svd_solver='full')
    raw = model.fit_transform(E.astype(np.float64))
    return normalized(raw), {'mean': model.mean_, 'components': model.components_,
                             'explained_variance_ratio': model.explained_variance_ratio_}


def partition(Z: np.ndarray, method: str, k: int, seed: int) -> tuple[np.ndarray, dict]:
    if not 2 <= k < len(Z):
        raise ValueError('Unsupported cluster count')
    if method == 'kmeans':
        model = KMeans(n_clusters=k, n_init=20, max_iter=300, random_state=seed, algorithm='lloyd')
        labels = model.fit_predict(Z)
        extra = {'centers': model.cluster_centers_, 'iterations': np.asarray(model.n_iter_)}
    elif method == 'ward':
        labels = AgglomerativeClustering(n_clusters=k, linkage='ward').fit_predict(Z)
        extra = {}
    else:
        raise ValueError('Unsupported partition method')
    if len(np.unique(labels)) != k:
        raise ValueError('Collapsed partition')
    return labels, extra


def neighbors(Z: np.ndarray, rows: list[dict], max_k: int, exclusion: str = 'self') -> np.ndarray:
    if max_k >= len(rows) or len(rows) != len(Z) or exclusion not in {'self','parent','meeting'}:
        raise ValueError('Invalid neighborhood request')
    S = normalized(Z) @ normalized(Z).T
    np.fill_diagonal(S, -np.inf)
    if exclusion != 'self':
        key = {'parent': 'parent_id', 'meeting': 'meeting_id'}[exclusion]
        group = np.array([r[key] for r in rows])
        S[group[:, None] == group[None, :]] = -np.inf
    if (np.isfinite(S).sum(axis=1) < max_k).any():
        raise ValueError('Too few eligible neighbors; comparison withheld')
    # Stable source-order tie break, not a random choice among duplicates.
    return np.argsort(-S, axis=1, kind='stable')[:, :max_k]


def overlap(A: np.ndarray, B: np.ndarray, k: int) -> np.ndarray:
    if A.shape != B.shape or not 1 <= k <= A.shape[1]:
        raise ValueError('Unpaired neighbor lists')
    return np.array([len(set(a[:k]) & set(b[:k])) / k for a,b in zip(A,B)])


def metrics(Z: np.ndarray, labels: np.ndarray, rows: list[dict]) -> dict:
    return {'usable': len(rows), 'clusters': int(len(np.unique(labels))),
        'silhouette': float(silhouette_score(Z, labels)),
        'meeting_AMI': float(adjusted_mutual_info_score([r['meeting_id'] for r in rows], labels)),
        'genre_AMI': float(adjusted_mutual_info_score([r['genre'] for r in rows], labels))}


def pair(left: str, right: str, a: dict, b: dict) -> dict:
    if [(r['id'], r['text_sha256']) for r in a['rows']] != [(r['id'], r['text_sha256']) for r in b['rows']]:
        return {'left': left, 'right': right, 'status': 'withheld', 'reason': 'Different IDs, order or text hashes'}
    return {'left': left, 'right': right, 'status': 'paired', 'denominator': len(a['rows']),
            'ari': float(adjusted_rand_score(a['labels'], b['labels']))}


def vectorize_probes(texts: list[str], saved: dict, prior_plan: dict) -> tuple[np.ndarray, list[int]]:
    opts = dict(prior_plan['vectorizer'])
    opts['ngram_range'] = tuple(opts['ngram_range'])
    v = TfidfVectorizer(**opts, vocabulary={term: i for i, term in enumerate(saved['terms'])})
    # Public idf_ setter initializes the transformer without refitting any text.
    v.idf_ = saved['idf']
    X = v.transform(texts)
    raw = np.asarray(X @ saved['svd_components'].T)
    norm = np.linalg.norm(raw, axis=1, keepdims=True)
    return raw / np.maximum(norm, 1e-12), np.flatnonzero(norm[:,0] < 1e-12).tolist()


def run(checkpoint: Path, model_dir: Path, out: Path, cache: Path | None = None) -> dict:
    started = time.perf_counter()
    plan = json.loads((ROOT / 'plan.json').read_text())
    lock = json.loads((ROOT / 'model-lock.json').read_text())
    if out.exists():
        raise FileExistsError('Use a new output directory; original files are never overwritten')
    out.mkdir(parents=True)
    write_json(out / 'plan.json', plan)
    write_json(out / 'probes-plan.json', json.loads((ROOT / 'probes.json').read_text()))
    corpus, allrows, manifest = load_checkpoint(checkpoint)
    rows = [r for r in allrows if r['baseline_eligible']]
    check_rows(rows)
    if len(rows) != 2057:
        raise ValueError('Frozen baseline population changed')
    row_index = {r['id']: i for i,r in enumerate(rows)}
    encoder = LocalEncoder(model_dir, lock)
    if cache is None:
        encode_start = time.perf_counter()
        E, chunks, audit = encoder.encode(rows)
        cache = out / 'embedding-cache'
        save_cache(cache, rows, E, chunks, audit, lock)
        encode_seconds = time.perf_counter() - encode_start
    else:
        encode_seconds = None
    E, cache_manifest = load_cache(cache, rows, lock)
    archive_provenance = {n: manifest[n] for n in manifest if n.startswith('final-analysis/') or n in ['original/corpus.json','final-review/machine-review.json','final-review/provisional-corpus.json']}
    write_json(out / 'input-lock.json', {'source_corpus_sha256': corpus['sha256'],
        'model_lock': lock, 'selected_ids_sha256': sha(canonical([(r['id'],r['text_sha256']) for r in rows])),
        'checkpoint_files': archive_provenance, 'cache_manifest_sha256': sha((cache / 'manifest.json').read_bytes())})
    fitted, fit_rows, comparisons, refits, display_rows, compositions = {}, [], [], [], [], []
    for spec in plan['settings']:
        name = spec['id']; selected = [r for r in rows if r[spec['population'] + '_eligible']]
        try:
            lexical_name = spec['population'] + '_lsa' + str(spec['dimensions'] or 64) + ('_ward10' if spec['method']=='ward' else '_k10')
            saved = load_lexical(checkpoint, lexical_name, selected)
            with warnings.catch_warnings(record=True) as caught:
                Z, transform = fit_geometry(E[[row_index[r['id']] for r in selected]], spec['dimensions'])
                labels, model = partition(Z, spec['method'], spec['k'], plan['seed'])
            # An additional centered PCA is only a display of the fitted geometry.
            display = PCA(n_components=2, svd_solver='full').fit_transform(Z)
            fitted[name] = {'rows': selected, 'Z': Z, 'labels': labels}
            result = {**spec, 'status': 'fitted', **metrics(Z, labels, selected),
                'retained_variance': float(transform['explained_variance_ratio'].sum()) if transform else None,
                'warnings': [str(w.message) for w in caught]}
            fit_rows.append(result)
            arrays(out / (name + '.npz'), ids=np.array([r['id'] for r in selected]),
                   text_hashes=np.array([r['text_sha256'] for r in selected]), labels=labels, geometry=Z,
                   display=display, **{'pca_' + k: v for k,v in transform.items()}, **model)
            display_p = np.linalg.norm(display[:,None,:]-display[None,:,:],axis=2)
            np.fill_diagonal(display_p, np.inf)
            near2 = np.argsort(display_p, axis=1, kind='stable')[:, :15]
            near = neighbors(Z, selected, 15)
            display_rows.append({'setting': name, 'neighbor_recall15': float(overlap(near,near2,15).mean()),
                'distance_spearman': float(spearmanr(pdist(Z),pdist(display)).statistic),
                'interpretation': 'Display distortion diagnostic, not evidence for clustering or policy alignment'})
            for scheme in plan['summary_weights']:
                w = weights(selected, scheme)
                for label in range(spec['k']):
                    compositions.append({'setting':name,'scheme':scheme,'cluster':label+1,
                        'passages':int((labels==label).sum()),'selected':len(selected),
                        'share':float(w[labels==label].sum())})
            lex = {'rows': selected, 'Z': saved['normalized_lsa'], 'labels': saved['labels']}
            comparisons.append(pair(lexical_name, name, lex, fitted[name]))
            print('FITTED', name, len(selected), flush=True)
        except Exception as exc:
            fit_rows.append({**spec, 'status': 'failed', 'error': str(exc)})
    strict_names = [n for n in fitted if n.startswith('strict_')]
    for i,left in enumerate(strict_names):
        for right in strict_names[i+1:]:
            comparisons.append(pair(left,right,fitted[left],fitted[right]))
    primary = fitted.get(plan['primary'])
    neighborhood_rows, row_scores, source_pairs = [], [], []
    probes_results = []
    nuisance = []
    if primary:
        selected = primary['rows']
        saved = load_lexical(checkpoint, 'strict_lsa64_k10', selected)
        L = saved['normalized_lsa']; R = E[[row_index[r['id']] for r in selected]].astype(np.float64)
        representations = {'lexical_lsa64': L, 'semantic_raw384': R, 'semantic_pca64': primary['Z']}
        for exclusion in ['self','parent','meeting']:
            near = {key: neighbors(value,selected,max(plan['neighbors']),exclusion) for key,value in representations.items()}
            for left,right in [('lexical_lsa64','semantic_raw384'),('lexical_lsa64','semantic_pca64'),('semantic_raw384','semantic_pca64')]:
                for k in plan['neighbors']:
                    values = overlap(near[left],near[right],k)
                    neighborhood_rows.append({'left':left,'right':right,'exclusion':exclusion,'k':k,'n':len(values),
                        'mean_overlap':float(values.mean()),'median_overlap':float(np.median(values))})
            if exclusion == 'self':
                for name, indices in near.items():
                    nuisance.append({'representation':name,'k':15,'same_meeting_neighbor_share':float(np.mean([[selected[i]['meeting_id']==selected[j]['meeting_id'] for j in a[:15]] for i,a in enumerate(indices)])),
                        'same_parent_neighbor_share':float(np.mean([[selected[i]['parent_id']==selected[j]['parent_id'] for j in a[:15]] for i,a in enumerate(indices)]))})
            if exclusion == 'meeting':
                scores = overlap(near['lexical_lsa64'], near['semantic_raw384'], 15)
                row_scores = [{'id':r['id'],'meeting_id':r['meeting_id'],'neighbor_overlap15':float(s)} for r,s in zip(selected,scores)]
                simL,simR = L @ L.T, R @ R.T
                for i,r in enumerate(selected):
                    j = int(near['semantic_raw384'][i,0])
                    eligible = np.array([x['meeting_id'] != r['meeting_id'] for x in selected])
                    rank = int(np.sum((simL[i] > simL[i,j]) & eligible) + 1)
                    source_pairs.append({'id':r['id'],'neighbor_id':selected[j]['id'],'source_url':r['source_url'],
                        'neighbor_source_url':selected[j]['source_url'],'meeting_id':r['meeting_id'],
                        'neighbor_meeting_id':selected[j]['meeting_id'],'text_sha256':r['text_sha256'],
                        'neighbor_text_sha256':selected[j]['text_sha256'],'semantic_cosine':float(simR[i,j]),
                        'lexical_cosine':float(simL[i,j]),'lexical_rank_of_semantic_neighbor':rank,
                        'text':r['text'],'neighbor_text':selected[j]['text']})
        old_refits = {r['omitted_meeting']:r for r in json.loads((checkpoint/'final-analysis/refits.json').read_text())}
        for meeting in sorted({r['meeting_id'] for r in selected}):
            mask = np.array([r['meeting_id'] != meeting for r in selected])
            try:
                Z,_ = fit_geometry(R[mask],64)
                labels,_ = partition(Z,'kmeans',10,plan['seed'])
                refits.append({'omitted_meeting':meeting,'status':'fitted','overlap_passages':int(mask.sum()),
                    'semantic_overlap_ari':float(adjusted_rand_score(primary['labels'][mask],labels)),
                    'saved_lexical_overlap_ari':old_refits[meeting]['overlap_ari'],
                    'interpretation':'Paired omission schedule; overlapping training observations, not held-out performance'})
                print('REFIT',meeting,flush=True)
            except Exception as exc:
                refits.append({'omitted_meeting':meeting,'status':'failed','error':str(exc)})
        probes = json.loads((ROOT/'probes.json').read_text());probe_rows=[]
        roles = ['anchor','paraphrase','opposite','boilerplate']
        for p in probes:
            for role in roles:
                text=p[role];probe_rows.append({'id':p['id']+':'+role,'text':text,'text_sha256':sha(text.encode()),'split':'development','language':'en'})
        PE,_,_ = encoder.encode(probe_rows)
        LX,zero = vectorize_probes([r['text'] for r in probe_rows],saved,json.loads((checkpoint/'final-analysis/plan.json').read_text()))
        for i,p in enumerate(probes):
            results={'probe':p['id'],'scope':'authored synthetic development diagnostic; not independent test accuracy'}
            for j,role in enumerate(roles[1:],1):
                results['semantic_'+role]=float(PE[4*i] @ PE[4*i+j])
                results['lexical_'+role]=None if 4*i in zero or 4*i+j in zero else float(LX[4*i] @ LX[4*i+j])
            probes_results.append(results)
        arrays(out/'probe-embeddings.npz',ids=np.array([r['id'] for r in probe_rows]),embeddings=PE,lexical_lsa=LX)
    write_json(out/'nuisance-diagnostics.json',nuisance)
    write_json(out/'fits.json',fit_rows);write_json(out/'comparisons.json',comparisons)
    write_json(out/'neighborhoods.json',neighborhood_rows);write_json(out/'refits.json',refits)
    write_json(out/'display-diagnostics.json',display_rows);write_json(out/'probe-results.json',probes_results)
    csv_file(out/'composition.csv',compositions);csv_file(out/'crossmeeting-neighbors.csv',source_pairs)
    csv_file(out/'neighbor-overlap.csv',row_scores)
    successes=[r for r in refits if r['status']=='fitted']
    summary={'schema':'un.semantic-comparison-result.v1','machine_only':True,'human_confirmations':0,
        'holdout_transcripts_opened':0,'source_corpus_sha256':corpus['sha256'],
        'model_revision':lock['revision'],'cache_audit':cache_manifest['audit'],
        'population_counts':{p:sum(r[p+'_eligible'] for r in rows) for p in ['strict','inclusive','baseline']},
        'fits_planned':len(plan['settings']),'fits_successful':sum(r['status']=='fitted' for r in fit_rows),
        'refits_planned':16,'refits_successful':len(successes),'embedding_seconds':encode_seconds,
        'semantic_refit_median_ari':float(np.median([r['semantic_overlap_ari'] for r in successes])) if successes else None,
        'elapsed_seconds':time.perf_counter()-started,'peak_process_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        'implementation_hashes':{p.name:sha(p.read_bytes()) for p in ROOT.iterdir() if p.suffix in {'.py','.json','.txt'} and not p.name.startswith('test_')},
        'python':platform.python_version(),'packages':{p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','onnxruntime','tokenizers','threadpoolctl']},
        'limits':'Research comparison only. No stance, coalition, weighted refit, formal null test, or held-out replication.'}
    write_json(out/'summary.json',summary)
    write_json(out/'SHA256.json',{p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file()})
    return summary


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkpoint',type=Path);parser.add_argument('model',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--cache',type=Path)
    args=parser.parse_args()
    with offline() as attempts, threadpool_limits(limits=1):
        summary=run(args.checkpoint,args.model,args.output,args.cache)
        if attempts:raise RuntimeError('A network connection was attempted')
    print(json.dumps(summary,indent=2))
    if summary['fits_successful'] != summary['fits_planned'] or summary['refits_successful'] != summary['refits_planned']:
        raise SystemExit('Incomplete execution; inspect the preserved failed-fit/refit records')
