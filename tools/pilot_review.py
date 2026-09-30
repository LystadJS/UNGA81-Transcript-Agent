"""Prepare and locally collect the owner's single-reviewer AI relevance pilot."""
from pathlib import Path
import argparse, datetime as dt, hashlib, html, json, random, re, secrets, subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
import review_data as rd

def now(): return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def prepare(root,replay):
    root=Path(root); replay=Path(replay); rd.initialize(root,replay)
    passages=rd.rows(root/'passages.csv')[1]
    pattern=re.compile(r'\bartificial intelligence\b|\bAI\b|\bmachine learning\b|\bautonomous weapons\b',re.I)
    hit=[p for p in passages if pattern.search(p['quote'])]; other=[p for p in passages if not pattern.search(p['quote'])]
    rng=random.Random(30092026);rng.shuffle(hit);rng.shuffle(other)
    selected=hit[:12]+other[:12];rng.shuffle(selected)
    rd.write_csv(root/'passages.csv',rd.SCHEMAS['passages'].split(),selected)
    ids={p['source_id'] for p in selected};observed=now();sources=rd.rows(root/'sources.csv')[1]
    for s in sources:
        s['available_at']=observed
        if not s['source_url']:s['source_url']='urn:sha256:'+sha(replay)+'#'+s['iso3']
    rd.write_csv(root/'sources.csv',rd.SCHEMAS['sources'].split(),[s for s in sources if s['source_id'] in ids])
    rd.write_csv(root/'propositions.csv',rd.SCHEMAS['propositions'].split(),[dict(proposition_id='ai-relevance-v1',version='1',target='Artificial Intelligence',proposition='Does the quoted passage substantively discuss AI systems, uses, risks, opportunities or governance?',scope='Include explicit AI and clearly contextualized AI applications. General technology/digital development alone is not enough. Ambiguous context is insufficient. Relevance is not support or opposition.')])
    policy=json.loads((root/'bundle.json').read_text());policy.update(review_mode='single_reviewer_pilot',dataset_kind='real',cutoff=observed,human_review_complete=False)
    (root/'bundle.json').write_text(json.dumps(policy,indent=2),encoding='utf-8')
    packet={'schema':'un.pilot.v1','issue':'Artificial Intelligence','source_archive_sha256':sha(replay),'observed_locally_at':observed,'availability_basis':'conservative local observation time, not first public availability','sample':'up to 12 lexical candidates plus 12 non-hits, deterministic shuffled sample; not a prevalence estimate','count':len(selected),'csrf':secrets.token_urlsafe(24),'selected_ids':[p['passage_id'] for p in selected],'review_complete':False}
    (root/'pilot.json').write_text(json.dumps(packet,indent=2),encoding='utf-8');render(root)
    return packet

