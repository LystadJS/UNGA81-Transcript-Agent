'use strict';
/* Coordinator-only extended renderer must preserve the accepted W6 contract.
 * No script loads private records or requests external resources.
 */
const test=require('node:test');
const assert=require('node:assert/strict');
const V=require('./evidence_renderer.cjs');
const Accepted=require('../../../site/experimental/evidence-viz/evidence-viz.js');
const Fixtures=require('../../../site/experimental/evidence-viz/fixture.js');
const copy=x=>structuredClone(x);

test('all four original W6 views remain available and legacy renderer stays unchanged',()=>{
  const f=Fixtures.fixture();
  for(const p of f.panels){
    const v=V.renderPanel(f.envelope,p);
    const original=Accepted.renderPanel(f.envelope,p);
    assert.equal(v.kind,original.kind);
    assert.equal(v.status,original.status);
    assert.ok(v.svg.startsWith('<svg'));
    assert.match(v.html,/Observation identity and source ledger/);
    assert.match(V.htmlDocument(v),/Static export/);
  }
});
test('standalone coordinator renderer accepts W6 original empty/failed/withheld states',()=>{
  for(const k of V.TYPES)for(const state of ['empty','failed','withheld']){
    const f=Fixtures.scenario(k,state);
    const result=V.renderPanel(f.envelope,f.panels[0]);
    assert.equal(result.status,state);
    assert.match(result.html,/ev-withheld/);
    assert.doesNotMatch(result.html,/data-ev-inspect=/);
  }
});
test('coordinator preview cannot masquerade real input as a synthetic source',()=>{
  for(const modify of [
    e=>{e.observations[0].source_url='https://docs.un.org/original';},
    e=>{e.observations[0].text='nonfictional source';},
    e=>{e.evidence[0].source_url='https://docs.un.org/record';},
    e=>{e.upstream.source_hash_basis='raw_response_bytes';},
  ]){
    const f=Fixtures.fixture(),e=copy(f.envelope);
    modify(e);
    assert.throws(()=>V.renderPanel(e,f.panels[0]),
      /synthetic|nonfictional source URL|contains text|Source identity mismatch/i);
  }
});
test('W2 numeric mode is not a fallback for the old equal-family demonstration',()=>{
  const f=Fixtures.fixture(),p=copy(f.panels[0]);
  assert.equal(p.pair_mode,undefined);
  assert.match(V.renderPanel(f.envelope,p).inspections['cons-0'].summary,
    /Equal-family average/);
  p.pair_mode='w2_weighted_conditional';
  assert.throws(()=>V.renderPanel(f.envelope,p),
    /method-family planned-weight audit/);
});
