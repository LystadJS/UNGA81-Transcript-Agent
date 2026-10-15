'use strict';
// Purely aggregated P2 original-source acceptance and negative release controls.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const here=__dirname;
const x=JSON.parse(fs.readFileSync(path.join(here,'W4_P2_2008_2023_INDEPENDENT_SOURCE_AUDIT_AGGREGATE_2026-10-13.json'),'utf8'));
const plan=JSON.parse(fs.readFileSync(path.join(here,'W4_EXPANDED_YEAR_INFERENCE_REGISTER_2026-10-13.json'),'utf8'));
const eq=(a,b)=>assert.equal(a,b);
eq(x.schema,'un.w4.p2.pre2016.independent-source-quality-acceptance.aggregate.v1');
eq(x.frozen_audit_split_sha256,'9f82613e7057a66f9ca7ccb550fade49797d4457fd67ada2443ef6a00edb9ef5');
eq(x.frozen_preregistration_commit,plan.preregistration_commit_sha);
eq(x.source_authentication.prior_development_original_PVs,90);
eq(x.source_authentication.fresh_independent_original_PV_audit_attempted,28);
eq(x.source_authentication.fresh_original_PV_sha256_header_symbol_date_extraction_passed,28);
eq(x.source_authentication.full_pre2016_original_PV_meeting_universe_complete,118);
eq(x.source_authentication.UN_publisher_signed_sha256_digest_available,false);
eq(x.speech_quality_audit.frozen_audit_associated_candidate_actor_years,178);
eq(x.speech_quality_audit.original_frozen_PV_mapping_full_speech_passes,176);
eq(x.speech_quality_audit.original_frozen_PV_mapping_full_speech_failures,2);
eq(x.speech_quality_audit.corrected_wrong_meeting_source_attributions,2);
eq(x.speech_quality_audit.corrected_missing_index_actor_source_attributions,6);
eq(x.speech_quality_audit.new_unique_qualifying_full_year_PV_matches_total,184);
eq(x.speech_quality_audit.multiple_full_year_qualifying_PV_source_matches,0);
eq(x.speech_quality_audit.independent_audit_sources_used_for_model_tuning,false);
const d=x.denominators;
eq(d.fixed_country_affiliation_count,plan.population.country_affiliations_frozen);
eq(d.fixed_calendar_year_count,plan.population.year_count);
eq(d.expected_country_year_opportunities,plan.population.candidate_cells);
eq(d.prior_pre2016_source_verified_inherited_from_P1+d.new_audit_source_corroborations+d.new_direct_original_PV_source_reconciliations,d.new_pre2016_source_verified_total);
eq(d.new_pre2016_source_verified_total+d.previous_2016_2023_source_verified_inherited_not_rerun,d.all_16_year_source_verified);
eq(d.all_16_year_source_verified+d.all_16_year_unverified_or_not_at_risk,d.expected_country_year_opportunities);
eq(d.yearly.length,16);
eq(d.yearly.reduce((sum,r)=>sum+r.verified,0),d.all_16_year_source_verified);
assert(d.yearly.every(r=>r.verified+r.unverified===99),'One year denominator corruption');
assert(d.yearly.every(r=>r.coverage_fraction>=0.90),'Annual coverage gate failed');
assert(d.source_verified_fraction_fixed_population>=0.95);
assert(d.fixed_affiliations_at_least_6_verified_each_8year_era>=90);
const missing=x.remaining_not_source_authenticated;
eq(missing.original_Harvard_archive_member_absent+missing.Harvard_speech_no_qualifying_full_PV_original_match+missing.prior_2016_2023_source_unverified_inherited,missing.total);
eq(missing.of_which_UN_member_status_pre_admission_not_at_risk,3);
eq(missing.total,10);
const gates=x.project_gates;
eq(gates.original_source_audit,'PASS');
eq(gates.historical_2008_2023_source_coverage,'PASS');
eq(gates.new_16year_64d_lexical_W4_fit,'NOT_RUN');
eq(gates.source_selection_MAR_positivity_validation,'NOT_RUN');
eq(gates.predeclared_36cell_21600world_synthetic_64D_calibration,'NOT_RUN');
eq(gates.calibrated_real_world_inference,'FAIL');
eq(gates.public_empirical_release,'FAIL');
eq(gates.frozen_D1_O1_to_O5_modified,false);
eq(gates.reserved_october_2026_meeting_transcripts_opened,0);
eq(x.private_row_level_source_data_committed_publicly,false);
eq(x.raw_original_source_PDFs_committed_publicly,false);
assert(Object.values(x.reproducibility_private_ledger_sha256).every(h=>/^[0-9a-f]{64}$/.test(h)));
console.log(JSON.stringify({
  suite:'W4 P2 independent UN PV original-source aggregate contract',
  source_only:true,original_original_PV_opened_in_this_test:0,
  verified_country_year_observations:d.all_16_year_source_verified,
  unresolved:d.all_16_year_unverified_or_not_at_risk,
  original_source_coverage_gates:'PASS',
  empirical_lexical_fit:'NOT_RUN',calibrated_inference:'FAIL',
  public_empirical_release:'FAIL',reserved_october_2026_transcripts_opened:0,
  status:'PASS'
}));
