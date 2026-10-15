# Make this isolated test directory importable both by nested W4 CI discovery
# and by standalone `unittest discover -s temporal_calibration_v2`.
import sys
from pathlib import Path as _Path
_local = str(_Path(__file__).resolve().parent)
if _local not in sys.path:
    sys.path.insert(0, _local)

import copy
import json
from pathlib import Path
import unittest
import numpy as np

from inference import (NotIdentified,FitFailure,fit_panel,fit_annual,estimate_covariance,
                       oracle_gls,real_fit,METHODS)
from synthetic_dev import draw,DEV_NAMESPACE
from synthetic_holdout import independently_draw,HOLDOUT_NAMESPACE
from source_adapter import audit_manifest,assert_compatible_cohorts,IncompatibleCohort
from run_study import ACCEPTANCE,code_hashes,frozen_receipt,validate_frozen,wilson

class SyntheticStudyTests(unittest.TestCase):
    def test_independent_seed_namespace_and_determinism(self):
        self.assertNotEqual(DEV_NAMESPACE,HOLDOUT_NAMESPACE)
        for function in (draw,independently_draw):
            one,_=function(16,'near_census','iid_MAR',17)
            two,_=function(16,'near_census','iid_MAR',17)
            self.assertTrue(np.array_equal(one['included'],two['included']))
            self.assertTrue(np.array_equal(one['value'],two['value'],equal_nan=True))
        dev,_=draw(16,'near_census','iid_MAR',17)
        hold,_=independently_draw(16,'near_census','iid_MAR',17)
        self.assertFalse(np.array_equal(dev['value'],hold['value'],equal_nan=True))
    def test_hidden_outcomes_are_nan_not_truth(self):
        observed,_=draw(16,'near_census','AR1_MNAR_audited',1)
        self.assertNotIn('truth',observed)
        self.assertTrue(np.isnan(observed['value'][~(observed['responded']|observed['audited'])]).all())
    def test_first_stage_exact_meeting_strata(self):
        for gen in (draw,independently_draw):
            x,_=gen(16,'stratified_2_of_3','iid_MAR',1)
            self.assertEqual(x['meeting'].shape,(16,99))
            for t in range(16):
                chosen=set(x['meeting'][t][x['included'][t]])
                self.assertEqual(len(chosen),8)
                for qtr in range(4):self.assertEqual(sum(3*qtr<=k<3*qtr+3 for k in chosen),2)
            self.assertTrue(np.all(x['inclusion_probability']==2/3))
    def test_no_audit_abstention_both_generators(self):
        for gen in (draw,independently_draw):
            x,_=gen(16,'near_census','AR1_MNAR_no_audit',1)
            with self.assertRaises(NotIdentified):fit_panel(x)
    def test_heldout_regularization_estimates_not_oracle(self):
        x,_=independently_draw(16,'near_census','AR1_MNAR_audited',7)
        result=fit_panel(x)
        self.assertEqual(set(result['methods']),set(METHODS))
        for method,v in result['methods'].items():
            self.assertTrue(v['nuisance_estimated_not_oracle'])
            self.assertGreater(v['se'],0)
            self.assertTrue(np.isfinite(v['beta_hat']))
            if method=='ar1_constrained': self.assertEqual(v['nugget_fraction_hat'],0.)
        self.assertLess(result['annual']['year_effective_n'].min(),99)
    def test_mnar_leakage_tamper(self):
        x,_=draw(16,'near_census','AR1_MNAR_audited',1)
        x['value'][0,0]=123.45 if not np.isfinite(x['value'][0,0]) else np.nan
        with self.assertRaises(NotIdentified):fit_panel(x)
    def test_wrong_first_stage_or_authentication_refused(self):
        x,_=draw(16,'near_census','iid_MAR',2)
        x['inclusion_probability'][0,0]=0
        with self.assertRaises(NotIdentified):fit_panel(x)
        x,_=draw(16,'near_census','iid_MAR',2)
        x['audit_independent']=False
        with self.assertRaises(NotIdentified):fit_panel(x)
    def test_missing_year_and_inconsistent_lineage_refused(self):
        x,_=draw(16,'near_census','iid_MAR',2)
        x['post'][0]=1
        with self.assertRaises(FitFailure):fit_panel(x)
        x,_=draw(16,'near_census','iid_MAR',2)
        x['audited'][x['responded']]=True
        with self.assertRaises(NotIdentified):fit_panel(x)
    def test_no_unjustified_year_independence(self):
        x=np.zeros(16)
        with self.assertRaises(FitFailure):estimate_covariance(x,'unknown_model')
        fitted=estimate_covariance(np.random.default_rng(42).normal(size=16),'ar1_nugget_ridge')
        self.assertIn('weakly_identified_rho',fitted)
        self.assertIn('rho_profile_support_width',fitted)
    def test_oracle_covariance_cholesky_algebra(self):
        T=16;rho=.65;sigma=.04;nugget=.02
        C=sigma*rho**np.abs(np.subtract.outer(np.arange(T),np.arange(T)))+nugget*np.eye(T)
        X=np.column_stack((np.ones(T),np.r_[np.zeros(8),np.ones(8)]))
        result=oracle_gls(np.arange(T)/10,rho,sigma,nugget)
        information=X.T@np.linalg.solve(C,X)
        expected=np.linalg.solve(information,X.T@np.linalg.solve(C,np.arange(T)/10))
        self.assertAlmostEqual(result['beta_hat'],expected[1],places=10)
        self.assertAlmostEqual(result['se']**2,np.linalg.inv(information)[1,1],places=10)
    def test_oracle_known_parameter_coverage(self):
        # Separate fixed-parameter control; never passes truth covariance to feasible fit_panel.
        g=np.random.default_rng(2026101501);T=16;rho=.65;sigma=.04
        C=sigma*rho**np.abs(np.subtract.outer(np.arange(T),np.arange(T)))
        chol=np.linalg.cholesky(C)
        observed=g.standard_normal((500,T))@chol.T+.2*np.r_[np.zeros(8),np.ones(8)]
        ok=sum(oracle_gls(row,rho,sigma)['interval_low']<=.2<=oracle_gls(row,rho,sigma)['interval_high'] for row in observed)
        self.assertTrue(425<=ok<=475,(ok,500))
    def test_pr62_frozen_recovery_thresholds_unaltered(self):
        self.assertEqual((ACCEPTANCE['max_absolute_rho_bias'],ACCEPTANCE['max_rho_rmse'],
                          ACCEPTANCE['max_rho_boundary_fraction']),(.12,.25,.05))
        self.assertEqual(ACCEPTANCE['max_coverage_deviation'],.05)
        self.assertEqual(ACCEPTANCE['target_coverage'],.90)
        self.assertEqual(ACCEPTANCE['min_holdout_completion_rate'],.95)
    def test_freeze_refuses_tampering(self):
        receipt={'schema':'un.w4.temporal_calibration_v2.frozen_development.v1',
           'holdout_inspected_at_freeze':False,
           'development_seed_namespace':DEV_NAMESPACE,
           'holdout_seed_namespace':HOLDOUT_NAMESPACE,
           'frozen_code_hashes':code_hashes(),
           'acceptance_thresholds':ACCEPTANCE,
           'models':list(METHODS),'years':[16,24,32],
           'masks':['near_census','stratified_2_of_3'],
           'worlds':['iid_MAR','AR1_MAR','AR1_MNAR_audited','AR1_MNAR_no_audit','AR1_nugget_MNAR_audited'],
           'rho_grid':[-.2,0.,.1,.25,.4,.55,.7,.85,.92],
           'nugget_grid':[0.,.2,.4,.6,.8],
           'locked_holdout_panels_per_scenario':240,
           'development_completed_identifiable_panels':2880,
           'development_expected_nonidentification':720,
           'critical_values':{str(T):{m:3.0 for m in METHODS} for T in (16,24,32)}}
        validate_frozen(receipt)
        for key,bad in [('development_expected_nonidentification',719),
                         ('frozen_code_hashes',{}),('holdout_inspected_at_freeze',True),
                         ('locked_holdout_panels_per_scenario',241)]:
            attempt=dict(receipt,**{key:bad})
            with self.assertRaises(ValueError,msg=key):validate_frozen(attempt)
    def test_wilson_valid(self):
        lower,upper=wilson(216,240)
        self.assertLess(lower,.90)
        self.assertGreater(upper,.90)
    def test_real_fit_locked(self):
        with self.assertRaises(PermissionError):real_fit(None)

