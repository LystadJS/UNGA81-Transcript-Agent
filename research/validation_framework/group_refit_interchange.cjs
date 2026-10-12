'use strict';

/*
 * W1 grouped hard-assignment sidecar v1.
 * Source links are preserved; original text/vectors are NEVER included.
 * Public use is synthetic-only. Opt-in private development outputs require
 * a separate, caller-controlled private file; no console/HTTP serialization.
 */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const F=require('./frame.cjs');
const W1=require('./interchange.cjs');
const SIDE_SCHEMA=require('./schemas/group-refits.v1.schema.json');

const SCHEMA='un.source-aware.group-refits.v1';
const VERSION='1.0.0';
const SHA=/^[a-f0-9]{64}$/;
const ok=(v,msg)=>assert.ok(v,'W1 grouped-refits: '+msg);
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const hash=x=>F.digest(x);
const RUNNER_SHA=()=>hash(fs.readFileSync(path.join(__dirname,'runner.cjs'),'utf8'));
const allowed=new Set(['fitted','failed','skipped']);

/** Dependency-free JSON Schema subset used by the pinned local sidecar. */
function structural(spec,v,loc='$'){
  if(Object.hasOwn(spec,'const'))ok(v===spec.const,loc+': wrong constant');
  if(spec.enum)ok(spec.enum.includes(v),loc+': unsupported enum');
  if(spec.type){
    const types=Array.isArray(spec.type)?spec.type:[spec.type];
    const matches=t=>t==='null'?v===null:t==='array'?Array.isArray(v):
      t==='object'?v!==null&&typeof v==='object'&&!Array.isArray(v):
      t==='integer'?Number.isSafeInteger(v):
      t==='number'?typeof v==='number'&&Number.isFinite(v):
      typeof v===t;
    ok(types.some(matches),loc+': wrong JSON type');
  }
  if(typeof v==='string'){
    if(spec.minLength!==undefined)ok(v.length>=spec.minLength,loc+': string too short');
    if(spec.pattern)ok(new RegExp(spec.pattern).test(v),loc+': wrong string format');
  }
  if(typeof v==='number'&&spec.minimum!==undefined)
    ok(v>=spec.minimum,loc+': below minimum');
  if(Array.isArray(v)&&spec.items)
    v.forEach((x,i)=>structural(spec.items,x,loc+'['+i+']'));
  if(v!==null&&typeof v==='object'&&!Array.isArray(v)){
    for(const k of spec.required||[])ok(Object.hasOwn(v,k),loc+': missing '+k);
    for(const [k,val] of Object.entries(v)){
      if(Object.hasOwn(spec.properties||{},k))structural(spec.properties[k],val,loc+'.'+k);
      else if(spec.additionalProperties===false)ok(false,loc+': unknown field '+k);
    }
  }
}

