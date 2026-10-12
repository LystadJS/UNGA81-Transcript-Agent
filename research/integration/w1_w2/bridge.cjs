'use strict';

/*
 * Coordinator read-only W1 -> W2 integration. Synthetic results only.
 * Raw W1 fitting provenance stays unchanged; this is an explicitly derived
 * family projection, never an upstream source or numerical kernel edit.
 */
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const fs=require('node:fs');
const path=require('node:path');
const W1=require('../../validation_framework/interchange.cjs');
const F=require('../../validation_framework/frame.cjs');
const W2=require('../../consensus/consensus.cjs');

const SCHEMA='un.w1-w2-consensus-bridge.v1';
const VERSION='1.0.0';
const SHA=/^[a-f0-9]{64}$/;
const FAMILY=Object.freeze({
  kmeans:'partition',pam:'partition',
  hierarchical:'hierarchical',hdbscan:'density',gmm:'mixture'
});
const digest=x=>crypto.createHash('sha256').update(
  typeof x==='string'?x:stable(x)).digest('hex');
const stable=x=>Array.isArray(x)?'['+x.map(stable).join(',')+']':
  x!==null&&typeof x==='object'?
    '{'+Object.keys(x).sort().filter(k=>x[k]!==undefined).map(k=>JSON.stringify(k)+':'+stable(x[k])).join(',')+'}':
    JSON.stringify(x);
const clone=x=>structuredClone(x);
const check=(ok,message)=>assert.ok(ok,'w1-w2: '+message);
const identical=(a,b)=>stable(a)===stable(b);
const codeSHA=()=>digest(fs.readFileSync(path.join(__dirname,'bridge.cjs'),'utf8'));
const W1_RUNNER_SHA=()=>digest(fs.readFileSync(
  path.join(__dirname,'../../validation_framework/runner.cjs'),'utf8'));
