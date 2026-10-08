'use strict';
/*
 * Validate the strictly additive P4 recovery of official original-PV MEETING
 * dates from three 2016/17/23 index omissions.
 *
 * This does not authenticate a speaker, reconstruct a Harvard speech, or
 * authorize any W1 fitting. It requires an original, immutable 792-row P3
 * inventory and rejects any non-date mutation in the derived candidate.
 *
 * The underlying original PV PDFs were separately byte-hashed and their
 * first-page date/weekday/source symbol verified in the private Python replay;
 * this JS validator only confirms the typed derivation and W1 grouping.
 */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const W1=require('../validation_framework/frame.cjs');
const {auditPrivateP3}=require('./p4_historical_w1_preflight.cjs');
const ORIGINAL='source_corroborated_date_unverified';
const DATED='source_corroborated_PV_meeting_date_not_index';
const DATE_PROVENANCE='original_PV_frontpage_header_SHA256_verified';
function demand(flag,reason){if(!flag)throw Error(reason);}
function copy(o){return structuredClone(o);}
function same(a,b){try{assert.deepStrictEqual(a,b);return true}catch{return false}}
function readDate(dateStr,year){
  if(!/^\d{4}-\d{2}-\d{2}$/.test(dateStr)||!dateStr.startsWith(String(year)+'-'))
    return false;
  const parsed=new Date(dateStr+'T00:00:00Z');
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0,10)===dateStr;
}
function reviewOriginalMeetingDateSupplement(original,derived){
  // Enforce original source metadata and frozen research gates first.
  const origAudit=auditPrivateP3(original,{resamples:5,seed:31415});
  demand(derived&&derived.schema===original.schema&&
    derived.split===original.split,'Derived historical source type changed');
  demand(same(derived.upstream,original.upstream)&&
    same(derived.release_gates,original.release_gates)&&
    same(derived.population,original.population),'Original upstream source/selection/frozen metadata changed');
  demand(Array.isArray(derived.observations)&&derived.observations.length===792,
    'Derived 792-cell source-year ledger is incomplete');
  const prior=new Map(original.observations.map(r=>[r.id,r]));
  const ids=new Set();
  const gained=[],dated=[];
  for(const candidate of derived.observations){
    demand(candidate&&typeof candidate.id==='string'&&!ids.has(candidate.id),
      'Duplicate or invalid derived historical source identity');
    ids.add(candidate.id);
    const before=prior.get(candidate.id);
    demand(before,'New source row was fabricated');
    if(before.source_status===ORIGINAL){
      const change=copy(before);
      demand(before.date===null&&candidate.source_status===DATED,
        'Date recovery must start from an explicitly date-unverified original PV source');
      demand(readDate(candidate.date,before.year),
        'Recovered official-PV meeting date invalid or outside actual historical year');
      demand(candidate.PV_meeting_date_source===DATE_PROVENANCE &&
        candidate.date_speaker_person_authentication===false,
        'Official-PV frontpage source/identity caveat missing');
      change.date=candidate.date;
      change.source_status=DATED;
      change.PV_meeting_date_source=DATE_PROVENANCE;
      change.date_speaker_person_authentication=false;
      demand(same(change,candidate),
        'Official original-PV date supplement altered source, text, person or fit identity');
      gained.push(candidate);
    }else{
      demand(same(before,candidate),
        'Non-target historical original-source row mutated in date supplement');
    }
    if(candidate.date!==null)dated.push(candidate);
    demand(candidate.harvard_original_raw_text_rechecked_now===false &&
      candidate.W1_model_fit_eligible===false&&candidate.W4_model_fit_eligible===false,
      'Date supplement cannot promote archived Harvard text to a fitted W1 model');
  }
  demand(gained.length===3&&ids.size===792&&dated.length===523,
    'The three recovered source-PV meeting dates have incorrect denominators');
  demand([2016,2017,2023].every(y=>gained.filter(x=>x.year===y).length===1),
    'Official original-PV date supplement must cover the three recorded missing-year instances');
  demand(derived.observations.filter(x=>x.source_status===
      'original_PV_not_verified_not_speech_absence').length===269,
    'Unverified original country-year cells cannot be recoded or lost');
  const rows=dated.map(r=>({id:r.id,meeting_id:r.meeting_id,
    source_family_id:r.source_family_id,country:r.country,affiliation:r.country,
    text_sha256:r.speech_text_sha256,genre:r.genre,role:'source_only_meeting_date'}));
  const groupedPV=W1.unionGroups(rows,'meeting');
  const groupedAffiliation=W1.unionGroups(rows,'affiliation');
  const nativePV=W1.auditSources(rows);
  const meetingPlan=W1.schedule(rows,'meeting',5,0.8,31415);
  const affiliationPlan=W1.schedule(rows,'affiliation',5,0.8,31415);
  demand(groupedPV.groups.length===55&&groupedAffiliation.groups.length===1,
    'Official-PV-derived source-family structure changed after date supplement');
  demand(nativePV.meetings===55&&nativePV.observations===523,
    'Native W1 audited count does not match date-supplemented source inventory');
  demand(meetingPlan.status==='scheduled'&&
    affiliationPlan.status==='skipped'&&affiliationPlan.attempted===0,
    'Cannot treat transitive source-linked affiliations as independent bootstrap groups');
  return {
    schema:'un.w1.p4.official-PV-meeting-date-supplement.check.v1',
    original_inventory_slots:792,
    prior_index_dated:origAudit.source_date_verified,
    newly_original_PV_meeting_dated:gained.length,
    official_PV_meeting_dated_cells:dated.length,
    original_source_unverified:269,source_meeting_groups:55,
    native_W1_meeting_grouping:'SOURCE_DESIGN_ONLY',
    native_W1_affiliation_grouping:affiliationPlan.status,
    native_W1_affiliation_group_count:groupedAffiliation.groups.length,
    native_W1_model_validation_on_original_Harvard_text:'NOT_RUN',
    event_date_is_original_meeting_date_not_person_authentication:true,
    fitted_W1_models:0,fitted_W4_models:0,
    publication_eligible:false,reserved_37_meetings_opened:0
  };
}
if(require.main===module){
  const a=process.argv.slice(2);
  const val=x=>{const j=a.indexOf(x);return j>=0?a[j+1]:null};
  const original=val('--original-private'),derived=val('--derived-private'),output=val('--private-output');
  if(!original||!derived||!output)throw Error('Require --original-private, --derived-private and --private-output');
  const repo=path.resolve(__dirname,'../..')+path.sep;
  for(const x of [original,derived,output])demand(!path.resolve(x).startsWith(repo),
    'Historical original inputs and derived validation output must remain out of the public checkout');
  const result=reviewOriginalMeetingDateSupplement(
    JSON.parse(fs.readFileSync(original,'utf8')),
    JSON.parse(fs.readFileSync(derived,'utf8')));
  fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n',{mode:0o600,flag:'wx'});
  console.log(JSON.stringify({status:'PASS_MEETING_DATE_SOURCE_DESIGN_ONLY',
    cells:result.official_PV_meeting_dated_cells,source_meetings:55,
    affiliation_grouping:result.native_W1_affiliation_grouping,
    model_fits:0,private_rows_published:false}));
}
module.exports={reviewOriginalMeetingDateSupplement};
