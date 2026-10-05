/* Regularized Gaussian mixtures on retained scores, with explicit model-conditioned
 * memberships. Original diagonal/spherical EM implementation; no UMAP fitting. */
(function(root){
  'use strict';
  const node=typeof module!=='undefined'&&module.exports;
  const DEFAULTS=Object.freeze({covariance:'diag',regularization:0.0001,starts:5,maxIterations:300,tolerance:0.00001,ambiguity:0.6});
  function options(value={}){
    const o={...DEFAULTS,...value};
    if(!['diag','spherical'].includes(o.covariance))throw Error('Choose diagonal or spherical mixture covariance.');
    for(const [key,min,max]of [['starts',1,10],['maxIterations',10,1000]])if(!Number.isInteger(o[key])||o[key]<min||o[key]>max)throw Error(`Invalid mixture ${key}: use ${min}–${max}.`);
    for(const [key,min,max]of [['regularization',1e-8,0.1],['tolerance',1e-8,0.01],['ambiguity',0.5,0.95]])if(!Number.isFinite(o[key])||o[key]<min||o[key]>max)throw Error(`Invalid mixture ${key}: use ${min}–${max}.`);
    return o;
  }
  function validate(x,k){
    if(!Array.isArray(x)||x.length<2||x.length>600||!Array.isArray(x[0])||!x[0].length||x[0].length>50||x.some(r=>!Array.isArray(r)||r.length!==x[0].length||r.some(v=>!Number.isFinite(v))))throw Error('Mixtures require 2–600 finite score rows and 1–50 dimensions.');
    if(!Number.isInteger(k)||k<1||k>12||k>=x.length)throw Error('Choose 1–12 mixture components, fewer than usable passages.');
  }
  function maximize(x,resp,covariance,reg){
    const n=x.length,d=x[0].length,k=resp[0].length,counts=Array(k).fill(0),means=Array.from({length:k},()=>Array(d).fill(0));
    for(let i=0;i<n;i++)for(let c=0;c<k;c++){const r=resp[i][c];counts[c]+=r;for(let j=0;j<d;j++)means[c][j]+=r*x[i][j];}
    if(counts.some(n=>!Number.isFinite(n)||n<1e-8))throw Error('A mixture component lost all numerical support.');
    for(let c=0;c<k;c++)for(let j=0;j<d;j++)means[c][j]/=counts[c];
    const variances=Array.from({length:k},()=>Array(d).fill(0));
    // Centered accumulation avoids catastrophic cancellation in E[X²] - E[X]².
    for(let i=0;i<n;i++)for(let c=0;c<k;c++)for(let j=0;j<d;j++)variances[c][j]+=resp[i][c]*(x[i][j]-means[c][j])**2;
    for(let c=0;c<k;c++){
      if(covariance==='spherical'){const v=variances[c].reduce((a,b)=>a+b,0)/(counts[c]*d)+reg;variances[c].fill(v);}
      else for(let j=0;j<d;j++)variances[c][j]=variances[c][j]/counts[c]+reg;
    }
    if(variances.some(r=>r.some(v=>!Number.isFinite(v)||v<=0)))throw Error('Invalid mixture variance.');
    return {weights:counts.map(v=>v/n),means,variances,covariance,regularization:reg};
  }
  function expectation(x,model){
    const k=model.weights.length,d=x[0].length,constant=d*Math.log(2*Math.PI);
    const logs=model.variances.map(v=>v.reduce((s,a)=>s+Math.log(a),0));
    const densities=[],responsibilities=[];
    for(const row of x){
      const values=model.weights.map((w,c)=>{
        let distance=0;for(let j=0;j<d;j++)distance+=(row[j]-model.means[c][j])**2/model.variances[c][j];
        return Math.log(w)-0.5*(constant+logs[c]+distance);
      });
      const maximum=Math.max(...values),norm=maximum+Math.log(values.reduce((s,v)=>s+Math.exp(v-maximum),0));
      if(!Number.isFinite(norm))throw Error('Mixture likelihood is not finite.');
      densities.push(norm);const r=values.map(v=>Math.exp(v-norm)),sum=r.reduce((a,b)=>a+b,0);responsibilities.push(r.map(v=>v/sum));
    }
    const logLikelihood=densities.reduce((a,b)=>a+b,0);
    return {responsibilities,log_densities:densities,log_likelihood:logLikelihood,mean_log_likelihood:logLikelihood/x.length};
  }
  async function solve(x,o,initial,progress=async()=>{}){
    let model=initial,e=expectation(x,model),converged=false,iterations=0;
    const history=[{iteration:0,mean_log_likelihood:e.mean_log_likelihood}];
    for(let iteration=1;iteration<=o.maxIterations;iteration++){
      model=maximize(x,e.responsibilities,o.covariance,o.regularization);const next=expectation(x,model);
      const change=next.mean_log_likelihood-e.mean_log_likelihood;e=next;iterations=iteration;
      history.push({iteration,mean_log_likelihood:e.mean_log_likelihood});
      if(iteration%10===0)await progress(`Mixture EM · iteration ${iteration}/${o.maxIterations}`);
      if(Math.abs(change)<o.tolerance){converged=true;break;}
    }
    return {model,...e,converged,iterations,history};
  }
  function ambiguity(row){
    const sorted=row.map((p,i)=>({p,i})).sort((a,b)=>b.p-a.p||a.i-b.i);
    const entropy=-row.reduce((s,p)=>s+(p>0?p*Math.log(p):0),0);
    return {cluster:sorted[0].i+1,max_membership:sorted[0].p,membership_margin:row.length>1?sorted[0].p-sorted[1].p:1,normalized_entropy:row.length>1?entropy/Math.log(row.length):0};
  }
  // Exact maximum-overlap alignment on shared posterior rows, not coordinate means:
  // each resample's PCA/LSA axes can rotate, change dimension or flip signs.
  function align(reference,other){
    if(!reference.length||reference.length!==other.length||reference[0].length!==other[0].length)throw Error('Soft alignment requires shared rows and equal component counts.');
    const k=reference[0].length,scores=Array.from({length:k},()=>Array(k).fill(0));
    for(let i=0;i<reference.length;i++)for(let a=0;a<k;a++)for(let b=0;b<k;b++)scores[a][b]+=reference[i][a]*other[i][b];
    const size=1<<k,dp=new Float64Array(size).fill(-Infinity),choice=new Int16Array(size).fill(-1);dp[0]=0;
    for(let mask=0;mask<size;mask++){let row=0;for(let bits=mask;bits;bits&=bits-1)row++;if(row===k)continue;
      for(let col=0;col<k;col++)if(!(mask&(1<<col))){const next=mask|(1<<col),v=dp[mask]+scores[row][col];if(v>dp[next]){dp[next]=v;choice[next]=col;}}
    }
    const mapping=Array(k);let mask=size-1;for(let a=k-1;a>=0;a--){mapping[a]=choice[mask];mask^=1<<mapping[a];}
    const point_tv=reference.map((r,i)=>r.reduce((s,v,a)=>s+Math.abs(v-other[i][mapping[a]]),0)/2);
    return {mapping:mapping.map(c=>c+1),mean_total_variation:point_tv.reduce((a,b)=>a+b,0)/point_tv.length,point_total_variation:point_tv,
      component_mean_absolute_change:mapping.map((c,a)=>reference.reduce((s,r,i)=>s+Math.abs(r[a]-other[i][c]),0)/reference.length),shared_passages:reference.length};
  }
  function parameterCount(k,d,covariance){return k*d+(covariance==='diag'?k*d:k)+k-1;}
  async function fit(x,value={},progress=async()=>{}){
    const o=options(value),k=value.k??4,seed=value.seed??42;validate(x,k);
    if(!Number.isInteger(seed)||seed<0||seed>4294967295)throw Error('Invalid mixture seed.');
    const C=node?require('./cluster-core.js'):root.UNClusters,runs=[],valid=[];
    for(let start=0;start<o.starts;start++){
      const startSeed=(seed+Math.imul(start,0x9e3779b9))>>>0;
      await progress(`Gaussian mixture · start ${start+1}/${o.starts}`);
      const init=k===1?{labels:x.map(()=>0),converged:true}:C.oneKmeans(x,k,C.rng(startSeed));
      if(!init?.converged){runs.push({seed:startSeed,skipped:'K-means initialization did not produce the requested components.'});continue;}
      let initial;try{initial=maximize(x,init.labels.map(c=>Array.from({length:k},(_,j)=>j===c?1:0)),o.covariance,o.regularization);}catch(e){runs.push({seed:startSeed,skipped:e.message});continue;}
      // Callback errors (including cancellation) must propagate, not become failed starts.
      let failed=false;
      const wrapped=async m=>{try{await progress(m);}catch(e){failed=true;throw e;}};
      try{
        const result=await solve(x,o,initial,wrapped);
        const record={seed:startSeed,converged:result.converged,iterations:result.iterations,log_likelihood:result.log_likelihood,history:result.history};runs.push(record);
        if(result.converged)valid.push({...result,seed:startSeed,record});
      }catch(e){if(failed)throw e;runs.push({seed:startSeed,skipped:e.message});}
    }
    if(!valid.length)return {skipped:'No Gaussian-mixture start converged. Inspect diagnostics, change settings or widen the collection; no fallback partition was released.',diagnostics:{starts:o.starts,converged_starts:0,runs}};
    const best=valid.reduce((a,b)=>b.log_likelihood>a.log_likelihood?b:a),n=x.length,d=x[0].length;
    const info=best.responsibilities.map(ambiguity),labels=info.map(p=>p.cluster-1),counts=Array(k).fill(0);labels.forEach(c=>counts[c]++);
    const softCounts=Array.from({length:k},(_,c)=>best.responsibilities.reduce((s,r)=>s+r[c],0));
    const parameters=parameterCount(k,d,o.covariance),warnings=[];
    const lowMass=softCounts.flatMap((v,c)=>v<Math.max(5,d+1)?[c+1]:[]),floor=best.model.variances.map(v=>v.filter(a=>a<=1.1*o.regularization).length);
    if(lowMass.length)warnings.push(`Components ${lowMass.join(', ')} have soft counts below ${Math.max(5,d+1)} passages. Inspect their support and covariance-floor sensitivity.`);
    if(counts.some(v=>v===0))warnings.push('At least one component has no highest-membership passage; it remains in the soft model and exports.');
    if(floor.some(v=>v>0))warnings.push('Some component variances are within 10% of the regularization floor. Compare another floor before interpreting memberships.');
    if(parameters>=n)warnings.push(`The model has ${parameters} free parameters for ${n} passages. Interpret in-sample likelihood and memberships cautiously.`);
    if(valid.length<o.starts)warnings.push(`${o.starts-valid.length} starts failed or reached the iteration limit. Only converged starts were eligible for selection.`);
    for(const r of valid)r.record.soft_agreement=align(best.responsibilities,r.responsibilities);
    return {labels,centers:best.model.means,responsibilities:best.responsibilities,point_diagnostics:info,converged:true,
      diagnostics:{...best.model,starts:o.starts,converged_starts:valid.length,selected_seed:best.seed,iterations:best.iterations,tolerance:o.tolerance,max_iterations:o.maxIterations,
        log_likelihood:best.log_likelihood,mean_log_likelihood:best.mean_log_likelihood,parameter_count:parameters,aic:2*parameters-2*best.log_likelihood,bic:Math.log(n)*parameters-2*best.log_likelihood,
        selection:'Largest final log likelihood among converged starts. No automatic component-count or covariance selection.',
        information_criteria_scope:'Same observations, dimensions, representation and preprocessing only. Regularized local fits and dependent passages limit formal AIC/BIC interpretation.',
        initialization:'Seeded k-means++ and Lloyd hard memberships, followed by regularized EM',covariance_type:o.covariance,
        convergence_rule:'Absolute change in average observed log likelihood below tolerance; not proof of a global optimum. Covariance regularization can reduce unpenalized likelihood.',
        hard_counts:counts,soft_counts:softCounts,near_floor_dimensions:floor,ambiguity_threshold:o.ambiguity,ambiguous_count:info.filter(p=>p.max_membership<o.ambiguity).length,
        mean_entropy:info.reduce((s,p)=>s+p.normalized_entropy,0)/n,runs,warnings}};
  }
  const api={DEFAULTS,options,validate,maximize,expectation,solve,ambiguity,align,parameterCount,fit};if(node)module.exports=api;else root.UNGaussianMixture=api;
})(globalThis);
