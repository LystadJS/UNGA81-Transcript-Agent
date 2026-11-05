#!/usr/bin/env node
'use strict';

/* Offline scorer for source-registered, owner-reviewed daily summaries. It
 * consumes decisions and hashes only and never opens source or transcript text. */
const fs=require('node:fs');
const crypto=require('node:crypto');
const REVIEW_SCHEMA='un.day-summary-owner-review.v1';
const LOCK_SCHEMA='un.day-summary-evaluation-lock.v1';
const REGISTRATION_SCHEMA='un.day-summary-sample-registration.v1';
const BROWSER_SCHEMA='un.day-summary-one-action-browser-receipt.v1';
const RESULT_SCHEMA='un.day-summary-evaluation.v1';
const METRICS={
  unsupported_claim_rate:{field:'claim_reviews',error:'unsupported',pass:'supported',coverage:'generated_substantive_claims'},
  missed_substantive_topic_rate:{field:'topic_reviews',error:'missed',pass:'found',coverage:'owner_substantive_topics'},
  incorrect_grouping_rate:{field:'grouping_reviews',error:'incorrect',pass:'correct',coverage:'grouping_decisions'},
  attribution_error_rate:{field:'attribution_reviews',error:'incorrect',pass:'correct',coverage:'country_attribution_decisions'}
};
function canonical(value){if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';if(value&&typeof value==='object')return '{'+Object.keys(value).sort().map(key=>JSON.stringify(key)+':'+canonical(value[key])).join(',')+'}';return JSON.stringify(value);}
function digest(value){return crypto.createHash('sha256').update(canonical(value)).digest('hex');}
function withoutHashDigest(value){const copy=structuredClone(value);delete copy.canonical_sha256;return digest(copy);}
function lockDigest(lock){return withoutHashDigest(lock);}
function registrationDigest(registration){return withoutHashDigest(registration);}
function iso(value){return typeof value==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(value)&&!Number.isNaN(Date.parse(value));}
function date(value){return typeof value==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value)&&!Number.isNaN(Date.parse(value));}
function sha(value){return typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);}
function uniqueStrings(values,label,allowEmpty=false){if(!Array.isArray(values)||(!allowEmpty&&!values.length)||values.some(value=>typeof value!=='string'||!value.trim())||new Set(values).size!==values.length)throw Error('Invalid '+label+'.');return values;}
function finiteRate(value,label){if(typeof value!=='number'||!Number.isFinite(value)||value<0||value>1)throw Error('Invalid '+label+'.');return value;}

function validateLock(lock){
  if(!lock||lock.schema!==LOCK_SCHEMA||!iso(lock.locked_at))throw Error('Unsupported or invalid acceptance lock.');
  const commitments=lock.sample_commitments||{};uniqueStrings(commitments.development_sample_ids,'legacy development sample IDs',true);
  if(commitments.untouched_test_sample_id!==null&&typeof commitments.untouched_test_sample_id!=='string')throw Error('Invalid legacy untouched sample ID.');
  for(const key of Object.keys(METRICS))finiteRate(lock.metrics?.[key]?.maximum,key+' threshold');
  if(!Number.isInteger(lock.critical_error_maximum)||lock.critical_error_maximum<0)throw Error('Invalid critical-error threshold.');
  for(const split of ['development','untouched_test']){const c=lock.minimum_coverage?.[split];for(const key of ['days','un_bodies','meeting_types','meetings','generated_substantive_claims','owner_substantive_topics','grouping_decisions','country_attribution_decisions'])if(!Number.isInteger(c?.[key])||c[key]<1)throw Error('Invalid '+split+' coverage threshold: '+key+'.');}
  const gate=lock.one_action_browser_gate;if(!gate||typeof gate.activation!=='string'||!Array.isArray(gate.viewports)||!gate.viewports.length||!Array.isArray(gate.required_outputs)||!gate.required_outputs.length)throw Error('Invalid one-action browser gate.');
  if(!sha(lock.canonical_sha256)||lock.canonical_sha256!==lockDigest(lock))throw Error('Acceptance lock hash mismatch.');return lock;
}

