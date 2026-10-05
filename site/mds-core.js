/* Metric, equal-weight SMACOF in two dimensions. Display only; no labels used. */
(function(root){
  'use strict';
  const DEFAULTS=Object.freeze({enabled:false,starts:3,seed:42,maxIterations:1000,tolerance:1e-6});
  function options(value={}){
    const o={...DEFAULTS,...value};if(typeof o.enabled!=='boolean')throw Error('Choose whether to compare metric MDS.');
    for(const [key,min,max]of [['starts',1,5],['seed',0,4294967295],['maxIterations',10,1000]])if(!Number.isInteger(o[key])||o[key]<min||o[key]>max)throw Error(`Invalid MDS ${key}: use ${min}–${max}.`);
    if(!Number.isFinite(o.tolerance)||o.tolerance<1e-9||o.tolerance>.001)throw Error('Invalid MDS convergence tolerance.');return o;
  }
  function rng(seed){let a=seed>>>0;return()=>{a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296;};}
  const center=x=>{const means=[0,1].map(d=>x.reduce((s,r)=>s+r[d],0)/x.length);return x.map(r=>r.map((v,d)=>v-means[d]));};
  function distances(x){const a=new Float64Array(x.length*(x.length-1)/2);let p=0;for(let i=1;i<x.length;i++)for(let j=0;j<i;j++)a[p++]=Math.sqrt(x[i].reduce((s,v,d)=>s+(v-x[j][d])**2,0));return a;}
  function evaluate(target,coordinates){
    const d=distances(coordinates);let stress=0,embedded=0,targetSum=0;for(let p=0;p<d.length;p++){stress+=(target[p]-d[p])**2;embedded+=d[p]**2;targetSum+=target[p]**2;}
    return {distances:d,stress,embedded_sum_squares:embedded,target_sum_squares:targetSum,relative_distance_error:targetSum?Math.sqrt(stress/targetSum):null,stress1:embedded?Math.sqrt(stress/embedded):null};
  }
  function initialize(n,target,seed){
    const random=rng(seed),x=center(Array.from({length:n},()=>[random()-.5,random()-.5]));
    const measured=evaluate(target,x),scale=Math.sqrt(measured.target_sum_squares/measured.embedded_sum_squares);return x.map(r=>r.map(v=>v*scale));
  }
  async function solve(target,initial,o,progress=async()=>{}){
    const n=initial.length;let x=center(initial),e=evaluate(target,x),iterations=0,converged=false;
    if(e.target_sum_squares>0&&!e.embedded_sum_squares)throw Error('MDS initialization collapsed despite positive target distances.');
    const history=[{iteration:0,stress:e.stress}];
    for(let t=1;t<=o.maxIterations;t++){
      const next=Array.from({length:n},()=>[0,0]);let p=0;
      for(let i=1;i<n;i++)for(let j=0;j<i;j++,p++){
        const ratio=e.distances[p]>0?target[p]/e.distances[p]:0;
        for(let d=0;d<2;d++){const step=ratio*(x[i][d]-x[j][d])/n;next[i][d]+=step;next[j][d]-=step;}
      }
      const measured=evaluate(target,next),improvement=e.stress-measured.stress;
      if(!Number.isFinite(measured.stress)||improvement< -1e-10*Math.max(e.target_sum_squares,1e-30))throw Error('MDS failed its finite, nonincreasing stress check.');
      x=next;e=measured;iterations=t;history.push({iteration:t,stress:e.stress});
      if(t%10===0)await progress(`Metric MDS · iteration ${t}/${o.maxIterations}`);
      if(!e.target_sum_squares||Math.max(0,improvement)/Math.max(e.embedded_sum_squares,Number.MIN_VALUE)<o.tolerance){converged=true;break;}
    }
    const {distances:ignored,...values}=e;return {coordinates:x,...values,iterations,converged,history};
  }
  function diagnostics(target,coordinates){
    const n=coordinates.length,e=evaluate(target,coordinates),max=target.reduce((a,b)=>Math.max(a,b),0),bins=Array.from({length:20},(_,i)=>({bin:i+1,lower:max*i/20,upper:max*(i+1)/20,count:0,target_sum:0,display_sum:0,min:Infinity,max:-Infinity})),pointError=Array(n).fill(0);
    let p=0;for(let i=1;i<n;i++)for(let j=0;j<i;j++,p++){
      const b=bins[Math.min(19,max?Math.floor(target[p]/max*20):0)],d=e.distances[p];b.count++;b.target_sum+=target[p];b.display_sum+=d;b.min=Math.min(b.min,d);b.max=Math.max(b.max,d);const r=(target[p]-d)**2;pointError[i]+=r;pointError[j]+=r;
    }
    return {pair_count:target.length,zero_target_pairs:Array.from(target).filter(d=>d===0).length,bins:bins.filter(b=>b.count).map(({target_sum,display_sum,...b})=>({...b,target_mean:target_sum/b.count,display_mean:display_sum/b.count})),point_relative_error:pointError.map(v=>e.target_sum_squares?Math.sqrt(v/(n-1)/(e.target_sum_squares/target.length)):null)};
  }
  async function fit(scores,value={},progress=async()=>{}){
    const o=options(value);
    if(!Array.isArray(scores)||scores.length<2||scores.length>600||!Array.isArray(scores[0])||!scores[0].length||scores[0].length>50||scores.some(r=>!Array.isArray(r)||r.length!==scores[0].length||r.some(v=>!Number.isFinite(v))))throw Error('MDS requires 2–600 finite score rows and 1–50 retained dimensions.');
    const target=distances(scores),runs=[],valid=[];
    if(!target.some(v=>v>0)){const coordinates=scores.map(()=>[0,0]);return {coordinates,converged:true,stress:0,relative_distance_error:null,stress1:null,runs:[],warnings:['All target distances are zero; this display contains no measurable geometry.'],...diagnostics(target,coordinates)};}
    for(let start=0;start<o.starts;start++){
      const seed=(o.seed+Math.imul(start,0x9e3779b9))>>>0;await progress(`Metric MDS · start ${start+1}/${o.starts}`);
      // Cancellation errors must propagate; numerical failures are recorded per start.
      let cancelled=false;const wrapped=async m=>{try{await progress(m);}catch(e){cancelled=true;throw e;}};
      try{const f=await solve(target,initialize(scores.length,target,seed),o,wrapped);const {coordinates,...summary}=f;runs.push({seed,...summary});valid.push({...f,seed});}
      catch(e){if(cancelled)throw e;runs.push({seed,skipped:e.message});}
    }
    if(!valid.length)return {skipped:'No finite MDS display passed the stress check. Clustering remains available.',runs};
    const best=valid.reduce((a,b)=>a.stress<=b.stress?a:b),warnings=[];
    if(!best.converged)warnings.push('The selected MDS layout reached its iteration limit. It remains a provisional display; inspect other starts or increase the limit.');
    if(runs.some(r=>r.skipped))warnings.push('Some MDS starts failed; their reasons remain in the diagnostics.');
    return {...best,history:undefined,parameters:o,runs,warnings,...diagnostics(target,best.coordinates),algorithm:'Metric SMACOF, equal weight for every unordered pair including zero distances',initialization:'Seeded uniform random coordinates, centered and scaled to target RMS pair distance',selection:'Smallest finite final raw stress across starts; iteration-limited selection is disclosed',convergence_rule:'Stress decrease divided by current sum of squared embedding distances below tolerance',role:'Display only; Euclidean distances in all retained, unwhitened scores; no cluster labels supplied'};
  }
  const api={DEFAULTS,options,distances,evaluate,initialize,solve,diagnostics,fit};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNMetricMDS=api;
})(globalThis);
