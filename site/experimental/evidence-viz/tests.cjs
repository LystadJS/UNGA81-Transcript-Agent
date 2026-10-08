'use strict';
/* Run: node --test site/experimental/evidence-viz/tests.cjs
   All records are synthetic; no network, source collection, or held-out access. */
const test=require('node:test');
const assert=require('node:assert/strict');
const V=require('./evidence-viz.js');
const F=require('./fixture.js');
const get=()=>F.fixture();
const clone=x=>structuredClone(x);
const panel=(f,k)=>f.panels.find(p=>p.kind===k);
const draw=(f,k)=>V.renderPanel(f.envelope,panel(f,k));

test('all four source-bound graphics render independent SVG and HTML',()=>{
  const f=get();
  assert.equal(f.envelope.schema,'un.parallel-analysis.v1');
  assert.equal(f.envelope.producer.fixture_kind,'synthetic');
  assert.equal(f.envelope.publication_eligible,false);
  for(const k of V.TYPES){
    const v=draw(f,k);
    assert.match(v.svg,/^<svg xmlns="http:\/\/www.w3.org\/2000\/svg"/);
    assert.match(v.svg,/<title>/);
    assert.match(v.svg,/<desc>/);
    assert.match(v.html,/data-ev-inspect=/);
    assert.match(v.html,/Observation identity and source ledger/);
    assert.match(v.html,/Synthetic engineering demonstration/);
    assert.match(V.htmlDocument(v),/Static export: evidence links/);
    assert.doesNotMatch(V.htmlDocument(v),/<script/i);
  }
});

test('consensus balances eligible method families and retains failed attempts',()=>{
  const v=draw(get(),'consensus');
  const entry=v.inspections['cons-0'];
  assert.match(entry.summary,/73%/); // (4/5 + 2/3)/2 = 73.3%, not 6/8 = 75%
  assert.match(entry.summary,/partition 4\/5 eligible, 1 failures/);
  assert.match(entry.summary,/density 2\/3 eligible, 2 failures/);
  assert.match(v.html,/No eligible pair exposures/);
  assert.match(v.html,/Missing pair record/);
  assert.match(v.html,/Diagonal not assessed/);
  assert.match(v.html,/unstable/);
});

test('country values separate real zero, withheld, and unassigned country',()=>{
  const v=draw(get(),'country-theme');
  assert.match(v.html,/0%/);
  assert.match(v.html,/Upstream component attribution deliberately withheld/);
  assert.match(v.html,/unresolved country attribution/);
  assert.match(v.svg,/Unattributed sources: 1/);
  assert.match(v.html,/not political position/);
});

test('network audits selected graph and distinguishes sensitivity from alliance',()=>{
  const v=draw(get(),'network');
  assert.match(v.html,/Connected component sizes: 4, 2, 1/);
  assert.match(v.html,/cosine_similarity ≥ 0.60/);
  assert.match(v.html,/not_assessed/);
  assert.match(v.html,/Edges do not establish alliance/);
  assert.match(v.svg,/stroke-dasharray="5 4"/);
});

test('failed cross-period alignment withholds even otherwise present 2027 points',()=>{
  const v=draw(get(),'longitudinal');
  assert.match(v.svg,/Actor A 25/);
  assert.match(v.svg,/Actor A 26/);
  assert.doesNotMatch(v.svg,/Actor A 27/);
  assert.doesNotMatch(v.svg,/Actor C 27/);
  assert.match(v.html,/2026 → 2027/);
  assert.match(v.html,/Withheld/);
  assert.match(v.html,/Unaligned-period coordinates are entirely withheld/);
});

test('all four empty states account for a genuinely empty population',()=>{
  for(const kind of V.TYPES){
    const f=F.scenario(kind,'empty');
    assert.equal(f.envelope.cohort.total_in_frame,0);
    assert.equal(f.envelope.cohort.eligible,0);
    const v=V.renderPanel(f.envelope,f.panels[0]);
    assert.equal(v.status,'empty');
    assert.match(v.html,/No eligible source observations/);
    assert.match(v.svg,/EMPTY:/);
  }
});

