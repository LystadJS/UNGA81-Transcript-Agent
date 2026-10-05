const assert=require('node:assert/strict');
const A=require('../site/analysis-core.js'),C=require('../site/cluster-core.js');
const S=require('../site/cluster-stability.js'),V=require('../site/stability-view.js');
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-10,`${a} != ${b}`);

(async()=>{
  // Independent small contingency tables and explicit pair-count arithmetic.
  near(C.ari([0,0,1,1],[0,1,0,1]),-0.5);
  near(C.ari([0,0,1,1],[1,1,0,0]),1);
  assert.equal(C.ari([],[]),1);assert.throws(()=>C.ari([1],[]));
  const overlap=S.jaccards([1,1,2,2],[0,1,1,1],[1,2,3]);
  near(overlap[0].jaccard,0.5);near(overlap[1].jaccard,2/3);assert.equal(overlap[2].jaccard,null);
  const cons=S.consensus([1,1,2,2],[
    {indices:[0,1,2],labels:[0,0,1]},
    {indices:[1,2,3],labels:[0,0,1]},
    {indices:[0,3],labels:[0,0],skipped:'failed'}
  ]);
  assert.deepEqual(cons.co_observed,[1,1,2,0,1,1]);
  assert.deepEqual(cons.co_clustered,[1,0,1,0,0,0]);
  assert.equal(cons.pair_coverage.never_observed,1);
  assert.deepEqual(cons.points.map(p=>p.included),[1,2,2,1]);
  near(cons.points[1].within_cluster,1);near(cons.points[1].strongest_other,1/3);
  assert.equal(S.consensus([1,2],[{indices:[0],labels:[0]}]).points[0].margin,null);

  const themes=['climate emissions carbon renewable solar transition energy',
    'security weapons conflict disarmament peace ceasefire diplomacy',
    'education school teachers literacy students university learning'];
  const data=Array.from({length:48},(_,i)=>({
    id:`m${Math.floor(i/6)}#${i%6}`,text_sha256:'a'.repeat(64),
    text:themes[i%3]+' '+themes[i%3]+' unique'+String.fromCharCode(97+Math.floor(i/26),97+i%26),
    date:'2026-09-22',country:'Affiliation '+(i%6),region:'Unmapped',language:'en',scope:'general_debate',
    meeting:'Meeting '+Math.floor(i/6),source_url:`https://transcripts.un.org/en/asset/k/test${Math.floor(i/6)}?t=${i}`
  }));
  const snapshot=JSON.stringify(data),terms=A.tfidf(data);
  const settings={k:3,components:8,stability:{enabled:true,replicates:10,fraction:0.75}};
  const fit=await C.run(data,terms.vectors,settings),s=fit.stability;
  assert.equal(s.successful,10);assert.equal(s.group_count,8);assert.equal(s.sample_group_count,6);
  assert.ok(s.clusters.every(c=>c.mean>0.8));
  const rerun=await C.run(data,terms.vectors,settings);assert.deepEqual(rerun,fit);
  const noStability=await C.run(data,terms.vectors,{k:3,components:8});
  assert.deepEqual(noStability.points,fit.points);assert.deepEqual(noStability.pca,fit.pca);
  assert.deepEqual(noStability.kmeans,fit.kmeans);assert.deepEqual(noStability.umap,fit.umap);
  const changedDisplay=await C.run(data,terms.vectors,{...settings,umapSeed:123,neighbors:5,minDist:0.4});
  assert.deepEqual(changedDisplay.stability,s);
  assert.equal(JSON.stringify(data),snapshot);
  for(const r of s.runs){
    const ids=r.indices.map(i=>s.reference_ids[i]);
    for(const group of s.groups){const count=group.ids.filter(id=>ids.includes(id)).length;assert.ok(count===0||count===group.ids.length);}
    const subset=data.filter(row=>ids.includes(row.id)),localTerms=A.tfidf(subset);
    assert.equal(r.vocabulary,localTerms.vocabulary);assert.ok(r.vocabulary<terms.vocabulary);
    // Independently rebuild the refit, rather than retaining full-data scores.
    const pca=C.pca(localTerms.vectors,8),km=await C.fitKmeans(pca.scores,3,r.kmeans_seed);
    near(km[0].inertia,r.inertia);assert.deepEqual(km[0].labels,r.labels);
  }
  // Reconstruct every denominator from the exported, successful resample log.
  for(let i=1;i<48;i++)for(let j=0;j<i;j++){
    let observed=0,together=0;
    for(const r of s.runs){if(r.skipped)continue;const a=r.indices.indexOf(i),b=r.indices.indexOf(j);
      if(a>=0&&b>=0){observed++;together+=r.labels[a]===r.labels[b]?1:0;}}
    assert.equal(s.consensus.co_observed[S.pairIndex(i,j)],observed);
    assert.equal(s.consensus.co_clustered[S.pairIndex(i,j)],together);
  }
  const other=await S.run(data,{...fit,parameters:{...fit.parameters,stability:{...fit.parameters.stability,unit:'affiliation',seed:88}}});
  assert.equal(other.group_count,6);assert.notDeepEqual(other.runs.map(r=>r.indices),s.runs.map(r=>r.indices));
  const twoGroups=data.map((r,i)=>({...r,source_url:`https://transcripts.un.org/en/asset/k/${i%2}`}));
  assert.match((await S.run(twoGroups,fit)).skipped,/at least three/);
  const missing=data.map(r=>({...r,source_url:'https://example.org/',meeting:''}));
  assert.match((await S.run(missing,fit)).skipped,/meeting title/);
  const imported=S.groupRecords(data.map(r=>({...r,source_url:'https://example.org/'})),'meeting');
  assert.equal(imported.groups.length,8);assert.equal(imported.fallback,48);
  const unidentified=S.groupRecords(data.map(r=>({...r,country:'Unidentified'})),'affiliation');
  assert.equal(unidentified.groups.length,1);assert.equal(unidentified.unknown,48);
  const sparseFit={...fit,parameters:{...fit.parameters,k:12},points:fit.points.slice(0,12),clusters:fit.clusters};
  const failed=await S.run(data,sparseFit);assert.ok(failed.skipped);assert.equal(failed.successful,0);
  assert.ok(failed.consensus.co_observed.every(v=>v===0));
  const stopped=[];
  await assert.rejects(()=>S.run(data,fit,async m=>{stopped.push(m);throw Error('cancel');}),/cancel/);
  assert.equal(stopped.length,1);
  for(const bad of [{replicates:9},{replicates:101},{fraction:1},{fraction:0.4},{seed:-1},{unit:'passage'},{enabled:'yes'}]){
    assert.throws(()=>C.options({stability:{enabled:true,...bad}}));
    assert.throws(()=>A.parameters({topic:'',start:'2026-09-22',end:'2026-09-23',region:'All regions',scope:'all',methods:['clusters'],clustering:{stability:{enabled:true,...bad}}}));
  }
  const corpus={schema:'un.browser.corpus.v1',records:data,coverage:[]};
  const analyzed=await A.analyze(corpus,{topic:'',start:'2026-09-22',end:'2026-09-22',region:'All regions',scope:'all',methods:['clusters'],clustering:settings});
  assert.deepEqual(analyzed.methods.clusters.stability,s);
  // Export views escape source content and represent missing comparisons as gray.
  const view=V.render(s,data,(heads,rows)=>JSON.stringify({heads,rows}));
  assert.match(view,/Consensus heatmap/);assert.match(view,/not confidence intervals/);
  assert.match(view,/Open original source/);assert.match(view,/Resampling record/);
  const html=V.heatmap({...s,consensus:cons,reference_ids:['a','b','c','d'],reference_clusters:[1,1,2,2]}).html;
  assert.match(html,/#d6dce2/);assert.match(html,/never observed/);
  console.log('PASS group subsampling, full TF-IDF/PCA refits, ARI/Jaccard references, consensus denominators, missing pairs, deterministic seeds, display independence, grouping fallbacks, failed-fit accounting, cancellation, option bounds and analysis integration');
})().catch(error=>{console.error(error);process.exitCode=1;});