function fromNative(native, v1, {allow_private_development=false}={}) {
  ok(native?.schema==='un.source-aware-validation.v1' &&
    native.evaluation_role==='engineering_only' &&
    native.publication_eligible===false, 'native W1 results required');
  ok(v1?.schema==='un.parallel-analysis.v1' && v1.contract_version==='1.0.0' &&
    v1.producer?.workstream_id==='W1' &&
    v1.evaluation_role==='engineering_only' && v1.publication_eligible===false,
    'original unmodified W1 v1 interchange required');
  ok(W1.validateRelational(v1)===true,'W1 v1 relational validation refused');
  const split=v1.cohort.split;
  ok(split==='synthetic' || split==='development' && allow_private_development===true,
    'private development child labels require an explicitly authorized private-only caller');
  ok(split===native.frame.split &&
    v1.producer.fixture_kind===(split==='synthetic'?'synthetic':'private_development'),
    'split/producer mismatch');
  ok(v1.upstream.source_sha256===native.frame.source_sha256 &&
    v1.upstream.selection_sha256===native.frame.selection_sha256 &&
    v1.upstream.source_hash_basis===native.frame.source_hash_basis &&
    v1.cohort.eligible===native.frame.eligible &&
    v1.observations.length===native.frame.observations_total,
    'source, population, hash basis or selection changed');
  ok(v1.producer.code_sha256===RUNNER_SHA(),
    'the actual fitted W1 runner SHA differs from original model producer');
  ok(native._internal_frame && Array.isArray(native._internal_group_refits),
    'run W1 with retain_group_assignments:true; summary-only refits are insufficient');
  ok(!Object.keys(native).includes('_internal_group_refits'),
    'raw child-fit labels may not be enumerable in public W1 outputs');
  const observations=v1.observations.map(o=>({
    id:o.id,text_sha256:o.text_sha256,parent_id:o.parent_id,
    parent_text_sha256:o.parent_text_sha256,meeting_id:o.meeting_id,
    source_family_id:o.source_family_id,date:o.date,
    source_url:o.source_url,json_pointer:o.json_pointer,start:o.start,end:o.end,
    source_status:o.source_status,exclusion_reasons:o.exclusion_reasons.slice()
  }));
  ok(observations.every(x=>!['2026-10-05','2026-10-06'].includes(x.date)),
    'reserved transcript dates never enter grouped refit sidecar');
  if(split==='synthetic')ok(observations.every(o=>o.source_url===null),
    'synthetic sidecar cannot publish original source URLs');
  const eligible=observations.filter(o=>o.source_status==='available'&&
    o.exclusion_reasons.length===0);
  const original=native._internal_frame.filter(o=>o.source_status==='available' &&
    !(o.exclusion_reasons||[]).length);
  ok(equal(eligible.map(x=>[x.id,x.text_sha256]),
    original.map(x=>[x.id,x.text_sha256])) &&
    eligible.length<=600 && eligible.length>=1, 'original ordered ID/text-hash population differs');
  const groupById=new Map(eligible.map(x=>[x.id,x.meeting_id]));
  ok(eligible.every(x=>typeof x.meeting_id==='string'&&x.meeting_id.length>0 &&
    SHA.test(x.text_sha256)), 'verified meeting and text hash required');
  const grouped=F.unionGroups(original,'meeting');
  const groupNames=[...new Set(eligible.map(x=>x.meeting_id))].sort();
  const plan=native.schedules?.meeting;
  ok(plan && Array.isArray(plan.samples) && Array.isArray(plan.groups)===false &&
    Number.isInteger(plan.groups) && plan.groups===grouped.groups.length,
    'W1 whole-meeting grouped schedule required');
  ok(plan.status==='scheduled' || plan.status==='skipped',
    'unknown W1 meeting resampling state');
  ok(native.fit_records.length===v1.models.length &&
    native.model_reports.length===v1.models.length,'model population differs');
  const references=new Map(v1.models.map(m=>[m.model_id,m]));
  const coverage=new Map(v1.coverage.models.map(c=>[c.model_id,c]));
  const records=new Map();
  for(const x of native._internal_group_refits){
    ok(x && x.group_unit==='meeting' && Number.isSafeInteger(x.attempt) &&
      x.attempt>0, 'unknown/non-meeting grouped refit');
    const key=JSON.stringify([x.model_id,x.attempt]);
    ok(!records.has(key), 'duplicate child-fit model/attempt');
    records.set(key,x);
  }
  const refits=[],schedules=[];
  for(const f of native.fit_records){
    const m=references.get(f.model_id),coverageRow=coverage.get(f.model_id),
      report=native.model_reports.find(r=>r.model_id===f.model_id);
    ok(m && coverageRow && report && m.method===f.method &&
      m.parameters_sha256===hash(f.parameters) &&
      m.representation_id===f.representation_id &&
      m.representation_version===f.representation_version &&
      equal(f.observation_ids,eligible.map(x=>x.id)) &&
      equal(f.observation_hashes,eligible.map(x=>x.text_sha256)) &&
      f.population_hash===native.frame.population_hash &&
      f.selection_sha256===v1.upstream.selection_sha256,
      'base W1 fit settings, representation or source-key mismatch');
    const reportGroup=report.group_stability.meeting;
    ok(reportGroup && reportGroup.schedule_sha256===(plan.schedule_sha256??null) &&
      reportGroup.attempted===reportGroup.runs.length &&
      reportGroup.planned===plan.attempted &&
      reportGroup.runs.length===(f.status==='fitted'?plan.samples.length:0),
      'native W1 per-model schedule ledger incomplete');
    schedules.push({base_model_id:f.model_id,group_unit:'meeting',
      schedule_sha256:plan.schedule_sha256??null,status:plan.status,
      planned:plan.attempted,executed:reportGroup.runs.length,
      successful:reportGroup.successful,failed:reportGroup.failed,
      skipped:reportGroup.skipped,distinct_group_samples:plan.unique_group_samples??0,
      reason:reportGroup.reason??null});
    for(const sample of plan.samples){
      if(f.status!=='fitted')continue;
      const meta=reportGroup.runs.find(x=>x.attempt===sample.attempt);
      const actual=records.get(JSON.stringify([f.model_id,sample.attempt]));
      ok(meta&&actual&&actual.model_id===f.model_id &&
        actual.schedule_sha256===plan.schedule_sha256 &&
        actual.attempt===sample.attempt &&
        actual.group_unit==='meeting' &&
        actual.seed===meta.seed &&
        equal(actual.group_indices,sample.group_indices) &&
        equal(actual.observation_ids,sample.indices.map(i=>eligible[i].id)) &&
        equal(actual.observation_text_sha256,sample.indices.map(i=>eligible[i].text_sha256)) &&
        equal(meta.observation_ids,actual.observation_ids) &&
        meta.status===actual.status &&
        meta.attempted_fit===actual.attempted_fit &&
        meta.successful_fit===actual.successful_fit &&
        meta.failed_fit===actual.failed_fit &&
        meta.reason===actual.reason,
        'retained child-fit labels disagree with the original W1 sample ledger');
      ok(allowed.has(actual.status) &&
        actual.attempted_fit===actual.successful_fit+actual.failed_fit &&
        actual.successful_fit<2 && actual.failed_fit<2 &&
        (actual.status==='fitted')===(actual.successful_fit===1),
        'child optimizer attempt/failure status incoherent');
      const selectedGroups=[...new Set(actual.observation_ids.map(id=>groupById.get(id)))].sort();
      const omittedGroups=groupNames.filter(g=>!selectedGroups.includes(g));
      ok(omittedGroups.length>0 && selectedGroups.length>0 &&
        original.every(row=>{
          const selected=actual.observation_ids.includes(row.id);
          return selected===selectedGroups.includes(row.meeting_id);
        }), 'sample splits a whole meeting or omits selected source IDs');
      const closure=new Set(sample.group_indices.flatMap(i=>grouped.groups[i]));
      ok(closure.size===sample.indices.length &&
        sample.indices.every(i=>closure.has(i)),
        'sample violates source-family/parent transitive grouping');
      const status=actual.status,selectedRows=actual.observation_ids.map((id,i)=>({
        observation_id:id,text_sha256:actual.observation_text_sha256[i],
        status:status!=='fitted'?'not_fitted':actual.assignments[i]>0?'assigned':'unassigned',
        cluster:status!=='fitted'?null:actual.assignments[i]
      }));
      ok(status!=='fitted'?actual.assignments===null:
        Array.isArray(actual.assignments) &&
        actual.assignments.length===actual.observation_ids.length &&
        actual.assignments.every(x=>Number.isSafeInteger(x)&&x>=0),
        'missing/invalid source-ordered hard labels');
      ok(selectedRows.filter(x=>x.status==='assigned').length===meta.assigned &&
        selectedRows.filter(x=>x.status==='unassigned').length===meta.unassigned,
        'selected assignment/noise counts differ from W1 reported fit');
      const sampleHash=hash({group_unit:'meeting',selected_groups:selectedGroups});
      const kind=omittedGroups.length===1?'leave_group_out':'group_subsample';
      const resample_id=(kind==='leave_group_out'?'loo-':'subsample-')+sampleHash.slice(0,24);
      const model_id='w1-child-'+hash([f.model_id,sample.attempt,meta.seed,
        plan.schedule_sha256,sampleHash]).slice(0,32);
      const parameters={...f.parameters,seed:meta.seed};
      const fitReplayIdentity=hash({
        runner_sha256:RUNNER_SHA(),source_sha256:native.frame.source_sha256,
        selection_sha256:native.frame.selection_sha256,
        model_id:f.model_id,original_representation_id:f.representation_id,
        representation_version:f.representation_version,
        selected_rows:selectedRows.map(r=>[r.observation_id,r.text_sha256]),
        parameters,group_unit:'meeting'
      });
      refits.push({model_id,base_model_id:f.model_id,
        method:f.method,representation_id:f.representation_id,
        representation_version:f.representation_version,
        original_parameters_sha256:m.parameters_sha256,
        refit_parameters_sha256:hash(parameters),fit_replay_key_sha256:fitReplayIdentity,
        source_group_unit:'meeting',resample_type:kind,resample_id,
        schedule_sha256:plan.schedule_sha256,attempt:sample.attempt,
        seed:meta.seed,selected_groups:selectedGroups,omitted_groups:omittedGroups,
        status,attempted_fits:actual.attempted_fit,
        successful_fits:actual.successful_fit,failed_fits:actual.failed_fit,
        skipped_fits:status==='skipped'?1:0,reason:actual.reason,
        selected_rows:selectedRows});
      records.delete(JSON.stringify([f.model_id,sample.attempt]));
    }
  }
  ok(records.size===0, 'unmatched, spurious or unsupported retained child-fit');
  const sidecar={schema:SCHEMA,contract_version:VERSION,
    evaluation_role:'engineering_only',publication_eligible:false,
    producer:{workstream_id:'W1',runtime:process.version,
      code_sha256:RUNNER_SHA(),artifact_kind:split==='synthetic'?'synthetic':'private_development'},
    upstream:{source_schema:v1.upstream.source_schema,
      source_hash_basis:v1.upstream.source_hash_basis,
      source_sha256:v1.upstream.source_sha256,
      selection_sha256:v1.upstream.selection_sha256,
      population_hash:native.frame.population_hash,
      observations_sha256:hash(observations),
      original_w1_interchange_code_sha256:v1.producer.code_sha256},
    cohort:{split,unit:v1.cohort.unit,eligible:eligible.length,
      inventory_meetings:v1.coverage.inventory_meetings,
      source_group_unit:'meeting',
      source_group_count:groupNames.length,
      grouping_components:grouped.groups.length,
      source_group_ids:groupNames,
      resampling_policy:'W1 whole-source-group without-replacement subsampling; no bootstrap or independent-replication claim'},
    observations,models:v1.models.map(m=>({...m})),schedules,refits,
    limitations:[
      'The sidecar retains actual refitted hard labels, not a reconstruction from W1 summary agreement metrics.',
      'Lexical vocabulary/IDF/PCA/LSA is refitted for each sample. The replay key proves settings and source identities, not a saved transformation matrix hash.',
      'Repeated source-group subsets are one distinct sample design, not independent source replications.',
      'Pairwise spread is a descriptive source-group sensitivity diagnostic, not a confidence interval, null test, government stance, alliance or probability.'
    ]};
  validateSidecar(sidecar,v1);
  return sidecar;
}

