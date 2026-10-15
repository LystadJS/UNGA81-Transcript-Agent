"""Independent pre-freeze gate audit for prospective temporal v3.

This audit cannot produce an approved freeze or run development/holdout.
It lists identified methodological incompleteness without altering v2.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from .v3_freeze_candidate import proposal_receipt, ROOT
from .v3_identification_audit import (
    conditional_vs_marginal_gamma, no_audit_mnar_counterexample,
    year_nugget_measurement_alias, nuisance_grid_truth_witness,
    independent_freeze_decision,
)

def review_candidate():
    candidate=proposal_receipt()
    design=json.loads((ROOT/"v3_design_proposal.json").read_text())
    expected={
        "v3_prototype.py","v3_nuisance.py","v3_design_proposal.json",
        "test_v3_prototype.py","test_v3_nuisance.py",
        "v3_grouped_development.py","test_v3_grouped_development.py",
        "v3_dependence_benchmark.py","v3_dependence_study.py",
        "test_v3_dependence_benchmark.py","test_v3_dependence_replay.py",
        "DEVELOPMENT_DEPENDENCE_RESULTS_V3.md",
        "v3_development_failure_masks.json",
        "v3_serial_partial.py","v3_serial_partial_study.py",
        "test_v3_serial_partial.py","test_v3_serial_partial_replay.py",
        "v3_serial_partial_failure_index.json",
        "SERIAL_RESPONSE_PARTIAL_COVARIANCE_V3.md",
        "v3_identification_audit.py","test_v3_identification_audit.py",
        "V3_IDENTIFICATION_FREEZE_DECISION.md","v3_identification_decision.json",
        "v3_freeze_candidate.py","test_v3_freeze_candidate.py",
        "v3_coordinator_preflight.py","test_v3_coordinator_preflight.py",
        "v3_finite_year_continuous.py","v3_finite_year_study.py",
        "test_v3_finite_year_continuous.py","test_v3_finite_year_replay.py",
        "v3_finite_year_development_receipt.json","v3_finite_year_failure_masks.json",
        "V3_FINITE_YEAR_CONTINUOUS_REVIEW.md",
        "v3_hierarchical_external.py","v3_hierarchical_external_study.py",
        "test_v3_hierarchical_external.py","test_v3_hierarchical_external_replay.py",
        "v3_hierarchical_external_development_receipt.json",
        "v3_hierarchical_external_failure_masks.json",
        "V3_HIERARCHICAL_EXTERNAL_FREEZE_REVIEW.md",
        "v3_hierarchical_freeze_decision.json",
    }
    if set(candidate["source_sha256"]) != expected:
        raise ValueError("freeze candidate source completeness failed")
    for name,sha in candidate["source_sha256"].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:
            raise ValueError("source hash mismatch")
    if design.get("gates_frozen") is not False or design.get("holdout_authorized") is not False:
        raise ValueError("unapproved protocol tried to authorize holdout")
    if candidate["holdout_run"] is not False or candidate["v2_thresholds_unmodified"] is not True:
        raise ValueError("v2 invariance/holdout refusal mismatch")
    # Independently verify the original v2 freeze bytes and exact pinned
    # executable sources, without importing any v2 generator or running a fit.
    v2_bytes=(ROOT/"frozen_development_v2.json").read_bytes()
    if hashlib.sha256(v2_bytes).hexdigest()!=(
            "8a3abd19198332dc58c19299301c5ce1f0bd61749ef724e6093f2027bdf970fd"):
        raise ValueError("original frozen v2 development bytes modified")
    frozen_v2=json.loads(v2_bytes)
    for name,sha in frozen_v2["frozen_code_hashes"].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:
            raise ValueError("original v2 fitted producer source changed")

    # Independent mathematical identification counterexamples, not fitted
    # policy outcomes or external human/statistical acceptance.
    witness_gamma=conditional_vs_marginal_gamma()
    witness_mnar=no_audit_mnar_counterexample()
    witness_alias=year_nugget_measurement_alias()
    witness_grid=nuisance_grid_truth_witness()
    refusal=independent_freeze_decision(candidate,design)
    decision=json.loads((ROOT/"v3_identification_decision.json").read_text())
    if decision.get("decision")!=refusal["status"] or decision.get("reviewer_approval_record")!=(
            "NONE_NO_INDEPENDENT_HUMAN_STATISTICIAN_SIGNOFF"):
        raise ValueError("coordinator decision or reviewer identity misrepresented")
    if (witness_gamma["absolute_difference"]<=.4 or
            witness_mnar["gamma_point_identified"] or
            witness_mnar["candidates"][0]["compatible_gamma"]<=0 or
            witness_mnar["candidates"][1]["compatible_gamma"]>=0 or
            witness_alias["max_absolute_covariance_difference"]>1e-12 or
            witness_grid["true_nuisance_in_narrow_range"]):
        raise ValueError("identification counterexample failed")
    numer=decision["numerical_development"]
    if (numer["gamma_completed"]+numer["gamma_refused"]!=numer["gamma_method_attempts"] or
            numer["covariance_completed"]+numer["covariance_refused"]!=numer["covariance_attempts"] or
            numer["gamma_refused"]+numer["covariance_refused"]!=numer["all_failed_fit_ids_retained"]):
        raise ValueError("prospective review evidence loses failed attempts")
    finite=json.loads((ROOT/"v3_finite_year_development_receipt.json").read_text())
    masks=json.loads((ROOT/"v3_finite_year_failure_masks.json").read_text())
    if (finite.get("schema")!="un.w4.v3.finite-year-development-replay.v1" or
            finite.get("holdout_attempted")!=0 or finite.get("statistical_acceptance") is not False or
            masks.get("v3_holdout_attempted")!=0 or masks.get("real_fit_authorized") is not False):
        raise ValueError("finite-year research improperly authorizes confirmation")
    if (finite["gamma_methods_attempted"] != finite["gamma_methods_completed"]+finite["gamma_methods_refused"] or
            finite["gamma_bootstrap_attempted"] != finite["gamma_bootstrap_completed"]+finite["gamma_bootstrap_failed"] or
            finite["cov_methods_attempted"] != finite["cov_methods_completed"]+finite["cov_methods_refused"]):
        raise ValueError("finite-year research attempt conservation failed")
    recovered=sum(int(x["mask_hex"],16).bit_count() for x in masks["masks"])
    if (recovered!=finite["failure_ledger_count"] or recovered!=masks["failures"] or
            masks["canonical_uncompressed_failure_sha256"]!=finite["failure_ledger_canonical_sha256"]):
        raise ValueError("finite-year failed-fit index or checksum mismatch")
    hierarchical=json.loads((ROOT/"v3_hierarchical_external_development_receipt.json").read_text())
    hierarchical_masks=json.loads((ROOT/"v3_hierarchical_external_failure_masks.json").read_text())
    hierarchical_review=json.loads((ROOT/"v3_hierarchical_freeze_decision.json").read_text())
    if (hierarchical.get("schema")!="un.w4.v3.hierarchical-external-development-replay.v1" or
            hierarchical_review.get("decision")!="STATISTICAL_FREEZE_NOT_ACCEPTED" or
            hierarchical.get("v3_holdout_attempted")!=0 or
            hierarchical_review.get("v3_holdout_attempted")!=0 or
            hierarchical.get("statistical_freeze_accepted") is not False or
            hierarchical_review.get("real_fit_authorized") is not False):
        raise ValueError("hierarchical development improper statistical promotion")
    if (hierarchical["gamma_attempted"]!=hierarchical["gamma_completed"]+hierarchical["gamma_refused"] or
            hierarchical["cov_attempted"]!=hierarchical["cov_completed"]+hierarchical["cov_refused"] or
            hierarchical["failure_count"]!=hierarchical["gamma_refused"]+hierarchical["cov_refused"]):
        raise ValueError("hierarchical response and external-scale lost attempted fits")
    mask_count=sum(int(item["failed_replicates_hex"],16).bit_count()
                   for item in hierarchical_masks["methods_and_scenarios"])
    if (mask_count!=hierarchical["failure_count"] or
            mask_count!=hierarchical_masks["retained_method_failures"] or
            hierarchical_masks["full_failure_canonical_sha256"]!=hierarchical["failure_canonical_sha256"]):
        raise ValueError("hierarchical failed-fit source identity mismatch")
    if (hierarchical_review["studies"]["gamma"]["refused"]!=hierarchical["gamma_refused"] or
            hierarchical_review["studies"]["covariance"]["refused"]!=hierarchical["cov_refused"] or
            hierarchical_review["all_failed_fit_records_retained"]!=mask_count):
        raise ValueError("hierarchical coordinator review disagrees with development evidence")
    # Continuous-bound correctness is mathematical and conditional. In
    # particular, neither upper scale source nor UN annual-selection
    # unbiasedness is authenticated by this source-free synthetic module.
    # An independent reviewer must not infer effective independent year
    # replicates from this descriptive year-score sandwich.
    gates={
        "source_hash_integrity": "PASS",
        "candidate_design_status": "PASS_UNAPPROVED",
        "holdout_execution_suppressed": "PASS",
        "v2_frozen_integrity": "PASS_REHASHED_ORIGINAL_RECEIPT_AND_FOUR_SOURCE_HASHES",
        "conditional_vs_marginal_gamma": "FAIL_NOT_SAME_ESTIMAND",
        "unaudited_MNAR_gamma": "FAIL_NOT_IDENTIFIED",
        "finite_covariance_nuisance_grid": "NOT_A_CONTINUOUS_IDENTIFIED_SET",
        "independent_methodological_statistician_signoff": "NOT_OBTAINED",
        "year_serial_dependence_aware_gamma_interval": "FAIL_NOT_IDENTIFIED",
        "gamma_model_misspecification_and_coverage": "DEVELOPMENT_YEAR_FE_POINT_BIAS_IMPROVED_BUT_INTERVAL_UNCALIBRATED",
        "year_process_nugget_external_identification": "FAIL_NOT_IDENTIFIED",
        "continuous_nuisance_variance_upper_bound": "PASS_CONDITIONAL_MATHEMATICAL_PROOF_ONLY",
        "external_empirical_year_scale_upper_source": "NOT_VERIFIED",
        "calendar_year_block_refit_gamma_interval": "DEVELOPMENT_NOT_CALIBRATED",
        "hierarchical_year_AR1_gamma_interval": "DEVELOPMENT_TWO_STAGE_NOT_CALIBRATED",
        "hierarchical_year_nuisance_profile": "FAILED_WEAK_IDENTIFICATION",
        "real_external_gaussian_world_scale_calibration": "NOT_AUTHENTICATED",
        "bonferroni_external_scale_continuous_bound": "CONDITIONAL_MATHEMATICS_ONLY",
        "response_audit_real_source_independence": "NOT_VERIFIED",
        "source_design_era_comparability": "NOT_VERIFIED",
        "full_prespecified_grid_and_thresholds": "NOT_FROZEN",
        "independent_holdout_producer_and_seeds": "NOT_IMPLEMENTED",
        "reviewer_approval": "NOT_OBTAINED",
    }
    return {
        "schema":"un.w4.v3.coordinator-freeze-preflight.v1",
        "status":"NOT_ACCEPTED_FOR_STATISTICAL_FREEZE",
        "engineering_preparation_reviewable":True,
        "candidate_source_sha256":candidate["source_sha256"],
        "gates":gates,
        "methodological_resolution":{
            "gamma":"new two-stage hierarchical annual AR1 empirical Bayes attempted, with all fitted correlated T16 nuisance profiles weak; finite-year structural gamma interval still uncalibrated",
            "measurement":"conditional Bonferroni 2.5% external Gaussian independent-world scale error + 7.5% Gaussian contrast error over a continuous nuisance region; no corresponding historical independent-world scale experiment authenticated",
            "selection":"without randomized recovery of missing original outcomes, outcome-dependent transcript selection is not identified",
        },
        "identification_counterexamples":{
            "conditional_vs_marginal":witness_gamma,
            "unaudited_mnar":witness_mnar,
            "calendar_nugget_alias":witness_alias,
            "narrow_nuisance_grid":witness_grid,
        },
        "approved":False,"v3_holdout_authorized":False,"real_fit_authorized":False,
    }

if __name__=="__main__":
    print(json.dumps(review_candidate(),sort_keys=True,indent=2))
