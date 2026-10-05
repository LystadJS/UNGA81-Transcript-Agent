const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const A=require('../site/analysis-core.js'),C=require('../site/cluster-core.js'),M=require('../site/representation-metrics.js');
const near=(a,b,t=1e-9)=>assert.ok(Math.abs(a-b)<t,`${a} != ${b}`);
const sparse=rows=>rows.map(row=>new Map(row.map((x,i)=>[String(i),x]).filter(([,x])=>x!==0)));
const d2=(a,b)=>a.reduce((s,v,i)=>s+(v-b[i])**2,0);
(async()=>{
  // Hand SVD: X'X = diag(27,2). First component is the mean profile,
  // with 27/29 of uncentered energy but none of the centered variation.
  const matrix=[[3,1],[3,-1],[3,0]],vectors=sparse(matrix);
  const one=C.lsa(vectors,1);near(one.singular_values[0],Math.sqrt(27));
  near(one.retained_energy,27/29);near(one.retained_variance,0);
  near(one.relative_reconstruction_error,Math.sqrt(2/29));
  assert.equal(one.component_terms[0].positive[0].term,'0');near(one.component_terms[0].positive[0].weight,1);
  const full=C.lsa(vectors,10);assert.equal(full.rank,2);assert.equal(full.components,2);
  near(full.retained_energy,1);near(full.retained_variance,1);
  for(let i=0;i<3;i++)for(let j=0;j<3;j++)near(d2(full.scores[i],full.scores[j]),d2(matrix[i],matrix[j]));
  const constant=C.lsa(sparse([[1,2],[1,2],[1,2]]),2);assert.equal(constant.retained_variance,null);near(constant.retained_energy,1);
  const empty=C.lsa([new Map(),new Map(),new Map()],2);assert.equal(empty.rank,0);
  assert.throws(()=>C.options({representation:'nmf'}));assert.throws(()=>C.represent(vectors,2,'unknown'));
  assert.deepEqual(M.sparseDistances(vectors),M.denseDistances(matrix));
  // Known rankings: k=1, one introduced neighbor of original rank 3.
  const hi=[[1,2,3,4],[0,2,3,4],[1,0,3,4],[2,4,1,0],[3,2,1,0]];
  const lo=hi.map(row=>row.slice());lo[0]=[3,2,1,4];
  const metric=M.agreement(hi,lo,1);near(metric.neighbor_overlap,0.8);near(metric.trustworthiness,1-4/30);near(metric.continuity,1-4/30);
  const identical=M.agreement(hi,hi,1);near(identical.trustworthiness,1);near(identical.continuity,1);near(identical.neighbor_overlap,1);
  assert.throws(()=>M.agreement(hi,lo,3));
  assert.deepEqual(M.order([[0,1,1],[1,0,2],[1,2,0]])[0],[1,2]);

  const topics=['climate emissions carbon renewable solar transition energy',
    'security weapons conflict disarmament peace ceasefire diplomacy',
    'education school teachers literacy students university learning'];
  const records=Array.from({length:48},(_,i)=>({id:'r'+i,text_sha256:'a'.repeat(64),
    text:topics[i%3]+' '+topics[i%3]+' unique'+String.fromCharCode(97+Math.floor(i/26),97+i%26),
    date:'2026-09-22',country:'Affiliation '+(i%6),region:'Unmapped',language:'en',scope:'general_debate',meeting:'Meeting '+Math.floor(i/6),source_url:`https://transcripts.un.org/en/asset/k/test${Math.floor(i/6)}?t=${i}`}));
  const terms=A.tfidf(records),settings={components:5,k:3,stability:{enabled:true,replicates:10}};
  const pca=await C.run(records,terms.vectors,settings);
  const lsa=await C.run(records,terms.vectors,{...settings,representation:'lsa'});
  const comparison=await C.run(records,terms.vectors,{...settings,representation:'compare'});
  assert.deepEqual(comparison.points,pca.points);assert.deepEqual(comparison.pca,pca.pca);
  assert.deepEqual(comparison.kmeans,pca.kmeans);assert.deepEqual(comparison.fidelity,pca.fidelity);
  assert.deepEqual(comparison.stability,pca.stability);assert.deepEqual(comparison.comparison.alternative,lsa);
  assert.equal(lsa.points[0].pca,undefined);assert.equal(lsa.pca,undefined);assert.equal(lsa.lsa.components,5);
  assert.equal(lsa.stability.representation,'lsa');assert.equal(comparison.comparison.paired_stability.count,10);
  assert.equal(comparison.comparison.membership_counts.flat().reduce((a,b)=>a+b,0),48);
  near(comparison.comparison.between_cluster_ari,C.ari(pca.points.map(p=>p.cluster),lsa.points.map(p=>p.cluster)));
  for(let i=0;i<10;i++){
    const a=pca.stability.runs[i],b=lsa.stability.runs[i];
    assert.deepEqual(a.groups,b.groups);assert.deepEqual(a.indices,b.indices);assert.equal(a.kmeans_seed,b.kmeans_seed);
    assert.equal(b.pca_components,undefined);assert.equal(b.lsa_components,5);
    const subset=records.filter(r=>b.indices.some(j=>lsa.points[j].id===r.id));
    const local=C.lsa(A.tfidf(subset).vectors,5,false),fits=await C.fitKmeans(local.scores,3,b.kmeans_seed);
    near(b.retained_variance,local.retained_variance);near(b.retained_energy,local.retained_energy);near(b.inertia,fits[0].inertia);
  }
  const repeat=await C.run(records,terms.vectors,{...settings,representation:'lsa'});assert.deepEqual(repeat,lsa);
  const displayChange=await C.run(records,terms.vectors,{...settings,representation:'lsa',umapSeed:19,neighbors:4});
  assert.deepEqual(displayChange.kmeans,lsa.kmeans);assert.deepEqual(displayChange.lsa,lsa.lsa);
  assert.deepEqual(displayChange.stability,lsa.stability);assert.deepEqual(displayChange.fidelity.representation,lsa.fidelity.representation);
  assert.notDeepEqual(displayChange.points.map(p=>p.umap),lsa.points.map(p=>p.umap));
  assert.ok((await C.run(records.slice(0,3),terms.vectors.slice(0,3),{representation:'lsa'})).skipped);
  const small=await C.run(records.slice(0,3),terms.vectors.slice(0,3),{representation:'compare'});assert.ok(small.comparison.skipped);
  const zero=await C.run([...records,{id:'empty'}],[...terms.vectors,new Map()],{representation:'lsa',k:3});assert.equal(zero.excluded[0].id,'empty');
  await assert.rejects(()=>C.run(records,terms.vectors,{...settings,representation:'compare'},async message=>{
    if(message.startsWith('LSA comparison'))throw Error('cancel alternative');
  }),/cancel alternative/);
  const result=await A.analyze({schema:'un.browser.corpus.v1',records,coverage:[]},{topic:'',start:'2026-09-22',end:'2026-09-22',region:'All regions',scope:'all',methods:['clusters'],clustering:{...settings,representation:'compare'}});
  assert.deepEqual(result.methods.clusters,comparison);
  // Render both valid and withheld comparisons using the actual page modules.
  const context=vm.createContext({});
  for(const name of ['stability-view.js','comparison-view.js','cluster-view.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../site',name),'utf8'),context);
  const rendered=context.UNClusterView.render(comparison,records,()=>'',()=>''),single=context.UNClusterView.render(lsa,records,()=>'',()=>'');
  assert.match(rendered,/PCA and LSA/);assert.match(rendered,/right map's colors are not LSA assignments/);
  assert.match(single,/LSA component vocabulary/);assert.match(single,/Neighborhood preservation/);
  assert.doesNotMatch(single,/PCA retains|PC 1/);
  assert.match(context.UNClusterView.render(small,records,()=>'',()=>''),/Both representations must yield a fit/);
  console.log('PASS LSA hand SVD, energy/variance distinction, full-rank geometry, deterministic signs, exact neighborhood metrics, paired samples/refits, unchanged PCA, standalone/comparison equivalence, display independence, exports rendering and cancellation');
})().catch(error=>{console.error(error);process.exitCode=1;});
