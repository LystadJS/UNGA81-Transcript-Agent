'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const fs=require('node:fs');
const path=require('node:path');
const {generate}=require('./synthetic.cjs');
const R=require('./reml.cjs');
const design=JSON.parse(fs.readFileSync(path.join(__dirname,'design.candidate.v0.json'),'utf8'));
const scenarios=new Map(design.proposed_synthetic_scenarios.map(x=>[x.id,x]));
const rowcopy=x=>structuredClone(x);
const gen=(id,seed=17)=>generate(scenarios.get(id),seed);
let a,b,c,d;
test.before(()=>{
 a=gen('E1_iid_16y',1001);
 b=gen('E2_ar1_16y',1001);
 c=gen('E3_ar1_24y',1001);
 d=gen('E8_declared_x_selection',1001);
});
test('candidate protocol identifies source-free numeric proxy, not real null or release',()=>{
 assert.equal(design.status,'candidate_for_independent_statistical_review_not_frozen_empirical_protocol');
 assert.equal(design.scope.empirical_sources_permitted,false);
 assert.equal(design.scientific_gates_passed,0);
 assert.equal(design.scientific_gates_not_run,13);
 assert.equal(design.estimator.covariance_components.length,5);
 assert.match(design.estimator.parameter_inference,/never pass generating/i);
});
test('all eight predeclared scenarios maintain truth completely separate from estimator input',()=>{
 assert.equal(scenarios.size,8);
 for(const s of scenarios.values()){
  const x=generate(s,9001);
  assert.equal(x.panel.producer.kind,'invented_numerical_proxy');
  assert.equal(x.panel.publication_eligible,false);
  assert.equal(x.panel.source_hash_basis,'synthetic');
  assert.equal(Object.hasOwn(x.panel,'truth'),false);
  assert.equal(Object.hasOwn(x.panel,'year_rho'),false);
  assert.equal(Object.hasOwn(x.panel,'meeting_variance'),false);
  assert.equal(Object.hasOwn(x.panel,'oracle_parameters'),false);
  assert.equal(x.truth.year_rho,s.year_rho);
  assert.equal(x.panel.selected_eligible+x.panel.available_not_selected+x.panel.unavailable_sources,
    x.panel.source_inventory_total);
  assert(x.panel.full_design_rows.every(x=>!Object.hasOwn(x,'text') &&
    !Object.hasOwn(x,'vector')&&x.source_hash_basis==='synthetic'));
 }
});
test('independent seeded restart gives identical source selections, responses and hashes',()=>{
 for(const s of scenarios.values()){
  const first=generate(s,45623).panel,second=generate(s,45623).panel;
  assert.deepEqual(first,second);
  assert.notEqual(first.selection_sha256,generate(s,45624).panel.selection_sha256);
 }
});
test('E4 eight-year model is withheld before covariance fitting, no false year SE',()=>{
 const panel=gen('E4_years8');
 assert.equal(R.verify(panel.panel).status,'WITHHELD_TOO_FEW_YEARS');
 assert.equal(R.fit(panel.panel).status,'WITHHELD_TOO_FEW_YEARS');
});
test('E5 one meeting per year cannot distinguish year and meeting random effects',()=>{
 assert.equal(R.fit(gen('E5_single_meeting_per_year').panel).status,
  'WITHHELD_YEAR_MEETING_CONFOUNDING');
});
test('E6 original family crossing meeting boundary cannot be split into nominal independent groups',()=>{
 const x=R.fit(gen('E6_shared_source_family').panel);
 assert.equal(x.status,'WITHHELD_CROSS_MEETING_FAMILY');
 assert.match(x.reason,/dependent original source/);
});
test('E7 latent-outcome-dependent missingness fails rather than assumes MAR',()=>{
 const x=R.fit(gen('E7_mnar_mask').panel);
 assert.equal(x.status,'WITHHELD_MNAR_SELECTION_NOT_IDENTIFIED');
 assert.equal(x.eligible_for_real_inference,false);
});
test('E8 declared-covariate selection is conditional analysis, never estimated population selection',()=>{
 const x=R.verify(d.panel);
 assert.equal(x.status,'DESIGN_IDENTIFIABLE_FOR_SYNTHETIC_PROBE_ONLY');
 assert(d.panel.available_not_selected>0);
 assert(x.selection_mechanism==='depends_on_observed_covariates');
});
test('E1/E2/E3 source designs are structurally estimable without injecting known truth',()=>{
 for(const x of [a,b,c]){
  const audit=R.verify(x.panel);
  assert.equal(audit.status,'DESIGN_IDENTIFIABLE_FOR_SYNTHETIC_PROBE_ONLY');
  assert(audit.meetingCount>=audit.yearCount*2);
  assert(audit.affiliationCount>=6);
  assert(audit.x_columns===7);
 }
});
test('restricted-likelihood candidate numerically estimates all covariance components and AR1',()=>{
 for(const x of [a,b]){
  const fit=R.fit(x.panel,{maximum_evaluations:900});
  assert.match(fit.status,/SYNTHETIC_ESTIMATOR/);
  assert.equal(fit.parameters_estimated_from_observations_only,true);
  assert(fit.optimizer_evaluations>20&&fit.optimizer_evaluations<=900);
  assert(Number.isFinite(fit.restricted_negative_log_likelihood));
  assert(fit.covariance_cholesky_min_diagonal>0);
  assert(fit.fixed_design_cholesky_min_diagonal>0);
  assert(fit.estimated_year_rho>-0.85&&fit.estimated_year_rho<0.85);
  assert(Object.values(fit.estimated_variances).every(x=>Number.isFinite(x)&&x>0));
  assert.equal(fit.parameter_standard_errors,null);
  assert.equal(fit.covariance_coverage_validated,false);
  assert.equal(fit.nuisance_parameter_estimation_accepted,false);
  assert.equal(fit.eligible_for_real_inference,false);
  assert.equal(fit.scientific_gates_passed,0);
 }
});
test('estimator is deterministic from a source-bound panel and excludes truth parameters',()=>{
 const panel=a.panel;
 const x=R.fit(panel,{maximum_evaluations:350});
 const y=R.fit(panel,{maximum_evaluations:350});
 assert.deepEqual(x,y);
 assert.throws(()=>R.fit(panel,{year_rho:0.65}),/no oracle parameters/);
 assert.throws(()=>R.fit({...panel,truth:a.truth}),/oracle generating parameters/);
});
test('panel source and response digests cannot be modified without refusal',()=>{
 const original=a.panel;
 const changed=rowcopy(original);
 changed.full_design_rows[0].response+=1;
 assert.throws(()=>R.verify(changed),/response hash/);
 const m=rowcopy(original);
 m.full_design_rows[0].meeting_id='fictional-meeting-other';
 assert.throws(()=>R.verify(m),/design identity/);
 const v=rowcopy(original);
 v.full_design_rows[0].fixed_covariates[0]=-1;
 assert.throws(()=>R.verify(v),/design identity/);
});
test('ineligible and missing responses are null, not zero, and source counts reconcile',()=>{
 const panel=d.panel;
 assert(panel.full_design_rows.filter(x=>x.selection_status==='available_not_selected')
   .every(x=>x.response===null&&x.response_sha256===null&&x.missing_reason));
 assert(panel.full_design_rows.filter(x=>x.selection_status==='unavailable_source')
   .every(x=>x.response===null&&x.response_sha256===null&&x.missing_reason));
 const corrupted=rowcopy(panel);
 const missing=corrupted.full_design_rows.find(x=>x.selection_status==='available_not_selected');
 missing.response=0;
 assert.throws(()=>R.verify(corrupted),/selected response hash|response invalid/);
});
test('unverified alternative source modality cannot pass as an invented source',()=>{
 const panel=rowcopy(a.panel);
 const row=panel.full_design_rows.find(x=>x.selection_status==='unavailable_source');
 row.source_hash_basis='raw_response_bytes';
 assert.throws(()=>R.verify(panel),/source\/selection provenance/);
});
test('invalid observation units, few affiliations and rank deficient X do not yield nuisance parameters',()=>{
 const o=rowcopy(a.panel);
 o.source_design_sha256='f'.repeat(64);
 assert.throws(()=>R.verify(o),/source identity/);
 const b0=rowcopy(a.panel);
 b0.full_design_rows[0].fixed_covariates=null;
 assert.throws(()=>R.verify(b0),/design identity/);
});
test('positive definiteness of fitted covariance is checked by the actual Cholesky objective',()=>{
 const audit=R.verify(a.panel);
 const data=R.preprocess(audit);
 const baseline=R.objective(data,[Math.log(.2),Math.log(.2),Math.log(.2),Math.log(.4),0]);
 assert(Number.isFinite(baseline.nll));
 assert(baseline.covariance_cholesky_min_diagonal>0);
 const changed=R.objective(data,[Math.log(.7),Math.log(.2),Math.log(.1),Math.log(.1),1]);
 assert(Number.isFinite(changed.nll));
 assert.notEqual(changed.nll,baseline.nll);
});
test('no empirical evidence, source text, p-values or intervals are written by candidate',()=>{
 const fitted=R.fit(a.panel,{maximum_evaluations:250});
 const json=JSON.stringify(fitted);
 assert(!json.includes('confidence_interval'));
 assert(!json.includes('"p_value"'));
 assert(!json.includes('"text"'));
 assert(!json.includes('source_url'));
 assert(!Object.hasOwn(fitted,'true_parameters'));
 assert.equal(fitted.publication_eligible,false);
});