function validateRegistration(input,lock){
  const registration=structuredClone(input);
  if(!registration||registration.schema!==REGISTRATION_SCHEMA||!iso(registration.created_at)||registration.threshold_lock_sha256!==lock.canonical_sha256)throw Error('Unsupported registration or threshold-lock binding mismatch.');
  if(!Array.isArray(registration.samples))throw Error('Registration samples must be an array.');
  const sampleIds=new Set(),meetingIds=new Set(),sourceBindings=new Map(),splitDates={development:new Set(),test:new Set()},splitSources={development:new Set(),test:new Set()},splitSourceHashes={development:new Set(),test:new Set()};
  for(const sample of registration.samples){
    if(!sample||typeof sample.sample_id!=='string'||!sample.sample_id||sampleIds.has(sample.sample_id)||!['development','test'].includes(sample.split)||!iso(sample.registered_at)||!Array.isArray(sample.days)||!sample.days.length)throw Error('Invalid or duplicate registered sample.');
    sampleIds.add(sample.sample_id);const dayIds=new Set();
    for(const day of sample.days){
      if(!day||typeof day.day_id!=='string'||!day.day_id||dayIds.has(day.day_id)||!date(day.date)||!Array.isArray(day.meetings)||!day.meetings.length)throw Error('Invalid registered day.');dayIds.add(day.day_id);splitDates[sample.split].add(day.date);
      for(const meeting of day.meetings){
        if(!meeting||typeof meeting.id!=='string'||!meeting.id||meetingIds.has(meeting.id)||typeof meeting.body!=='string'||!meeting.body||typeof meeting.meeting_type!=='string'||!meeting.meeting_type||!Array.isArray(meeting.sources)||!meeting.sources.length)throw Error('Invalid or duplicate registered meeting.');meetingIds.add(meeting.id);
        for(const source of meeting.sources){if(!source||typeof source.id!=='string'||!source.id||!sha(source.sha256))throw Error('Registered source requires an ID and SHA-256 hash.');const prior=sourceBindings.get(source.id);if(prior&&prior!==source.sha256)throw Error('Source ID is rebound to a different hash.');sourceBindings.set(source.id,source.sha256);splitSources[sample.split].add(source.id);splitSourceHashes[sample.split].add(source.sha256);}
      }
    }
  }
  for(const value of splitDates.development)if(splitDates.test.has(value))throw Error('Development and untouched test dates overlap.');
  for(const value of splitSources.development)if(splitSources.test.has(value))throw Error('Development and untouched test source IDs overlap.');
  for(const value of splitSourceHashes.development)if(splitSourceHashes.test.has(value))throw Error('Development and untouched test source hashes overlap.');
  if(!sha(registration.canonical_sha256)||registration.canonical_sha256!==registrationDigest(registration))throw Error('Registration hash mismatch.');return registration;
}

function readiness(lockInput,registrationInput){
  const lock=validateLock(structuredClone(lockInput));
  if(!registrationInput)return {schema:'un.day-summary-evaluation-readiness.v1',status:'not_evaluated_missing_owner_samples',missing:['source-bound sample registration manifest'],reserved_transcripts_opened:0,lock_sha256:lock.canonical_sha256};
  const registration=validateRegistration(registrationInput,lock),missing=[];
  if(!registration.samples.some(s=>s.split==='development'))missing.push('registered owner-reviewed development daily-summary sample');
  if(!registration.samples.some(s=>s.split==='test'))missing.push('registered untouched owner-reviewed test daily-summary sample');
  return {schema:'un.day-summary-evaluation-readiness.v1',status:missing.length?'not_evaluated_missing_owner_samples':'ready',missing,reserved_transcripts_opened:0,lock_sha256:lock.canonical_sha256,registration_sha256:registration.canonical_sha256};
}

