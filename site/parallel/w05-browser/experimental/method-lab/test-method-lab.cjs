'use strict';
/* Standalone synthetic-only Node tests; no network and no reserved source access. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const C=require('./contracts.js');
const A=require('./adapters.js');
const {TaskController}=require('./task-controller.js');
const UNLatent=require('../../../latent-core.js');
const UNClusters=require('../../../cluster-core.js');
const UNLSA=require('../../../lsa-core.js');

const fixture=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/synthetic-contract.json'),'utf8'));
const clone=value=>JSON.parse(JSON.stringify(value));
let tests=0;
async function test(label,fn) {
  await fn();
  console.log('PASS '+label);
  tests++;
}
async function reject(label,change,pattern) {
  await test(label,()=>assert.throws(()=>C.validateParallel(change(clone(fixture))),pattern));
}
const hash=text=>crypto.createHash('sha256').update(text,'utf8').digest('hex');

class FakeWorker {
  constructor(url) {
    this.url=url;
    this.killed=false;
    FakeWorker.last=this;
  }
  postMessage(value) { this.lastMessage=value; }
  terminate() {this.killed=true;}
  emit(data) {this.onmessage?.({data});}
}

async function main() {
  await test('synthetic source/fit accounting and metadata',()=>{
    C.validateParallel(fixture);
    const view=C.fromParallel(fixture);
    assert.equal(view.observations.length,5);
    assert.equal(view.coverage.eligible,4);
    assert.equal(view.coverage.excluded,1);
    assert.equal(view.models.length,3);
    assert.equal(view.observations[4].source_status,'unavailable');
    assert.equal(view.models[2].rows[0].membership_kind,'nmf_share');
  });
  await reject('duplicate observations rejected',v=>{v.observations[1].id=v.observations[0].id;return v;},/duplicate/i);
  await reject('missing source hash reason rejected',v=>{v.upstream.source_sha256=null;return v;},/missing reason/i);
  await reject('non-https source rejected',v=>{v.observations[0].source_url='http://example.org';return v;},/HTTPS/);
  await reject('orphan result rejected',v=>{v.results[0].observation_id='missing';return v;},/Orphan/);
  await reject('duplicated result rejected',v=>{v.results.push(clone(v.results[0]));return v;},/Duplicate/);
  await reject('cross-representation point rejected',v=>{v.results[0].representation_basis_id='changed';return v;},/Representation/);
  await reject('unsupported contract minor rejected',v=>{v.contract_version='1.1.0';return v;},/compatibility review/);
  await reject('hidden withheld split rejected',v=>{v.cohort.split='holdout';return v;},/provenance/);
  await reject('fake omission of unavailable source rejected',v=>{v.results[4].status='assigned';v.results[4].cluster=1;return v;},/excluded/);
  await reject('invalid Unicode span rejected',v=>{v.observations[0].start=10;v.observations[0].end=9;return v;},/span/);
  await reject('invalid membership total rejected',v=>{v.results.find(r=>r.memberships).memberships=[.1,.2];return v;},/mixture vector/);
  await reject('missing fit denominator rejected',v=>{v.coverage.models[0].assigned=3;return v;},/Model coverage/);
  await reject('claim of release eligibility rejected',v=>{v.publication_eligible=true;return v;},/Engineering-only/);
  await test('comparison permits only source/representation-matched partitions',()=>{
    const view=C.fromParallel(fixture);
    assert.equal(A.compareViews(view,view,'fixture-kmeans','fixture-pam').numerical_comparison_permitted,true);
    assert.equal(A.compareViews(view,view,'fixture-kmeans','fixture-nmf').numerical_comparison_permitted,false);
    const changed=clone(fixture);
    changed.upstream.source_sha256='f'.repeat(64);
    assert.equal(A.compareViews(view,C.fromParallel(changed),'fixture-kmeans','fixture-pam').identical_population,false);
    const reordered=clone(fixture);
    reordered.observations.reverse();
    assert.equal(C.compare(view,C.fromParallel(reordered),'fixture-kmeans','fixture-pam').identical_population,true);
  });
  await test('checksum roundtrip: current method-lab save',async()=>{
    const packed=await A.packParallel([fixture]);
    const replay=await A.restoreParallel(packed);
    assert.deepEqual(replay,[fixture]);
    const corrupted=JSON.parse(packed);
    corrupted.payload_json=corrupted.payload_json.replace('synthetic-1','changed-id');
    await assert.rejects(()=>A.restoreParallel(JSON.stringify(corrupted)),/checksum mismatch/);
    corrupted.version='2.0.0';
    await assert.rejects(()=>A.restoreParallel(JSON.stringify(corrupted)),/Unsupported lab archive/);
  });
  await test('cancel terminates computation and rejects incomplete result',async()=>{
    const manager=new TaskController('worker.js',url=>new FakeWorker(url));
    const activity=manager.start('run_local',{},()=>{});
    const worker=FakeWorker.last,id=worker.lastMessage.id;
    worker.emit({id,type:'progress',message:'started'});
    assert.equal(manager.cancel(),true);
    assert.equal(worker.killed,true);
    await assert.rejects(activity,/Cancelled/);
    worker.emit({id,type:'result',result:'late'});
    assert.equal(manager.busy,false);
    const next=manager.start('open',{text:'synthetic'},()=>{});
    FakeWorker.last.emit({id:FakeWorker.last.lastMessage.id,type:'result',kind:'parallel'});
    await next;
    assert.equal(manager.busy,false);
  });
  await test('worker error and malformed message fail without retained partials',async()=>{
    const manager=new TaskController('worker.js',url=>new FakeWorker(url));
    const promise=manager.start('open',{});
    FakeWorker.last.emit({id:FakeWorker.last.lastMessage.id,type:'error',message:'Invalid source'});
    await assert.rejects(promise,/Invalid source/);
    assert.equal(manager.busy,false);
  });
  const texts=[
    'synthetic cedar cedar river',
    'synthetic cedar river forest',
    'synthetic cedar forest green',
    'synthetic desert stone dry',
    'synthetic desert sand stone',
    'synthetic sand dry desert'
  ];
  const records=texts.map((text,i)=>({
    id:'test-'+(i+1),date:'2026-09-22',country:'Synthetic '+(i+1),
    region:'Synthetic',language:'en',scope:'general_debate',
    meeting:'Synthetic fixture (not an actual UN meeting)',
    source_url:'https://example.org/synthetic/'+(i+1),
    text,text_sha256:hash(text)
  }));
  const corpus={schema:'un.browser.corpus.v1',records,coverage:[],origin:'local synthetic fixture'};
  const payload={kind:'corpus',text:JSON.stringify(corpus)};
  const plan={schema:'un.latent-plan.v1',
    base:{topic:'',phrases:[],exclude:[],start:'2026-09-22',end:'2026-09-22',region:'All regions',scope:'all'},
    compare_parents:false,
    stability:{enabled:false,unit:'meeting',replicates:30,fraction:.8,seed:31415},
    settings:[
      {label:'Synthetic PCA k-means',method:'clusters',
        options:{representation:'pca',algorithm:'kmeans',k:2,components:2,neighbors:3,seed:12,umapSeed:12}},
      {label:'Synthetic LSA PAM',method:'clusters',
        options:{representation:'lsa',algorithm:'pam',k:2,components:2,neighbors:3,seed:12,umapSeed:12}},
      {label:'Synthetic NMF',method:'nmf',
        options:{components:2,starts:1,maxIterations:100,seed:12}}
    ]};
  await test('existing numerical adapter runs source-bound synthetic corpus',async()=>{
    const fitted=await UNLatent.run(payload,plan,{engine:UNLatent.VERSION,execution:'synthetic-node-test'});
    assert.equal(fitted.entries.length,3);
    assert.equal(fitted.source_hash,await UNLatent.hash(payload.text));
    const archive=await UNLatent.pack(payload,fitted);
    const restored=await UNLatent.restore(archive);
    const view=A.fromLegacy(restored);
    assert.equal(view.models.length,3);
    assert.equal(view.observations.length,6);
    assert.equal(view.models[0].rows.length,6);
    assert.equal(view.models[2].rows.length,6);
    const old=clone(fitted);old.engine='latent-comparison-1.0.0';
    const oldArchive=await UNLatent.pack(payload,old);
    const oldRestored=await UNLatent.restore(oldArchive);
    assert.equal(A.fromLegacy(oldRestored).models.length,3);
    const bad=JSON.parse(archive);bad.result_json=bad.result_json.replace('Synthetic LSA PAM','tampered');
    await assert.rejects(()=>UNLatent.restore(JSON.stringify(bad)),/integrity/);
  });
  await test('deterministic PCA/LSA cross-run numeric check',()=>{
    const vectors=[
      new Map([['alpha',1],['beta',.4]]),
      new Map([['alpha',.8],['beta',.3]]),
      new Map([['gamma',1],['delta',.4]]),
      new Map([['gamma',.8],['delta',.3]])
    ];
    const pca1=UNClusters.pca(vectors,2),pca2=UNClusters.pca(vectors,2);
    const lsa1=UNLSA.lsa(vectors,2),lsa2=UNLSA.lsa(vectors,2);
    const close=(a,b)=>Math.abs(a-b)<1e-9;
    for (const [first,second] of [[pca1,pca2],[lsa1,lsa2]]) {
      assert.equal(first.scores.length,4);
      for(let i=0;i<4;i++)for(let j=0;j<2;j++){
        assert.ok(Number.isFinite(first.scores[i][j]));
        assert.ok(close(first.scores[i][j],second.scores[i][j]));
      }
    }
    assert.equal(lsa1.rank,2);
  });
  console.log('TOTAL '+tests+' tests passed; synthetic only; browser/device acceptance separate.');
}
main().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
