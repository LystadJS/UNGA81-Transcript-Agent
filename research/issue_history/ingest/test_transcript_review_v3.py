"""Invented committee-role regressions; no actual transcript excerpts."""
import unittest
from unittest.mock import patch
from . import test_transcript_review as fixtures
from . import transcript_review_v3 as R


class CommitteeRoleTests(unittest.TestCase):
    setUp=fixtures.TranscriptReviewTests.setUp
    prepare=fixtures.TranscriptReviewTests.prepare
    snapshot=fixtures.TranscriptReviewTests.snapshot

    def build(self):return R.build_review_overlay(self.store,self.raw,self.receipt,self.frame,self.reviews)

    def test_new_committee_roles_case_and_punctuation_reject_national(self):
        for role in ('Vice-Chair','VICE CHAIR','Vice—Chairperson','vIcE.cHaIrPeRsOn','Rapporteur','RAPPORTEUR','Rap-porteur'):
            with self.subTest(role=role):
                self.doc['transcript']['data'][0]['speaker']['function']=role;self.prepare();before=self.snapshot()
                with self.assertRaisesRegex(ValueError,'Vice-chair or rapporteur'):self.build()
                self.assertEqual(before,self.snapshot())

    def test_procedural_and_unclear_roles_are_preserved(self):
        self.doc['transcript']['data'][0]['speaker']['function']='Vice-Chair';self.prepare()
        for capacity in ('procedural','unclear'):
            self.reviews[0]['capacity']=capacity;self.reviews[0]['policy_matches']=[];before=self.snapshot();result=self.build()
            self.assertEqual(capacity,result['reviews'][0]['capacity_proposal']);self.assertEqual(0,result['summary']['national_candidate_countries']);self.assertEqual(before,self.snapshot())

    def test_explicit_collective_mandate_not_replaced_by_country(self):
        first=self.doc['transcript']['data'][0];first['speaker'].update(function='Rapporteur',group='Synthetic Committee Group')
        first['paragraphs'][0]['sentences'][0]['text']='I speak on behalf of the Synthetic Committee Group.'
        self.prepare();self.reviews[0]['capacity']='collective';self.reviews[0]['policy_matches']=[];result=self.build()
        self.assertEqual('Synthetic Committee Group',result['reviews'][0]['group_entity']);self.assertIsNone(result['reviews'][0]['country_entity'])

    def test_legitimate_national_remains_provisional_and_source_bound(self):
        self.doc['transcript']['data'][0]['speaker']['function']='Permanent Representative';self.prepare();before=self.snapshot();result=self.build()
        self.assertEqual(R.VERSION,result['version']);self.assertEqual('Nigeria',result['reviews'][0]['country_entity'])
        self.assertFalse(result['owner_confirmed']);self.assertFalse(result['accepted_positions']);self.assertFalse(result['comparisons_eligible'])
        self.assertIn('transcript_review_v3.py',result['input_fingerprints']['method_sha256']);self.assertEqual(before,self.snapshot())

    def test_old_role_guards_remain_active(self):
        for role in ('PGA','Vice-President','Chair','Co-Chair'):
            with self.subTest(role=role):
                self.doc['transcript']['data'][0]['speaker']['function']=role;self.prepare()
                with self.assertRaises(ValueError):self.build()

    def test_final_current_batch_recheck_is_required(self):
        before=self.snapshot()
        with patch.object(R,'get_current_batch',return_value=None):
            with self.assertRaisesRegex(ValueError,'Current batch changed'):self.build()
        self.assertEqual(before,self.snapshot())


if __name__=='__main__':unittest.main()
