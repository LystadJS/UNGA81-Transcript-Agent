"""Independent pre-freeze gate audit for prospective temporal v3.

This audit cannot produce an approved freeze or run development/holdout.
It lists identified methodological incompleteness without altering v2.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from .v3_freeze_candidate import proposal_receipt, ROOT

def review_candidate():
    candidate=proposal_receipt()
    design=json.loads((ROOT/"v3_design_proposal.json").read_text())
    expected={
        "v3_prototype.py","v3_nuisance.py","v3_design_proposal.json",
        "test_v3_prototype.py","test_v3_nuisance.py",
        "v3_grouped_development.py","test_v3_grouped_development.py",
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
    # An independent reviewer must not infer effective independent year
    # replicates from this descriptive year-score sandwich.
    gates={
        "source_hash_integrity": "PASS",
        "candidate_design_status": "PASS_UNAPPROVED",
        "holdout_execution_suppressed": "PASS",
        "v2_frozen_integrity": "NOT_INDEPENDENTLY_REHASHED_BY_THIS_MODULE",
        "year_serial_dependence_aware_gamma_interval": "FAIL_NOT_IDENTIFIED",
        "gamma_model_misspecification_and_coverage": "NOT_RUN",
        "year_process_nugget_external_identification": "FAIL_NOT_IDENTIFIED",
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
            "gamma":"year-cluster sandwich reported only as a diagnostic; year dependence remains unaccounted for",
            "measurement":"replicate measurement error estimable under independent pairs, but calendar-year process nugget is not identified",
            "selection":"without randomized recovery of missing original outcomes, outcome-dependent transcript selection is not identified",
        },
        "approved":False,"v3_holdout_authorized":False,"real_fit_authorized":False,
    }

if __name__=="__main__":
    print(json.dumps(review_candidate(),sort_keys=True,indent=2))
