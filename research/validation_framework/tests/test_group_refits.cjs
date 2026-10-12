'use strict';
/* Synthetic W1 child-fit provenance, source-group omission and privacy controls. */
const test=require('node:test');
const assert=require('node:assert/strict');
const W1=require('../runner.cjs');
const V1=require('../interchange.cjs');
const GROUP=require('../group_refit_interchange.cjs');
const F=require('../frame.cjs');
const {makeFixture,SETTINGS}=require('../examples/synthetic_fixture.cjs');

const clone=x=>structuredClone(x);
let native,envelope,group;
test.before(async()=>{
  const fixture=makeFixture();
  native=await W1.run(fixture.frame,SETTINGS,{
    saved:fixture.saved,group_units:['meeting'],replicates:7,
    group_seed:31,retain_group_assignments:true});
  envelope=V1.toInterchangeV1(native);
  group=GROUP.fromNative(native,envelope);
});
test('opt-in retains real W1 child labels without changing native public JSON',()=>{
  assert(Array.isArray(native._internal_group_refits));
  assert.equal(native._internal_group_refits.length,35);
  assert.equal(Object.hasOwn(native,'_internal_group_refits'),true);
  assert.equal(Object.keys(native).includes('_internal_group_refits'),false);
  assert(!JSON.stringify(native).includes('observation_text_sha256'));
  assert.equal(group.schema,'un.source-aware.group-refits.v1');
  assert.equal(group.publication_eligible,false);
  assert.equal(GROUP.validateSidecar(group,envelope),true);
  assert.equal(group.producer.code_sha256,envelope.producer.code_sha256);
  assert.equal(group.cohort.eligible,24);
  assert.equal(group.cohort.inventory_meetings,7);
  assert.equal(group.cohort.grouping_components,6);
});
test('exact W1 group-level raw source IDs, hashes, fitted labels, counts and attempts survive',()=>{
  assert.equal(group.models.length,5);
  assert.equal(group.refits.length,35);
  for(const child of group.refits){
    const sample=native.model_reports.find(m=>m.model_id===child.base_model_id)
      .group_stability.meeting.runs.find(x=>x.attempt===child.attempt);
    assert.equal(child.seed,sample.seed);
    assert.equal(child.attempted_fits,sample.attempted_fit);
    assert.equal(child.successful_fits,sample.successful_fit);
    assert.equal(child.failed_fits,sample.failed_fit);
    assert.equal(child.status,sample.status);
    assert.equal(child.selected_rows.length,sample.observation_ids.length);
    assert.deepEqual(child.selected_rows.map(x=>x.observation_id),sample.observation_ids);
    assert(child.selected_rows.every(x=>/^[a-f0-9]{64}$/.test(x.text_sha256)));
    assert(child.selected_rows.every(x=>x.status==='assigned'||x.status==='unassigned'));
    assert.equal(child.refit_parameters_sha256.length,64);
    assert.equal(child.fit_replay_key_sha256.length,64);
    assert.equal(child.resample_type,'leave_group_out');
    assert.equal(child.omitted_groups.length,1);
  }
});
test('duplicate without-replacement samples share group design but use their original attempt/seed identities',()=>{
  const grouped=new Map();
  for(const x of group.refits){
    const a=grouped.get(x.resample_id)||[];
    a.push(x);
    grouped.set(x.resample_id,a);
  }
  assert(grouped.size<=6);
  assert(grouped.size>=2);
  assert([...grouped.values()].some(x=>x.length>5));
  for(const list of grouped.values())assert(list.every(x=>
    JSON.stringify(x.selected_groups)===JSON.stringify(list[0].selected_groups)));
});
test('sidecar contains no original synthetic source texts or vectors and has all frame provenance',()=>{
  const s=JSON.stringify(group);
  for(const phrase of ['Harbor ferry cargo docks','Forest canopy oak nature','Clinic nurse treatment vaccine'])
    assert(!s.includes(phrase));
  assert(!s.includes('"text":'));
  assert(!s.includes('"vector":'));
  assert(group.observations.every(o=>o.source_url===null&&
    !Object.hasOwn(o,'text')&&!Object.hasOwn(o,'affiliation')));
  assert.equal(group.upstream.source_sha256,envelope.upstream.source_sha256);
  assert.equal(group.upstream.selection_sha256,envelope.upstream.selection_sha256);
});
test('refuses attempts to derive hard-label records from W1 summary-only runs',async()=>{
  const fixture=makeFixture();
  const no=await W1.run(fixture.frame,[SETTINGS[0]],{
    replicates:2,group_units:['meeting'],group_seed:31});
  const original=V1.toInterchangeV1(no);
  assert.equal(Object.hasOwn(no,'_internal_group_refits'),false);
  assert.throws(()=>GROUP.fromNative(no,original),/retain_group_assignments/);
});
test('rejects corrupt text hashes, omitted groups, mislabeled noise, unknown fields and producer code',()=>{
  const bad=clone(group);
  bad.refits[0].selected_rows[0].text_sha256='a'.repeat(64);
  assert.throws(()=>GROUP.validateSidecar(bad,envelope),/wrong text SHA|child assignment/);
  const b=clone(group);
  b.refits[0].selected_groups.push(b.refits[0].omitted_groups[0]);
  assert.throws(()=>GROUP.validateSidecar(b,envelope),/selected\/omitted/);
  const c=clone(group);
  c.refits[0].selected_rows[0].status='unassigned';
  c.refits[0].selected_rows[0].cluster=2;
  assert.throws(()=>GROUP.validateSidecar(c,envelope),/child assignment row/);
  const d=clone(group);
  d.refits[0].selected_rows[0].source_text='unauthorized';
  assert.throws(()=>GROUP.validateSidecar(d,envelope),/unknown field/);
  const e=clone(envelope);
  e.producer.code_sha256='c'.repeat(64);
  assert.throws(()=>GROUP.fromNative(native,e),/actual fitted W1 runner SHA differs/);
});
test('rejects wrong source hash, scheme, reserved dates, duplicate child IDs and bootstrap masquerading',()=>{
  const bad=clone(group);
  bad.upstream.selection_sha256='d'.repeat(64);
  assert.throws(()=>GROUP.validateSidecar(bad,envelope),/source identity/);
  const d=clone(group);
  d.observations[0].date='2026-10-05';
  assert.throws(()=>GROUP.validateSidecar(d,envelope),/source identity|reserved source dates/);
  const b=clone(group);
  b.refits[1].model_id=b.refits[0].model_id;
  assert.throws(()=>GROUP.validateSidecar(b,envelope),/duplicate child-fit/);
  const c=clone(group);
  c.refits[0].resample_type='group_bootstrap';
  assert.throws(()=>GROUP.validateSidecar(c,envelope),/unsupported enum|sample design/);
});
test('W1 explicitly withholds source-group uncertainty when fewer than three meeting groups exist',async()=>{
  const fx=makeFixture();
  const selected=fx.frame.observations.filter(o=>
    ['fictional-meeting-0','fictional-meeting-1'].includes(o.meeting_id));
  fx.frame.observations=selected;
  fx.frame.inventory_meetings=2;
  const out=await W1.run(fx.frame,[SETTINGS[0]],{
    group_units:['meeting'],replicates:3,group_seed:31,retain_group_assignments:true});
  const e=V1.toInterchangeV1(out);
  const g=GROUP.fromNative(out,e);
  assert.equal(g.cohort.source_group_count,2);
  assert.equal(g.schedules[0].status,'skipped');
  assert.equal(g.refits.length,0);
  assert.equal(g.schedules[0].planned,0);
});
test('seeded independent restart reproduces the same source-bound W1 child assignments',async()=>{
  const f=makeFixture();
  const a=await W1.run(f.frame,[SETTINGS[0]],{
    group_units:['meeting'],replicates:5,group_seed:31,retain_group_assignments:true});
  const b=await W1.run(f.frame,[SETTINGS[0]],{
    group_units:['meeting'],replicates:5,group_seed:31,retain_group_assignments:true});
  const x=GROUP.fromNative(a,V1.toInterchangeV1(a)),y=GROUP.fromNative(b,V1.toInterchangeV1(b));
  assert.deepEqual(x,y);
});
