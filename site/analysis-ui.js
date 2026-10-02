(function(){
'use strict';
const el=id=>document.getElementById(id),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let countries=[],controller=null,corpus=null,result=null,ready=false,stale=false;
const status=s=>{el('analysisStatus').textContent=s;};
const pause=()=>new Promise(r=>setTimeout(r,0));
const split=s=>s.split(',').map(x=>x.trim()).filter(Boolean);
function openPanel(){const id=location.hash==='#review'?'reviewPanel':location.hash==='#help'?'helpPanel':null;if(id)el(id).open=true;}
window.addEventListener('hashchange',openPanel);openPanel();
function settings(){return UNAnalysis.parameters({topic:el('topic').value.trim(),phrases:[el('topic').value.trim(),...split(el('phrases').value)],exclude:split(el('excludePhrases').value),start:el('startDate').value,end:el('endDate').value,region:el('region').value,scope:el('meetingScope').value,methods:[...document.querySelectorAll('input[name=method]:checked')].map(e=>e.value)});}
function table(headers,rows){return '<div class="table-wrap"><table><thead><tr>'+headers.map(x=>'<th scope="col">'+esc(x)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(x=>'<td>'+esc(x)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
function chart(title,items,label,value,suffix=''){
 if(!items.length)return '<p>No observations.</p>';
 const max=Math.max(...items.map(value),1e-12),height=items.length*32+36;
 return '<div class="chart-wrap"><svg viewBox="0 0 850 '+height+'" role="img" aria-label="'+esc(title)+'"><title>'+esc(title)+'</title>'+items.map((r,i)=>{const v=value(r),y=i*32+14;return '<text x="0" y="'+(y+14)+'" font-size="13">'+esc(label(r).slice(0,27))+'</text><rect class="bar" fill="#002d74" x="220" y="'+y+'" width="'+(v/max*500).toFixed(2)+'" height="20"/><text x="730" y="'+(y+14)+'" font-size="13">'+esc((suffix==='%'?v.toFixed(1):Number.isInteger(v)?v:v.toFixed(3))+suffix)+'</text>';}).join('')+'</svg></div>';
}
function render(r){
 const p=r.parameters,n=r.counts,issues=r.coverage.filter(x=>x.status!=='collected'),byStatus={};for(const c of r.coverage)byStatus[c.status]=(byStatus[c.status]||0)+1;
 let html='<div class="report-document"><p class="eyebrow">TRANSCRIPT REPORT</p><h2>'+esc(p.topic)+'</h2><p>'+esc(p.start)+' through '+esc(p.end)+' · '+esc(p.region)+' · '+esc(p.scope==='all'?'All inventoried meetings':'General Debate meetings')+'</p><p>Any phrase: '+esc(p.phrases.join(' | '))+'. Exclusions: '+esc(p.exclude.join(' | ')||'None')+'.</p><p class="method-note">Prepared '+esc(r.created_at.slice(0,10))+' · English transcripts</p>';
 html+='<div class="metrics">'+[[n.eligible,'Passages analyzed'],[n.matched,'Topic matches'],[n.eligible?(100*n.matched/n.eligible).toFixed(1)+'%':'N/A','Match rate'],[n.duplicates,'Duplicates removed']].map(([v,t])=>'<div class="metric"><strong>'+esc(v)+'</strong>'+esc(t)+'</div>').join('')+'</div>';
 html+='<p class="method-note">Matches identify language, not a speaker’s position. These results describe the collected passages; verify their meaning in the source.</p>';
 if(!n.matched)html+='<p class="warning">No matching segments were found in the available eligible corpus. This does not establish that the topic was absent from unavailable or excluded sources.</p>';
 if(r.collection&&(p.start<r.collection.start||p.end>r.collection.end||(r.collection.scope==='general_debate'&&p.scope==='all')))html+='<p class="warning">This saved collection does not cover the requested dates or scope. Collect live transcripts to extend it.</p>';
 if(issues.length)html+='<p class="warning">'+issues.length+' collection entries lack usable English text. Missing sources are excluded from the match rate.</p>';
 html+='<details class="coverage-panel"><summary>Collection coverage</summary><p>'+esc(n.input)+' passages collected; '+esc(n.eligible_before_dedup)+' eligible before deduplication; '+esc(n.unmapped)+' with unmapped regions.</p>';
 if(r.collection)html+='<p>Collected '+esc(r.collection.start)+'–'+esc(r.collection.end)+'. '+esc(r.collection.selected_meetings)+' meetings selected from '+esc(r.collection.inventory_meetings)+' in the inventory.</p>';
 html+=table(['Status','Entries'],Object.entries(byStatus))+table(['Date','Meeting / day','Status','Detail'],r.coverage.map(c=>[c.date,c.title||'Daily inventory',c.status,c.error||c.language||'']))+'</details>';
 const m=r.methods;
 for(const [key,title] of [['frequency','Topic frequency by region'],['timeline','Topic frequency by date']])if(m[key]){
  html+='<h3>'+title+'</h3><p class="method-note">Share of eligible passages containing the topic. Groups without eligible text are omitted.</p>'+chart(title,m[key],x=>x.name,x=>x.percent,'%')+'<details><summary>View figures</summary>'+table(['Group','Matched','Eligible','Match %'],m[key].map(x=>[x.name,x.matches,x.total,x.percent.toFixed(2)]))+'</details>';
 }
 if(m.length)html+='<h3>Passage length</h3><p class="method-note">Word counts for matched passages.</p>'+chart('Segment length',m.length,x=>x.name,x=>x.total)+'<details><summary>View figures</summary>'+table(['Words','Passages'],m.length.map(x=>[x.name,x.total]))+'</details>';
 if(m.tfidf)html+='<h3>TF-IDF term ranking</h3><p class="method-note">Terms ranked by their average TF-IDF weight across matched passages.</p><details><summary>Calculation</summary><p>Top 20 mean L2-normalized weights across matched segments; lowercase Unicode unigrams, length &gt;2, fixed English stop list, sublinear TF = 1 + ln(count), smoothed IDF = 1 + ln((1 + N)/(1 + document frequency)). Vocabulary: '+m.tfidf.vocabulary+'. Query terms may rank highly.</p></details>'+chart('Mean TF-IDF weight',m.tfidf.terms,x=>x.term,x=>x.mean)+'<details><summary>View figures</summary>'+table(['Term','Mean weight','Passages'],m.tfidf.terms.map(x=>[x.term,x.mean.toFixed(5),x.documents]))+'</details>';
 if(m.similarity){html+='<h3>Pairwise cosine text similarity</h3>';if(m.similarity.skipped)html+='<p class="warning">'+esc(m.similarity.skipped)+'</p>';else html+='<p class="method-note">Top 10 of '+m.similarity.compared+' pairs using the same full TF-IDF vectors. Similar language is not evidence of shared stance or coordination. Exact duplicates have already been removed.</p>'+table(['Segment A','Segment B','Cosine'],m.similarity.pairs.map(x=>[x.left,x.right,x.cosine.toFixed(4)]));}
 html+='<h3>Source passages</h3><p>Showing '+Math.min(100,r.matched.length)+' of '+r.matched.length+' full source segments. Download analysis JSON or CSV for all matches and identifiers. </p>';
 for(const v of r.matched.slice(0,100))html+='<div class="evidence-item"><strong>'+esc(v.country)+' · '+esc(v.date)+'</strong><p>'+esc(v.meeting)+'</p><p class="method-note">'+esc(v.region)+'</p><p>'+esc(v.text.slice(0,350))+(v.text.length>350?'…':'')+'</p><details><summary>Read full source segment</summary><blockquote>'+esc(v.text)+'</blockquote><p class="method-note">Record '+esc(v.id)+' · SHA-256 '+esc(v.text_sha256)+'</p></details><a href="'+esc(v.source_url)+'" target="_blank" rel="noopener noreferrer">Open original source ↗</a></div>';
 html+='<details class="report-notes"><summary>Methods and source record</summary><p><strong>These comparisons describe the collected text.</strong> Segments can contain procedural remarks, repeat a speaker or depend on the same meeting. The figures do not estimate population effects or establish coordination.</p><p><strong>The data export preserves the analysis.</strong> It records the query, methods, source links, text hashes and duplicate mapping. Exact-text deduplication normalizes Unicode and whitespace; near-duplicates remain. Imported metadata is supplied by the file’s author, and text hashes establish integrity rather than authenticity.</p><p class="method-note">Engine: '+esc(r.engine)+' · Prepared: '+esc(r.created_at)+'</p></details></div>';
 return html;
}
function save(value,name,type){const url=URL.createObjectURL(new Blob([value],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
const exportButtons=()=>[...el('analysisOutput').querySelectorAll('button')];
function invalidate(){if(result){stale=true;exportButtons().forEach(b=>b.disabled=true);status('Settings changed. Generate a new report before exporting.');}}
el('analysisForm').addEventListener('input',invalidate);
el('corpusSource').onchange=()=>{el('corpusFileLabel').hidden=el('corpusSource').value!=='import';};
el('cancelAnalysis').onclick=()=>controller?.abort();
el('analysisForm').onsubmit=async e=>{
 e.preventDefault();if(controller)return;
 try{
  if(!ready)throw Error('Country registry is not available. Reload the page.');const p=settings();controller=new AbortController();
  for(const c of el('analysisForm').elements)c.disabled=true;el('cancelAnalysis').disabled=false;el('analysisOutput').hidden=true;result=null;corpus=null;stale=false;
  if(el('corpusSource').value==='import'){
   status('Checking imported collection and hashes…');const f=el('corpusFile').files[0];if(!f||f.size>30000000)throw Error('Choose a collection JSON under 30 MB.');
   corpus=UNAnalysis.validateCorpus(JSON.parse(await f.text()));
   for(const r of corpus.records){if(controller.signal.aborted)throw new DOMException('Cancelled','AbortError');if(await UNCollector.sha(r.text)!==r.text_sha256)throw Error('Text hash mismatch for '+r.id);}
  }else corpus=await UNCollector.collect(p,countries,{signal:controller.signal,progress:status});
  if(controller.signal.aborted)throw new DOMException('Cancelled','AbortError');
  status('Analyzing collected text…');await pause();result=await UNAnalysis.analyze(corpus,p,async message=>{status(message);await pause();if(controller.signal.aborted)throw new DOMException('Cancelled','AbortError');});
  if(controller.signal.aborted)throw new DOMException('Cancelled','AbortError');
  el('analysisReport').innerHTML=render(result);el('analysisOutput').hidden=false;exportButtons().forEach(b=>b.disabled=false);
  status('Report ready: '+result.counts.matched+' topic matches from '+result.counts.eligible+' passages.');
 }catch(error){result=null;corpus=null;el('analysisOutput').hidden=true;status(error.name==='AbortError'?'Collection cancelled. No partial report was released.':'Could not complete report: '+error.message+' If live access is blocked by your network, import an exported collection.');}
 finally{controller=null;for(const c of el('analysisForm').elements)c.disabled=false;el('cancelAnalysis').disabled=true;}
};
el('exportResult').onclick=()=>{if(result&&!stale)save(JSON.stringify(result,null,2),'un-analysis.json','application/json');};
el('exportCorpus').onclick=()=>{if(corpus&&!stale)save(JSON.stringify(corpus),'un-transcripts.json','application/json');};
el('exportCSV').onclick=()=>{if(!result||stale)return;const fields=['id','date','country','region','meeting','source_url','text_sha256','text'];const cell=x=>'"'+String(x??'').replace(/^[=+@\-\t\r]/,"'$&").replace(/"/g,'""')+'"';save('\uFEFF'+[fields,...result.matched.map(r=>fields.map(f=>r[f]))].map(row=>row.map(cell).join(',')).join('\r\n'),'un-matched-segments.csv','text/csv;charset=utf-8');};
el('exportHTML').onclick=async()=>{if(!result||stale)return;try{const response=await fetch('analysis.css');if(!response.ok)throw Error('Styles unavailable');const css=await response.text();save('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'"><title>UN transcript report</title><style>body{font:16px/1.5 Arial,sans-serif;max-width:1100px;margin:auto;padding:28px}'+css+'</style><body>'+render(result)+'</body></html>','un-report.html','text/html');}catch(e){status('Report download failed: '+e.message);}};
el('printAnalysis').onclick=()=>{if(result&&!stale)window.print();};
fetch('countries.json').then(r=>{if(!r.ok)throw Error('Registry unavailable');return r.json();}).then(data=>{countries=data;for(const region of [...new Set(data.map(c=>c.region))].sort()){const o=document.createElement('option');o.textContent=region;el('region').append(o);}ready=true;}).catch(e=>status('Country registry failed to load: '+e.message));
})();
