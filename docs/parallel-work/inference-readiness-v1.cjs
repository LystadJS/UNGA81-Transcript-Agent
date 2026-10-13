'use strict';
/*
 * Fail-closed registry validator for PROSPECTIVE, NOT-RUN inference requirements.
 * This is policy metadata only. It never fits models or accesses source text.
 * A future scientific acceptance needs a new reviewed registry/version and
 * independent evidence verification; local metadata cannot certify sources.
 */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const STATUS='NOT_RUN';
const SCHEMA='un.w1-w2.inference-readiness.v1';
const IDS=Object.freeze(Array.from({length:13},(_,i)=>'G'+String(i+1).padStart(2,'0')));
const SHA=/^[a-f0-9]{40}$/;
const expectedRoot=new Set([
 'schema','requirements_version','record_date','baseline_repository',
 'baseline_main_commit_sha','requirements_document','document_status',
 'proposal_frozen','empirical_evaluation_authorized','inferential_eligible',
 'public_release_eligible','reserved_october_2026_holdout_sealed',
 'current_evaluation_role','statistics_policy','gates'
]);
const policyFields=new Set([
 'global_familywise_alpha_proposed','inner_reference_draws_min_proposed',
 'outer_independent_null_worlds_min_proposed','upper_confidence_level',
 'max_one_sided_wilson_upper_null_false_discovery_rate_proposed',
 'threshold_status','random_row_permutation_is_cluster_significance_test',
 'source_group_loo_is_confidence_interval','source_group_subsampling_is_bootstrap',
 'historical_four_year_per_era_asymptotic_inference_allowed',
 'minimum_effective_independent_groups','group_exchangeability_verified',
 'selected_global_statistic_id','null_generator_version_sha256',
 'frozen_future_evaluation_manifest_sha256'
]);
const gateFields=new Set([
'id','title','category','dependencies','required_for_empirical_inference',
'required_for_publication','status','evidence_sha256','evidence_url',
'reviewer','reviewed_at','acceptance_criterion','unresolved_reason'
]);
const fail=message=>{throw Error('inferential-readiness: '+message);};
const check=(x,message)=>{if(!x)fail(message);};
const only=(obj,allowed,tag)=>{
 check(obj&&typeof obj==='object'&&!Array.isArray(obj),tag+': plain object required');
 check(Object.keys(obj).length===allowed.size,tag+': unexpected/missing keys');
 for(const k of Object.keys(obj))check(allowed.has(k),tag+': forbidden field '+k);
 for(const k of allowed)check(Object.hasOwn(obj,k),tag+': missing field '+k);
};
function validate(doc,{requireDocumentation=false}={}){
 only(doc,expectedRoot,'root');
 check(doc.schema===SCHEMA&&doc.requirements_version==='1.0.0',
   'unrecognized future inferential protocol/version');
 check(doc.record_date==='2026-10-13'&&doc.baseline_repository==='LystadJS/UNGA81-Transcript-Agent'&&
   SHA.test(doc.baseline_main_commit_sha),'requirements provenance or date mismatch');
 check(doc.document_status==='prospective_requirements_not_frozen_test_protocol' &&
   doc.current_evaluation_role==='engineering_only',
   'requirements must not claim scientific acceptance');
 for(const field of ['proposal_frozen','empirical_evaluation_authorized','inferential_eligible','public_release_eligible'])
   check(doc[field]===false,'publication/inference/empirical gate remains withheld: '+field);
 check(doc.reserved_october_2026_holdout_sealed===true,
   '37 reserved transcripts must stay unopened');
 check(doc.requirements_document===
   'docs/parallel-work/W1_W2_INFERENCE_READINESS_REQUIREMENTS_2026-10-13.md',
   'requirements document reference changed');
 only(doc.statistics_policy,policyFields,'statistics_policy');
 const p=doc.statistics_policy;
 check(p.global_familywise_alpha_proposed===0.05 &&
   p.inner_reference_draws_min_proposed===1999 &&
   p.outer_independent_null_worlds_min_proposed===1000 &&
   p.upper_confidence_level===0.95 &&
   p.max_one_sided_wilson_upper_null_false_discovery_rate_proposed===0.075 &&
   p.threshold_status==='prospective_requirements_not_statistically_calibrated',
   'prospective numerical criteria changed without a new policy version');
 for(const k of [
   'random_row_permutation_is_cluster_significance_test',
   'source_group_loo_is_confidence_interval',
   'source_group_subsampling_is_bootstrap',
   'historical_four_year_per_era_asymptotic_inference_allowed',
   'group_exchangeability_verified'
 ])check(p[k]===false,'invalid statistical shortcut: '+k);
 for(const k of ['minimum_effective_independent_groups','selected_global_statistic_id',
   'null_generator_version_sha256','frozen_future_evaluation_manifest_sha256'])
   check(p[k]===null,'not-yet-frozen inferential specification must remain null: '+k);
 check(Array.isArray(doc.gates)&&doc.gates.length===IDS.length,'exactly thirteen evidence gates are required');
 const seen=new Set();
 for(const [i,g] of doc.gates.entries()){
   only(g,gateFields,'gate '+i);
   check(g.id===IDS[i]&&!seen.has(g.id),'missing, reordered or repeated gate identity');
   seen.add(g.id);
   check(typeof g.title==='string'&&g.title.length>=8 &&
     typeof g.acceptance_criterion==='string'&&g.acceptance_criterion.length>=40 &&
     typeof g.unresolved_reason==='string'&&g.unresolved_reason.length>=12,
     'gate missing substantive requirements or withholding reason');
   check(['source_dependence','null_calibration','evaluation_release'].includes(g.category),
     'unrecognized gate category');
   check(g.required_for_publication===true &&
     g.required_for_empirical_inference===(g.id!=='G13'),
     'wrong publication or inferential gate membership');
   check(g.status===STATUS &&
     g.evidence_sha256===null && g.evidence_url===null &&
     g.reviewer===null && g.reviewed_at===null,
     'no gate may self-certify PASS or fabricate evidence in this prospective snapshot');
   check(Array.isArray(g.dependencies)&&new Set(g.dependencies).size===g.dependencies.length &&
     g.dependencies.every(dependency=>seen.has(dependency)),
     'gate prerequisites must precede the gate and cannot form cycles');
 }
 if(requireDocumentation){
   const file=path.resolve(__dirname,'W1_W2_INFERENCE_READINESS_REQUIREMENTS_2026-10-13.md');
   const text=fs.readFileSync(file,'utf8');
   for(const phrase of ['INFERENCE WITHHELD','G01','G13','Randomly permuting rows',
      'family-wise error','37 reserved','no additional cross-source latent-discourse association'])
     check(text.toLowerCase().includes(phrase.toLowerCase()),
       'required methodological explanation absent: '+phrase);
 }
 return Object.freeze({schema:SCHEMA,status:'WITHHELD',
   inferential_eligible:false,empirical_evaluation_authorized:false,
   public_release_eligible:false,total_gates:doc.gates.length,
   passed_gates:0,not_run_gates:doc.gates.length,
   note:'Structural/prospective-policy receipt only; no original sources, statistical models or null generators assessed.'});
}
function main(){
 const input=JSON.parse(fs.readFileSync(path.resolve(__dirname,'w1-w2-inference-readiness.v1.json'),'utf8'));
 const result=validate(input,{requireDocumentation:true});
 process.stdout.write(JSON.stringify(result)+'\n');
}
if(require.main===module)main();
module.exports={SCHEMA,IDS,validate};
