"""Export assigned packets for browser review; validate returned reviews locally."""
import argparse, datetime as dt, hashlib, json
from pathlib import Path
import review_data as rd
import reviewed_loader as loader
import pilot_review as pilot

def canonical(data):return json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
def identity(data):return hashlib.sha256(canonical(data)).hexdigest()
def packet(root):
    root=Path(root);meta=json.loads((root/'pilot.json').read_text(encoding='utf-8'))
    tables={name:rd.rows(root/(name+'.csv'))[1] for name in ('sources','passages','propositions')}
    sources={s['source_id']:s for s in tables['sources']};passages=[]
    if not 1<=len(tables['passages'])<=200:raise ValueError('Packet must contain 1..200 passages')
    for p in tables['passages']:
        s=sources[p['source_id']];raw=loader.safe(root,s['text_path']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=s['text_sha256']:raise ValueError('Source hash mismatch')
        text=raw.decode('utf-8');start,end=int(p['start']),int(p['end'])
        if not 0<=start<end<=len(text) or text[start:end]!=p['quote']:raise ValueError('Quote does not resolve')
        url=s['source_url'] if s['source_url'].startswith('https://') else ''
        passages.append(dict(passage_id=p['passage_id'],country=s['iso3'],date=s['event_date'],quote=p['quote'],context=text[max(0,start-900):min(len(text),end+900)],source_url=url,source_sha256=s['text_sha256'],start=start,end=end))
    role='held_out_test' if meta.get('packet_kind')=='held_out_test' else 'development'
    table_hashes={n:loader.sha(root/(n+'.csv')) for n in tables}
    prop=tables['propositions'][0]
    return dict(schema='un.remote.packet.v1',packet_id=identity(table_hashes),role=role,title='Artificial Intelligence · '+('held-out test' if role=='held_out_test' else 'development review'),codebook=prop['proposition']+' '+prop['scope'],sampling=meta.get('sampling_method',meta.get('sample','See assignment instructions')),source_tables_sha256=table_hashes,passages=passages)

def export(root,dest):
    data=packet(root);dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
    return dict(packet_sha256=identity(data),passages=len(data['passages']),role=data['role'])

def import_review(root,review):
    root=Path(root);data=packet(root);path=Path(review)
    if path.stat().st_size>5_000_000:raise ValueError('Review file too large')
    incoming=json.loads(path.read_text(encoding='utf-8-sig'))
    if incoming.get('schema')!='un.remote.review.v1' or incoming.get('packet_id')!=data['packet_id'] or incoming.get('packet_sha256')!=identity(data) or incoming.get('role')!=data['role']:raise ValueError('Returned review does not match assigned packet')
    if incoming.get('confirmed') is not True:raise ValueError('Reviewer confirmation missing')
    completed=dt.datetime.fromisoformat(incoming.get('completed_at','').replace('Z','+00:00'))
    if completed.tzinfo is None or completed>dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=5):raise ValueError('Invalid review completion time')
    if not isinstance(incoming.get('rows'),list):raise ValueError('Missing review choices')
    for r in incoming['rows']:
        if r.get('boundary') not in ('national_address','other_intervention','uncertain') or (r['boundary']!='national_address' and r.get('label')!='insufficient'):raise ValueError('Invalid intervention/label combination')
        if not isinstance(r.get('rationale'),str) or len(r['rationale'])>800:raise ValueError('Invalid rationale')
    meta=json.loads((root/'pilot.json').read_text());payload=dict(incoming,token=meta['csrf'])
    report=pilot.complete(root,payload)
    result=loader.export(root,root/'remote-validated-import.json')
    receipt=dict(schema='un.remote.import.v1',review_sha256=loader.sha(path),packet_sha256=identity(data),reviewer_reported_completed_at=incoming['completed_at'],imported_at=pilot.now(),bundle_sha256=result['bundle_sha256'],passed=report['passed'],publication_eligible=False,note='Identity is reviewer-declared, not authenticated. No automatic model training or daily attachment.')
    (root/'remote-import-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
    for cmd in ('export','import'):
        a=s.add_parser(cmd);a.add_argument('root');a.add_argument('file')
    a=p.parse_args();print(json.dumps(export(a.root,a.file) if a.cmd=='export' else import_review(a.root,a.file),indent=2))
