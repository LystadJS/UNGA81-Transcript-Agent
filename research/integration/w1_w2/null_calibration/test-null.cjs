'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const Crypto=require('./lock.cjs');
const World=require('./world.cjs');
const Dep=require('./dependence.cjs');
const Cal=require('./calibration.cjs');
const Run=require('./run.cjs');
const F=require('../../../validation_framework/frame.cjs');
const {protocol:p,protocol_sha256:sha}=Crypto.lock();
const get=id=>p.nuisance_worlds.find(x=>x.id===id);
const source=()=>{
 const s=fs.readFileSync(path.join(__dirname,'protocol.v1.locked.json'));
 return Crypto.gitBlobSha1(s);
};

test('prospectively frozen SHA/Git-blob lock was created before simulations',()=>{
 assert.equal(source(),Crypto.GIT_BLOB_SHA1);
 assert.equal(sha.length,64);
 assert.equal(p.status,'frozen_for_fictional_synthetic_simulation_only');
 assert.equal(p.calibration.corrected_reference_draws_min,1999);
 assert.equal(p.calibration.outer_worlds_per_null_regime_min,1000);
 assert.equal(p.calibration.alpha_global,.05);
 assert.equal(p.eligible_for_real_inference,false);
 assert.notEqual(Crypto.gitBlobSha1(Buffer.from('tampered protocol')),Crypto.GIT_BLOB_SHA1);
});

test('source scope and 13 frozen inference gates cannot be bypassed',()=>{
 const result=Crypto.lock();
 assert.equal(result.status.gates_not_run,13);
 assert.equal(result.status.gates_passed,0);
 assert.equal(result.status.empirical_evaluation_authorized,false);
 assert.equal(result.status.inferential_eligible,false);
 assert.equal(result.status.publication_eligible,false);
 assert.equal(p.source_inputs.read_private_historical_sources,false);
 assert.equal(p.source_inputs.read_original_UN_documents,false);
 assert.equal(p.source_inputs.access_reserved_october_5_6_2026,false);
});

test('six predeclared source-nuisance scenarios have exactly five nulls and one known positive',()=>{
 assert.equal(p.nuisance_worlds.length,6);
 assert.equal(p.nuisance_worlds.filter(x=>x.truth==='null').length,5);
 assert.equal(p.nuisance_worlds.filter(x=>x.truth==='positive').length,1);
 assert.equal(new Set(p.nuisance_worlds.map(x=>x.id)).size,6);
 assert.deepEqual(p.statistic.strata,[
  'all_cross_meeting','different_genre_cross_meeting',
  'different_language_cross_meeting']);
});

test('SHA-derived independent draws are deterministic and nonrepeating',()=>{
 const a=Crypto.deriveSeed(sha,'N1_independent',0,0,'reference');
 const b=Crypto.deriveSeed(sha,'N1_independent',0,0,'reference');
 const c=Crypto.deriveSeed(sha,'N1_independent',0,1,'reference');
 const d=Crypto.deriveSeed(sha,'N1_independent',1,0,'reference');
 assert.equal(a,b);
 assert.notEqual(a,c);
 assert.notEqual(a,d);
 assert.throws(()=>Crypto.deriveSeed(sha,'N1',0,0,'invented-domain'),/invalid deterministic/);
});

test('exact original IDs, statuses, lengths, duplicates and nuisance masks are preserved across null draws',()=>{
 for(const s of p.nuisance_worlds){
  const a=World.generate(s,31991,{nullReference:true});
  const b=World.generate(s,9321,{nullReference:true});
  assert.equal(a.receipt.attendance_fingerprint,b.receipt.attendance_fingerprint);
  assert.equal(a.receipt.total,b.receipt.total);
  assert.equal(a.receipt.eligible,b.receipt.eligible);
  assert.equal(a.receipt.unavailable,b.receipt.unavailable);
  assert.notEqual(a.receipt.source_sha256,b.receipt.source_sha256);
  assert.equal(a.receipt.source_hash_basis,'synthetic');
  assert.equal(F.validateFrame(a.frame).eligible.length,a.design.eligible);
  assert.equal(a.frame.observations.length,a.design.planned_total);
  for(const row of a.frame.observations){
   assert.equal(row.source_url,null);
   if(row.source_status==='available')assert.equal(F.digest(row.text),row.text_sha256);
   else assert.equal(row.text_sha256,null);
  }
  assert.equal(a.frame.observations.some(x=>Object.hasOwn(x,'p2_original_pdf_sha256')),false);
 }
});

