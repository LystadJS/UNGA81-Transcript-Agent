'use strict';
/* Freeze identity and guardrails. No network or source imports. */
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const ROOT=path.join(__dirname,'protocol.v1.locked.json');
const GIT_BLOB_SHA1='95ee908bd710b7a6f075b685f0181a6fc979c33e';
const GATE_REGISTER=path.resolve(__dirname,'../../../..','docs/parallel-work/w1-w2-inference-readiness.v1.json');
const err=message=>{throw Error('synthetic-null-lock: '+message);};
const check=(x,m)=>{if(!x)err(m);};
const sha256=x=>crypto.createHash('sha256').update(x).digest('hex');
const gitBlobSha1=bytes=>crypto.createHash('sha1')
  .update(Buffer.from('blob '+bytes.length+'\0','utf8')).update(bytes).digest('hex');
function lock(){
  const bytes=fs.readFileSync(ROOT);
  check(gitBlobSha1(bytes)===GIT_BLOB_SHA1,'frozen protocol bytes altered; create v2 instead');
  const value=JSON.parse(bytes.toString('utf8'));
  check(value.schema==='un.w1-w2.synthetic-null.protocol.v1' &&
    value.version==='1.0.0' && value.frozen_at_date==='2026-10-13' &&
    value.status==='frozen_for_fictional_synthetic_simulation_only' &&
    value.eligible_for_real_inference===false,
    'invalid synthetic-only protocol version or scientific eligibility');
  check(value.source_inputs.fixture_kind==='synthetic' &&
    value.source_inputs.read_original_UN_documents===false &&
    value.source_inputs.read_private_historical_sources===false &&
    value.source_inputs.access_reserved_october_5_6_2026===false &&
    value.source_inputs.access_network===false &&
    value.reference_generator.kind==='oracle_parametric_nuisance_draw_v1' &&
    value.reference_generator.oracle_nuisance_is_empirically_verified===false,
    'real-source data or unverified scientific inference forbidden');
  check(value.nuisance_worlds.length===6 &&
    new Set(value.nuisance_worlds.map(x=>x.id)).size===6 &&
    value.nuisance_worlds.filter(x=>x.truth==='null').length===5 &&
    value.nuisance_worlds.filter(x=>x.truth==='positive').length===1,
    'five null and one planted positive control are required');
  check(value.fixed_method_grid.length===5 &&
    new Set(value.fixed_method_grid.map(x=>x.id)).size===5 &&
    value.fixed_method_grid.every(x=>x.seed===17),
    'fixed numerical search grid changed');
  check(value.statistic.strata.length===3 &&
    value.statistic.id==='cross_meeting_max_strata_consensus_fraction_v1' &&
    value.statistic.selection_multiplicity.startsWith('max statistic') &&
    value.statistic.association_cutoff===0.75 &&
    value.statistic.assignment_coverage_cutoff===0.45 &&
    value.statistic.min_contributing_families===2,
    'preselected cross-meeting test statistic or multiplicity changed');
  check(value.calibration.alpha_global===0.05 &&
    value.calibration.corrected_reference_draws_min===1999 &&
    value.calibration.outer_worlds_per_null_regime_min===1000 &&
    value.calibration.nominal_type1_upper_wilson_threshold===0.075 &&
    value.calibration.ci_smoke.outer_worlds===2 &&
    value.calibration.ci_smoke.reference_draws===7 &&
    value.calibration.smoke_must_remain_inferentially_withheld===true,
    'prospective budgets or nonrelease thresholds changed');
  check(value.grouped_refits.unit==='meeting' &&
    value.grouped_refits.sampling==='without_replacement' &&
    value.grouped_refits.retain_original_child_labels===true,
    'whole-source design changed');
  const status=JSON.parse(fs.readFileSync(GATE_REGISTER,'utf8'));
  check(status.schema==='un.w1-w2.inference-readiness.v1' &&
    status.gates.length===13 &&
    status.gates.every(x=>x.status==='NOT_RUN') &&
    status.empirical_evaluation_authorized===false &&
    status.inferential_eligible===false &&
    status.public_release_eligible===false &&
    status.reserved_october_2026_holdout_sealed===true,
    'original G01–G13 inferential release gate must remain fully withheld');
  return Object.freeze({protocol:value,protocol_sha256:sha256(bytes),
    protocol_blob_sha1:GIT_BLOB_SHA1,status:{
      inferential_eligible:false,empirical_evaluation_authorized:false,
      publication_eligible:false,source_split:'synthetic',gates_passed:0,gates_not_run:13}});
}
function deriveSeed(lockIdentity,scenario,world,draw,domain){
  check(/^[a-f0-9]{64}$/.test(lockIdentity)&&typeof scenario==='string' &&
    Number.isSafeInteger(world)&&world>=0&&Number.isSafeInteger(draw)&&draw>=-1 &&
    ['observed','reference','design','shock','positive'].includes(domain),
    'invalid deterministic seed derivation inputs');
  return Number.parseInt(sha256(JSON.stringify([lockIdentity,scenario,world,draw,domain])).slice(0,8),16)>>>0;
}
function rng(seed){
  let state=seed>>>0;
  return ()=>{state=(state+0x6D2B79F5)>>>0;let t=state;
    t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);
    return ((t^(t>>>14))>>>0)/4294967296;
  };
}
function normal(random){
  const u=Math.max(1e-12,random()),v=random();
  return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v);
}
module.exports={lock,sha256,gitBlobSha1,GIT_BLOB_SHA1,deriveSeed,rng,normal};
if(require.main===module){
  const v=lock();
  process.stdout.write(JSON.stringify({
    schema:'un.w1-w2.synthetic-null.lock-receipt.v1',
    protocol_sha256:v.protocol_sha256,protocol_blob_sha1:v.protocol_blob_sha1,
    status:'FROZEN_SYNTHETIC_ONLY',inferential_eligible:false,
    gates_passed:0,gates_not_run:13
  })+'\n');
}
