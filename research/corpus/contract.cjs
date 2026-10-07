'use strict';
/** Expanded-corpus contract. All text-bearing outputs are local research artifacts. */
const {createHash} = require('node:crypto');
const A = require('../../site/analysis-core.js');
const P = require('../../site/meeting-picker-core.js');
const VERSION = 'passage-corpus-1.0.0';
const validated=new WeakSet();
const TYPES = ['substantive_speech','mixed_speech_procedure','right_of_reply','procedure','speech_fragment','suspected_transcription_issue','uncertain'];
const assert = (ok, message) => { if (!ok) throw Error(message); };
const sha = value => createHash('sha256').update(value).digest('hex');
const stable = x => Array.isArray(x) ? '['+x.map(stable).join(',')+']' : x && typeof x==='object' ? '{'+Object.keys(x).sort().filter(k=>x[k]!==undefined).map(k=>JSON.stringify(k)+':'+stable(x[k])).join(',')+'}' : JSON.stringify(x);
const clone = x => JSON.parse(JSON.stringify(x));
const cp = text => Array.from(text);
const slice = (text,start,end) => cp(text).slice(start,end).join('');
const freeze = x => { if(x && typeof x==='object' && !Object.isFrozen(x)){Object.values(x).forEach(freeze);Object.freeze(x);}return x; };
const unsigned = x => Object.fromEntries(Object.entries(x).filter(([k])=>k!=='sha256'));
const seal = x => freeze({...x,sha256:sha(stable(x))});
function verify(x,schema){assert(x && x.schema===schema,'Expected '+schema);assert(x.sha256===sha(stable(unsigned(x))),'Content digest mismatch: '+schema);return x;}
const unique = xs => [...new Set(xs)];
const by = (rows,key) => {const out=new Map();for(const r of rows){const k=typeof key==='function'?key(r):r[key];if(!out.has(k))out.set(k,[]);out.get(k).push(r);}return out;};
function url(path){const u=new URL(path,'https://transcripts.un.org');assert(u.origin==='https://transcripts.un.org'&&!u.username&&!u.password&&!u.search&&!u.hash,'Unsafe source URL');return u.href;}
function plan(value){
  const x=clone(value);
  const allowed=['schema','selection_rule','development_dates','holdout_dates','split_unit','fit_weighting','partition','language','duplicate_policy','review_policy','country_missing'];
  assert(Object.keys(x).every(k=>allowed.includes(k)),'Unknown plan field; no policy is silently ignored');
  assert(x.schema==='un.passage-plan.v1'&&typeof x.selection_rule==='string'&&x.selection_rule.trim(),'A declared source-selection rule is required');
  assert(Array.isArray(x.development_dates)&&x.development_dates.length&&Array.isArray(x.holdout_dates)&&x.holdout_dates.length,'Both date sets are required');
  const dates=[...x.development_dates,...x.holdout_dates];
  assert(dates.every(P.dateOK)&&unique(dates).length===dates.length&&dates.length<=31,'Invalid, overlapping or excessive dates');
  x.development_dates.sort();x.holdout_dates.sort();
  assert(x.development_dates.at(-1)<x.holdout_dates[0],'Temporal holdout must follow all development dates');
  assert(x.split_unit==='whole_meeting'&&x.fit_weighting==='equal_passage','Only whole-meeting splits and validated equal-passage fitting are supported');
  assert(x.partition?.algorithm==='balanced_whitespace_v1'&&Number.isSafeInteger(x.partition.max_tokens)&&x.partition.max_tokens>=40&&x.partition.max_tokens<=1000,'Invalid partition policy');
  assert(Number.isSafeInteger(x.partition.min_tokens)&&x.partition.min_tokens>=1&&x.partition.min_tokens<=x.partition.max_tokens,'Invalid minimum length');
  assert(x.language==='en'&&x.duplicate_policy==='retain_and_audit','Unsupported language or duplicate policy');
  assert(x.review_policy==='explicit_speech_boundaries'&&x.country_missing==='withhold','Explicit boundaries and fail-closed country weights required');
  return seal(x);
}
function makeFrame(inventory, rawPlan){
  const p=rawPlan.sha256?verify(rawPlan,'un.passage-plan.v1'):plan(rawPlan);
  assert(inventory.schema==='un.inventory-frame.v1'&&inventory.transcripts_opened===0,'Use a metadata-only inventory snapshot');
  const expected=[...p.development_dates,...p.holdout_dates].sort();
  assert(Array.isArray(inventory.dates)&&stable(inventory.dates.map(d=>d.date).sort())===stable(expected),'Inventory must cover every declared date exactly once');
  const meetings=[],pages=[];
  for(const day of inventory.dates){
    let total=null,count=0;
    assert(day.pages?.length>0&&day.pages.length<=50,'Missing inventory pages');
    for(const [index,item] of day.pages.entries()){
      const d=item.data;
      assert(item.url===`https://transcripts.un.org/en/meetings.json?date=${day.date}&xlang=1&page=${index+1}`,'Inventory URL differs from date/page');
      assert(/^[a-f0-9]{64}$/.test(item.sha256),'Missing original inventory response digest');
      assert(d&&Array.isArray(d.meetings)&&d.page===index+1&&Number.isSafeInteger(d.total)&&d.total>=0&&d.total<=15000&&typeof d.hasMore==='boolean','Malformed inventory page');
      if(total===null)total=d.total;
      assert(d.total===total&&d.hasMore===(index<day.pages.length-1),'Incomplete or changing pagination');
      for(const m of d.meetings){
        P.checkMeeting(m,day.date);
        assert(url(m.pageUrl)===`https://transcripts.un.org/en/${m.slug}`,'Meeting URL/identity mismatch');
        assert(!m.hasTranscript||url(m.jsonUrl)===`https://transcripts.un.org/en/${m.slug}.json`,'Transcript URL/identity mismatch');
        meetings.push({meeting_id:m.slug,date:day.date,title:m.title,body:m.body??null,genre:m.category??'Unspecified',duration:m.duration??null,has_transcript:m.hasTranscript,source_url:url(m.pageUrl),json_url:m.hasTranscript?url(m.jsonUrl):null,split:p.development_dates.includes(day.date)?'development':'holdout',source_family_id:m.slug});
      }
      count+=d.meetings.length;
      pages.push({date:day.date,page:index+1,response_sha256:item.sha256,parsed_content_sha256:sha(stable(d)),meetings:d.meetings.length});
    }
    assert(count===total,'Incomplete inventory total');
  }
  assert(unique(meetings.map(m=>m.meeting_id)).length===meetings.length,'Repeated meeting identity across frame');
  assert(meetings.some(m=>m.split==='development')&&meetings.some(m=>m.split==='holdout'),'Both split populations must contain meetings');
  meetings.sort((a,b)=>a.date.localeCompare(b.date)||a.meeting_id.localeCompare(b.meeting_id));
  return seal({schema:'un.passage-frame.v1',engine:VERSION,plan:p,inventory_sha256:sha(stable(inventory)),retrieved_at:inventory.retrieved_at,pages,meetings,holdout_state:'reserved_not_downloaded',prior_exposure:'Not inspected by this stage. Prior exposure elsewhere is unknown; not a claim of globally unseen evidence.',dependence:'Whole meetings and dates are disjoint. Affiliations, recurring series and boilerplate may cross periods; independence is not assumed.'});
}
function validateFrame(frame){
  verify(frame,'un.passage-frame.v1');verify(frame.plan,'un.passage-plan.v1');
  assert(stable(unsigned(plan(unsigned(frame.plan))))===stable(unsigned(frame.plan)),'Plan is not canonical');
  assert(unique(frame.meetings.map(m=>m.meeting_id)).length===frame.meetings.length,'Duplicate meeting');
  for(const m of frame.meetings){assert(P.validSlug(m.meeting_id)&&P.dateOK(m.date),'Invalid meeting identity');assert(m.split===(frame.plan.development_dates.includes(m.date)?'development':frame.plan.holdout_dates.includes(m.date)?'holdout':'invalid'),'Split/date mismatch');}
  return frame;
}
function makeBundle(frame,responses,registry){
  validateFrame(frame);
  const dev=frame.meetings.filter(m=>m.split==='development');
  assert(Array.isArray(responses)&&responses.length===dev.length&&unique(responses.map(r=>r.meeting_id)).length===dev.length,'Account for every development meeting once');
  for(const r of responses){
    const m=dev.find(m=>m.meeting_id===r.meeting_id);assert(m,'Held-out or out-of-frame source cannot enter development');
    assert((r.status==='inventory_unavailable')===(!m.has_transcript),'Inventory availability/status mismatch');
    assert(['downloaded','inventory_unavailable','failed'].includes(r.status),'Unknown acquisition status');
    assert(r.status==='downloaded'?(typeof r.raw_base64==='string'&&r.raw_base64.length>0):!r.raw_base64,'Source bytes/status mismatch');
    if(r.status==='failed')assert(typeof r.error==='string'&&r.error.length,'Record source failure reason');
  }
  assert(Array.isArray(registry),'Country registry required');
  return seal({schema:'un.passage-source-bundle.v1',frame_sha256:frame.sha256,split:'development',registry:clone(registry),registry_sha256:sha(stable(registry)),sources:clone(responses).sort((a,b)=>a.meeting_id.localeCompare(b.meeting_id)),source_text_policy:'Original response bytes are retained; no automatic audio correction or speaker inference.'});
}
function decode(raw){
  assert(typeof raw==='string'&&raw.length<=16*1024*1024&&raw.length%4===0&&/^[A-Za-z0-9+/]*={0,2}$/.test(raw),'Invalid or oversized base64 source');
  const bytes=Buffer.from(raw,'base64');assert(bytes.toString('base64')===raw,'Noncanonical base64 source');
  return {bytes,text:new TextDecoder('utf-8',{fatal:true}).decode(bytes)};
}
function sourceRecords(frame,bundle){
  validateFrame(frame);verify(bundle,'un.passage-source-bundle.v1');
  assert(bundle.frame_sha256===frame.sha256&&bundle.split==='development','Source bundle belongs to a different frame or split');
  assert(stable(unsigned(makeBundle(frame,bundle.sources,bundle.registry)))===stable(unsigned(bundle)),'Invalid source bundle');
  const alias=new Map(),meetings=new Map(frame.meetings.map(m=>[m.meeting_id,m]));
  for(const c of bundle.registry){
    assert(typeof c.country==='string'&&Array.isArray(c.aliases),'Invalid country registry row');
    for(const key of [c.country,...c.aliases]){
      const k=key.toLocaleLowerCase('en-US');
      if(alias.has(k)&&alias.get(k)?.country!==c.country)alias.set(k,null);else if(!alias.has(k))alias.set(k,c);
    }
  }
  const records=[],coverage=[];
  for(const src of bundle.sources){
    const m=meetings.get(src.meeting_id),row={meeting_id:m.meeting_id,date:m.date,split:'development',genre:m.genre,body:m.body,status:src.status,error:src.error??null,raw_sha256:null,source_segments:0,empty_segments:0};coverage.push(row);
    if(src.status!=='downloaded')continue;
    const raw=decode(src.raw_base64);row.raw_sha256=sha(raw.bytes);
    assert(!src.raw_sha256||src.raw_sha256===row.raw_sha256,'Raw source digest mismatch');
    const doc=JSON.parse(raw.text.replace(/^\uFEFF/,''));
    assert(doc.video?.slug===m.meeting_id&&doc.video?.date?.slice(0,10)===m.date,'Raw transcript meeting/date mismatch');
    if(!doc.transcript||!Array.isArray(doc.transcript.data)){row.status='transcript_unavailable';continue;}
    const tr=doc.transcript;row.language=tr.language??'unknown';row.timestamps_flagged=!!tr.timestamps_flagged;row.source_segments=tr.data.length;
    assert(tr.data.length<=15000,'Source segment limit exceeded');
    for(const [index,s] of tr.data.entries()){
      assert(s&&Array.isArray(s.paragraphs??[]),'Malformed source segment');
      const sentences=[];let text='';
      for(const [pi,par] of (s.paragraphs||[]).entries()){
        assert(Array.isArray(par.sentences??[]),'Malformed sentence list');
        for(const [si,sentence] of (par.sentences||[]).entries()){
          assert(typeof sentence.text==='string','Malformed sentence text');
          if(sentences.length)text+=' ';
          const start=cp(text).length;text+=sentence.text;
          sentences.push({start,end:cp(text).length,json_pointer:`/transcript/data/${index}/paragraphs/${pi}/sentences/${si}/text`});
        }
      }
      const speaker=s.speaker||{},aff=String(speaker.affiliation||speaker.affiliation_full||'');
      const c=alias.get(aff.toLocaleLowerCase('en-US'))||alias.get(String(speaker.affiliation_full||'').toLocaleLowerCase('en-US'));
      if(!text.trim())row.empty_segments++;
      records.push({id:m.meeting_id+'#'+index,meeting_id:m.meeting_id,date:m.date,split:'development',genre:m.genre,body:m.body,source_url:m.source_url,json_pointer:'/transcript/data/'+index,raw_sha256:row.raw_sha256,text,text_sha256:sha(text),sentences,speaker_metadata:clone(speaker),affiliation_raw:aff,country:c?.country??null,region:c?.region??null,language:tr.language??'unknown',timestamps_flagged:!!tr.timestamps_flagged,unit:'source_segment',speech_id:null,review_status:'pending',review_type:null,extent:'unknown'});
    }
    row.status=tr.data.length?'collected':'empty_transcript';
  }
  assert(records.length<=50000&&records.reduce((n,r)=>n+r.text.length,0)<=50000000,'Expanded source envelope exceeded; no truncation performed');
  return {records,coverage};
}
function applyReview(records,bundle,review){
  if(!review)return records;
  assert(review.schema==='un.corpus-boundary-review.v1'&&review.source_bundle_sha256===bundle.sha256&&Array.isArray(review.choices),'Review must bind the exact source bundle');
  assert(unique(review.choices.map(c=>c.id)).length===review.choices.length,'Duplicate boundary choice');
  const lookup=new Map(records.map(r=>[r.id,r]));
  for(const c of review.choices){
    const r=lookup.get(c.id);
    assert(r&&r.text_sha256===c.text_sha256,'Boundary choice source mismatch');
    if(c.confirmed===false)continue; // Pending templates never become human decisions.
    assert(c.confirmed===true&&TYPES.includes(c.type)&&typeof c.reviewer==='string'&&c.reviewer.trim()&&/(Z|[+-]\d\d:\d\d)$/.test(c.reviewed_at||'')&&Number.isFinite(Date.parse(c.reviewed_at))&&Date.parse(c.reviewed_at)<=Date.now()+300000,'Invalid explicit boundary review');
    assert(['complete','near_complete','fragment','unknown'].includes(c.extent),'Declare observed speech extent');
    if(['complete','near_complete'].includes(c.extent))assert(typeof c.speech_id==='string'&&c.speech_id.trim(),'Complete speech needs an explicit speech ID');
    if(c.extent==='near_complete')assert(typeof c.note==='string'&&c.note.trim(),'Explain near-complete coverage');
    Object.assign(r,{speech_id:c.speech_id||null,extent:c.extent,review_type:c.type,review_status:'confirmed',review_choice:clone(c)});
  }
  for(const rows of by(records.filter(r=>r.speech_id),'speech_id').values()){
    assert(unique(rows.map(r=>r.meeting_id)).length===1,'A speech cannot cross meetings');
    assert(unique(rows.map(r=>r.country)).length===1&&unique(rows.map(r=>r.affiliation_raw)).length===1,'Speech affiliation conflicts');
    assert(unique(rows.map(r=>stable(r.speaker_metadata))).length===1,'Speech speaker metadata conflicts');
  }
  return records;
}
/** Contiguous exact slices: no ellipses, overlap, dropped whitespace or silent truncation. */
function partition(text,maxTokens){
  const chars=cp(text),spans=[];let active=false,start=0;
  for(let i=0;i<chars.length;i++){if(!/\s/u.test(chars[i])&&!active){start=i;active=true;}if(/\s/u.test(chars[i])&&active){spans.push([start,i]);active=false;}}
  if(active)spans.push([start,chars.length]);
  if(!chars.length)return [];
  if(!spans.length)return [{start:0,end:chars.length,tokens:0}];
  const k=Math.ceil(spans.length/maxTokens),base=Math.floor(spans.length/k),extra=spans.length%k,result=[];let n=0,left=0;
  for(let j=0;j<k;j++){const count=base+(j<extra?1:0);n+=count;const end=j===k-1?chars.length:spans[n][0];result.push({start:left,end,tokens:count});left=end;}
  return result;
}
function build(frame,bundle,review=null){
  const {records,coverage}=sourceRecords(frame,bundle);applyReview(records,bundle,review);
  const p=frame.plan,passages=[];
  for(const r of records){
    for(const [index,s] of partition(r.text,p.partition.max_tokens).entries()){
      const text=slice(r.text,s.start,s.end),exclusions=[];
      if(r.language!==p.language)exclusions.push('excluded_language');
      if(!text.trim())exclusions.push('empty_text');
      if(s.tokens<p.partition.min_tokens)exclusions.push('short_partition');
      if(['procedure','suspected_transcription_issue','uncertain'].includes(r.review_type))exclusions.push('reviewed_'+r.review_type);
      const speechExclusions=[...exclusions];
      if(r.review_status!=='confirmed')speechExclusions.push('boundary_review_pending');
      if(!r.speech_id||!['complete','near_complete'].includes(r.extent))speechExclusions.push('speech_extent_unresolved');
      if(r.review_status==='confirmed'&&!['substantive_speech','mixed_speech_procedure','right_of_reply'].includes(r.review_type))speechExclusions.push('not_reviewed_speech');
      passages.push({id:r.id+'@'+s.start+':'+s.end,parent_id:r.id,meeting_id:r.meeting_id,speech_id:r.speech_id,date:r.date,split:r.split,genre:r.genre,body:r.body,country:r.country,region:r.region,affiliation_raw:r.affiliation_raw,language:r.language,source_url:r.source_url,raw_sha256:r.raw_sha256,parent_text_sha256:r.text_sha256,json_pointer:r.json_pointer,parent_start:s.start,parent_end:s.end,offset_unit:'Unicode code points; zero-based; end-exclusive',partition_index:index,tokens:s.tokens,text,text_sha256:sha(text),normalized_text_sha256:sha(text.normalize('NFKC').replace(/\s+/gu,' ').trim()),review_status:r.review_status,review_type:r.review_type,extent:r.extent,exclusions,speech_exclusions:unique(speechExclusions),timestamps_flagged:r.timestamps_flagged});
    }
  }
  const duplicateFamilies=[...by(passages.filter(r=>r.text.trim()),'normalized_text_sha256')].filter(([,rs])=>rs.length>1).map(([hash,rs])=>({normalized_text_sha256:hash,ids:rs.map(r=>r.id),policy:'Retained: identical wording across distinct source occurrences is not proof of duplicate collection.'}));
  const passageParents=by(passages,'parent_id');
  const parentCoverage=records.map(r=>{const ps=passageParents.get(r.id)||[];return {parent_id:r.id,meeting_id:r.meeting_id,speech_id:r.speech_id,observed_code_points:cp(r.text).length,partitioned_code_points:ps.reduce((n,p)=>n+p.parent_end-p.parent_start,0),source_eligible_code_points:ps.filter(p=>!p.exclusions.length).reduce((n,p)=>n+p.parent_end-p.parent_start,0),speech_eligible_code_points:ps.filter(p=>!p.speech_exclusions.length).reduce((n,p)=>n+p.parent_end-p.parent_start,0),partitions:ps.length,review_status:r.review_status,extent:r.extent,coverage_basis:'Observed source segment, not independently verified delivered-speech coverage'};});
  assert(parentCoverage.every(r=>r.observed_code_points===r.partitioned_code_points),'Source partition coverage mismatch');
  const out={schema:'un.passage-corpus.v1',engine:VERSION,frame:clone(frame),source_bundle:clone(bundle),boundary_review:clone(review),parents:records,parent_coverage:parentCoverage,passages,coverage,duplicate_families:duplicateFamilies,counts:{meetings:coverage.length,parents:records.length,passages:passages.length,source_segment_eligible:passages.filter(r=>!r.exclusions.length).length,reviewed_speech_eligible:passages.filter(r=>!r.speech_exclusions.length).length,reserved_meetings:frame.meetings.filter(m=>m.split==='holdout').length},interpretation:'Complete partitions of observed source segments; only explicitly reviewed complete/near-complete speech IDs support speech denominators. Source segments are not automatically speeches. No population-representative or nonrandomness claim.'};
  const sealed=seal(out);validated.add(sealed);return sealed;
}
function load(corpus){verify(corpus,'un.passage-corpus.v1');const derived=build(corpus.frame,corpus.source_bundle,corpus.boundary_review);assert(derived.sha256===corpus.sha256,'Corpus lineage/coverage differs from exact source re-derivation');return derived;}
function select(corpus,{population='reviewed_speeches',meeting_id=null}={}){
  if(!validated.has(corpus))corpus=load(corpus);
  assert(['reviewed_speeches','source_segments'].includes(population),'Unknown analytical population');
  if(meeting_id)assert(corpus.frame.meetings.some(m=>m.meeting_id===meeting_id&&m.split==='development'),'Only a development meeting may be selected');
  const rows=corpus.passages.filter(r=>(!meeting_id||r.meeting_id===meeting_id)&&!(population==='reviewed_speeches'?r.speech_exclusions:r.exclusions).length);
  assert(rows.every(r=>r.split==='development'),'Held-out content is prohibited from development fitting');
  return {rows,population,meeting_id,selection_sha256:sha(stable(rows.map(r=>[r.id,r.text_sha256]))),review_warning:population==='source_segments'?'Audit-only; unreviewed source segments may include mixed speech and procedure.':null};
}
function weights(selection,scheme='equal_passage'){
  const rows=selection.rows,n=rows.length;
  assert(unique(rows.map(r=>r.id)).length===n&&rows.every(r=>r.split==='development'&&sha(r.text)===r.text_sha256),'Invalid weighted observation identity, split or text');
  assert(selection.selection_sha256===sha(stable(rows.map(r=>[r.id,r.text_sha256]))),'Weight population digest mismatch');
  assert(['equal_passage','equal_speech','equal_country','equal_meeting'].includes(scheme),'Unknown weighting scheme');
  const base={schema:'un.passage-weights.v1',scheme,population:selection.population,selection_sha256:selection.selection_sha256,role:'Descriptive composition weights, NOT a weighted refit or survey inclusion probabilities',denominator:n};
  if(!n)return {...base,status:'withheld',reason:'No eligible observations',rows:[]};
  if(['equal_speech','equal_country'].includes(scheme)&&rows.some(r=>!r.speech_id||r.review_status!=='confirmed'||!['complete','near_complete'].includes(r.extent)))return {...base,status:'withheld',reason:'Speech boundaries and extent are not confirmed for every selected observation',rows:[]};
  if(scheme==='equal_country'&&rows.some(r=>!r.country))return {...base,status:'withheld',reason:'Country attribution is missing or ambiguous; no unknown-country pseudo-state or silent known-only subset',rows:[]};
  const speech=by(rows,r=>r.meeting_id+'|'+r.speech_id),meeting=by(rows,'meeting_id'),countries=by(rows,'country');
  const values=rows.map(r=>{
    let w=1/n;
    if(scheme==='equal_meeting')w=1/(meeting.size*meeting.get(r.meeting_id).length);
    if(scheme==='equal_speech')w=1/(speech.size*speech.get(r.meeting_id+'|'+r.speech_id).length);
    if(scheme==='equal_country')w=1/(countries.size*unique(countries.get(r.country).map(x=>x.meeting_id+'|'+x.speech_id)).length*speech.get(r.meeting_id+'|'+r.speech_id).length);
    return {id:r.id,text_sha256:r.text_sha256,weight:w,meeting_id:r.meeting_id,speech_id:r.speech_id,country:r.country};
  });
  const sum=values.reduce((a,r)=>a+r.weight,0);assert(Math.abs(sum-1)<1e-10,'Weight normalization failure');
  return {...base,status:'available',rows:values,weight_sum:sum,kish_weight_concentration:1/values.reduce((a,r)=>a+r.weight*r.weight,0),independent_sample_size:null,meetings:meeting.size,speeches:rows.every(r=>r.speech_id)?speech.size:null,countries:unique(rows.map(r=>r.country).filter(Boolean)).length};
}
function composition(selection,points,scheme){
  const w=weights(selection,scheme);if(w.status!=='available')return w;
  assert(Array.isArray(points)&&unique(points.map(p=>p.id)).length===points.length,'Duplicate fit assignments');
  const ids=new Map(selection.rows.map(r=>[r.id,r]));
  for(const p of points)assert(ids.get(p.id)?.text_sha256===p.text_sha256&&Number.isSafeInteger(p.cluster)&&p.cluster>=0,'Fit assignment identity, hash or label mismatch');
  const labels=new Map(points.map(p=>[p.id,p.cluster===0?'unassigned':String(p.cluster)])),totals=new Map();
  for(const row of w.rows){const label=labels.get(row.id)||'not_fitted';if(!totals.has(label))totals.set(label,{label,passages:0,share:0});const t=totals.get(label);t.passages++;t.share+=row.weight;}
  return {...unsigned(w),rows:undefined,totals:[...totals.values()],assignment_denominator:'All eligible observations; missing vectors/failed fits retain not_fitted mass. No renormalization on assigned rows.'};
}
const referenceTokens=text=>A.tokens(text); // Deliberately preserves negation; versioned separately from browser stop words.
function fitReference(corpus,options={}){
  assert(Object.keys(options).every(k=>['population','meeting_id','fit_weighting','max_features','clustering'].includes(k)),'Unknown reference option');
  const c=load(corpus),s=select(c,options);assert(s.rows.length>0,'No development observations for a reference');
  assert((options.fit_weighting||'equal_passage')==='equal_passage','Weighted model fitting is not validated; summary weights cannot change the objective');
  const max=options.max_features??20000;assert(Number.isSafeInteger(max)&&max>=10&&max<=50000,'Invalid vocabulary bound');
  const df=new Map();for(const r of s.rows)for(const t of unique(referenceTokens(r.text)))df.set(t,(df.get(t)||0)+1);
  const sorted=[...df].sort((a,b)=>b[1]-a[1]||(a[0]<b[0]?-1:a[0]>b[0]?1:0));
  const vocabulary=sorted.slice(0,max).map(([term,documents])=>({term,documents,idf:1+Math.log((1+s.rows.length)/(1+documents))}));
  return seal({schema:'un.passage-reference.v1',engine:VERSION,runtime:{node:process.version,unicode:process.versions.unicode,icu:process.versions.icu},fit_split:'development',fit_weighting:'equal_passage',corpus_sha256:c.sha256,frame_sha256:c.frame.sha256,plan_sha256:c.frame.plan.sha256,selection:{population:s.population,meeting_id:s.meeting_id,selection_sha256:s.selection_sha256},tokenizer:'NFKC lowercase Unicode letter/number tokens; no stop list; negation retained',tokens_engine_sha256:sha(require('node:fs').readFileSync(require.resolve('../../site/analysis-core.js'))),max_features:max,omitted_terms:Math.max(0,df.size-max),training_ids:s.rows.map(r=>({id:r.id,text_sha256:r.text_sha256,normalized_text_sha256:r.normalized_text_sha256,meeting_id:r.meeting_id,parent_id:r.parent_id,raw_sha256:r.raw_sha256})),vocabulary,formula:'tf=1+log(count); idf=1+log((1+n_development)/(1+df_development)); row L2 normalization',model_role:'Lexical reference only; not a fitted PCA, semantic encoder or clustering model'});
}
function transform(reference,rows,access={}){
  verify(reference,'un.passage-reference.v1');assert(reference.engine===VERSION&&reference.tokens_engine_sha256===sha(require('node:fs').readFileSync(require.resolve('../../site/analysis-core.js'))),'Reference tokenizer/runtime mismatch');assert(unique(rows.map(r=>r.id)).length===rows.length,'Repeated transform identity');
  assert(rows.every(r=>['development','holdout'].includes(r.split)),'Declare transform split');
  if(rows.some(r=>r.split==='holdout')){
    assert(rows.every(r=>r.split==='holdout'),'Do not mix development and holdout during evaluation');
    const allowed=authorizeHoldout(access.frame,reference,access.lock);
    assert(rows.every(r=>allowed.includes(r.meeting_id)),'Out-of-frame held-out source');
    const train=reference.training_ids;
    assert(rows.every(r=>!train.some(t=>t.meeting_id===r.meeting_id||t.parent_id===r.parent_id||t.raw_sha256===r.raw_sha256)),'Holdout source-family leakage');
    assert(rows.every(r=>!train.some(t=>t.normalized_text_sha256===sha(r.text.normalize('NFKC').replace(/\s+/gu,' ').trim()))),'Exact normalized text overlaps development; quarantine and record before evaluation');
  }
  const vocab=new Map(reference.vocabulary.map(v=>[v.term,v.idf]));
  return rows.map(r=>{assert(sha(r.text)===r.text_sha256,'Transform text digest mismatch');const counts=new Map(),tokens=referenceTokens(r.text);let retained=0;for(const t of tokens)if(vocab.has(t)){retained++;counts.set(t,(counts.get(t)||0)+1);}const values=[...counts].map(([t,n])=>[t,(1+Math.log(n))*vocab.get(t)]);const norm=Math.sqrt(values.reduce((a,[,v])=>a+v*v,0));return {id:r.id,text_sha256:r.text_sha256,vector:values.map(([t,v])=>[t,v/(norm||1)]),token_coverage:tokens.length?retained/tokens.length:null,out_of_vocabulary_tokens:tokens.length-retained,status:norm?'usable':'zero_vector'};});
}
function comparisonLock(frame,reference,settings){
  validateFrame(frame);verify(reference,'un.passage-reference.v1');
  assert(reference.frame_sha256===frame.sha256,'Reference/frame mismatch');
  assert(settings&&typeof settings.question==='string'&&settings.question.trim()&&Array.isArray(settings.metrics)&&settings.metrics.length&&settings.metrics.every(m=>typeof m==='string'&&m.trim())&&typeof settings.model_sha256==='string'&&/^[a-f0-9]{64}$/.test(settings.model_sha256),'Freeze the question, named metrics and fitted development model digest first');
  return seal({schema:'un.passage-comparison-lock.v1',frame_sha256:frame.sha256,plan_sha256:frame.plan.sha256,reference_sha256:reference.sha256,settings:clone(settings),holdout_ids:frame.meetings.filter(m=>m.split==='holdout').map(m=>m.meeting_id),role:'Prospective evaluation lock, not an evaluation result or proof of statistical independence'});
}
function authorizeHoldout(frame,reference,lock){validateFrame(frame);verify(reference,'un.passage-reference.v1');verify(lock,'un.passage-comparison-lock.v1');assert(lock.frame_sha256===frame.sha256&&lock.reference_sha256===reference.sha256&&lock.plan_sha256===frame.plan.sha256&&stable(lock.holdout_ids)===stable(frame.meetings.filter(m=>m.split==='holdout').map(m=>m.meeting_id)),'Held-out access lock mismatch');return lock.holdout_ids;}
function audit(corpus){
  const c=load(corpus),s=select(c,{population:'source_segments'}),reviewed=select(c),frame=c.frame;
  const histogram=key=>[...by(c.passages,key)].map(([value,rs])=>({value,passages:rs.length,parents:unique(rs.map(r=>r.parent_id)).length,meetings:unique(rs.map(r=>r.meeting_id)).length}));
  return {schema:'un.passage-audit.v1',engine:VERSION,corpus_sha256:c.sha256,frame_sha256:frame.sha256,plan_sha256:frame.plan.sha256,counts:c.counts,source_statuses:[...by(c.coverage,'status')].map(([status,rows])=>({status,meetings:rows.length})),length:{min:c.passages.length?c.passages.reduce((v,p)=>Math.min(v,p.tokens),Infinity):0,max:c.passages.reduce((v,p)=>Math.max(v,p.tokens),0)},by_date:histogram('date'),by_genre:histogram('genre'),by_language:histogram('language'),by_review:histogram('review_status'),unknown_country_passages:c.passages.filter(p=>!p.country).length,duplicate_families:c.duplicate_families.length,weights:{source_segments:['equal_passage','equal_meeting','equal_speech','equal_country'].map(mode=>{const {rows,...rest}=weights(s,mode);return rest;}),reviewed_speeches:['equal_passage','equal_speech','equal_country'].map(mode=>{const {rows,...rest}=weights(reviewed,mode);return rest;})},holdout:{meetings:frame.meetings.filter(m=>m.split==='holdout').length,transcripts_downloaded:0,state:frame.holdout_state,text_overlap_check:'Not yet assessable: held-out transcript bytes have not been opened',independence:'Not established; temporal and meeting separation only'},originals_changed:false,publication_gate_changed:false};
}
module.exports={VERSION,TYPES,assert,sha,stable,seal,verify,plan,makeFrame,validateFrame,makeBundle,sourceRecords,build,load,select,weights,composition,fitReference,transform,comparisonLock,authorizeHoldout,audit,partition,slice};
