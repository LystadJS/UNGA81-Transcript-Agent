'use strict';
/* Synthetic-only W5/W6 coordinator interface verification; no source/network reads. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const R=require('../site/research-browser.js');
const F=require('../site/experimental/evidence-viz/fixture.js');
const C=require('../site/parallel/w05-browser/experimental/method-lab/contracts.js');
const V=require('../site/experimental/evidence-viz/evidence-viz.js');
const clone=x=>structuredClone(x);
const reject=(label,change)=>test(label,()=>{
 const x=clone(F.fixture());change(x);assert.throws(()=>R.inspect(x));
});
test('accepted W5 and W6 independently validate the complete synthetic envelope',()=>{
 const f=F.fixture(),v=R.inspect(f),summary=R.summaryData(v);
 assert.strictEqual(C.validateParallel(f.envelope),f.envelope);
 assert.equal(V.validateEnvelope(f.envelope).size,11);
 assert.equal(v.panels.length,4);
 assert.deepEqual(v.panels.map(x=>x.kind).sort(),V.TYPES.slice().sort());
 assert.equal(summary.frame,11);
 assert.equal(summary.eligible,10);
 assert.equal(summary.excluded,1);
 assert.equal(summary.unavailable,1);
 assert.equal(summary.models.length,2);
 for(const m of summary.models) {
  assert.equal(m.assigned+m.unassigned+m.not_fitted,10);
  assert.equal(m.excluded,1);
 }
 for(const panel of v.panels) {
  assert.match(panel.svg,/^<svg xmlns=/);
  assert.match(panel.html,/Observation identity and source ledger/);
 }
});
reject('reject private source flag',x=>{x.envelope.producer.fixture_kind='private_development';});
reject('reject development/held-out split',x=>{x.envelope.cohort.split='development';});
reject('reject forged non-synthetic upstream',x=>{x.envelope.upstream.source_schema='un.passage-corpus.v1';});
reject('reject original transcript source URLs',x=>{x.envelope.observations[0].source_url='https://transcripts.un.org/en/asset/x/y';});
reject('reject private text content',x=>{x.envelope.observations[0].text='confidential';});
reject('reject embedded review record',x=>{x.panels[0].review_packet='confidential';});
reject('reject missing excluded-model row',x=>{
 const row=x.envelope.results.findIndex(y=>y.status==='excluded');
 x.envelope.results.splice(row,1);
});
reject('reject mismatched panel selection hash',x=>{x.panels[0].identity.selection_sha256='0'.repeat(64);});
reject('reject missing visualization panel',x=>{x.panels.pop();});
reject('reject extra untrusted bundle fields',x=>{x.extra='untrusted';});
reject('reject wrong result representation',x=>{x.envelope.results[0].representation_basis_id='wrong';});
reject('reject publication gate bypass',x=>{x.envelope.publication_eligible=true;});
test('no upload, persistent storage, external model fitting or public release action',()=>{
 const source=fs.readFileSync(path.join(__dirname,'../site/research-browser.js'),'utf8');
 const html=fs.readFileSync(path.join(__dirname,'../site/research.html'),'utf8');
 assert.match(html,/connect-src 'none'/);
 assert.match(html,/worker-src 'none'/);
 assert.doesNotMatch(source,/\b(fetch|XMLHttpRequest|sendBeacon|localStorage|sessionStorage|WebSocket|importScripts)\s*\(/);
 assert.match(html,/parallel\/w05-browser\/experimental\/method-lab\/contracts\.js/);
 assert.match(html,/experimental\/evidence-viz\/evidence-viz\.js/);
 assert.match(fs.readFileSync(path.join(__dirname,'../site/index.html'),'utf8'),/href="research.html"/);
 assert.match(fs.readFileSync(path.join(__dirname,'../site/latent.html'),'utf8'),/href="research.html"/);
 assert.equal(R.MAX_BYTES,1048576);
});
test('nested private metadata refused before rendering',()=>{
 let x={},y=x;for(let i=0;i<40;i++){y.more={};y=y.more;}
 assert.throws(()=>R.checkMetadataOnly(x),/depth/);
});