function reviewRows(day,field,spec,meetingMap){
  const rows=day[field];if(!Array.isArray(rows))throw Error(`Missing ${field} for ${day.day_id}.`);const ids=new Set();
  return rows.map(row=>{if(!row||typeof row.id!=='string'||!row.id||ids.has(row.id))throw Error(`Invalid or duplicate ${field} ID for ${day.day_id}.`);ids.add(row.id);if(![spec.error,spec.pass,'unreviewable'].includes(row.verdict))throw Error(`Invalid ${field} verdict for ${day.day_id}.`);const meeting=meetingMap.get(row.meeting_id);if(!meeting||row.body!==meeting.body||row.meeting_type!==meeting.meeting_type)throw Error(`Every ${field} row must carry registered meeting_id, body, and meeting_type.`);return row;});
}

function validateReview(input,lock,registration){
  const review=structuredClone(input);
  if(!review||review.schema!==REVIEW_SCHEMA||!['development','test'].includes(review.split))throw Error('Unsupported owner-review sample.');
  if(review.owner_review?.reviewer_mode!=='owner_single_reviewer'||review.owner_review?.owner_confirmation!==true)throw Error('Actual owner confirmation in the declared single-reviewer mode is required.');
  if(typeof review.sample_id!=='string'||!review.sample_id||!iso(review.evaluation_started_at)||!iso(review.reviewed_at)||review.evaluation_started_at>review.reviewed_at)throw Error('Invalid review identity or timestamps.');
  const registered=registration.samples.find(sample=>sample.sample_id===review.sample_id&&sample.split===review.split);if(!registered)throw Error('Review sample is absent from the source-bound registration.');
  if(registered.registered_at>=review.evaluation_started_at)throw Error('Sample registration must predate review start.');
  if(review.split==='test'&&review.evaluation_started_at<lock.locked_at)throw Error('Untouched test evaluation must begin after the locked thresholds.');
  if(!Array.isArray(review.days)||review.days.length!==registered.days.length)throw Error('Review days do not match registration.');
  const registeredDays=new Map(registered.days.map(day=>[day.day_id,day])),seen=new Set();
  for(const day of review.days){
    const registeredDay=registeredDays.get(day?.day_id);if(!registeredDay||seen.has(day.day_id)||day.date!==registeredDay.date||!sha(day.summary_sha256))throw Error('Reviewed day does not match registration.');seen.add(day.day_id);
    const meetingMap=new Map(registeredDay.meetings.map(m=>[m.id,m]));if(!Array.isArray(day.meetings)||day.meetings.length!==meetingMap.size)throw Error('Reviewed meetings do not match registration.');
    const reviewedMeetings=new Set();for(const meeting of day.meetings){const bound=meetingMap.get(meeting?.id);if(!bound||reviewedMeetings.has(meeting.id)||meeting.body!==bound.body||meeting.meeting_type!==bound.meeting_type)throw Error('Reviewed meetings do not match registration.');reviewedMeetings.add(meeting.id);}
    const bodies=[...new Set(registeredDay.meetings.map(m=>m.body))].sort(),types=[...new Set(registeredDay.meetings.map(m=>m.meeting_type))].sort();
    if(!Array.isArray(day.bodies)||!Array.isArray(day.meeting_types)||JSON.stringify([...day.bodies].sort())!==JSON.stringify(bodies)||JSON.stringify([...day.meeting_types].sort())!==JSON.stringify(types))throw Error('Reviewed body or meeting-type inventory does not match registration.');
    for(const spec of Object.values(METRICS))reviewRows(day,spec.field,spec,meetingMap);
    if(day.critical_errors!==undefined){if(!Array.isArray(day.critical_errors)||day.critical_errors.some(value=>typeof value!=='string'||!value.trim())||new Set(day.critical_errors).size!==day.critical_errors.length)throw Error('critical_errors must contain unique nonempty strings.');}
  }
  return review;
}

