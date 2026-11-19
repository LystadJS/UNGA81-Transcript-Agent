/* Manual outreach records. No transcript inference, electorate or vote prediction. */
(function(root){
 'use strict';
 const SCHEMA='un.campaign-notebook.v3',LIMIT=1048576,MAX=250,encoder=new TextEncoder();
 const STATUSES=Object.freeze({unrecorded:'Not assessed',planned:'Outreach planned',contacted:'Contacted',support_reported:'Support reported',conditional:'Conditional support reported',declined:'Support declined',unclear:'Unclear'});
 const KINDS=Object.freeze({meeting:'Meeting',call:'Call',email:'Email',note:'Other / note'}),LOG_MAX=100,TOTAL_LOG_MAX=1000;
 const CONTACT_MAX=25,TOTAL_CONTACT_MAX=1000,contactFields={id:64,name:160,role:160,email:320,notes:2000};
 const logFields={id:64,date:10,kind:16,contact:160,email:320,summary:4000,reference:2000};
 const campaignFields={title:160,candidate:160,body:160,election_date:10,notes:8000},entryFields={country:160,contact:160,role:160,email:320,status:32,status_date:10,follow_up_date:10,reference:2000,notes:4000};
 const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(k=>Object.hasOwn(value,k));
 function text(value,max,required=false){
  if(typeof value!=='string'||value.length>max||(required&&!value.trim()))throw Error('Complete required fields and keep text within its stated limit.');
  for(const c of value){const n=c.codePointAt(0);if((n<32&&![9,10,13].includes(n))||(n>=0xd800&&n<=0xdfff))throw Error('Unsupported text character. Exact JSON text was not changed.');}
  return value;
 }
 function date(value){return typeof value==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value)&&+value.slice(0,4)>=1900&&+value.slice(0,4)<=9998&&Number.isFinite(Date.parse(value+'T00:00:00Z'))&&new Date(value+'T00:00:00Z').toISOString().slice(0,10)===value;}
 function countries(registry){
  if(!Array.isArray(registry)||!registry.length||registry.some(r=>!r||typeof r.country!=='string'||!r.country.trim()))throw Error('Country/territory registry is unavailable.');
  const values=registry.map(r=>text(r.country,160,true));if(new Set(values).size!==values.length)throw Error('Duplicate country/territory registry labels.');return values.sort((a,b)=>a.localeCompare(b,'en'));
 }
 function bounded(value,label='Notebook'){if(encoder.encode(typeof value==='string'?value:JSON.stringify(value)).length>LIMIT)throw Error(label+' exceeds 1 MiB. Shorten notes or keep fewer records; nothing was truncated.');return value;}
 function normalize(value,fields){if(!exact(value,Object.keys(fields)))throw Error('Unexpected notebook fields. Use campaign notebook JSON v1, v2 or v3.');const result={};for(const [key,max] of Object.entries(fields))result[key]=text(value[key],max,key==='title'||key==='country');return result;}
 function interaction(raw){
  const item=normalize(raw,logFields);if(!/^[a-zA-Z0-9_-]{1,64}$/.test(item.id)||!date(item.date)||!Object.hasOwn(KINDS,item.kind)||!item.summary.trim())throw Error('Complete the interaction date, channel and notes.');return item;
 }
 function interactions(raw){
  if(!Array.isArray(raw)||raw.length>LOG_MAX)throw Error('Keep at most 100 logged interactions per place.');
  const seen=new Set();return raw.map(item=>{const next=interaction(item);if(seen.has(next.id))throw Error('Duplicate interaction identity.');seen.add(next.id);return next;}).sort((a,b)=>a.date.localeCompare(b.date)||a.id.localeCompare(b.id));
 }
 function contact(raw){const item=normalize(raw,contactFields);if(!/^[a-zA-Z0-9_-]{1,64}$/.test(item.id)||!item.name.trim())throw Error('Enter a contact name. Contact identities remain unverified.');return item;}
 function contacts(raw){if(!Array.isArray(raw)||raw.length>CONTACT_MAX)throw Error('Keep at most 25 contact profiles per place.');const seen=new Set();return raw.map(item=>{const next=contact(item);if(seen.has(next.id))throw Error('Duplicate contact profile identity.');seen.add(next.id);return next;}).sort((a,b)=>a.name.localeCompare(b.name,'en')||a.id.localeCompare(b.id));}
 function validate(value,registry){
  if(!exact(value,['schema','campaign','entries'])||![SCHEMA,'un.campaign-notebook.v1','un.campaign-notebook.v2'].includes(value.schema))throw Error('Use a campaign notebook JSON file (v1, v2 or v3).');
  const known=new Set(countries(registry)),campaign=normalize(value.campaign,campaignFields);
  if(campaign.election_date&&!date(campaign.election_date))throw Error('Use a valid campaign date from 1900 through 9998.');
  if(!Array.isArray(value.entries)||value.entries.length>MAX)throw Error('A notebook supports at most 250 geographic records.');
  const seen=new Set();let logCount=0,contactCount=0;const entries=value.entries.map(raw=>{
   const old=value.schema==='un.campaign-notebook.v1';if(!exact(raw,[...Object.keys(entryFields),...(old?[]:['interactions']),...(value.schema===SCHEMA?['contacts']:[])]))throw Error('Unexpected country fields. Use campaign notebook JSON v1, v2 or v3.');
   const fields=Object.fromEntries(Object.keys(entryFields).map(k=>[k,raw[k]])),e=normalize(fields,entryFields);e.contacts=value.schema===SCHEMA?contacts(raw.contacts):[];contactCount+=e.contacts.length;if(contactCount>TOTAL_CONTACT_MAX)throw Error('Keep at most 1,000 contact profiles per notebook.');e.interactions=old?[]:interactions(raw.interactions);logCount+=e.interactions.length;if(logCount>TOTAL_LOG_MAX)throw Error('Keep at most 1,000 logged interactions per notebook.');if(!known.has(e.country)||seen.has(e.country))throw Error('Use one record per registered country/territory. Existing records are not overwritten.');seen.add(e.country);
   if(!Object.hasOwn(STATUSES,e.status))throw Error('Unknown outreach status.');
   if((e.status!=='unrecorded'&&!e.status_date)||(e.status_date&&!date(e.status_date)))throw Error('Choose a valid status date for a recorded outreach status.');
   if(e.follow_up_date&&!date(e.follow_up_date))throw Error('Choose a valid follow-up date from 1900 through 9998.');
   return e;
  }).sort((a,b)=>a.country.localeCompare(b.country,'en'));
  return bounded({schema:SCHEMA,campaign,entries});
 }
 function empty(){return {schema:SCHEMA,campaign:{title:'Untitled campaign',candidate:'',body:'',election_date:'',notes:''},entries:[]};}
 function withEntry(value,entry,registry,editing=null){
  const current=validate(value,registry);if(editing!==null&&editing!==entry.country)throw Error('Country identity stays fixed while editing. Add another record for a different place.');
  const exists=current.entries.some(e=>e.country===entry.country);
  if(editing!==null&&!exists)throw Error('This record is no longer in the notebook.');
  if(editing===null&&exists)throw Error('This country/territory already has a record. Use Edit to update it.');
  return validate({...current,entries:[...current.entries.filter(e=>e.country!==editing),entry]},registry);
 }
 function withoutEntry(value,country,registry){const current=validate(value,registry);if(!current.entries.some(e=>e.country===country))throw Error('This record is no longer in the notebook.');return validate({...current,entries:current.entries.filter(e=>e.country!==country)},registry);}
 function view(entries,{query='',status='',due='',schedule='',order='country'}={}){
  text(query,300);if(status&&!Object.hasOwn(STATUSES,status))throw Error('Unknown status filter.');if(due&&!date(due))throw Error('Choose a valid follow-up filter date.');
  if(!['','dated','undated'].includes(schedule))throw Error('Unknown follow-up date filter.');if(!['country','follow_up','interaction'].includes(order))throw Error('Unknown record order.');
  const words=query.toLocaleLowerCase('en').split(/\s+/).filter(Boolean);
  const rows=entries.filter(e=>(!schedule||(schedule==='dated'?!!e.follow_up_date:!e.follow_up_date))&&(!status||e.status===status)&&(!due||(e.follow_up_date&&e.follow_up_date<=due))&&words.every(w=>[e.country,e.contact,e.role,e.email,e.reference,e.notes,...e.contacts.flatMap(c=>[c.name,c.role,c.email,c.notes]),...e.interactions.flatMap(i=>[i.contact,i.email,i.summary,i.reference,KINDS[i.kind]]),STATUSES[e.status]].join(' ').toLocaleLowerCase('en').includes(w)));
  const latest=e=>e.interactions.reduce((last,i)=>i.date>last?i.date:last,'');
  return rows.sort((a,b)=>{const country=()=>a.country.localeCompare(b.country,'en');if(order==='country')return country();const x=order==='follow_up'?a.follow_up_date:latest(a),y=order==='follow_up'?b.follow_up_date:latest(b);if(!x||!y)return x?-1:y?1:country();return (order==='follow_up'?x.localeCompare(y):y.localeCompare(x))||country();});
 }
 function summary(entries){const counts=Object.fromEntries(Object.keys(STATUSES).map(k=>[k,0]));for(const e of entries){if(!Object.hasOwn(counts,e.status))throw Error('Unknown outreach status.');counts[e.status]++;}return counts;}
 const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const cell=value=>'"'+(/^\s*[=+\-@]/.test(String(value))?"'":'')+String(value).replace(/"/g,'""')+'"';
 function csv(value,registry){const n=validate(value,registry),c=n.campaign,rows=[['campaign_title','candidate','target_body','election_date','country_or_territory','lead_contact','role','contact_address','status_code','status_label','status_recorded_date','follow_up_date','source_reference','country_notes','record_kind']];for(const e of n.entries)rows.push([c.title,c.candidate,c.body,c.election_date,e.country,e.contact,e.role,e.email,e.status,STATUSES[e.status],e.status_date,e.follow_up_date,e.reference,e.notes,'user_entered_outreach_not_actual_vote']);return bounded(rows.map(r=>r.map(cell).join(',')).join('\r\n')+'\r\n','Country CSV');}
 function logCSV(value,registry){const n=validate(value,registry),rows=[['campaign_title','country_or_territory','interaction_id','interaction_date','channel','contact_name','contact_address','interaction_notes','source_reference','record_kind']];for(const e of n.entries)for(const i of e.interactions)rows.push([n.campaign.title,e.country,i.id,i.date,KINDS[i.kind],i.contact,i.email,i.summary,i.reference,'user_entered_interaction_not_verified_event']);return bounded(rows.map(r=>r.map(cell).join(',')).join('\r\n')+'\r\n','Interaction CSV');}
 function contactCSV(value,registry){const n=validate(value,registry),rows=[['campaign_title','country_or_territory','contact_profile_id','contact_name','role','contact_address','contact_notes','record_kind']];for(const e of n.entries)for(const c of e.contacts)rows.push([n.campaign.title,e.country,c.id,c.name,c.role,c.email,c.notes,'user_entered_contact_not_verified_identity']);return bounded(rows.map(r=>r.map(cell).join(',')).join('\r\n')+'\r\n','Contact CSV');}
 const CONTACT_TRANSFER_SCHEMA='un.campaign-contacts.v1';
 function validateContactTransfer(value,registry){
  if(!exact(value,['schema','entries'])||value.schema!==CONTACT_TRANSFER_SCHEMA||!Array.isArray(value.entries)||value.entries.length>MAX)throw Error('Use contact-only transfer JSON (un.campaign-contacts.v1), not a complete notebook or CSV.');
  const known=new Set(countries(registry)),seen=new Set();let count=0;const entries=value.entries.map(raw=>{if(!exact(raw,['country','contacts']))throw Error('Unexpected contact-transfer fields.');const country=text(raw.country,160,true);if(!known.has(country)||seen.has(country))throw Error('Use one registered country/territory per transfer group.');seen.add(country);const list=contacts(raw.contacts);count+=list.length;if(count>TOTAL_CONTACT_MAX)throw Error('Keep at most 1,000 contact profiles per transfer.');return {country,contacts:list};}).sort((a,b)=>a.country.localeCompare(b.country,'en'));return bounded({schema:CONTACT_TRANSFER_SCHEMA,entries},'Contact transfer');
 }
 function contactTransfer(value,registry){const n=validate(value,registry);return validateContactTransfer({schema:CONTACT_TRANSFER_SCHEMA,entries:n.entries.filter(e=>e.contacts.length).map(e=>({country:e.country,contacts:e.contacts}))},registry);}
 function planContactTransfer(value,transfer,registry,options={}){
  if(!exact(options,[])&&!exact(options,['reviewUpdates']))throw Error('Use only the reviewUpdates boolean option.');
  const reviewUpdates=Object.hasOwn(options,'reviewUpdates')?options.reviewUpdates:false;if(typeof reviewUpdates!=='boolean')throw Error('Use a boolean reviewUpdates option.');
  const n=validate(value,registry),incoming=validateContactTransfer(transfer,registry),byCountry=new Map(n.entries.map(e=>[e.country,e])),changes=[];let added=0,updated=0,unchanged=0;
  for(const group of incoming.entries){if(!group.contacts.length)continue;const exists=byCountry.has(group.country),entry=byCountry.get(group.country)||{country:group.country,contact:'',role:'',email:'',status:'unrecorded',status_date:'',follow_up_date:'',reference:'',notes:'',contacts:[],interactions:[]},byID=new Map(entry.contacts.map(c=>[c.id,c])),next=[],updates=[];let same=0;
   for(const item of group.contacts){const previous=byID.get(item.id);if(previous){if(JSON.stringify(previous)!==JSON.stringify(item)){if(!reviewUpdates)throw Error('Conflicting saved contact profile for '+group.country+': '+item.name+'. No profiles were imported; resolve this contact manually or enable change review.');updates.push({before:previous,after:item,fields:['name','role','email','notes'].filter(k=>previous[k]!==item[k])});}else same++;}else next.push(item);}
   added+=next.length;updated+=updates.length;unchanged+=same;
   if(next.length||updates.length){const replacements=new Map(updates.map(u=>[u.after.id,u.after]));byCountry.set(group.country,{...entry,contacts:[...entry.contacts.map(c=>replacements.get(c.id)||c),...next]});changes.push({country:group.country,new_country:!exists,contacts:next,updates});}
  }
  const notebook=validate({...n,entries:[...byCountry.values()]},registry);return {notebook,added,updated,unchanged,changes};
 }
 function html(value,registry){
  const n=validate(value,registry),c=n.campaign,counts=summary(n.entries),field=(label,value)=>'<dt>'+label+'</dt><dd>'+escape(value||'Not recorded')+'</dd>';
  return bounded('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'"><title>'+escape(c.title)+'</title><style>body{font:16px/1.6 system-ui;max-width:1000px;margin:32px auto;padding:20px;color:#182b40}p,dd,li,h1,h2,h3,h4{overflow-wrap:anywhere}dd{margin:0 0 12px;white-space:pre-wrap}dt{font-weight:bold}.notice{border-left:4px solid #805900;padding:12px;background:#fff7e8}section{border-top:1px solid #cbd5df;margin-top:24px;padding-top:12px}section p{white-space:pre-wrap}@media print{h2{break-after:avoid}section{break-inside:auto}}</style><h1>'+escape(c.title)+'</h1><p class="notice">User-entered outreach records. Reported support is not an actual vote, verified identity or vote prediction. The geographic registry is not an eligible-voter roster.</p><dl>'+field('Candidate / purpose',c.candidate)+field('Target body / seat',c.body)+field('Campaign date (user-entered)',c.election_date)+'</dl><h2>All notebook records: '+n.entries.length+'</h2><ul>'+Object.entries(counts).map(([k,v])=>'<li>'+STATUSES[k]+': '+v+' geographic records</li>').join('')+'</ul><section><h2>Campaign notes</h2><p>'+escape(c.notes||'Not recorded')+'</p></section>'+n.entries.map(e=>'<section><h2>'+escape(e.country)+'</h2><dl>'+field('Lead contact (user-entered)',e.contact)+field('Role / organization',e.role)+field('Contact address (unverified)',e.email)+field('Outreach status',STATUSES[e.status])+field('Status recorded date',e.status_date)+field('Follow-up date',e.follow_up_date)+field('Source / conversation reference',e.reference)+'</dl><h3>Country notes</h3><p>'+escape(e.notes||'Not recorded')+'</p><h3>Contact profiles (unverified): '+e.contacts.length+'</h3>'+e.contacts.map(c=>'<div><h4>'+escape(c.name)+'</h4><dl>'+field('Role / organization',c.role)+field('Contact address (unverified)',c.email)+field('Contact notes',c.notes)+'</dl></div>').join('')+'<h3>Manually logged interactions: '+e.interactions.length+'</h3>'+e.interactions.map(i=>'<div><h4>'+escape(i.date)+' · '+KINDS[i.kind]+'</h4><dl>'+field('Contact (user-entered)',i.contact)+field('Contact address (unverified)',i.email)+field('Interaction notes',i.summary)+field('Source reference',i.reference)+'</dl></div>').join('')+(e.interactions.length?'':'<p>No interactions logged. Earlier history is not known.</p>')+'</section>').join('')+(n.entries.length?'':'<p>No country/territory record has been added. This does not describe unrecorded outreach or voting intentions.</p>')+'<p>Reading copy of the complete notebook. Keep campaign notebook JSON to reopen work. Filters do not reduce this copy.</p></html>','Reading HTML');
 }
 const api={CONTACT_UPDATE_VERSION:1,VIEW_VERSION:1,SCHEMA,LIMIT,MAX,STATUSES,KINDS,LOG_MAX,TOTAL_LOG_MAX,CONTACT_MAX,TOTAL_CONTACT_MAX,contact,interaction,date,countries,validate,empty,withEntry,withoutEntry,view,summary,csv,logCSV,contactCSV,CONTACT_TRANSFER_SCHEMA,validateContactTransfer,contactTransfer,planContactTransfer,html};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNCampaignNotebook=api;
})(globalThis);
