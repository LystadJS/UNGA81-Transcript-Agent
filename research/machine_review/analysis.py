#!/usr/bin/env python3
"""Offline lexical exploration of an explicitly provisional development population."""
from __future__ import annotations
import argparse, collections, hashlib, json, platform, time, warnings
from pathlib import Path
import numpy as np
import scipy, sklearn
from scipy import sparse
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.decomposition import TruncatedSVD, NMF
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics import adjusted_rand_score, adjusted_mutual_info_score, silhouette_score
from sklearn.preprocessing import normalize
from threadpoolctl import threadpool_limits
from review import read_verified, validate_ledger, selections, digest, dump, write_csv

VERSION = 'provisional-lexical-1.0.0'
STOP = sorted((set(ENGLISH_STOP_WORDS) - {'no','not','nor','never'}) | {'thank','thanks','mr','madam','chair','president','vice','excellency','excellencies','distinguished','delegates'})
PLAN = {'schema':'un.machine-exploration-plan.v1','fit_split':'development','review_status':'machine_only_provisional',
        'holdout_access':False,'fit_weighting':'equal_passage','max_observations':5000,
        'primary':'strict_lsa64_k10','seed':271828,
        'vectorizer':{'ngram_range':[1,2],'min_df':3,'max_df':0.95,'max_features':10000,'sublinear_tf':True,'norm':'l2','strip_accents':'unicode','stop_words':STOP},
        'settings':[{'id':'strict_lsa32_k6','population':'strict','dimensions':32,'k':6,'method':'kmeans'},
                    {'id':'strict_lsa32_k10','population':'strict','dimensions':32,'k':10,'method':'kmeans'},
                    {'id':'strict_lsa64_k10','population':'strict','dimensions':64,'k':10,'method':'kmeans'},
                    {'id':'strict_lsa64_ward10','population':'strict','dimensions':64,'k':10,'method':'ward'},
                    {'id':'inclusive_lsa64_k10','population':'inclusive','dimensions':64,'k':10,'method':'kmeans'},
                    {'id':'baseline_lsa64_k10','population':'baseline','dimensions':64,'k':10,'method':'kmeans'}],
        'nmf_ranks':[8,12],'refits':'leave each represented strict-development meeting out once; refit TF-IDF and SVD; compare overlapping training observations only',
        'summary_weights':['equal_passage','equal_observed_parent','equal_meeting'],
        'interpretation':'No country alliance, stance, independent replication, calibrated significance or complete-speech claim. No sampling. Display coordinates do not determine clusters.'}

def save_arrays(path: Path, **arrays: object) -> None:
    """Store numeric and Unicode arrays only; loading never requires pickle."""
    clean = {}
    for name, value in arrays.items():
        array = np.asarray(value)
        if array.dtype.hasobject:
            if not all(isinstance(x, str) for x in array.flat):
                raise ValueError('Object arrays other than strings are prohibited')
            array = array.astype(str)
        clean[name] = array
    np.savez_compressed(path, **clean)


def vectorizer(plan: dict) -> TfidfVectorizer:
    opts=dict(plan['vectorizer']);opts['ngram_range']=tuple(opts['ngram_range'])
    return TfidfVectorizer(**opts, dtype=np.float64)

def select_rows(allrows: list[dict], population: str) -> list[dict]:
    if population not in {'strict','inclusive','baseline'}:
        raise ValueError('Unknown population')
    return [r for r in allrows if r[population+'_eligible']]