def render(root):
    root=Path(root);meta=json.loads((root/'pilot.json').read_text());sources={s['source_id']:s for s in rd.rows(root/'sources.csv')[1]}
    cards=[]
    for i,p in enumerate(rd.rows(root/'passages.csv')[1],1):
        s=sources[p['source_id']]
        cards.append(f'''<article data-id="{html.escape(p['passage_id'])}"><h2>{i}. {html.escape(s['iso3'])} · {s['event_date']}</h2><p>{html.escape(p['quote'])}</p><label>AI relevance <select required><option value="">Choose after reading</option><option value="relevant">Relevant</option><option value="not_relevant">Not relevant</option><option value="insufficient">Insufficient context</option></select></label><label>Optional note <input class="note" maxlength="1000"></label></article>''')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI relevance pilot</title><style>body{font:17px system-ui;background:#f2f5f8;color:#062135;max-width:900px;margin:30px auto;padding:20px}h1{border-bottom:4px solid #d01319;padding-bottom:12px}article{background:white;padding:22px;margin:18px 0;border:1px solid #ccd4df;border-radius:6px}h2{font-size:18px}p{line-height:1.6;white-space:pre-wrap}label{display:block;margin:14px 0}input,select,button{font:inherit;padding:10px;max-width:100%;box-sizing:border-box}input.note{width:100%}button{background:#002d74;color:white;border:0;cursor:pointer}#status{position:sticky;bottom:0;background:white;padding:18px;border-top:2px solid #002d74}</style><h1>Artificial Intelligence · quick review</h1><p>You are the sole reviewer and finalizer. Read each passage and choose a label. Include AI systems, applications, risks, opportunities and governance. General references to technology or digital development alone are not sufficient. Relevance does not mean support. Use “Insufficient context” when unclear.</p><p>This is a small, enriched pilot from the archived 23 September corpus. It cannot establish prevalence, independent reviewer agreement or a forward-time model evaluation.</p><form><label>Your reviewer name or role <input id="reviewer" value="project-owner" required maxlength="100"></label>'''+''.join(cards)+'''<label><input id="confirm" type="checkbox" required> I personally reviewed every choice and finalize these labels for audit-only use.</label><button>Save my completed review</button></form><div id="status">No human review has been recorded yet.</div><script>const token=TOKEN;document.querySelector('form').onsubmit=async e=>{e.preventDefault();const rows=[...document.querySelectorAll('article')].map(a=>({passage_id:a.dataset.id,label:a.querySelector('select').value,rationale:a.querySelector('.note').value||'Manual owner review; no additional note provided'}));const status=document.querySelector('#status');status.textContent='Saving…';try{const r=await fetch('/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token,reviewer:document.querySelector('#reviewer').value,confirmed:document.querySelector('#confirm').checked,rows})});const v=await r.json();if(!r.ok)throw Error(v.error);status.textContent='Saved. '+v.message;document.querySelector('button').disabled=true}catch(err){status.textContent=err.message}};</script></html>'''
    page=page.replace('TOKEN',json.dumps(meta['csrf']));(root/'index.html').write_text(page,encoding='utf-8')

def complete(root,payload):
    root=Path(root);meta=json.loads((root/'pilot.json').read_text())
    if meta['review_complete']:raise ValueError('Pilot already finalized; use a new revision for changes')
    if payload.get('token')!=meta['csrf'] or payload.get('confirmed') is not True:raise ValueError('Explicit owner review confirmation required')
    reviewer=payload.get('reviewer','').strip()
    if not reviewer or len(reviewer)>100:raise ValueError('Reviewer identity required')
    rows=payload['rows'];ids=[r['passage_id'] for r in rows]
    if meta.get('packet_kind')=='later_date_development':
        if any(r.get('boundary') not in ('national_address','other_intervention','uncertain') or (r['boundary']!='national_address' and r.get('label')!='insufficient') for r in rows):
            raise ValueError('Check each intervention; other or uncertain interventions require insufficient context')
        rows=[dict(r,rationale='Intervention: '+r['boundary']+'. '+r.get('rationale','')) for r in rows]
    if len(ids)!=len(set(ids)) or set(ids)!=set(meta['selected_ids']):raise ValueError('Every selected passage needs exactly one review')
    if any(r['label'] not in rd.LABELS['issue'] or not isinstance(r['rationale'],str) or not r['rationale'].strip() or len(r['rationale'])>1000 for r in rows):raise ValueError('Invalid label or rationale')
    when=now();annotations=[];final=[]
    for i,r in enumerate(rows):
        base=dict(passage_id=r['passage_id'],task='issue',proposition_id='ai-relevance-v1',rationale=r['rationale'])
        annotations.append(dict(base,annotation_id=f'owner-{i+1:03d}',label=r['label'],reviewer_id=reviewer,reviewed_at=when))
        final.append(dict(base,final_label=r['label'],adjudicator_id=reviewer,adjudicated_at=when))
    rd.write_csv(root/'annotations.csv',rd.SCHEMAS['annotations'].split(),annotations);rd.write_csv(root/'adjudications.csv',rd.SCHEMAS['adjudications'].split(),final)
    policy=json.loads((root/'bundle.json').read_text());policy.update(human_review_complete=True,cutoff=when);(root/'bundle.json').write_text(json.dumps(policy,indent=2),encoding='utf-8')
    report=rd.validate(root,'pilot')
    if not report['passed']:raise ValueError('; '.join(report['errors']))
    meta.update(review_complete=True,reviewer=reviewer,completed_at=when);(root/'pilot.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    (root/'pilot-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report

def finish_workflow(root,daily_run,package_root=None,rscript=None):
    import reviewed_loader as loader
    root=Path(root)
    result=loader.attach(root,daily_run)
    if package_root and rscript:
        validator=Path(__file__).with_name('validate_review_run.R')
        check=subprocess.run([str(rscript),str(validator.resolve()),str(Path(package_root).resolve()),str(Path(daily_run).resolve())],capture_output=True,text=True,timeout=300)
        (root/'daily-validation.log').write_text(check.stdout+'\n'+check.stderr,encoding='utf-8')
        if check.returncode:raise ValueError('Labels saved and attached, but native daily validation needs attention; inspect daily-validation.log')
        result['native_daily_validation_passed']=True
    (root/'workflow.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

def serve(root,port,daily_run=None,package_root=None,rscript=None):
    root=Path(root).resolve()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in ('/','/index.html'):self.send_error(404);return
            data=(root/'index.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(data)
        def do_POST(self):
            try:
                if self.path!='/complete' or self.headers.get('Host')!=f'127.0.0.1:{port}':raise ValueError('Invalid local endpoint')
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=100000:raise ValueError('Invalid request size')
                complete(root,json.loads(self.rfile.read(length)))
                if daily_run:
                    try:
                        audit=finish_workflow(root,daily_run,package_root,rscript)
                        result={'message':f"Review saved and {audit['matched_passages']} passages imported into the audit record. The briefing is unchanged."}
                    except Exception as e:
                        (root/'workflow-error.txt').write_text(str(e),encoding='utf-8')
                        result={'message':'Your review is saved. Audit integration needs attention; your labels have been preserved.'}
                else:result={'message':'Single-reviewer pilot finalized. Independent review and model release remain unestablished.'}
                status=200
            except (ValueError,KeyError,TypeError) as e:result={'error':str(e)};status=400
            self.send_response(status);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(result).encode())
    HTTPServer(('127.0.0.1',port),Handler).serve_forever()

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('prepare');a.add_argument('output',type=Path);a.add_argument('replay',type=Path)
    a=sub.add_parser('serve');a.add_argument('output',type=Path);a.add_argument('--port',type=int,default=8767);a.add_argument('--daily-run',type=Path);a.add_argument('--package-root',type=Path);a.add_argument('--rscript',type=Path)
    a=p.parse_args()
    if a.cmd=='prepare':print(json.dumps(prepare(a.output,a.replay),indent=2))
    else:serve(a.output,a.port,a.daily_run,a.package_root,a.rscript)
