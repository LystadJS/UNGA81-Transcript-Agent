'use strict';

/*
 * Authenticated W1 child hard-labels -> W2 grouped source sensitivity.
 * Coordinator research adapter only, no browser or private source ingestion.
 * Actual child labels come from W1's opt-in internal grouped numerical fits.
 */
const assert=require('node:assert/strict');
const W1=require('../../validation_framework/group_refit_interchange.cjs');
const W2=require('../../consensus/consensus.cjs');
const Bridge=require('./bridge.cjs');

const check=(p,m)=>assert.ok(p,'W1-W2 grouped: '+m);
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const deepCopy=x=>structuredClone(x);
const groupKey=o=>o.meeting_id;
const selected=(r,groups)=>groups.includes(groupKey(r));
function buildChildEnvelope(parent,sidecar,baseline) {
  check(parent&&parent.schema==='un.parallel-analysis.v1'&&
    parent.producer.workstream_id==='W2'&&parent.cohort.split==='synthetic',
    'verified W2-derived baseline required');
  W1.validateSidecar(sidecar,baseline.original);
  check(sidecar.refits.every(r=>r.source_group_unit==='meeting' &&
    ['leave_group_out','group_subsample'].includes(r.resample_type)),
    'child fits must identify the original without-replacement meeting group design');
  check(sidecar.refits.length<=2000,'too many grouped child-fit records; no implicit selection');
  const models=[],results=[],coverage=[],failure_ledger=[],fit_plan={};
  const parentModels=new Map(parent.models.map(m=>[m.model_id,m]));
  const configured=new Map(baseline.modelAudit.map(x=>[x.model_id,x]));
  const source=parent.observations;
  const excluded=source.filter(o=>o.source_status!=='available'||o.exclusion_reasons.length>0);
  const eligible=source.filter(o=>o.source_status==='available'&&o.exclusion_reasons.length===0);
  const originals=new Map(eligible.map(o=>[o.id,o]));
  const parents=new Map(parent.results.map(r=>[r.model_id+'\u001f'+r.observation_id,r]));
  const seen=new Set();
  for(const refit of sidecar.refits){
    const baseModel=parentModels.get(refit.base_model_id);
    const audit=configured.get(refit.base_model_id);
    check(baseModel&&audit&&audit.derived_family===baseModel.method_family&&
      refit.method===baseModel.method &&
      refit.representation_id===baseModel.representation_id &&
      refit.representation_version===baseModel.representation_version &&
      refit.original_parameters_sha256===baseModel.parameters_sha256 &&
      !seen.has(refit.model_id), 'original model identity or repeated child ID');
    seen.add(refit.model_id);
    const childModel={
      ...deepCopy(baseModel),model_id:refit.model_id,
      // These are sample-specific replay IDs, NOT actual fitted feature-matrix digests.
      representation_id:baseModel.representation_id+'::group-refit-'+refit.fit_replay_key_sha256.slice(0,24),
      representation_version:baseModel.representation_version+'+W1-group-refit-v1',
      fit_version:'source-validation-group-refit-1.0.0',
      parameters_sha256:refit.refit_parameters_sha256,
      diagnostic_basis:'Native W1 hard assignments; source-group-subset refit, source/seed replay key, NOT saved geometry'
    };
    models.push(childModel);
    const byId=new Map(refit.selected_rows.map(row=>[row.observation_id,row]));
    let assigned=0,unassigned=0,not_fitted=0;
    for(const observation of source){
      const original=parents.get(refit.base_model_id+'\u001f'+observation.id);
      check(original,'original W1 result missing source record');
      const removed=observation.source_status!=='available'||observation.exclusion_reasons.length>0;
      const r=byId.get(observation.id);
      let status,cluster,reason;
      if(removed){status='excluded';cluster=null;reason=original.reason||observation.exclusion_reasons.join('; ')||'Source absent/excluded';}
      else if(!selected(observation,refit.selected_groups)){
        check(!r,'omitted source group contains a fitted label');
        status='not_fitted';cluster=null;reason='Omitted whole source group under W1 resampling';
        not_fitted++;
      }else {
        check(r&&r.text_sha256===originals.get(observation.id).text_sha256,
          'selected child-fit source ID/text SHA missing or changed');
        status=r.status;cluster=r.cluster;
        reason=status==='not_fitted'?refit.reason||'W1 child refit failed/skipped':
          status==='unassigned'?'W1 density noise / unassigned':null;
        if(status==='assigned')assigned++;
        else if(status==='unassigned')unassigned++;
        else if(status==='not_fitted')not_fitted++;
        else check(false,'unknown child-fit assignment status');
      }
      results.push({model_id:childModel.model_id,observation_id:observation.id,
        status,cluster,membership_kind:'none',memberships:null,membership_strength:null,
        representation_basis_id:childModel.representation_id,reason});
    }
    check(assigned+unassigned+not_fitted===eligible.length &&
      assigned+unassigned===(refit.status==='fitted'?refit.selected_rows.length:0),
      'child eligible source accounting or skipped results inconsistent');
    coverage.push({
      model_id:refit.model_id,eligible:eligible.length,assigned,unassigned,not_fitted,
      excluded:excluded.length,attempted_fits:refit.attempted_fits,
      successful_fits:refit.successful_fits,failed_fits:refit.failed_fits,
      skipped_fits:refit.skipped_fits
    });
    if(refit.status!=='fitted')failure_ledger.push({
      model_id:refit.model_id,attempt:refit.attempt,
      status:refit.status==='skipped'?'skipped':'failed',
      reason:refit.reason||'Nonfitted W1 grouped sample',
      seed:refit.seed,source_group:'meeting'
    });
    fit_plan[refit.model_id]={
      configuration_id:audit.configuration_id,seed:refit.seed,
      resample_type:refit.resample_type,resample_id:refit.resample_id,
      sampled_groups:refit.selected_groups.slice()
    };
  }
  const derived={
    schema:'un.parallel-analysis.v1',contract_version:'1.0.0',
    producer:{...deepCopy(parent.producer),adapter_version:'W1-W2-grouped-1.0.0'},
    upstream:deepCopy(parent.upstream),cohort:deepCopy(parent.cohort),
    observations:deepCopy(parent.observations),models,results,
    coverage:{inventory_meetings:parent.coverage.inventory_meetings,
      observations_total:parent.observations.length,eligible:eligible.length,
      excluded:excluded.length,
      unavailable_sources:parent.coverage.unavailable_sources,
      models:coverage,failure_ledger},
    evidence:[],diagnostics:[],
    limitations:[{code:'group_subsample_descriptive',scope:'all',
      description:'Source-group child fits are without-replacement subsamples. Neither bootstrap nor source-independent inference.'}],
    publication_eligible:false,evaluation_role:'engineering_only'
  };
  // Empty W1 schedules are legitimate but cannot contribute W2 pair uncertainty.
  if(models.length)W2.validateEnvelope(derived);
  return {derived,fit_plan,base_models:parent.models.length,
    child_models:models.length,source_groups:sidecar.cohort.source_group_count};
}
function withGroupedRefits(native,original,{sidecar=null,limits={}}={}){
  check(native?._internal_group_refits&&native.frame?.split==='synthetic',
    'only opt-in W1 synthetic source-bound child fits supported in public coordinator adapter');
  const originalSidecar=W1.fromNative(native,original);
  const supplied=sidecar||originalSidecar;
  check(same(supplied,originalSidecar),
    'persisted group-refit sidecar differs from actual retained W1 child numerical labels');
  const baseline=Bridge.recordAudit(native,original);
  const inner=buildChildEnvelope(baseline.projected,supplied,{
    original,modelAudit:baseline.models
  });
  const inputs=[baseline.projected];
  if(inner.child_models>0)inputs.push(inner.derived);
  const plan={...baseline.fit_plan,...inner.fit_plan};
  const consensus=W2.runConsensus(inputs,{
    fit_plan:plan,cross_basis_protocol:'identity_join_hard_partition_v1',
    ...limits
  });
  W2.validateConsensus(consensus);
  const v1=W2.toInterchangeV1(baseline.projected,consensus,
    {generated_at:'2026-10-08T00:00:00Z'});
  W2.validateEnvelope(v1);
  const distinct=Object.fromEntries(['leave_group_out','group_subsample','group_bootstrap']
    .map(type=>[type,new Set(supplied.refits.filter(x=>x.resample_type===type)
      .map(x=>x.resample_id)).size]));
  const attempts={
    planned:supplied.schedules.reduce((s,x)=>s+x.planned,0),
    executed:supplied.refits.length,
    attempted:supplied.refits.reduce((s,x)=>s+x.attempted_fits,0),
    successful:supplied.refits.reduce((s,x)=>s+x.successful_fits,0),
    failed:supplied.refits.reduce((s,x)=>s+x.failed_fits,0),
    skipped:supplied.refits.reduce((s,x)=>s+x.skipped_fits,0)
  };
  check(attempts.attempted===attempts.successful+attempts.failed &&
    attempts.planned>=attempts.executed,
    'source-group attempts incorrectly counted or dropped');
  const audit={
    schema:'un.w1-w2.source-group-uncertainty.v1',
    evaluation_role:'engineering_only',publication_eligible:false,
    source_sha256:supplied.upstream.source_sha256,
    source_hash_basis:supplied.upstream.source_hash_basis,
    selection_sha256:supplied.upstream.selection_sha256,
    w1_runner_sha256:supplied.producer.code_sha256,
    original_models:inner.base_models,child_models:inner.child_models,
    source_groups:inner.source_groups,grouping_components:supplied.cohort.grouping_components,
    resample_design:'whole-meeting without-replacement only',
    distinct_group_samples:distinct,attempts,
    pairwise_records:consensus.uncertainty.pairwise.length,
    pairwise_descriptive:consensus.uncertainty.pairwise.filter(p=>
      ['leave_group_out','group_subsample'].some(t=>p[t]?.status==='descriptive')).length,
    null_calibrated_evidence:'not_run',
    contains_real_source_text:false,opened_reserved_transcripts:0,
    limitations:[
      'Source-group resampling is descriptive sensitivity, not an independent replication design, inferential confidence interval, or bootstrap.',
      'W1 source-group labels and source hashes are validated; source-group exchangeability and source-family dependence are not established.',
      'The refit replay key describes immutable settings and input IDs, not a stored lexical feature-matrix checksum.',
      'Fitted-group similarity never measures official country stance, alliance, causation or policy agreement.'
    ]
  };
  return {sidecar:supplied,baseline:baseline.projected,refits:inner.derived,
    consensus,interchange:v1,audit};
}
module.exports={buildChildEnvelope,withGroupedRefits};
