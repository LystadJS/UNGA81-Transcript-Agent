'use strict';
// Public renderer; inputs and generated source-bearing HTML must remain private.
const crypto=require('node:crypto');
function canonical(value){if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';if(value&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';return JSON.stringify(value);}
function render(packet){
 if(packet.schema!=='un.private-country-corrections.v1'||packet.version!=='private-country-corrections-1'||!Array.isArray(packet.rows)||!/^[a-f0-9]{64}$/.test(packet.packet_id))throw Error('Invalid packet');
 if(packet.private_only!==true||['owner_identity_verified','accepted_positions','comparisons_eligible'].some(k=>packet[k]!==false))throw Error('Packet cannot grant acceptance');
 if(!packet.input_fingerprints||!['original_packet_id','corrections_sha256','correction_method_sha256'].every(k=>/^[a-f0-9]{64}$/.test(packet.input_fingerprints[k])))throw Error('Correction identity required');
 const unsigned={...packet};delete unsigned.packet_id;
 if(crypto.createHash('sha256').update(canonical(unsigned)).digest('hex')!==packet.packet_id||new Set(packet.rows.map(r=>r.id)).size!==packet.rows.length||packet.rows.some(r=>r.owner_decision!==null))throw Error('Packet content or unreviewed membership does not match');
 for(const row of packet.rows){if(row.correction&&(!['corrected','unresolved'].includes(row.correction.status)||row.correction.review_state!=='assistant_provisional'||!row.original_proposal||row.original_proposal.owner_decision!==null||!Array.isArray(row.correction.unresolved_reasons)||(row.correction.status==='unresolved'&&!row.correction.unresolved_reasons.length)||(row.correction.status==='corrected'&&row.correction.unresolved_reasons.length)))throw Error('Invalid provisional correction');}
 const json=JSON.stringify(packet).replace(/</g,'\\u003c').replace(/\u2028/g,'\\u2028').replace(/\u2029/g,'\\u2029');
 const script='('+browser.toString()+')('+json+');';
 const hash=crypto.createHash('sha256').update(script).digest('base64');
 return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'sha256-${hash}'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; base-uri 'none'; form-action 'none'"><title>Private corrected country-position review</title><style>*{box-sizing:border-box}body{overflow-wrap:anywhere;font:17px system-ui;line-height:1.5;max-width:1050px;margin:2rem auto;padding:0 1rem;color:#15283a;background:#f5f7fa}article,header{background:white;padding:1rem;margin:1rem 0;border:1px solid #ccd5df;border-radius:6px}label{display:inline-block;margin:.4rem;max-width:calc(100% - .8rem);min-width:0}input[type=file]{display:block;width:100%;min-width:0}pre{white-space:pre-wrap;overflow-wrap:anywhere}select,button,input,textarea{font:inherit;max-width:100%;min-width:0;padding:.35rem}textarea{display:block;width:95%;min-height:4rem}blockquote{white-space:pre-wrap;margin:.6rem 0;border-left:3px solid #668;padding:.6rem;overflow-wrap:anywhere}small{display:block;overflow-wrap:anywhere}h2{font-size:1.3rem}#status{font-weight:600}a{color:#064d8d}</style><header><h1>Private corrected country-position review</h1><p>Review proposed country positions against their supporting text. These are provisional proposals, not accepted government positions. Collective and unknown-capacity statements remain separate.</p><p>All choices start unselected. Saving records unauthenticated reviewer-entered choices; it does not approve a model or publish evidence.</p><div id="overview"></div><label>Country <select id="country"></select></label><label>Capacity <select id="capacity"></select></label><label>Correction status <select id="correctionStatus"></select></label><label>Policy <select id="policy"></select></label><label>Review status <select id="reviewStatus"></select></label><p><button id="save">Save review</button> <label>Open review <input id="open" type="file" accept="application/json,.json"></label></p><p id="status" role="status"></p></header><main id="rows"></main><script>${script}</script></html>`;
}
function browser(packet){
 'use strict';
 const $=id=>document.getElementById(id), allowed=[null,'confirm','reject','unclear'];
 const choices=packet.rows.map(r=>({row_id:r.id,label:null,note:''}));
 const filters={country:'all',capacity:'all',policy:'all',correction_status:'all',status:'all'};
 const countries=[...new Set(packet.rows.map(r=>r.country||'Collective / unknown capacity'))].sort();
 const capacities=[...new Set(packet.rows.map(r=>r.capacity))].sort();
 const correctionStatuses=[...new Set(packet.rows.map(r=>(r.correction?.status||'unchanged')))].sort();
 const policies=[...new Set(packet.rows.map(r=>r.policy_id))].sort();
 function element(tag,text,parent){const e=document.createElement(tag);if(text!==undefined)e.textContent=String(text);if(parent)parent.append(e);return e;}
 function options(id,values){for(const [value,text]of values){const e=element('option',text,$(id));e.value=value;}}
 options('country',[['all','All countries and capacities'],...countries.map(x=>[x,x])]);
 options('capacity',[['all','All capacities'],...capacities.map(x=>[x,x.replaceAll('_',' ')])]);
 options('correctionStatus',[['all','All corrections'],...correctionStatuses.map(x=>[x,x])]);
 options('policy',[['all','All policy questions'],...policies.map(x=>[x,x])]);
 options('reviewStatus',[['all','All choices'],['unreviewed','Unreviewed'],...allowed.slice(1).map(x=>[x,x])]);
 const count=packet.rows.length; $('overview').textContent=`${countries.length} country/capacity groups · ${count} proposals. Repeated proposals are evidence to review, not opinion weights.`;
 function official(url){try{const u=new URL(url);return u.protocol==='https:'&&!u.username&&!u.password&&!u.port&&(u.hostname==='un.org'||u.hostname.endsWith('.un.org'))?u.href:null;}catch{return null;}}
 function draw(){
  $('rows').replaceChildren();let shown=0;
  for(let i=0;i<packet.rows.length;i++){
   const row=packet.rows[i],choice=choices[i],country=row.country||'Collective / unknown capacity';
   if(filters.capacity!=='all'&&filters.capacity!==row.capacity||filters.correction_status!=='all'&&filters.correction_status!==(row.correction?.status||'unchanged')||filters.country!=='all'&&filters.country!==country||filters.policy!=='all'&&filters.policy!==row.policy_id||filters.status!=='all'&&(filters.status==='unreviewed'?choice.label!==null:choice.label!==filters.status))continue;
   shown++;const article=element('article',undefined,$('rows'));article.dataset.rowId=row.id;
   element('h2',`${country} — ${row.policy_id}`,article);
   element('p',`Capacity: ${row.capacity.replaceAll('_',' ')}; group: ${row.group||'unspecified'}; meeting: ${row.meeting_id}`,article);
   for(const warning of packet.source_warnings||[]){if((warning.affected_row_ids||[]).includes(row.id)){for(const reason of warning.unresolved_reasons||[])element('p','Related statement caution: '+reason,article);element('p','This caution does not mark every related proposal unresolved.',article);}}
   element('p',`Correction status: ${(row.correction?.status||'unchanged')}`,article);
   for(const flag of row.correction?.unresolved_reasons||[])element('p','Unresolved: '+flag,article);
   if(row.correction){element('p','Correction: '+row.correction.note,article);for(const [key,value] of Object.entries(row.correction.interpretation||{})){if(value)element('p',key.replaceAll('_',' ')+': '+value,article);}}
   element('p','Current provisional reading: '+String(row.assistant_proposal.stance||'Unclear')+'. '+(row.assistant_proposal.discourse_labels||[]).join(', '),article);
   const original=element('details',undefined,article);element('summary','Original proposal before correction',original);element('pre',JSON.stringify(row.original_proposal||row,null,2),original);
   const details=element('details',undefined,article);element('summary','Evidence and source details',details);element('pre',JSON.stringify(row.assistant_proposal,null,2),details);
   for(const evidence of row.evidence){element('small',`${evidence.kind} evidence · ${evidence.pointer}`,article);element('blockquote',evidence.quote,article);}
   const link=official(row.source.url);if(link){const a=element('a','Open source',article);a.href=link;a.target='_blank';a.rel='noopener noreferrer';}else element('p','Source link unavailable or outside permitted official hosts.',article);
   element('small',`Source hash: ${row.source.sha256}; text hash: ${row.source.text_sha256}; modality: ${row.source.modality}`,details);
   const label=element('label','Your decision ',article),select=element('select',undefined,label);select.setAttribute('aria-label',`Choice for ${row.id}`);
   for(const value of allowed){const o=element('option',value===null?'Choose a label':value,select);o.value=value||'';}select.value=choice.label||'';select.onchange=()=>{choice.label=select.value||null;};
   const note=element('textarea',undefined,article);note.maxLength=2000;note.value=choice.note;note.setAttribute('aria-label',`Review note for ${row.id}`);note.oninput=()=>{choice.note=note.value;};
  }
  $('status').textContent=`Showing ${shown} of ${count} proposals. No choices are accepted positions.`;
 }
 for(const [id,key]of [['country','country'],['capacity','capacity'],['policy','policy'],['correctionStatus','correction_status'],['reviewStatus','status']])$(id).onchange=()=>{filters[key]=$(id).value;draw();};
 function saved(){return {schema:'un.private-country-decisions-corrections.v1',packet_id:packet.packet_id,original_packet_id:packet.input_fingerprints.original_packet_id,corrections_sha256:packet.input_fingerprints.corrections_sha256,revision:1,parent_revision_sha256:null,choices:choices.map(x=>({...x})).sort((a,b)=>a.row_id.localeCompare(b.row_id)),filters:{...filters},owner_identity_verified:false,accepted_positions:false,comparisons_eligible:false};}
 function canonical(value){if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';if(value&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';return JSON.stringify(value);}
 async function digest(value){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical(value))))).map(x=>x.toString(16).padStart(2,'0')).join('');}
 $('save').onclick=async()=>{const value=saved();value.revision_sha256=await digest(value);const blob=new Blob([JSON.stringify(value,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=element('a');a.href=url;a.download='private-country-corrected-review-choices.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 function exactKeys(value,keys){return value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).sort().join('|')===keys.sort().join('|');}
 async function validate(value){
  if(!exactKeys(value,['schema','packet_id','original_packet_id','corrections_sha256','revision','parent_revision_sha256','choices','filters','owner_identity_verified','accepted_positions','comparisons_eligible','revision_sha256'])||value.schema!=='un.private-country-decisions-corrections.v1'||value.packet_id!==packet.packet_id||value.original_packet_id!==packet.input_fingerprints.original_packet_id||value.corrections_sha256!==packet.input_fingerprints.corrections_sha256||value.revision!==1||value.parent_revision_sha256!==null||value.owner_identity_verified!==false||value.accepted_positions!==false||value.comparisons_eligible!==false)throw Error('Packet identity or review contract does not match.');
  if(!Array.isArray(value.choices)||value.choices.length!==count)throw Error('Review choices do not match packet membership.');
  const ids=packet.rows.map(r=>r.id).sort();value.choices.forEach((c,i)=>{if(!exactKeys(c,['row_id','label','note'])||c.row_id!==ids[i]||!allowed.includes(c.label)||typeof c.note!=='string'||c.note.length>2000)throw Error('Invalid review choice.');});
  const unsigned={...value};delete unsigned.revision_sha256;if(value.revision_sha256!==await digest(unsigned))throw Error('Review content digest does not match.');
  const f=value.filters;if(!exactKeys(f,['country','capacity','policy','correction_status','status'])||!['all',...countries].includes(f.country)||!['all',...capacities].includes(f.capacity)||!['all',...correctionStatuses].includes(f.correction_status)||!['all',...policies].includes(f.policy)||!['all','unreviewed',...allowed.slice(1)].includes(f.status))throw Error('Invalid saved filters.');
 }
 $('open').onchange=async()=>{try{const file=$('open').files[0];if(!file)return;if(file.size>5000000)throw Error('Review file is too large.');const data=JSON.parse(await file.text());await validate(data);data.choices.forEach(x=>Object.assign(choices.find(c=>c.row_id===x.row_id),x));Object.assign(filters,data.filters);for(const [id,key]of [['country','country'],['capacity','capacity'],['policy','policy'],['correctionStatus','correction_status'],['reviewStatus','status']])$(id).value=filters[key];draw();$('status').textContent+=' Saved choices and filters reopened.';}catch(error){$('status').textContent='Reopen rejected: '+error.message;}finally{$('open').value='';}};
 draw();
}
module.exports={render};
if(require.main===module){const fs=require('node:fs');if(process.argv.length!==4)throw Error('Usage: node private_review_html.cjs private-packet.json private-output.html');fs.writeFileSync(process.argv[3],render(JSON.parse(fs.readFileSync(process.argv[2],'utf8'))),{flag:'wx'});}
