/* Nonnegative TF-IDF = W H. Frobenius multiplicative updates (Lee & Seung, 2001).
 * Original implementation, sparse X / dense small factors; no centering or UMAP.
 * Components are overlapping lexical patterns, never automatic political labels.
 */
(function(root){
  'use strict';
  const node=typeof module!=='undefined'&&module.exports;
  const O=node?require('./nmf-options.js'):root.UNNMFOptions;
  const A=node?require('./analysis-core.js'):root.UNAnalysis;
  const C=node?require('./cluster-core.js'):root.UNClusters;
  const S=node?require('./cluster-stability.js'):root.UNClusterStability;
  const EPS=1e-16;
  function matrix(vectors){
    const terms=[...new Set(vectors.flatMap(v=>[...v.keys()]))].sort(),index=new Map(terms.map((t,i)=>[t,i]));
    let norm2=0,sum=0;
    const rows=vectors.map(v=>[...v].map(([t,x])=>{
      if(!Number.isFinite(x)||x<0)throw Error('NMF requires finite, nonnegative input.');
      norm2+=x*x;sum+=x;return [index.get(t),x];
    }));
    return {rows,terms,n:rows.length,m:terms.length,norm2,sum};
  }
  function initialize(x,k,seed){
    const random=C.rng(seed),scale=Math.sqrt(x.sum/(x.n*x.m*k));
    return {W:Float64Array.from({length:x.n*k},()=>scale*(0.1+random())),H:Float64Array.from({length:k*x.m},()=>scale*(0.1+random()))};
  }
  function gramRows(H,k,m){
    const g=new Float64Array(k*k);
    for(let a=0;a<k;a++)for(let b=0;b<=a;b++){
      let v=0;for(let j=0;j<m;j++)v+=H[a*m+j]*H[b*m+j];g[a*k+b]=g[b*k+a]=v;
    }return g;
  }
  function gramColumns(W,n,k){
    const g=new Float64Array(k*k);
    for(let a=0;a<k;a++)for(let b=0;b<=a;b++){
      let v=0;for(let i=0;i<n;i++)v+=W[i*k+a]*W[i*k+b];g[a*k+b]=g[b*k+a]=v;
    }return g;
  }
  function step(x,W,H,k){
    const {n,m,rows}=x,gH=gramRows(H,k,m),next=new Float64Array(k);
    for(let i=0;i<n;i++){
      for(let a=0;a<k;a++){
        let numerator=0,denominator=0;
        for(const [j,v] of rows[i])numerator+=v*H[a*m+j];
        for(let b=0;b<k;b++)denominator+=W[i*k+b]*gH[b*k+a];
        next[a]=W[i*k+a]*numerator/Math.max(denominator,EPS);
      }W.set(next,i*k);
    }
    const gW=gramColumns(W,n,k),cross=new Float64Array(k*m),nextH=new Float64Array(k*m);
    for(let i=0;i<n;i++)for(const [j,v]of rows[i])for(let a=0;a<k;a++)cross[a*m+j]+=W[i*k+a]*v;
    for(let a=0;a<k;a++)for(let j=0;j<m;j++){
      let denominator=0;for(let b=0;b<k;b++)denominator+=gW[a*k+b]*H[b*m+j];
      nextH[a*m+j]=H[a*m+j]*cross[a*m+j]/Math.max(denominator,EPS);
    }H.set(nextH);
  }
  function residual(x,W,H,k){
    const gW=gramColumns(W,x.n,k),gH=gramRows(H,k,x.m);let cross=0,product=0;
    for(let i=0;i<x.n;i++)for(const [j,v]of x.rows[i])for(let a=0;a<k;a++)cross+=v*W[i*k+a]*H[a*x.m+j];
    for(let a=0;a<k*k;a++)product+=gW[a]*gH[a];
    const squared=x.norm2-2*cross+product;
    // The Gram identity loses relative precision near an exact reconstruction.
    // Use explicit residuals there, so roundoff cannot falsely report divergence.
    if(squared<1e-10*Math.max(1,x.norm2)){
      let direct=0;
      for(let i=0;i<x.n;i++){
        const original=new Map(x.rows[i]);
        for(let j=0;j<x.m;j++){let predicted=0;for(let a=0;a<k;a++)predicted+=W[i*k+a]*H[a*x.m+j];direct+=((original.get(j)||0)-predicted)**2;}
      }return Math.sqrt(direct);
    }
    return Math.sqrt(squared);
  }
  function normalize(W,H,n,m,k){
    // Resolve factor scaling before comparing passage mixtures: each H row has unit L2 norm.
    for(let a=0;a<k;a++){
      let norm=0;for(let j=0;j<m;j++)norm+=H[a*m+j]**2;norm=Math.sqrt(norm);
      if(norm>0){for(let j=0;j<m;j++)H[a*m+j]/=norm;for(let i=0;i<n;i++)W[i*k+a]*=norm;}
    }
  }
  async function solve(x,o,seed,progress=async()=>{}){
    const k=o.components,{W,H}=initialize(x,k,seed),initial=residual(x,W,H,k),history=[{iteration:0,residual:initial}];
    let previous=initial,converged=false,iteration=0;
    for(iteration=1;iteration<=o.maxIterations;iteration++){
      step(x,W,H,k);
      if(iteration%10===0||iteration===o.maxIterations){
        const error=residual(x,W,H,k);if(!Number.isFinite(error))throw Error('NMF produced a nonfinite fit.');
        if(error>previous+1e-8*Math.max(1,initial))throw Error('NMF reconstruction error increased beyond numeric tolerance.');
        history.push({iteration,residual:error});await progress(`NMF · iteration ${iteration} of ${o.maxIterations}`);
        if(Math.max(0,previous-error)/Math.max(initial,EPS)<o.tolerance){converged=true;break;}previous=error;
      }
    }
    normalize(W,H,x.n,x.m,k);
    return {W,H,seed,iterations:Math.min(iteration,o.maxIterations),converged,residual:residual(x,W,H,k),history};
  }
  // Exact one-to-one maximum-score assignment; k <= 12 bounds the bitmask DP.
  function assignment(scores){
    const k=scores.length,size=1<<k,dp=new Float64Array(size).fill(-Infinity),choice=new Int16Array(size).fill(-1);dp[0]=0;
    for(let mask=0;mask<size;mask++){
      let row=0;for(let bits=mask;bits;bits&=bits-1)row++;
      if(row===k)continue;
      for(let col=0;col<k;col++)if(!(mask&(1<<col))){const next=mask|(1<<col),score=dp[mask]+scores[row][col];if(score>dp[next]){dp[next]=score;choice[next]=col;}}
    }
    const result=Array(k);let mask=size-1;for(let row=k-1;row>=0;row--){result[row]=choice[mask];mask^=1<<result[row];}return result;
  }
  function align(left,right){
    const k=left.components.length;if(right.components.length!==k)throw Error('Alignment requires equal component counts.');
    const index=new Map(right.vocabulary.map((t,j)=>[t,j])),pairs=left.vocabulary.flatMap((t,j)=>index.has(t)?[[j,index.get(t)]]:[]);
    // Both H rows have unit L2 norm on their FULL vocabularies. Missing terms stay zero.
    const cosine=left.factors.H.map(a=>right.factors.H.map(b=>Math.min(1,pairs.reduce((v,[i,j])=>v+a[i]*b[j],0))));
    const matched=assignment(cosine),byId=new Map(right.points.map(p=>[p.id,p])),shared=left.points.filter(p=>byId.has(p.id)&&p.shares!==null&&byId.get(p.id).shares!==null);
    const components=matched.map((j,i)=>({component:i+1,matched_component:j+1,cosine:cosine[i][j]}));
    return {components,mean_cosine:components.reduce((s,c)=>s+c.cosine,0)/k,shared_passages:shared.length,
      mean_mixture_l1:shared.length?shared.reduce((s,p)=>s+p.shares.reduce((v,w,i)=>v+Math.abs(w-byId.get(p.id).shares[matched[i]]),0),0)/shared.length:null,
      shared_vocabulary:pairs.length,reference_vocabulary:left.vocabulary.length,other_vocabulary:right.vocabulary.length};
  }
  function materialize(records,x,fit,o){
    const k=o.components,H=Array.from({length:k},(_,a)=>Array.from(fit.H.slice(a*x.m,(a+1)*x.m))),W=Array.from({length:x.n},(_,i)=>Array.from(fit.W.slice(i*k,(i+1)*k)));
    const points=records.map((r,i)=>{const total=W[i].reduce((a,b)=>a+b,0);return {id:r.id,text_sha256:r.text_sha256,weights:W[i],shares:total>EPS?W[i].map(w=>w/total):null};});
    const components=H.map((row,a)=>({component:a+1,norm:Math.sqrt(row.reduce((s,v)=>s+v*v,0)),
      mean_share:points.reduce((s,p)=>s+(p.shares?.[a]||0),0)/points.length,
      terms:row.map((weight,j)=>({term:x.terms[j],weight})).filter(t=>t.weight>0).sort((a,b)=>b.weight-a.weight||a.term.localeCompare(b.term)).slice(0,12),
      sources:points.map((p,i)=>({id:p.id,weight:p.weights[a],share:p.shares?.[a]??null,index:i})).filter(p=>p.weight>EPS).sort((a,b)=>b.weight-a.weight||a.index-b.index).slice(0,5).map(({index,...p})=>p)}));
    return {vocabulary:x.terms,factors:{H},components,points};
  }
  async function run(records,rawVectors,value={},progress=async()=>{}){
    const o=O.options(value),base={schema:'un.nmf.v1',parameters:o,input_count:records.length,
      procedure:'Uncentered, L2-normalized nonnegative TF-IDF; Frobenius multiplicative updates; positive random starts; lowest residual selected; H rows scaled to unit L2 norm.',
      interpretation:'Overlapping lexical components. Normalized passage weights are descriptive mixture shares, not probabilities, stances or reviewed themes.'};
    if(records.length>600)return {...base,skipped:'NMF supports at most 600 selected passages. Narrow the collection; no sampling was applied.'};
    if(rawVectors.length!==records.length)throw Error('NMF vectors must match source rows.');
    if(new Set(records.map(r=>r.id)).size!==records.length)throw Error('NMF requires unique source IDs.');
    const vectors=rawVectors.map(v=>new Map(v));matrix(vectors); // Validate even rows excluded as zero.
    const keep=vectors.flatMap((v,i)=>[...v.values()].some(x=>x>0)?[i]:[]),selected=keep.map(i=>records[i]),excluded=records.flatMap((r,i)=>keep.includes(i)?[]:[{id:r.id,reason:'No usable TF-IDF terms'}]);
    const x=matrix(keep.map(i=>vectors[i]));
    if(x.n<4||o.components>=x.n||o.components>x.m)return {...base,excluded,skipped:'NMF needs at least four usable passages, fewer components than passages, and no more components than terms.'};
    const fits=[];
    for(let start=0;start<o.starts;start++)fits.push(await solve(x,o,(o.seed+Math.imul(start,0x9e3779b9))>>>0,async m=>progress(`Start ${start+1}/${o.starts} · ${m}`)));
    const best=fits.reduce((a,b)=>b.residual<a.residual?b:a),view=materialize(selected,x,best,o);
    const result={...base,...view,excluded,usable_count:x.n,vocabulary_count:x.m,
      diagnostics:{selected_seed:best.seed,converged:best.converged,iterations:best.iterations,residual:best.residual,relative_residual:best.residual/Math.sqrt(x.norm2),
        squared_reconstruction_fraction:1-best.residual**2/x.norm2,convergence_rule:'Every ten iterations: residual decrease / initial residual < tolerance; this is not proof of a global optimum.',
        starts:fits.map(f=>({seed:f.seed,iterations:f.iterations,converged:f.converged,residual:f.residual,history:f.history,
          alignment:align(view,materialize(selected,x,f,o))}))},warnings:[]};
    if(!best.converged)result.warnings.push('The selected fit reached its iteration limit. Treat its components and stability as provisional.');
    if(result.components.some(c=>c.norm<EPS))result.warnings.push('At least one component collapsed to zero. Reduce the component count or inspect alternative starts.');
    if(result.points.some(p=>p.shares===null))result.warnings.push('Some usable passages have no reconstructed component weight; their mixture shares are undefined.');
    result.stability=await stability(records,result,progress);return result;
  }
  async function stability(records,fit,progress){
    const s=fit.parameters.stability,base={parameters:s,procedure:'Whole-group subsampling; vocabulary, IDF and NMF refitted. Components matched one-to-one by maximum full-vocabulary cosine; absent terms count as zero. Mixtures compared only on shared source IDs.',warnings:[]};
    if(!s.enabled)return {...base,skipped:'Component stability was not selected.'};
    if(records.some(r=>typeof r.text!=='string'))return {...base,skipped:'Source text is required for stability refits.'};
    let grouped;try{grouped=S.groupRecords(records,s.unit);}catch(e){return {...base,skipped:e.message};}
    const groups=grouped.groups,G=groups.length,count=Math.min(G-1,Math.ceil(G*s.fraction));
    Object.assign(base,{group_count:G,sample_group_count:count,groups:groups.map(g=>({key:g.key,ids:g.indices.map(i=>records[i].id)}))});
    if(G<3)return {...base,skipped:'Component stability requires at least three groups.'};
    if(G<10)base.warnings.push(`Only ${G} source groups; repeated omissions are not independent evidence.`);
    if(grouped.fallback)base.warnings.push(`${grouped.fallback} passages use recorded date, scope and meeting title as their grouping key.`);
    if(grouped.unknown)base.warnings.push(`${grouped.unknown} unknown affiliations are kept in one group.`);
    const random=C.rng(s.seed),runs=[],unique=new Set();
    for(let attempt=0;attempt<s.replicates;attempt++){
      const chosen=S.sampleGroups(G,count,random);unique.add(chosen.join(','));
      const ids=new Set(chosen.flatMap(g=>groups[g].indices)),rows=records.filter((_,i)=>ids.has(i));
      const seed=(s.seed+Math.imul(attempt+1,0x85ebca6b))>>>0;
      const sample=await run(rows,A.tfidf(rows).vectors,{...fit.parameters,seed,stability:{...s,enabled:false}},async m=>progress(`NMF sample ${attempt+1}/${s.replicates} · ${m}`));
      const common={attempt:attempt+1,groups:chosen,seed,selected_count:rows.length};
      runs.push(sample.skipped?{...common,skipped:sample.skipped}:{...common,usable_count:sample.usable_count,excluded:sample.excluded,
        converged:sample.diagnostics.converged,relative_residual:sample.diagnostics.relative_residual,...align(fit,sample)});
    }
    const successful=runs.filter(r=>!r.skipped),converged=successful.filter(r=>r.converged);
    if(successful.length<s.replicates)base.warnings.push(`${s.replicates-successful.length} samples were skipped; inspect their reasons.`);
    if(converged.length<successful.length)base.warnings.push(`${successful.length-converged.length} fitted samples reached the iteration limit. All-fit and converged-only summaries are separate.`);
    return {...base,attempted:runs.length,successful:successful.length,converged:converged.length,unique_group_samples:unique.size,runs,
      cosine:S.summary(successful.map(r=>r.mean_cosine)),converged_cosine:S.summary(converged.map(r=>r.mean_cosine)),mixture_l1:S.summary(successful.map(r=>r.mean_mixture_l1)),
      components:fit.components.map(c=>({component:c.component,...S.summary(successful.map(r=>r.components[c.component-1].cosine))}))};
  }
  const api={options:O.options,matrix,initialize,step,residual,normalize,solve,assignment,align,run};if(node)module.exports=api;else root.UNNMF=api;
})(globalThis);
