"""Version-two cohort checks using invented source artifacts and private stores."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from . import test_transcript_cohort as fixtures
from . import transcript_cohort_v2 as C
from . import transcripts_un_audit as A
from . import transcripts_un_batch as B


class CohortV2Tests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.TranscriptCohortTests()
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)

    def build(self,**changes):
        f=self.fixture
        return C.build_cohort_coverage(f.store,changes.get('frame',f.frame),
            changes.get('artifacts',f.artifacts),changes.get('review_inputs',f.review_inputs))

    def role_fixture(self,role,capacity):
        f=self.fixture;f.add(f.mid,review=True)
        artifact=f.artifacts[f.mid];doc=json.loads(artifact['raw'])
        first=doc['transcript']['data'][0];first['speaker']['function']=role
        if capacity=='procedural':
            first['paragraphs'][0]['sentences'][0]['text']='I now give the floor to the next representative.'
        if capacity=='collective':
            first['speaker']['group']='Synthetic group'
            first['paragraphs'][0]['sentences'][0]['text']='On behalf of the Synthetic group, we call for safe humanitarian access in Sudan.'
        raw=json.dumps(doc).encode();receipt={**artifact['receipt'],'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        entry={**next(e for e in f.frame['meetings'] if e['meeting_id']==f.mid),'frame_sha256':f.frame['sha256']}
        B.persist_artifact(f.store,raw,receipt,entry);audit=A.audit_source(raw,receipt,entry)
        f.artifacts[f.mid]={'raw':raw,'receipt':receipt}
        for row,segment in zip(f.review_inputs[f.mid],audit['segments']):
            for field in ('text_sha256','locator_id','json_pointer'):row[field]=segment[field]
        row=f.review_inputs[f.mid][0];row['capacity']=capacity
        quote=first['paragraphs'][0]['sentences'][0]['text']
        row['attribution_evidence']=[{'pointer':'/transcript/data/0/paragraphs/0/sentences/0/text','quote':quote}]
        if capacity=='procedural':row['policy_matches']=[]
        else:row['policy_matches'][0]['evidence']=copy.deepcopy(row['attribution_evidence'])

    def test_new_schema_and_own_review_method_pins_do_not_change_old_modules(self):
        folder=Path(__file__).parent
        paths=[folder/'transcript_cohort.py',folder/'transcript_review.py',folder/'transcript_review_v2.py']
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        self.fixture.add(self.fixture.mid,review=True);result=self.build()
        self.assertEqual('un.transcript-cohort-coverage.v2',result['schema'])
        self.assertEqual('transcript-cohort-2',result['version'])
        self.assertEqual(1,result['summary']['complete_provisional_review_linkage'])
        pins=result['input_fingerprints']['method_sha256']
        for name in ('transcript_cohort_v2.py','transcript_review_v3.py'):
            self.assertEqual(hashlib.sha256((folder/name).read_bytes()).hexdigest(),pins[name])
        self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})

    def test_vice_chair_national_proposal_is_review_gap_without_country_contribution(self):
        self.role_fixture('Vice-Chair','national_candidate');result=self.build()
        row=self.fixture.row(result)
        self.assertTrue(row['stages']['current_batch_validated'])
        self.assertFalse(row['stages']['complete_provisional_review_linkage'])
        self.assertEqual(0,result['summary']['national_candidate_countries'])
        self.assertEqual([],result['countries'])

    def test_rapporteur_national_proposal_is_also_withheld(self):
        self.role_fixture('Rapporteur','national_candidate');result=self.build()
        self.assertFalse(self.fixture.row(result)['stages']['complete_provisional_review_linkage'])
        self.assertFalse(result['countries'])

    def test_supported_vice_chair_procedure_is_retained(self):
        self.role_fixture('Vice-Chair','procedural');result=self.build()
        self.assertTrue(self.fixture.row(result)['stages']['complete_provisional_review_linkage'])
        self.assertEqual([],result['countries']);self.assertEqual([],result['groups'])

    def test_collective_vice_chair_is_not_forced_into_procedure_or_national_country(self):
        self.role_fixture('Vice-Chair','collective');result=self.build()
        self.assertTrue(self.fixture.row(result)['stages']['complete_provisional_review_linkage'])
        self.assertEqual([],result['countries']);self.assertEqual(1,len(result['groups']))
        self.assertEqual('Synthetic group',result['groups'][0]['group'])

    def test_frame_seal_and_out_of_frame_guards_remain_fail_closed(self):
        frame=copy.deepcopy(self.fixture.frame);frame['sha256']='0'*64
        with self.assertRaises(ValueError):self.build(frame=frame)
        with self.assertRaises(ValueError):self.build(artifacts={'sc/forbidden':{'raw':b'never_opened','receipt':{}}})

    def test_bad_source_pin_is_gap_with_full_roster_preserved(self):
        f=self.fixture;f.add(f.mid,persist=False)
        f.artifacts[f.mid]['receipt']['sha256']='0'*64
        result=self.build()
        self.assertEqual(2,len(result['meetings']))
        self.assertFalse(f.row(result)['stages']['receipt_pinned'])
        self.assertFalse(f.row(result)['stages']['format_audit_verified'])
        self.assertEqual('unknown',result['archive_completeness'])

    def test_missing_sc_is_cohort_scope_and_never_a_policy_or_archive_zero(self):
        result=self.build()
        sc=next(r for r in result['body_coverage'] if r['body']=='SC')
        self.assertEqual('not_in_declared_cohort',sc['status'])
        self.assertEqual('no_accepted_comparable_evidence',result['us_reference']['status'])
        self.assertFalse(result['accepted_positions']);self.assertFalse(result['comparisons_eligible'])

    def test_current_batch_recheck_rejects_concurrent_loss(self):
        f=self.fixture;f.add(f.mid)
        batch=B.get_current_batch(f.store,f.mid,f.artifacts[f.mid]['receipt']['source_url'])
        before=f.snapshot()
        with patch.object(C,'get_current_batch',side_effect=[batch,None]):
            with self.assertRaises(ValueError):self.build()
        self.assertEqual(before,f.snapshot())

    def test_read_only_deterministic_output_contains_no_wording(self):
        f=self.fixture;f.add(f.mid,review=True);before=f.snapshot()
        result=self.build()
        self.assertEqual(result,self.build());self.assertEqual(before,f.snapshot())
        self.assertEqual(result,json.loads(json.dumps(result)))
        self.assertNotIn('Nigeria calls for safe humanitarian access',json.dumps(result))


if __name__=='__main__':unittest.main()
