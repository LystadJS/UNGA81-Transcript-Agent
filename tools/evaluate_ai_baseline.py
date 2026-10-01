"""Evaluate a fixed lexical baseline against provenance-verified owner labels."""
import argparse, hashlib, json, re
from pathlib import Path
import reviewed_loader as loader

def predict(text, spec):
    flags=re.I if spec['ignore_case'] else 0
    return int(any(re.search(p,text,flags) for p in spec['positive_patterns']))

def metrics(truth, predictions):
    if len(truth)!=len(predictions) or not truth:raise ValueError('Nonempty aligned observations required')
    if any(v not in (0,1) for v in truth+predictions):raise ValueError('Binary observations required')
    tp=sum(y==1 and p==1 for y,p in zip(truth,predictions))
    tn=sum(y==0 and p==0 for y,p in zip(truth,predictions))
    fp=sum(y==0 and p==1 for y,p in zip(truth,predictions))
    fn=sum(y==1 and p==0 for y,p in zip(truth,predictions))
    divide=lambda a,b:a/b if b else None
    return dict(n=len(truth),true_positive=tp,false_positive=fp,false_negative=fn,true_negative=tn,
                precision=divide(tp,tp+fp),recall=divide(tp,tp+fn),specificity=divide(tn,tn+fp),
                f1=divide(2*tp,2*tp+fp+fn),accuracy=(tp+tn)/len(truth))

def evaluate(spec_path, test_root, development, output):
    output=Path(output)
    if output.exists():raise FileExistsError(output)
    spec_path=Path(spec_path);spec=json.loads(spec_path.read_text(encoding='utf-8'))
    test_root=Path(test_root);lock=json.loads((test_root/'test-lock.json').read_text())
    export=test_root/'validated-test-import.json'
    if loader.sha(export)!=lock['export_sha256']:raise ValueError('Frozen export changed')
    test=loader.load_bundle(test_root)
    if test['bundle_sha256']!=lock['bundle_sha256'] or json.loads(export.read_text())!=test:raise ValueError('Frozen test changed')
    dev=[loader.load_bundle(p) for p in development]
    if [b['bundle_sha256'] for b in dev]!=lock['development_bundle_hashes']:raise ValueError('Development identity changed')
    if any(b['engineering_fixture'] or not b['human_review_complete'] for b in [test]+dev):raise ValueError('Actual reviewed data required')
    if any(r['event_date']!='2026-09-28' for r in test['records']):raise ValueError('Wrong test date')
    if {r['iso3'] for b in dev for r in b['records']} & {r['iso3'] for r in test['records']}:raise ValueError('Country overlap')
    results={};private={}
    for name,records in [('development',[r for b in dev for r in b['records']]),('test',test['records'])]:
        if any(r['binary_label'] is None for r in records):raise ValueError('Unresolved labels cannot be silently omitted')
        truth=[r['binary_label'] for r in records];pred=[predict(r['quote'],spec) for r in records]
        results[name]=dict(keyword=metrics(truth,pred),always_not_relevant=metrics(truth,[0]*len(truth)))
        private[name]=[dict(passage_id=r['passage_id'],iso3=r['iso3'],quote=r['quote'],actual=y,predicted=p) for r,y,p in zip(records,truth,pred)]
    report=dict(baseline=spec,spec_sha256=loader.sha(spec_path),runner_sha256=loader.sha(__file__),test_bundle_sha256=test['bundle_sha256'],development_bundle_hashes=lock['development_bundle_hashes'],results=results,training_performed=False,publication_eligible=False,
                limitations=['Only three positive test passages; each changes recall by one third.', '24 passages clustered within 14 countries; not 24 independent countries.', 'Development packets were keyword-enriched; development metrics are diagnostic only.', 'Retrospective single-reviewer labels; no independent adjudication.', 'Lexical rules miss implicit references and cannot establish model readiness.'])
    output.mkdir(parents=True)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (output/'predictions-private.json').write_text(json.dumps(private,indent=2)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('spec');p.add_argument('test');p.add_argument('output');p.add_argument('--development',nargs=2,required=True);a=p.parse_args()
    print(json.dumps(evaluate(a.spec,a.test,a.development,a.output),indent=2))
