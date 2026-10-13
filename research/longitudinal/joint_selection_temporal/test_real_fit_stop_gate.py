"""Fail-closed representation-fit eligibility and source-status negative tests."""
import unittest
from real_fit_stop_gate import assess

class StopGateTests(unittest.TestCase):
 def test_failed_T16_covariance_blocks_even_with_real_source_audit(self):
  h={'schema':'un.w4.joint_selection_serial_dependence.independent_holdout.v1',
     'horizon_16_all_preregistered_numerical_gates_passed':False,
     'rho_point_reliability_scenarios_passed':0,
     'unsafe_no_audit_fits':0,'actual_MNAR_no_audit_abstentions':1440}
  s={'schema':'un.W4.source-preflight.private-aggregate.v1',
     'random_phase2_outcome_audit_provenance_available':True,
     'common_2008_2023_frozen_training_selection_accepted':True,
     'source_sampling_generalizable_to_UN_member_census':True}
  v=assess(h,s)
  self.assertEqual(v['decision'],'WITHHELD_NOT_FIT')
  self.assertIn('temporal_covariance_failed_independent_T16_recovery_or_coverage',v['stop_reasons'])
 def test_synthetic_success_cannot_authorize_no_audit_real_source(self):
  h={'schema':'un.w4.joint_selection_serial_dependence.independent_holdout.v1',
     'horizon_16_all_preregistered_numerical_gates_passed':True,
     'rho_point_reliability_scenarios_passed':18,
     'unsafe_no_audit_fits':0,'actual_MNAR_no_audit_abstentions':1440}
  s={'schema':'un.W4.source-preflight.private-aggregate.v1',
     'random_phase2_outcome_audit_provenance_available':False,
     'common_2008_2023_frozen_training_selection_accepted':True,
     'source_sampling_generalizable_to_UN_member_census':True}
  v=assess(h,s)
  self.assertEqual(v['decision'],'WITHHELD_NOT_FIT')
  self.assertIn('no_randomized_verified_outcome_audit_for_missing_real_speeches',v['stop_reasons'])
 def test_no_automatic_real_fit_even_if_all_boolean_checks_pass(self):
  h={'schema':'un.w4.joint_selection_serial_dependence.independent_holdout.v1',
     'horizon_16_all_preregistered_numerical_gates_passed':True,
     'rho_point_reliability_scenarios_passed':18,'unsafe_no_audit_fits':0,
     'actual_MNAR_no_audit_abstentions':1440}
  s={'schema':'un.W4.source-preflight.private-aggregate.v1',
     'random_phase2_outcome_audit_provenance_available':True,
     'common_2008_2023_frozen_training_selection_accepted':True,
     'source_sampling_generalizable_to_UN_member_census':True}
  z=assess(h,s)
  self.assertEqual(z['decision'],'PROVISIONAL_REVIEW_REQUIRED')
  self.assertFalse(z['new_real_2008_2023_representation_fitted'])
  self.assertFalse(z['real_world_CI_eligible'])
  self.assertEqual(z['human_owner_release_confirmation'],'REQUIRED_EVEN_IF_ALL_COMPUTATIONAL_GATES_PASS')

if __name__=='__main__':unittest.main()
