"""Synthetic-only security/lineage/denominator tests for coordinator adapter."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'tests'))
import bridge
import fixtures
import readout

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.envelope, self.intent, self.proofs, self.approval=fixtures.make_fixture(readout)

    def prepare(self):
        return bridge.prepare(self.envelope,self.intent,self.proofs,self.approval,readout_module=readout)

    def denied(self, code=None):
        with self.assertRaises(bridge.Withheld) as cm:
            self.prepare()
        if code:
            self.assertEqual(cm.exception.code,code)

    def test_01_synthetic_complete_descriptive_draft(self):
        c=self.prepare()
        self.assertEqual(c.population_audit,{'total_in_frame':5,'eligible':2,'excluded':1,'missing':2,
          'planned_fits':1,'attempted_fits':1,'converged_fits':1,'failed_fits':0,'skipped_fits':0,'unassigned':1})
        self.assertEqual(len(c.report['sources']),2)
        self.assertEqual(len(c.report['findings'][0]['supporting']),1)
        self.assertEqual(len(c.report['findings'][0]['contrary']),1)
        self.assertNotIn('\"original_bytes\":',json.dumps(c.report))
        # The bridge DOES NOT mint ReviewDecision or authorize the draft.
        view=readout.normalize(c.report,c.proofs,None)
        self.assertEqual(view['release_state'],'withheld')
        self.assertEqual(view['sources'],[])

    def test_02_external_synthetic_review_is_separate(self):
        c=self.prepare()
        from readout import ReviewDecision, report_digest
        decision=ReviewDecision(report_sha256=report_digest(c.report),source_gate='pass',
             reviewer_gate='pass',privacy_gate='pass',statistical_gate='not_run',
             evaluation_role='synthetic_fixture')
        view=readout.normalize(c.report,c.proofs,decision)
        self.assertEqual(view['release_state'],'descriptive_only')
        self.assertFalse(view['publication_eligible'])
        for fmt in ('json','markdown','html'):
            output=readout.render(c.report,fmt,proofs=c.proofs,decision=decision)
            self.assertNotIn(fixtures.source_text('synthetic-A'),output)
            self.assertNotIn('original_bytes":',output)

    def test_03_untrusted_v1_does_not_self_approve(self):
        self.approval=None
        self.denied('upstream_validation_receipt_missing_or_mismatch')

    def test_04_receipt_wrong_digest(self):
        self.approval=replace(self.approval,envelope_sha256='f'*64)
        self.denied('upstream_validation_receipt_missing_or_mismatch')

    def test_05_mutated_selection_receipt_denied(self):
        self.envelope['upstream']['selection_sha256']='0'*64
        self.denied('upstream_validation_receipt_missing_or_mismatch')

    def test_06_malformed_json_schema(self):
        self.envelope['random_private_text']='PRIVATE_UN_APPROVED'
        self.approval=fixtures.reaffirm(self.envelope,self.approval)
        self.denied('interchange_schema_invalid')

    def test_07_real_split_not_allowed_even_with_receipt(self):
        self.envelope['cohort']['split']='development'
        self.envelope['producer']['fixture_kind']='private_development'
        self.approval=fixtures.reaffirm(self.envelope,self.approval)
        self.denied('real_source_mode_disabled')

    def test_08_fake_publication_unlock_denied(self):
        self.envelope['publication_eligible']=True
        self.approval=fixtures.reaffirm(self.envelope,self.approval)
        self.denied('interchange_schema_invalid')

    def test_09_observation_id_duplicate(self):
        self.envelope['observations'][1]['id']='synthetic-A'
        self.approval=fixtures.reaffirm(self.envelope,self.approval)
        self.denied('duplicate_source_or_model_id')

    def test_10_model_basis_drift(self):
        self.envelope['results'][0]['representation_basis_id']='different'
        self.approval=fixtures.reaffirm(self.envelope,self.approval)
        self.denied('interchange_representation_mismatch')

    def test_11_parent_sha_corruption(self):
        self.envelope['observations'][0]['parent_text_sha256']='0'*64
        self.approval=fixtures.reaffirm(self.envelope,self.approval)
        self.denied('source_text_hash_basis_mismatch')

    def test_12_missing_source_fail_closed(self):
        self.proofs['synthetic-A']=replace(self.proofs['synthetic-A'],accepted=False)
        self.denied('authenticated_source_receipt_required')

    def test_13_private_source_fail_closed(self):
        self.proofs['synthetic-A']=replace(self.proofs['synthetic-A'],public=False)
        self.denied('authenticated_source_receipt_required')

    def test_14_raw_bytes_tampered(self):
        self.proofs['synthetic-A']=replace(self.proofs['synthetic-A'],original_bytes=b'FAKE PRIVATE SOURCE')
        self.denied('source_original_bytes_mismatch')

    def test_15_text_hash_corruption(self):
        self.envelope['observations'][0]['text_sha256']='1'*64
        self.approval=fixtures.reaffirm(self.envelope,self.approval)
        self.denied('source_text_hash_basis_mismatch')

    def test_16_wrong_json_pointer(self):
        self.envelope['observations'][0]['json_pointer']='/records/9/text'
        self.envelope['evidence'][0]['json_pointer']='/records/9/text'
        self.approval=fixtures.reaffirm(self.envelope,self.approval)
        self.denied('source_parent_or_representation_mismatch')

    def test_17_invalid_codepoint_offset(self):
        self.envelope['evidence'][0]['end']=len(self.proofs['synthetic-A'].text)+20
        self.approval=fixtures.reaffirm(self.envelope,self.approval)
        self.denied('interchange_evidence_outside_observation')

    def test_18_invented_country_attribution_rejected(self):
        self.intent['findings'][0]['country_attribution']={'iso3':'USA'}
        self.denied('country_stance_requires_separate_adjudication')

    def test_19_invented_stance_rejected(self):
        self.intent['findings'][0]['stance']={'position':'support'}
        self.denied('country_stance_requires_separate_adjudication')

    def test_20_unknown_source_reference(self):
        self.intent['findings'][0]['supporting']=['synthetic-nope']
        self.denied('unknown_evidence_observation')

    def test_21_source_unavailable_as_support(self):
        self.intent['findings'][0]['supporting']=['synthetic-D']
        self.denied('unavailable_or_excluded_evidence')

    def test_22_role_swap_denied(self):
        self.intent['findings'][0]['supporting']=['synthetic-B']
        self.denied('unverified_evidence_role_or_identity')

    def test_23_provisional_evidence_denied(self):
        self.envelope['evidence'][0]['verification']='provisional'
        self.approval=fixtures.reaffirm(self.envelope,self.approval)
        self.denied('evidence_verification_or_span_missing')

    def test_24_duplicate_evidence_role(self):
        self.envelope['evidence'].append(copy.deepcopy(self.envelope['evidence'][0]))
        self.approval=fixtures.reaffirm(self.envelope,self.approval)
        self.denied('ambiguous_evidence_pointer')

    def test_25_contrary_none_not_inferred(self):
        self.intent['findings'][0]['contrary']=[]
        self.intent['findings'][0]['contrary_search']='assessed_none'
        self.denied('contrary_absence_cannot_be_certified')

    def test_26_missing_model_result(self):
        self.envelope['results']=self.envelope['results'][1:]
        self.approval=fixtures.reaffirm(self.envelope,self.approval)
        self.denied('interchange_result_coverage_mismatch')

    def test_27_fit_ledger_mismatch(self):
        self.envelope['coverage']['models'][0]['successful_fits']=2
        self.approval=fixtures.reaffirm(self.envelope,self.approval)
        self.denied('interchange_fit_coverage_invalid')

    def test_28_missingness_ledger_preserved(self):
        c=self.prepare()
        self.assertEqual(c.report['coverage']['missing_reasons'],[
          {'code':'unavailable_unavailable','count':1},
          {'code':'unobserved_inventory','count':1}])
        self.assertEqual(c.report['coverage']['exclusion_reasons'],[{'code':'excluded_procedural','count':1}])

    def test_29_unsupported_authoring_key(self):
        self.intent['outlook_send']=True
        self.denied('authoring_intent_incomplete')

    def test_31_unavailable_count_must_match_source_frame(self):
        self.envelope['coverage']['unavailable_sources']=0
        self.approval=fixtures.reaffirm(self.envelope,self.approval)
        self.denied('interchange_unavailable_source_count_mismatch')

    def test_32_duplicate_supporting_observation_denied(self):
        self.intent['findings'][0]['supporting']=['synthetic-A','synthetic-A']
        self.denied('duplicate_finding_evidence_identity')

    def test_33_unfitted_observation_cannot_ground_exploratory_claim(self):
        self.envelope['results'][1]['status']='not_fitted'
        self.envelope['results'][1]['cluster']=None
        self.envelope['results'][1]['reason']='synthetic not fitted'
        self.envelope['coverage']['models'][0]['unassigned']=0
        self.envelope['coverage']['models'][0]['not_fitted']=1
        self.approval=fixtures.reaffirm(self.envelope,self.approval)
        self.intent['findings'][0]['category']='exploratory'
        self.intent['findings'][0]['observation']=None
        self.intent['findings'][0]['pattern']='Fictional grouping only; no real diplomatic evidence'
        self.denied('exploratory_evidence_not_fitted')

    def test_30_statistical_result_requires_external_gate(self):
        self.intent['findings'][0]['category']='exploratory'
        self.intent['findings'][0]['pattern']='Fictional grouping, no diplomatic inference'
        self.intent['findings'][0]['observation']=None
        c=self.prepare()
        from readout import ReviewDecision, report_digest
        decision=ReviewDecision(report_sha256=report_digest(c.report),source_gate='pass',reviewer_gate='pass',
          privacy_gate='pass',statistical_gate='not_run',evaluation_role='synthetic_fixture')
        self.assertEqual(readout.normalize(c.report,c.proofs,decision)['release_state'],'withheld')

if __name__=='__main__':
    unittest.main()