function validateBrowserReceipt(input,review,lock,registration){
  if(!input)return {passed:false,reasons:['missing required one-action browser receipt']};
  const receipt=structuredClone(input),gate=lock.one_action_browser_gate,reasons=[];
  if(receipt.schema!==BROWSER_SCHEMA)reasons.push('unsupported receipt schema');if(receipt.sample_id!==review.sample_id)reasons.push('sample ID mismatch');if(receipt.threshold_lock_sha256!==lock.canonical_sha256)reasons.push('threshold lock mismatch');if(receipt.registration_sha256!==registration.canonical_sha256)reasons.push('registration mismatch');
  if(!iso(receipt.tested_at)||receipt.tested_at<review.evaluation_started_at)reasons.push('receipt must occur during or after evaluation start');
  const expectedHashes=[...review.days.map(d=>d.summary_sha256)].sort();if(!Array.isArray(receipt.summary_sha256)||JSON.stringify([...receipt.summary_sha256].sort())!==JSON.stringify(expectedHashes))reasons.push('summary hash mismatch');
  if(receipt.activation!==gate.activation)reasons.push('activation mismatch');if(receipt.completion_rate!==gate.required_completion_rate)reasons.push('completion rate failed');if(!Number.isInteger(receipt.uncaught_javascript_errors)||receipt.uncaught_javascript_errors<0||receipt.uncaught_javascript_errors>gate.uncaught_javascript_errors_maximum)reasons.push('JavaScript error maximum exceeded');if(!Number.isInteger(receipt.document_overflow)||receipt.document_overflow<0||receipt.document_overflow>gate.document_overflow_maximum)reasons.push('document overflow maximum exceeded');
  const viewports=Array.isArray(receipt.viewports)?receipt.viewports:[];for(const required of gate.viewports)if(!viewports.some(v=>v.width===required.width&&v.height===required.height))reasons.push(`missing viewport ${required.width}x${required.height}`);
  for(const output of gate.required_outputs)if(receipt.required_outputs?.[output]!==true)reasons.push('missing output: '+output);if(gate.saved_json_and_standalone_html_parity_required&&receipt.saved_json_and_standalone_html_parity!==true)reasons.push('saved JSON/HTML parity failed');
  return {passed:reasons.length===0,reasons,receipt_sha256:digest(receipt),tested_at:receipt.tested_at||null};
}

function emptyCounts(){return {errors:0,assessable:0,unreviewable:0,reviewed:0,rate:null};}
function addRow(target,metric,row){const spec=METRICS[metric],out=target[metric]||(target[metric]=emptyCounts());out.reviewed++;if(row.verdict==='unreviewable')out.unreviewable++;else{out.assessable++;if(row.verdict===spec.error)out.errors++;}}
function finalize(group){for(const metric of Object.keys(METRICS)){const out=group[metric]||emptyCounts();out.rate=out.assessable?out.errors/out.assessable:null;group[metric]=out;}return group;}
function rowBreakdown(days,field){const groups={};for(const day of days)for(const [metric,spec] of Object.entries(METRICS))for(const row of day[spec.field]){const key=field==='day_id'?day.day_id:row[field];if(!groups[key])groups[key]={};addRow(groups[key],metric,row);}return Object.fromEntries(Object.entries(groups).sort(([a],[b])=>a.localeCompare(b)).map(([key,value])=>[key,finalize(value)]));}
function maximumBodyShare(days,reviewField){const counts=new Map();let total=0;for(const day of days)for(const row of day[reviewField])if(row.verdict!=='unreviewable'){counts.set(row.body,(counts.get(row.body)||0)+1);total++;}return {share:total?Math.max(...counts.values())/total:null,assessable:total,by_body:Object.fromEntries([...counts].sort(([a],[b])=>a.localeCompare(b)))};}

