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
 for(const [i,scenario] of design.proposed_synthetic_scenarios.entries()){
   const feasible=scenario.intended_status==='candidate_feasible'||
     scenario.intended_status==='candidate_conditional_only';
   const previews=feasible?design.plan_for_accuracy_calibration.preview_panels_per_feasible_scenario:1;
   const panelResults=[];
   for(let w=0;w<previews;w++){
     const generated=generate(scenario,20261013+i+w*1000);
     const report=fit(generated.panel,{maximum_evaluations:800});
     const canFit=/^SYNTHETIC_ESTIMATOR/.test(report.status);
     if(feasible){
       if(!canFit)throw Error('Predeclared fictional numerically feasible scenario withheld: '+scenario.id+' '+report.status);
     }else if(report.status!==scenario.intended_status)
       throw Error('Predeclared expected source design refusal missing for '+scenario.id+': '+report.status);
     panelResults.push({
       preview_index:w,
       status:report.status,
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
   const errors=panelResults.flatMap(p=>p.comparison_from_oracle_after_fit_only?
     [p.comparison_from_oracle_after_fit_only.absolute_year_rho_error]:[]);
   outcomes.push({
     scenario_id:scenario.id,source_split:'synthetic',
     expected_status:scenario.intended_status,
     year_count:scenario.years,source_meetings:scenario.years*scenario.meetings_per_year,
     preview_panels:panelResults.length,
     numeric_fits_completed:errors.length,
     estimated_year_rho_absolute_errors:errors,
     maximum_absolute_rho_error:errors.length?Math.max(...errors):null,
     candidate_design_unreliable:errors.some(e=>e>0.5) ||
       panelResults.some(x=>x.estimation_warnings.some(w=>/bound|budget/.test(w))),
     panels:panelResults,
     nuisance_accepted_for_real_text:false
   });
 }
 const numeric=outcomes.reduce((n,x)=>n+x.numeric_fits_completed,0);
 const panels=outcomes.reduce((n,x)=>n+x.preview_panels,0);
 const refusals=outcomes.filter(x=>x.numeric_fits_completed===0).length;
 const reliabilityFlags=outcomes.filter(x=>x.candidate_design_unreliable).map(x=>x.scenario_id);
 const receipt={
   schema:'un.w1w2.nuisance-estimation.synthetic-preflight.v0',
   recorded_date:'2026-10-13',
   candidate_design_sha256:hash(plan),
   mode:'synthetic_numeric_proxy_only',
   estimator_family:'restricted_likelihood_crossed_meeting_affiliation_AR1_year',
   fit_provided_true_nuisance_parameters:false,
   scenarios:outcomes.length,preflight_panels:panels,estimation_attempts:numeric,
   correctly_withheld_scenarios:refusals,
   candidate_reliability_red_flags:reliabilityFlags,
   estimator_precision_accepted:false,
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
 try{
   const receipt=exportTo(dir);
   process.stdout.write(JSON.stringify(receipt)+'\n');
   const reports=JSON.parse(fs.readFileSync(path.join(path.resolve(dir),'synthetic-estimator-diagnostics.json'),'utf8'));
   process.stdout.write(JSON.stringify({schema:'un.w1w2.nuisance-estimation.synthetic-fit-summary.v0',
     scientific_gates_passed:0,
     rows:reports.simulated_scenarios.map(r=>({
       id:r.scenario_id,expected_status:r.expected_status,preview_panels:r.preview_panels,
       estimated_rho:r.panels.map(p=>p.comparison_from_oracle_after_fit_only?.estimated_year_rho??null),
       truth_rho:r.panels.map(p=>p.comparison_from_oracle_after_fit_only?.truth_year_rho??null),
       absolute_rho_errors:r.estimated_year_rho_absolute_errors,
       candidate_design_unreliable:r.candidate_design_unreliable,
       warnings:r.panels.map(p=>p.estimation_warnings)
     }))})+'\n');
 }
 catch(e){process.stderr.write('Nuisance preflight refused: '+String(e.message||e)+'\n');process.exitCode=1;}
}
module.exports={exportTo};
