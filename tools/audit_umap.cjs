/* Freeze retained scores and memberships; vary only UMAP display settings. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const C=require('../site/cluster-core.js'),M=require('../site/representation-metrics.js'),N=require('../site/numerics.js');
const hash=v=>crypto.createHash('sha256').update(JSON.stringify(v)).digest('hex');
function distanceError(high,low){
  let hh=0,ll=0,hl=0;for(let i=1;i<high.length;i++)for(let j=0;j<i;j++){const h=Math.sqrt(high[i][j]),l=Math.sqrt(low[i][j]);hh+=h*h;ll+=l*l;hl+=h*l;}
  const scale=ll?hl/ll:0;let error=0;for(let i=1;i<high.length;i++)for(let j=0;j<i;j++)error+=(Math.sqrt(high[i][j])-scale*Math.sqrt(low[i][j]))**2;
  return {scale,relative_distance_error:hh?Math.sqrt(error/hh):null,pairs:high.length*(high.length-1)/2};
}
function compact({points,...values}){return values;}
async function run(directory,output){
  const results={schema:'un.umap-sensitivity.v1',protocol:{seeds:[7,42,2026],neighbors:[5,15,30,50],min_dist:.1,epochs:300,evaluation_neighbors:10,metric:'Euclidean on frozen retained scores',reference:{seed:42,neighbors:15},scope:'Six frozen policy/representation matrices; Gaussian mixture assignments are never refitted or supplied to UMAP. Three seeds are a sensitivity grid, not uncertainty intervals.'},fits:[]};
  for(const policy of ['full','substantive','inclusive']){
    const input=path.join(directory,policy+'-diag.json'),bytes=fs.readFileSync(input),fit=JSON.parse(bytes).methods.clusters;
    for(const f of [fit,fit.comparison.alternative]){
      const x=f.points.map(p=>p[f.representation]),ids=f.points.map(p=>p.id),memberships=f.points.map(p=>p.memberships),before=hash({x,ids,memberships});
      const high=M.denseDistances(x),order=M.order(high),baseline=M.order(M.denseDistances(f.points.map(p=>p.umap)));
      const entry={policy,representation:f.representation,passages:x.length,dimensions:x[0].length,input_sha256:crypto.createHash('sha256').update(bytes).digest('hex'),frozen_state_sha256:before,ids,scores:x,labels:f.points.map(p=>p.cluster),runs:[],seed_comparisons:[]};
      for(const neighbors of results.protocol.neighbors)for(const seed of results.protocol.seeds){
        const umap=new N.UMAP({nComponents:2,nNeighbors:neighbors,minDist:.1,spread:1,nEpochs:300,random:C.rng(seed)}),count=umap.initializeFit(x);
        for(let i=0;i<count;i++)umap.step();const coordinates=umap.getEmbedding();
        assert.ok(coordinates.every(r=>r.length===2&&r.every(Number.isFinite)));
        if(neighbors===15&&seed===42)assert.deepEqual(coordinates,f.points.map(p=>p.umap),'Reference display changed');
        const low=M.denseDistances(coordinates),rank=M.order(low);
        entry.runs.push({neighbors,seed,coordinates,fidelity:compact(M.agreement(order,rank,10)),reference_layout_overlap:M.agreement(baseline,rank,10).neighbor_overlap,...distanceError(high,low)});
      }
      for(const neighbors of results.protocol.neighbors){const runs=entry.runs.filter(r=>r.neighbors===neighbors);
        for(let a=0;a<runs.length;a++)for(let b=0;b<a;b++)entry.seed_comparisons.push({neighbors,seeds:[runs[b].seed,runs[a].seed],overlap:M.agreement(M.order(M.denseDistances(runs[b].coordinates)),M.order(M.denseDistances(runs[a].coordinates)),10).neighbor_overlap});
      }
      assert.equal(hash({x,ids,memberships}),before);entry.frozen_memberships_unchanged=true;results.fits.push(entry);
      console.log(JSON.stringify({policy,representation:f.representation,layouts:entry.runs.length,overlap_range:[Math.min(...entry.runs.map(r=>r.fidelity.neighbor_overlap)),Math.max(...entry.runs.map(r=>r.fidelity.neighbor_overlap))],seed_overlap_range:[Math.min(...entry.seed_comparisons.map(r=>r.overlap)),Math.max(...entry.seed_comparisons.map(r=>r.overlap))]}));
    }
  }
  fs.writeFileSync(output,JSON.stringify(results)+'\n');return results;
}
if(require.main===module)run(...process.argv.slice(2)).catch(e=>{console.error(e);process.exitCode=1;});
module.exports={run,distanceError};
