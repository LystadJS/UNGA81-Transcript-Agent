"""Build the private later-date development review interface; never assign labels."""
import argparse, hashlib, html, json, re
from pathlib import Path
import pilot_review as pilot
import review_data as rd

def prepare(candidates, output):
    output=Path(output)
    if output.exists(): raise FileExistsError(output)
    rows=json.loads(Path(candidates).read_text(encoding='utf-8'))
    eligible=[r for r in rows if r['speech_date'] in ('2026-09-24','2026-09-25','2026-09-26') and not r['overlaps_pilot_country']]
    for r in eligible:
        if hashlib.sha256(r['text'].encode()).hexdigest()!=r['text_sha256']: raise ValueError('Candidate text changed')
    replay=output.parent/(output.name+'-input.json')
    replay.parent.mkdir(parents=True,exist_ok=True)
    with replay.open('x',encoding='utf-8') as f:
        json.dump([dict(iso3=r['country_id'],date=r['speech_date'],text=r['text'],source_url=r['source_url']) for r in eligible],f)
    meta=pilot.prepare(output,replay)
    meta.update(packet_kind='later_date_development',held_out_date='2026-09-28',candidate_sha256=pilot.sha(candidates))
    (output/'pilot.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return render(output)

def render(output):
    output=Path(output);meta=json.loads((output/'pilot.json').read_text())
    sources={s['source_id']:s for s in rd.rows(output/'sources.csv')[1]}
    cards=[];sampling=[]
    pattern=re.compile(r'\bartificial intelligence\b|\bAI\b|\bmachine learning\b|\bautonomous weapons\b',re.I)
    for i,p in enumerate(rd.rows(output/'passages.csv')[1],1):
        s=sources[p['source_id']];text=(output/s['text_path']).read_text(encoding='utf-8')
        a,b=int(p['start']),int(p['end']);context=text[max(0,a-900):min(len(text),b+900)]
        sampling.append(dict(passage_id=p['passage_id'],stratum='lexical_candidate' if pattern.search(p['quote']) else 'non_hit'))
        cards.append(f'''<article data-id="{p['passage_id']}"><h2>{i:02d} · {s['iso3']} <small>{s['event_date']}</small></h2>
<p class="quote">{html.escape(p['quote'])}</p><details><summary>Read surrounding context and check the speech boundary</summary><p>{html.escape(context)}</p><a href="{html.escape(s['source_url'],quote=True)}" target="_blank" rel="noopener">Open UN source ↗</a></details>
<label>1. Does this belong to the national address?<select class="boundary" required><option value="">Choose after checking context</option><option value="national_address">Yes — national address</option><option value="other_intervention">No — procedural remark or other intervention</option><option value="uncertain">Uncertain</option></select></label>
<label>2. AI relevance<select class="relevance" required><option value="">Choose a label</option><option value="relevant">Relevant</option><option value="not_relevant">Not relevant</option><option value="insufficient">Insufficient context / excluded intervention</option></select></label><label>Optional note<input class="note" maxlength="800"></label></article>''')
    (output/'sampling.json').write_text(json.dumps(sampling,indent=2),encoding='utf-8')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI · Later-date review</title><style>
*{box-sizing:border-box}body{font:17px system-ui;background:#f1f4f8;color:#062135;max-width:960px;margin:auto;padding:24px}header{background:#062135;color:white;padding:28px;border-bottom:5px solid #d01319}h1{font-size:30px;margin:10px 0}h2{font-size:21px}small{display:block;font-size:15px;font-weight:400;margin-top:6px}article{background:white;border:1px solid #ced7e0;border-radius:6px;padding:24px;margin:22px 0}p{line-height:1.65;white-space:pre-wrap;overflow-wrap:anywhere}label{display:block;margin-top:18px}input,select,button{font:inherit;padding:12px;max-width:100%;border:1px solid #9caebe;border-radius:4px}select,.note{width:100%;margin-top:7px}button{background:#002d74;color:white;cursor:pointer;margin:8px 8px 8px 0}button:disabled{opacity:.6}summary{cursor:pointer;color:#002d74;padding:12px 0}a{color:#002d74}#progress{position:sticky;top:0;background:#fff;padding:14px;border-bottom:2px solid #d01319;z-index:2}#status{padding:16px;background:#e7eef7;margin:12px 0}input[type=checkbox]{width:20px;height:20px} :focus-visible{outline:3px solid #d01319;outline-offset:3px}</style>
<header><small>UN TRANSCRIPT REVIEW · DEVELOPMENT PACKET</small><h1>Artificial Intelligence</h1><p>24 passages · September 24–26<br>September 28 remains reserved for testing.</p></header><div id="progress" role="status"></div>
<p>You are the sole reviewer and finalizer. First check the intervention type, then label AI relevance. Include AI systems, applications, risks, opportunities and governance. Generic technology alone is not enough. Relevance does not mean support or opposition.</p>
<p>This enriched sample contains 12 lexical candidates and 12 non-hits. It is for development, not estimating overall accuracy. The source is automatic transcription. If the passage is outside a national address or its role is unclear, choose “Insufficient context / excluded intervention.”</p>
<form><label>Your reviewer name or role<input id="reviewer" required maxlength="100" value="project-owner"></label>CARDS
<label><input id="confirm" required type="checkbox"> I reviewed all choices and finalize them for audit-only use.</label><button id="save">Save completed review</button><button type="button" id="download">Download review backup</button></form><div id="status" role="status">Draft choices are saved in this browser. Final submission requires your confirmation.</div>
<script>
const token=TOKEN, cards=[...document.querySelectorAll('article')], key='later-review-'+token;
const collect=()=>({token,reviewer:document.querySelector('#reviewer').value,confirmed:document.querySelector('#confirm').checked,rows:cards.map(a=>({passage_id:a.dataset.id,label:a.querySelector('.relevance').value,boundary:a.querySelector('.boundary').value,rationale:'Intervention: '+a.querySelector('.boundary').value+'. '+(a.querySelector('.note').value||'No additional note.')}))});
const update=()=>{let n=cards.filter(a=>a.querySelector('.relevance').value&&a.querySelector('.boundary').value).length;document.querySelector('#progress').textContent=n+' / '+cards.length+' passages reviewed';};
try{const d=JSON.parse(localStorage.getItem(key));if(d){document.querySelector('#reviewer').value=d.reviewer;for(const r of d.rows){const a=cards.find(a=>a.dataset.id===r.passage_id);if(a){a.querySelector('.relevance').value=r.label;a.querySelector('.boundary').value=r.boundary;a.querySelector('.note').value=r.note||'';}}}}catch(e){}
document.querySelector('form').addEventListener('input',()=>{const d=collect();d.rows.forEach((r,i)=>r.note=cards[i].querySelector('.note').value);try{localStorage.setItem(key,JSON.stringify(d));}catch(e){document.querySelector('#status').textContent='Browser draft storage unavailable. Download a backup before closing.';}update();});update();
document.querySelector('#download').onclick=()=>{const blob=new Blob([JSON.stringify(collect(),null,2)],{type:'application/json'});const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download='ai-later-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);};
document.querySelector('form').onsubmit=async e=>{e.preventDefault();const p=collect(),status=document.querySelector('#status');if(p.rows.some(r=>r.boundary!=='national_address'&&r.label!=='insufficient')){status.textContent='For other or uncertain interventions, select Insufficient context / excluded intervention.';return;}if(location.protocol==='file:'){status.textContent='Use the local review server to submit, or download your completed review backup and provide it for import.';return;}const button=document.querySelector('#save');button.disabled=true;status.textContent='Saving and validating…';try{const res=await fetch('/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});const data=await res.json();if(!res.ok)throw Error(data.error);status.textContent='Saved and validated. Your labels remain audit-only. Download a backup if desired.';try{localStorage.removeItem(key);}catch(e){}document.querySelectorAll('select,input').forEach(x=>x.disabled=true);}catch(e){status.textContent=e.message;button.disabled=false;}};
</script></html>'''
    if meta.get('packet_kind')=='held_out_test':
        page=page.replace('DEVELOPMENT PACKET','HELD-OUT TEST PACKET').replace('24 passages · September 24–26<br>September 28 remains reserved for testing.','24 passages · September 28<br>Reserved for final evaluation.').replace('This enriched sample contains 12 lexical candidates and 12 non-hits. It is for development, not estimating overall accuracy.','This is a seeded random sample after duplicate and country-overlap exclusions. No topic-keyword enrichment was used. Do not use these labels for training or tuning.').replace('AI · Later-date review','AI · September 28 test review')
    page=page.replace('CARDS',''.join(cards)).replace('TOKEN',json.dumps(meta['csrf']))
    (output/'index.html').write_text(page,encoding='utf-8')
    return {'passages':meta['count'],'dates':sorted({s['event_date'] for s in sources.values()}),'held_out_date_excluded':all(s['event_date']!='2026-09-28' for s in sources.values()),'labels_assigned':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidates');p.add_argument('output');a=p.parse_args();print(json.dumps(prepare(a.candidates,a.output)))
