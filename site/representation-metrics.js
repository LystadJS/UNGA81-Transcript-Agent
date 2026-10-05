/* Neighborhood diagnostics are descriptive geometry checks, not semantic scores. */
(function(root){
  'use strict';
  const L=typeof module!=='undefined'&&module.exports?require('./lsa-core.js'):root.UNLSA;
  const d2=(a,b)=>a.reduce((sum,x,i)=>sum+(x-b[i])**2,0);
  function sparseDistances(vectors){
    const {matrix}=L.gram(vectors),norms=matrix.map((row,i)=>row[i]);
    return matrix.map((row,i)=>Array.from(row,(v,j)=>i===j?0:Math.max(0,norms[i]+norms[j]-2*v)));
  }
  const denseDistances=rows=>rows.map(a=>rows.map(b=>d2(a,b)));
  function order(distances){
    // A documented tie rule makes neighborhood sets reproducible, including
    // text vectors which differ only below numerical precision.
    return distances.map((row,i)=>row.map((v,j)=>({v:Math.round(v*1e12)/1e12,j}))
      .filter(x=>x.j!==i).sort((a,b)=>a.v-b.v||a.j-b.j).map(x=>x.j));
  }
  function agreement(high,low,k,ids){
    const n=high.length;
    if(n<3||k<1||k>=n/2)throw Error('Neighborhood diagnostics require 1 <= k < n/2.');
    let intrusion=0,omission=0,overlap=0;
    const points=high.map((row,i)=>{
      const original=row.slice(0,k),reduced=low[i].slice(0,k);
      const shared=original.filter(j=>reduced.includes(j)).length;overlap+=shared;
      for(const j of reduced)if(!original.includes(j))intrusion+=row.indexOf(j)+1-k;
      for(const j of original)if(!reduced.includes(j))omission+=low[i].indexOf(j)+1-k;
      return {id:ids?.[i]??i,overlap:shared/k,
        original_neighbors:original.map(j=>ids?.[j]??j),reduced_neighbors:reduced.map(j=>ids?.[j]??j)};
    });
    const factor=2/(n*k*(2*n-3*k-1));
    return {neighbors:k,neighbor_overlap:overlap/(n*k),trustworthiness:1-factor*intrusion,
      continuity:1-factor*omission,points};
  }
  function assess(vectors,scores,layout,ids){
    const k=Math.min(10,Math.floor((vectors.length-1)/2));
    const raw=order(sparseDistances(vectors)),reduced=order(denseDistances(scores)),display=order(denseDistances(layout));
    return {metric:'Euclidean; TF-IDF input vectors are L2-normalized',
      tie_rule:'Squared distances rounded to 12 decimal places; ties resolved by input row order',
      representation:agreement(raw,reduced,k,ids),display:agreement(reduced,display,k,ids)};
  }
  const api={sparseDistances,denseDistances,order,agreement,assess};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNRepresentationMetrics=api;
})(globalThis);