test('a planted cross-meeting theme is present only in its positive world',()=>{
 const s=get('P1_cross_meeting_theme');
 const seed=Crypto.deriveSeed(sha,s.id,0,-1,'observed');
 const signal=World.generate(s,seed,{nullReference:false});
 const reference=World.generate(s,seed,{nullReference:true});
 assert.equal(signal.receipt.reference_signal_strength,1.5);
 assert.equal(reference.receipt.reference_signal_strength,0);
 const observed=signal.frame.observations.filter(o=>o.source_status==='available')
  .map(o=>o.text).join(' ');
 const nullText=reference.frame.observations.filter(o=>o.source_status==='available')
  .map(o=>o.text).join(' ');
 assert.match(observed,/planted/);
 assert.doesNotMatch(nullText,/planted/);
 assert.equal(signal.receipt.attendance_fingerprint,reference.receipt.attendance_fingerprint);
});

test('within-source nuisance duplicates and unequal group counts are accounted for, never counted as new independent groups',()=>{
 const s=get('N2_meeting_dominant');
 const x=World.generate(s,24777);
 const a=Dep.audit(x,s);
 assert(a.within_meeting_duplicate_text_groups>=2);
 assert.equal(a.distinct_meeting_labels,6);
 assert(a.meeting_parent_family_closure.components<=6);
 assert.equal(a.source_group_exchangeability_verified,false);
 assert.deepEqual(a.meeting_parent_family_closure.component_sizes.slice().sort((u,v)=>u-v),
  s.group_sizes.slice().sort((u,v)=>u-v));
});

test('cross-meeting original-source family linkage is a hard refusal, not a naive source bootstrap',()=>{
 const s=get('N3_cross_classified'),x=World.generate(s,20417);
 const a=Dep.audit(x,s);
 assert.equal(a.group_refit_admissible,false);
 assert(a.cross_meeting_original_source_family_links>=1);
 assert(a.meeting_parent_family_closure.components<8);
 assert(a.affiliation_augmented_closure.components<=a.meeting_parent_family_closure.components);
 assert(a.risk_flags.includes('cross_meeting_original_source_family_closure'));
 assert.match(a.withheld_reason,/crosses declared meeting/);
});

test('nonrandom attendance and few-year counts remain explicit, not speech absences or independent years',()=>{
 for(const id of ['N4_year_independent','N5_year_serial_ar1']){
  const s=get(id),x=World.generate(s,40221),a=Dep.audit(x,s);
  assert.equal(a.four_years_per_era,true);
  assert.equal(a.nonrandom_attendance,true);
  assert.equal(a.source_group_exchangeability_verified,false);
  assert(a.risk_flags.includes('four_years_per_era_insufficient_for_year_cluster_asymptotics'));
  assert(x.receipt.unavailable>=4);
  const missing=x.frame.observations.filter(o=>o.source_status==='unavailable');
  assert(missing.every(o=>o.missing_reason&&o.text_sha256===null));
 }
});

test('AR(1) nuisance year-shock mechanism independently recovers pinned dependence contrast',()=>{
 const independent=get('N4_year_independent'),serial=get('N5_year_serial_ar1');
 const covariance=s=>{
  let sum=0,n=0;
  for(let i=0;i<1000;i++){
   const seed=Crypto.deriveSeed(sha,s.id,i,-1,'shock');
   const x=World.generate(s,seed).year_shocks;
   for(let y=1;y<x.length;y++){sum+=x[y]*x[y-1];n++;}
  }
  return sum/n;
 };
 const ind=covariance(independent),ar=covariance(serial);
 assert(Math.abs(ind)<0.1,'independent-year covariance '+ind);
 assert(ar>0.5&&ar<0.8,'serial AR(1) covariance '+ar);
});

test('global statistic excludes self/within-meeting pairs and audits distinct requested strata',()=>{
 const s=get('N1_independent'),x=World.generate(s,9001);
 const included=x.frame.observations.filter(o=>o.source_status==='available');
 const original={
   producer:{fixture_kind:'synthetic'},
   cohort:{split:'synthetic'},
   upstream:{source_sha256:x.frame.source_sha256},
   observations:x.frame.observations
 };
 const keys=included.map(o=>o.id).sort();
 const pairs=[];
 for(let i=0;i<keys.length;i++)for(let j=i;j<keys.length;j++)pairs.push({
  observation_a:keys[i],observation_b:keys[j],
  association:i%2===j%2?.9:.1,assignment_coverage:.7,
  assigned_both_count:2,failed_fit_count:0,
  contributing_families:['partition','mixture']
 });
 const z=Cal.statistic({schema:'un.consensus.v1',publication_eligible:false,pairs},original,p.statistic,{syntheticSourceFrame:x.frame});
 assert(z.total_cross_meeting_pairs>0);
 assert(z.total_cross_meeting_pairs<keys.length*(keys.length-1)/2);
 assert.equal(z.searched_strata,3);
 assert(z.value>=0&&z.value<=1);
 assert.equal(z.status,'descriptive_synthetic_test_statistic_not_empirical_significance');
});