test('withheld and failed panels do not leak a chart',()=>{
  for(const kind of V.TYPES)for(const state of ['withheld','failed']){
    const f=F.scenario(kind,state),v=V.renderPanel(f.envelope,f.panels[0]);
    assert.equal(v.status,state);
    assert.match(v.html, /ev-withheld/);
    assert.doesNotMatch(v.html,/data-ev-inspect=/);
  }
});

test('source-hash mismatches and duplicate identities fail closed',()=>{
  const f=get();
  panel(f,'network').identity.observation_refs[0].text_sha256='f'.repeat(64);
  assert.throws(()=>draw(f,'network'),/hash mismatch/);
  const g=get();g.envelope.observations.push(clone(g.envelope.observations[0]));
  assert.throws(()=>draw(g,'network'),/Duplicate observation IDs/);
  const h=get();panel(h,'network').identity.selection_sha256='1'.repeat(64);
  assert.throws(()=>draw(h,'network'),/Source identity mismatch/);
});

test('unknown sources, graph errors and impossible denominators fail closed',()=>{
  const f=get();panel(f,'network').edges[0].observation_ids=['unknown'];
  assert.throws(()=>draw(f,'network'),/Unrecognized evidence observation ID/);
  const g=get();panel(g,'network').graph.threshold=.96;
  assert.throws(()=>draw(g,'network'),/below declared threshold/);
  const h=get();panel(h,'country-theme').cells[0].weighted_sum=8;
  assert.throws(()=>draw(h,'country-theme'),/Invalid prevalence numerator/);
  const i=get();panel(i,'consensus').pairs[0].families[0].together=10;
  assert.throws(()=>draw(i,'consensus'),/Invalid pair fit counts/);
  const j=get();panel(j,'longitudinal').alignments[0].status='passed-by-reviewer';
  assert.throws(()=>draw(j,'longitudinal'),/Alignment ledger incomplete/);
});

test('untrusted labels are escaped in interactive and static outputs',()=>{
  const f=get();
  panel(f,'network').nodes[0].label='<img src=x onerror=alert(1)>';
  const v=draw(f,'network');
  assert.doesNotMatch(v.html,/<img src=x/);
  assert.match(v.html,/&lt;img/);
  assert.doesNotMatch(V.htmlDocument(v),/<img src=x/);
  assert.match(v.svg,/&lt;img/);
});

test('cross-panel source, model and temporal identity contradictions fail closed',()=>{
  const a=get();panel(a,'country-theme').cells[0].observation_ids=['S04'];
  assert.throws(()=>draw(a,'country-theme'),/Country attribution mismatch/);
  const b=get();panel(b,'network').edges[0].observation_ids=['S01','S03'];
  assert.throws(()=>draw(b,'network'),/edge must link evidence from each endpoint/);
  const c=get();panel(c,'longitudinal').alignments[0].reference_basis='other-model';
  assert.throws(()=>draw(c,'longitudinal'),/Alignment ledger incomplete/);
  const d=get();panel(d,'longitudinal').actors[0].positions[0].observation_ids=['S02'];
  assert.throws(()=>draw(d,'longitudinal'),/Actor-period source date mismatch/);
  const e=get();e.envelope.coverage.eligible=9;
  assert.throws(()=>draw(e,'network'),/Frame\/eligibility accounting mismatch/);
  const f=get();panel(f,'network').identity.representation_version='arbitrary-version';
  assert.throws(()=>draw(f,'network'),/Unknown representation and version/);
});

test('no remote data or automatic political inference in prototype sources',()=>{
  const fs=require('node:fs');
  const src=fs.readFileSync(require('node:path').join(__dirname,'evidence-viz.js'),'utf8');
  assert.doesNotMatch(src,/\bfetch\s*\(|XMLHttpRequest|WebSocket|https:\/\/api\./);
  assert.match(src,/Similarity is not an alliance/);
  assert.match(src,/not political position/);
});
