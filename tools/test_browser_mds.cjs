const assert=require('node:assert/strict'),D=require('../site/mds-core.js'),C=require('../site/cluster-core.js'),A=require('../site/analysis-core.js');
(async()=>{
  const square=[[0,0],[1,0],[0,1],[1,1]],before=JSON.stringify(square),f=await D.fit(square,{maxIterations:1000,tolerance:1e-9});
  assert.ok(f.stress<1e-7);assert.equal(JSON.stringify(square),before);assert.deepEqual(f,await D.fit(square,{maxIterations:1000,tolerance:1e-9}));
  for(const r of f.runs)for(let i=1;i<r.history.length;i++)assert.ok(r.history[i].stress<=r.history[i-1].stress+1e-10);
  assert.equal(f.pair_count,6);assert.equal(f.bins.reduce((s,b)=>s+b.count,0),6);
  const duplicate=await D.fit([[0,0],[0,0],[1,0],[0,1]]);assert.equal(duplicate.zero_target_pairs,1);assert.ok(duplicate.coordinates.every(r=>r.every(Number.isFinite)));
  const zero=await D.fit([[1],[1],[1]]);assert.equal(zero.stress,0);assert.equal(zero.relative_distance_error,null);
  const x=Array.from({length:31},(_,i)=>[Math.sin(i),Math.cos(i*.4),i%5/5]);const limited=await D.fit(x,{starts:1,maxIterations:10,tolerance:1e-9});assert.equal(limited.converged,false);assert.ok(limited.warnings.some(w=>w.includes('provisional')));
  await assert.rejects(()=>D.solve(D.distances(square),square.map(()=>[0,0]),{maxIterations:10,tolerance:1e-6}),/collapsed/);
  await assert.rejects(()=>D.fit(x,{},async()=>{throw Error('cancel');}),/cancel/);await assert.rejects(()=>D.fit([[NaN],[1]]),/finite/);assert.throws(()=>D.options({starts:0}));
  assert.equal(D.diagnostics(new Float64Array(600*599/2).fill(1),Array.from({length:600},(_,i)=>[i/600,0])).pair_count,179700);
  const records=Array.from({length:18},(_,i)=>({id:'p'+i,text_sha256:'a'.repeat(64),text:(i<9?'energy climate emissions solar':'security peace weapons diplomacy')+' policy'+i,date:'2026-09-22',country:'Fixture',scope:'general_debate',meeting:'Meeting '+i%6,source_url:'https://example.org/'+i})),v=A.tfidf(records).vectors;
  const opts={algorithm:'gmm',representation:'compare',components:3,k:2,gmm:{starts:2},stability:{enabled:true,replicates:10}},baseline=await C.run(records,v,opts),compared=await C.run(records,v,{...opts,mds:{enabled:true}});
  for(const [a,b]of [[baseline,compared],[baseline.comparison.alternative,compared.comparison.alternative]]){
    assert.deepEqual(a.gmm,b.gmm);assert.deepEqual(a.stability,b.stability);assert.deepEqual(a.points,b.points.map(({mds,...p})=>p));assert.equal(b.mds.fidelity.points.length,18);assert.ok(b.points.every(p=>p.mds.length===2));
  }
  console.log('PASS metric MDS geometry, stress descent, duplicates, degeneracy, limits, restart reproducibility, cancellation, and unchanged UMAP/memberships/grouped refits in PCA/LSA');
})().catch(e=>{console.error(e);process.exitCode=1;});
