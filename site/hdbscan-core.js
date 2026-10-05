/* Exact dense Euclidean HDBSCAN*: core distances -> mutual-reachability MST
 * -> single linkage -> condensed tree -> excess-of-mass or leaf selection.
 * Condensing/selection semantics follow scikit-learn 1.7.2 (BSD-3-Clause);
 * see HDBSCAN_LICENSE.txt. No approximate neighbors, embedding or forced k. */
(function(root){
  'use strict';
  const B=typeof module!=='undefined'&&module.exports?require('./cluster-algorithms.js'):root.UNClusterAlgorithms;
  const exported=v=>Number.isFinite(v)?v:'Infinity';
  async function fit(x,{minClusterSize=15,minSamples=5,selection='eom'}={},progress=async()=>{}){
    const n=x.length;
    if(!Number.isInteger(minClusterSize)||minClusterSize<2||!Number.isInteger(minSamples)||minSamples<2)throw Error('HDBSCAN sizes must be integers of at least two.');
    if(!['eom','leaf'].includes(selection))throw Error('Choose EOM or leaf cluster selection.');
    if(n<3||minSamples>n)return {skipped:'HDBSCAN needs at least as many usable passages as its density-neighbor count.'};
    await progress('HDBSCAN · core distances');
    const d=B.distances(x,2),core=d.map(row=>Array.from(row).sort((a,b)=>a-b)[minSamples-1]);
    // Exact Prim MST. Stable point-order ties; no sparse/approximate search.
    const seen=Array(n).fill(false),best=Array(n).fill(Infinity),parent=Array(n).fill(-1),mst=[];best[0]=0;
    for(let step=0;step<n;step++){
      let point=-1;for(let i=0;i<n;i++)if(!seen[i]&&(point<0||best[i]<best[point]))point=i;
      seen[point]=true;
      if(parent[point]>=0)mst.push({left:Math.min(point,parent[point]),right:Math.max(point,parent[point]),distance:best[point]});
      for(let j=0;j<n;j++)if(!seen[j]){
        const value=Math.max(core[point],core[j],d[point][j]);
        if(value<best[j]){best[j]=value;parent[j]=point;}
      }
      if(step%100===0)await progress(`HDBSCAN · reachability tree ${step+1} of ${n}`);
    }
    mst.sort((a,b)=>a.distance-b.distance);
    const roots=Array.from({length:2*n-1},(_,i)=>i),size=Array(2*n-1).fill(1),tree=[];
    const find=i=>{while(roots[i]!==i){roots[i]=roots[roots[i]];i=roots[i];}return i;};
    for(const edge of mst){
      const a=find(edge.left),b=find(edge.right),node=n+tree.length;
      tree.push({node,left:Math.min(a,b),right:Math.max(a,b),distance:edge.distance,size:size[a]+size[b]});
      roots[a]=roots[b]=node;size[node]=size[a]+size[b];
    }
    await progress('HDBSCAN · condensing the hierarchy');
    const condensed=[],birth=new Map([[n,0]]),children=new Map([[n,[]]]),death=new Map(),mass=new Map([[n,0]]),pointParent=Array(n),pointLambda=Array(n);
    const queue=[{node:2*n-2,cluster:n}];let next=n+1;
    const add=(p,c,lambda,count)=>{
      condensed.push({parent:p,child:c,lambda,size:count});death.set(p,Math.max(death.get(p)||0,lambda));
      const born=birth.get(p),duration=lambda===born?0:lambda-born;
      mass.set(p,(mass.get(p)||0)+duration*count);
      if(c<n){pointParent[c]=p;pointLambda[c]=lambda;}
    };
    function drop(node,cluster,lambda){
      const stack=[node];while(stack.length){const v=stack.pop();if(v<n)add(cluster,v,lambda,1);else{const t=tree[v-n];stack.push(t.right,t.left);}}
    }
    for(let index=0;index<queue.length;index++){
      const {node,cluster}=queue[index],t=tree[node-n],lambda=t.distance===0?Infinity:1/t.distance;
      const big=[t.left,t.right].filter(v=>size[v]>=minClusterSize);
      if(big.length===2){
        for(const child of big){const id=next++;birth.set(id,lambda);mass.set(id,0);children.set(id,[]);children.get(cluster).push(id);add(cluster,id,lambda,size[child]);queue.push({node:child,cluster:id});}
      }else if(big.length===1){const small=t.left===big[0]?t.right:t.left;drop(small,cluster,lambda);queue.push({node:big[0],cluster});}
      else{drop(t.left,cluster,lambda);drop(t.right,cluster,lambda);}
    }
    // Root selection is deliberately disabled. A no-cluster result is valid.
    function choose(id){
      const below=children.get(id).map(choose),sum=below.reduce((s,c)=>s+c.mass,0);
      if(id===n)return {mass:sum,nodes:below.flatMap(c=>c.nodes)};
      if(selection==='leaf')return below.length?{mass:sum,nodes:below.flatMap(c=>c.nodes)}:{mass:mass.get(id),nodes:[id]};
      return sum>mass.get(id)?{mass:sum,nodes:below.flatMap(c=>c.nodes)}:{mass:mass.get(id),nodes:[id]};
    }
    const selected=new Set(choose(n).nodes),clusterParent=new Map(condensed.filter(e=>e.child>=n).map(e=>[e.child,e.parent]));
    const owner=pointParent.map(p=>{while(p!==n&&!selected.has(p))p=clusterParent.get(p);return selected.has(p)?p:-1;});
    const ids=[...selected].filter(c=>owner.includes(c)).sort((a,b)=>owner.indexOf(a)-owner.indexOf(b));
    const labels=owner.map(c=>c<0?-1:ids.indexOf(c));
    const strengths=labels.map((c,i)=>{
      if(c<0)return 0;const maximum=death.get(ids[c]);
      return maximum===0||pointLambda[i]===Infinity?1:Math.min(pointLambda[i],maximum)/maximum;
    });
    await progress('HDBSCAN · cluster selection complete');
    return {labels,strengths,converged:true,diagnostics:{min_cluster_size:minClusterSize,min_samples:minSamples,
      min_samples_convention:'Includes the observation itself (scikit-learn convention)',selection,
      alpha:1,cluster_selection_epsilon:0,allow_single_cluster:false,metric:'Euclidean',exact_mst:true,
      core_distances:core,mst,single_linkage:tree,condensed_tree:condensed.map(e=>({...e,lambda:exported(e.lambda)})),
      selected_nodes:ids,selection_stability:ids.map(id=>({node:id,value:exported(mass.get(id)),birth:exported(birth.get(id)),death:exported(death.get(id))})),
      assigned_count:labels.filter(c=>c>=0).length,unassigned_count:labels.filter(c=>c<0).length,
      noise_label:-1,seed_used:false,ties:'Source row order in exact Prim MST; stable distance sort preserves MST insertion order',
      infinity_encoding:'Exact zero distances give infinite lambda, exported as the string Infinity; no finite distance floor applied',
      membership_strength_definition:'Point departure lambda divided by selected-cluster maximum departure lambda, capped at one; unassigned is zero. Geometric strength, not calibrated confidence.'}};
  }
  const api={fit};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNHDBSCAN=api;
})(typeof globalThis!=='undefined'?globalThis:this);
