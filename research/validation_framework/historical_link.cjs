'use strict';

/*
 * Candidate W1 ⇄ source-inventory linkage for coordinator review.
 * Does not alter un.parallel-analysis.v1 or fabricate a historical v2 release.
 * Private observations stay in the source runtime; returned JSON is aggregate-only.
 */
const F=require('./frame.cjs');
const Inventory=require('../../docs/parallel-work/source-inventory-v1.cjs');

const P2='un.p2.original-pv-reconciled.v1';
const SYNTHETIC='un.source-validation.synthetic.v1';
const HEX=/^[a-f0-9]{64}$/;
function ensure(ok,why){if(!ok)throw Error('Historical W1 linkage withheld: '+why);}
function isHash(x){return typeof x==='string'&&HEX.test(x);}
function compatibleSource(run,inventory){
  const f=run.frame,u=inventory.upstream;
  ensure(f.split===inventory.population.split,'source split mismatch');
  ensure(u.source_schema===f.source_schema,'original upstream source schema mismatch; no relabeling');
  ensure(u.source_engine===f.source_engine,'original upstream source engine mismatch');
  ensure(u.source_hash_basis===f.source_hash_basis,'original bytes/text hash basis mismatch');
  ensure(u.source_sha256===f.source_sha256,'original source SHA-256 mismatch');
  ensure(f.source_schema===P2||f.source_schema===SYNTHETIC,'unsupported upstream source adapter');
  ensure(f.source_schema!==SYNTHETIC || f.split==='synthetic','invented fixtures cannot masquerade as development');
  ensure(f.source_schema!==P2 || f.split==='development','P2 requires historical development lineage');
  ensure(f.source_schema!==P2 || inventory.population.frame_unit==='country_year',
    'P2 inventory must retain country-year observation unit');
  ensure(f.source_schema!==P2 || inventory.producer.fixture_kind==='private_development',
    'P2 requires privately verified original-source inventory');
}
function matchRow(observed,entry,split){
  ensure(entry&&entry.id===observed.id,'source ID absent from independently inventoried source states');
  ensure(entry.source_status===observed.source_status,'availability changed after source authentication');
  ensure(entry.text_sha256===observed.text_sha256,'original observed-text digest mismatch');
  ensure(entry.meeting_id===(observed.meeting_id??null),'verified meeting/source group mismatch');
  ensure(entry.source_family_id===(observed.source_family_id??null),'source-family identity mismatch');
  ensure(entry.event_date===(observed.date??null),'original event date mismatch');
  ensure(entry.review_status===(observed.review_status??'not_applicable'),
    'source verification/review status mismatch');
  if(entry.source_status==='available'){
    if(split==='development'){
      ensure(entry.actor_kind==='recorded_affiliation' &&
        entry.actor_id===observed.country &&
        observed.affiliation===observed.country &&
        observed.speech_id==null,'recorded affiliation was promoted to a verified speaker');
      ensure(entry.source_verification==='full_original_verified',
        'independently original-source-verified inventory required');
      ensure(isHash(observed.p2_original_pdf_sha256) &&
        entry.source_sha256===observed.p2_original_pdf_sha256,
        'original PV PDF byte hash mismatch');
      ensure(observed.p2_full_speech_verified===true,
        'full-original-PV speech corroboration missing');
    }else{
      ensure(entry.actor_kind==='synthetic' && entry.source_verification==='synthetic',
        'invented fixture cannot claim original source authentication');
      ensure(isHash(observed.original_source_sha256)&&
        entry.source_sha256===observed.original_source_sha256,
        'synthetic original-source identifier mismatch');
    }
  }else{
    ensure(entry.missing_reason===observed.missing_reason,
      'unavailable observed record reason mismatch');
    ensure(entry.source_verification!=='full_original_verified',
      'missing observation was promoted to observed source');
  }
}
function checkFit(f,run,eligible,modelIds){
  ensure(!modelIds.has(f.model_id),'duplicate model identity');
  modelIds.add(f.model_id);
  ensure(f.population_hash===run.frame.population_hash &&
    f.selection_sha256===run.frame.selection_sha256 &&
    f.source_sha256===run.frame.source_sha256,
    'model source/selection fingerprint mismatch');
  ensure(f.observation_ids?.length===eligible.length &&
    f.observation_hashes?.length===eligible.length,'model changed retained population');
  for(let i=0;i<eligible.length;i++)ensure(
    f.observation_ids[i]===eligible[i].id &&
    f.observation_hashes[i]===eligible[i].text_sha256,
    'model population/order changed');
  ensure(['fitted','skipped','failed'].includes(f.status),'unrecognized numerical fit status');
  ensure(Number.isSafeInteger(f.attempted_fit) && Number.isSafeInteger(f.successful_fit) &&
    Number.isSafeInteger(f.failed_fit) && f.attempted_fit===f.successful_fit+f.failed_fit,
    'full-fit attempts not completely accounted for');
  if(f.status==='fitted'){
    ensure(f.attempted_fit===1&&f.successful_fit===1&&
      f.assignments?.length===eligible.length&&
      f.assignments.every(v=>Number.isSafeInteger(v)&&v>=0),
      'successful fit has incomplete or invalid hard assignment');
  }else ensure(f.assignments===null&&typeof f.reason==='string'&&f.reason,
    'skipped/failed fit must retain reason and cannot return hard assignments');
  return {
    model_id:f.model_id,method:f.method,
    representation_id:f.representation_id,representation_version:f.representation_version,
    status:f.status,full_attempted:f.attempted_fit,full_successful:f.successful_fit,
    full_failed:f.failed_fit,
    assigned:f.assignments?.filter(x=>x>0).length??0,
    unassigned_noise:f.assignments?.filter(x=>x===0).length??0,
    selected_but_not_fitted:f.status==='fitted'?0:eligible.length
  };
}
function linkW1Inventory(run,inventory){
  ensure(run?.schema==='un.source-aware-validation.v1'&&
    run?.publication_eligible===false&&run.evaluation_role==='engineering_only',
    'source-bound, engineering-only W1 numerical result required');
  ensure(Array.isArray(run._internal_frame),'private original frame lineage is absent');
  // Delegate schema shape, inventory hash, country-year uniqueness, periods,
  // source-state completeness and legacy refusal to the coordinator's validator.
  const check=Inventory.validateInventory(inventory);
  ensure(check.legacy_binding==='withheld','legacy v1 analytical export was improperly authorized');
  compatibleSource(run,inventory);
  const original=run._internal_frame;
  ensure(run.frame.observations_total===original.length &&
    run.frame.eligible+run.frame.excluded===original.length,'W1 source denominator mismatch');
  const eligible=original.filter(r=>r.source_status==='available'&&!(r.exclusion_reasons||[]).length);
  ensure(eligible.length===run.frame.eligible&&eligible.length<=600&&eligible.length>0,
    'unsupported W1 retained population');
  const expectedSelection=F.digest(eligible.map(x=>[x.id,x.text_sha256]));
  const expectedPopulation=F.digest([
    run.frame.source_schema,run.frame.source_hash_basis,run.frame.source_sha256,expectedSelection]);
  ensure(expectedSelection===run.frame.selection_sha256 &&
    expectedPopulation===run.frame.population_hash,'model population SHA-256 cannot be reproduced');
  const entries=new Map(inventory.observations.map(o=>[o.id,o]));
  const checked=new Set();
  for(const observed of original){
    ensure(!checked.has(observed.id),'duplicate W1 source ID');
    checked.add(observed.id);
    matchRow(observed,entries.get(observed.id),run.frame.split);
  }
  const available=inventory.observations.filter(o=>o.source_status==='available');
  const selected=new Set(eligible.map(o=>o.id));
  ensure(available.length>=eligible.length,'more fitted observations than original available sources');
  // All model records must use the exact same observation ordering, text hashes,
  // fitted geometry lineage and original archive identity.
  ensure(Array.isArray(run.fit_records)&&run.fit_records.length>0 &&
    Array.isArray(run.model_reports),'missing complete W1 model inventory');
  const modelIds=new Set();
  const models=run.fit_records.map(f=>checkFit(f,run,eligible,modelIds));
  ensure(run.model_reports.length===models.length,'model stability ledger incomplete');
  const grouping=[];
  for(const row of run.model_reports){
    ensure(modelIds.has(row.model_id),'unknown model in grouped-refit ledger');
    const records=run.fit_records.find(f=>f.model_id===row.model_id);
    for(const [unit,s] of Object.entries(row.group_stability||{})){
      ensure(['meeting','affiliation'].includes(unit)&&Array.isArray(s.runs),
        'unknown group-dependence unit or refit ledger');
      const attempted=s.runs.filter(x=>x.attempted_fit===1).length;
      const successful=s.runs.filter(x=>x.status==='fitted').length;
      const failed=s.runs.filter(x=>x.status==='failed').length;
      ensure(s.attempted===s.runs.length&&s.successful===successful&&s.failed===failed &&
        s.attempted<=s.planned && successful<=attempted,
        'refit attempt/success/failed denominators inconsistent');
      ensure(s.runs.every(x=>x.selected+x.out_of_sample===eligible.length),
        'source-group refit changed denominator');
      ensure(!s.runs.some(x=>x.status==='fitted' && x.comparison==null),
        'unreported comparison on successful group refit');
      grouping.push({model_id:row.model_id,unit,planned:s.planned,executed:s.attempted,
        successful:s.successful,failed:s.failed,
        skipped:s.skipped,assessable_ari:s.assessable_ari,
        independent_source_replication:false,
        inferential_uncertainty:'withheld'});
    }
  }
  ensure(run.failure_ledger.every(x=>modelIds.has(x.model_id)),
    'failure ledger contains unknown model');
  const indexSelected=available.filter(o=>selected.has(o.id));
  ensure(indexSelected.length===eligible.length,'selected source subset was not originally available');
  const w1ExcludedAvailable=original.filter(o=>o.source_status==='available'&&
    (o.exclusion_reasons||[]).length).length;
  const total=inventory.population.total_in_frame,usable=inventory.population.available;
  const tested=eligible.length;
  const extra=usable-tested-w1ExcludedAvailable;
  ensure(extra>=0,'negative unselected original-source denominator');
  // W1 fit subset need not exhaust the historical inventory. Unselected
  // original verified cells are never assigned model labels or missing/zero topics.
  const modelPairs=run.comparisons||[];
  ensure(modelPairs.every(p=>modelIds.has(p.left)&&modelIds.has(p.right)),
    'unrecognized model in pairwise comparisons');
  const document={
    schema:'un.w1-historical-inventory-link.candidate.v0',adapter_version:'0.1.0',
    fixture_kind:run.frame.split==='synthetic'?'synthetic':'private_development',
    publication_eligible:false,evaluation_role:'engineering_only',
    contract_status:'coordinator_review_required',legacy_interchange_v1:'withheld',
    upstream:{source_schema:run.frame.source_schema,source_engine:run.frame.source_engine,
      original_source_hash_basis:run.frame.source_hash_basis,
      original_source_sha256:run.frame.source_sha256,
      full_inventory_sha256:inventory.inventory_sha256,
      inventory_selection_sha256:inventory.upstream.selection_sha256,
      w1_selection_sha256:run.frame.selection_sha256,
      w1_population_sha256:run.frame.population_hash},
    coverage:{inventory_total:total,verified_available:usable,
      unverified:inventory.population.unverified,other_missing:inventory.population.other_missing,
      w1_frame_total:original.length,w1_selected_fit_eligible:tested,
      w1_excluded_in_frame:run.frame.excluded,
      verified_explicitly_excluded_in_frame:w1ExcludedAvailable,
      verified_not_selected:extra,
      never_interpret_unverified_as_zero:true,
      unselected_reason:'outside source-bound W1 fit selection, not a failed model or topic absence'},
    models,group_refits:grouping,comparison_count:modelPairs.length,
    failure_ledger_count:run.failure_ledger.length,
    limitations:[
      'Historical candidate read model only; requires coordinator versioned analytical contract approval.',
      'Source verification is inherited from the independently checked private upstream inventory; this linkage does not authenticate original bytes.',
      'Not-selected, unverified, failed and noise observations remain distinct denominators.',
      'Meeting and recorded-affiliation/group source dependence prohibits treating grouped refits as independent replication.',
      'No inference, confidence intervals, geopolitical stance, or public empirical country mapping.'
    ]
  };
  ensure(total===usable+document.coverage.unverified+document.coverage.other_missing,
    'candidate inventory count does not close');
  // Internal check only: a model that declares a full fit may not silently skip
  // some selected eligible rows. No raw texts, source IDs, addresses or vectors serialize.
  ensure(!JSON.stringify(document).includes('"observations"'),'candidate must never include original rows');
  return document;
}
module.exports={linkW1Inventory};
