'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const W1Run=require('../../validation_framework/runner.cjs');
const W1Export=require('../../validation_framework/interchange.cjs');
const {makeFixture,SETTINGS}=require('../../validation_framework/examples/synthetic_fixture.cjs');
const W2=require('../../consensus/consensus.cjs');
const W2Fixture=require('../../consensus/fixtures.cjs');
const Bridge=require('./bridge.cjs');
const W6Panel=require('./w6_panel.cjs');
const W5=require('../../../site/parallel/w05-browser/experimental/method-lab/contracts.js');
const W5Archive=require('../../../site/parallel/w05-browser/experimental/method-lab/adapters.js');
const W6=require('../../../site/experimental/evidence-viz/evidence-viz.js');
const clone=x=>structuredClone(x);
let native,w1,joined,panel;
test.before(async()=>{
  const fixture=makeFixture();
  native=await W1Run.run(fixture.frame,SETTINGS,{
    saved:fixture.saved,group_units:['meeting'],replicates:3,group_seed:31});
  w1=W1Export.toInterchangeV1(native);
  joined=Bridge.fromW1(native,w1);
  panel=W6Panel.panelForW6(joined);
});
test('actual merged W1 synthetic runner returns complete versioned source and model records',()=>{
  assert.equal(native.schema,'un.source-aware-validation.v1');
  assert.equal(w1.producer.workstream_id,'W1');
  assert.equal(native.fit_records.length,5);
  assert.equal(native.frame.eligible,24);
  assert.equal(native.frame.excluded,1);
  assert.equal(w1.observations.length,25);
  assert.equal(w1.models.length,5);
  assert.equal(w1.results.length,125);
  assert.equal(W1Export.validateRelational(w1),true);
});
test('bridge keeps W1 originals unmodified while deriving four balanced method families',()=>{
  assert(w1.models.every(m=>m.method_family==='unsupervised_partition'));
  assert.equal(joined.projected_envelope.producer.workstream_id,'W2');
  assert.deepEqual(joined.projected_envelope.observations,w1.observations);
  assert.deepEqual(joined.projected_envelope.results,w1.results);
  assert.deepEqual(joined.projected_envelope.coverage,w1.coverage);
  assert.deepEqual(joined.projected_envelope.upstream,w1.upstream);
  assert.deepEqual(joined.projected_envelope.cohort,w1.cohort);
  assert.deepEqual(joined.audit.models.map(x=>x.derived_family).sort(),
    ['density','hierarchical','mixture','partition','partition']);
  assert.deepEqual(joined.consensus.family_weight_audit.map(x=>x.total_weight),
    [0.25,0.25,0.25,0.25]);
  assert.equal(W2.validateConsensus(joined.consensus),true);
  assert.equal(joined.consensus.pairs.length,300);
  assert.equal(joined.consensus.observation_ids.length,24);
  assert.equal(joined.consensus.source.representation_versions.length,3);
  assert.equal(joined.audit.original_w1_code_sha256,w1.producer.code_sha256);
  assert.equal(joined.interchange.producer.workstream_id,'W2');
});
test('W1 grouped resample summaries never manufacture W2 bootstrap or leave-one-out pairs',()=>{
  assert(native.model_reports.every(m=>Object.values(m.group_stability).every(g=>g.runs.length===3)));
  assert.equal(joined.audit.grouped_refit_pairwise_status,'withheld');
  assert.match(joined.audit.grouped_refit_pairwise_reason,/no per-refit hard-assignment arrays/);
  assert.equal(joined.consensus.uncertainty.design,'not_estimated');
  assert.deepEqual(joined.consensus.uncertainty.pairwise,[]);
  assert(joined.interchange.diagnostics.some(d=>d.status==='withheld'));
  assert(!Object.hasOwn(joined.consensus,'p_value'));
});
test('W2 pair audit has planned, assigned-both and co-assigned denominators on real W1 labels',()=>{
  for(const p of joined.consensus.pairs){
    assert.equal(p.planned_count,5);
    assert(p.assigned_both_count<=p.planned_count);
    assert(p.coassigned_count<=p.assigned_both_count);
    assert(p.coassigned_weight<=p.assigned_both_weight);
    assert.equal(p.association===null,p.assigned_both_count===0);
  }
  const models=joined.audit.models;
  assert.equal(models.filter(x=>x.method==='kmeans').length,1);
  assert.equal(models.filter(x=>x.method==='hierarchical').length,1);
});
test('W5 accepts original W1 and W2 results without a refit or invented political interpretation',()=>{
  const old=W5.fromParallel(w1),now=W5.fromParallel(joined.interchange);
  assert.equal(old.models.length,5);
  assert.equal(now.models.length,1);
  assert.equal(now.models[0].method,'descriptive_complete_link_consensus');
  assert.equal(now.observations.length,25);
  assert.equal(now.models[0].rows.length,25);
  assert.equal(now.models[0].coverage.excluded,1);
  assert.equal(now.source.hash,w1.upstream.source_sha256);
  assert.equal(W5.compare(now,now,now.models[0].id,now.models[0].id).identical_population,true);
  assert.equal(now.models[0].execution,'offline_only');
});
test('W5 checksum archive/replay of W1 and W2 derived fit outputs is byte-identical',async()=>{
  const packed=await W5Archive.packParallel([w1,joined.interchange]);
  const restored=await W5Archive.restoreParallel(packed);
  assert.deepEqual(restored,[w1,joined.interchange]);
  const tampered=JSON.parse(packed);
  tampered.payload_json=tampered.payload_json.replace('fictional','modified');
  await assert.rejects(()=>W5Archive.restoreParallel(JSON.stringify(tampered)),/checksum/i);
});
test('W6 renders genuine W1-derived pair calculations only after rate equivalence proof',()=>{
  assert.equal(W6.validateEnvelope(joined.interchange).size,25);
  assert.equal(panel.status,'ready');
  assert.equal(panel.panel.status,'ready');
  assert.equal(panel.panel.coverage.frame,25);
  assert.equal(panel.panel.coverage.eligible,24);
  assert.equal(panel.panel.coverage.excluded,1);
  assert.equal(panel.panel.coverage.missing,1);
  assert.equal(panel.panel.observation_ids.length,24);
  assert.equal(panel.panel.pairs.length,276);
  assert.equal(panel.comparability.compared_pairs,276);
  assert(panel.comparability.max_absolute_fraction_difference<1e-9);
  const rendered=W6.renderPanel(joined.interchange,panel.panel);
  assert.equal(rendered.status,'ready');
  assert.match(rendered.html,/Synthetic engineering demonstration/);
  assert.match(rendered.html,/Frame 25/);
  assert.match(rendered.svg,/<svg/);
  assert.match(rendered.html,/not agreement|not.*coalition/i);
});
test('derived public objects contain only W1 metadata; synthetic source text stays in W1 memory',()=>{
  const serialized=JSON.stringify(joined)+JSON.stringify(panel);
  assert(!serialized.includes('Harbor ferry cargo'));
  assert(!serialized.includes('Clinic nurse treatment'));
  assert(!serialized.includes('Forest canopy oak'));
  assert(!serialized.includes('"text":'));
  assert.equal(joined.audit.publication_eligible,false);
  assert.equal(joined.audit.no_holdout_access,true);
});
test('reject a mutated W1 upstream producer numerical revision',()=>{
  const x=clone(w1);x.producer.code_sha256='0'.repeat(64);
  assert.throws(()=>Bridge.fromW1(native,x),/numerical runner differs/);
});
test('reject source-text-hash and source-selection mutation',()=>{
  const x=clone(w1);x.observations[0].text_sha256='f'.repeat(64);
  assert.throws(()=>Bridge.fromW1(native,x),/population.*source identity drift|observation/i);
  const y=clone(w1);y.upstream.selection_sha256='b'.repeat(64);
  assert.throws(()=>Bridge.fromW1(native,y),/source cohort differ|model training selection mismatch/);
});
test('reject upstream W1 family ambiguity and mismatched model parameters',()=>{
  const x=clone(w1);x.models[0].method_family='partition';
  assert.throws(()=>Bridge.fromW1(native,x),/mapping contract changed/);
  const y=clone(w1);y.models[0].parameters_sha256='c'.repeat(64);
  assert.throws(()=>Bridge.fromW1(native,y),/unverified native parameters/);
});
test('reject native W1 label tampering and a fake re-fit assignment',()=>{
  const x=clone(native);x.fit_records[0].assignments[0]=x.fit_records[0].assignments[0]===1?2:1;
  assert.throws(()=>Bridge.fromW1(x,w1),/assignment differs/);
  const y=clone(native);y.model_reports[0].group_stability.meeting.runs[0].assignments=[1,2];
  assert.throws(()=>Bridge.fromW1(y,w1),/record layout changed/);
});
test('seed-normalized configuration ID is stable across independent seeds',()=>{
  const a=clone(native.fit_records[0]),b=clone(a);
  b.seed=999;b.parameters.seed=999;
  b.model_id='renamed-seed';b.parameters.id='renamed-seed';
  assert.equal(Bridge.configIdentity(a),Bridge.configIdentity(b));
});
test('reject unsupported source split before any W2 release or browser presentation',()=>{
  const x=clone(w1);x.cohort.split='development';x.producer.fixture_kind='private_development';
  assert.throws(()=>Bridge.fromW1(native,x),/synthetic/);
  assert.equal(joined.consensus.publication_eligible,false);
  assert.equal(joined.interchange.publication_eligible,false);
});

