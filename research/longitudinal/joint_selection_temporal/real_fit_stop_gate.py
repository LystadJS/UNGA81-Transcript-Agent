"""Explicit STOP gate before ANY 2008–2023 real feature/embedding fit.

Never initiates training itself. Only verifies independent synthetic and original
source preflight acceptance. A Boolean flag alone cannot authorize publication;
the cohort-specific frozen training selection and protocol still need owner review.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

def assess(holdout,source):
    reasons=[]
    if holdout.get('schema')!='un.w4.joint_selection_serial_dependence.independent_holdout.v1':
        reasons.append('independent_holdout_schema_unverified')
    if holdout.get('horizon_16_all_preregistered_numerical_gates_passed') is not True:
        reasons.append('temporal_covariance_failed_independent_T16_recovery_or_coverage')
    if holdout.get('rho_point_reliability_scenarios_passed')!=18:
        reasons.append('rho_parameter_reliability_not_demonstrated_in_all_identifiable_worlds')
    if holdout.get('unsafe_no_audit_fits')!=0 or \
      holdout.get('actual_MNAR_no_audit_abstentions')!=1440:
        reasons.append('unsafe_or_missing_no_audit_refusal')
    if source.get('schema')!='un.W4.source-preflight.private-aggregate.v1':
        reasons.append('real_source_authentication_schema_mismatch')
    if source.get('random_phase2_outcome_audit_provenance_available') is not True:
        reasons.append('no_randomized_verified_outcome_audit_for_missing_real_speeches')
    if source.get('common_2008_2023_frozen_training_selection_accepted') is not True:
        reasons.append('source_cross_2008_2023_comparability_and_training_selection_not_accepted')
    if source.get('source_sampling_generalizable_to_UN_member_census') is not True:
        reasons.append('population_sampling_and_response_inclusion_not_validated')
    return {'schema':'un.W4.new_real_representation_fitting_decision.v1',
            'decision':'WITHHELD_NOT_FIT' if reasons else 'PROVISIONAL_REVIEW_REQUIRED',
            'stop_reasons':reasons,'new_real_2008_2023_representation_fitted':False,
            'real_world_CI_eligible':False,'publication_eligible':False,
            'heldout_37_reserved_meeting_texts_read':0,
            'human_owner_release_confirmation':'REQUIRED_EVEN_IF_ALL_COMPUTATIONAL_GATES_PASS'}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--holdout',type=Path,required=True)
    p.add_argument('--source-preflight',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise ValueError('Gate receipt must not overwrite older evidence')
    holdout=json.loads(a.holdout.read_text())
    source=json.loads(a.source_preflight.read_text())
    status=assess(holdout,source)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(status,indent=2))
    if status['decision']=='WITHHELD_NOT_FIT':
        raise SystemExit(2)
    raise SystemExit('PROVISIONAL_REVIEW_REQUIRED: no automatic real representation training')

if __name__=='__main__':main()
