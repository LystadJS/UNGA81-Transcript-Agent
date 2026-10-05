/* Uncentered truncated SVD for bounded sparse-text collections (LSA).
 * Compute U*S through XX' without materializing the document-term matrix.
 * The retained-energy denominator is uncentered; variance is reported separately. */
(function(root) {
  'use strict';
  const N=typeof module!=='undefined'&&module.exports?require('./numerics.js'):root.UNNumerics;
  function gram(vectors) {
    const n=vectors.length,postings=new Map();
    vectors.forEach((row,i)=>{for(const [term,w] of row){
      if(!postings.has(term))postings.set(term,[]);postings.get(term).push([i,w]);
    }});
    const matrix=Array.from({length:n},()=>new Float64Array(n));
    for(const rows of postings.values())for(let a=0;a<rows.length;a++)for(let b=0;b<=a;b++){
      const [i,x]=rows[a],[j,y]=rows[b];matrix[i][j]+=x*y;if(i!==j)matrix[j][i]+=x*y;
    }
    return {matrix,postings};
  }
  function lsa(vectors,requested,descriptors=true) {
    const n=vectors.length,{matrix,postings}=gram(vectors);
    if(n<2)throw Error('LSA needs at least two vectors.');
    const energy=matrix.reduce((sum,row,i)=>sum+row[i],0);
    const meanEnergy=matrix.reduce((sum,row)=>sum+row.reduce((a,b)=>a+b,0),0)/n;
    const centeredEnergy=Math.max(0,energy-meanEnergy);
    const eigen=new N.EigenvalueDecomposition(new N.Matrix(matrix.map(r=>Array.from(r))),{assumeSymmetric:true});
    const sorted=eigen.realEigenvalues.map((value,index)=>({value,index})).sort((a,b)=>b.value-a.value);
    const tolerance=Math.max(1e-12,Math.max(0,sorted[0].value)*1e-10);
    if(sorted.some(x=>x.value < -100*tolerance))throw Error('LSA decomposition failed its numerical check.');
    const positive=sorted.filter(x=>x.value>tolerance),chosen=positive.slice(0,requested);
    const scores=Array.from({length:n},()=>[]);
    for(const {value,index} of chosen){
      let anchor=0;
      for(let r=1;r<n;r++)if(Math.abs(eigen.eigenvectorMatrix.get(r,index))>Math.abs(eigen.eigenvectorMatrix.get(anchor,index)))anchor=r;
      const sign=eigen.eigenvectorMatrix.get(anchor,index)<0?-1:1;
      for(let r=0;r<n;r++)scores[r].push(sign*Math.sqrt(value)*eigen.eigenvectorMatrix.get(r,index));
    }
    const variances=chosen.map((_,c)=>{
      const mean=scores.reduce((sum,row)=>sum+row[c],0)/n;
      return scores.reduce((sum,row)=>sum+(row[c]-mean)**2,0);
    });
    const ratios=variances.map(v=>centeredEnergy>tolerance?v/centeredEnergy:null);
    const retainedEnergy=Math.min(1,chosen.reduce((sum,x)=>sum+x.value,0)/(energy||1));
    const terms=descriptors?chosen.map(({value},c)=>{
      // V = X'*(U*S)/S^2. Signs are numerical orientation, not stance labels.
      const weights=[...postings].map(([term,rows])=>({term,weight:rows.reduce((sum,[i,w])=>sum+w*scores[i][c],0)/value}));
      return {component:c+1,
        positive:weights.filter(x=>x.weight>1e-12).sort((a,b)=>b.weight-a.weight||a.term.localeCompare(b.term)).slice(0,8),
        negative:weights.filter(x=>x.weight < -1e-12).sort((a,b)=>a.weight-b.weight||a.term.localeCompare(b.term)).slice(0,8)};
    }):undefined;
    return {scores,rank:positive.length,components:chosen.length,requested_components:requested,
      singular_values:chosen.map(x=>Math.sqrt(x.value)),energy_ratio:chosen.map(x=>x.value/(energy||1)),
      retained_energy:retainedEnergy,relative_reconstruction_error:Math.sqrt(Math.max(0,1-retainedEnergy)),
      explained_variance_ratio:ratios,retained_variance:centeredEnergy>tolerance?Math.min(1,ratios.reduce((a,b)=>a+b,0)):null,
      vocabulary:postings.size,component_terms:terms,
      centering:'None; no feature standardization, whitening or score renormalization',
      solver:'ml-matrix 6.15.0 symmetric eigendecomposition of uncentered Gram matrix; leading positive singular triplets',
      variance_definition:'Centered variance of projected scores / centered variance of input TF-IDF; distinct from uncentered singular-value energy'};
  }
  const api={gram,lsa};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNLSA=api;
})(globalThis);
