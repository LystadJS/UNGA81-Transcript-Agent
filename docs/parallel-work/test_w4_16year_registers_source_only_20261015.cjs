'use strict';
// Public aggregate-only structural regression. No private PV/text/actor-year rows.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const source=JSON.parse(fs.readFileSync(path.join(__dirname,'W4_16YEAR_REGISTER_VALIDATION_AGGREGATE_2026-10-15.json'),'utf8'));
function check(z){
 const v=z.scope,p=z.source_provenance,g=z.genre,t=z.translation,r=z.roster,s=z.selection_and_missingness,h=z.release;
 assert.equal(v.recorded_affiliations*v.expected_cells/v.expected_cells,99);
 assert.equal(v.recorded_affiliations*16,v.expected_cells);
 assert.equal(v.expected_cells,v.unique_cells);
 assert.equal(v.source_verified+v.unverified_or_not_at_risk,v.expected_cells);
 assert.equal(v.source_verified,1574);
 assert.equal(v.pre_admission_structural_nonopportunities,3);
 assert.equal(p.indexed_original_PV_meeting_documents,223);
 assert.equal(p.locally_rehashed_against_prior_source_manifests,223);
 assert.equal(p.verified_actor_year_original_source_meeting_date_links,1574);
 assert.equal(p.inherited_2016_2023_source_identity_hash_rows_unchanged,792);
 assert.equal(p.preera_audit_split_verified,true);
 assert.equal(g.UN_speaker_index_rows,3379);
 assert.equal(g.UN_index_rows_tagged_general_debate,3379);
 assert.equal(g.UN_index_rows_also_tagged_special_statements,2096);
 assert.equal(g.preera_fixed99_country_years_with_multiple_indexed_PV_candidates,15);
 assert.equal(g.year2020.extra_same_state_PV_rows,187);
 assert.equal(g.year2021.extra_same_state_PV_rows,85);
 assert.equal(g.independent_speech_level_genre_adjudications_current_audit,0);
 assert.equal(t.original_PV_english_version_documents,223);
 assert.equal(t.spoken_language_per_speech_verified,0);
 assert.equal(t.translation_method_per_speech_verified,0);
 assert.equal(t.complete_pdf_language_marker_scan,'NOT_RUN_TIMED_OUT');
 assert.equal(r.fixed_99_member_state_at_risk_by_year_complete,false);
 assert.equal(s.probabilistic_actor_year_inclusion_pi_known,false);
 assert.equal(s.verification_propensity_q_estimated,false);
 assert.equal(s.weights_capped_fraction,null);
 assert.equal(s.source_weight_positivity_gate,'NOT_RUN');
 assert.equal(s.MAR_assumption,'NOT_TESTABLE');
 assert.equal(s.structural_uniform_99x16_opportunity_positivity,'FAIL_3_NOT_AT_RISK');
 assert.equal(s.unverified_reasons.pre_membership_structural+s.unverified_reasons.unverified_original_source+s.unverified_reasons.full_original_speech_nonmatch+s.unverified_reasons.inherited_prior_source_unverified,10);
 assert.equal(h.source_integrity_and_denominator,'PASS');
 assert.equal(h.calibrated_empirical_inference,'FAIL');
 assert.equal(h.public_empirical_release,'FAIL');
 assert.equal(h.lexical_model_fits,'NOT_RUN');
 assert.equal(h.synthetic_full_36_cell_calibration,'NOT_RUN');
 assert.equal(h.reserved_2026_transcripts_opened,0);
 assert.equal(h.frozen_release_gates_modified,false);
 assert.equal(z.private_metadata_records_published,false);
 assert.equal(z.original_transcripts_published,false);
}
check(source);let controls=1;
function refusal(change){const altered=JSON.parse(JSON.stringify(source));change(altered);assert.throws(()=>check(altered),{name:'AssertionError'});controls++;}
refusal(z=>z.scope.unique_cells--);
refusal(z=>z.translation.translation_method_per_speech_verified=1574);
refusal(z=>z.selection_and_missingness.verification_propensity_q_estimated=true);
refusal(z=>z.release.public_empirical_release='PASS');
refusal(z=>z.release.reserved_2026_transcripts_opened=1);
console.log(JSON.stringify({suite:'W4-16year-registers-aggregate',controls,failed:0,
 private_inputs_read:0,original_PVs_opened:0,source_only:true,
 inference_eligible:false,publication_eligible:false}));
