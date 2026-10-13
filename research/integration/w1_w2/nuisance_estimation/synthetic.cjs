'use strict';
/*
 * Fictional scalar lexical-proxy response, not actual text, embeddings or
 * diplomatic positions. Ground truth is returned separately, never in panel.
 */
const crypto=require('node:crypto');
const {rng,normal}=require('../null_calibration/lock.cjs');
const hash=x=>crypto.createHash('sha256').update(typeof x==='string'?x:JSON.stringify(x)).digest('hex');
const check=(ok,m)=>{if(!ok)throw Error('nuisance-design-synthetic: '+m);};
const BETA=[0.35,0.27,-0.18,0.12,0.31,0.22,-0.14];
const dot=(x,y)=>x.reduce((s,v,i)=>s+v*y[i],0);
function generate(scenario,seed){
 check(scenario && /^E\d/.test(scenario.id) &&
   Number.isSafeInteger(seed)&&seed>=0 && seed<=0xffffffff,
   'locked fictional scenario and UInt32 seed required');
 const random=rng(seed),years=scenario.years,perYear=scenario.meetings_per_year;
 const count=years*perYear*scenario.rows_per_meeting;
 check(count<=192&&years>=8&&perYear>=1,'unsupported synthetic source size');
 const meetingShock=Array.from({length:years*perYear},
   ()=>Math.sqrt(scenario.meeting_variance)*normal(random));
 const affiliationShock=Array.from({length:scenario.affiliations},
   ()=>Math.sqrt(scenario.affiliation_variance)*normal(random));
 const yearShock=[];
 for(let t=0;t<years;t++) {
   const eta=normal(random);
   yearShock.push(t===0?eta:scenario.year_rho*yearShock[t-1]+
     Math.sqrt(1-scenario.year_rho**2)*eta);
 }
 const rows=[];
 for(let t=0;t<years;t++)for(let m=0;m<perYear;m++)
 for(let j=0;j<scenario.rows_per_meeting;j++){
   const idx=t*perYear+m,affiliation=(j+2*m+t)%scenario.affiliations;
   const genre=(j+t)%2,language=(m+j+t)%2,role=(j+m)%2;
   const agenda=(j+t+m)%3;
   const length=(13+(j+2*t+m)%17-20)/10;
   const X=[1,genre,language,role,length,Number(agenda===1),Number(agenda===2)];
   const y=dot(BETA,X)+meetingShock[idx]+affiliationShock[affiliation]+
     Math.sqrt(scenario.year_variance)*yearShock[t]+
     Math.sqrt(scenario.residual_variance)*normal(random);
   const key='fictitious-'+scenario.id+'-y'+t+'-m'+m+'-r'+j;
   const family=(scenario.id==='E6_shared_source_family'&&m===0&&j===0&&(t===0||t===1))?
     'fictional-cross-meeting-source-family':'fictional-source-family-'+idx+'-'+j;
   const parent='fictional-parent-'+idx+'-'+j;
   const missingDueX=scenario.selection==='depends_on_observed_covariates' &&
     agenda===2&&j%3===2;
   const missingDueY=scenario.selection==='depends_on_latent_response'&&
     y > BETA[0]+Math.sqrt(scenario.residual_variance)*0.25;
   const selected=!(missingDueX||missingDueY);
   rows.push({
     id:key,
     source_status:'synthetic_available',
     selection_status:selected?'selected_eligible':'available_not_selected',
     missing_reason:selected?null:(missingDueY?
       'Synthetic selection depends on unobserved outcome; MNAR':'Deterministic design covariate mask'),
     source_hash_basis:'synthetic',
     meeting_id:'fictional-meeting-'+idx,meeting_index:idx,
     source_family_id:family,parent_id:parent,
     affiliation_id:'fictional-affiliation-'+affiliation,affiliation_index:affiliation,
     calendar_year:2000+t,year_index:t,
     fixed_covariates:X,genre,language,role,agenda,length,
     response:selected?y:null,
     response_sha256:selected?hash(y.toPrecision(17)):null
   });
 }
 // Original-source unavailable opportunities are never assigned fake y or 0.
 for(let i=0;i<years;i++)rows.push({
   id:'fictional-unavailable-'+scenario.id+'-'+i,source_status:'synthetic_unavailable',
   selection_status:'unavailable_source',missing_reason:'Invented source not collected',
   source_hash_basis:'synthetic',
   meeting_id:null,meeting_index:null,source_family_id:null,parent_id:null,
   affiliation_id:null,affiliation_index:null,calendar_year:2000+i,year_index:i,
   fixed_covariates:null,genre:null,language:null,role:null,agenda:null,length:null,
   response:null,response_sha256:null
 });
 const sourceIdentity=rows.map(x=>[x.id,x.source_status,x.selection_status,
   x.meeting_id,x.source_family_id,x.parent_id,x.affiliation_id,x.calendar_year,
   x.fixed_covariates]);
 const selected=rows.filter(x=>x.selection_status==='selected_eligible');
 const panel={
   schema:'un.w1w2.nuisance-estimation.synthetic-panel.v0',
   producer:{kind:'invented_numerical_proxy',scenario_id:scenario.id,seed,
     scientific_authority:'none',publication_eligible:false},
   source_hash_basis:'synthetic',source_design_sha256:hash(sourceIdentity),
   selection_sha256:hash(selected.map(x=>[x.id,x.response_sha256])),
   source_inventory_total:rows.length,selected_eligible:selected.length,
   available_not_selected:rows.filter(x=>x.selection_status==='available_not_selected').length,
   unavailable_sources:years,selection_mechanism:scenario.selection,
   year_index_source:'invented 2000+ annual steps',
   full_design_rows:rows,
   source_group_exchangeability_verified:false,
   inferential_eligible:false,empirical_evaluation_authorized:false,
   publication_eligible:false
 };
 return {panel,truth:{
   // A synthetic QA oracle, NEVER supplied to the estimator.
   scenario_id:scenario.id,seed,year_rho:scenario.year_rho,
   variances:{meeting:scenario.meeting_variance,affiliation:scenario.affiliation_variance,
     year:scenario.year_variance,residual:scenario.residual_variance},
   fixed_effects:BETA,
   year_shocks:yearShock.slice(),source_groups:years*perYear
 }};
}
module.exports={generate};
