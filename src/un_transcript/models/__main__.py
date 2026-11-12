"""Private model workbench: python -m un_transcript.models --help."""
import argparse
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from .contracts import (LABELS, RESERVED_DATES, check_labels, check_registration, digest,
                        identity, read_json, verify_artifacts, write_json)
from .evaluation import evaluate
from .runtime import OnnxPredictor, analyze_segments, predict_pair, source_windows


def calibrate(labels, registration, directory, output):
    """Fit one temperature using only reviewed focal spans in calibration sources."""
    import shutil
    rows=check_labels(labels,registration,'calibration')
    manifest=read_json(Path(directory)/'manifest.json');verify_artifacts(directory,manifest)
    if manifest.get('registration_sha256') != digest(registration):
        raise ValueError('Calibration registration differs from the training split freeze')
    if manifest.get('calibration_status')!='not_run':
        raise ValueError('Calibrate an uncalibrated training candidate only')
    if Path(output).exists(): raise ValueError('Calibration output must be a new directory')
    predictor=OnnxPredictor(directory,manifest); scores=[]
    for row in rows:
        if row['status']!='clear': continue
        budget=min(350,512-len(predictor.tokenizer(row['proposition'],add_special_tokens=False)['input_ids'])-3)
        windows=[w for w in source_windows(row['text'],budget,64,predictor.tokenizer)
                 if w['start'] <= row.get('focal_start',0) and w['end'] >= row.get('focal_end',len(row['text']))]
        if not windows: raise ValueError('Calibration focal span exceeds the model window')
        scores.append((predictor(row['proposition'],windows[0]['text'])['probabilities'],LABELS.index(row['label'])))
    if len(scores)<25 or {label for _,label in scores}!=set(range(5)):
        raise ValueError('Calibration requires at least 25 actual clear labels spanning all five classes')
    def loss(temperature):
        value=0.
        for probabilities,label in scores:
            weights=[math.exp(math.log(max(p,1e-12))/temperature) for p in probabilities]
            value-=math.log(max(weights[label]/sum(weights),1e-12))
        return value/len(scores)
    temperature=min([.5,.75,1.,1.25,1.5,2.,3.,4.],key=loss)
    out=Path(output);out.mkdir(parents=True)
    for name in manifest['artifacts']: shutil.copy2(Path(directory)/name,out/name)
    calibrated={**manifest,'temperature':temperature,
                'calibration_status':'calibrated_on_registered_source_disjoint_sample',
                'calibration_labels_sha256':digest(labels),'registration_sha256':digest(registration),
                'calibration_rows':len(scores),'calibration_method':'focal-window temperature grid, fixed 0.9 decision threshold',
                'parent_manifest_sha256':digest(manifest)}
    calibrated['model_id']='distilbert-'+digest(calibrated)[:20]
    write_json(out/'manifest.json',calibrated)
    return {'status':'calibrated_candidate_not_accepted','model_id':calibrated['model_id'],'rows':len(scores)}


