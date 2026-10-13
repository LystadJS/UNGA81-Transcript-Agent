'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {fixtureKnown,fixtureNuisance}=require('../../consensus/fixtures.cjs');
const {runConsensus,toInterchangeV1}=require('../../consensus/consensus.cjs');
const B=require('./w2_bridge.cjs');
const V=require('./evidence_renderer.cjs');

function ready(){
  const f=fixtureKnown(true);
  const report=runConsensus(f.envelopes,{fit_plan:f.fit_plan,min_coverage:.2});
  const envelope=toInterchangeV1(f.envelopes[0],report,{
    generated_at:'2026-10-12T00:00:00Z'
  });
  return {report,envelope};
}
const copy=x=>structuredClone(x);

test('Native W2 weighted pair reaches W6 without recomputing method balance',()=>{
  const {report,envelope}=ready();
  const p=B.toW6Consensus(report,envelope),view=V.renderPanel(envelope,p);
  assert.equal(p.pair_mode,'w2_weighted_conditional');
  assert.equal(p.observation_ids.length,12);
  assert.equal(p.coverage.frame,6); // six meeting inventory groups; 12 observations
  assert.equal(p.coverage.eligible,12);
  assert.match(view.html,/Inventory 6 meetings · eligible 12 synthetic observations/);
  assert.match(view.html,/preplanned|allocated|preserved exactly/i);
  assert.ok(view.svg.includes('W2 WEIGHTED'));
  assert.match(view.html,/Method-family planned-weight audit/);
  assert.match(view.html,/Planned weight/);
  assert.match(view.html,/Internal failed attempts/);
  for(const a of p.pairs){
    const original=report.pairs.find(r=>r.observation_a===a.a&&r.observation_b===a.b);
    assert.ok(original);
    assert.equal(a.association,original.association);
    assert.equal(a.assigned_both_weight,original.assigned_both_weight);
    assert.equal(a.planned_weight,original.planned_weight);
    assert.equal(a.failed_fit_count,original.failed_fit_count);
  }
  assert.equal(report.pairs.length,12*13/2);
  assert.equal(p.pairs.length,12*11/2);
  assert.equal(envelope.observations.length,12);
  assert.equal(p.family_weight_audit.length,report.family_weight_audit.length);
  assert.ok(view.html.includes('Source')||view.html.includes('source'));
});

test('W2 exposed planned-fit failures, missingness and ambiguity remain descriptive',()=>{
  const {report,envelope}=ready();
  const p=B.toW6Consensus(report,envelope);
  assert.ok(p.pairs.some(q=>q.failed_fit_count>0));
  assert.ok(p.pairs.some(q=>q.noise_pair_count>0));
  assert.ok(p.warnings.some(w=>w.includes('NOT confidence')));
  assert.ok(p.warnings.some(w=>w.includes('withheld')));
  const v=V.renderPanel(envelope,p);
  assert.ok(Object.values(v.inspections).some(x=>x.summary.includes('failed fits')));
  assert.match(v.html,/assignment|source group/i);
  assert.doesNotMatch(v.html,/<script/i);
  assert.match(V.htmlDocument(v),/Static export/);
});

test('W2 report identity, envelope original SHA and producer are checked',()=>{
  const source=ready();
  const altered=copy(source.report);
  altered.source.observation_keys[0].text_sha256='f'.repeat(64);
  assert.throws(()=>B.toW6Consensus(altered,source.envelope),/source|sidecar|mismatch/i);
  const envelope=copy(source.envelope);
  envelope.upstream.selection_sha256='e'.repeat(64);
  assert.throws(()=>B.toW6Consensus(source.report,envelope),/provenance|source|selection/i);
  const privateCopy=copy(source.envelope);
  privateCopy.producer.fixture_kind='private_development';
  assert.throws(()=>B.toW6Consensus(source.report,privateCopy.envelope||privateCopy),/synthetic/i);
  const nonFictional=copy(source.envelope);
  nonFictional.observations[0].source_url='https://example.org/real';
  assert.throws(()=>B.toW6Consensus(source.report,nonFictional),/source|URL|fictional/i);
});

test('W2 tampered pair ratio and incorrect noise/planned counts are rejected',()=>{
  const source=ready();
  const broken=copy(source.report);
  const item=broken.pairs.find(p=>p.observation_a!==p.observation_b&&p.association!==null);
  item.association=.12345678;
  assert.throws(()=>B.toW6Consensus(broken,source.envelope),/association|coassignment|weighted|consensus/i);
  const panel=B.toW6Consensus(source.report,source.envelope);
  const bad=copy(panel);
  bad.pairs[0].planned_count++;
  assert.throws(()=>V.renderPanel(source.envelope,bad),/planned pair accounting/i);
  const bad2=copy(panel);
  bad2.pairs[0].assigned_both_weight=1.5;
  assert.throws(()=>V.renderPanel(source.envelope,bad2),/weights|association|coverage/i);
});

test('W2 planned family weights fail closed on missing, duplicate or inflated audit',()=>{
  const source=ready(),panel=B.toW6Consensus(source.report,source.envelope);
  const missing=copy(panel);delete missing.family_weight_audit;
  assert.throws(()=>V.renderPanel(source.envelope,missing),/planned-weight audit/);
  const duplicate=copy(panel);
  duplicate.family_weight_audit[1].family=duplicate.family_weight_audit[0].family;
  assert.throws(()=>V.renderPanel(source.envelope,duplicate),/planned-weight audit/);
  const inflated=copy(panel);
  inflated.family_weight_audit[0].planned_weight=.99;
  assert.throws(()=>V.renderPanel(source.envelope,inflated),/planned-weight audit/);
});

test('W2 nuisance-only control does not turn source clusters into findings',()=>{
  const f=fixtureNuisance();
  const n=runConsensus(f.envelopes,{fit_plan:f.fit_plan});
  assert.equal(n.publication_eligible,false);
  assert.equal(n.reproducible_groups.length,0);
  assert.ok(n.source_restricted_groups.length>=1);
});

test('Original W6 illustrative equal-family mode remains unchanged',()=>{
  const F=require('../../../site/experimental/evidence-viz/fixture.js');
  const fixture=F.fixture(),p=fixture.panels[0],v=V.renderPanel(fixture.envelope,p);
  assert.equal(p.pair_mode,undefined);
  assert.match(v.inspections['cons-0'].summary,/Equal-family average/);
  assert.equal(v.inspections['cons-0'].summary.includes('4/5'),true);
});
