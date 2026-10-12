'use strict';
/* Native W2 producer -> un.parallel-analysis.v1 -> coordinator browser read model.
 * Synthetic-only; no transcript data, model fitting, or held-out material. */
const assert=require('node:assert/strict');
const {fixtureNuisance}=require('../consensus/fixtures.cjs');
const {makeFixture,SETTINGS}=require('../validation_framework/examples/synthetic_fixture.cjs');
const {run}=require('../validation_framework/runner.cjs');
const {toInterchangeV1:sourceV1}=require('../validation_framework/interchange.cjs');
const {fromW1}=require('./w1_w2/bridge.cjs');
const {runConsensus,validateConsensus}=require('../consensus/consensus.cjs');
const B=require('../../site/research-consensus.js');
const C=require('../../site/parallel/w05-browser/experimental/method-lab/contracts.js');
const V=require('../../site/experimental/evidence-viz/evidence-viz.js');
const clone=value=>structuredClone(value);
// W1's original 25-observation frame (24 eligible, 1 unavailable) is the
// source-complete, unchanged input to the accepted W1→W2 coordinator bridge.
// The standalone W2 fixture counts six meetings in a different inventory grain
// and must not be rewritten just to appease a renderer.
let passed=0,env,report;
async function test(name,fn){
  await fn();
  passed++;
  console.log('PASS '+name);
}
async function rejected(name,change,pattern){
  await test(name,async()=>{
    const [e,r]=change(clone(env),clone(report));
    await assert.rejects(()=>B.validate(e,r),pattern);
  });
}
async function main(){
  const fixture=makeFixture();
  const native=await run(fixture.frame,SETTINGS,{
    saved:fixture.saved,group_units:['meeting'],replicates:3,group_seed:31
  });
  const original=sourceV1(native);
  const joined=fromW1(native,original);
  report=joined.consensus;env=joined.interchange;
  await test('native W2 sidecar schema, W1/W5/W6 interoperable source frame',async()=>{
    validateConsensus(report);
    C.validateParallel(env);V.validateEnvelope(env);
    const result=await B.validate(env,report);
    const s=B.sampleFreeSummary(result);
    assert.equal(s.eligible,report.observation_ids.length);
    assert.equal(s.pair_opportunities,s.eligible*(s.eligible-1)/2);
    assert.equal(result.pairs_total,s.eligible*(s.eligible+1)/2);
    assert.equal(s.groups,report.reproducible_groups.length);
    assert.equal(s.ungrouped,report.ungrouped_observations.length);
    assert.equal(s.heatmap_state,'available');
    assert.equal(s.family_count,report.family_weight_audit.length);
    assert.equal(env.publication_eligible,false);
  });
  await test('W2 original weighted associations retained, including source noise/failures',async()=>{
    const output=await B.validate(env,report);
    for(const p of report.pairs){
      const stored=output.pairMap.get([p.observation_a,p.observation_b].sort().join('\0'));
      assert.strictEqual(stored,p,'No transformed or recomputed association values.');
      assert.ok(p.assigned_both_count+p.noise_pair_count+p.missing_pair_count===p.planned_count);
    }
    assert.ok(report.family_weight_audit.some(f=>f.internal_attempts>0));
  });
  await test('nuisance-only control cannot invent reproducible groups',()=>{
    const nuisance=fixtureNuisance();
    const output=runConsensus(nuisance.envelopes,{fit_plan:nuisance.fit_plan});
    validateConsensus(output);
    assert.equal(output.reproducible_groups.length,0);
    assert.ok(output.source_restricted_groups.length>0);
  });
  await rejected('reject source hash-basis difference',(e,r)=>{
    r.source.source_hash_basis='raw_response_bytes';return [e,r];
  },/source_hash_basis/);
  await rejected('reject source hash mismatch',(e,r)=>{
    r.source.source_sha256='a'.repeat(64);return [e,r];
  },/source_sha256/);
  await rejected('reject selection policy mismatch',(e,r)=>{
    r.source.cohort.selection_policy='changed';return [e,r];
  },/selection_policy/);
  await rejected('reject source-row hash tampering',(e,r)=>{
    r.source.observation_keys[0].text_sha256='b'.repeat(64);return [e,r];
  },/source-offset lineage/);
  await rejected('reject source metadata changes',(e,r)=>{
    r.source.observation_keys[0].meeting_id='fictional-other-meeting';return [e,r];
  },/lineage/);
  await rejected('reject v1 assignment mismatch',(e,r)=>{
    const row=e.results.find(x=>x.status==='assigned');
    assert.ok(row);
    row.cluster+=99;return [e,r];
  },/group assignment/);
  await rejected('reject parameter-hash mismatch',(e,r)=>{
    r.thresholds.min_association=.99;return [e,r];
  },/parameter SHA-256/);
  await rejected('reject missing pair',(e,r)=>{
    r.pairs.pop();return [e,r];
  },/pair frame/);
  await rejected('reject duplicate pair',(e,r)=>{
    r.pairs[1]=clone(r.pairs[0]);return [e,r];
  },/Duplicated W2 pair/);
  await rejected('reject false conditional association',(e,r)=>{
    const pair=r.pairs.find(x=>x.association!==null&&x.observation_a!==x.observation_b);
    assert.ok(pair);pair.association=pair.association===0?1:0;return [e,r];
  },/weighted association/);
  await rejected('reject false raw opportunity',(e,r)=>{
    r.pairs[0].missing_pair_count++;return [e,r];
  },/counts do not reconcile/);
  await rejected('reject matrix/row disagreement',(e,r)=>{
    r.matrix.association[0][1]=r.matrix.association[0][1]===null?0:null;return [e,r];
  },/matrix differs/);
  await rejected('reject family planned-weight tampering',(e,r)=>{
    r.family_weight_audit[0].total_weight+=.1;return [e,r];
  },/weights do not sum/);
  await rejected('reject false report split',(e,r)=>{
    e.cohort.split='development';return [e,r];
  },/provenance|synthetic/);
  await rejected('reject fabricated source text',(e,r)=>{
    e.observations[0].text='invented test string';return [e,r];
  },/text-bearing observations/);
  await rejected('reject unsupported W2 sidecar version',(e,r)=>{
    r.version='1.0.0';return [e,r];
  },/sidecar schema/);
  await test('withhold W2 heatmap above 35 IDs without sampling',async()=>{
    const result=await B.validate(env,report);
    result.ids=Array.from({length:40},(_,i)=>'synthetic-'+i);
    const s=B.sampleFreeSummary(result);
    assert.equal(s.heatmap_state,'withheld_above_35_full_ledger_retained');
    assert.equal(s.eligible,40);
  });
  console.log('PASS W2 browser adapter: '+passed+' synthetic-only tests; no model refitting or publication.');
}
main().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
