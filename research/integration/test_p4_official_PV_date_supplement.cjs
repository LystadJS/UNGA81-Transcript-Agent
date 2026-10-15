'use strict';
const assert=require('node:assert/strict');
const {fixture}=require('./test_p4_historical_w1_preflight.cjs');
const {reviewOriginalMeetingDateSupplement}=require('./p4_official_PV_date_supplement.cjs');

function derivedFrom(original){
 const d=structuredClone(original);
 let changed=0;
 for(const item of d.observations){
   if(item.source_status!=='source_corroborated_date_unverified')continue;
   changed++;
   item.date=item.year+'-09-24';
   item.source_status='source_corroborated_PV_meeting_date_not_index';
   item.PV_meeting_date_source='original_PV_frontpage_header_SHA256_verified';
   item.date_speaker_person_authentication=false;
 }
 assert.equal(changed,3);
 return d;
}
function tests(){
 let count=0;
 function caseRun(label,fn){fn();count++;process.stdout.write('PASS '+label+'\n')}
 function refuse(fn,match){
   const original=fixture(),updated=derivedFrom(original);
   fn(original,updated);
   assert.throws(()=>reviewOriginalMeetingDateSupplement(original,updated),match);
 }
 caseRun('exactly three official source-meeting date additions retain every row',()=>{
   const old=fixture(),updated=derivedFrom(old);
   const data=reviewOriginalMeetingDateSupplement(old,updated);
   assert.equal(data.original_inventory_slots,792);
   assert.equal(data.prior_index_dated,520);
   assert.equal(data.newly_original_PV_meeting_dated,3);
   assert.equal(data.official_PV_meeting_dated_cells,523);
   assert.equal(data.original_source_unverified,269);
   assert.equal(data.native_W1_affiliation_grouping,'skipped');
   assert.equal(data.native_W1_affiliation_group_count,1);
   assert.equal(data.source_meeting_groups,55);
   assert.equal(data.fitted_W1_models,0);
   assert.equal(data.publication_eligible,false);
 });
 caseRun('date preflight deterministic with original P3 inventory unmodified',()=>{
   const input=fixture();
   const raw=JSON.stringify(input);
   assert.deepEqual(reviewOriginalMeetingDateSupplement(input,derivedFrom(input)),
     reviewOriginalMeetingDateSupplement(input,derivedFrom(input)));
   assert.equal(JSON.stringify(input),raw);
 });
 caseRun('reject invented meeting date on a genuinely missing original PV',()=>{
   refuse((a,d)=>{const x=d.observations.find(z=>z.source_status==='original_PV_not_verified_not_speech_absence');x.date=x.year+'-09-24'},
     /Non-target historical original-source row mutated/);
 });
 caseRun('refuse changed source or speech text SHA under recovered PV date',()=>{
   refuse((a,d)=>{const x=d.observations.find(z=>z.PV_meeting_date_source);x.speech_text_sha256='0'.repeat(64)},
     /altered source/);
 });
 caseRun('refuse fabricated person or W1 model-ready status',()=>{
   refuse((a,d)=>{const x=d.observations.find(z=>z.PV_meeting_date_source);x.date_speaker_person_authentication=true},
     /caveat missing/);
   refuse((a,d)=>{const x=d.observations.find(z=>z.PV_meeting_date_source);x.W1_model_fit_eligible=true},
     /altered source/);
 });
 caseRun('refuse date recovery outside year and duplicate records',()=>{
   refuse((a,d)=>{const x=d.observations.find(z=>z.PV_meeting_date_source);x.date='2026-10-05'},
     /date invalid/);
   refuse((a,d)=>{d.observations[0]=structuredClone(d.observations[1])},
     /Duplicate or invalid/);
 });
 caseRun('refuse any removal of all 269 source-unverified cells',()=>{
   refuse((a,d)=>{d.observations=d.observations.filter(x=>x.source_status!=='original_PV_not_verified_not_speech_absence')},
     /792-cell/);
 });
 caseRun('refuse false original PV date provenance',()=>{
   refuse((a,d)=>{const x=d.observations.find(z=>z.PV_meeting_date_source);x.PV_meeting_date_source='UN_index_verified'},
     /source\/identity caveat missing/);
 });
 process.stdout.write(JSON.stringify({suite:'p4-official-PV-meeting-date-supplement-synthetic',
    tests:count,failed:0,prior_source_date_verified:520,
    recovered_original_PV_dates:3,source_group_meetings:55,
    raw_harvard_speeches_verified:0,model_fits:0,reserved_37_meetings_opened:0})+'\n');
}
try{tests()}catch(error){process.stderr.write(error.stack+'\n');process.exitCode=1;}
