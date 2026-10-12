'use strict';
/* Native W1 source-group hard labels -> W2 conditional pair uncertainty. */
const test=require('node:test');
const assert=require('node:assert/strict');
const W1=require('../../validation_framework/runner.cjs');
const W1V1=require('../../validation_framework/interchange.cjs');
const Source=require('../../validation_framework/group_refit_interchange.cjs');
const F=require('../../validation_framework/frame.cjs');
const {makeFixture,SETTINGS}=require('../../validation_framework/examples/synthetic_fixture.cjs');
const W2=require('../../consensus/consensus.cjs');
const W5=require('../../../site/parallel/w05-browser/experimental/method-lab/contracts.js');
const Bridge=require('./bridge.cjs');
const Grouped=require('./grouped_refits.cjs');

const clone=x=>structuredClone(x);
let original,native,sidecar,merged,baseline;
test.before(async()=>{
  const f=makeFixture();
  native=await W1.run(f.frame,SETTINGS,{
    saved:f.saved,group_units:['meeting'],replicates:18,
    group_seed:31,retain_group_assignments:true});
  original=W1V1.toInterchangeV1(native);
  sidecar=Source.fromNative(native,original);
  merged=Grouped.withGroupedRefits(native,original,{sidecar});
  baseline=Bridge.fromW1(native,original);
});
test('W1 exports authentic source-hash-linked child labels after original numerical fits',()=>{
  assert.equal(native._internal_group_refits.length,90);
  assert.equal(sidecar.refits.length,90);
  assert.equal(sidecar.cohort.eligible,24);
  assert.equal(sidecar.cohort.source_group_count,6);
  assert(sidecar.refits.every(r=>r.source_group_unit==='meeting' &&
    r.omitted_groups.length===1 && r.resample_type==='leave_group_out'));
  assert.equal(Source.validateSidecar(sidecar,original),true);
});
test('W2 receives complete original eligible frame including every omitted child pair',()=>{
  assert.equal(W2.validateEnvelope(merged.refits).eligible.size,24);
  assert.equal(merged.refits.models.length,90);
  assert.equal(merged.refits.coverage.models.length,90);
  assert.equal(merged.refits.results.length,90*25);
  assert(merged.refits.coverage.models.every(c=>c.eligible===24 && c.excluded===1 &&
    c.assigned+c.unassigned+c.not_fitted===24 &&
    c.attempted_fits===c.successful_fits+c.failed_fits));
  for(const r of sidecar.refits){
    const rows=merged.refits.results.filter(x=>x.model_id===r.model_id);
    const omitted=rows.filter(x=>x.status==='not_fitted');
    assert.equal(omitted.length,4);
    assert(omitted.every(x=>x.reason.includes('Omitted whole source group')));
    assert.equal(rows.filter(x=>x.status==='excluded').length,1);
  }
});
test('W2 preserves baseline family equality and explicit pair numerators with child missingness',()=>{
  assert.equal(merged.audit.original_models,5);
  assert.equal(merged.audit.child_models,90);
  assert.equal(merged.consensus.observation_ids.length,24);
  assert.equal(merged.consensus.pairs.length,300);
  assert.equal(merged.consensus.family_weight_audit.length,4);
  assert(merged.consensus.family_weight_audit.every(f=>Math.abs(f.total_weight-.25)<1e-9));
  const group=merged.consensus.pairs.find(p=>p.observation_a==='synthetic-01' &&
    p.observation_b==='synthetic-02');
  assert.equal(group.planned_count,95);
  assert(group.missing_pair_count>0);
  assert(group.assigned_both_count<group.planned_count);
  assert(group.coassigned_count<=group.assigned_both_count);
  assert.equal(merged.audit.attempts.planned,90);
  assert.equal(merged.audit.attempts.executed,90);
  assert.equal(merged.audit.attempts.failed,0);
  assert.equal(merged.audit.attempts.skipped,0);
  assert.equal(W2.validateConsensus(merged.consensus),true);
});
test('W2 truly computes leave-group-out pairwise descriptive spread and never confidence',()=>{
  assert.equal(merged.consensus.uncertainty.design,'grouped_refits_descriptive_spread');
  assert.equal(merged.consensus.uncertainty.source_groups,6);
  assert.equal(merged.consensus.uncertainty.pairwise.length,276);
  assert.equal(merged.audit.distinct_group_samples.leave_group_out,6);
  assert.equal(merged.audit.distinct_group_samples.group_subsample,0);
  assert.equal(merged.audit.distinct_group_samples.group_bootstrap,0);
  assert(merged.audit.pairwise_descriptive>0);
  const p=merged.consensus.uncertainty.pairwise.find(x=>
    x.observation_a==='synthetic-01'&&x.observation_b==='synthetic-02');
  assert.equal(p.leave_group_out.total_resamples,6);
  assert.equal(p.leave_group_out.assessable_resamples,5);
  assert.equal(p.leave_group_out.status,'descriptive');
  assert(p.leave_group_out.p05!==null&&p.leave_group_out.p95!==null);
  assert(p.leave_group_out.p05>=0&&p.leave_group_out.p95<=1);
  assert.equal(p.leave_group_out.reference_policy,'omit_exactly_one_source_group');
  assert.equal(p.group_bootstrap.status,'withheld');
  assert.equal(p.group_subsample.status,'withheld');
  assert(!Object.keys(p.leave_group_out).includes('confidence_interval'));
  assert.equal(merged.audit.null_calibrated_evidence,'not_run');
});
test('source-separated baseline comparison and W5 export retain original provenance and no texts',()=>{
  assert.deepEqual(merged.baseline.observations,baseline.projected_envelope.observations);
  assert.deepEqual(merged.interchange.upstream,original.upstream);
  assert.equal(merged.interchange.coverage.excluded,1);
  assert.equal(merged.interchange.coverage.unavailable_sources,1);
  assert.equal(W5.fromParallel(merged.interchange).models.length,1);
  const contents=JSON.stringify(merged);
  assert(!contents.includes('Harbor ferry cargo docks'));
  assert(!contents.includes('"text":'));
  assert(!contents.includes('"vector":'));
  assert.equal(merged.interchange.publication_eligible,false);
  assert.equal(merged.audit.opened_reserved_transcripts,0);
});
test('source-hash, sample-selection or child-label corruption is refused before W2 computation',()=>{
  const a=clone(sidecar);
  a.refits[0].selected_rows[0].cluster=a.refits[0].selected_rows[0].cluster===1?2:1;
  assert.throws(()=>Grouped.withGroupedRefits(native,original,{sidecar:a}),/differs from actual retained W1/);
  const b=clone(sidecar);
  b.refits[0].selected_rows[0].text_sha256='0'.repeat(64);
  assert.throws(()=>Grouped.withGroupedRefits(native,original,{sidecar:b}),/source|child|differs/);
  const c=clone(sidecar);
  c.refits[0].resample_type='group_bootstrap';
  assert.throws(()=>Grouped.withGroupedRefits(native,original,{sidecar:c}),/differs/);
  const d=clone(original);
  d.upstream.selection_sha256='e'.repeat(64);
  assert.throws(()=>Grouped.withGroupedRefits(native,d),/source|selection|contract/);
});
test('grouped child records cannot be invented from W1 summary-only outputs',async()=>{
  const f=makeFixture();
  const no=await W1.run(f.frame,[SETTINGS[0]],{
    group_units:['meeting'],replicates:3,group_seed:31});
  const v1=W1V1.toInterchangeV1(no);
  assert.throws(()=>Grouped.withGroupedRefits(no,v1),/opt-in W1 synthetic/);
});
test('W1 group subsampling of several source groups is never mislabeled bootstrap',async()=>{
  const f=makeFixture();
  // Extend with four invented meetings, preserving W1 original text/hash/speaker contracts.
  for(let meeting=6;meeting<10;meeting++)for(let actor=0;actor<4;actor++){
    const base=f.frame.observations[meeting%6*4+actor];
    const row=clone(base);
    row.id='synthetic-extra-'+meeting+'-'+actor;
    row.text=base.text+' invented second sample '+meeting;
    row.text_sha256=F.digest(row.text);
    row.parent_id='fictional-extra-parent-'+meeting+'-'+actor;
    row.parent_text_sha256=F.digest(row.parent_id);
    row.meeting_id='fictional-meeting-'+meeting;
    row.source_family_id='fictional-family-extra-'+meeting+'-'+actor;
    row.date='2026-02-'+String(meeting+1).padStart(2,'0');
    f.frame.observations.push(row);
  }
  f.frame.inventory_meetings=11;
  f.frame.source_sha256=F.digest('extended-fictional-source-frame-v1');
  const out=await W1.run(f.frame,[SETTINGS[0],SETTINGS[2]],{
    group_units:['meeting'],replicates:16,fraction:0.7,group_seed:47,
    retain_group_assignments:true});
  const e=W1V1.toInterchangeV1(out);
  const g=Source.fromNative(out,e);
  assert.equal(g.cohort.source_group_count,10);
  assert(g.refits.every(x=>x.resample_type==='group_subsample'&&x.omitted_groups.length===3));
  const result=Grouped.withGroupedRefits(out,e,{sidecar:g});
  assert.equal(result.audit.original_models,2);
  assert.equal(result.audit.child_models,32);
  assert.equal(result.audit.distinct_group_samples.leave_group_out,0);
  assert(result.audit.distinct_group_samples.group_subsample>=5);
  assert(result.consensus.uncertainty.pairwise.some(row=>row.group_subsample.status==='descriptive'));
  assert(result.consensus.uncertainty.pairwise.every(row=>row.leave_group_out.status==='withheld'));
  assert(result.consensus.uncertainty.pairwise.every(row=>row.group_bootstrap.status==='withheld'));
});
test('failure/skip child model stays in the planned denominator and has no fabricated assignments',()=>{
  const c=clone(merged.refits);
  const id=c.models[0].model_id;
  for(const r of c.results.filter(x=>x.model_id===id&&x.status!=='excluded')){
    r.status='not_fitted';r.cluster=null;r.reason='Synthetic forced unavailable refit';
  }
  const coverage=c.coverage.models.find(x=>x.model_id===id);
  coverage.assigned=0;coverage.unassigned=0;coverage.not_fitted=coverage.eligible;
  coverage.successful_fits=0;coverage.failed_fits=1;
  c.coverage.failure_ledger.push({model_id:id,attempt:1,status:'failed',
    reason:'Synthetic forced unavailable refit',seed:777,source_group:'meeting'});
  assert.equal(W2.validateEnvelope(c).eligible.size,24);
  const sample=merged.refits.results.filter(x=>x.model_id===id&&x.status==='assigned').length;
  assert(sample>0);
  const w=W2.runConsensus([merged.baseline,c],{
    fit_plan:{...Bridge.recordAudit(native,original).fit_plan,
      ...Object.fromEntries(sidecar.refits.map(x=>[x.model_id,{
        configuration_id:Bridge.configIdentity(native.fit_records.find(f=>f.model_id===x.base_model_id)),
        seed:x.seed,resample_type:x.resample_type,resample_id:x.resample_id,sampled_groups:x.selected_groups
      }]))},
    cross_basis_protocol:'identity_join_hard_partition_v1'
  });
  const p=w.pairs.find(x=>x.observation_a==='synthetic-01'&&x.observation_b==='synthetic-02');
  assert.equal(p.planned_count,95);
  assert(p.missing_pair_count>0);
  assert(p.assigned_both_count<p.planned_count);
});
