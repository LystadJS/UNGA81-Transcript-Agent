const assert=require('node:assert/strict'),G=require('../site/gmm-core.js'),C=require('../site/cluster-core.js'),A=require('../site/analysis-core.js');
const close=(a,b,t=1e-8)=>assert.ok(Math.abs(a-b)<t,`${a} != ${b}`);
(async()=>{
  const model={weights:[.5,.5],means:[[-1],[1]],variances:[[1],[1]],covariance:'diag',regularization:0};
  const e=G.expectation([[0],[1000]],model);close(e.responsibilities[0][0],.5);close(e.log_densities[0],-.5*Math.log(2*Math.PI)-.5);assert.ok(Number.isFinite(e.log_likelihood));close(e.responsibilities[1][1],1);
  const x=[[0,0],[2,4],[4,8]],r=[[1,0],[.5,.5],[0,1]],m=G.maximize(x,r,'diag',.01);
  close(m.means[0][0],2/3);close(m.means[1][0],10/3);close(m.variances[0][0],8/9+.01);close(m.variances[0][1],32/9+.01);
  const sphere=G.maximize(x,r,'spherical',.01);close(sphere.variances[0][0],20/9+.01);close(sphere.variances[0][1],20/9+.01);
  assert.equal(G.parameterCount(4,20,'diag'),163);assert.equal(G.parameterCount(4,20,'spherical'),87);
  const aligned=G.align([[.9,.1],[.4,.6]],[[.1,.9],[.6,.4]]);assert.deepEqual(aligned.mapping,[2,1]);close(aligned.mean_total_variation,0);
  close(G.align([[1,0],[0,1]],[[.5,.5],[.5,.5]]).mean_total_variation,.5);close(G.ambiguity([.5,.5]).normalized_entropy,1);close(G.ambiguity([1]).normalized_entropy,0);
  const data=Array.from({length:40},(_,i)=>[(i<20?-3:3)+Math.sin(i)*.5,Math.cos(i)*.3]);
  for(const covariance of ['diag','spherical']){
    const fit=await G.fit(data,{k:2,covariance});assert.equal(fit.labels.length,40);assert.equal(fit.diagnostics.hard_counts[0]+fit.diagnostics.hard_counts[1],40);
    assert.ok(fit.diagnostics.converged_starts>0);assert.ok(fit.labels.slice(0,20).every(c=>c===fit.labels[0]));assert.notEqual(fit.labels[0],fit.labels[39]);
    fit.responsibilities.forEach(r=>close(r.reduce((a,b)=>a+b,0),1));assert.deepEqual(fit,await G.fit(data,{k:2,covariance}));
    close(fit.diagnostics.aic,2*fit.diagnostics.parameter_count-2*fit.diagnostics.log_likelihood);
    close(fit.diagnostics.bic,Math.log(40)*fit.diagnostics.parameter_count-2*fit.diagnostics.log_likelihood);
  }
  const overlap=Array.from({length:31},(_,i)=>[Math.sin(i*.7)+(i%3)*.3,Math.cos(i*.4)]);const limited=await G.fit(overlap,{k:2,starts:1,maxIterations:10,tolerance:1e-8});assert.ok(limited.skipped);assert.equal(limited.diagnostics.runs[0].converged,false);
  const one=await G.fit(data,{k:1});assert.ok(one.labels.every(c=>c===0));assert.ok(one.responsibilities.every(r=>r[0]===1));
  const singular=await G.fit(Array.from({length:6},()=>[1,1]),{k:1});assert.ok(singular.diagnostics.near_floor_dimensions[0]===2);assert.ok(singular.diagnostics.warnings.length);
  assert.ok((await G.fit(Array.from({length:6},()=>[1,1]),{k:2})).skipped);
  await assert.rejects(()=>G.fit(data,{k:2},async()=>{throw Error('cancel');}),/cancel/);
  assert.throws(()=>G.options({covariance:'full'}));assert.throws(()=>G.options({regularization:0}));assert.throws(()=>C.options({algorithm:'kmeans',k:1}));assert.equal(C.options({algorithm:'gmm',k:1}).k,1);
  const rows=Array.from({length:18},(_,i)=>({id:'p'+i,text_sha256:'a'.repeat(64),text:(i<9?'energy climate emissions solar':'security peace weapons diplomacy')+' policy'+i,date:'2026-09-22',country:'Fixture',scope:'general_debate',meeting:'Meeting '+i%6,source_url:'https://example.org/'+i}));
  const vectors=A.tfidf(rows).vectors,options={algorithm:'gmm',representation:'compare',components:3,k:2,gmm:{starts:2},stability:{enabled:true,replicates:10}};
  const fit=await C.run(rows,vectors,options);assert.ok(!fit.skipped);assert.equal(fit.points[0].memberships.length,2);assert.equal(fit.stability.successful,10);assert.equal(fit.stability.soft_membership.mean_total_variation.count,10);
  assert.deepEqual(fit.stability.runs.map(r=>r.groups),fit.comparison.alternative.stability.runs.map(r=>r.groups));
  const changed=await C.run(rows,vectors,{...options,neighbors:3,minDist:.4,umapSeed:99});assert.deepEqual(fit.gmm,changed.gmm);assert.deepEqual(fit.stability,changed.stability);assert.deepEqual(fit.points.map(p=>p.memberships),changed.points.map(p=>p.memberships));assert.notDeepEqual(fit.points.map(p=>p.umap),changed.points.map(p=>p.umap));
  const k1=await C.run(rows,vectors,{...options,k:1});assert.equal(k1.clustering.silhouette,null);assert.equal(k1.comparison.between_cluster_ari,null);assert.equal(k1.stability.ari.count,0);
  console.log('PASS Gaussian density/EM hand calculations, stable log likelihood, regularization, information criteria, reproducibility, soft alignment, single-component reference, degenerate starts, cancellation, PCA/LSA grouped refits and UMAP independence');
})().catch(e=>{console.error(e);process.exitCode=1;});
