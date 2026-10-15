'use strict';
/* Native C5 cross-contract refusal tests. Only generated synthetic inputs.
 * Run after generating original W1->W2 and W4 source bundles.
 */
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const C=require('../../site/research-consensus.js');
const Bridge=require('../../site/research-evidence.js');
const V=require('../integration/w2_w4_w6/evidence_renderer.cjs');
const Accepted=require('../../site/experimental/evidence-viz/evidence-viz.js');
const raw=x=>fs.readFileSync(x);
const clone=x=>structuredClone(x);
const w2dir=process.env.C5_W2_FIXTURES;
const w4dir=process.env.C5_W4_FIXTURES;
const pinned=process.env.C5_W4_PINNED;
const missing=process.env.C5_W4_MISSING;
const files=['SHA256.json','w4-source-panel.json','w4-analysis.json','w4-envelope.json','w4-panel.json'];
function input(dir,modified={}){
  return files.map(name=>{
    const buf=modified[name]||raw(path.join(dir,name));
    return {name,size:buf.length,arrayBuffer:async()=>Uint8Array.from(buf).buffer};
  });
}
function read(dir,name){return JSON.parse(raw(path.join(dir,name)).toString('utf8'));}
const requireInputs=()=>{assert(w2dir&&w4dir&&pinned&&missing,'C5 original producer directories required');};
test.before(requireInputs);

test('W2 native W1->W2 sidecar retains exact weighted pairs in staged W6',async()=>{
  const sidecar=read(w2dir,'w2-consensus.json');
  const env=read(w2dir,'w2-v1-interchange.json');
  const validated=await C.validate(env,sidecar);
  const p=Bridge.toW2Panel(validated),view=V.renderPanel(env,p);
  assert.equal(p.status,'ready');
  assert.equal(p.pair_mode,'w2_weighted_conditional');
  assert.equal(p.coverage.frame,25);
  assert.equal(p.coverage.eligible,24);
  assert.equal(p.coverage.excluded,1);
  assert.equal(p.coverage.missing,1);
  assert.equal(p.observation_ids.length,24);
  assert.equal(p.pairs.length,276);
  assert.match(view.html,/Method-family planned-weight audit/);
  assert.match(view.html,/Original|weighted|planned/i);
  assert.match(view.svg,/W2 WEIGHTED/);
  assert.match(V.htmlDocument(view),/Static export/);
  for(const rec of p.pairs){
    const o=sidecar.pairs.find(z=>z.observation_a===rec.a&&z.observation_b===rec.b);
    assert(o);
    assert.equal(rec.association,o.association);
    assert.equal(rec.coassigned_weight,o.coassigned_weight);
    assert.equal(rec.assigned_both_weight,o.assigned_both_weight);
    assert.equal(rec.planned_weight,o.planned_weight);
    assert.equal(rec.failed_fit_count,o.failed_fit_count);
  }
});

test('W2 method audit and original complete source-pair frame fail closed',async()=>{
  const env=read(w2dir,'w2-v1-interchange.json');
  const side=read(w2dir,'w2-consensus.json');
  const valid=await C.validate(env,side);
  const changed=Bridge.toW2Panel(valid);
  changed.family_weight_audit[0].planned_weight=.9;
  assert.throws(()=>V.renderPanel(env,changed),/planned-weight audit/);
  const wrong=clone(side);
  wrong.pairs.find(x=>x.observation_a!==x.observation_b).assigned_both_weight=.99;
  await assert.rejects(()=>C.validate(env,wrong),/pair|weighted|denominator|matrix|coassignment/i);
  const fake=clone(env);
  fake.observations[0].source_url='https://docs.un.org/original';
  await assert.rejects(()=>C.validate(fake,side),/source|real|URL/i);
  assert.notEqual(Accepted, V,'C5 renderer intentionally separate from original published W6.');
});

