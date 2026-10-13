#!/usr/bin/env node
'use strict';
/* Synthetic-only estimator smoke. No original source, no null significance. */
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {generate}=require('./synthetic.cjs');
const {fit}=require('./reml.cjs');
const ROOT=path.resolve(__dirname,'../../../..');
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const plan=fs.readFileSync(path.join(__dirname,'design.candidate.v0.json'));
const design=JSON.parse(plan);
function exportTo(dir){
 const target=path.resolve(dir||'');
 if(!dir||target===ROOT||target.startsWith(ROOT+path.sep)||fs.existsSync(target))
   throw Error('New outside-repository output directory required; never overwrite a file.');
 const outcomes=[];
 for(const [i,s] of design.proposed_synthetic_scenarios.entries()){
   const generated=generate(s,20261013+i);
   const report=fit(generated.panel,{maximum_evaluations:800});
   const canFit=/^SYNTHETIC_ESTIMATOR/.test(report.status);
   if(s.intended_status==='candidate_feasible'||
     s.intended_status==='candidate_conditional_only'){
     if(!canFit)throw Error('Frozen fictional feasible estimator scenario withheld: '+s.id+' '+report.status);
   }else if(report.status!==s.intended_status)
     throw Error('Frozen expected refusal missing for '+s.id+': '+report.status);
   outcomes.push({
     scenario_id:s.id,source_split:'synthetic',
     status:report.status,expected_status:s.intended_status,
     year_count:s.years,source_meetings:s.years*s.meetings_per_year,
     original_inventory:generated.panel.source_inventory_total,
     selected:generated.panel.selected_eligible,
     available_not_selected:generated.panel.available_not_selected,
     unavailable:generated.panel.unavailable_sources,
     comparison_from_oracle_after_fit_only:canFit?{
       truth_year_rho:generated.truth.year_rho,
       estimated_year_rho:report.estimated_year_rho,
       absolute_year_rho_error:Math.abs(report.estimated_year_rho-generated.truth.year_rho),
       estimated_variances:report.estimated_variances,
       known_variances:generated.truth.variances
     }:null,
     optimizer_evaluations:report.optimizer_evaluations??0,
     estimation_warnings:report.warnings??[report.reason],
     nuisance_accepted_for_real_text:false
   });
 }
 const complete=outcomes.filter(x=>x.comparison_from_oracle_after_fit_only).length;
 const receipt={
   schema:'un.w1w2.nuisance-estimation.synthetic-preflight.v0',
   recorded_date:'2026-10-13',
   candidate_design_sha256:hash(plan),
   mode:'synthetic_numeric_proxy_only',
   estimator_family:'restricted_likelihood_crossed_meeting_affiliation_AR1_year',
   fit_provided_true_nuisance_parameters:false,
   scenarios:outcomes.length,estimation_attempts:complete,
   correctly_withheld_scenarios:outcomes.length-complete,
   selection_mechanism_conditional_only:true,
   estimated_AR1_year_parameter:true,
   calibrated_error_rate:false,
   estimator_covariance_coverage_validated:false,
   actual_source_nuisance_parameters_identified:false,
   full_W1_W2_lexical_null_with_estimated_parameters_implemented:false,
   original_UN_source_bytes_opened:0,
   reserved_37_transcripts_opened:0,
   g01_g13_scientific_gates_passed:0,
   scientific_evaluation_authorized:false,
   public_release_eligible:false,
   limitations:[
     'This prototype fits one invented numeric nuisance proxy, not an actual W1 word-count or semantic representation.',
     'Covariance components and year rho are estimated without oracle inputs to the fitter; no synthetic coverage, bias or finite-sample precision acceptance.',
     'MNAR availability, one-meeting-per-year covariance confounding, short-year panels and cross-meeting families remain withheld.',
     'A source-authenticated lexical nuisance/selection estimator, independently evaluated covariance identifiability and nested full W1/W2 null calibration are still required.'
   ]
 };
 fs.mkdirSync(target,{mode:0o700,recursive:false});
 const reports={
   'receipt.json':receipt,
   'synthetic-estimator-diagnostics.json':{
     schema:'un.w1w2.nuisance-estimation.synthetic-diagnostics.v0',
     candidate_design_sha256:receipt.candidate_design_sha256,
     source_split:'synthetic',source_text_exported:false,
     simulated_scenarios:outcomes,scientific_gates_passed:0
   }
 };
 const manifest={};
 for(const [filename,x] of Object.entries(reports)){
   const data=Buffer.from(JSON.stringify(x,null,2)+'\n');
   fs.writeFileSync(path.join(target,filename),data,{flag:'wx',mode:0o600});
   manifest[filename]=hash(data);
 }
 fs.writeFileSync(path.join(target,'SHA256.json'),JSON.stringify(manifest,null,2)+'\n',{flag:'wx',mode:0o600});
 return receipt;
}
if(require.main===module){
 const dir=process.argv[2];
 try{process.stdout.write(JSON.stringify(exportTo(dir))+'\n');}
 catch(e){process.stderr.write('Nuisance preflight refused: '+String(e.message||e)+'\n');process.exitCode=1;}
}
module.exports={exportTo};
