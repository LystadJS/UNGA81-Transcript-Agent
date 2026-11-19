/* Manual outreach records. No transcript inference, electorate or vote prediction. */
(function(root){
 'use strict';
 const SCHEMA='un.campaign-notebook.v1',LIMIT=1048576,MAX=250,encoder=new TextEncoder();
 const STATUSES=Object.freeze({unrecorded:'Not assessed',planned:'Outreach planned',contacted:'Contacted',support_reported:'Support reported',conditional:'Conditional support reported',declined:'Support declined',unclear:'Unclear'});
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
 function normalize(value,fields){if(!exact(value,Object.keys(fields)))throw Error('Unexpected notebook fields. Use campaign notebook JSON v1.');const result={};for(const [key,max] of Object.entries(fields))result[key]=text(value[key],max,key==='title'||key==='country');return result;}
 function validate(value,registry){
  if(!exact(value,['schema','campaign','entries'])||value.schema!==SCHEMA)throw Error('Use a campaign notebook JSON file (un.campaign-notebook.v1).');
  const known=new Set(countries(registry)),campaign=normalize(value.campaign,campaignFields);
  if(campaign.election_date&&!date(campaign.election_date))throw Error('Use a valid campaign date from 1900 through 9998.');
  if(!Array.isArray(value.entries)||value.entries.length>MAX)throw Error('A notebook supports at most 250 geographic records.');
  const seen=new Set(),entries=value.entries.map(raw=>{
   const e=normalize(raw,entryFields);if(!known.has(e.country)||seen.has(e.country))throw Error('Use one record per registered country/territory. Existing records are not overwritten.');seen.add(e.country);
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
 function view(entries,{query='',status='',due=''}={}){
  text(query,300);if(status&&!Object.hasOwn(STATUSES,status))throw Error('Unknown status filter.');if(due&&!date(due))throw Error('Choose a valid follow-up filter date.');
  const words=query.toLocaleLowerCase('en').split(/\s+/).filter(Boolean);
  return entries.filter(e=>(!status||e.status===status)&&(!due||(e.follow_up_date&&e.follow_up_date<=due))&&words.every(w=>[e.country,e.contact,e.role,e.email,e.reference,e.notes,STATUSES[e.status]].join(' ').toLocaleLowerCase('en').includes(w)));
 }
 function summary(entries){const counts=Object.fromEntries(Object.keys(STATUSES).map(k=>[k,0]));for(const e of entries){if(!Object.hasOwn(counts,e.status))throw Error('Unknown outreach status.');counts[e.status]++;}return counts;}
 const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const cell=value=>'"'+(/^\s*[=+\-@]/.test(String(value))?"'":'')+String(value).replace(/"/g,'""')+'"';
 function csv(value,registry){const n=validate(value,registry),c=n.campaign,rows=[['campaign_title','candidate','target_body','election_date','country_or_territory','lead_contact','role','contact_address','status_code','status_label','status_recorded_date','follow_up_date','source_reference','country_notes','record_kind']];for(const e of n.entries)rows.push([c.title,c.candidate,c.body,c.election_date,e.country,e.contact,e.role,e.email,e.status,STATUSES[e.status],e.status_date,e.follow_up_date,e.reference,e.notes,'user_entered_outreach_not_actual_vote']);return bounded(rows.map(r=>r.map(cell).join(',')).join('\r\n')+'\r\n','Country CSV');}
 function html(value,registry){
  const n=validate(value,registry),c=n.campaign,counts=summary(n.entries),field=(label,value)=>'<dt>'+label+'</dt><dd>'+escape(value||'Not recorded')+'</dd>';
  return bounded('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'"><title>'+escape(c.title)+'</title><style>body{font:16px/1.6 system-ui;max-width:1000px;margin:32px auto;padding:20px;color:#182b40}p,dd,li,h1,h2{overflow-wrap:anywhere}dd{margin:0 0 12px;white-space:pre-wrap}dt{font-weight:bold}.notice{border-left:4px solid #805900;padding:12px;background:#fff7e8}section{border-top:1px solid #cbd5df;margin-top:24px;padding-top:12px}section p{white-space:pre-wrap}@media print{h2{break-after:avoid}section{break-inside:auto}}</style><h1>'+escape(c.title)+'</h1><p class="notice">User-entered outreach records. Reported support is not an actual vote, verified identity or vote prediction. The geographic registry is not an eligible-voter roster.</p><dl>'+field('Candidate / purpose',c.candidate)+field('Target body / seat',c.body)+field('Campaign date (user-entered)',c.election_date)+'</dl><h2>All notebook records: '+n.entries.length+'</h2><ul>'+Object.entries(counts).map(([k,v])=>'<li>'+STATUSES[k]+': '+v+' geographic records</li>').join('')+'</ul><section><h2>Campaign notes</h2><p>'+escape(c.notes||'Not recorded')+'</p></section>'+n.entries.map(e=>'<section><h2>'+escape(e.country)+'</h2><dl>'+field('Lead contact (user-entered)',e.contact)+field('Role / organization',e.role)+field('Contact address (unverified)',e.email)+field('Outreach status',STATUSES[e.status])+field('Status recorded date',e.status_date)+field('Follow-up date',e.follow_up_date)+field('Source / conversation reference',e.reference)+'</dl><h3>Country notes</h3><p>'+escape(e.notes||'Not recorded')+'</p></section>').join('')+(n.entries.length?'':'<p>No country/territory record has been added. This does not describe unrecorded outreach or voting intentions.</p>')+'<p>Reading copy of the complete notebook. Keep campaign notebook JSON to reopen work. Filters do not reduce this copy.</p></html>','Reading HTML');
 }
 const api={SCHEMA,LIMIT,MAX,STATUSES,date,countries,validate,empty,withEntry,withoutEntry,view,summary,csv,html};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNCampaignNotebook=api;
})(globalThis);