test('W4 original 5 files accepted with independent saved rigid-map replay',async()=>{
  const data=await Bridge.loadW4Files(input(w4dir));
  assert.equal(data.panel.status,'ready');
  assert.equal(data.panel.alignments[0].mode,'rigid_full_refit');
  assert.equal(data.provenance.publication_eligible,false);
  assert.equal(data.provenance.unavailable_rows,0);
  assert.ok(data.provenance.actors>=9);
  assert.equal(data.panel.coverage.frame,data.envelope.observations.length);
  const view=V.renderPanel(data.envelope,data.panel);
  assert.match(view.html,/source|Synthetic/i);
  assert.match(view.svg,/Aligned latent dimension/);
  assert.doesNotMatch(V.htmlDocument(view),/<script/i);
});

test('W4 pinned-reference mode preserves zero fitted anchors',async()=>{
  const data=await Bridge.loadW4Files(input(pinned));
  assert.equal(data.panel.status,'ready');
  assert.equal(data.panel.alignments[0].mode,'identity_pinned_transform');
  assert.equal(data.panel.alignments[0].anchors,0);
});

test('W4 missing source-family cannot be transformed into zero motion',async()=>{
  const data=await Bridge.loadW4Files(input(missing));
  assert.equal(data.provenance.unavailable_rows,11);
  assert.equal(data.provenance.unavailable_source_groups,1);
  assert.equal(data.panel.coverage.excluded,11);
  assert.equal(data.panel.coverage.missing,1);
  assert.equal(data.panel.status,'ready');
});

test('W4 missing or corrupted original file digest is rejected',async()=>{
  let arr=input(w4dir);
  arr=arr.filter(x=>x.name!=='w4-source-panel.json');
  await assert.rejects(()=>Bridge.loadW4Files(arr),/exactly|missing/i);
  const alter=raw(path.join(w4dir,'w4-source-panel.json')).toString().replace(
    '"synthetic"', '"development"');
  const altered={'w4-source-panel.json':Buffer.from(alter)};
  await assert.rejects(()=>Bridge.loadW4Files(input(w4dir,altered)),/SHA256 mismatch/);
});

test('W4 rehashed coordinated forgery cannot change alignment or source provenance',async()=>{
  const source=read(w4dir,'w4-source-panel.json'),analysis=read(w4dir,'w4-analysis.json'),
    env=read(w4dir,'w4-envelope.json'),p=read(w4dir,'w4-panel.json');
  const fresh=()=>({
    'w4-source-panel.json':clone(source),'w4-analysis.json':clone(analysis),
    'w4-envelope.json':clone(env),'w4-panel.json':clone(p)
  });
  let bundle=fresh();
  bundle['w4-analysis.json'].aligned_coordinates[0].coordinates[0]+=1;
  await assert.rejects(()=>Bridge.validateW4(bundle),/coordinate|alignment|source/i);
  bundle=fresh();
  bundle['w4-envelope.json'].results[0].status='excluded';
  await assert.rejects(()=>Bridge.validateW4(bundle),/row counts|result|fit|source/i);
  bundle=fresh();
  bundle['w4-source-panel.json'].observations[0].source_url='https://docs.un.org/original';
  await assert.rejects(()=>Bridge.validateW4(bundle),/source|fictional|synthetic/i);
  bundle=fresh();
  bundle['w4-panel.json'].actors[0].positions.find(x=>x.status==='observed').xy[0]+=1;
  await assert.rejects(()=>Bridge.validateW4(bundle),/actor score|weighted|source/i);
});

test('Original W6 synthetic demonstrator remains unmodified and source-safe',()=>{
  const Fixtures=require('../../site/experimental/evidence-viz/fixture.js').fixture();
  for(const p of Fixtures.panels){
    const legacy=Accepted.renderPanel(Fixtures.envelope,p),
      c5=V.renderPanel(Fixtures.envelope,p);
    assert.equal(legacy.kind,c5.kind);
    assert.equal(legacy.status,c5.status);
    assert.match(c5.svg,/^<svg/);
  }
});
