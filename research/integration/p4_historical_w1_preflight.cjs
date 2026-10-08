'use strict';
// Private-source lineage and grouped-dependence preflight for P3 historical
// General Debate. Do not coerce this dataset into a native W1 fit schema.
// Import existing W1 grouping/audit functions unchanged.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const W1=require('../validation_framework/frame.cjs');

const HASH=/^[a-f0-9]{64}$/;
const COUNTRY=/^[A-Z]{3}$/;
const SOURCES={
  dated:'source_and_index_date_corroborated_hash_only',
  undated:'source_corroborated_date_unverified',
  unverified:'original_PV_not_verified_not_speech_absence'
};
const SELECTION='3ebec834635e4d493e8035aeede3321efb951aa22f2f61d81f6ac7a0f65a4c89';
const TAR_SHA='55077dccf7242cdf544aa95c4797c68e443b0c37344c9c112a2e2392ddfcf8e5';
const RESERVED=new Set(['2026-10-05','2026-10-06']);
function check(condition, reason){if(!condition)throw Error(reason);}
function hash(x){return crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');}
function hashOK(s){return typeof s==='string'&&HASH.test(s);}
function sourceRow(r){
  return {id:r.id,meeting_id:r.meeting_id,source_family_id:r.source_family_id,
    country:r.country,affiliation:r.country,
    text_sha256:r.speech_text_sha256,
    genre:r.genre,role:'original_PV_recorded_affiliation_only',
    parent_id:r.parent_id??null};
}
function auditPrivateP3(inventory,{resamples=20,seed=31415}={}){
  check(inventory&&inventory.schema==='un.w1.p3.longitudinal-source-inventory.v1',
    'Unrecognized private P3 historical inventory');
  check(inventory.split==='private_development_inventory',
    'Must be original private-development inventory');
  check(inventory.upstream?.P2_source_selection_sha256===SELECTION &&
    inventory.upstream?.harvard_v14_original_tar_expected_sha256===TAR_SHA &&
    inventory.upstream?.harvard_v14_raw_text_file_bytes_accessible_now===false,
    'Original P2 selection / Harvard-unverified upstream gate changed');
  check(inventory.release_gates?.reserved_37_meetings_opened===0 &&
    inventory.release_gates?.publication_eligible===false &&
    inventory.release_gates?.W1_real_model_fit==='NOT_RUN' &&
    inventory.release_gates?.W4_descriptive_fit==='WITHHELD',
    'Frozen scientific or heldout source release gate was weakened');
  const rows=inventory.observations;
  check(Array.isArray(rows)&&rows.length===792,'Exact full 792-cell frame required');
  check(Number.isSafeInteger(resamples)&&resamples>=0&&resamples<=100,
    'Resampling request exceeds metadata-only design cap');
  const seen=new Set(),countryYears=new Map(),meetingSHA=new Map(),yearCounts=new Map();
  const groups={dated:[],undated:[],unverified:[]};
  for(const r of rows){
    check(r&&typeof r==='object'&&COUNTRY.test(r.country)&&Number.isInteger(r.year) &&
      r.year>=2016&&r.year<=2023,'Invalid country-year frame key');
    const key=r.country+'|'+r.year;
    check(!seen.has(key),'Duplicate country-year inventory slot');
    seen.add(key);
    check(r.id===r.country+'_'+r.year,'Unexpected P3 original observation identity');
    check(r.genre==='general_debate'&&r.actor_kind==='recorded_affiliation'&&
      r.review_status.startsWith('source_'),'Original speaker role and genre not retained');
    check(!r.W1_model_fit_eligible&&!r.W4_model_fit_eligible&&
      r.harvard_original_raw_text_rechecked_now===false &&
      r.training_representation_frozen===false&&!r.speech_source_role_authenticated,
      'Historical archived source status was prematurely promoted');
    check(r.independently_authenticated_person_id===null&&r.verified_speech_id===null,
      'Unverified recorded affiliation promoted to human gold speech identity');
    check(r.date===null||!RESERVED.has(r.date),'Reserved 2026 evaluation date');
    if(!countryYears.has(r.country))countryYears.set(r.country,[]);
    countryYears.get(r.country).push(r.year);
    if(!yearCounts.has(r.year))yearCounts.set(r.year,{dated:0,undated:0,unverified:0});
    let state;
    if(r.source_status===SOURCES.dated)state='dated';
    else if(r.source_status===SOURCES.undated)state='undated';
    else if(r.source_status===SOURCES.unverified)state='unverified';
    else throw Error('Unrecognized source status; never translate missing to absent');
    groups[state].push(r);
    yearCounts.get(r.year)[state]++;
    if(state==='dated'||state==='undated'){
      check(/^A\/[0-9]{2}\/PV\.[0-9]+$/.test(r.meeting_id||'') &&
        Number(r.meeting_id.split('/')[1])===r.year-1945,
        'Meeting original A/session/PV symbol inconsistent with speech year');
      check(typeof r.source_family_id==='string'&&r.source_family_id.length>0 &&
        hashOK(r.original_source_pdf_sha256)&&hashOK(r.original_source_full_text_sha256) &&
        hashOK(r.speech_text_sha256)&&r.speech_hash_basis==='harvard_v14_utf8_original_txt_file_bytes'&&
        typeof r.source_url==='string'&&
        /^https:\/\/documents\.un\.org\//.test(r.source_url),
        'Original PV source identity missing or Harvard hash basis falsified');
      const item=[r.original_source_pdf_sha256,r.original_source_full_text_sha256,r.source_family_id,r.source_url];
      if(meetingSHA.has(r.meeting_id))check(JSON.stringify(meetingSHA.get(r.meeting_id))===JSON.stringify(item),
        'Same original PV source appears with conflicting original PDF/text SHA or family');
      else meetingSHA.set(r.meeting_id,item);
      check(r.parent_id===null&&r.parent_start===null&&r.parent_end===null,
        'Unverified speech boundary must not be invented from PV or Harvard hash');
      if(state==='dated'){
        check(/^\d{4}-\d{2}-\d{2}$/.test(r.date)&&r.date.startsWith(String(r.year)+'-'),
          'Date-verified source cell has no verified date');
        check(r.W1_source_provenance_preflight===true,'Dated source preflight flag inconsistent');
      } else {
        check(r.date===null,'Date-unverified source cell must not get an invented date');
      }
    }else{
      check(r.date===null&&r.meeting_id===null&&r.source_family_id===null&&
        r.original_source_pdf_sha256===null&&r.original_source_full_text_sha256===null&&
        r.speech_text_sha256===null&&r.source_url===null&&
        !r.W1_source_provenance_preflight,
        'Unverified original-PV inventory cell is not an observed speech or a zero');
    }
  }
  check(countryYears.size===99&&seen.size===792,'Unrecognized recorded-affiliation inventory');
  for(const years of countryYears.values()){
    check(years.length===8&&new Set(years).size===8 &&
      years.every(y=>y>=2016&&y<=2023),'Country yearly opportunities not exhaustive');
  }
  check(groups.dated.length===520&&groups.undated.length===3&&
    groups.unverified.length===269&&meetingSHA.size===55,
    'Selected original PV/Harvard hash statuses or meeting groups changed');
  check(groups.dated.length+groups.undated.length+groups.unverified.length===792,
    'Historic missingness ledger does not reconcile');
  const byYear=[];
  for(let y=2016;y<=2023;y++){
    let x=yearCounts.get(y);
    check(x&&x.dated+x.undated+x.unverified===99,'Year-level expected actor slots not complete');
    byYear.push({year:y,expected:99,source_corroborated:x.dated+x.undated,
      date_verified:x.dated,date_missing:x.undated,
      original_source_unverified:x.unverified});
  }
  const sourceBound=groups.dated.map(sourceRow);
  const meetingGroups=W1.unionGroups(sourceBound,'meeting');
  const affiliationGroups=W1.unionGroups(sourceBound,'affiliation');
  const meetingPlan=W1.schedule(sourceBound,'meeting',resamples,0.8,seed);
  const affiliationPlan=W1.schedule(sourceBound,'affiliation',resamples,0.8,seed);
  const sourceAudit=W1.auditSources(sourceBound,null);
  check(meetingGroups.groups.length===55&&meetingPlan.groups===55&&
    meetingPlan.status==='scheduled','Verified original-PV source grouping changed');
  check(affiliationGroups.groups.length===1&&affiliationPlan.status==='skipped' &&
    affiliationPlan.attempted===0,
    'Country×source-family transitive dependence no longer rejects resampling');
  check(sourceAudit.observations===520&&sourceAudit.meetings===55,
    'Native W1 source audit contradicts private original-PV inventory');
  const yearsLeftOut=byYear.map(y=>({
    year:y.year,original_source_cells_removed:y.source_corroborated,
    date_verified_rows_removed:y.date_verified,
    date_verified_rows_retained:520-y.date_verified,
    inferential_interval:false
  }));
  return {
    schema:'un.w1.p4.historical-dependence-preflight.aggregate.v1',
    input:'private P3, original UN-PV source identities with saved Harvard hashes',
    original_harvard_speech_text_bytes_reverified:false,
    native_W1_aggregate_audit_and_group_schedules_executed:true,
    native_W1_validateFrame_with_empirical_text_executed:false,
    W1_real_model_fit_eligible:false,W1_model_fits:0,W4_model_fits:0,
    publication_eligible:false,heldout_37_reserved_meetings_opened:0,
    inventory_cells:792,recorded_affiliations:99,original_PV_source_corroborated:523,
    source_date_verified:520,source_date_unresolved:3,original_source_unverified:269,
    original_PV_meeting_groups:55,
    by_year:byYear,
    meeting_grouping:{groups:meetingGroups.groups.length,
      planned_resamples:resamples,attempted:meetingPlan.attempted,
      design_sample_sha256:meetingPlan.schedule_sha256,unit:'whole_original_PV',
      status:meetingPlan.status,source_pair_share:sourceAudit.within_meeting_pair_share??null,
      max_group_count:sourceAudit.largest_meeting_count??null,
      actual_statistical_model_refits:0},
    affiliation_grouping:{groups:affiliationGroups.groups.length,
      attempted:affiliationPlan.attempted,status:affiliationPlan.status,
      reason:affiliationPlan.reason,
      source_family_transitive_closure_is_single_group:true},
    source_concentration:{meeting_groups:sourceAudit.meetings,
      largest_meeting_observation_count:sourceAudit.largest_meeting_count,
      largest_meeting_observation_share:sourceAudit.largest_meeting_share,
      within_meeting_pair_fraction:sourceAudit.within_meeting_pair_share,
      duplicate_text_hash_groups:sourceAudit.duplicate_text_groups,
      missing_affiliation_observations:sourceAudit.missing_affiliation_count},
    year_leave_one_out:yearsLeftOut,
    deterministic_aggregate_sha256:hash([byYear,meetingPlan.schedule_sha256,
      sourceAudit.observations,affiliationGroups.groups.length]),
    limitations:['This is actual W1 grouping/audit code on saved source identities, not W1 validated raw speech data.',
      'No independent original Harvard v14 raw text bytes, fitted representation, source-level inferential null or model fit.',
      'The single affiliation/source-family transitive group prohibits an affiliation-group bootstrap.',
      'Year and original-PV meeting may not be independent across groups.']
  };
}

if(require.main===module){
  const args=process.argv.slice(2);
  const index=args.indexOf('--private-input');
  const file=index>=0?args[index+1]:null;
  const outFlag=args.indexOf('--private-output');
  const target=outFlag>=0?args[outFlag+1]:null;
  if(!file||!target)throw Error('Require --private-input and --private-output (not public checkout)');
  const repo=path.resolve(__dirname,'../..');
  const absolute=path.resolve(file),output=path.resolve(target);
  if(absolute===repo||absolute.startsWith(repo+path.sep)||
     output===repo||output.startsWith(repo+path.sep))
    throw Error('Private input and receipt must remain outside public Git repository');
  const result=auditPrivateP3(JSON.parse(fs.readFileSync(absolute,'utf8')));
  fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n',{flag:'wx',mode:0o600});
  console.log(JSON.stringify({status:'PASS_SOURCE_DEPENDENCE_ONLY',
    inventory_cells:result.inventory_cells,dated:result.source_date_verified,
    source_meetings:result.original_PV_meeting_groups,
    grouped_meeting_schedule:result.meeting_grouping.status,
    grouped_affiliation_schedule:result.affiliation_grouping.status,
    empirical_fit:'WITHHELD',public_source_rows:false}));
}
module.exports={auditPrivateP3};