def prepare_pilot(segments, catalog, output, policy):
    from ..attribution import infer_capacity
    attribution=infer_capacity({'text':''})
    if isinstance(segments, dict): segments = segments['segments']
    eligible = [s for s in segments if s.get('language','en')=='en' and s.get('date') not in RESERVED_DATES]
    dates = sorted({s['date'] for s in eligible})
    if len(dates) < 3: raise ValueError('At least three distinct nonreserved dates are needed for prospective time splits')
    train_end=max(1,min(len(dates)-2,int(len(dates)*.6)))
    cal_end=max(train_end+1,min(len(dates)-1,int(len(dates)*.8)))
    split_by_date={d:('train' if i<train_end else 'calibration' if i<cal_end else 'test') for i,d in enumerate(dates)}
    sources=[]
    for s in eligible:
        source_id=s.get('source_id') or s.get('revision_id')
        source_hash=s.get('source_hash') or s.get('artifact_sha256') or s.get('raw_sha256')
        if not source_id or not source_hash or not s.get('segment_id'):
            raise ValueError('Every intake segment needs source/revision, raw-byte hash and segment identity')
        sources.append({'source_id':source_id,'source_hash':source_hash,'meeting_id':s['meeting_id'],
                        'date':s['date'],'split':split_by_date[s['date']],'segment_id':s['segment_id'],
                        'text_sha256':digest(s['text'].encode())})
    registration={'schema':'un.stance-registration.v1','registered_at':datetime.now(timezone.utc).isoformat(),
                  'required_bodies':sorted({s.get('body','unknown') for s in eligible}),
                  'catalog_sha256':digest(catalog),'sources':sources,
                  'policy_sha256':digest(policy),
                  'attribution_method_version':attribution['attribution_method_version'],
                  'attribution_registry_sha256':attribution['attribution_registry_sha256'],
                  'propositions':{i['id']:i['proposition'] for i in catalog['issues']},
                  'sampling':'initial 300-pair maximum stratified pilot; 70 percent lexical candidates, 30 percent controls; not a complete-source benchmark'}
    check_registration(registration)
    out=Path(output)
    if out.exists(): raise ValueError('Pilot output must be a new private directory')
    write_json(out/'registration.json',registration)
    # Bounded source/issue-stratified pilot; this intentionally cannot substitute
    # for the independently registered complete-source acceptance benchmark.
    for split in ('train','calibration','test'):
        pools={}
        for s,pin in zip(eligible,sources):
            if pin['split']!=split: continue
            for issue in catalog['issues']:
                row={**pin,'pair_id':identity('pair',s['segment_id'],issue['id'],catalog['version']),
                             'issue_id':issue['id'],'proposition':issue['proposition'],'policy_area':issue.get('policy_area','unknown'),
                             'body':s.get('body','unknown'),'text':s['text'],'start':s.get('start',0),
                             'end':s.get('end',len(s['text'])),'focal_start':0,'focal_end':len(s['text']),
                             'capacity':s.get('capacity','unknown'),'label':None,'status':None,
                             'country':s.get('country'),
                             'national_attribution_valid':None,'owner_confirmed':False}
                matched=any(re.search(p,s['text'],re.I) for p in issue.get('patterns',[]))
                row['sampling_route']='lexical_candidate' if matched else 'unfiltered_control'
                key=(matched,issue.get('policy_area','unknown'),issue['id'])
                pool=pools.setdefault(key,[]);pool.append(row)
                pool.sort(key=lambda r:digest(r['pair_id']))
                del pool[4:]
        budget={'train':180,'calibration':60,'test':60}[split]
        rows=[];source_counts={}
        for matched,limit in ((True,int(budget*.7)),(False,budget-int(budget*.7))):
            keys=sorted(k for k in pools if k[0]==matched)
            taken=0
            for index in range(4):
                for key in keys:
                    pool=pools[key]
                    if taken>=limit or index>=len(pool):continue
                    row=pool[index];sid=row['segment_id']
                    if source_counts.get(sid,0)>=3:continue
                    rows.append(row);taken+=1;source_counts[sid]=source_counts.get(sid,0)+1
        write_json(out/(split+'-draft.json'),{'schema':'un.stance-labels.v1','registration_sha256':digest(registration),
                   'owner_confirmed':False,'reviewer_id':None,'reviewed_at':None,
                   'sample_role':'initial_pilot_not_acceptance_benchmark','target_pairs':budget,'achieved_pairs':len(rows),
                   'complete_source_review':{'owner_confirmed':False,'meeting_ids':[],
                                             'all_issues_and_missing_candidates_reviewed':False},'rows':rows})
    discovery=analyze_segments(eligible,catalog)['issue_candidates']
    novel=[{k:v for k,v in c.items() if k not in ('attribution_evidence',)} for c in discovery
           if c['status']=='uncatalogued_lexical_discovery']
    write_json(out/'novel-issue-draft.json',{'owner_confirmed':False,'sample_role':'discovery_only_not_stance_gold',
                                           'candidates':sorted(novel,key=lambda c:c['candidate_id'])[:30]})
    return {'status':'unreviewed_pilot_created','sources':len(sources),'reserved_sources_included':0,
            'instruction':'Keep all packets private. Complete actual owner labels; keep test sealed until evaluation.'}


