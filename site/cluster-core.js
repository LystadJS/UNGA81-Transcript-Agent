/* TF-IDF -> PCA or LSA scores -> selected clustering; UMAP displays the scores. */
(function(root) {
  'use strict';
  const N = typeof module !== 'undefined' && module.exports ? require('./numerics.js') : root.UNNumerics;
  const O = typeof module !== 'undefined' && module.exports ? require('./cluster-options.js') : root.UNClusterOptions;
  const L = typeof module !== 'undefined' && module.exports ? require('./lsa-core.js') : root.UNLSA;
  const M = typeof module !== 'undefined' && module.exports ? require('./representation-metrics.js') : root.UNRepresentationMetrics;
  const B = typeof module !== 'undefined' && module.exports ? require('./cluster-algorithms.js') : root.UNClusterAlgorithms;
  const {DEFAULTS, options} = O;
  const MAX_RECORDS = 600;
  // Mulberry32: local generators prevent UMAP from consuming k-means random state.
  function rng(seed) {let a=seed>>>0;return ()=>{a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;};}
  const d2 = (a,b) => a.reduce((sum,x,i)=>sum+(x-b[i])**2,0);
  function pca(vectors, requested) {
    const n=vectors.length, postings=new Map();
    vectors.forEach((v,i)=>{for(const [term,w] of v){if(!postings.has(term))postings.set(term,[]);postings.get(term).push([i,w]);}});
    const gram=Array.from({length:n},()=>new Float64Array(n));
    for(const rows of postings.values())for(let a=0;a<rows.length;a++)for(let b=0;b<=a;b++){
      const [i,x]=rows[a],[j,y]=rows[b];gram[i][j]+=x*y;if(i!==j)gram[j][i]+=x*y;
    }
    const means=gram.map(row=>row.reduce((a,b)=>a+b,0)/n),grand=means.reduce((a,b)=>a+b,0)/n;
    for(let i=0;i<n;i++)for(let j=0;j<n;j++)gram[i][j]-=means[i]+means[j]-grand;
    const eigen=new N.EigenvalueDecomposition(new N.Matrix(gram.map(r=>Array.from(r))),{assumeSymmetric:true});
    const sorted=eigen.realEigenvalues.map((v,i)=>({v,i})).sort((a,b)=>b.v-a.v);
    const tolerance=Math.max(1e-12, Math.max(0,sorted[0].v)*1e-10);
    if(sorted.some(x=>x.v < -100*tolerance))throw Error('PCA decomposition failed its numerical check.');
    const positive=sorted.filter(x=>x.v>tolerance),total=sorted.reduce((sum,x)=>sum+Math.max(0,x.v),0);
    const chosen=positive.slice(0,requested),scores=Array.from({length:n},()=>[]);
    for(const {v,i} of chosen){let anchor=0;for(let r=1;r<n;r++)if(Math.abs(eigen.eigenvectorMatrix.get(r,i))>Math.abs(eigen.eigenvectorMatrix.get(anchor,i)))anchor=r;
      const sign=eigen.eigenvectorMatrix.get(anchor,i)<0?-1:1;
      for(let r=0;r<n;r++)scores[r].push(sign*Math.sqrt(v)*eigen.eigenvectorMatrix.get(r,i));
    }
    return {scores,rank:positive.length,components:chosen.length,requested_components:requested,
      eigenvalues:chosen.map(x=>x.v/(n-1)),explained_variance_ratio:chosen.map(x=>x.v/total),
      retained_variance:chosen.reduce((sum,x)=>sum+x.v,0)/(total||1),vocabulary:postings.size,
      centering:'Feature means subtracted; no feature standardization or whitening',solver:'ml-matrix 6.15.0 symmetric eigendecomposition of centered Gram matrix'};
  }
  function oneKmeans(x,k,random) {
    const centers=[x[Math.floor(random()*x.length)].slice()];
    while(centers.length<k){const weights=x.map(row=>Math.min(...centers.map(c=>d2(row,c)))),sum=weights.reduce((a,b)=>a+b,0);
      if(sum<=1e-20)return null;
      let draw=random()*sum,index=weights.length-1;for(let i=0;i<weights.length;i++){draw-=weights[i];if(draw<0){index=i;break;}}centers.push(x[index].slice());
    }
    let labels=Array(x.length).fill(-1),converged=false,iterations=0;
    for(;iterations<300;iterations++){
      const next=x.map(row=>{let best=0;for(let j=1;j<k;j++)if(d2(row,centers[j])<d2(row,centers[best]))best=j;return best;});
      const counts=Array(k).fill(0);next.forEach(j=>counts[j]++);
      for(let j=0;j<k;j++)if(!counts[j]){
        let far=-1,dist=-1;for(let i=0;i<x.length;i++)if(counts[next[i]]>1&&d2(x[i],centers[next[i]])>dist){far=i;dist=d2(x[i],centers[next[i]]);}
        if(far<0||dist<=1e-20)return null;counts[next[far]]--;next[far]=j;counts[j]++;
      }
      const sums=Array.from({length:k},()=>Array(x[0].length).fill(0));
      x.forEach((row,i)=>row.forEach((v,d)=>{sums[next[i]][d]+=v;}));
      for(let j=0;j<k;j++)centers[j]=sums[j].map(v=>v/counts[j]);
      converged=next.every((v,i)=>v===labels[i]);labels=next;if(converged){iterations++;break;}
    }
    return {labels,centers,iterations,converged,inertia:x.reduce((sum,row,i)=>sum+d2(row,centers[labels[i]]),0)};
  }
  function ari(a,b){if(a.length!==b.length)throw Error('ARI requires paired labels.');if(a.length<2)return 1;
    const rows=new Map(),cols=new Map(),cells=new Map(),choose=n=>n*(n-1)/2;
    a.forEach((v,i)=>{rows.set(v,(rows.get(v)||0)+1);cols.set(b[i],(cols.get(b[i])||0)+1);const key=v+','+b[i];cells.set(key,(cells.get(key)||0)+1);});
    const sum=m=>[...m.values()].reduce((s,v)=>s+choose(v),0),expected=sum(rows)*sum(cols)/choose(a.length),max=(sum(rows)+sum(cols))/2;
    return Math.abs(max-expected)<1e-15?1:(sum(cells)-expected)/(max-expected);
  }
  async function fitKmeans(x,k,seed,progress=async()=>{}) {
    const runs=[];
    for(let start=0;start<10;start++){
      await progress(`k-means · start ${start+1} of 10`);
      const fit=oneKmeans(x,k,rng((seed+Math.imul(start,0x9e3779b9))>>>0));
      if(fit?.converged)runs.push(fit);
    }
    runs.sort((a,b)=>a.inertia-b.inertia);
    return runs;
  }
  function silhouette(x,labels){let total=0;const k=Math.max(...labels)+1;
    for(let i=0;i<x.length;i++){const sums=Array(k).fill(0),counts=Array(k).fill(0);
      for(let j=0;j<x.length;j++)if(i!==j){sums[labels[j]]+=Math.sqrt(d2(x[i],x[j]));counts[labels[j]]++;}
      if(!counts[labels[i]])continue;
      const a=sums[labels[i]]/counts[labels[i]],b=Math.min(...sums.map((s,c)=>c!==labels[i]&&counts[c]?s/counts[c]:Infinity));total+=(b-a)/(Math.max(a,b)||1);
    }return total/x.length;
  }
  function represent(vectors,components,method='pca',descriptors=true){
    if(!['pca','lsa'].includes(method))throw Error('Unknown text representation.');
    return method==='lsa'?L.lsa(vectors,components,descriptors):pca(vectors,components);
  }
  const algorithmName=o=>o.algorithm==='pam'?'PAM':o.algorithm==='hierarchical'?`Hierarchical (${o.linkage})`:'k-means';
  async function fitPartition(x,value,progress=async()=>{}){
    const o=options(value);
    if(o.algorithm==='kmeans'){
      const runs=await fitKmeans(x,o.k,o.seed,progress);
      if(!runs.length)return {skipped:'k-means could not form the requested number of stable non-empty clusters. Reduce the cluster count.'};
      const best=runs[0],agreement=runs.map(r=>ari(best.labels,r.labels));
      return {...best,diagnostics:{initialization:'k-means++',starts:10,converged_starts:runs.length,max_iterations:300,
        iterations:best.iterations,inertia:best.inertia,centroids:best.centers,restart_inertia:runs.map(r=>r.inertia),
        mean_ari_to_selected:agreement.reduce((a,b)=>a+b,0)/agreement.length,min_ari_to_selected:Math.min(...agreement)}};
    }
    const fit=o.algorithm==='pam'?await B.pam(x,o.k,progress):await B.hierarchical(x,o.k,o.linkage,progress);
    return fit.converged?fit:{skipped:fit.reason};
  }
  async function runSingle(records,rawVectors,value={},progress=async()=>{}) {
    const o=options(value),method=o.representation,name=method.toUpperCase(),algorithm=algorithmName(o);
    const base={schema:'un.text-clusters.v1',representation:method,algorithm:o.algorithm,parameters:o,sequence:['TF-IDF',name,algorithm,'UMAP'],input_count:records.length};
    if(records.length>MAX_RECORDS)return {...base,skipped:`Clustering supports at most ${MAX_RECORDS} selected passages. Narrow the dates, topic or region; no sampling was applied.`};
    const vectors=rawVectors.map(v=>v instanceof Map?v:new Map(v)),keep=[],excluded=[];
    vectors.forEach((v,i)=>{if(v.size)keep.push(i);else excluded.push({id:records[i].id,reason:'No terms remain after token and stop-word filtering'});});
    if(keep.length<4)return {...base,excluded,skipped:'Clustering needs at least four passages with usable terms.'};
    if(o.k>=keep.length)return {...base,excluded,skipped:'Choose fewer clusters than usable passages.'};
    const selected=keep.map(i=>records[i]),v=keep.map(i=>vectors[i]);
    await progress(name+' · representing the selected text');const representation=represent(v,o.components,method);
    if(!representation.rank)return {...base,excluded,skipped:'The TF-IDF vectors have no measurable variation.'};
    const x=representation.scores,best=await fitPartition(x,o,progress);
    if(best.skipped)return {...base,excluded,skipped:best.skipped};
    await progress('Checking clustering separation');const sil=silhouette(x,best.labels);
    const summaries=Array.from({length:o.k},(_,c)=>{const indices=best.labels.flatMap((label,i)=>label===c?[i]:[]),terms=new Map();
      const center=best.centers?.[c]||x[0].map((_,d)=>indices.reduce((sum,i)=>sum+x[i][d],0)/indices.length);
      for(const i of indices)for(const [term,w] of v[i])terms.set(term,(terms.get(term)||0)+w);
      const representative=best.medoids?.[c]??indices.reduce((a,i)=>d2(x[i],center)<d2(x[a],center)?i:a,indices[0]);
      return {cluster:c+1,size:indices.length,representative_id:selected[representative].id,representative_role:o.algorithm==='pam'?'PAM medoid':'Nearest passage to the cluster centroid',terms:[...terms].map(([term,sum])=>({term,mean:sum/indices.length})).sort((a,b)=>b.mean-a.mean||a.term.localeCompare(b.term)).slice(0,8)};
    });
    const neighbors=Math.min(o.neighbors,x.length-1),epochs=300;
    // Fit to retained scores without labels; assignments never depend on this display.
    await progress('UMAP · preparing the display');
    const umap=new N.UMAP({nComponents:2,nNeighbors:neighbors,minDist:o.minDist,spread:1,nEpochs:epochs,random:rng(o.umapSeed)});
    const count=umap.initializeFit(x);
    for(let epoch=0;epoch<count;epoch++){umap.step();if(epoch%10===0)await progress(`UMAP · display iteration ${epoch+1} of ${count}`);}
    const layout=umap.getEmbedding();if(layout.some(row=>row.length!==2||row.some(v=>!Number.isFinite(v))))throw Error('UMAP returned an invalid display.');
    await progress(name+' · checking neighborhood preservation');
    const result={...base,excluded,analyzed_count:x.length,[method]:{...representation,scores:undefined},
      clustering:{algorithm:o.algorithm,name:algorithm,k:o.k,silhouette:sil,metric:`Euclidean on retained, unwhitened ${name} scores`},
      [o.algorithm]:{k:o.k,...best.diagnostics,silhouette:sil,metric:`Euclidean on retained, unwhitened ${name} scores`,
        ...(o.algorithm==='pam'?{medoid_ids:best.medoids.map(i=>selected[i].id)}:{}),
        ...(o.algorithm==='hierarchical'?{leaf_ids:selected.map(r=>r.id)}:{})},
      umap:{library:'umap-js 1.4.0',neighbors,requested_neighbors:o.neighbors,min_dist:o.minDist,spread:1,epochs:count,seed:o.umapSeed,metric:`Euclidean on the same ${name} scores`,initialization:'random',role:'Display only; no labels supplied'},
      fidelity:M.assess(v,x,layout,selected.map(r=>r.id)),
      clusters:summaries,points:selected.map((r,i)=>({id:r.id,text_sha256:r.text_sha256,cluster:best.labels[i]+1,[method]:x[i],umap:layout[i]}))};
    if(o.stability.enabled){
      const S=typeof module!=='undefined'&&module.exports?require('./cluster-stability.js'):root.UNClusterStability;
      result.stability=await S.run(records,result,progress);
    }
    return result;
  }
  function compareFits(left,right){
    const base={schema:'un.representation-comparison.v1',alternative:right,
      protocol:'Same selected rows, TF-IDF, requested dimensions, clustering algorithm/settings and group schedule; each representation fitted independently; no automatic winner selected'};
    if(left.skipped||right.skipped)return {...base,skipped:'Both representations must yield a fit for comparison. See each result for its reason.'};
    if(left.points.length!==right.points.length||left.points.some((p,i)=>p.id!==right.points[i].id))throw Error('Representation comparison requires identical passage order.');
    const matrix=Array.from({length:left.clustering.k},()=>Array(right.clustering.k).fill(0));
    left.points.forEach((p,i)=>{matrix[p.cluster-1][right.points[i].cluster-1]++;});
    const neighbors=left.fidelity.representation.neighbors;
    const pointComparisons=left.fidelity.representation.points.map((p,i)=>{
      const q=right.fidelity.representation.points[i];
      return {id:p.id,pca_cluster:left.points[i].cluster,lsa_cluster:right.points[i].cluster,
        pca_neighbors:p.reduced_neighbors,lsa_neighbors:q.reduced_neighbors,
        neighbor_overlap:p.reduced_neighbors.filter(id=>q.reduced_neighbors.includes(id)).length/neighbors};
    });
    const paired=[];
    if(left.stability?.runs&&right.stability?.runs){
      const rightRuns=new Map(right.stability.runs.map(r=>[r.attempt,r]));
      for(const r of left.stability.runs){const q=rightRuns.get(r.attempt);
        if(!q||JSON.stringify(r.groups)!==JSON.stringify(q.groups))throw Error('Resampling groups differ between representations.');
        if(!r.skipped&&!q.skipped)paired.push({attempt:r.attempt,pca_ari:r.ari,lsa_ari:q.ari,lsa_minus_pca:q.ari-r.ari});
      }
    }
    return {...base,between_cluster_ari:ari(left.points.map(p=>p.cluster),right.points.map(p=>p.cluster)),
      membership_counts:matrix,neighbors,mean_neighbor_overlap:pointComparisons.reduce((sum,p)=>sum+p.neighbor_overlap,0)/pointComparisons.length,
      points:pointComparisons,paired_stability:{count:paired.length,samples:paired,
        mean_ari_difference:paired.length?paired.reduce((sum,p)=>sum+p.lsa_minus_pca,0)/paired.length:null}};
  }
  async function run(records,rawVectors,value={},progress=async()=>{}){
    const o=options(value);
    if(o.representation!=='compare')return runSingle(records,rawVectors,o,progress);
    const left=await runSingle(records,rawVectors,{...o,representation:'pca'},async m=>progress('PCA comparison · '+m));
    const right=await runSingle(records,rawVectors,{...o,representation:'lsa'},async m=>progress('LSA comparison · '+m));
    return {...left,requested_parameters:o,comparison:compareFits(left,right)};
  }
  const api={DEFAULTS,MAX_RECORDS,options,rng,pca,lsa:L.lsa,represent,oneKmeans,fitKmeans,fitPartition,algorithmName,ari,silhouette,compareFits,run};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNClusters=api;
})(typeof globalThis!=='undefined'?globalThis:this);
