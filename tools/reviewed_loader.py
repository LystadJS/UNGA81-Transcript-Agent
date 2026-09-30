"""Snapshot, validate and import human labels into a strictly audit-only sidecar."""
from pathlib import Path
import argparse, datetime as dt, hashlib, json, shutil, tempfile
import review_data as rd

def digest(raw):return hashlib.sha256(raw).hexdigest()
def sha(p):return digest(Path(p).read_bytes())
def safe(root,rel):
    root=Path(root).resolve();rel=Path(rel)
    if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe bundle path')
    p=root
    for part in rel.parts:
        p=p/part
        if p.is_symlink():raise ValueError('Symlink in bundle path')
    p.resolve().relative_to(root)
    return p

def load_bundle(root,capability='pilot'):
    if capability not in ('pilot','labels','stance'):raise ValueError('Only reviewed passage labels supported by this loader')
    root=Path(root).resolve();raw={}
    for name in ['bundle.json']+[n+'.csv' for n in rd.SCHEMAS]:
        p=safe(root,name)
        if p.stat().st_size>10_000_000:raise ValueError('Review table exceeds size bound')
        raw[name]=p.read_bytes()
    # Validate an immutable byte snapshot, never a changing live directory.
    with tempfile.TemporaryDirectory(prefix='un-label-snapshot-') as temp:
        snap=Path(temp).resolve()
        assert snap.is_relative_to(Path(tempfile.gettempdir()).resolve())
        for name,content in raw.items():(snap/name).write_bytes(content)
        sources=rd.rows(snap/'sources.csv')[1]
        for s in sources:
            rel=s['text_path'];p=safe(root,rel)
            if p.stat().st_size>2_000_000:raise ValueError('Source exceeds size bound')
            if rel in raw:raise ValueError('Source path collides with bundle metadata or another source')
            content=p.read_bytes();raw[rel]=content
            dest=safe(snap,rel);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content)
        if sum(map(len,raw.values()))>128_000_000:raise ValueError('Review snapshot exceeds size bound')
        report=rd.validate(snap,capability)
        if not report['passed']:raise ValueError('Review bundle rejected: '+'; '.join(report['errors']))
        policy=json.loads(raw['bundle.json']);props={p['proposition_id']:p for p in rd.rows(snap/'propositions.csv')[1]}
        ps={p['passage_id']:p for p in rd.rows(snap/'passages.csv')[1]};ss={s['source_id']:s for s in sources}
        annotations=rd.rows(snap/'annotations.csv')[1];splits={s['source_id']:s['split'] for s in rd.rows(snap/'splits.csv')[1]};records=[]
        for f in rd.rows(snap/'adjudications.csv')[1]:
            p=ps[f['passage_id']];s=ss[p['source_id']];prop=props.get(f['proposition_id'])
            if not prop:raise ValueError('Every imported task needs a named versioned target/codebook')
            reviewers=[a for a in annotations if (a['passage_id'],a['task'],a['proposition_id'])==(f['passage_id'],f['task'],f['proposition_id'])]
            # A review cannot predate availability of its evidence.
            avail=dt.datetime.fromisoformat(s['available_at'].replace('Z','+00:00'))
            if any(dt.datetime.fromisoformat(a['reviewed_at'].replace('Z','+00:00'))<avail for a in reviewers):raise ValueError('Review predates available evidence')
            records.append(dict(passage_id=p['passage_id'],source_id=s['source_id'],iso3=s['iso3'],event_date=s['event_date'],available_at=s['available_at'],source_url=s['source_url'],text_sha256=s['text_sha256'],quote=p['quote'],start=int(p['start']),end=int(p['end']),task=f['task'],target=prop,label=f['final_label'],binary_label={'relevant':1,'not_relevant':0}.get(f['final_label']) if f['task']=='issue' else None,split=splits.get(s['source_id']),reviews=reviewers,finalization=f))
        inputs={name:digest(content) for name,content in sorted(raw.items())}
        identity=digest(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode())
        return {'schema':'un.review.import.v1','bundle_sha256':identity,'input_sha256':inputs,'capability':capability,'review_mode':policy.get('review_mode','independent'),
                'human_review_complete':not bool(policy.get('engineering_fixture',False)),'engineering_fixture':bool(policy.get('engineering_fixture',False)),'independent_review_established':policy.get('review_mode','independent')=='independent' and not bool(policy.get('engineering_fixture',False)),'records':records,'validation':report,
                'publication_eligible':False,'model_fit_authorized':False,'daily_adapter_integrated':False,'training_split_validated':capability in ('labels','stance'),
                'note':'Imported human assertions with structural/provenance checks. Semantic accuracy and reviewer identity are not certified. Insufficient labels remain unresolved.'}

