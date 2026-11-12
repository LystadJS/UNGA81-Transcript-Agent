'use strict';
/* Execute only in a checkout with merged C5 source and its original synthetic
 * generator outputs. This script never regenerates or alters model results.
 * Required environment variables: C5_W2_FIXTURES, C5_W4_FIXTURES.
 */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const W2=require('../../research-consensus.js');
const W4=require('../../research-evidence.js');
const V=require('./renderer.js');
const Adapter=require('./adapter.js');
const W4_FILES=['SHA256.json','w4-source-panel.json','w4-analysis.json','w4-envelope.json','w4-panel.json'];
const base=process.env.C5_W2_FIXTURES;
const w4base=process.env.C5_W4_FIXTURES;
if(!base || !w4base)throw Error('Native C5 fixture directories required; set C5_W2_FIXTURES and C5_W4_FIXTURES. Do not substitute invented W2/W4 mock outputs.');
const read=(folder,name)=>JSON.parse(fs.readFileSync(path.join(folder,name),'utf8'));
const w4files=(dir,edit=()=>{})=>W4_FILES.map(name=>{
  let bytes=fs.readFileSync(path.join(dir,name));
  bytes=edit(name,bytes)||bytes;
  return {name,size:bytes.length,arrayBuffer:async()=>Uint8Array.from(bytes).buffer};
});
const key=(a,b)=>[a,b].sort().join('\u001f');

test('Merged native C5 W2 validator and v2 adapter preserve full weighted pair/source frame',async()=>{
  const env=read(base,'w2-v1-interchange.json'),side=read(base,'w2-consensus.json');
  const verified=await W2.validate(env,side);
  const view=await Adapter.fromW2(env,side,{validateW2:W2.validate});
  V.validate(view);
  const p=view.panels.find(x=>x.kind==='consensus');
  assert.equal(view.sources.length,env.cohort.total_in_frame);
  assert.equal(view.sources.filter(x=>x.status==='available').length,env.cohort.eligible);
  assert.equal(p.coverage.missing,env.coverage.unavailable_sources);
  assert.equal(p.coverage.excluded,env.coverage.excluded);
  assert.equal(p.pair_population_ids.length,verified.ids.length);
  assert.equal(p.rows.length,verified.eligible_off_diagonal);
  assert.equal(side.pairs.length,verified.ids.length*(verified.ids.length+1)/2);
  const old=new Map(side.pairs.map(r=>[key(r.observation_a,r.observation_b),r]));
  for(const row of p.rows){
    const ref=old.get(key(row.a,row.b));
    assert.ok(ref,'Original unordered pair must be retained');
    for(const name of ['association','assignment_coverage','coassigned_weight','assigned_both_weight',
      'planned_weight','coassigned_count','assigned_both_count','planned_count',
      'missing_pair_count','noise_pair_count','failed_fit_count'])
      assert.equal(row[name],ref[name],`Native W2 read-model drift: ${row.a}/${row.b}: ${name}`);
    assert.deepEqual(row.contributing_families,ref.contributing_families);
  }
  assert.equal(p.family_weight_audit.reduce((sum,x)=>sum+x.planned_weight,0),1);
  assert.equal(view.publication_eligible,false);
});

test('Merged native C5 W4 five-file bytes, source period IDs and fitted outputs bind to v2 without refit',async()=>{
  const original=await W4.loadW4Files(w4files(w4base));
  const view=await Adapter.fromW4(w4files(w4base),{loadW4Files:W4.loadW4Files});
  V.validate(view);
  const native=original.panel,p=view.panels.find(x=>x.kind==='longitudinal');
  assert.equal(view.sources.length,original.envelope.observations.length);
  assert.equal(p.coverage.frame,original.envelope.cohort.total_in_frame);
  assert.equal(p.coverage.eligible,original.envelope.cohort.eligible);
  assert.equal(p.coverage.missing,original.envelope.coverage.unavailable_sources);
  assert.deepEqual(p.periods,native.periods);
  const periods=new Map(original.source.observations.map(o=>[o.id,o.period]));
  assert.ok(view.sources.every(o=>o.period===periods.get(o.id)));
  const origRows=new Map(native.actors.flatMap(a=>a.positions.map(q=>[a.id+'\u001f'+q.period,q])));
  for(const r of p.rows){
    const old=origRows.get(r.actor+'\u001f'+r.period);
    assert.ok(old);
    assert.deepEqual(r.xy,old.xy);
    assert.deepEqual(r.source_ids,old.observation_ids);
    assert.equal(r.n,old.n);
  }
  assert.equal(original.provenance.publication_eligible,false);
});

test('C5 native W2 source-selection tampering is refused before v2 projection',async()=>{
  const e=read(base,'w2-v1-interchange.json'),s=read(base,'w2-consensus.json');
  e.upstream.selection_sha256='f'.repeat(64);
  await assert.rejects(Adapter.fromW2(e,s,{validateW2:W2.validate}),/refused|mismatch|differs|source/i);
});

test('C5 native W4 original byte tampering is refused before v2 projection',async()=>{
  const files=w4files(w4base,(name,buf)=>name==='w4-analysis.json'?Buffer.concat([buf,Buffer.from(' ')]):buf);
  await assert.rejects(Adapter.fromW4(files,{loadW4Files:W4.loadW4Files}),/refused|mismatch|SHA256/i);
});