function validateSidecar(sidecar,original){
  structural(SIDE_SCHEMA,sidecar);
  ok(sidecar&&sidecar.schema===SCHEMA&&sidecar.contract_version===VERSION &&
    sidecar.publication_eligible===false&&sidecar.evaluation_role==='engineering_only',
    'versioned engineering sidecar required');
  ok(original?.schema==='un.parallel-analysis.v1' &&
    original.producer?.workstream_id==='W1'&&
    original.publication_eligible===false,
    'original W1 interchange required to authenticate sidecar');
  const s=sidecar,src=original.upstream;
  ok(s.upstream.source_schema===src.source_schema &&
    s.upstream.source_hash_basis===src.source_hash_basis &&
    s.upstream.source_sha256===src.source_sha256 &&
    s.upstream.selection_sha256===src.selection_sha256 &&
    s.upstream.original_w1_interchange_code_sha256===original.producer.code_sha256 &&
    s.upstream.observations_sha256===hash(s.observations) &&
    s.cohort.eligible===original.cohort.eligible &&
    s.cohort.inventory_meetings===original.coverage.inventory_meetings &&
    s.cohort.unit===original.cohort.unit &&
    s.cohort.split===original.cohort.split &&
    s.cohort.source_group_unit==='meeting' &&
    equal(s.observations.map(x=>[x.id,x.text_sha256,x.meeting_id,x.parent_id,x.source_family_id,x.source_url,x.start,x.end]),
      original.observations.map(x=>[x.id,x.text_sha256,x.meeting_id,x.parent_id,x.source_family_id,x.source_url,x.start,x.end])),
    'sidecar source identity or observation lineage was altered');
  ok(s.producer.code_sha256===original.producer.code_sha256,
    'producer/runner provenance differs');
  ok(s.cohort.split==='synthetic'||s.cohort.split==='development',
    'unsupported sidecar split');
  if(s.cohort.split==='synthetic')ok(s.producer.artifact_kind==='synthetic' &&
    s.observations.every(x=>x.source_url===null &&
      !['2026-10-05','2026-10-06'].includes(x.date)),
    'fictional source only; reserved source dates and source URLs forbidden');
  const eligible=new Map(s.observations.filter(o=>o.source_status==='available' &&
    o.exclusion_reasons.length===0).map(o=>[o.id,o]));
  const groups=[...new Set([...eligible.values()].map(o=>o.meeting_id))].sort();
  ok(groups.length>=1 && equal(groups,s.cohort.source_group_ids) &&
    s.cohort.source_group_count===groups.length,
    'invalid whole-source group ledger');
  const base=new Map(original.models.map(m=>[m.model_id,m]));
  ok(s.models.length===base.size &&
    s.models.every(m=>base.has(m.model_id)&&equal(m,base.get(m.model_id))),
    'parent model identity changed');
  const seen=new Set(),scheduleMap=new Map(s.schedules.map(x=>[x.base_model_id,x]));
  ok(scheduleMap.size===base.size,'missing model sample schedule');
  for(const x of s.refits){
    const ref=base.get(x.base_model_id);
    ok(ref&&ref.method===x.method &&
      ref.representation_id===x.representation_id &&
      ref.representation_version===x.representation_version &&
      ref.parameters_sha256===x.original_parameters_sha256 &&
      SHA.test(x.refit_parameters_sha256) && SHA.test(x.fit_replay_key_sha256) &&
      x.source_group_unit==='meeting' &&
      Number.isInteger(x.seed)&&Number.isInteger(x.attempt)&&x.attempt>=1,
      'child numerical model and original parameters mismatch');
    ok(!seen.has(x.model_id)&&x.model_id!==x.base_model_id,'duplicate child-fit identity');
    seen.add(x.model_id);
    ok(equal(x.selected_groups,[...new Set(x.selected_groups)].sort()) &&
      x.omitted_groups.length>0 &&
      equal([...x.selected_groups,...x.omitted_groups].sort(),groups) &&
      x.selected_groups.every(g=>!x.omitted_groups.includes(g)),
      'selected/omitted meeting ledger incomplete');
    ok(x.resample_type===(x.omitted_groups.length===1?'leave_group_out':'group_subsample') &&
      x.resample_id===
        (x.resample_type==='leave_group_out'?'loo-':'subsample-')+
        hash({group_unit:'meeting',selected_groups:x.selected_groups}).slice(0,24),
      'sample design incorrectly labelled as bootstrap/LOO');
    const schedule=scheduleMap.get(x.base_model_id);
    ok(schedule && schedule.status==='scheduled' &&
      x.schedule_sha256===schedule.schedule_sha256 &&
      x.attempt<=schedule.planned, 'child outside declared schedule');
    ok(x.attempted_fits===x.successful_fits+x.failed_fits &&
      x.successful_fits<=1&&x.failed_fits<=1 &&
      (x.status==='fitted')===(x.successful_fits===1) &&
      (x.status==='skipped')===(x.skipped_fits===1) &&
      allowed.has(x.status),
      'child attempt/status/missingness accounting invalid');
    const matched=new Set();
    for(const row of x.selected_rows){
      const o=eligible.get(row.observation_id);
      ok(o&&!matched.has(row.observation_id) &&
        row.text_sha256===o.text_sha256 &&
        x.selected_groups.includes(o.meeting_id) &&
        (x.status==='fitted'?
          row.status===(row.cluster>0?'assigned':'unassigned') &&
          Number.isSafeInteger(row.cluster)&&row.cluster>=0:
          row.status==='not_fitted'&&row.cluster===null),
        'child assignment row missing, duplicated, noise mislabeled or wrong text SHA');
      matched.add(row.observation_id);
    }
    ok(matched.size===([...eligible.values()].filter(o=>x.selected_groups.includes(o.meeting_id))).length,
      'selected whole source groups lack complete original child labels');
  }
  for(const schedule of s.schedules){
    ok(base.has(schedule.base_model_id) &&
      schedule.executed===s.refits.filter(r=>r.base_model_id===schedule.base_model_id).length &&
      schedule.planned>=schedule.executed &&
      schedule.successful===s.refits.filter(r=>r.base_model_id===schedule.base_model_id &&r.status==='fitted').length &&
      schedule.failed===s.refits.filter(r=>r.base_model_id===schedule.base_model_id &&r.status==='failed').length &&
      schedule.skipped===s.refits.filter(r=>r.base_model_id===schedule.base_model_id &&r.status==='skipped').length,
      'per-model grouped refit ledger does not reconcile');
  }
  return true;
}
module.exports={SCHEMA,VERSION,fromNative,validateSidecar};
