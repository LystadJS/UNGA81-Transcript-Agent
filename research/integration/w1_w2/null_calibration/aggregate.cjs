'use strict';
/*
 * Aggregate disjoint future 1-world/1999-reference synthetic shards without
 * pretending missing or failed draws are independent success.
 */
const {lock,deriveSeed}=require('./lock.cjs');
const {wilsonUpper}=require('./calibration.cjs');
const fail=m=>{throw Error('synthetic-null-shard: '+m);};
const check=(x,m)=>{if(!x)fail(m);};
function aggregate(shards){
 const {protocol:p,protocol_sha256:sha}=lock();
 check(Array.isArray(shards)&&shards.length>0,'source-free synthetic shard reports required');
 const all=new Map(p.nuisance_worlds.map(s=>[s.id,new Map()]));
 for(const shard of shards){
   check(shard&&shard.schema==='un.w1-w2.synthetic-null.calibration-audit.v1' &&
     shard.protocol_sha256===sha && shard.mode==='full_shard' &&
     shard.source_split==='synthetic' &&
     shard.inferential_eligible===false&&shard.publication_eligible===false &&
     shard.empirical_evaluation_authorized===false&&shard.reserved_transcripts_opened===0,
     'only frozen source-free full-shard results admitted');
   check(shard.scenarios.length===1 && shard.detail.length===1 &&
     shard.scenarios[0].scenario_id===shard.detail[0].scenario_id &&
     shard.detail[0].worlds.length===1 &&
     shard.scenarios[0].reference_draws_per_world===1999,
     'one exact world/scenario with all 1999 planned references required per shard');
   const id=shard.detail[0].scenario_id;
   const world=shard.detail[0].worlds[0], scenario=p.nuisance_worlds.find(x=>x.id===id);
   check(scenario&&Number.isInteger(world.world_index)&&
     world.world_index>=0&&world.world_index<1000,
     'world index or invented nuisance regime outside frozen plan');
   check(world.observed_seed===deriveSeed(sha,id,world.world_index,-1,'observed'),
     'world seed disagrees with immutable synthetic design');
   const byWorld=all.get(id);
   check(!byWorld.has(world.world_index),'duplicate world index/seed masquerading as independent replication');
   byWorld.set(world.world_index,world);
 }
 const summaries=[];
 for(const scenario of p.nuisance_worlds){
   const worlds=[...all.get(scenario.id).values()];
   const complete=worlds.length===1000;
   const delivered=worlds.filter(w=>w.status==='ORACLE_REFERENCE_PILOT'&&
     w.reference_attempted===1999&&w.reference_completed===1999&&
     w.reference_failed===0&&w.corrected_tail_p!==null);
   const withheld=worlds.length-delivered.length;
   const misses=1000-worlds.length;
   const applicable=complete&&withheld===0&&scenario.truth==='null';
   const reject=applicable?delivered.filter(w=>w.corrected_tail_p<=.05).length:null;
   const wilson=applicable?wilsonUpper(reject,1000):null;
   summaries.push({
     scenario_id:scenario.id,truth:scenario.truth,
     attempted_outer_worlds:worlds.length,missing_outer_worlds:misses,
     delivered_outer_worlds:delivered.length,withheld_outer_worlds:withheld,
     reference_draws_attempted:worlds.reduce((x,w)=>x+(w.reference_attempted||0),0),
     reference_draws_completed:worlds.reduce((x,w)=>x+(w.reference_completed||0),0),
     reference_draws_failed:worlds.reduce((x,w)=>x+(w.reference_failed||0),0),
     null_rejections:reject,oracle_null_rejection_rate:reject===null?null:reject/1000,
     oracle_upper_one_sided_wilson_95:wilson,
     oracle_acceptance_criterion_met:wilson===null?null:wilson<=0.075,
     scientific_status:'NOT_RUN',
     status:misses||withheld?'WITHHELD_INCOMPLETE_OR_DEPENDENT':
       scenario.truth==='positive'?'SYNTHETIC_POWER_REFERENCE_ONLY':
       'COMPLETE_ORACLE_BUT_NOT_REAL_NUISANCE_CALIBRATION'
   });
 }
 const allNull=summaries.filter(s=>s.truth==='null');
 return {
   schema:'un.w1-w2.synthetic-null.aggregate-shards.v1',
   protocol_sha256:sha,planned_outer_per_regime:1000,
   planned_reference_draws_per_outer:1999,
   total_shards:shards.length,
   all_null_regimes_complete:allNull.every(x=>
     x.attempted_outer_worlds===1000&&x.withheld_outer_worlds===0),
   all_oracle_false_positive_screens_met:allNull.every(x=>
     x.oracle_acceptance_criterion_met===true),
   all_scientific_gates_NOT_RUN:true,passed_scientific_gates:0,
   empirical_inference_eligible:false,public_release_eligible:false,
   statuses:summaries,
   limitations:[
     'Oracle nuisance parameters are invented, not independently estimated or validated from original UN sources.',
     'Cross-meeting source family closure and few effective year blocks cannot be repaired by more Monte Carlo draws.',
     'An oracle false-positive screen is not a valid empirical p-value or a finding about diplomatic structures.'
   ]
 };
}
module.exports={aggregate};
