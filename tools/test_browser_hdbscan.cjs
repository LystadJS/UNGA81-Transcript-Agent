const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const H=require('../site/hdbscan-core.js'),C=require('../site/cluster-core.js'),S=require('../site/cluster-stability.js'),A=require('../site/analysis-core.js');
const near=(a,b,t=1e-9)=>assert.ok(Math.abs(a-b)<t,`${a} != ${b}`);
(async()=>{
  const x=[...Array.from({length:20},(_,i)=>[i%5*.01,Math.floor(i/5)*.01]),...Array.from({length:20},(_,i)=>[5+i%5*.02,5+Math.floor(i/5)*.02]),[-10,12],[20,-15],[40,30]];
  const fitted=await H.fit(x,{minClusterSize:8,minSamples:5});
  assert.equal(new Set(fitted.labels.filter(c=>c>=0)).size,2);assert.ok(fitted.labels.some(c=>c<0));
  assert.deepEqual(fitted,await H.fit(x,{minClusterSize:8,minSamples:5}));
  assert.ok(fitted.strengths.every(v=>Number.isFinite(v)&&v>=0&&v<=1));
  const condensed=fitted.diagnostics.condensed_tree;
  assert.equal(condensed.filter(e=>e.child<x.length).length,x.length);
  assert.equal(new Set(condensed.filter(e=>e.child<x.length).map(e=>e.child)).size,x.length);
  assert.equal(fitted.diagnostics.mst.length,x.length-1);
  const noise=await H.fit(x,{minClusterSize:100,minSamples:5});assert.ok(noise.labels.every(c=>c===-1));assert.ok(noise.strengths.every(v=>v===0));
  const duplicates=await H.fit([...Array(12).fill([0,0]),...Array(12).fill([4,4]),[10,10]],{minClusterSize:5,minSamples:5});
  assert.equal(new Set(duplicates.labels.filter(c=>c>=0)).size,2);assert.match(JSON.stringify(duplicates),/Infinity/);assert.ok(duplicates.strengths.every(Number.isFinite));
  const identical=await H.fit(Array(12).fill([1,1]));assert.ok(identical.labels.every(c=>c===-1));
  assert.ok((await H.fit(x,{minSamples:100})).skipped);
  await assert.rejects(()=>H.fit(x,{minClusterSize:1}));await assert.rejects(()=>H.fit([[NaN],[1],[2]],{minSamples:2}));
  await assert.rejects(()=>H.fit(x,{},async message=>{if(message.includes('condensing'))throw Error('cancel');}),/cancel/);
  assert.throws(()=>C.options({algorithm:'hdbscan',hdbscan:{minSamples:1}}));assert.throws(()=>C.options({algorithm:'hdbscan',hdbscan:{selection:'unknown'}}));

  const reference=[1,1,0,2,2],runs=[{indices:[0,1,2,3,4],labels:[-1,-1,-1,0,0]},{indices:[0,1,2],labels:[0,0,-1]}];
  const consensus=S.consensus(reference,runs,true),p=S.pairIndex(0,1);
  assert.equal(consensus.co_observed[p],2);assert.equal(consensus.co_clustered[p],1);assert.equal(consensus.co_assigned[p],1);
  assert.equal(consensus.co_clustered[S.pairIndex(0,2)],0);assert.equal(consensus.points[0].assigned,1);assert.equal(consensus.points[0].unassigned,1);
  assert.equal(consensus.points[2].margin,null);assert.equal(consensus.points[2].within_cluster,null);
  assert.equal(S.assignmentAgreement(reference,runs[0].labels).ari,null);
  assert.equal(S.assignmentAgreement(reference,[0,0,-1,1,1]).ari,1);
  const j=S.jaccards(reference,[-1,-1,-1,-1,-1],[1,2],true);assert.ok(j.every(c=>c.jaccard===0&&c.matched_cluster===null));
  near(S.jaccards(reference,[0,-1,-1,1,1],[1,2],true)[0].jaccard,.5);
  // An all-noise run is successful and contributes exposure, never co-clustering.
  const emptyConsensus=S.consensus(reference,[{indices:[0,1,2,3,4],labels:[-1,-1,-1,-1,-1]}],true);
  assert.ok(emptyConsensus.co_observed.every(v=>v===1));assert.ok(emptyConsensus.co_clustered.every(v=>v===0));

  const topics=['climate emissions solar carbon energy renewable','security weapons peace diplomacy disarmament conflict','school university education teachers literacy students'];
  const records=Array.from({length:54},(_,i)=>({id:'p'+i,text_sha256:'a'.repeat(64),text:topics[i%3]+' marker'+String.fromCharCode(97+Math.floor(i/26),97+i%26),date:'2026-09-22',country:'Affiliation '+i%6,region:'Unmapped',language:'en',scope:'general_debate',meeting:'Meeting '+Math.floor(i/9),source_url:`https://transcripts.un.org/en/asset/k/demo${Math.floor(i/9)}?t=${i}`}));
  records.splice(4,0,{...records[0],id:'empty',text:'the and'});
  const vectors=A.tfidf(records).vectors,settings={algorithm:'hdbscan',representation:'compare',components:5,hdbscan:{minClusterSize:5,minSamples:3},stability:{enabled:true,replicates:10}};
  const fit=await C.run(records,vectors,settings),baseline=await C.run(records,vectors,{...settings,algorithm:'kmeans',k:3,stability:{enabled:false}});
  for(const [got,old] of [[fit,baseline],[fit.comparison.alternative,baseline.comparison.alternative]]){
    assert.equal(got.hdbscan.assigned_count+got.hdbscan.unassigned_count,got.analyzed_count);
    assert.deepEqual(got.points.map(p=>p[got.representation]),old.points.map(p=>p[old.representation]));
    assert.deepEqual(got.points.map(p=>p.umap),old.points.map(p=>p.umap));assert.deepEqual(got.excluded,old.excluded);
    for(const run of got.stability.runs){
      assert.equal(run.assignment.assigned_count+run.assignment.unassigned_count,run.indices.length);
      const selected=new Set(run.groups.flatMap(g=>got.stability.groups[g].ids)),subset=records.filter(r=>selected.has(r.id));
      const v=A.tfidf(subset).vectors.filter(v=>v.size),rep=C.represent(v,5,got.representation,false);
      const rebuilt=await H.fit(rep.scores,settings.hdbscan);assert.deepEqual(rebuilt.labels,run.labels);
    }
  }
  const unassigned=await C.run(records,vectors,{...settings,hdbscan:{minClusterSize:600,minSamples:3}});
  assert.equal(unassigned.clustering.k,0);assert.equal(unassigned.clustering.silhouette,null);assert.equal(unassigned.comparison.between_cluster_ari,null);
  assert.equal(unassigned.stability.successful,10);assert.equal(unassigned.stability.ari.count,0);assert.equal(unassigned.stability.ari.mean,null);
  assert.ok(unassigned.stability.consensus.co_clustered.every(v=>v===0));assert.ok(unassigned.stability.consensus.co_assigned.every(v=>v===0));
  assert.ok(unassigned.points.every(p=>p.cluster===0&&p.assignment_status==='unassigned'));
  assert.equal(unassigned.hdbscan.unassigned_ids.length,54);assert.ok(!unassigned.hdbscan.unassigned_ids.includes('empty'));
  const repeat=await C.run(records,vectors,{...settings,seed:991,k:12});assert.deepEqual(repeat.points,fit.points);assert.deepEqual(repeat.stability,fit.stability);
  const context=vm.createContext({});
  for(const name of ['stability-view.js','comparison-view.js','hierarchy-view.js','cluster-view.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../site',name),'utf8'),context);
  const html=context.UNClusterView.render(unassigned,records,()=>'',()=>'');assert.match(html,/No groups met these settings/);assert.match(html,/Unassigned passages/);assert.doesNotMatch(html,/NaN|undefined|Infinity%|k-means assignments/);
  console.log('PASS HDBSCAN dense groups/noise, duplicates, all-noise success, bounds, deterministic fitting, cancellation, explicit exclusions, representation/UMAP invariance, exact group refits, noise-aware ARI/Jaccard/pair denominators and all-noise rendering');
})().catch(error=>{console.error(error);process.exitCode=1;});
