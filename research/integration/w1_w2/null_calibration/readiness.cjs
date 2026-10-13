'use strict';
/*
 * G01–G13 remain NOT_RUN even if a fictional oracle diagnostic succeeds.
 * Never update docs/parallel-work/w1-w2-inference-readiness.v1.json.
 */
const fs=require('node:fs');
const path=require('node:path');
const {lock}=require('./lock.cjs');
const {validate}=require('../../../../docs/parallel-work/inference-readiness-v1.cjs');
const REGISTER=path.resolve(__dirname,'../../../../docs/parallel-work/w1-w2-inference-readiness.v1.json');
const descriptions={
 G01:'Actual original-byte UN PV and precise historical TAR-member hashes were not opened or verified.',
 G02:'No real observation selection/missingness census, authenticated source identity or country-year inventory was assessed.',
 G03:'Only fictional source-family/meeting/affiliation/year closures and duplicates were diagnosed; the real source graph is unverified.',
 G04:'Source-group exchangeability and effective independent opportunities are not established. Cross-meeting family and four-year/era stress regimes illustrate withholding.',
 G05:'Only the fictional global max statistic is frozen. A source-backed inferential estimand and confirmatory split are not frozen.',
 G06:'Five synthetic W1 methods and three inspected pair strata are fixed; the full real method/threshold/representation search family is not frozen.',
 G07:'Reference simulations draw nuisance parameters from the known invented oracle. None were estimated, validated or calibrated against actual UN source nuisance.',
 G08:'Real W1 numerical TF-IDF/PCA/LSA/clustering, grouped child fitting and W2 recomputation were exercised on invented tokens; no empirical null generator or nuisance parameter estimation was tested.',
 G09:'The reference and independent-null-world budgets were not completed: the fixed criteria are 1,999 inner draws and 1,000 outer null worlds per regime; no valid error-rate claim.',
 G10:'Synthetic positive/null, duplicates, AR(1), group closure, missingness and failure controls run; no independent empirical known-structure or misspecification acceptance.',
 G11:'No authorized independent empirical source groups, prospective held-out texts, leak-proof training split or sealed 37-meeting evaluation were opened.',
 G12:'Only engineering SHA/seed/attempt receipts are reproduced. Original source, transformations and empirical null-calibration provenance remain unverified.',
 G13:'Owner/coordinator has not authorized political interpretation, public release, O1–O5 changes or website mirror.'
};
function assess(a){
 const frozen=lock();
 const doc=JSON.parse(fs.readFileSync(REGISTER,'utf8'));
 validate(doc,{requireDocumentation:true});
 if(!a||a.schema!=='un.w1-w2.synthetic-null.calibration-audit.v1' ||
   a.protocol_sha256!==frozen.protocol_sha256 ||
   a.inferential_eligible!==false ||
   a.empirical_evaluation_authorized!==false||
   a.publication_eligible!==false||
   a.reserved_transcripts_opened!==0||
   a.g01_g13_all_not_run!==true)
   throw Error('W1-W2 readiness assessment refuses nonfrozen/nonfictional or unapproved analytic outputs');
 const scenarios=a.scenarios||[];
 const details=a.detail||[];
 const ledger=doc.gates.map(g=>({
   id:g.id,title:g.title,scientific_status:'NOT_RUN',
   synthetic_engineering_evidence_gathered:
     ['G03','G04','G05','G06','G07','G08','G09','G10','G12'].includes(g.id)&&
     scenarios.length>0,
   requires_additional_review:true,blocking_reason:descriptions[g.id]
 }));
 const withholds=scenarios.filter(s=>s.status==='WITHHELD_NONDELIVERY');
 const groupRefusal=details.some(s=>s.worlds.some(w=>
   w.typed_dependence_flags?.includes('cross_meeting_original_source_family_closure')));
 const serial=details.some(s=>s.worlds.some(w=>
   w.typed_dependence_flags?.includes('serial_year_dependence_present')));
 const report={
   schema:'un.w1-w2.synthetic-null.gate-assessment.v1',
   status:'INFERENCE_WITHHELD',
   protocol_sha256:frozen.protocol_sha256,
   current_source_scope:'fictional synthetic only',
   first_protocol_commit:'35dd737a7fd1d7896464df45fa77e2f2a28db4ca',
   total_scientific_gates:13,scientific_gates_passed:0,
   scientific_gates_not_run:13,actual_original_byte_authentication:false,
   real_exchangeability_established:false,
   real_nuisance_parameters_estimated:false,
   prospective_empirical_test_statistic_frozen:false,
   selected_synthetic_test_statistic_frozen:true,
   simulated_reference_draws:a.attempted_reference_draws,
   simulated_outer_worlds:a.worlds_attempted,
   full_known_truth_calibration_executed:false,
   source_group_crossing_refusal_seen:groupRefusal,
   serial_year_stress_covered:serial,
   nuisance_withheld_regimes:withholds.map(s=>s.scenario_id),
   empirical_evaluation_authorized:false,
   inferential_eligible:false,public_release_eligible:false,
   reserved_october_2026_holdout_sealed:true,
   blockers:[
     'Original UN/source-family byte proof and source/selection graph G01–G04 unverified.',
     'Known synthetic nuisance oracle is not a fitted/validated real source null G07.',
     'Preregistered 1,000 × 1,999 known-truth simulation burden and FWER validation G09 uncompleted.',
     'No independently source-separated prospective evaluation or human scientific/publication approval G11–G13.'
   ],
   gates:ledger
 };
 if(report.gates.some(g=>g.scientific_status!=='NOT_RUN'))
   throw Error('No scientific gate may be self-promoted by a simulation');
 return report;
}
module.exports={assess};
