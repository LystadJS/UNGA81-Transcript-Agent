'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const V = require('./renderer.js');
const A = require('./adapter.js');
const original = JSON.parse(fs.readFileSync(path.join(__dirname,'fixture.json'),'utf8'));
const copy = () => structuredClone(original);
const fails = (name,fn,pattern=/refused|invalid|mismatch|missing|incoherent|cannot|incomplete|dropped/i) =>
  test(name,()=>assert.throws(fn,pattern));

test('complete invented fixture and sources validate',()=>{
  assert.equal(V.check(copy()).sources.length,5);
  assert.equal(original.panels.length,4);
  assert.deepEqual(original.sources.map(s=>s.status),['available','available','available','missing','failed']);
  assert.equal(original.panels[0].coverage.missing,2);
  assert.equal(original.panels[0].coverage.excluded,2);
});
test('synthetic weighted W2 supplied association is 2/3, observed zero distinct from no joint fit',()=>{
  const p=original.panels[0];
  assert.ok(Math.abs(p.rows[0].association-2/3)<1e-12);
  assert.equal(p.rows[1].association,0);
  assert.equal(p.rows[2].association,null);
  const svg=V.renderPanel(p);
  assert.match(svg,/66\.7%/);
  assert.match(svg,/0\.0%/);
  assert.match(svg,/no joint fit/);
  assert.match(svg,/unstable/);
  assert.doesNotMatch(svg,/75\.0%/);
});
test('NMF zero, source absence, and withheld values remain distinct',()=>{
  const p=original.panels[1];
  assert.equal(p.rows.find(r=>r.country==='Illustrative B'&&r.theme==='T1').weighted_sum,0);
  assert.equal(p.rows.find(r=>r.country==='Illustrative C'&&r.theme==='T1').status,'missing');
  assert.equal(p.rows.find(r=>r.country==='Illustrative B'&&r.theme==='T2').status,'withheld');
  assert.match(V.renderPanel(p),/0\.0%/);
  assert.match(V.renderPanel(p),/WITHHELD/);
});
test('temporal failed boundary has no fabricated continuous trajectory',()=>{
  const p=original.panels[2],svg=V.renderPanel(p);
  assert.equal(p.alignments[1].status,'withheld');
  assert.match(svg,/WITHHELD/);
  assert.match(svg,/composition change/i);
});
test('attempted, failed, skipped and unassigned are visible',()=>{
  const svg=V.renderPanel(original.panels[3]);
  assert.match(svg,/failed 3/);
  assert.match(svg,/skipped 1/);
  assert.match(svg,/INCOMPATIBLE/);
});
test('script-free HTML and JSON replay preserve numeric values exactly',()=>{
  const data=copy(),json=V.exportJSON(data),staticPage=V.htmlDocument(data);
  assert.deepEqual(JSON.parse(json),data);
  assert.deepEqual(V.check(JSON.parse(json)),JSON.parse(json)); // validated replay is semantically identical
  assert.match(staticPage,/Original weighted association/);
  assert.match(staticPage,/SRC-E/);
  assert.match(staticPage,/failed/);
  assert.doesNotMatch(staticPage,/<script\b/i);
  assert.doesNotMatch(staticPage,/fetch\(/);
});
test('deterministic replay checksum',()=>{
  const digest=x=>crypto.createHash('sha256').update(V.exportJSON(x)).digest('hex');
  assert.equal(digest(copy()),digest(copy()));
  assert.match(digest(copy()),/^[a-f0-9]{64}$/);
});
test('SVG uses titles, text labels, and no executable scripts',()=>{
  for(const p of original.panels){const svg=V.renderPanel(p);
    assert.match(svg,/<svg\s/);assert.match(svg,/<title>/);assert.match(svg,/<desc>/);
    assert.doesNotMatch(svg,/<script|onload=|onclick=/i);}
});

fails('reject non-synthetic fixture',()=>{const x=copy();x.fixture_kind='empirical';V.check(x)});
fails('reject eligible source without SHA-256',()=>{const x=copy();x.sources[0].sha256=null;V.check(x)});
fails('reject invented hash for missing source without reason',()=>{const x=copy();x.sources[3].missing_reason=null;V.check(x)});
fails('reject duplicate source identity',()=>{const x=copy();x.sources[1].id=x.sources[0].id;V.check(x)});
fails('reject source text entering public display',()=>{const x=copy();x.sources[1].transcript='PRIVATE';V.check(x)});
fails('reject real network URL in synthetic source',()=>{const x=copy();x.sources[0].source_url='https://un.org/example';V.check(x)});
fails('reject hidden failed group in frame',()=>{const x=copy();x.sources.pop();V.check(x)});
fails('reject dropping missing groups from panel identity',()=>{const x=copy();x.panels[1].identity.source_ids.pop();V.check(x)});
fails('reject source population denominator changed after exclusion',()=>{const x=copy();x.panels[0].coverage.eligible=4;V.check(x)});
fails('reject incomplete off-diagonal pair frame',()=>{const x=copy();x.panels[0].rows.pop();V.check(x)});
fails('reject duplicate unordered pair',()=>{const x=copy();x.panels[0].rows[2].a='SRC-B';x.panels[0].rows[2].b='SRC-A';x.panels[0].rows[2].source_ids=['SRC-B','SRC-A'];V.check(x)});
fails('reject weighted W2 ratio tampering',()=>{const x=copy();x.panels[0].rows[0].association=.9;V.check(x)});
fails('reject inappropriate mean-family substitution',()=>{const x=copy();x.panels[0].rows[0].association=.5;V.check(x)});
fails('reject failed fit denominator disappearance',()=>{const x=copy();x.panels[0].rows[0].failed_fit_count=2;V.check(x)});
fails('reject planned pair opportunity mismatch',()=>{const x=copy();x.panels[0].rows[0].planned_count=4;V.check(x)});
fails('reject null when jointly assigned opportunity exists',()=>{const x=copy();x.panels[0].rows[1].association=null;V.check(x)});
fails('reject zero in place of unassessed pair',()=>{const x=copy();x.panels[0].rows[2].association=0;V.check(x)});
fails('reject missing source pair faked with opportunities',()=>{const x=copy();x.panels[0].rows[2].record_status='missing_pair';V.check(x)});
fails('reject family weight sum changed',()=>{const x=copy();x.panels[0].family_weight_audit[0].planned_weight=.6;V.check(x)});
fails('reject family attempt ledger discrepancy',()=>{const x=copy();x.panels[0].family_weight_audit[1].failed=4;V.check(x)});
fails('reject false country attribution join',()=>{const x=copy();x.panels[1].rows[0].source_ids=['SRC-C'];x.panels[1].rows[0].evidence_count=1;V.check(x)});
fails('reject absent country-component cell',()=>{const x=copy();x.panels[1].rows.pop();V.check(x)});
fails('reject missing theme converted to numerical zero',()=>{const x=copy();x.panels[1].rows[5].weighted_sum=0;V.check(x)});
fails('reject component denominator zero',()=>{const x=copy();x.panels[1].rows[0].weight_total=0;V.check(x)});
fails('reject invalid source attribution count',()=>{const x=copy();x.panels[1].unattributed_count=1;V.check(x)});
fails('reject missing temporal year in full actor frame',()=>{const x=copy();x.panels[2].rows.pop();V.check(x)});
fails('reject temporal score assigned to missing source',()=>{const x=copy();x.panels[2].rows[2].status='observed';x.panels[2].rows[2].xy=[0,0];V.check(x)});
fails('reject fictitious alignment rank on passed gate',()=>{const x=copy();x.panels[2].alignments[0].rank_ok=false;V.check(x)});
fails('reject temporal representation change',()=>{const x=copy();x.panels[2].alignments[0].reference_basis='other';V.check(x)});
fails('reject temporal source period mismatch',()=>{const x=copy();x.panels[2].rows[0].source_ids=['SRC-B'];V.check(x)});
fails('reject method fit-accounting mismatch',()=>{const x=copy();x.panels[3].rows[0].failed=3;V.check(x)});
fails('reject comparable stability for incompatible method',()=>{const x=copy();x.panels[3].rows[1].stability=.92;V.check(x)});
fails('reject settings checksum corruption',()=>{const x=copy();x.panels[3].rows[0].settings_sha256='broken';V.check(x)});
fails('reject representation change in comparison',()=>{const x=copy();x.panels[3].rows[0].representation_id='different';V.check(x)});
fails('reject unmarked withheld result',()=>{const x=copy();x.panels[2].status='withheld';x.panels[2].reason=null;V.check(x)});
fails('reject source hash identity conflict',()=>{const x=copy();x.panels[0].identity.selection_sha256='f'.repeat(64);V.check(x)});

test('failed/empty/withheld remain visible without exposing unaccepted plots',()=>{
  for(const state of ['failed','empty','withheld']){
    const x=copy();x.panels[2].status=state;x.panels[2].reason='Synthetic '+state+' gate';
    V.check(x);
    assert.match(V.htmlDocument(x),new RegExp('ABSTAIN — '+state));
    assert.match(V.renderPanel(x.panels[2]),new RegExp('Synthetic '+state));
  }
});
test('HTML injection in benign label is escaped',()=>{
  const x=copy();x.panels[1].themes[0].label='<img src=x onerror=alert(1)>';
  const html=V.htmlDocument(x);
  assert.doesNotMatch(html,/<img\s/);
  assert.match(html,/&lt;img/);
});

// Test the injected accepted-validation boundary. Mocks model only the verified
// shape; they are NOT evidence that the authentic W2/W4 producer has passed.
function w2Mock(){
  const data=copy(),obs=data.sources.map(s=>({id:s.id,text_sha256:s.sha256,
    source_status:s.status==='available'?'available':'unavailable',
    exclusion_reasons:s.status==='available'?[]:['unavailable'],
    missing_reason:s.missing_reason,country:s.country,date:s.period+'-01-01',
    meeting_id:s.meeting_id,source_url:null,json_pointer:null,review_status:s.review_status}));
  const p=data.panels[0];
  const env={schema:'un.parallel-analysis.v1',contract_version:'1.0.0',
    producer:{workstream_id:'W2',fixture_kind:'synthetic'},
    upstream:{source_schema:'synthetic.v1',source_hash_basis:'synthetic',source_sha256:data.source.source_sha256,
      selection_sha256:data.source.selection_sha256},
    cohort:{split:'synthetic',population:'invented frame',unit:'synthetic',weighting:'equal source opportunity',
      total_in_frame:5,eligible:3},
    observations:obs,models:[{representation_id:'w2-hard-assignment-identity-join-v1',representation_version:'1'}],
    coverage:{eligible:3,excluded:2,unavailable_sources:2,models:[]},
    publication_eligible:false,evaluation_role:'engineering_only'};
  const sidecar={pairs:[...p.rows.map(r=>({
    observation_a:r.a,observation_b:r.b,...Object.fromEntries([
      'coassigned_count','assigned_both_count','planned_count','missing_pair_count',
      'noise_pair_count','different_cluster_count','failed_fit_count',
      'coassigned_weight','assigned_both_weight','planned_weight',
      'association','assignment_coverage','contributing_families'
    ].map(k=>[k,r[k]]))})),...obs.slice(0,3).map(o=>({observation_a:o.id,observation_b:o.id}))],
    family_weight_audit:p.family_weight_audit.map(f=>({method_family:f.family,total_weight:f.planned_weight})),
    ambiguous_members:[{observation_id:'SRC-A'}]};
  return {env,sidecar,validators:{validateW2:async(e,s)=>({env:e,sidecar:s,ids:['SRC-A','SRC-B','SRC-C']})}};
}
test('W2 adapter calls validator and maps only original weighted evidence',async()=>{
  const x=w2Mock();let calls=0;
  const data=await A.fromW2(x.env,x.sidecar,{validateW2:async(e,s)=>{calls++;return x.validators.validateW2(e,s)}});
  assert.equal(calls,1);assert.ok(Math.abs(data.panels[0].rows[0].association-2/3)<1e-12);
  assert.equal(data.panels[0].family_weight_audit[0].attempted,null);
  assert.equal(data.sources.length,5);
  assert.equal(data.panels[2].status,'withheld');
});
test('W2 adapter requires genuine callable source validator, not a boolean',async()=>{
  const x=w2Mock();await assert.rejects(A.fromW2(x.env,x.sidecar,{validated:true}),/validator is required/);
});
test('W2 adapter refuses consensus ratio corruption even after mocked validator',async()=>{
  const x=w2Mock();x.sidecar.pairs[0].association=.5;
  await assert.rejects(A.fromW2(x.env,x.sidecar,x.validators),/weighted conditional association/);
});
test('W2 adapter rejects missing unavailable source and inflated eligible denominator',async()=>{
  const x=w2Mock();x.env.observations.pop();await assert.rejects(A.fromW2(x.env,x.sidecar,x.validators),/Source frame/);
});
test('W2 adapter rejects source text attached to public synthetic observation',async()=>{
  const x=w2Mock();x.env.observations[0].text='SECRET';
  await assert.rejects(A.fromW2(x.env,x.sidecar,x.validators),/text-bearing/);
});
test('W2 adapter rejects non-synthetic envelope before rendering',async()=>{
  const x=w2Mock();x.env.producer.fixture_kind='empirical';
  await assert.rejects(A.fromW2(x.env,x.sidecar,x.validators),/synthetic/);
});
test('W4 adapter requires accepted source and alignment validator',async()=>{
  await assert.rejects(A.fromW4({},{}),/validator required/);
});
test('W6 adapter requires envelope and panel validators',()=>{
  assert.throws(()=>A.fromW6Themes({}, {}, {}),/validators required/);
});
