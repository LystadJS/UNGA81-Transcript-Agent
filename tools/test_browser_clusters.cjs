const assert=require('node:assert/strict');
const A=require('../site/analysis-core.js'),C=require('../site/cluster-core.js');
const close=(a,b,t=1e-8)=>assert.ok(Math.abs(a-b)<t,`${a} != ${b}`);
(async()=>{
  // Independent hand calculation: centered diamond, covariance diag(2/3,2/3).
  const vectors=[[1,0],[0,1],[-1,0],[0,-1]].map(row=>new Map(row.map((v,i)=>[String(i),v])));
  const p=C.pca(vectors,10);assert.equal(p.rank,2);assert.equal(p.components,2);
  p.eigenvalues.forEach(x=>close(x,2/3));close(p.retained_variance,1);
  const d2=(a,b)=>a.reduce((s,v,i)=>s+(v-b[i])**2,0);
  for(let i=0;i<4;i++)for(let j=0;j<4;j++)close(d2(p.scores[i],p.scores[j]),d2([...vectors[i].values()],[...vectors[j].values()]));
  for(let j=0;j<2;j++)close(p.scores.reduce((s,row)=>s+row[j],0),0);
  close(C.silhouette([[0],[1],[10],[11]],[0,0,1,1]),(9.5/10.5+8.5/9.5)/2);
  close(C.ari([0,0,1,1],[1,1,0,0]),1);
  const data=Array.from({length:18},(_,i)=>({id:'p'+i,text_sha256:'a'.repeat(64),text:(i<9?'energy climate emissions carbon solar':'security peace conflict weapons diplomacy')+' '+['policy','budget','proposal'][i%3]}));
  const t=A.tfidf(data),fit=await C.run(data,t.vectors,{k:2,components:4});
  assert.equal(fit.points.length,18);assert.equal(fit.clusters.length,2);
  assert.equal(new Set(fit.points.slice(0,9).map(p=>p.cluster)).size,1);
  assert.notEqual(fit.points[0].cluster,fit.points[9].cluster);
  assert.ok(fit.kmeans.silhouette>0.5);assert.ok(fit.kmeans.inertia>=0);
  const same=await C.run(data,t.vectors,{k:2,components:4});assert.deepEqual(fit,same);
  const changed=await C.run(data,t.vectors,{k:2,components:4,umapSeed:17,neighbors:3,minDist:0.4});
  assert.deepEqual(fit.kmeans,changed.kmeans);assert.deepEqual(fit.points.map(x=>[x.cluster,x.pca]),changed.points.map(x=>[x.cluster,x.pca]));
  assert.notDeepEqual(fit.points.map(x=>x.umap),changed.points.map(x=>x.umap));
  assert.ok((await C.run(data.slice(0,3),t.vectors.slice(0,3))).skipped);
  assert.ok((await C.run(Array(601).fill(data[0]),[])).skipped);
  assert.ok((await C.run(data,Array(18).fill(new Map([['same',1]])))).skipped);
  assert.ok((await C.run(data.slice(0,4),t.vectors.slice(0,4),{k:4})).skipped);
  const empty=await C.run([...data,{id:'empty'}],[...t.vectors,new Map()],{k:2});assert.equal(empty.excluded[0].id,'empty');
  assert.throws(()=>C.options({components:1}));assert.throws(()=>C.options({minDist:1}));
  await assert.rejects(()=>C.run(data,t.vectors,{k:2},async()=>{throw Error('test cancel');}),/test cancel/);
  const corpus={schema:'un.browser.corpus.v1',coverage:[],records:data.map(r=>({...r,date:'2026-09-22',country:'Fixture',region:'Unmapped',language:'en',scope:'general_debate',meeting:'General Debate',source_url:'https://example.org/'}))};
  const params={topic:'',phrases:[],exclude:[],start:'2026-09-22',end:'2026-09-22',region:'All regions',scope:'all',methods:['clusters'],clustering:{k:2}};
  // Repeated texts are removed by existing deduplication before the new pipeline.
  const result=await A.analyze(corpus,params);assert.equal(result.methods.clusters.input_count,6);assert.equal(result.counts.duplicates,12);
  const topicResult=await A.analyze(corpus,{...params,topic:'energy',phrases:['energy']});assert.equal(topicResult.counts.matched,3);assert.ok(topicResult.methods.clusters.skipped);
  console.log('PASS PCA reference geometry, k-means separation, silhouette, seed reproducibility, UMAP independence, rank/size limits, exclusions, cancellation and filter integration');
})().catch(e=>{console.error(e);process.exitCode=1;});
