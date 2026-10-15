"""Prospective v3 freeze CANDIDATE maker, not a preregistration approval.

Hashes local source and proposed design. Does not run simulations, seed a holdout,
derive cutoffs, or modify any frozen v2 files. Output is stdout only.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import platform
from .v3_prototype import verify_design

ROOT=Path(__file__).resolve().parent
FILES=("v3_prototype.py","v3_nuisance.py","v3_design_proposal.json",
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
       "v3_hierarchical_freeze_decision.json")

def proposal_receipt():
    cfg=json.loads((ROOT/"v3_design_proposal.json").read_text())
    verify_design(cfg)
    if cfg.get("gates_frozen") is not False:
        raise ValueError("unapproved v3 design must never be recorded as frozen")
    hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES}
    return dict(schema="un.w4.temporal-v3.freeze-candidate.v1",
        status="UNAPPROVED_DESIGN_CANDIDATE_NOT_FROZEN",
        source_sha256=hashes,
        proposed_primary_horizon=16,
        v2_thresholds_unmodified=True,
        v3_acceptance_thresholds_locked=False,
        development_calibration_run=False,
        independent_holdout_generator_implemented=False,
        independent_holdout_seed_committed=False,
        holdout_run=False,
        response_gamma_grouped_inference_validated=False,
        development_only_grouped_diagnostics_present=True,
        external_measurement_error_calibration_development_only=True,
        serial_year_response_development_only=True,
        hypothetical_covariance_sensitivity_development_only=True,
        externally_measured_year_process_nugget_available=False,
        full_covariance_identification_achieved=False,
        whole_year_block_refit_development_only=True,
        conditional_continuous_variance_math_demonstrated=True,
        external_total_year_scale_source_authenticated=False,
        hierarchical_year_effect_gamma_development_only=True,
        independent_world_gaussian_scale_development_only=True,
        hierarchical_gamma_interval_calibrated=False,
        external_historical_gaussian_scale_authentication=False,
        real_fit_authorized=False,
        next_authorization="coordinator and independent statistician must approve design and model assumptions",
        python_runtime=platform.python_version())

if __name__=="__main__":
    print(json.dumps(proposal_receipt(),indent=2,sort_keys=True))