class MetadataAdapterTests(unittest.TestCase):
    def manifest(self):
        h='a'*64
        return {'schema':'un.historical-source-audit.v1',
          'frames':[dict(id='f1',year=2015,meeting_design='design1',genre='debate',language='en',
                         translation_modality='original',roster_definition='99 affiliations',
                         selection_design='2 per stratum')],
          'receipts':[dict(document_id='doc',meeting_id='PV1',year=2015,available=True,
                           transcript_available=True,sha256=h,text_sha256=h)],
          'observations':[dict(id='speech1',frame_id='f1',document_id='doc',meeting_id='PV1',
                               speech_id='s1',country='SYN',year=2015,attribution='unverified',
                               outcome_available=True,inclusion_probability=2/3,speech_length=100,
                               text_sha256=h)]}
    def test_accepted_metadata_still_refuses_empirical_fit(self):
        output=audit_manifest(self.manifest())
        self.assertEqual(output['frames'][0]['metadata_eligible'],1)
        self.assertFalse(output['pooling_authorized'])
        self.assertFalse(output['real_fit_authorized'])
        self.assertFalse(output['frames'][0]['original_source_bytes_independently_authenticated'])
    def test_missingness_distinct_from_absence(self):
        data=self.manifest();data['observations'][0]['outcome_available']=False
        counts=audit_manifest(data)['frames'][0]
        self.assertEqual(counts['outcome_missing'],1)
        self.assertEqual(counts['metadata_eligible'],0)
    def test_corrupt_source_identity_refused(self):
        data=self.manifest();data['receipts'][0]['sha256']='invalid'
        with self.assertRaises(IncompatibleCohort):audit_manifest(data)
    def test_wrong_year_meeting_refused(self):
        data=self.manifest();data['observations'][0]['year']=2016
        with self.assertRaises(IncompatibleCohort):audit_manifest(data)
    def test_duplicate_speech_refused(self):
        data=self.manifest();data['observations'].append(dict(data['observations'][0]))
        with self.assertRaises(IncompatibleCohort):audit_manifest(data)
    def test_cross_era_pooling_refused_even_if_matching_metadata(self):
        a=dict(schema_version='v1',source_design_id='d',population_hash='a',
               representation_fingerprint='z',year_definition='calendar',
               sampling_frame_hash='a',translation_policy='original',roster_definition='99',
               independently_verified_original_bytes=True,independent_nonresponse_outcome_audit=True)
        b=dict(a,population_hash='b')
        with self.assertRaises(IncompatibleCohort):assert_compatible_cohorts(a,b)
        b=dict(a)
        self.assertFalse(assert_compatible_cohorts(a,b)['real_fit_authorized'])
    def test_undocumented_independent_audit_refused(self):
        a=dict(schema_version='v1',source_design_id='d',population_hash='a',
               representation_fingerprint='z',year_definition='calendar',
               sampling_frame_hash='a',translation_policy='original',roster_definition='99',
               independently_verified_original_bytes=True,
               independent_nonresponse_outcome_audit=False)
        with self.assertRaises(IncompatibleCohort):assert_compatible_cohorts(a,a)

if __name__=='__main__':unittest.main()
