"""Invented source-local context proofs; no actual transcript excerpts."""
import copy
import json
import unittest
from unittest.mock import patch
from . import test_transcript_review as fixtures
from . import transcript_review_v3 as V3
from . import transcript_context as C


class TranscriptContextTests(unittest.TestCase):
    setUp=fixtures.TranscriptReviewTests.setUp
    prepare=fixtures.TranscriptReviewTests.prepare
    snapshot=fixtures.TranscriptReviewTests.snapshot

    def rows(self):
        overlay=V3.build_review_overlay(self.store,self.raw,self.receipt,self.frame,self.reviews)
        return [{'candidate_id':m['candidate_id'],'review_state':'assistant_provisional',
                 'state':'anchored','object_evidence':[{'pointer':self.pointer(),'quote':'humanitarian access'}],
                 'context_evidence':[{'pointer':self.pointer(),'quote':'in Sudan'}],
                 'relation':'same_sentence','reason':None}
                for r in overlay['reviews'] for m in r['policy_matches']]

    def pointer(self,sentence=0,paragraph=0,segment=0):
        return f'/transcript/data/{segment}/paragraphs/{paragraph}/sentences/{sentence}/text'

    def build(self,rows=None):
        return C.build_context_overlay(self.store,self.raw,self.receipt,self.frame,self.reviews,
                                       self.rows() if rows is None else rows)

    def test_read_only_deterministic_hash_only_provisional_output(self):
        before=self.snapshot();inputs=copy.deepcopy((self.reviews,self.rows()));out=self.build()
        self.assertEqual('un.transcript-context-overlay.v1',out['schema'])
        self.assertEqual(1,out['summary']['anchored']);self.assertEqual(0,out['summary']['accepted_contexts'])
        self.assertEqual(0,out['summary']['comparison_eligible'])
        self.assertFalse(out['contexts'][0]['context_accepted']);self.assertFalse(out['contexts'][0]['comparisons_eligible'])
        self.assertNotIn('humanitarian access',json.dumps(out));self.assertNotIn('in Sudan',json.dumps(out))
        self.assertEqual(before,self.snapshot());self.assertEqual(inputs,(self.reviews,self.rows()))
        self.assertEqual(out,self.build())

    def test_each_candidate_required_exactly_once(self):
        rows=self.rows()
        for bad in ([],rows+copy.deepcopy(rows)):
            with self.assertRaises(ValueError):self.build(bad)

    def test_stale_or_forged_candidate_rejected(self):
        rows=self.rows();rows[0]['candidate_id']='provisional-policy:'+'0'*64
        with self.assertRaises(ValueError):self.build(rows)

    def test_owner_and_unknown_fields_rejected(self):
        for key,value in [('review_state','owner_confirmed'),('comparisons_eligible',True),('context_id','sudan')]:
            rows=self.rows();rows[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.build(rows)

    def test_forged_quote_or_other_segment_rejected(self):
        for field in ('object_evidence','context_evidence'):
            for bad in ({'pointer':self.pointer(),'quote':'Absent wording'},
                        {'pointer':self.pointer(segment=1),'quote':'I now give the floor'}):
                rows=self.rows();rows[0][field]=[bad]
                with self.subTest(field=field,bad=bad),self.assertRaises(ValueError):self.build(rows)

    def test_object_must_be_subset_of_original_match_evidence(self):
        rows=self.rows()
        self.reviews[0]['policy_matches'][0]['evidence'][0]['quote']='safe humanitarian access'
        rows=self.rows();rows[0]['object_evidence'][0]['quote']='Nigeria calls'
        with self.assertRaises(ValueError):self.build(rows)

    def add_sentence(self,text):
        sentences=self.doc['transcript']['data'][0]['paragraphs'][0]['sentences']
        sentences.append({**copy.deepcopy(sentences[0]),'text':text})

    def test_adjacent_context_allowed_but_not_claimed_semantically_verified(self):
        self.add_sentence('The context is the armed conflict in Sudan.');self.prepare()
        rows=self.rows();rows[0]['context_evidence']=[{'pointer':self.pointer(1),'quote':'armed conflict in Sudan'}]
        rows[0]['relation']='adjacent_sentence_review';out=self.build(rows)
        self.assertEqual(1,out['summary']['anchored']);self.assertFalse(out['contexts'][0]['context_accepted'])

    def test_relation_must_match_actual_sentence_distance(self):
        rows=self.rows();rows[0]['relation']='adjacent_sentence_review'
        with self.assertRaises(ValueError):self.build(rows)
        self.add_sentence('Armed conflict in Sudan.');self.prepare();rows=self.rows()
        rows[0]['context_evidence']=[{'pointer':self.pointer(1),'quote':'Sudan'}]
        with self.assertRaises(ValueError):self.build(rows)

    def test_distant_sentence_and_other_paragraph_rejected(self):
        self.add_sentence('Intervening invented sentence.');self.add_sentence('Conflict in Sudan.')
        self.doc['transcript']['data'][0]['paragraphs'].append({'sentences':[copy.deepcopy(self.doc['transcript']['data'][0]['paragraphs'][0]['sentences'][2])]})
        self.prepare()
        for pointer in (self.pointer(2),self.pointer(0,1)):
            rows=self.rows();rows[0]['context_evidence']=[{'pointer':pointer,'quote':'Sudan'}];rows[0]['relation']='adjacent_sentence_review'
            with self.subTest(pointer=pointer),self.assertRaises(ValueError):self.build(rows)

    def test_unresolved_requires_explicit_reason_and_no_anchor(self):
        rows=self.rows();rows[0].update(state='unresolved',object_evidence=[],context_evidence=[],relation=None,reason='ambiguous_reference')
        self.assertEqual(1,self.build(rows)['summary']['unresolved'])
        for change in ({'reason':None},{'relation':'same_sentence'},{'object_evidence':[{'pointer':self.pointer(),'quote':'access'}]}):
            bad=copy.deepcopy(rows);bad[0].update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):self.build(bad)

    def test_anchored_needs_both_evidence_and_null_reason(self):
        for change in ({'object_evidence':[]},{'context_evidence':[]},{'reason':'no_literal_context'}):
            rows=self.rows();rows[0].update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):self.build(rows)

    def test_zero_policy_candidates_has_empty_complete_context_set(self):
        self.reviews[0]['policy_matches']=[];out=self.build([])
        self.assertEqual([],out['contexts']);self.assertEqual(0,out['summary']['candidates'])
        with self.assertRaises(ValueError):self.build([{'candidate_id':'invented'}])

    def test_stale_raw_or_review_identity_fails_closed(self):
        rows=self.rows();self.reviews[0]['text_sha256']='0'*64
        with self.assertRaises(ValueError):self.build(rows)

    def test_changed_current_batch_during_context_build_rejected(self):
        rows=self.rows();before=self.snapshot()
        with patch.object(C,'get_current_batch',return_value=None):
            with self.assertRaises(ValueError):self.build(rows)
        self.assertEqual(before,self.snapshot())

    def test_reopened_store_returns_exact_same_context_metadata(self):
        before=self.build();self.store.close()
        self.store=fixtures.IssueStore(self.path)
        self.assertEqual(before,json.loads(json.dumps(self.build())))

    def test_method_change_during_validation_rejected(self):
        rows=self.rows();methods=C._methods();changed={**methods,'transcript_context.py':'0'*64}
        with patch.object(C,'_methods',side_effect=[methods,changed]):
            with self.assertRaisesRegex(ValueError,'methods changed'):self.build(rows)

    def test_source_role_or_current_source_family_tampering_rejected(self):
        rows=self.rows();before=self.snapshot()
        self.receipt['source_role']='evaluation'
        with self.assertRaises(ValueError):self.build(rows)
        self.assertEqual(before,self.snapshot())
        self.receipt['source_role']='product_development'
        for row in self.store.db.execute('SELECT id,revision,payload FROM source_revisions').fetchall():
            payload=json.loads(row[2])
            if payload.get('family')=='un_transcript_segment':
                payload['family']='official_policy_document'
                self.store.db.execute('UPDATE source_revisions SET payload=? WHERE id=? AND revision=?',
                                      (json.dumps(payload),row[0],row[1]))
        self.store.db.commit()
        with self.assertRaises(ValueError):self.build(rows)


if __name__=='__main__':unittest.main()
