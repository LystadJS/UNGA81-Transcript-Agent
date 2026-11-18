/* Source-bound personal model drafts; the browser never calls a model endpoint. */
(function(root){
 'use strict';
 const node=typeof module!=='undefined'&&module.exports,Core=node?require('./meeting-report-core.js'):root.UNMeetingReport,Collector=node?require('./collector.js'):root.UNCollector,Reader=node?require('./meeting-quick-reader.js'):root.UNMeetingQuickReader;
 const INPUT='un.report-draft-input.v1',CONTEXT='un.report-draft-context.v1',OUTPUT='un.report-draft.v1',INPUT_LIMIT=65536,LIMIT=262144,encoder=new TextEncoder();
 const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(k=>Object.hasOwn(value,k));
 const canonical=value=>Array.isArray(value)?'['+value.map(canonical).join(',')+']':value&&typeof value==='object'?'{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}':JSON.stringify(value);
 const bytes=value=>encoder.encode(JSON.stringify(value)).length;
 const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function text(value,max,empty=false){
  if(typeof value!=='string'||value.length>max||(!empty&&!value.trim()))throw Error('Invalid draft text or field length.');
  for(const char of value){const n=char.codePointAt(0);if((n<32&&![9,10,13].includes(n))||(n>=0xd800&&n<=0xdfff))throw Error('Draft text contains an unsupported character. Original report work is unchanged.');}
  return value;
 }
 async function createInput(report,policy){
  const questions=Core.questions(report?.settings?.questions);if(!questions.length)throw Error('Add at least one briefing question and prepare the report.');
  const meetings=report.meetings.map(m=>{if(!Core.allowed(m.date,m.slug,policy)||+m.date.slice(0,4)<1)throw Error('Draft source meeting is not eligible.');return {slug:m.slug,date:m.date,title:text(m.title,INPUT_LIMIT),source_url:text(m.source_url,INPUT_LIMIT)};}).sort((a,b)=>a.slug<b.slug?-1:a.slug>b.slug?1:0);
  const selected=new Set(meetings.map(m=>m.slug)),needed=new Set();
  const ordered=questions.map(q=>{text(q.heading,160);text(q.query,300);const record_ids=Core.search(report.records,q.query).map(r=>r.id).sort();record_ids.forEach(id=>needed.add(id));return {...q,record_ids};});
  if(needed.size>100)throw Error('Personal model input exceeds 100 matching passages. Use more specific briefing searches or fewer meetings. Nothing was truncated.');
  const records=report.records.filter(r=>needed.has(r.id)).map(r=>{
   if(!selected.has(r.meeting_slug)||!Reader.safeURL(r.source_url)||!['raw_sha256','text_sha256'].every(k=>/^[a-f0-9]{64}$/.test(r[k])))throw Error('Draft input requires complete source identities.');
   const speaker=r.speaker_metadata||{};
   return {id:text(r.id,INPUT_LIMIT),meeting_slug:r.meeting_slug,date:r.date,country:text(r.country||'',INPUT_LIMIT,true),source_url:r.source_url,raw_sha256:r.raw_sha256,text_sha256:r.text_sha256,json_pointer:text(r.json_pointer,INPUT_LIMIT),text:text(r.text,INPUT_LIMIT),speaker_name:text(speaker.name||'',INPUT_LIMIT,true),speaker_role:text(speaker.function||'',INPUT_LIMIT,true),speaker_group:text(speaker.group||'',INPUT_LIMIT,true),speaking_capacity:Reader.collectiveAttribution(r)?'collective_indicated':'unverified'};
  }).sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0);
  const context={schema:CONTEXT,meetings,source_record_count:report.records.length,questions:ordered,records};
  if(!Number.isInteger(context.source_record_count)||context.source_record_count>15000||records.length!==needed.size)throw Error('Invalid personal draft source scope.');
  // Reserve the fixed envelope before hashing or retaining an oversized packet.
  if(bytes({schema:INPUT,context,context_sha256:'0'.repeat(64)})>INPUT_LIMIT)throw Error('Personal model input exceeds 64 KiB. Use more specific briefing searches or fewer meetings. Nothing was truncated.');
  for(const r of records)if(await Collector.sha(r.text)!==r.text_sha256)throw Error('A draft source text hash differs. Reopen verified report sources.');
  return {schema:INPUT,context,context_sha256:await Collector.sha(canonical(context))};
 }
 function checkOutput(value,packet){
  if(bytes(value)>LIMIT||!exact(value,['schema','context_sha256','generated_at','model','request_count','review_status','sections'])||value.schema!==OUTPUT||value.context_sha256!==packet.context_sha256||value.review_status!=='unreviewed')throw Error('Use an unreviewed personal draft matching this prepared report and its briefing questions.');
  text(value.model,160);if(typeof value.generated_at!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(value.generated_at)||new Date(value.generated_at).toISOString()!==value.generated_at)throw Error('Invalid draft generation time.');
  const context=packet.context,records=new Map(context.records.map(r=>[r.id,r]));
  if(value.request_count!==context.questions.filter(q=>q.record_ids.length).length||!Array.isArray(value.sections)||value.sections.length!==context.questions.length)throw Error('Draft question coverage differs from its input.');
  value.sections.forEach((section,index)=>{
   const q=context.questions[index],known=new Set(q.record_ids);
   if(!exact(section,['heading','query','status','bullets'])||section.heading!==q.heading||section.query!==q.query||!Array.isArray(section.bullets)||section.bullets.length>5)throw Error('Invalid draft section.');
   const status=!known.size?'no_matching_source':section.bullets.length?'generated':'model_abstained';if(section.status!==status||(!known.size&&section.bullets.length))throw Error('Draft does not preserve its evidence gaps.');
   for(const bullet of section.bullets){
    if(!exact(bullet,['text','evidence'])||!Array.isArray(bullet.evidence)||!bullet.evidence.length||bullet.evidence.length>3)throw Error('Each draft bullet needs one to three source quotations.');
    text(bullet.text,1000);const seen=new Set();
    for(const e of bullet.evidence){if(!exact(e,['record_id','quote'])||!known.has(e.record_id))throw Error('Draft cites a passage outside its question evidence.');text(e.quote,1200);const key=e.record_id+'\0'+e.quote;if(seen.has(key)||!records.get(e.record_id).text.includes(e.quote))throw Error('Draft quotation differs from the original source or repeats a citation.');seen.add(key);}
   }
  });
  return value;
 }
 async function open(value,report,policy){return checkOutput(value,await createInput(report,policy));}
 function reviewHTML(value,report,{interactive=false}={}){
  const records=new Map(report.records.map(r=>[r.id,r]));
  return '<section class="personal-model-draft"><h2 id="personal-model-draft" tabindex="-1">Unreviewed personal model draft</h2><p class="notice">Model text is not verified policy or an accepted stance prediction. Quotation checks establish source matching, not factual entailment. Review every claim before using it.</p><p>Declared model: '+escape(value.model)+' · Generated UTC: '+escape(value.generated_at)+' · Model requests: '+value.request_count+'.</p><p>This draft answers its recorded briefing questions from a bounded subset of matching passages. The country overview and comparison gaps above retain the complete selected report scope. Ordinary report exports exclude this draft; keep its JSON separately.</p>'+value.sections.map(s=>'<section><h3>'+escape(s.heading)+'</h3><p>Evidence search: '+escape(s.query)+'</p>'+(s.status==='no_matching_source'?'<p>No matching source passage. No model request was made; this does not establish silence or neutrality.</p>':s.status==='model_abstained'?'<p>The model returned no draft bullets. The question remains unanswered.</p>':s.bullets.map(b=>'<article><p><strong>Unreviewed model text:</strong> '+escape(b.text)+'</p>'+b.evidence.map(e=>{const r=records.get(e.record_id);return '<blockquote>'+escape(e.quote)+'</blockquote><p>Recorded affiliation: '+escape(r.country||'Unresolved attribution')+' · '+escape(r.date)+' · <a href="'+escape(Reader.safeURL(r.source_url))+'" target="_blank" rel="noopener noreferrer">'+escape(r.id)+'</a></p>'+(interactive?'<button type="button" data-evidence-id="'+escape(r.id)+'">Read cited source context</button>':'');}).join('')+'</article>').join(''))+'</section>').join('')+'<details><summary>Draft provenance</summary><p>Input context SHA-256: '+escape(value.context_sha256)+'. A matching hash is a consistency check, not authentication of the model or correctness of its claims.</p></details></section>';
 }
 function standalone(value,report){const html=Core.standalone(report).replace('</html>',reviewHTML(value,report)+'</html>');if(encoder.encode(html).length>Core.LIMIT)throw Error('Draft review HTML exceeds 25 MB. Current work kept.');return html;}
 const api={INPUT,CONTEXT,OUTPUT,INPUT_LIMIT,LIMIT,canonical,createInput,checkOutput,open,reviewHTML,standalone};if(node)module.exports=api;else root.UNReportDraft=api;
})(globalThis);