function evaluate(reviewInput,lockInput,registrationInput,browserReceiptInput){
  const lock=validateLock(structuredClone(lockInput)),registration=validateRegistration(registrationInput,lock),review=validateReview(reviewInput,lock,registration);
  const totals={};for(const day of review.days)for(const metric of Object.keys(METRICS))for(const row of day[METRICS[metric].field])addRow(totals,metric,row);finalize(totals);
  const meetings=review.days.flatMap(day=>day.meetings),bodies=new Set(meetings.map(m=>m.body)),meetingTypes=new Set(meetings.map(m=>m.meeting_type)),required=lock.minimum_coverage[review.split==='test'?'untouched_test':'development'];
  const observed={days:review.days.length,un_bodies:bodies.size,meeting_types:meetingTypes.size,meetings:new Set(meetings.map(m=>m.id)).size};for(const [metric,spec] of Object.entries(METRICS))observed[spec.coverage]=totals[metric].assessable;
  const claims=maximumBodyShare(review.days,'claim_reviews'),topics=maximumBodyShare(review.days,'topic_reviews'),countCoverage=Object.keys(observed).every(key=>observed[key]>=required[key]);
  const multiBody=!required.multi_body_day_required||review.days.some(d=>d.bodies.length>1),multiType=!required.multi_meeting_type_day_required||review.days.some(d=>d.meeting_types.length>1),concentration=required.maximum_single_body_share===undefined||((claims.share??1)<=required.maximum_single_body_share&&(topics.share??1)<=required.maximum_single_body_share);
  const coverage={...observed,bodies:[...bodies].sort(),meeting_type_labels:[...meetingTypes].sort(),body_concentration:{assessable_claims:claims,owner_topics:topics,maximum_allowed:required.maximum_single_body_share??null},meets_thresholds:countCoverage&&multiBody&&multiType&&concentration};
  const gates={};for(const metric of Object.keys(METRICS)){const maximum=lock.metrics[metric].maximum,observedRate=totals[metric].rate;gates[metric]={maximum,observed:observedRate,passed:observedRate!==null&&observedRate<=maximum};}
  const criticalErrors=review.days.reduce((n,d)=>n+(d.critical_errors?.length||0),0);gates.critical_errors={maximum:lock.critical_error_maximum,observed:criticalErrors,passed:criticalErrors<=lock.critical_error_maximum};gates.coverage={required,observed,body_concentration:coverage.body_concentration,passed:coverage.meets_thresholds};gates.one_action_browser=validateBrowserReceipt(browserReceiptInput,review,lock,registration);
  const passed=Object.values(gates).every(g=>g.passed);
  return {schema:RESULT_SCHEMA,status:passed?'accepted_on_owner_reviewed_sample':'thresholds_not_met',sample_id:review.sample_id,split:review.split,owner_review_status:'owner-confirmed single-reviewer operational sample; not independent gold or inter-rater agreement',acceptance_lock_sha256:lock.canonical_sha256,registration_sha256:registration.canonical_sha256,review_sha256:digest(review),coverage,metrics:totals,breakdowns:{by_day:rowBreakdown(review.days,'day_id'),by_body:rowBreakdown(review.days,'body'),by_meeting_type:rowBreakdown(review.days,'meeting_type')},gates,passed,limitations:['Rates describe only the owner-reviewed sample and its explicit assessable decisions.','Unreviewable decisions are reported and excluded from metric and minimum-coverage denominators.','Body and meeting-type breakdowns use each decision row’s registered meeting binding.','No transcript text is opened or reclassified by this evaluator.']};
}

function main(){const [lockPath,registrationPath,reviewPath,browserPath,outputPath]=process.argv.slice(2);if(!lockPath||!registrationPath||!reviewPath||!browserPath||!outputPath||fs.existsSync(outputPath))throw Error('Usage: node evaluate.cjs LOCK.json REGISTRATION.json OWNER_REVIEW.json BROWSER_RECEIPT.json NEW_RESULT.json\n   or: node evaluate.cjs LOCK.json REGISTRATION.json --readiness - NEW_RESULT.json');const lock=JSON.parse(fs.readFileSync(lockPath,'utf8')),registration=JSON.parse(fs.readFileSync(registrationPath,'utf8'));const result=reviewPath==='--readiness'?readiness(lock,registration):evaluate(JSON.parse(fs.readFileSync(reviewPath,'utf8')),lock,registration,JSON.parse(fs.readFileSync(browserPath,'utf8')));fs.writeFileSync(outputPath,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:result.status,sample_id:result.sample_id,passed:result.passed}));}
const api={REVIEW_SCHEMA,LOCK_SCHEMA,REGISTRATION_SCHEMA,BROWSER_SCHEMA,RESULT_SCHEMA,METRICS,canonical,digest,lockDigest,registrationDigest,validateLock,validateRegistration,validateReview,validateBrowserReceipt,readiness,evaluate};
if(require.main===module){try{main();}catch(error){console.error(error.message);process.exitCode=1;}}else module.exports=api;
