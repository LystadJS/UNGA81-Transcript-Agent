/* Deterministic Euclidean PAM (BUILD + best SWAP) and agglomerative clustering.
 * Coordinates are the unchanged retained PCA/LSA scores; UMAP never enters here. */
(function(root) {
  'use strict';
  function distances(x,k) {
    if(!Array.isArray(x)||x.length<2||!Number.isInteger(k)||k<2||k>=x.length)throw Error('Choose 2 ≤ k < number of passages.');
    const dimensions=x[0].length;
    if(!dimensions||x.some(row=>row.length!==dimensions||row.some(v=>!Number.isFinite(v))))throw Error('Clustering requires finite, equal-length score vectors.');
    const d=Array.from({length:x.length},()=>new Float64Array(x.length));
    for(let i=0;i<x.length;i++)for(let j=0;j<i;j++){
      let sum=0;for(let c=0;c<dimensions;c++)sum+=(x[i][c]-x[j][c])**2;
      d[i][j]=d[j][i]=Math.sqrt(sum);
      if(!Number.isFinite(d[i][j]))throw Error('Clustering distance overflow.');
    }
    return d;
  }
  function nearest(d,medoids) {
    const first=[],second=[],labels=[];
    for(let i=0;i<d.length;i++){
      let a=Infinity,b=Infinity,label=-1;
      for(let m=0;m<medoids.length;m++){
        const value=d[i][medoids[m]];
        if(value<a){b=a;a=value;label=m;}else if(value<b)b=value;
      }
      first.push(a);second.push(b);labels.push(label);
    }
    return {first,second,labels,objective:first.reduce((sum,v)=>sum+v,0)};
  }
  async function pam(x,k,progress=async()=>{}) {
    const d=distances(x,k),n=x.length,medoids=[];
    let closest=Array(n).fill(Infinity);
    // BUILD: first global medoid, then greatest reduction in total distance.
    for(let step=0;step<k;step++){
      await progress(`PAM · BUILD ${step+1} of ${k}`);
      let best=-1,cost=Infinity;
      for(let h=0;h<n;h++)if(!medoids.includes(h)){
        let candidate=0;for(let i=0;i<n;i++)candidate+=Math.min(closest[i],d[i][h]);
        if(candidate<cost){cost=candidate;best=h;}
      }
      if(step&&closest.reduce((s,v)=>s+v,0)-cost<=1e-12*Math.max(1,cost))return {converged:false,reason:'PAM cannot find k distinct score locations. Reduce the cluster count.'};
      medoids.push(best);closest=closest.map((v,i)=>Math.min(v,d[i][best]));
    }
    medoids.sort((a,b)=>a-b);
    let state=nearest(d,medoids);const history=[state.objective],buildMedoids=medoids.slice();
    for(let iteration=0;iteration<=300;iteration++){
      await progress(`PAM · SWAP check ${iteration+1}`);
      const tolerance=1e-12*Math.max(1,state.objective);
      let bestDelta=-tolerance,remove=-1,add=-1;
      // For each candidate, share its improvement across removal choices. The
      // owner's correction uses the second-nearest medoid. This evaluates ALL
      // single swaps, not an alternating assign/update approximation to PAM.
      for(let h=0;h<n;h++)if(!medoids.includes(h)){
        let common=0;const correction=new Float64Array(k);
        for(let i=0;i<n;i++){
          const improvement=Math.min(d[i][h],state.first[i])-state.first[i];
          common+=improvement;
          correction[state.labels[i]]+=Math.min(d[i][h],state.second[i])-state.first[i]-improvement;
        }
        for(let m=0;m<k;m++){
          const delta=common+correction[m];
          if(delta<bestDelta){bestDelta=delta;remove=m;add=h;}
        }
      }
      if(remove<0)return {labels:state.labels,medoids,converged:true,
        diagnostics:{initialization:'Deterministic BUILD',optimization:'Best improving single SWAP until local optimum',
          swaps:history.length-1,max_swaps:300,total_distance:state.objective,mean_distance:state.objective/n,
          objective_history:history,build_medoid_indices:buildMedoids,medoid_indices:medoids.slice(),
          tolerance,ties:'First candidate in source row order; then current medoid row order',seed_used:false}};
      if(iteration===300)return {converged:false,reason:'PAM reached its 300-swap limit before convergence. No partition released.'};
      medoids[remove]=add;medoids.sort((a,b)=>a-b);
      const next=nearest(d,medoids);
      if(!(next.objective<state.objective-tolerance))throw Error('PAM swap failed its objective-decrease check.');
      state=next;history.push(state.objective);
    }
  }
  async function hierarchical(x,k,linkage='ward',progress=async()=>{}) {
    if(!['ward','average'].includes(linkage))throw Error('Choose Ward or average linkage.');
    const d=distances(x,k),n=x.length,active=Array(n).fill(true),sizes=Array(n).fill(1),nodes=Array.from({length:n},(_,i)=>i);
    const members=nodes.map(i=>[i]),merges=[];let cut=null;
    if(linkage==='ward')for(let i=0;i<n;i++)for(let j=0;j<i;j++)d[i][j]=d[j][i]=d[i][j]**2;
    for(let step=0;step<n-1;step++){
      if(step%20===0)await progress(`Hierarchical · merge ${step+1} of ${n-1}`);
      let a=-1,b=-1,best=Infinity,left=Infinity,right=Infinity;
      for(let i=0;i<n;i++)if(active[i])for(let j=0;j<i;j++)if(active[j]){
        const l=Math.min(nodes[i],nodes[j]),r=Math.max(nodes[i],nodes[j]),v=d[i][j];
        if(v<best||(v===best&&(l<left||(l===left&&r<right)))){best=v;a=j;b=i;left=l;right=r;}
      }
      const size=sizes[a]+sizes[b],height=linkage==='ward'?Math.sqrt(best):best;
      merges.push({node:n+step,left,right,height,size});
      for(let c=0;c<n;c++)if(active[c]&&c!==a&&c!==b){
        let value=linkage==='average'?(sizes[a]*d[a][c]+sizes[b]*d[b][c])/size:
          ((sizes[a]+sizes[c])*d[a][c]+(sizes[b]+sizes[c])*d[b][c]-sizes[c]*best)/(size+sizes[c]);
        if(value < -1e-10*Math.max(1,d[a][c],d[b][c]))throw Error('Invalid hierarchical distance update.');
        d[a][c]=d[c][a]=Math.max(0,value);
      }
      active[b]=false;sizes[a]=size;nodes[a]=n+step;members[a]=members[a].concat(members[b]);
      if(step+1===n-k)cut=nodes.flatMap((node,i)=>active[i]?[{node,indices:members[i].slice()}]:[]).sort((a,b)=>Math.min(...a.indices)-Math.min(...b.indices));
    }
    const labels=Array(n);cut.forEach((group,c)=>group.indices.forEach(i=>{labels[i]=c;}));
    const cutHeight=merges[n-k-1].height,nextHeight=merges[n-k].height;
    return {labels,converged:true,diagnostics:{linkage,merges,cut_nodes:cut.map(c=>c.node),
      leaf_ordering:'Children ordered by node index; leaves follow source row indexes',
      node_indexing:'Leaves 0..n-1 in point order; merge nodes n..2n-2',
      height_definition:linkage==='ward'?'sqrt(2 × increase in within-cluster sum of squares)':'Mean pairwise Euclidean distance between the merged groups',
      cut_rule:'Exactly k groups after n-k merges; labels ordered by first source row',
      cut_height:cutHeight,next_merge_height:nextHeight,
      tied_cut:Math.abs(nextHeight-cutHeight)<=1e-12*Math.max(1,nextHeight),
      ties:'Equal merge costs resolved by ascending pair of node indexes',seed_used:false}};
  }
  const api={distances,pam,hierarchical};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNClusterAlgorithms=api;
})(typeof globalThis!=='undefined'?globalThis:this);
