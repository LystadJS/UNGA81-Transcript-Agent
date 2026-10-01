'use strict';
(() => {
 const X=window.HLW_EXPLORER, root=document.querySelector('#lexical-explorer');
 if(!root||!X)return;
 const $=s=>root.querySelector(s), make=(t,s,c)=>{const e=document.createElement(t);if(s!==undefined)e.textContent=s;if(c)e.className=c;return e;};
 const colors=['#002d74','#b33c36','#287e7b','#805a9b','#9c650c','#516476'];
 const pct=n=>(n*100).toFixed(1)+'%', num=n=>n.toFixed(3);
 let k=X.default_k, group=0, selected=0;
 const partition=()=>X.partitions.find(p=>p.k===k);
 const svgNode=(tag,attrs,text)=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [a,v] of Object.entries(attrs||{}))n.setAttribute(a,v);if(text!==undefined)n.textContent=text;return n;};
 const metric=(value,label)=>{const e=make('div');e.append(make('strong',String(value)),make('span',label));return e;};
 $('#lex-stats').append(metric(X.counts.passages,'unique candidate passages'),metric(X.counts.source_segments,'source segments'),metric(X.counts.affiliation_labels,'source affiliation labels'),metric(pct(X.variance_ratio.reduce((a,b)=>a+b,0)),'variance retained in this plot'));
 $('#lex-summary').textContent=`${X.counts.topic_rows} topic hits become ${X.counts.passages} unique source-offset passages. Median length: ${X.counts.median_words} words; middle 50%: ${X.counts.q1_words}–${X.counts.q3_words}; range: ${X.counts.min_words}–${X.counts.max_words}. Repeated topic hits are collapsed; passages from the same speaker remain dependent.`;
 $('#lex-limit').textContent=`Interpretation: the best tested silhouette is ${num(Math.max(...X.partitions.map(p=>p.silhouette)))} on a −1 to +1 scale, and this projection retains ${pct(X.variance_ratio.reduce((a,b)=>a+b,0))} of variance. Use the display to navigate wording, not to establish discrete diplomatic groups.`;
 for(const p of X.partitions){const o=make('option',`${p.k} clusters`);o.value=p.k;$('#lex-k').append(o);}$('#lex-k').value=k;
 function detail(i){
  selected=i;const p=X.points[i],host=$('#lex-detail');host.replaceChildren();
  host.append(make('span',`PASSAGE ${i+1} / GROUP ${partition().labels[i]}`,'usun-kicker'),make('h3',p.country||'Unattributed speaker'),make('p',`${p.date} · ${p.scope==='general_debate'?'General Debate':'Broader HLW'} · ${p.words} words`,'small'),make('blockquote',p.quote));
  const a=make('a','Open source statement ↗');const u=new URL(p.source_url);if(u.protocol==='https:'&&u.hostname==='transcripts.un.org')a.href=u.href;host.append(a);
  host.append(make('p',p.topics.join(' · '),'small'));
  if(p.timestamps_flagged==='True')host.append(make('p','Source timing is flagged as unreliable.','small'));
  root.querySelectorAll('.lex-point').forEach(n=>n.setAttribute('stroke-width',Number(n.dataset.index)===i?'3':'1'));
 }
 function scatter(){
  const svg=$('#lex-scatter');svg.replaceChildren();
  const xs=X.points.map(p=>p.x),ys=X.points.map(p=>p.y),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
  const sx=x=>65+(x-xmin)/(xmax-xmin||1)*490,sy=y=>325-(y-ymin)/(ymax-ymin||1)*280;
  for(let j=0;j<=4;j++){
   const x=xmin+(xmax-xmin)*j/4,y=ymin+(ymax-ymin)*j/4;
   svg.append(svgNode('line',{x1:sx(x),x2:sx(x),y1:35,y2:335,stroke:'#e4e9ef'}),svgNode('line',{x1:55,x2:565,y1:sy(y),y2:sy(y),stroke:'#e4e9ef'}),svgNode('text',{x:sx(x),y:351,'text-anchor':'middle'},x.toFixed(2)),svgNode('text',{x:48,y:sy(y)+4,'text-anchor':'end'},y.toFixed(2)));
  }
  svg.append(svgNode('text',{x:310,y:382,'text-anchor':'middle'},`PC1 · ${pct(X.variance_ratio[0])} variance`),svgNode('text',{x:18,y:185,transform:'rotate(-90 18 185)','text-anchor':'middle'},`PC2 · ${pct(X.variance_ratio[1])} variance`));
  const labels=partition().labels;
  X.points.forEach((p,i)=>{
   if(group&&labels[i]!==group)return;
   const circle=svgNode('circle',{cx:sx(p.x),cy:sy(p.y),r:6,fill:colors[labels[i]-1],stroke:'#fff','stroke-width':i===selected?3:1,tabindex:0,role:'button','aria-label':`Passage ${i+1}, ${p.country}, group ${labels[i]}. Read source quotation.`,class:'lex-point','data-index':i});
   circle.onclick=()=>detail(i);circle.onfocus=()=>detail(i);circle.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();detail(i);}};
   svg.append(circle);
  });
 }
 function clusters(){
  const host=$('#lex-clusters');host.replaceChildren();
  for(const c of partition().clusters){
   const b=make('button',undefined,'lex-cluster');b.type='button';b.setAttribute('aria-pressed',String(group===c.id));b.style.borderLeftColor=colors[c.id-1];
   b.append(make('strong',`Group ${c.id} · ${c.n} passages`),make('span',c.terms.join(' · ')));
   const track=make('span',undefined,'track'),fill=make('span',undefined,'fill');fill.style.width=pct(c.n/X.points.length);fill.style.background=colors[c.id-1];track.append(fill);b.append(track);
   b.onclick=()=>{group=group===c.id?0:c.id;render();};host.append(b);
  }
  $('#lex-visible').textContent=group?`Showing group ${group}: ${partition().clusters.find(c=>c.id===group).n} passages. Select it again to show all.`:`Showing all ${X.points.length} passages. Select a group to isolate it.`;
 }
 function quality(){
  const svg=$('#lex-quality');svg.replaceChildren();
  svg.setAttribute('aria-label','Mean cosine silhouette: '+X.partitions.map(p=>`${p.k} clusters ${num(p.silhouette)}`).join('; '));
  const sx=x=>75+(x+1)*225;
  [-1,-.5,0,.5,1].forEach(x=>{svg.append(svgNode('line',{x1:sx(x),x2:sx(x),y1:20,y2:225,stroke:x===0?'#8190a0':'#e4e9ef'}),svgNode('text',{x:sx(x),y:245,'text-anchor':'middle'},String(x)));});
  X.partitions.forEach((p,i)=>{const y=32+i*39,x=sx(p.silhouette);svg.append(svgNode('text',{x:58,y:y+14,'text-anchor':'end'},`k = ${p.k}`),svgNode('rect',{x:Math.min(sx(0),x),y,width:Math.abs(x-sx(0)),height:21,fill:p.k===k?'#002d74':'#aab8cc'}),svgNode('text',{x:x+7,y:y+15},num(p.silhouette)));});
  svg.append(svgNode('text',{x:300,y:273,'text-anchor':'middle'},'Mean cosine silhouette · −1 to +1'));
  const p=partition();$('#lex-quality-note').textContent=`Selected k=${k}: silhouette ${num(p.silhouette)}; smallest group ${p.smallest_cluster} passage${p.smallest_cluster===1?'':'s'}. Near-zero scores indicate overlapping lexical groups. The default maximizes this score only among k=2–6; it does not validate a natural number of themes.`;
 }
 function render(){
  if(group&&!partition().clusters.some(c=>c.id===group))group=0;
  if(group&&partition().labels[selected]!==group)selected=partition().labels.indexOf(group);
  scatter();clusters();quality();detail(selected);
 }
 $('#lex-k').onchange=e=>{k=Number(e.target.value);group=0;render();};
 const short=['Embargo','Sanctions','Terrorism list','Extraterritorial'];
 const table=$('#lex-overlap'),head=make('tr');head.append(make('th','Source segment overlap'));short.forEach(t=>head.append(make('th',t)));const thead=make('thead');thead.append(head);table.append(thead);const body=make('tbody');
 X.overlap.forEach((row,i)=>{const tr=make('tr'),th=make('th',short[i]);th.scope='row';tr.append(th);row.forEach(c=>{const td=make('td');td.style.background=`rgba(0,45,116,${.04+(c.jaccard||0)*.17})`;td.append(make('strong',c.jaccard===null?'N/A':pct(c.jaccard)),make('span',`${c.intersection} / ${c.union} segments`));tr.append(td);});body.append(tr);});table.append(body);
 render();
})();