def fit(rows: list[dict], spec: dict, plan: dict) -> dict:
    if any(r.get('split') != 'development' for r in rows):
        raise ValueError('Only explicitly declared development observations may enter a fit')
    if not 20 <= len(rows) <= plan['max_observations']:
        raise ValueError('Outside offline research envelope; no truncation or silent sampling')
    v=vectorizer(plan);X=v.fit_transform([r['text'] for r in rows])
    eligible=np.asarray(X.getnnz(axis=1)>0);usable=[r for r,ok in zip(rows,eligible) if ok];X=X[eligible]
    d=spec['dimensions']
    if min(X.shape)<=d or len(usable)<=spec['k']:
        raise ValueError('Insufficient usable rank/population for declared setting')
    svd=TruncatedSVD(n_components=d,algorithm='randomized',n_iter=7,random_state=plan['seed'])
    raw=svd.fit_transform(X);Z=normalize(raw)
    if spec['method']=='ward':
        model=AgglomerativeClustering(n_clusters=spec['k'],linkage='ward');labels=model.fit_predict(Z)
    else:
        model=KMeans(n_clusters=spec['k'],n_init=20,max_iter=300,random_state=plan['seed'],algorithm='lloyd');labels=model.fit_predict(Z)
    if not np.isfinite(Z).all() or len(np.unique(labels))!=spec['k']:
        raise ValueError('Nonfinite geometry or collapsed partition')
    return {'rows':usable,'selected':rows,'X':X,'v':v,'svd':svd,'raw':raw,'Z':Z,'model':model,'labels':labels,'spec':spec}

def weights(rows: list[dict], scheme: str) -> np.ndarray:
    if scheme=='equal_passage':return np.repeat(1/len(rows),len(rows))
    key={'equal_observed_parent':'parent_id','equal_meeting':'meeting_id'}[scheme]
    counts=collections.Counter(r[key] for r in rows)
    return np.array([1/(len(counts)*counts[r[key]]) for r in rows])

def shares(f: dict) -> list[dict]:
    # Include all selected rows, including zero-vector rows, in each denominator.
    lookup={r['id']:int(l)+1 for r,l in zip(f['rows'],f['labels'])};out=[]
    for scheme in PLAN['summary_weights']:
        w=weights(f['selected'],scheme)
        for label in ['not_fitted']+list(range(1,f['spec']['k']+1)):
            mask=np.array([lookup.get(r['id'],'not_fitted')==label for r in f['selected']])
            out.append({'setting':f['spec']['id'],'weighting':scheme,'cluster':label,'selected_passages':len(mask),'passages':int(mask.sum()),'share':float(w[mask].sum())})
    return out

