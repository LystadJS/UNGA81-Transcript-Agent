'use strict';
const D=window.HLW_DATA,$=s=>document.querySelector(s),E=D.evidence;
const labels={general_debate:'General Debate',broader_hlw:'Broader HLW',other_week_proceedings:'Background proceedings'};
const state={scope:'hlw',topic:'embargo_focus',day:'',context:false,page:0};
const key=e=>e.raw_file+'|'+e.json_pointer;
const restrictionTopics=new Set(['Embargo and blockade','Unilateral sanctions','Terrorism-list designation','Extraterritorial restrictions']);
const focusRows=rows=>{const cubaKeys=new Set(rows.filter(e=>e.topic==='Cuba').map(key));return rows.filter(e=>restrictionTopics.has(e.topic)&&cubaKeys.has(key(e)));};
const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const scopeRows=()=>E.filter(e=>state.scope==='all'||(state.scope==='hlw'?e.scope!=='other_week_proceedings':e.scope===state.scope));
function coverage(){
 const host=$('#coverage-chart');
 for(const scope of Object.keys(labels)){
  const list=D.coverage.filter(r=>r.scope===scope),yes=list.filter(r=>r.collection_status==='downloaded').length;
  const row=node('div',undefined,'coverage-row');row.append(node('span',labels[scope]));
  const stack=node('div',undefined,'stack');stack.setAttribute('role','img');stack.setAttribute('aria-label',`${yes} downloaded and ${list.length-yes} unavailable out of ${list.length} meetings`);
  for(const [n,c] of [[yes,'navy'],[list.length-yes,'missing']]){const part=node('span',undefined,c);part.style.width=100*n/list.length+'%';stack.append(part);}
  row.append(stack,node('span',`${yes} / ${list.length} available`,'coverage-count'));host.append(row);
 }
}
function charts(){
 const rows=scopeRows(),cuba=focusRows(rows),keys=new Set(rows.filter(r=>r.topic==='Cuba').map(key));
 const counts=Array.from({length:8},(_,i)=>{const date='2026-09-'+(21+i);return{date,n:cuba.filter(e=>e.date===date).length};});
 const max=Math.max(1,...counts.map(r=>r.n)),host=$('#daily-chart');host.replaceChildren();
 for(const row of counts){const button=node('button',undefined,'daily');button.type='button';button.dataset.date=row.date;button.dataset.count=row.n;button.setAttribute('aria-label',`${row.date}: ${row.n} restriction candidate rows in Cuba-containing segments; show evidence`);
  const track=node('span',undefined,'track'),fill=node('span',undefined,'fill');fill.style.width=100*row.n/max+'%';track.append(fill);button.append(node('span',row.date.slice(8)+' Sep'),track,node('b',String(row.n)));
  button.onclick=()=>{state.day=row.date;state.topic='embargo_focus';state.context=false;state.page=0;$('#topic').value='embargo_focus';$('#evidence-search').value='';evidence();$('#evidence').scrollIntoView();};host.append(button);}
 const topics=[...new Set(E.map(r=>r.topic))].filter(t=>restrictionTopics.has(t)).map(topic=>({topic,n:new Set(rows.filter(r=>r.topic===topic&&keys.has(key(r))).map(key)).size})).sort((a,b)=>b.n-a.n||a.topic.localeCompare(b.topic));
 const topMax=Math.max(1,...topics.map(r=>r.n)),th=$('#topic-chart');th.replaceChildren();
 for(const row of topics){const b=node('button',undefined,'topic-bar');b.type='button';b.dataset.topic=row.topic;b.dataset.count=row.n;b.setAttribute('aria-label',`${row.topic}: ${row.n} source segments also containing Cuba; show evidence`);
  const title=node('span',undefined,'topic-label');title.append(node('span',row.topic),node('b',String(row.n)));const track=node('span',undefined,'track'),fill=node('span',undefined,'fill');fill.style.width=100*row.n/topMax+'%';track.append(fill);b.append(title,track);
  b.onclick=()=>{state.topic=row.topic;state.context=true;state.day='';state.page=0;$('#topic').value=row.topic;$('#evidence-search').value='';evidence();$('#evidence').scrollIntoView();};th.append(b);}
}
function evidence(){
 const scoped=scopeRows(),keys=new Set(scoped.filter(e=>e.topic==='Cuba').map(key)),q=$('#evidence-search').value.trim().toLowerCase();
 const source=state.topic==='embargo_focus'?focusRows(scoped):scoped;
 const rows=source.filter(e=>(state.topic==='embargo_focus'||state.topic==='all'||e.topic===state.topic)&&(!state.day||e.date===state.day)&&(!state.context||keys.has(key(e)))&&(!q||[e.country,e.quote,e.meeting,e.topic].join(' ').toLowerCase().includes(q)));
 const pages=Math.max(1,Math.ceil(rows.length/20));state.page=Math.min(state.page,pages-1);const host=$('#evidence-list');host.replaceChildren();
 $('#result-count').textContent=`${rows.length.toLocaleString()} candidate evidence rows · ${state.scope==='hlw'?'General Debate + broader HLW':state.scope==='all'?'Full archive':labels[state.scope]}`;
 $('#context-note').textContent=(state.day?`Date: ${state.day}. `:'')+(state.topic==='embargo_focus'?'Embargo focus: four restriction topics in source segments also mentioning Cuba. Segment co-occurrence does not confirm that each restriction refers to Cuba. ':'')+(state.context?'Only source segments also containing a Cuba reference. ':'')+'A source segment can contain multiple topics and several passages. Introductions remain candidates.';
 for(const e of rows.slice(state.page*20,state.page*20+20)){
  const article=node('article',undefined,'evidence-item');article.dataset.scope=e.scope;article.dataset.topic=e.topic;article.dataset.date=e.date;
  const meta=node('div',undefined,'evidence-meta');meta.append(node('span',e.date),node('span',labels[e.scope]),node('span',e.topic));article.append(meta,node('h3',e.country||'Unattributed speaker'),node('p',e.meeting,'meeting'));
  const details=node('details');details.append(node('summary',e.quote.length>190?e.quote.slice(0,190)+'…':e.quote),node('blockquote',e.quote));article.append(details);
  const link=node('a','Open source statement ↗');const url=new URL(e.source_url);if(url.protocol==='https:'&&url.hostname==='transcripts.un.org')link.href=url.href;article.append(link);
  if(e.timestamps_flagged==='True')article.append(node('p','Source flags timing as unreliable; verify the text location.','small'));
  host.append(article);
 }
 if(!rows.length)host.append(node('p','No candidate rows match these filters. Try another scope or clear the filters.','empty'));
 $('#page-count').textContent=`Page ${state.page+1} of ${pages}`;$('#prev').disabled=state.page===0;$('#next').disabled=state.page>=pages-1;
}
for(const topic of [...new Set(E.map(r=>r.topic))].filter(t=>t!=='Cuba')){const o=node('option',topic);o.value=topic;$('#topic').append(o);}
$('#scope').onchange=e=>{state.scope=e.target.value;state.day='';state.context=false;state.page=0;charts();evidence();};
$('#topic').onchange=e=>{state.topic=e.target.value;state.context=false;state.page=0;evidence();};
$('#evidence-search').oninput=()=>{state.page=0;evidence();};
$('#clear').onclick=()=>{state.topic='embargo_focus';state.day='';state.context=false;state.page=0;$('#topic').value='embargo_focus';$('#evidence-search').value='';evidence();};
$('#prev').onclick=()=>{state.page--;evidence();};$('#next').onclick=()=>{state.page++;evidence();};
$('#search').oninput=e=>document.querySelectorAll('#countries tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(e.target.value.toLowerCase()));
function appearance(){document.documentElement.style.setProperty('--reading',$('#font-size').value);document.documentElement.style.setProperty('--space',$('#spacing').value);try{localStorage.setItem('hlw-cuba-appearance',JSON.stringify({font:$('#font-size').value,spacing:$('#spacing').value}));}catch{}}
try{const p=JSON.parse(localStorage.getItem('hlw-cuba-appearance')||'null');if(p&&['16px','18px'].includes(p.font)&&['22px','32px','42px'].includes(p.spacing)){$('#font-size').value=p.font;$('#spacing').value=p.spacing;}}catch{}
$('#font-size').onchange=appearance;$('#spacing').onchange=appearance;$('#reset-look').onclick=()=>{$('#font-size').value='16px';$('#spacing').value='32px';appearance();};
coverage();charts();evidence();appearance();