test('reject W1 invented fixture masquerading with incomplete inventory, original links or reserved dates',()=>{
  const bad=clone(w1);bad.cohort.total_in_frame=20;
  assert.throws(()=>Bridge.fromW1(native,bad),/full frame must be complete/);
  const link=clone(w1);link.observations[0].source_url='https://transcripts.un.org/fictional';
  assert.throws(()=>Bridge.fromW1(native,link),/no original links|full frame must be complete/);
  const date=clone(w1);date.observations[0].date='2026-10-05';
  assert.throws(()=>Bridge.fromW1(native,date),/reserved dates/);
});

test('W6 withholds mismatched raw family rates instead of displaying incorrect weighted consensus',()=>{
  const f=W2Fixture.fixtureKnown(false);
  for(const e of f.envelopes){
    e.observations.forEach(o=>o.source_url=null);
    e.cohort.total_in_frame=e.observations.length;
  }
  const first=f.envelopes[0].results.find(r=>r.observation_id==='fictional-unit-1-a');
  first.cluster=first.cluster===1?2:1;
  const out=W2.runConsensus(f.envelopes,{fit_plan:f.fit_plan});
  const e=W2.toInterchangeV1(f.envelopes[0],out,{generated_at:'2026-10-08T00:00:00Z'});
  const synthetic={projected_envelope:f.envelopes[0],consensus:out,interchange:e,
    audit:{schema:'un.w1-w2-consensus-bridge.v1',publication_eligible:false,source_split:'synthetic'}};
  // Put all original model records into a compatible multi-model projection.
  synthetic.projected_envelope=clone(f.envelopes[0]);
  synthetic.projected_envelope.models=f.envelopes.map(x=>x.models[0]);
  synthetic.projected_envelope.results=f.envelopes.flatMap(x=>x.results);
  synthetic.projected_envelope.coverage.models=f.envelopes.map(x=>x.coverage.models[0]);
  synthetic.projected_envelope.coverage.failure_ledger=f.envelopes.flatMap(x=>x.coverage.failure_ledger);
  W2.validateEnvelope(synthetic.projected_envelope);
  const view=W6Panel.panelForW6(synthetic);
  assert.equal(view.status,'withheld');
  assert.match(view.panel.reason,/not equivalent/);
  assert.equal(view.panel.coverage.included,0);
  assert.deepEqual(view.panel.observation_ids,[]);
  assert.equal(W6.renderPanel(e,view.panel).status,'withheld');
});
