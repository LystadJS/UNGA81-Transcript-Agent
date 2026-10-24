"""Source-free chair-role regression; the v1 validator remains immutable."""
import hashlib
from pathlib import Path
import unittest
from . import test_transcript_review as fixtures
from . import transcript_review_v2 as R


class VersionedChairTests(unittest.TestCase):
    setUp=fixtures.TranscriptReviewTests.setUp
    prepare=fixtures.TranscriptReviewTests.prepare
    snapshot=fixtures.TranscriptReviewTests.snapshot

    def build(self):
        return R.build_review_overlay(self.store,self.raw,self.receipt,self.frame,self.reviews)

    def test_chair_and_cochair_national_proposals_rejected(self):
        for role in ('Chair','Co-Chair','Chairperson','Co-Chairperson'):
            with self.subTest(role=role):
                self.doc['transcript']['data'][0]['speaker']['function']=role
                self.prepare()
                before=self.snapshot()
                with self.assertRaisesRegex(ValueError,'Chair or co-chair'):self.build()
                self.assertEqual(before,self.snapshot())

    def test_procedural_chair_preserved(self):
        self.doc['transcript']['data'][0]['speaker']['function']='Co-Chair'
        self.prepare();self.reviews[0]['capacity']='procedural';self.reviews[0]['policy_matches']=[]
        result=self.build()
        self.assertEqual('procedural',result['reviews'][0]['capacity_proposal'])
        self.assertEqual(0,result['summary']['national_candidate_countries'])

    def test_national_representative_remains_only_provisional(self):
        self.doc['transcript']['data'][0]['speaker']['function']='Permanent Representative'
        self.prepare();before=self.snapshot();result=self.build()
        self.assertEqual(R.VERSION,result['version'])
        self.assertEqual('Nigeria',result['reviews'][0]['country_entity'])
        self.assertFalse(result['owner_confirmed'])
        self.assertFalse(result['accepted_positions']);self.assertFalse(result['comparisons_eligible'])
        self.assertIn('not_semantic_label_or_attribution_truth',result['structural_validation_scope'])
        self.assertIn('transcript_review_v2.py',result['input_fingerprints']['method_sha256'])
        self.assertEqual(before,self.snapshot())

    def test_v1_source_hash_unchanged(self):
        path=Path(__file__).with_name('transcript_review.py')
        self.assertEqual('08a1a7115d7f442314de46529d0b0baa77a47c1e55f3178ab79382ea00568d09',hashlib.sha256(path.read_bytes()).hexdigest())


if __name__=='__main__':unittest.main()