test('corrected reference tail never uses zero Monte Carlo probability',()=>{
 assert.equal((1+0)/(1+7),0.125);
 assert.equal((1+1)/(1+1999),0.001);
 assert(Cal.wilsonUpper(0,1000)<0.075);
 assert(Cal.wilsonUpper(100,1000)>0.075);
 assert.throws(()=>Cal.wilsonUpper(-1,1000),/valid binomial numerator/);
});

test('source-dependence refusal is kept as non-delivery under the entire frozen CI-smoke denominator',async()=>{
 const report=await Cal.calibration({mode:'smoke',scenarioIds:['N3_cross_classified']});
 assert.equal(report.worlds_attempted,2);
 assert.equal(report.worlds_withheld,2);
 assert.equal(report.attempted_reference_draws,0);
 assert.equal(report.scenarios[0].status,'WITHHELD_NONDELIVERY');
 assert.equal(report.scenarios[0].synthetic_null_rejections,null);
 assert.equal(report.inferential_eligible,false);
 assert.equal(report.g01_g13_all_not_run,true);
});

test('unmodified source-aware W1 and W2 actually refit synthetic methods including whole-meeting omissions',async()=>{
 const s=get('N1_independent');
 const x=await Cal.fitDraw(s,11773,p,{nullReference:true});
 assert.equal(x.status,'SYNTHETIC_DESCRIPTIVE');
 assert.equal(x.source_counts.eligible,24);
 assert.equal(x.source_counts.unavailable,1);
 assert.equal(x.method_family_count,4);
 assert.equal(x.grouped_fit_planned,15);
 assert.equal(x.planned_model_records,20);
 assert.equal(x.test_statistic.searched_strata,3);
 assert(x.test_statistic.total_cross_meeting_pairs>=150);
 assert.equal(x.dependence.inferential_eligible,false);
});

test('G01–G13 remain NOT_RUN after successful and withheld synthetic nuisance worlds',async()=>{
 const Ready=require('./readiness.cjs');
 const result=await Cal.calibration({mode:'smoke',scenarioIds:['N3_cross_classified']});
 const report=Ready.assess(result);
 assert.equal(report.scientific_gates_passed,0);
 assert.equal(report.scientific_gates_not_run,13);
 assert(report.gates.every(g=>g.scientific_status==='NOT_RUN'));
 assert.equal(report.actual_original_byte_authentication,false);
 assert.equal(report.real_nuisance_parameters_estimated,false);
 assert.equal(report.source_group_crossing_refusal_seen,true);
 assert.deepEqual(report.nuisance_withheld_regimes,['N3_cross_classified']);
 assert.equal(report.public_release_eligible,false);
 const corrupted=structuredClone(result);corrupted.inferential_eligible=true;
 assert.throws(()=>Ready.assess(corrupted),/refuses nonfrozen/);
});

test('future full-budget shards require unique frozen world indices and cannot declare G09 pass early',()=>{
 const Aggregate=require('./aggregate.cjs');
 const shard={
  schema:'un.w1-w2.synthetic-null.calibration-audit.v1',
  protocol_sha256:sha,mode:'full_shard',source_split:'synthetic',
  inferential_eligible:false,publication_eligible:false,
  empirical_evaluation_authorized:false,reserved_transcripts_opened:0,
  scenarios:[{scenario_id:'N1_independent',reference_draws_per_world:1999}],
  detail:[{scenario_id:'N1_independent',worlds:[{
   world_index:0,observed_seed:Crypto.deriveSeed(sha,'N1_independent',0,-1,'observed'),
   status:'ORACLE_REFERENCE_PILOT',
   reference_attempted:1999,reference_completed:1999,reference_failed:0,
   corrected_tail_p:0.037
  }]}]
 };
 const result=Aggregate.aggregate([shard]);
 assert.equal(result.total_shards,1);
 assert.equal(result.statuses[0].missing_outer_worlds,999);
 assert.equal(result.statuses[0].scientific_status,'NOT_RUN');
 assert.equal(result.all_null_regimes_complete,false);
 assert.equal(result.all_scientific_gates_NOT_RUN,true);
 assert.equal(result.empirical_inference_eligible,false);
 assert.throws(()=>Aggregate.aggregate([shard,shard]),/duplicate world index/);
 const bogus=structuredClone(shard);
 bogus.detail[0].worlds[0].observed_seed=1;
 assert.throws(()=>Aggregate.aggregate([bogus]),/world seed disagrees/);
 const published=structuredClone(shard);published.publication_eligible=true;
 assert.throws(()=>Aggregate.aggregate([published]),/frozen source-free/);
});

test('no synthetic summary path can modify frozen source repository or silently overwrite outputs',()=>{
 const root=path.resolve(__dirname,'../../../..');
 assert.throws(()=>Run.outputSafe(root),/inside the source repository/);
 assert.throws(()=>Run.outputSafe(path.join(__dirname,'fixtures')),/inside the source repository/);
 assert.throws(()=>Run.outputSafe(''),/required/);
});