def execute(corpus_path: Path, review_path: Path, out: Path, do_refits: bool=True) -> dict:
    started=time.time();corpus=read_verified(corpus_path);ledger=json.loads(review_path.read_text());validate_ledger(corpus,ledger)
    allrows=selections(corpus,ledger)
    if out.exists():raise FileExistsError('Use a new analysis directory')
    out.mkdir(parents=True);dump(out/'plan.json',PLAN)
    if any(r['split']!='development' for r in allrows):raise ValueError('Holdout cannot enter exploration')
    provenance={'source_corpus_sha256':corpus['sha256'],'review_file_sha256':digest(review_path.read_bytes()),
                'plan_sha256':digest((out/'plan.json').read_bytes()),'implementation_sha256':digest(Path(__file__).read_bytes()),
                'source_count':len(corpus['parents']),'partition_count':len(allrows),'python':platform.python_version(),
                'numpy':np.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__,'seed':PLAN['seed'],
                'threads':1,'holdout_transcripts_opened':0,'human_confirmations':0}
    dump(out/'provenance.json',provenance)
    fitted={};fits=[];assignments=[];compositions=[];pairwise=[];topics=[];profiles=[];refits=[]
    for spec in PLAN['settings']:
        print('FIT',spec['id'],flush=True)
        try:
            with warnings.catch_warnings(record=True) as caught:
                f=fit(select_rows(allrows,spec['population']),spec,PLAN)
            fitted[spec['id']]=f
            labels=f['labels'];rs=f['rows'];Z=f['Z']
            fits.append({**spec,'status':'fitted','selected':len(f['selected']),'usable':len(rs),
                         'not_fitted':len(f['selected'])-len(rs),'features':f['X'].shape[1],
                         'retained_variance':float(f['svd'].explained_variance_ratio_.sum()),
                         'silhouette':float(silhouette_score(Z,labels)),
                         'meeting_AMI':float(adjusted_mutual_info_score([r['meeting_id'] for r in rs],labels)),
                         'genre_AMI':float(adjusted_mutual_info_score([r['genre'] for r in rs],labels)),
                         'warnings':[str(w.message) for w in caught]})
            assignments.extend({'setting':spec['id'],'id':r['id'],'text_sha256':r['text_sha256'],'parent_id':r['parent_id'],
                                'meeting_id':r['meeting_id'],'country':r['country'],'actor_role':r['machine_actor_role'],
                                'cluster':int(l)+1,'x':float(z[0]),'y':float(z[1])} for r,l,z in zip(rs,labels,f['raw']))
            compositions.extend(shares(f))
            save_arrays(out/(spec['id']+'.npz'),ids=np.array([r['id'] for r in rs]),labels=labels,
                                svd_components=f['svd'].components_,svd_raw=f['raw'],normalized_lsa=Z,
                                idf=f['v'].idf_,terms=f['v'].get_feature_names_out())
        except Exception as e:
            fits.append({**spec,'status':'failed','error':str(e)})
    for i,left in enumerate(fitted):
        for right in list(fitted)[i+1:]:
            lf,rf=fitted[left],fitted[right];rl={r['id']:(r['text_sha256'],int(l)) for r,l in zip(rf['rows'],rf['labels'])}
            shared=[(r,int(l)) for r,l in zip(lf['rows'],lf['labels']) if r['id'] in rl and rl[r['id']][0]==r['text_sha256']]
            pairwise.append({'left':left,'right':right,'comparison':'same_population' if lf['spec']['population']==rf['spec']['population'] else 'changed_population_common_ids_only',
                             'shared_usable':len(shared),'left_usable':len(lf['rows']),'right_usable':len(rf['rows']),
                             'ari':float(adjusted_rand_score([l for _,l in shared],[rl[r['id']][1] for r,_ in shared])) if len(shared)>1 else None})
    primary=fitted.get(PLAN['primary'])
    if primary:
        X=primary['X'];rs=primary['rows'];terms=primary['v'].get_feature_names_out()
        for rank in PLAN['nmf_ranks']:
            try:
                with warnings.catch_warnings(record=True) as caught:
                    model=NMF(n_components=rank,init='nndsvda',random_state=PLAN['seed'],max_iter=600,tol=1e-4,solver='cd')
                    W=model.fit_transform(X);H=model.components_
                # Resolve arbitrary component scale before making composition summaries.
                mass=W*H.sum(axis=1)[None,:];den=mass.sum(axis=1);proportions=np.divide(mass,den[:,None],out=np.zeros_like(mass),where=den[:,None]>0)
                save_arrays(out/f'nmf{rank}.npz',ids=np.array([r['id'] for r in rs]),W=W,H=H,component_shares=proportions,terms=terms)
                for j in range(rank):
                    top=np.argsort(H[j])[::-1][:12];indices=np.argsort(proportions[:,j])[::-1]
                    examples=[];seen=set()
                    for i in indices:
                        r=rs[i]
                        if r['parent_id'] in seen:continue
                        seen.add(r['parent_id']);examples.append({'id':r['id'],'parent_id':r['parent_id'],'country':r['country'],'actor_role':r['machine_actor_role'],
                            'meeting_id':r['meeting_id'],'source_url':r['source_url'],'json_pointer':r['json_pointer'],'parent_start':r['parent_start'],'parent_end':r['parent_end'],
                            'text_sha256':r['text_sha256'],'text':r['text'],'share':float(proportions[i,j])})
                        if len(examples)==4:break
                    topics.append({'rank':rank,'component':j+1,'terms':terms[top].tolist(),'mean_component_mass_share':float(proportions[:,j].mean()),
                                   'examples':examples,'converged':model.n_iter_<600,'iterations':model.n_iter_,
                                   'relative_residual':float(model.reconstruction_err_/np.sqrt(X.multiply(X).sum())),
                                   'warnings':[str(w.message) for w in caught]})
                for mid in sorted({r['meeting_id'] for r in rs}):
                    idx=np.array([r['meeting_id']==mid for r in rs])
                    for j in range(rank):profiles.append({'rank':rank,'meeting_id':mid,'component':j+1,'passages':int(idx.sum()),'mean_component_mass_share':float(proportions[idx,j].mean())})
            except Exception as e:
                topics.append({'rank':rank,'status':'failed','error':str(e)})
        if do_refits:
            for mid in sorted({r['meeting_id'] for r in rs}):
                print('OMIT DEVELOPMENT',mid,flush=True)
                kept=[r for r in primary['selected'] if r['meeting_id']!=mid]
                try:
                    with warnings.catch_warnings(record=True) as caught:
                        refit=fit(kept,primary['spec'],PLAN)
                    original={r['id']:int(l) for r,l in zip(rs,primary['labels'])}
                    overlap=[i for i,r in enumerate(refit['rows']) if r['id'] in original]
                    refits.append({'omitted_meeting':mid,'status':'fitted','overlap_passages':len(overlap),'omitted_passages':len(primary['selected'])-len(kept),
                                   'overlap_ari':float(adjusted_rand_score([original[refit['rows'][i]['id']] for i in overlap],refit['labels'][overlap])),
                                   'feature_count':refit['X'].shape[1],'warnings':[str(w.message) for w in caught]})
                except Exception as e:refits.append({'omitted_meeting':mid,'status':'failed','error':str(e)})
    for name,obj in [('fits',fits),('pairwise',pairwise),('topics',topics),('refits',refits)]:dump(out/(name+'.json'),obj)
    if assignments:write_csv(out/'assignments.csv',assignments,list(assignments[0]))
    if compositions:write_csv(out/'composition.csv',compositions,list(compositions[0]))
    if profiles:write_csv(out/'meeting-components.csv',profiles,list(profiles[0]))
    vals=[r['overlap_ari'] for r in refits if r['status']=='fitted']
    summary={'schema':'un.machine-exploration-summary.v1','engine':VERSION,'population_status':'machine_only_provisional',
             'planned_fits':len(PLAN['settings']),'successful_fits':sum(f['status']=='fitted' for f in fits),'failed_fits':sum(f['status']=='failed' for f in fits),
             'nmf_ranks_planned':PLAN['nmf_ranks'],'nmf_successful_ranks':sorted({t['rank'] for t in topics if 'component' in t}),
             'strict_passages':sum(r['strict_eligible'] for r in allrows),'inclusive_passages':sum(r['inclusive_eligible'] for r in allrows),
             'baseline_passages':sum(r['baseline_eligible'] for r in allrows),'primary':PLAN['primary'],
             'strict_parents':len({r['parent_id'] for r in allrows if r['strict_eligible']}),'strict_meetings':len({r['meeting_id'] for r in allrows if r['strict_eligible']}),
             'group_refits_planned':len({r['meeting_id'] for r in primary['rows']}) if primary and do_refits else 0,
             'group_refits_successful':len(vals),'group_refits_failed':sum(r['status']=='failed' for r in refits),
             'group_refit_overlap_ari':{'min':min(vals),'median':float(np.median(vals)),'max':max(vals)} if vals else None,
             'sampling_performed':False,'browser_limit_changed':False,'holdout_transcripts_opened':0,'human_confirmations':0,
             'runtime_seconds':round(time.time()-started,2),'warnings':['Training-overlap ARI is sensitivity, not independent replication or a significance test.','Equal observed-parent weights are not equal-speech weights.','NMF component mass is descriptive and not a probability of a policy position.','Country attribution, transcription and machine type assignments remain provisional.']}
    dump(out/'summary.json',summary)
    dump(out/'SHA256.json',{p.name:digest(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()})
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('corpus',type=Path);p.add_argument('review',type=Path);p.add_argument('output',type=Path);p.add_argument('--no-refits',action='store_true');a=p.parse_args()
    with threadpool_limits(limits=1):
        print(json.dumps(execute(a.corpus,a.review,a.output,not a.no_refits),indent=2))