function eligible(e){
  return e.observations.filter(x=>x.source_status==='available'&&x.exclusion_reasons.length===0);
}
function configIdentity(f){
  const spec=clone(f.parameters);
  // Seed and display ID are not settings; all other validated fit choices are.
  delete spec.seed;
  delete spec.id;
  return digest({method:f.method,representation_id:f.representation_id,
    representation_version:f.representation_version,parameters_without_seed:spec});
}
function recordAudit(out,e){
  check(out&&out.schema==='un.source-aware-validation.v1' &&
    out.publication_eligible===false && out.evaluation_role==='engineering_only',
    'verified W1 native result required');
  check(e&&e.schema==='un.parallel-analysis.v1' &&
    e.contract_version==='1.0.0'&&e.producer?.workstream_id==='W1' &&
    e.producer?.fixture_kind==='synthetic' &&
    e.cohort?.split==='synthetic' && out.frame?.split==='synthetic' &&
    e.evaluation_role==='engineering_only'&&e.publication_eligible===false,
    'only W1 synthetic, engineering-only interchange may be projected');
  check(e.upstream?.source_schema==='synthetic.v1'&&
    e.upstream?.source_hash_basis==='synthetic', 'synthetic source schema/hash basis required');
  check(e.producer.code_sha256===W1_RUNNER_SHA(),
    'W1 numerical runner differs from the declared producer code hash');
  W2.validateEnvelope(e);
  check(W1.validateRelational(e)===true,'W1 source/fit relational contract failed');
  check(out.frame.source_sha256===e.upstream.source_sha256 &&
    out.frame.selection_sha256===e.upstream.selection_sha256 &&
    out.frame.source_hash_basis===e.upstream.source_hash_basis &&
    out.frame.eligible===e.cohort.eligible &&
    out.frame.observations_total===e.observations.length &&
    out.frame.unit===e.cohort.unit &&
    e.cohort.source_group_unit==='synthetic',
    'native W1 and interchange source cohort differ');
  check(Array.isArray(out.fit_records)&&out.fit_records.length===e.models.length &&
    Array.isArray(out.model_reports) && out.model_reports.length===e.models.length,
    'unmatched W1 fitted models');
  check(!e.observations.some(o=>Object.hasOwn(o,'text')) &&
    !e.results.some(r=>Object.hasOwn(r,'text')), 'no source text in public W1 v1 metadata');
  const ids=eligible(e).map(o=>o.id),hashes=eligible(e).map(o=>o.text_sha256);
  const audit=[], plan={}, projected=clone(e);
  const models=new Map(e.models.map(m=>[m.model_id,m]));
  const coverage=new Map(e.coverage.models.map(c=>[c.model_id,c]));
  const reports=new Map(out.model_reports.map(r=>[r.model_id,r]));
  const seen=new Set();
  for(const f of out.fit_records){
    const m=models.get(f.model_id), c=coverage.get(f.model_id), r=reports.get(f.model_id);
    check(m&&c&&r&&!seen.has(f.model_id),'unknown/duplicate W1 native model');
    seen.add(f.model_id);
    check(Object.hasOwn(FAMILY,f.method)&&m.method===f.method,
      'unknown or mismatched W1 clustering algorithm');
    check(m.method_family==='unsupervised_partition',
      'W1 family mapping contract changed; do not silently remap');
    check(m.parameters_sha256===F.digest(f.parameters) &&
      Number.isSafeInteger(f.seed) && f.seed>=0 &&
      f.seed===f.parameters.seed, 'unverified native parameters or seed');
    check(f.source_sha256===e.upstream.source_sha256 &&
      f.selection_sha256===e.upstream.selection_sha256 &&
      f.population_hash===out.frame.population_hash &&
      f.representation_id===m.representation_id &&
      f.representation_version===m.representation_version &&
      identical(f.observation_ids,ids)&&identical(f.observation_hashes,hashes),
      'W1 model population, transformation or source identity drift');
    const result=new Map(e.results.filter(x=>x.model_id===f.model_id)
      .map(x=>[x.observation_id,x]));
    check(result.size===e.observations.length,'model results omit an observation');
    check(f.status==='fitted' || f.status==='failed'||f.status==='skipped',
      'unknown numerical fit state');
    for(let i=0;i<ids.length;i++){
      const row=result.get(ids[i]);
      const expected=f.status==='fitted'?
        (f.assignments[i]===0?'unassigned':'assigned'):'not_fitted';
      check(row.status===expected &&
        row.cluster===(expected==='not_fitted'?null:f.assignments[i]),
        'native W1 assignment differs from interchange');
    }
    check(f.status==='fitted'?
      f.successful_fit===1&&f.failed_fit===0&&c.successful_fits>0:
      f.successful_fit===0&&
      e.results.filter(x=>x.model_id===f.model_id&&x.status==='assigned').length===0,
      'failed/nonfit full model has no valid W1 accounting');
    const family=FAMILY[f.method];
    const config=configIdentity(f);
    const mapped=projected.models.find(x=>x.model_id===f.model_id);
    mapped.method_family=family;
    plan[f.model_id]={configuration_id:config,seed:f.seed};
    const groups=Object.fromEntries(Object.entries(r.group_stability||{}).map(([unit,g])=>
      [unit,{planned:g.planned,attempted:g.attempted,successful:g.successful,
        failed:g.failed,skipped:g.skipped,
        source_groups:g.groups,assessable_ari:g.assessable_ari,
        pairwise_refit_assignments_available:false}]));
    // W1 exposes comparisons/assignment counts per refit, NOT the child
    // observation -> child cluster labels needed for W2 pair opportunities.
    for(const g of Object.values(r.group_stability||{}))
      check((g.runs||[]).every(x=>!Object.hasOwn(x,'assignments')),
        'W1 refit record layout changed; review before consuming');
    audit.push({model_id:f.model_id,original_family:m.method_family,
      derived_family:family,method:f.method,seed:f.seed,
      configuration_id:config,
      parameters_sha256:m.parameters_sha256,
      representation_id:m.representation_id,
      representation_version:m.representation_version,
      full_fit_status:f.status,
      full_fit_assigned:result.size?ids.filter(id=>result.get(id).status==='assigned').length:0,
      grouped_refits:groups});
  }
  check(seen.size===models.size,'incomplete W1 fit audit');
  // Explicit derivation: a W2 projection must not impersonate the W1 producer.
  projected.producer={
    workstream_id:'W2',adapter_version:VERSION,code_sha256:codeSHA(),
    runtime:process.version,generated_at:'2026-10-08T00:00:00Z',fixture_kind:'synthetic'
  };
  W2.validateEnvelope(projected);
  check(identical(projected.upstream,e.upstream) &&
    identical(projected.cohort,e.cohort) &&
    identical(projected.observations,e.observations) &&
    identical(projected.results,e.results) &&
    identical(projected.coverage,e.coverage),
    'family remapping altered original input, results, source identity or coverage');
  return {projected,fit_plan:plan,models:audit};
}
function fromW1(out,original,{min_association=0.8,min_coverage=0.4,
  min_families=2,min_source_groups=2}={}){
  const a=recordAudit(out,original);
  const consensus=W2.runConsensus([a.projected],{
    fit_plan:a.fit_plan,
    cross_basis_protocol:'identity_join_hard_partition_v1',
    min_association,min_coverage,min_families,min_source_groups});
  W2.validateConsensus(consensus);
  check(consensus.uncertainty.design==='not_estimated' &&
    consensus.uncertainty.pairwise.length===0,
    'W1 stability summaries cannot become W2 group-refit assignment evidence');
  const interchange=W2.toInterchangeV1(a.projected,consensus,
    {generated_at:'2026-10-08T00:00:00Z',code_sha256:codeSHA()});
  W2.validateEnvelope(interchange);
  const audit={schema:SCHEMA,version:VERSION,evaluation_role:'engineering_only',
    publication_eligible:false,source_split:'synthetic',
    original_w1_code_sha256:original.producer.code_sha256,
    bridge_code_sha256:codeSHA(),
    source_sha256:original.upstream.source_sha256,
    source_hash_basis:original.upstream.source_hash_basis,
    selection_sha256:original.upstream.selection_sha256,
    source_unit:original.cohort.unit,
    eligible:original.cohort.eligible,excluded:original.coverage.excluded,
    unavailable_sources:original.coverage.unavailable_sources,
    method_family_mapping:FAMILY,
    models:a.models,
    weighted_families:consensus.family_weight_audit.map(f=>({
      method_family:f.method_family,total_planned_weight:f.total_weight,
      models:f.models,fully_failed_records:f.completely_failed_fit_records})),
    grouped_refit_pairwise_status:'withheld',
    grouped_refit_pairwise_reason:'W1 group_stability.runs retains summary metrics but no per-refit hard-assignment arrays; cannot derive pairwise numerators or uncertainty spread.',
    numerical_fit_stability_status:'W1 summary only; kept separate from W2 cross-method agreement.',
    cross_method_agreement_status:'conditional_descriptive',
    inferential_evidence_status:'withheld_no_null_calibration',
    no_holdout_access:true,no_publication:true,
    limitations:[
      'Source-group omission diagnostics belong to W1; W2 pairwise bootstrap/LOO uncertainty is NOT estimated from summary-only W1 refits.',
      'Method families are a declared algorithm classification; similar lexical representations do not confer independent source evidence.',
      'No real-source inference, national positions, alliances, diplomatic agreement probability or best-model metric.'
    ]};
  return {projected_envelope:a.projected,consensus,interchange,audit};
}
module.exports={SCHEMA,VERSION,FAMILY,recordAudit,configIdentity,fromW1};