def export(root,output,capability='pilot'):
    result=load_bundle(root,capability);output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
    return result

def attach(root,run,capability='pilot'):
    """Post-run integration: append evidence under audit/, without changing daily products."""
    data=load_bundle(root,capability);run=Path(run).resolve()
    for name in ('checkpoint.json','validation.json','brief.json','daily_briefing.eml','daily_briefing.html','daily_briefing.txt','audit/analytics/method_ledger.csv','audit/analytics/gate_ledger.csv','audit/speeches.json'):
        if not safe(run,name).is_file():raise ValueError('Incomplete daily run: '+name)
    cp=json.loads((run/'checkpoint.json').read_text(encoding='utf-8'));qa=json.loads((run/'validation.json').read_text(encoding='utf-8'))
    if cp.get('stage')!='complete' or cp.get('no_email_sent') is not True or qa.get('passed') is not True or qa.get('five_output_packet_contract')!='passed':raise ValueError('Daily run must have passed its five-output validation')
    # Bind to every prior file, leaving the original run checksum manifest intact.
    before={}
    for p in run.rglob('*'):
        if p.is_symlink():raise ValueError('Symlink in daily run')
        if p.is_file() and p.relative_to(run).parts[:2]!=('audit','reviewed_labels'):before[p.relative_to(run).as_posix()]=sha(p)
    speeches=json.loads((run/'audit/speeches.json').read_text(encoding='utf-8'))
    current={(s['iso3'],digest(s['text'].encode('utf-8'))) for s in speeches}
    matched=[r['passage_id'] for r in data['records'] if (r['iso3'],r['text_sha256']) in current]
    if not matched:raise ValueError('No reviewed source resolves to this daily corpus')
    target=safe(run,'audit/reviewed_labels')/data['bundle_sha256']
    target.mkdir(parents=True,exist_ok=False)
    (target/'labels.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    for name,expected in before.items():
        if sha(safe(run,name))!=expected:raise ValueError('Daily artifact changed during audit attachment')
    receipt={'schema':'un.review.audit.v1','status':'engineering_fixture_only' if data['engineering_fixture'] else 'attached_audit_only','bundle_sha256':data['bundle_sha256'],'review_mode':data['review_mode'],'matched_passage_ids':matched,'unmatched_passage_ids':[r['passage_id'] for r in data['records'] if r['passage_id'] not in matched],
             'base_run_file_sha256':before,'publication_eligible':False,'model_fit_authorized':False,'method_gates_changed':False,'daily_products_unchanged':True,'labels_sha256':sha(target/'labels.json')}
    (target/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    (target/'SHA256.json').write_text(json.dumps({p.name:sha(p) for p in target.iterdir()},indent=2)+'\n',encoding='utf-8')
    return {'audit_directory':str(target),'matched_passages':len(matched),'daily_products_unchanged':True,'publication_eligible':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
    for cmd in ('export','attach'):
        s=sub.add_parser(cmd);s.add_argument('bundle',type=Path);s.add_argument('destination',type=Path);s.add_argument('--capability',choices=['pilot','labels','stance'],default='pilot')
    a=p.parse_args();result=export(a.bundle,a.destination,a.capability) if a.cmd=='export' else attach(a.bundle,a.destination,a.capability)
    print(json.dumps({'status':'complete','records':len(result.get('records',[])),'publication_eligible':False,**({} if a.cmd=='export' else result)},indent=2))
