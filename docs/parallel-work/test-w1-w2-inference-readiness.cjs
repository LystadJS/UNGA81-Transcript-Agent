'use strict';
/*
 * Synthetic metadata-only refusal tests. No UN original text, P2 private data,
 * transcript network access, statistical fitting, or reserved evaluation.
 */
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const V=require('./inference-readiness-v1.cjs');
const source=JSON.parse(fs.readFileSync(path.join(__dirname,
  'w1-w2-inference-readiness.v1.json'),'utf8'));
const copy=x=>structuredClone(x);

test('the entire prospective register remains fail-closed with thirteen NOT_RUN inferential gates',()=>{
 const result=V.validate(source,{requireDocumentation:true});
 assert.equal(result.status,'WITHHELD');
 assert.equal(result.total_gates,13);
 assert.equal(result.passed_gates,0);
 assert.equal(result.not_run_gates,13);
 assert.equal(result.inferential_eligible,false);
 assert.equal(result.empirical_evaluation_authorized,false);
 assert.equal(result.public_release_eligible,false);
 assert.equal(source.reserved_october_2026_holdout_sealed,true);
 assert.equal(source.statistics_policy.null_generator_version_sha256,null);
 assert.equal(source.statistics_policy.selected_global_statistic_id,null);
});

test('source authentication cannot be promoted to PASS without independently reviewed evidence',()=>{
 const d=copy(source);
 d.gates[0].status='PASS';
 assert.throws(()=>V.validate(d),/self-certify|fabricate evidence/);
 d.gates[0].evidence_sha256='f'.repeat(64);
 d.gates[0].evidence_url='https://github.com/fake';
 d.gates[0].reviewer='self';d.gates[0].reviewed_at='2026-10-13';
 assert.throws(()=>V.validate(d),/self-certify|fabricate evidence/);
});

test('source dependence cannot be bypassed by flipping inferential or publication permission',()=>{
 for(const key of ['inferential_eligible','empirical_evaluation_authorized',
   'public_release_eligible','proposal_frozen']){
   const d=copy(source);d[key]=true;
   assert.throws(()=>V.validate(d),/withheld/);
 }
});

test('holdout and original date boundaries remain sealed',()=>{
 const x=copy(source);
 x.reserved_october_2026_holdout_sealed=false;
 assert.throws(()=>V.validate(x),/37 reserved transcripts/);
 const y=copy(source);y.gates[10].status='PASS';
 assert.throws(()=>V.validate(y),/self-certify/);
});

test('all source, dependence, nuisance and null gates remain mandatory',()=>{
 for(const g of source.gates){
   assert.equal(g.required_for_publication,true);
   assert.equal(g.required_for_empirical_inference,g.id!=='G13');
   assert(g.acceptance_criterion.length>=40);
   assert.equal(g.status,'NOT_RUN');
 }
 const d=copy(source);d.gates.pop();
 assert.throws(()=>V.validate(d),/thirteen/);
 const e=copy(source);e.gates.splice(3,1);
 assert.throws(()=>V.validate(e),/thirteen/);
});

test('unknown keys, duplicate gates and cycles cannot silently downgrade the protocol',()=>{
 const a=copy(source);a.private_source_text='forbidden';
 assert.throws(()=>V.validate(a),/root: unexpected/);
 const b=copy(source);b.gates[3].id='G03';
 assert.throws(()=>V.validate(b),/identity/);
 const c=copy(source);c.gates[2].dependencies.push('G13');
 assert.throws(()=>V.validate(c),/prerequisites/);
 const d=copy(source);d.gates[0].extra='unreviewed';
 assert.throws(()=>V.validate(d),/gate 0: unexpected/);
});

test('random row reorder, group deletions and few-year asymptotics can never become a significance claim by metadata',()=>{
 for(const field of ['random_row_permutation_is_cluster_significance_test',
  'source_group_loo_is_confidence_interval',
  'source_group_subsampling_is_bootstrap',
  'historical_four_year_per_era_asymptotic_inference_allowed',
  'group_exchangeability_verified']){
  const d=copy(source);d.statistics_policy[field]=true;
  assert.throws(()=>V.validate(d),/invalid statistical shortcut/);
 }
});

test('the proposed numerical calibration thresholds cannot be relaxed without a new policy',()=>{
 for(const [name,value] of [
   ['global_familywise_alpha_proposed',0.15],
   ['inner_reference_draws_min_proposed',199],
   ['outer_independent_null_worlds_min_proposed',5],
   ['max_one_sided_wilson_upper_null_false_discovery_rate_proposed',1]
 ]){const x=copy(source);x.statistics_policy[name]=value;
   assert.throws(()=>V.validate(x),/numerical criteria changed/);}
});

test('a post-hoc statistic or self-selected model does not become preregistered by assigning an identifier',()=>{
 const a=copy(source);
 a.statistics_policy.selected_global_statistic_id='best-looking-cluster';
 assert.throws(()=>V.validate(a),/must remain null/);
 const b=copy(source);
 b.statistics_policy.null_generator_version_sha256='a'.repeat(64);
 assert.throws(()=>V.validate(b),/must remain null/);
 const c=copy(source);
 c.statistics_policy.frozen_future_evaluation_manifest_sha256='a'.repeat(64);
 assert.throws(()=>V.validate(c),/must remain null/);
});

test('source and authorial decision provenance is versioned, not free-form',()=>{
 const a=copy(source);a.schema='un.parallel-analysis.v1';
 assert.throws(()=>V.validate(a),/protocol\/version/);
 const b=copy(source);b.baseline_main_commit_sha='invalid';
 assert.throws(()=>V.validate(b),/provenance/);
 const c=copy(source);c.gates[0].dependencies=['G02'];
 assert.throws(()=>V.validate(c),/prerequisites/);
});

test('the requirements document explicitly distinguishes original-source, dependence, calibration and nonrelease',()=>{
 const doc=fs.readFileSync(path.join(__dirname,
  'W1_W2_INFERENCE_READINESS_REQUIREMENTS_2026-10-13.md'),'utf8');
 for(const phrase of ['original TAR member', 'no additional cross-source latent-discourse association',
   'without replacement','year shocks','conditional coassignment',
   'no unapproved holdout','not a cluster-significance test']){
  const match=doc.toLowerCase().includes(phrase.toLowerCase());
  assert(match,'Missing documented inferential limit: '+phrase);
 }
});
