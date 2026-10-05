const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const B=require('../site/cluster-algorithms.js'),C=require('../site/cluster-core.js'),A=require('../site/analysis-core.js');
const near=(a,b,t=1e-9)=>assert.ok(Math.abs(a-b)<t,`${a} != ${b}`);
const distance=(a,b)=>Math.sqrt(a.reduce((sum,v,i)=>sum+(v-b[i])**2,0));
const cost=(x,medoids)=>x.reduce((sum,row)=>sum+Math.min(...medoids.map(i=>distance(row,x[i]))),0);
// Independent deliberately slow PAM: enumerate every replacement and recompute
// all distances. Validates the shared-delta optimization, including BUILD.
function brutePam(x,k){
  let medoids=[];
  while(medoids.length<k){
    const choices=x.map((_,i)=>i).filter(i=>!medoids.includes(i));
    choices.sort((a,b)=>cost(x,[...medoids,a])-cost(x,[...medoids,b])||a-b);
    medoids.push(choices[0]);
  }
  medoids.sort((a,b)=>a-b);
  for(let step=0;step<300;step++){
    const objective=cost(x,medoids);let best=objective-1e-12*Math.max(1,objective),replacement=null;
    for(let h=0;h<x.length;h++)if(!medoids.includes(h))for(let m=0;m<k;m++){
      const candidate=medoids.map((v,i)=>i===m?h:v),value=cost(x,candidate);
      if(value<best){best=value;replacement=candidate;}
    }
    if(!replacement)return {medoids,objective};medoids=replacement.sort((a,b)=>a-b);
  }
  throw Error('Reference did not converge');
}
(async()=>{
  let swapped=0;const random=C.rng(72309);
  for(let example=0;example<40;example++){
    const x=Array.from({length:12+example%7},()=>Array.from({length:3},()=>random()*10)),k=2+example%3;
    const fit=await B.pam(x,k),reference=brutePam(x,k);
    near(fit.diagnostics.total_distance,reference.objective);swapped+=fit.diagnostics.swaps;
    near(cost(x,fit.medoids),fit.diagnostics.total_distance);
    fit.labels.forEach((c,i)=>near(distance(x[i],x[fit.medoids[c]]),Math.min(...fit.medoids.map(m=>distance(x[i],x[m])))));
    for(let i=1;i<fit.diagnostics.objective_history.length;i++)assert.ok(fit.diagnostics.objective_history[i]<fit.diagnostics.objective_history[i-1]);
    for(const m of fit.medoids)for(let h=0;h<x.length;h++)if(!fit.medoids.includes(h))assert.ok(cost(x,fit.medoids.map(v=>v===m?h:v))>=fit.diagnostics.total_distance-1e-9);
  }
  assert.ok(swapped>0,'Fixture must exercise actual SWAP steps');
  const line=[[0],[1],[10],[12]],average=await B.hierarchical(line,2,'average'),ward=await B.hierarchical(line,2,'ward');
  assert.deepEqual(average.labels,[0,0,1,1]);assert.deepEqual(ward.labels,average.labels);
  [1,2,10.5].forEach((v,i)=>near(average.diagnostics.merges[i].height,v));
  [1,2,Math.sqrt(220.5)].forEach((v,i)=>near(ward.diagnostics.merges[i].height,v));
  // Ward's sum of squared heights / 2 equals total centered sum of squares.
  near(ward.diagnostics.merges.reduce((s,m)=>s+m.height**2/2,0),line.reduce((s,r)=>s+(r[0]-5.75)**2,0));
  const finer=await B.hierarchical(line,3,'average');
  for(let i=0;i<4;i++)for(let j=0;j<4;j++)if(finer.labels[i]===finer.labels[j])assert.equal(average.labels[i],average.labels[j]);
  const tied=await B.hierarchical([[1],[1],[1],[1]],2,'ward');assert.equal(tied.diagnostics.tied_cut,true);assert.equal(new Set(tied.labels).size,2);
  assert.deepEqual(tied,await B.hierarchical([[1],[1],[1],[1]],2,'ward'));
  assert.equal((await B.pam([[0],[0],[1],[1]],3)).converged,false);
  for(const x of [[],[[NaN],[1],[2]],[[1],[2,3],[4]]])await assert.rejects(()=>B.pam(x,2));
  await assert.rejects(()=>B.hierarchical(line,2,'cosine'));
  assert.throws(()=>C.options({algorithm:'unknown'}));assert.throws(()=>C.options({linkage:'single'}));
  for(const fn of [()=>B.pam(line,2,async()=>{throw Error('cancel PAM');}),()=>B.hierarchical(line,2,'ward',async()=>{throw Error('cancel HC');})])await assert.rejects(fn,/cancel/);

  const topics=['climate emissions carbon renewable solar energy','security weapons conflict disarmament peace diplomacy','education school teachers literacy university learning'];
  const records=Array.from({length:42},(_,i)=>({id:'row'+i,text_sha256:'a'.repeat(64),text:topics[i%3]+' token'+String.fromCharCode(97+Math.floor(i/26),97+i%26),country:'Affiliation '+(i%5),region:'Unmapped',date:'2026-09-22',language:'en',scope:'general_debate',meeting:'Meeting '+Math.floor(i/7),source_url:`https://transcripts.un.org/en/asset/k/test${Math.floor(i/7)}?t=${i}`}));
  records.splice(5,0,{...records[0],id:'empty',text:'the and'});
  const vectors=A.tfidf(records).vectors,settings={representation:'compare',components:5,k:3,stability:{enabled:true,replicates:10}};
  const base=await C.run(records,vectors,settings),fits=[];
  for(const options of [{algorithm:'pam'},{algorithm:'hierarchical',linkage:'ward'},{algorithm:'hierarchical',linkage:'average'}]){
    const fit=await C.run(records,vectors,{...settings,...options});fits.push(fit);
    assert.equal(fit.comparison.paired_stability.count,10);
    for(const [got,old] of [[fit,base],[fit.comparison.alternative,base.comparison.alternative]]){
      const method=got.representation;assert.ok(!got.kmeans);assert.equal(got.algorithm,options.algorithm);
      assert.deepEqual(got.points.map(p=>p[method]),old.points.map(p=>p[method]));
      assert.deepEqual(got.points.map(p=>p.umap),old.points.map(p=>p.umap));
      assert.deepEqual(got.fidelity,old.fidelity);assert.deepEqual(got.excluded,old.excluded);
      assert.deepEqual(got.stability.runs.map(r=>r.groups),old.stability.runs.map(r=>r.groups));
      assert.equal(got.stability.algorithm,options.algorithm);
      got.clusters.forEach(c=>assert.equal(got.points.find(p=>p.id===c.representative_id).cluster,c.cluster));
      if(got.pam)assert.deepEqual(got.pam.medoid_ids,got.clusters.map(c=>c.representative_id));
      if(got.hierarchical){assert.equal(got.hierarchical.merges.length,got.points.length-1);assert.deepEqual(got.hierarchical.leaf_ids,got.points.map(p=>p.id));}
      for(const run of got.stability.runs){
        assert.equal(run.kmeans_seed,undefined);assert.equal(run.inertia,undefined);
        const selected=new Set(run.groups.flatMap(g=>got.stability.groups[g].ids));
        const subset=records.filter(r=>selected.has(r.id)),tfidf=A.tfidf(subset);
        const keep=tfidf.vectors.flatMap((v,i)=>v.size?[i]:[]);
        const scores=C.represent(keep.map(i=>tfidf.vectors[i]),settings.components,method,false).scores;
        const rebuilt=await C.fitPartition(scores,{...settings,...options,representation:method});
        assert.deepEqual(run.labels,rebuilt.labels);near(run.ari,C.ari(run.indices.map(i=>got.points[i].cluster),run.labels));
        if(run.pam)near(run.pam.total_distance,rebuilt.diagnostics.total_distance);
        else near(run.hierarchical.cut_height,rebuilt.diagnostics.cut_height);
      }
    }
    const rerun=await C.run(records,vectors,{...settings,...options,seed:900});assert.deepEqual(rerun.points,fit.points);assert.deepEqual(rerun.stability,fit.stability);
    const single=await C.run(records,vectors,{...settings,...options,representation:'lsa'});assert.deepEqual(single,fit.comparison.alternative);
    const entry=await A.analyze({schema:'un.browser.corpus.v1',records,coverage:[]},{topic:'',start:'2026-09-22',end:'2026-09-22',region:'All regions',scope:'all',methods:['clusters'],clustering:{...settings,...options}});
    assert.deepEqual(entry.methods.clusters,fit);
  }
  const context=vm.createContext({});
  for(const name of ['stability-view.js','comparison-view.js','hierarchy-view.js','cluster-view.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../site',name),'utf8'),context);
  for(const fit of fits){const html=context.UNClusterView.render(fit,records,()=>'',()=>'');assert.doesNotMatch(html,/k-means|K-means inertia/);assert.match(html,fit.pam?/PAM medoid/:/Full passage dendrogram/);}
  // Degenerate grouped samples: valid full PAM has three distinct locations;
  // each two-group refit has only two, so none may enter consensus denominators.
  const degenerate=Array.from({length:18},(_,i)=>({...records[0],id:'deg'+i,
    text:topics[Math.floor(i/6)],meeting:'Group '+Math.floor(i/6),source_url:`https://transcripts.un.org/en/asset/g/${Math.floor(i/6)}`}));
  const withheld=await C.run(degenerate,A.tfidf(degenerate).vectors,{algorithm:'pam',k:3,components:3,stability:{enabled:true,replicates:10,fraction:0.5}});
  assert.ok(withheld.points);assert.equal(withheld.stability.successful,0);assert.ok(withheld.stability.skipped);
  assert.ok(withheld.stability.runs.every(r=>r.skipped));assert.ok(withheld.stability.consensus.co_observed.every(n=>n===0));
  assert.ok(!withheld.stability.ari);
  console.log(`PASS PAM against 40 independent exhaustive BUILD/SWAP fixtures (${swapped} improving swaps); Ward/average hand heights, nested/tied cuts, input gates, cancellation; both representations, refit identity, shared group schedule, medoid/source mapping, unchanged coordinates and default k-means, report rendering`);
})().catch(error=>{console.error(error);process.exitCode=1;});
