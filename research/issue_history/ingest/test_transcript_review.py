"""Synthetic read-only review proposals; no actual source payloads or labels."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from ..store import IssueStore
from . import test_transcripts_un_audit as fixtures
from . import transcripts_un_audit as A
from . import transcripts_un_batch as B
from . import transcript_review as R


class TranscriptReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.environ.get('SC_ACTION_TEST_ROOT'))
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'history.sqlite';self.store=IssueStore(self.path)
        self.addCleanup(lambda:self.store.close())
        self.doc,self.base_receipt,self.frame=fixtures.fixture()
        first,second=self.doc['transcript']['data']
        first['speaker']['affiliation']='NGA'
        first['paragraphs'][0]['sentences']=[{**first['paragraphs'][0]['sentences'][0],
            'text':'Nigeria calls for safe humanitarian access in Sudan.'}]
        second['speaker'].update(affiliation='GA',affiliation_full='GA',function='PGA',group=None)
        second['paragraphs'][0]['sentences'][0]['text']='I now give the floor to the next representative.'
        self.prepare()

    def prepare(self):
        self.raw=json.dumps(self.doc,ensure_ascii=False).encode()
        self.receipt={**self.base_receipt,'bytes':len(self.raw),'sha256':hashlib.sha256(self.raw).hexdigest()}
        self.audit=A.audit_source(self.raw,self.receipt,self.frame)
        B.persist_artifact(self.store,self.raw,self.receipt,self.frame)
        self.reviews=[]
        for i,segment in enumerate(self.audit['segments']):
            pointer=f'/transcript/data/{i}/paragraphs/0/sentences/0/text'
            quote=self.doc['transcript']['data'][i]['paragraphs'][0]['sentences'][0]['text']
            self.reviews.append({'statement_number':segment['statement_number'],'json_pointer':segment['json_pointer'],
                'text_sha256':segment['text_sha256'],'locator_id':segment['locator_id'],
                'review_state':'assistant_provisional','capacity':'national_candidate' if i==0 else 'procedural',
                'attribution_evidence':[{'pointer':pointer,'quote':quote}],
                'policy_matches':[{'policy_id':'humanitarian_access','proposed_stance':'support','context_id':None,
                    'discourse_labels':['requested_action'],'evidence':[{'pointer':pointer,'quote':quote}],
                    'comparison_eligible':False}] if i==0 else [],'speech_boundary':'unverified'})

    def build(self,reviews=None,raw=None,receipt=None):
        return R.build_review_overlay(self.store,self.raw if raw is None else raw,
            self.receipt if receipt is None else receipt,self.frame,self.reviews if reviews is None else reviews)

    def snapshot(self):
        return {name:[tuple(r) for r in self.store.db.execute('SELECT * FROM '+name+' ORDER BY 1,2')]
                for name in ('sources','source_revisions','artifacts','dependencies','evidence')}

    def test_read_only_structural_overlay_not_accepted_positions(self):
        before=self.snapshot();inputs=copy.deepcopy(self.reviews);result=self.build()
        self.assertEqual('un.transcript-review-overlay.v1',result['schema'])
        self.assertFalse(result['accepted_positions']);self.assertFalse(result['comparisons_eligible'])
        self.assertEqual('unresolved',result['context_resolution'])
        self.assertEqual(0,result['summary']['accepted_positions']);self.assertEqual(0,result['summary']['comparison_eligible'])
        self.assertEqual(1,result['summary']['national_candidate_countries'])
        self.assertEqual('Nigeria',result['reviews'][0]['country_entity'])
        self.assertFalse(result['reviews'][0]['attribution_accepted'])
        self.assertFalse(result['production_intake_accepted'])
        self.assertIn('not_semantic_label_or_attribution_truth',result['structural_validation_scope'])
        self.assertEqual(before,self.snapshot());self.assertEqual(inputs,self.reviews)
        self.assertEqual(result,self.build())

    def test_every_current_segment_must_be_reviewed_exactly_once(self):
        for rows in (self.reviews[:1],self.reviews+[copy.deepcopy(self.reviews[0])]):
            with self.subTest(count=len(rows)):
                with self.assertRaises(ValueError):self.build(reviews=rows)

    def test_source_text_hash_locator_and_segment_pointer_are_bound(self):
        for field,value in [('text_sha256','0'*64),('locator_id','forged-locator'),
                            ('json_pointer','/transcript/data/1'),('statement_number',999)]:
            rows=copy.deepcopy(self.reviews);rows[0][field]=value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.build(reviews=rows)

    def test_quotes_must_be_exact_and_within_the_matching_segment(self):
        for mutation in ('quote','pointer','outside'):
            rows=copy.deepcopy(self.reviews);ev=rows[0]['attribution_evidence'][0]
            if mutation=='quote':ev['quote']='Invented nonexistent words'
            elif mutation=='pointer':ev['pointer']='/transcript/data/0/paragraphs/99/sentences/0/text'
            else:ev.update(pointer='/transcript/data/1/paragraphs/0/sentences/0/text',
                quote=self.doc['transcript']['data'][1]['paragraphs'][0]['sentences'][0]['text'])
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):self.build(reviews=rows)

    def test_policy_evidence_is_also_exactly_bound(self):
        rows=copy.deepcopy(self.reviews);rows[0]['policy_matches'][0]['evidence'][0]['quote']='Absent policy quote'
        with self.assertRaises(ValueError):self.build(reviews=rows)

    def test_owner_labels_comparison_eligibility_and_resolved_context_are_rejected(self):
        for mutation in ('owner','comparable','context','speech'):
            rows=copy.deepcopy(self.reviews)
            if mutation=='owner':rows[0]['review_state']='owner_confirmed'
            elif mutation=='comparable':rows[0]['policy_matches'][0]['comparison_eligible']=True
            elif mutation=='context':rows[0]['policy_matches'][0]['context_id']='sudan'
            else:rows[0]['speech_boundary']='complete'
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):self.build(reviews=rows)

    def test_chair_function_cannot_be_overridden_to_national(self):
        rows=copy.deepcopy(self.reviews);rows[1]['capacity']='national_candidate'
        with self.assertRaises(ValueError):self.build(reviews=rows)

    def test_affiliation_metadata_alone_cannot_substitute_for_national_sentence_evidence(self):
        rows=copy.deepcopy(self.reviews)
        rows[0]['attribution_evidence']=[{'pointer':'/transcript/data/0/speaker/affiliation','quote':'NGA'}]
        with self.assertRaises(ValueError):self.build(reviews=rows)

    def test_group_affiliation_never_becomes_national_country(self):
        self.doc['transcript']['data'][0]['speaker'].update(group='Synthetic group')
        self.prepare()
        with self.assertRaises(ValueError):self.build()
        rows=copy.deepcopy(self.reviews);rows[0]['capacity']='collective'
        result=self.build(reviews=rows)
        self.assertIsNone(result['reviews'][0]['country_entity'])
        self.assertEqual('Synthetic group',result['reviews'][0]['group_entity'])
        self.assertEqual(0,result['summary']['national_candidate_countries'])

    def test_reported_conditions_and_implementation_do_not_invent_stances(self):
        for label in ('reported_condition','claimed_implementation'):
            self.doc['transcript']['data'][0]['paragraphs'][0]['sentences'][0]['text']=(
                'Nigeria reports humanitarian access remains obstructed in Sudan.' if label=='reported_condition'
                else 'Nigeria reports it has provided humanitarian relief access in Sudan.')
            self.prepare()
            rows=copy.deepcopy(self.reviews);match=rows[0]['policy_matches'][0]
            match.update(discourse_labels=[label],proposed_stance=None)
            result=self.build(reviews=rows)
            self.assertIsNone(result['reviews'][0]['policy_matches'][0]['proposed_stance'])
            match['proposed_stance']='support'
            with self.subTest(label=label):
                with self.assertRaises(ValueError):self.build(reviews=rows)

    def test_requested_action_and_condition_can_coexist_without_collapsing_labels(self):
        self.doc['transcript']['data'][0]['paragraphs'][0]['sentences'][0]['text']='Nigeria calls for safe relief access in Sudan because access remains obstructed.'
        self.prepare()
        rows=copy.deepcopy(self.reviews)
        rows[0]['policy_matches'][0]['discourse_labels']=['requested_action','reported_condition']
        result=self.build(reviews=rows)
        self.assertEqual({'requested_action','reported_condition'},set(result['reviews'][0]['policy_matches'][0]['discourse_labels']))
        self.assertEqual(1,result['summary']['requested_action_countries'])
        self.assertEqual(1,result['summary']['reported_condition_countries'])

    def test_multiple_same_country_segments_count_country_once(self):
        second=self.doc['transcript']['data'][1]
        second['speaker']=copy.deepcopy(self.doc['transcript']['data'][0]['speaker'])
        second['paragraphs'][0]['sentences'][0]['text']='Nigeria also requests safe relief access in Sudan.'
        self.prepare();self.reviews[1]['capacity']='national_candidate'
        self.reviews[1]['policy_matches']=copy.deepcopy(self.reviews[0]['policy_matches'])
        self.reviews[1]['policy_matches'][0]['evidence']=copy.deepcopy(self.reviews[1]['attribution_evidence'])
        result=self.build()
        self.assertEqual(2,result['summary']['reviewed_segments'])
        self.assertEqual(1,result['summary']['national_candidate_countries'])
        self.assertEqual(1,result['summary']['requested_action_countries'])
        self.assertEqual(1,len(result['countries']))

    def test_output_contains_hashes_not_source_quotes_or_freeform_notes(self):
        result=self.build();encoded=json.dumps(result)
        quote=self.reviews[0]['attribution_evidence'][0]['quote']
        self.assertNotIn(quote,encoded)
        self.assertEqual(hashlib.sha256(quote.encode()).hexdigest(),result['reviews'][0]['attribution_evidence'][0]['quote_sha256'])
        self.assertNotIn('"quote":',encoded)
        rows=copy.deepcopy(self.reviews);rows[0]['notes']=['SYNTHETIC_PRIVATE_FREEFORM_NOTE']
        try:changed=self.build(reviews=rows)
        except ValueError:return
        self.assertNotIn('SYNTHETIC_PRIVATE_FREEFORM_NOTE',json.dumps(changed))

    def test_current_manifest_must_match_exact_supplied_raw_version(self):
        doc=copy.deepcopy(self.doc);doc['metadata']['new_revision']=True
        raw=json.dumps(doc).encode();receipt={**self.receipt,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        with self.assertRaises(ValueError):self.build(raw=raw,receipt=receipt)

    def test_current_provenance_invalidation_blocks_overlay(self):
        current=B.get_current_batch(self.store,self.frame['meeting_id'],self.receipt['source_url'])
        self.store.db.execute('UPDATE artifacts SET valid=0 WHERE id=?',(current['members'][0]['provenance_artifact_id'],));self.store.db.commit()
        with self.assertRaises(ValueError):self.build()

    def test_json_roundtrip_and_database_reopen_preserve_deterministic_result(self):
        original=self.build();self.store.close();self.store=IssueStore(self.path)
        self.assertEqual(original,self.build(reviews=json.loads(json.dumps(self.reviews))))
        self.assertEqual(original,json.loads(json.dumps(original)))


if __name__=='__main__':unittest.main()
