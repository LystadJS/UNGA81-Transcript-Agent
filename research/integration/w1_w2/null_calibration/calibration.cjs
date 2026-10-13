'use strict';
/*
 * Full native W1 -> W2 synthetic oracle-reference calibration.
 * Every draw recomputes lexical TF-IDF/PCA/LSA, five clustering methods,
 * meeting-group refits, W2 full provenance and family-balanced co-assignment.
 * No actual UN texts or observations are loaded. Smoke != inferential PASS.
 */
const {lock,deriveSeed}=require('./lock.cjs');
const World=require('./world.cjs');
const Dependence=require('./dependence.cjs');
const W1=require('../../../validation_framework/runner.cjs');
const W1V1=require('../../../validation_framework/interchange.cjs');
const Grouped=require('../grouped_refits.cjs');
const W2=require('../../../consensus/consensus.cjs');
const check=(v,m)=>{if(!v)throw Error('synthetic-null-calibration: '+m);};
const round=x=>Number.isFinite(x)?Math.round(x*1e9)/1e9:null;
function statistic(consensus,original,policy,{syntheticSourceFrame}={}){
 check(consensus?.schema==='un.consensus.v1'&&consensus.publication_eligible===false &&
   original?.producer?.fixture_kind==='synthetic' &&
   original.cohort.split==='synthetic' &&
   syntheticSourceFrame?.schema==='un.source-validation.frame.v1' &&
   syntheticSourceFrame.split==='synthetic' &&
   syntheticSourceFrame.source_schema==='un.source-validation.synthetic.v1' &&
   syntheticSourceFrame.source_sha256===original.upstream.source_sha256,
   'synthetic W2 pair ledger and original source-bound nuisance frame required');
 // The canonical W1 v1 exporter carries ID/hash/meeting but intentionally
 // does NOT carry language/genre. A separately validated, private-in-memory
 // synthetic design companion is required before computing stratum values.
 const rows=new Map(syntheticSourceFrame.observations.map(x=>[x.id,x]));
 check(rows.size===original.observations.length &&
   original.observations.every(x=>{
     const o=rows.get(x.id);
     return o&&o.text_sha256===x.text_sha256 &&
       o.meeting_id===x.meeting_id &&
       o.parent_id===x.parent_id &&
       o.source_family_id===x.source_family_id &&
       o.source_status===x.source_status &&
       JSON.stringify(o.exclusion_reasons)===JSON.stringify(x.exclusion_reasons);
   }),'synthetic nuisance covariates do not join the authenticated v1 original source identity');
 check([...rows.values()].filter(x=>x.source_status==='available').every(x=>
   typeof x.genre==='string'&&typeof x.language==='string'),
   'verified nuisance genre/language metadata required, never imputed');
 const strata=Object.fromEntries(policy.strata.map(k=>[k,{
   name:k,eligible_cross_source_pairs:0,
   observed_jointly_assigned_pairs:0,missing_or_null_pairs:0,
   qualifying_pairs:0,failed_fit_pair_opportunities:0
 }]));
 for(const pair of consensus.pairs){
   if(pair.observation_a===pair.observation_b)continue;
   const a=rows.get(pair.observation_a),b=rows.get(pair.observation_b);
   check(a&&b,'W2 pair lost original source identity');
   if(a.source_status!=='available'||b.source_status!=='available' ||
     a.exclusion_reasons.length||b.exclusion_reasons.length)continue;
   if(a.meeting_id===b.meeting_id ||
     a.parent_id&&a.parent_id===b.parent_id ||
     a.source_family_id&&a.source_family_id===b.source_family_id)continue;
   const keys=['all_cross_meeting'];
   if(a.genre!==b.genre)keys.push('different_genre_cross_meeting');
   if(a.language!==b.language)keys.push('different_language_cross_meeting');
   const qualifies=pair.association!==null &&
     pair.association>=policy.association_cutoff &&
     pair.assignment_coverage!==null &&
     pair.assignment_coverage>=policy.assignment_coverage_cutoff &&
     pair.contributing_families.length>=policy.min_contributing_families;
   for(const key of keys){
     const r=strata[key];check(r,'unapproved global statistic stratum');
     r.eligible_cross_source_pairs++;
     if(pair.assigned_both_count>0)r.observed_jointly_assigned_pairs++;
     if(pair.association===null)r.missing_or_null_pairs++;
     r.failed_fit_pair_opportunities+=pair.failed_fit_count;
     if(qualifies)r.qualifying_pairs++;
   }
 }
 const total=strata.all_cross_meeting.eligible_cross_source_pairs;
 check(total>0,'no original eligible cross-meeting pair opportunities');
 let max=-Infinity,selected=null,assessable=0;
 for(const key of policy.strata){
   const s=strata[key];
   s.declared_eligibility=s.eligible_cross_source_pairs>=policy.minimum_pairs_per_stratum;
   s.qualifying_fraction=s.declared_eligibility?
     round(s.qualifying_pairs/s.eligible_cross_source_pairs):null;
   s.weighted_search_score=s.declared_eligibility?
     round(s.qualifying_fraction*Math.sqrt(s.eligible_cross_source_pairs/total)):null;
   if(s.weighted_search_score!==null){
     assessable++;
     if(s.weighted_search_score>max){max=s.weighted_search_score;selected=key;}
   }
 }
 check(assessable===policy.strata.length,
   'one or more prespecified source strata lack sufficient pair denominator');
 return {statistic_id:policy.id,value:round(max),selected_stratum:selected,
   searched_strata:policy.strata.length,
   total_cross_meeting_pairs:total,strata,
   status:'descriptive_synthetic_test_statistic_not_empirical_significance'};
}
function wilsonUpper(k,n,confidence=.95){
 check(Number.isInteger(k)&&Number.isInteger(n)&&n>0&&k>=0&&k<=n&&
   confidence===.95,'valid binomial numerator and one-sided confidence required');
 const z=1.6448536269514722,p=k/n,z2=z*z;
 return round((p+z2/(2*n)+z*Math.sqrt(p*(1-p)/n+z2/(4*n*n)))/(1+z2/n));
}
async function fitDraw(scenario,seed,protocol,{nullReference=false}={}){
 const world=World.generate(scenario,seed,{nullReference});
 const audit=Dependence.audit(world,scenario);
 if(!audit.group_refit_admissible)
   return {status:'WITHHELD_SOURCE_DEPENDENCE',reason:audit.withheld_reason,
     source_counts:{eligible:world.receipt.eligible,total:world.receipt.total,
       unavailable:world.receipt.unavailable},
     design_sha256:world.design.attendance_fingerprint,dependence:audit,
     attempted_full_methods:0,attempted_group_fits:0,
     fitted_source_sha256:world.receipt.source_sha256};
 const originalNative=await W1.run(world.frame,protocol.fixed_method_grid,{
   group_units:[protocol.grouped_refits.unit],
   replicates:protocol.grouped_refits.replicates,
   fraction:protocol.grouped_refits.fraction,
   group_seed:protocol.grouped_refits.seed,
   retain_group_assignments:protocol.grouped_refits.retain_original_child_labels
 });
 const original=W1V1.toInterchangeV1(originalNative);
 const joined=Grouped.withGroupedRefits(originalNative,original);
 W2.validateConsensus(joined.consensus);
 const checkSource=joined.consensus.source;
 check(checkSource.source_sha256===world.receipt.source_sha256 &&
   checkSource.selection_sha256===world.receipt.selection_sha256,
   'W2 result/source selection mismatch');
 const scored=statistic(joined.consensus,original,protocol.statistic,{syntheticSourceFrame:world.frame});
 const full=originalNative.fit_records.map(f=>({id:f.model_id,status:f.status,
   attempted:f.attempted_fit,successful:f.successful_fit,failed:f.failed_fit,
   unassigned:f.assignments?.filter(x=>x===0).length??0}));
 const counts=joined.audit.attempts;
 const planned=joined.consensus.pairs[0]?.planned_count;
 return {
   status:'SYNTHETIC_DESCRIPTIVE',source_counts:{total:world.receipt.total,
     eligible:world.receipt.eligible,unavailable:world.receipt.unavailable},
   design_sha256:world.design.attendance_fingerprint,
   fitted_source_sha256:world.receipt.source_sha256,
   selection_sha256:world.receipt.selection_sha256,
   dependence:audit,full_fit_attempts:full.reduce((x,f)=>x+f.attempted,0),
   full_fit_successes:full.reduce((x,f)=>x+f.successful,0),
   full_fit_failures:full.reduce((x,f)=>x+f.failed,0),
   skipped_full_fits:full.filter(f=>f.status==='skipped').length,
   unassigned_full_fit_points:full.reduce((x,f)=>x+f.unassigned,0),
   grouped_fit_planned:counts.planned,grouped_fit_attempted:counts.attempted,
   grouped_fit_successes:counts.successful,grouped_fit_failures:counts.failed,
   grouped_fit_skips:counts.skipped,
   distinct_source_selections:joined.audit.distinct_group_samples,
   planned_model_records:planned,method_family_count:joined.consensus.family_weight_audit.length,
   test_statistic:scored
 };
}
function scenarioStatus(s,worlds,inner,protocol){
 const failed=worlds.filter(w=>w.status!=='ORACLE_REFERENCE_PILOT').length;
 const nullScenario=s.truth==='null';
 const complete=worlds.length===protocol.calibration.outer_worlds_per_null_regime_min &&
   inner>=protocol.calibration.corrected_reference_draws_min;
 const valid=complete&&failed===0&&nullScenario;
 const k=valid?worlds.filter(w=>w.corrected_tail_p<=protocol.calibration.alpha_global).length:null;
 const upper=valid?wilsonUpper(k,worlds.length):null;
 return {
   scenario_id:s.id,truth:s.truth,
   status:failed?'WITHHELD_NONDELIVERY':
     complete?'ORACLE_SYNTHETIC_CALIBRATION_ONLY_NOT_EMPIRICAL':
       'PILOT_UNDERPOWERED_NOT_CALIBRATION',
   worlds_requested:worlds.length,worlds_delivered:worlds.length-failed,
   worlds_failed_or_withheld:failed,
   reference_draws_per_world:inner,
   reference_draws_attempted:worlds.reduce((x,w)=>x+w.reference_attempted,0),
   reference_draws_completed:worlds.reduce((x,w)=>x+w.reference_completed,0),
   reference_draws_failed:worlds.reduce((x,w)=>x+w.reference_failed,0),
   observed_worlds_with_numeric_statistic:worlds.filter(w=>w.observed_statistic!==null).length,
   synthetic_null_rejections:k,
   null_rejection_rate:valid?round(k/worlds.length):null,
   upper_wilson_null_false_rejection_rate:upper,
   proposed_upper_limit_met:valid?upper<=protocol.calibration.nominal_type1_upper_wilson_threshold:null,
   inferential_eligible:false,
   empirical_evaluation_authorized:false,publication_eligible:false,
   warnings:[
     'Synthetic oracle nuisance parameters are known from the generator, not estimated from source data.',
     'Failed/withheld worlds remain in denominators; do not select only delivering replicates.',
     'Source-group labels, simulated year effects, missingness and group closure are not actual UN source exchangeability.'
   ]
 };
}
async function calibration({mode='smoke',scenarioIds=null,outerStart=0,
  outerCount=null,referenceDraws=null}={}){
 const frozen=lock(),p=frozen.protocol;
 check(['smoke','pilot','full_shard'].includes(mode),'use declared smoke, pilot or full_shard');
 const preset=mode==='smoke'?p.calibration.ci_smoke:p.calibration.pilot;
 const worlds=outerCount??preset.outer_worlds;
 const inner=referenceDraws??preset.reference_draws;
 check(Number.isSafeInteger(outerStart)&&outerStart>=0&&
   Number.isSafeInteger(worlds)&&worlds>=1&&
   Number.isSafeInteger(inner)&&inner>=1,'invalid simulation budget');
 if(mode==='smoke')check(worlds===2&&inner===7&&outerStart===0,
   'CI smoke budgets are frozen; use pilot for changes');
 if(mode==='pilot')check(worlds<=p.calibration.pilot.outer_worlds &&
   inner<=p.calibration.pilot.reference_draws &&
   outerStart===0,'pilot cannot silently raise planned budget');
 if(mode==='full_shard')check(worlds===1&&inner===1999&&outerStart<1000,
   'full synthetic protocol requires 1 outer world/shard, 1999 references, explicit environment budget');
 const declared=p.nuisance_worlds;
 const selections=scenarioIds===null?declared:
   declared.filter(s=>scenarioIds.includes(s.id));
 check(selections.length>0&&(!scenarioIds||
   selections.length===scenarioIds.length&&new Set(scenarioIds).size===scenarioIds.length),
   'only frozen nuisance scenarios are allowed');
 const summaries=[],detailed=[];
 for(const scenario of selections){
   const records=[];
   for(let i=outerStart;i<outerStart+worlds;i++){
     const seed=deriveSeed(frozen.protocol_sha256,scenario.id,i,-1,'observed');
     let observed;
     try{observed=await fitDraw(scenario,seed,p,{nullReference:false});}
     catch(e){records.push({
       status:'WITHHELD_OBSERVED_FIT_FAILURE',world_index:i,
       reason:String(e.message||e).slice(0,260),
       observed_statistic:null,reference_attempted:0,reference_completed:0,reference_failed:0,
       corrected_tail_p:null
     });continue;}
     const record={
       status:observed.status==='SYNTHETIC_DESCRIPTIVE'?'ORACLE_REFERENCE_PILOT':observed.status,
       world_index:i,observed_seed:seed,
       observed_statistic:observed.test_statistic?.value??null,
       observed_stratum:observed.test_statistic?.selected_stratum??null,
       source_group_count:observed.dependence?.distinct_meeting_labels??null,
       typed_dependence_flags:observed.dependence?.risk_flags||[],
       source_group_closure_components:observed.dependence?.meeting_parent_family_closure?.components??null,
       affiliation_augmented_components:observed.dependence?.affiliation_augmented_closure?.components??null,
       source_counts:observed.source_counts,
       grouped_fit_planned:observed.grouped_fit_planned??0,
       grouped_fit_attempted:observed.grouped_fit_attempted??0,
       grouped_fit_failures:observed.grouped_fit_failures??0,
       full_fit_failures:observed.full_fit_failures??0,
       reference_attempted:0,reference_completed:0,reference_failed:0,
       upper_reference_ties_or_exceedances:null,corrected_tail_p:null
     };
     if(record.status!=='ORACLE_REFERENCE_PILOT'){
       records.push(record);continue;
     }
     let successes=0,failed=0,upper=0;
     for(let b=0;b<inner;b++){
       record.reference_attempted++;
       const referenceSeed=deriveSeed(frozen.protocol_sha256,scenario.id,i,b,'reference');
       try{
         const reference=await fitDraw(scenario,referenceSeed,p,{nullReference:true});
         check(reference.status==='SYNTHETIC_DESCRIPTIVE' &&
           reference.design_sha256===observed.design_sha256 &&
           reference.source_counts.eligible===observed.source_counts.eligible &&
           reference.source_counts.unavailable===observed.source_counts.unavailable,
           'null generator failed to preserve source design/eligibility');
         successes++;
         if(reference.test_statistic.value>=record.observed_statistic)upper++;
       }catch(e){
         failed++;
         if(!record.first_failure_reason)record.first_failure_reason=String(e.message||e).slice(0,220);
       }
     }
     record.reference_completed=successes;
     record.reference_failed=failed;
     record.upper_reference_ties_or_exceedances=upper;
     if(failed||successes!==inner){
       record.status='WITHHELD_REFERENCE_NONDELIVERY';
       record.corrected_tail_p=null;
     }else {
       record.corrected_tail_p=round((1+upper)/(1+inner));
     }
     records.push(record);
   }
   summaries.push(scenarioStatus(scenario,records,inner,p));
   detailed.push({scenario_id:scenario.id,worlds:records});
 }
 const attempt=sum=>summaries.reduce((v,x)=>v+x[sum],0);
 return {
   schema:'un.w1-w2.synthetic-null.calibration-audit.v1',
   protocol_sha256:frozen.protocol_sha256,protocol_git_blob_sha1:frozen.protocol_blob_sha1,
   status:'SYNTHETIC_ENGINEERING_ONLY_NO_EMPIRICAL_INFERENCE',
   mode,source_split:'synthetic',analysis_population:'fictional invented samples',
   num_scenarios:selections.length,scenarios:summaries,
   attempted_reference_draws:attempt('reference_draws_attempted'),
   successful_reference_draws:attempt('reference_draws_completed'),
   failed_reference_draws:attempt('reference_draws_failed'),
   worlds_attempted:selections.length*worlds,
   worlds_delivered:attempt('worlds_delivered'),
   worlds_withheld:attempt('worlds_failed_or_withheld'),
   full_g09_calibration_executed:false,
   inferential_eligible:false,empirical_evaluation_authorized:false,
   publication_eligible:false,
   g01_g13_all_not_run:true,reserved_transcripts_opened:0,
   notes:[
     'Monte Carlo fractions are pilot/oracle diagnostics only, not empirical p-values.',
     'No nuisance parameters are estimated from real sources; the source dependency graph and exchangeability remain unverified.',
     'A full synthetic run alone does not satisfy G01–G13, and this module cannot authorize publication.'
   ],
   detail:detailed
 };
}
module.exports={statistic,wilsonUpper,fitDraw,calibration,scenarioStatus};