def predict_benchmark(labels, registration, directory, catalog, split):
    rows=check_labels(labels,registration,split)
    manifest=read_json(Path(directory)/'manifest.json');verify_artifacts(directory,manifest)
    if registration.get('catalog_sha256')!=digest(catalog):
        raise ValueError('Benchmark catalog differs from prospective registration')
    predictor=OnnxPredictor(directory,manifest)
    issues={i['id']:i for i in catalog['issues']}
    results=[]; baseline_results=[]
    # Replay the exact training-only TF-IDF baseline on the same untouched pairs.
    try:
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError as exc:
        raise RuntimeError('Install requirements-model.txt to evaluate the matched baseline') from exc
    baseline=read_json(Path(directory)/'baseline.json')
    vectorizer=TfidfVectorizer(ngram_range=(1,2),vocabulary=baseline['vocabulary'])
    vectorizer.fit(['placeholder initialization']);vectorizer.idf_=np.asarray(baseline['idf'])
    for row in rows:
        from ..attribution import infer_capacity
        attributed=infer_capacity(row)
        if any(manifest.get(k)!=attributed[k] for k in ('attribution_method_version','attribution_registry_sha256')):
            raise ValueError('Benchmark attribution pipeline differs from the trained pipeline')
        issue=issues.get(row['issue_id'])
        if issue and issue['proposition']!=row['proposition']:
            raise ValueError('Gold proposition differs from canonical catalog')
        if not issue or not any(re.search(p,row['text'],re.I) for p in issue.get('patterns',[])) or attributed['attribution_kind'] not in ('national','individual_country') or not attributed['canonical_country']:
            results.append({'pair_id':row['pair_id'],'label':None,'status':'not_retrieved_or_attributed'})
            baseline_results.append({'pair_id':row['pair_id'],'label':None,'status':'not_retrieved_or_attributed'})
            continue
        answer=predict_pair(row['proposition'],row['text'],predictor,manifest['decision_threshold'],manifest['status_threshold'])
        results.append({'pair_id':row['pair_id'],**{k:v for k,v in answer.items() if k!='windows'}})
        vector=vectorizer.transform([row['proposition']+' [SEP] '+row['text']])
        logits=(vector @ np.asarray(baseline['coefficients']).T).ravel()+np.asarray(baseline['intercept'])
        weights=np.exp(logits-logits.max()); probabilities=weights/weights.sum()
        label=baseline['classes'][int(probabilities.argmax())] if probabilities.max()>=manifest['decision_threshold'] else None
        baseline_results.append({'pair_id':row['pair_id'],'label':label,'confidence':float(probabilities.max())})
    return {'model_manifest_sha256':digest(manifest),'labels_sha256':digest(labels),
            'attribution_method_version':manifest['attribution_method_version'],
            'attribution_registry_sha256':manifest['attribution_registry_sha256'],
            'catalog_sha256':digest(catalog),'engine':'onnx_candidate','predictions':results,
            'baseline_predictions':baseline_results}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    pilot=sub.add_parser('prepare-pilot');pilot.add_argument('--segments',required=True);pilot.add_argument('--output',required=True)
    pilot.add_argument('--catalog',default='config/issues.json')
    pilot.add_argument('--policy',default='config/model-policy.json')
    train=sub.add_parser('train')
    for name in ('labels','registration','base-model','revision','output'): train.add_argument('--'+name,required=True)
    train.add_argument('--policy',default='config/model-policy.json');train.add_argument('--epochs',type=int,default=3)
    train.add_argument('--batch-size',type=int,default=8);train.add_argument('--resume')
    cal=sub.add_parser('calibrate')
    for name in ('labels','registration','model-dir','output'): cal.add_argument('--'+name,required=True)
    predict=sub.add_parser('predict-benchmark')
    for name in ('labels','registration','model-dir','output'): predict.add_argument('--'+name,required=True)
    predict.add_argument('--split',choices=['calibration','test'],required=True);predict.add_argument('--catalog',default='config/issues.json')
    ev=sub.add_parser('evaluate')
    for name in ('labels','registration','predictions','model-dir','output'): ev.add_argument('--'+name,required=True)
    ev.add_argument('--policy',default='config/model-policy.json');ev.add_argument('--catalog',default='config/issues.json')
    approve=sub.add_parser('approve')
    for name in ('receipt','model-dir','catalog','owner'): approve.add_argument('--'+name,required=True)
    approve.add_argument('--confirm-release',action='store_true')
    args=parser.parse_args(argv)
    if args.command=='prepare-pilot': result=prepare_pilot(read_json(args.segments),read_json(args.catalog),args.output,read_json(args.policy))
    elif args.command=='train':
        from .training import train as train_model
        result=train_model(read_json(args.labels),read_json(args.registration),args.base_model,args.revision,
                           read_json(args.policy),args.output,args.epochs,args.batch_size,args.resume)
    elif args.command=='predict-benchmark':
        result=predict_benchmark(read_json(args.labels),read_json(args.registration),args.model_dir,read_json(args.catalog),args.split)
        write_json(args.output,result);result={'status':'prediction_receipt_written','pairs':len(result['predictions'])}
    elif args.command=='calibrate':
        result=calibrate(read_json(args.labels),read_json(args.registration),args.model_dir,args.output)
    elif args.command=='evaluate':
        manifest=read_json(Path(args.model_dir)/'manifest.json');verify_artifacts(args.model_dir,manifest)
        result=evaluate(read_json(args.labels),read_json(args.registration),read_json(args.predictions),
                        read_json(args.policy),manifest,read_json(args.catalog))
        write_json(args.output,result)
        print(__import__('json').dumps({'status':result['status'],'reasons':result['reasons'],'metrics':result['metrics']}))
        return 0 if result['status']=='pass' else 2
    elif args.command=='approve':
        receipt=read_json(args.receipt);manifest=read_json(Path(args.model_dir)/'manifest.json')
        verify_artifacts(args.model_dir,manifest)
        if not args.confirm_release or not args.owner.strip(): raise ValueError('Actual owner release confirmation is required')
        if receipt.get('status')!='pass' or receipt.get('model_manifest_sha256')!=digest(manifest) or receipt.get('catalog_sha256')!=digest(read_json(args.catalog)):
            raise ValueError('A passing receipt bound to this model and catalog is required')
        accepted={**receipt,'status':'accepted','owner_release_confirmed':True,'owner':args.owner,
                  'approved_at':datetime.now(timezone.utc).isoformat()}
        write_json(Path(args.model_dir)/'acceptance.json',accepted)
        result={'status':'accepted','model_id':manifest['model_id']}
    print(__import__('json').dumps(result))
    return 0


if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError,KeyError,OSError,RuntimeError) as error:
        raise SystemExit('Model workbench refused: '+str(error))
