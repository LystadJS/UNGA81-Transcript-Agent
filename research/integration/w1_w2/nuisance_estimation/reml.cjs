'use strict';
/*
 * Pure Node Gaussian REML candidate on synthetic scalar covariance proxies.
 * True generating parameters are NEVER accepted by fit(). No empirical source
 * API. Crossed affiliation/meeting/year dependence cannot be inferred from
 * counts of groups. This only probes numerical feasibility/identification.
 */
const crypto=require('node:crypto');
const check=(ok,m)=>{if(!ok)throw Error('nuisance-remL-candidate: '+m);};
const hash=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
function chol(v,n,eps=1e-11){
 const l=new Float64Array(n*n);
 let min=Infinity,max=0;
 for(let i=0;i<n;i++)for(let j=0;j<=i;j++){
   let z=v[i*n+j];
   for(let k=0;k<j;k++)z-=l[i*n+k]*l[j*n+k];
   if(i===j){
     if(!Number.isFinite(z)||z<=eps)return null;
     const d=Math.sqrt(z);
     l[i*n+j]=d;min=Math.min(min,d);max=Math.max(max,d);
   }else l[i*n+j]=z/l[j*n+j];
 }
 return {matrix:l,min_diag:min,max_diag:max};
}
function forward(l,n,b){
 const x=new Float64Array(n);
 for(let i=0;i<n;i++){
   let z=b[i];
   for(let k=0;k<i;k++)z-=l[i*n+k]*x[k];
   x[i]=z/l[i*n+i];
 }
 return x;
}
function backward(l,n,b){
 const x=new Float64Array(n);
 for(let i=n-1;i>=0;i--){
   let z=b[i];
   for(let k=i+1;k<n;k++)z-=l[k*n+i]*x[k];
   x[i]=z/l[i*n+i];
 }
 return x;
}
function verify(panel,{minimumYears=12}={}){
 check(panel&&panel.schema==='un.w1w2.nuisance-estimation.synthetic-panel.v0' &&
   panel.source_hash_basis==='synthetic'&&
   panel.producer?.kind==='invented_numerical_proxy' &&
   panel.publication_eligible===false&&
   panel.inferential_eligible===false&&
   panel.empirical_evaluation_authorized===false,
   'only source-free invented scalar proxy panels are allowed');
 check(!Object.hasOwn(panel,'truth')&&
   !Object.hasOwn(panel,'oracle_parameters')&&
   !Object.hasOwn(panel,'generating_variances'),
   'estimator must not receive any oracle generating parameters');
 const all=panel.full_design_rows;
 check(Array.isArray(all)&&all.length===panel.source_inventory_total &&
   new Set(all.map(x=>x.id)).size===all.length,
   'complete invented observation inventory with unique IDs required');
 const ids=all.map(r=>[r.id,r.source_status,r.selection_status,
   r.meeting_id,r.source_family_id,r.parent_id,r.affiliation_id,r.calendar_year,
   r.fixed_covariates]);
 check(panel.source_design_sha256===hash(ids),'unverified original synthetic design identity');
 const selected=all.filter(r=>r.selection_status==='selected_eligible');
 check(selected.length===panel.selected_eligible &&
   hash(selected.map(x=>[x.id,x.response_sha256]))===panel.selection_sha256,
   'source-bound fitted selection/hash changed');
 check(all.filter(x=>x.selection_status==='unavailable_source').length===
   panel.unavailable_sources &&
   all.filter(x=>x.selection_status==='available_not_selected').length===
   panel.available_not_selected &&
   all.every(r=>r.source_hash_basis==='synthetic' &&
     typeof r.id==='string' &&
     (r.id.startsWith('fictitious-')||r.id.startsWith('fictional-unavailable-'))),
   'unavailable source/selection provenance inconsistent');
 check(all.every(x=>x.response===null||
   x.selection_status==='selected_eligible'&&
   Number.isFinite(x.response)&&
   x.response_sha256===crypto.createHash('sha256')
     .update(x.response.toPrecision(17)).digest('hex')) &&
   all.filter(x=>x.selection_status!=='selected_eligible').every(x=>
     x.response===null&&x.response_sha256===null),
   'selected response hash, unavailable or verified-not-selected response invalid');
 const mechanism=panel.selection_mechanism;
 if(mechanism==='depends_on_latent_response')
   return {status:'WITHHELD_MNAR_SELECTION_NOT_IDENTIFIED',reason:
     'Selection depends on the unobserved latent response; conditioning on fixed X does not identify its mechanism.',sample_size:selected.length};
 check(['complete','depends_on_observed_covariates'].includes(mechanism),
   'unknown selection model without source-probability attestation');
 const years=[...new Set(selected.map(r=>r.year_index))].sort((a,b)=>a-b);
 const meetings=new Map(),perYear=new Map(),affiliations=new Map(),families=new Map();
 for(const row of selected){
   check(Number.isFinite(row.response)&&
     Array.isArray(row.fixed_covariates)&&row.fixed_covariates.length===7&&
     row.fixed_covariates.every(Number.isFinite) &&
     Number.isSafeInteger(row.year_index)&&row.year_index>=0 &&
     row.calendar_year===2000+row.year_index &&
     typeof row.meeting_id==='string'&&
     typeof row.affiliation_id==='string'&&
     row.meeting_id.startsWith('fictional-meeting-') &&
     row.affiliation_id.startsWith('fictional-affiliation-'),
     'invalid invented numeric response or year/affiliation/source fields');
   if(!meetings.has(row.meeting_id))meetings.set(row.meeting_id,[]);
   meetings.get(row.meeting_id).push(row);
   if(!perYear.has(row.year_index))perYear.set(row.year_index,new Set());
   perYear.get(row.year_index).add(row.meeting_id);
   if(!affiliations.has(row.affiliation_id))affiliations.set(row.affiliation_id,[]);
   affiliations.get(row.affiliation_id).push(row);
   for(const field of ['source_family_id','parent_id']){
     if(!row[field])continue;
     const k=field+'\u001f'+row[field];
     if(families.has(k)&&families.get(k)!==row.meeting_id)
       return {status:'WITHHELD_CROSS_MEETING_FAMILY',reason:
         'A dependent original source-family/parent crosses two meeting blocks; no meeting-independent covariance design.',sample_size:selected.length};
     families.set(k,row.meeting_id);
   }
 }
 if(years.length<minimumYears)
   return {status:'WITHHELD_TOO_FEW_YEARS',
     reason:'At least twelve distinct synthetic year blocks required for engineering preflight; historical four-per-era inference remains withheld.',
     sample_size:selected.length,years:years.length};
 if([...perYear.values()].some(x=>x.size<2))
   return {status:'WITHHELD_YEAR_MEETING_CONFOUNDING',
     reason:'At least two distinct source meetings per calendar year are required to separate meeting and year variance.',
     sample_size:selected.length,years:years.length};
 if(selected.length<72||affiliations.size<6||
   [...meetings.values()].some(x=>x.length<2)||
   years.some((year,i)=>i>0&&year!==years[i-1]+1))
   return {status:'WITHHELD_RANK_OR_GROUP_IDENTIFICATION',
     reason:'Too few original observations, repeated affiliations, per-meeting records, or noncontiguous declared years.',
     sample_size:selected.length,years:years.length};
 const p=selected[0].fixed_covariates.length;
 const xtx=new Float64Array(p*p);
 for(const r of selected)for(let i=0;i<p;i++)for(let j=0;j<p;j++)
   xtx[i*p+j]+=r.fixed_covariates[i]*r.fixed_covariates[j];
 const gram=chol(xtx,p,1e-8);
 if(!gram||gram.min_diag/gram.max_diag<1e-5)
   return {status:'WITHHELD_RANK_OR_GROUP_IDENTIFICATION',
     reason:'Declared covariate design matrix is rank-deficient or numerically confounded.',
     sample_size:selected.length,years:years.length};
 return {
   status:'DESIGN_IDENTIFIABLE_FOR_SYNTHETIC_PROBE_ONLY',
   selected,yearCount:years.length,meetingCount:meetings.size,
   affiliationCount:affiliations.size,
   selection_mechanism:mechanism,
   x_columns:p,source_design_sha256:panel.source_design_sha256,
   selection_sha256:panel.selection_sha256,
   samples_per_year:[...perYear.values()].map(x=>x.size),
   covariance_parameters_provably_identifiable:false,
   real_source_group_exchangeability_verified:false,
   empirical_inference_eligible:false
 };
}
function preprocess(verified){
 const r=verified.selected,n=r.length,p=verified.x_columns,year=r.map(x=>x.year_index);
 const yy=new Float64Array(n);
 const x=new Float64Array(n*p),sameM=new Uint8Array(n*n),sameA=new Uint8Array(n*n),
   gap=new Uint8Array(n*n);
 let avg=0;
 r.forEach((row,i)=>{
   yy[i]=row.response;avg+=row.response;
   row.fixed_covariates.forEach((v,j)=>x[i*p+j]=v);
 });
 avg/=n;
 const variance=yy.reduce((s,v)=>s+(v-avg)**2,0)/Math.max(1,n-1);
 for(let i=0;i<n;i++)for(let j=0;j<=i;j++){
   const k=i*n+j,q=j*n+i;
   sameM[k]=sameM[q]=Number(r[i].meeting_id===r[j].meeting_id);
   sameA[k]=sameA[q]=Number(r[i].affiliation_id===r[j].affiliation_id);
   const d=Math.abs(year[i]-year[j]);
   check(d<256,'year separation exceeds declared finite-design grid');
   gap[k]=gap[q]=d;
 }
 return {n,p,x,y:yy,sameM,sameA,gap,scale:Math.max(1e-6,variance)};
}
function objective(data,params){
 const {n,p,x,y,sameM,sameA,gap,scale}=data;
 const varRatio=params.slice(0,4).map(t=>Math.exp(Math.max(-10,Math.min(Math.log(8),t))));
 const [vm,va,vy,ve]=varRatio.map(t=>t*scale);
 const rho=.85*Math.tanh(params[4]);
 const v=new Float64Array(n*n);
 const rhoPows=Array.from({length:256},(_,i)=>Math.pow(rho,i));
 for(let i=0;i<n;i++)for(let j=0;j<=i;j++){
   const k=i*n+j;
   const u=vm*sameM[k]+va*sameA[k]+vy*rhoPows[gap[k]]+(i===j?ve:0);
   v[k]=v[j*n+i]=u;
 }
 const L=chol(v,n,Math.max(1e-12,scale*1e-10));
 if(!L)return {nll:Infinity,reason:'non_positive_covariance'};
 const z=forward(L.matrix,n,y);
 const w=new Float64Array(n*p);
 for(let j=0;j<p;j++){
   const col=forward(L.matrix,n,Array.from({length:n},(_,i)=>x[i*p+j]));
   for(let i=0;i<n;i++)w[i*p+j]=col[i];
 }
 const xtx=new Float64Array(p*p),xty=new Float64Array(p);
 for(let i=0;i<n;i++)for(let j=0;j<p;j++){
   xty[j]+=w[i*p+j]*z[i];
   for(let k=0;k<=j;k++)xtx[j*p+k]+=w[i*p+j]*w[i*p+k];
 }
 for(let i=0;i<p;i++)for(let j=0;j<i;j++)xtx[j*p+i]=xtx[i*p+j];
 const R=chol(xtx,p,1e-12);
 if(!R)return {nll:Infinity,reason:'fixed_effect_rank_deficient'};
 const temp=forward(R.matrix,p,xty),beta=backward(R.matrix,p,temp);
 let ss=0;
 for(let i=0;i<n;i++){
   let e=z[i];
   for(let j=0;j<p;j++)e-=w[i*p+j]*beta[j];
   ss+=e*e;
 }
 let logdet=0;
 for(let i=0;i<n;i++)logdet+=Math.log(L.matrix[i*n+i]);
 for(let i=0;i<p;i++)logdet+=Math.log(R.matrix[i*p+i]);
 const nll=logdet+.5*ss+.5*(n-p)*Math.log(2*Math.PI);
 return {nll:Number.isFinite(nll)?nll:Infinity,
   variance:{meeting:vm,affiliation:va,year:vy,residual:ve},rho,beta:[...beta],
   covariance_cholesky_min_diagonal:L.min_diag,
   fixed_design_cholesky_min_diagonal:R.min_diag};
}
function minimize(data,{maxEvaluations=1000}={}){
 let evaluations=0,best=null;
 const starts=[-.7,0,.7];
 for(const rhoStart of starts){
   const start=[
     Math.log(.23),Math.log(.23),Math.log(.23),Math.log(.38),
     Math.atanh(Math.max(-.95,Math.min(.95,rhoStart/.85)))
   ];
   let params=start,estimate=objective(data,params);
   evaluations++;
   for(const step of [1.1,.5,.22,.085]){
     for(let iter=0;iter<5;iter++){
       let improved=false;
       for(let coordinate=0;coordinate<5;coordinate++){
         for(const sign of [-1,1]){
           if(evaluations>=maxEvaluations)break;
           const option=params.slice();
           option[coordinate]+=sign*step;
           if(coordinate<4)option[coordinate]=Math.max(-10,Math.min(Math.log(8),option[coordinate]));
           else option[coordinate]=Math.max(-4,Math.min(4,option[coordinate]));
           const obj=objective(data,option);
           evaluations++;
           if(obj.nll+1e-8<estimate.nll){
             params=option;estimate=obj;improved=true;
           }
         }
       }
       if(!improved||evaluations>=maxEvaluations)break;
     }
     if(evaluations>=maxEvaluations)break;
   }
   if(!best||estimate.nll<best.estimate.nll)
     best={params,estimate};
   if(evaluations>=maxEvaluations)break;
 }
 return {best,evaluations,evaluation_budget:maxEvaluations};
}
function fit(panel,options={}){
 check(options&&
   Object.keys(options).every(x=>['maximum_evaluations'].includes(x)),
   'no oracle parameters or external nuisance settings accepted by fitter');
 const quality=verify(panel);
 if(quality.status!=='DESIGN_IDENTIFIABLE_FOR_SYNTHETIC_PROBE_ONLY')
   return {schema:'un.w1w2.nuisance-reml.candidate.v0',status:quality.status,
     reason:quality.reason,source_scope:'synthetic_numeric_only',
     sample_size:quality.sample_size??0,scientific_gates_passed:0,
     eligible_for_real_inference:false,publication_eligible:false};
 const prep=preprocess(quality);
 const result=minimize(prep,{maxEvaluations:options.maximum_evaluations??1000});
 const b=result.best;
 check(b&&Number.isFinite(b.estimate.nll),'no finite candidate restricted likelihood');
 const e=b.estimate;
 const warning=[];
 if(Math.abs(e.rho)>.77)warning.push('ar1_profile_near_bound');
 if(Object.values(e.variance).some(v=>v<prep.scale*0.0001))
   warning.push('variance_component_near_zero_boundary');
 if(result.evaluations>=result.evaluation_budget)
   warning.push('optimizer_budget_exhausted');
 if(quality.yearCount<16)
   warning.push('engineering_preflight_only_fewer_than_sixteen_years');
 if(quality.selection_mechanism!=='complete')
   warning.push('selection_mask_conditioned_on_declared_X_not_estimated');
 return {
   schema:'un.w1w2.nuisance-reml.candidate.v0',
   status:warning.length?'SYNTHETIC_ESTIMATOR_WARNING':'SYNTHETIC_ESTIMATOR_DIAGNOSTIC_ONLY',
   source_scope:'synthetic_numeric_only',
   original_design_sha256:quality.source_design_sha256,
   selected_response_sha256:quality.selection_sha256,
   effective_observations:prep.n,
   original_inventory:panel.source_inventory_total,
   verified_not_selected:panel.available_not_selected,
   unavailable_sources:panel.unavailable_sources,
   source_meetings:quality.meetingCount,years:quality.yearCount,
   recurring_affiliations:quality.affiliationCount,
   parameters_estimated_from_observations_only:true,
   estimated_variances:e.variance,estimated_year_rho:e.rho,
   fitted_fixed_effects:e.beta,
   objective:'Gaussian REML (candidate) - partial out fixed effect coefficients, fit positive covariance components and bounded AR1',
   restricted_negative_log_likelihood:e.nll,
   covariance_cholesky_min_diagonal:e.covariance_cholesky_min_diagonal,
   fixed_design_cholesky_min_diagonal:e.fixed_design_cholesky_min_diagonal,
   optimizer_evaluations:result.evaluations,
   optimizer_budget:result.evaluation_budget,
   warnings:warning,
   parameter_standard_errors:null,
   covariance_coverage_validated:false,
   nuisance_parameter_estimation_accepted:false,
   source_dependence_exchangeability_verified:false,
   scientific_gates_passed:0,
   eligible_for_real_inference:false,
   publication_eligible:false
 };
}
module.exports={fit,verify,objective,preprocess};
