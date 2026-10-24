"""Invented sealed cohort metadata; no source fetching or actual UN payloads."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ..store import IssueStore
from ..store.repository import canonical_bytes
from . import test_transcripts_un_audit as fixtures
from . import transcripts_un_audit as A
from . import transcripts_un_batch as B
from . import transcript_cohort as C


def seal(frame):
    value={k:v for k,v in frame.items() if k!='sha256'}
    return {**value,'sha256':hashlib.sha256(canonical_bytes(value)).hexdigest()}


class TranscriptCohortTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.environ.get('SC_ACTION_TEST_ROOT'))
        self.addCleanup(self.temp.cleanup)
        self.store=IssueStore(Path(self.temp.name)/'history.sqlite');self.addCleanup(self.store.close)
        doc,receipt,entry=fixtures.fixture();entry.pop('frame_sha256')
        committee={**entry,'meeting_id':'ga/c3/81/9999','source_family_id':'ga/c3/81/9999',
            'date':'2026-10-02','body':'Third Committee','source_url':'https://transcripts.un.org/en/ga/c3/81/9999',
            'json_url':'https://transcripts.un.org/en/ga/c3/81/9999.json'}
        self.frame=seal({'schema':'un.passage-frame.v1','meetings':[entry,committee]})
        self.mid=entry['meeting_id'];self.committee=committee['meeting_id']
        self.artifacts={};self.review_inputs={}

    def add(self,mid,*,persist=True,review=False,group=None):
        entry=next(m for m in self.frame['meetings'] if m['meeting_id']==mid)
        doc,receipt,old=fixtures.fixture();previous=old['meeting_id']
        doc['url']=entry['source_url'];doc['video'].update(slug=mid,date=entry['date']+'T00:00:00.000Z')
        for segment in doc['transcript']['data']:segment['pageUrl']=segment['pageUrl'].replace(previous,mid)
        first,second=doc['transcript']['data']
        first['speaker'].update(affiliation='NGA',affiliation_full='Nigeria',function=None,group=group)
        first['paragraphs'][0]['sentences']=[{**first['paragraphs'][0]['sentences'][0],
            'text':'Nigeria calls for safe humanitarian access in Sudan.'}]
        second['speaker'].update(affiliation='GA',affiliation_full='GA',function='PGA',group=None)
        second['paragraphs'][0]['sentences'][0]['text']='I now give the floor to the next representative.'
        raw=json.dumps(doc).encode();pin={**receipt,'meeting_id':mid,'frame_date':entry['date'],
            'frame_sha256':self.frame['sha256'],'source_url':entry['json_url'],'final_url':entry['json_url'],
            'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        framed={**entry,'frame_sha256':self.frame['sha256']}
        self.artifacts[mid]={'raw':raw,'receipt':pin}
        if persist:B.persist_artifact(self.store,raw,pin,framed)
        if review:
            audit=A.audit_source(raw,pin,framed);rows=[]
            for i,segment in enumerate(audit['segments']):
                evidence=[{'pointer':f'/transcript/data/{i}/paragraphs/0/sentences/0/text',
                           'quote':doc['transcript']['data'][i]['paragraphs'][0]['sentences'][0]['text']}]
                rows.append({'statement_number':segment['statement_number'],'json_pointer':segment['json_pointer'],
                    'text_sha256':segment['text_sha256'],'locator_id':segment['locator_id'],
                    'review_state':'assistant_provisional','capacity':('collective' if group else 'national_candidate') if i==0 else 'procedural',
                    'attribution_evidence':evidence,'policy_matches':[{'policy_id':'humanitarian_access','context_id':None,
                    'proposed_stance':'support','discourse_labels':['requested_action'],'evidence':evidence,'comparison_eligible':False}] if i==0 else [],
                    'speech_boundary':'unverified'})
            self.review_inputs[mid]=rows

    def build(self,**changes):
        return C.build_cohort_coverage(self.store,changes.get('frame',self.frame),
            changes.get('artifacts',self.artifacts),changes.get('review_inputs',self.review_inputs))

    def row(self,result,mid=None):return next(r for r in result['meetings'] if r['meeting_id']==(mid or self.mid))

    def snapshot(self):
        return {name:[tuple(r) for r in self.store.db.execute('SELECT * FROM '+name+' ORDER BY 1,2')]
                for name in ('sources','source_revisions','artifacts','dependencies','evidence')}

    def test_missing_artifacts_preserve_full_declared_roster_not_archive_zeroes(self):
        result=self.build()
        self.assertEqual(2,result['summary']['eligible_meetings']);self.assertEqual(2,len(result['meetings']))
        self.assertTrue(all(not any(r['stages'].values()) for r in result['meetings']))
        self.assertEqual('unknown',result['archive_completeness'])
        sc=next(r for r in result['body_coverage'] if r['body']=='SC')
        self.assertEqual('not_in_declared_cohort',sc['status'])
        self.assertEqual('no_accepted_comparable_evidence',result['us_reference']['status'])

    def test_valid_artifact_without_persisted_batch_has_distinct_audit_stage(self):
        self.add(self.mid,persist=False);row=self.row(self.build())
        self.assertTrue(row['stages']['artifact_supplied']);self.assertTrue(row['stages']['receipt_pinned'])
        self.assertTrue(row['stages']['format_audit_verified']);self.assertFalse(row['stages']['current_batch_validated'])
        self.assertFalse(row['stages']['complete_provisional_review_linkage'])

    def test_bad_raw_hash_differs_from_pinned_but_unsupported_format(self):
        self.add(self.mid,persist=False)
        self.artifacts[self.mid]['receipt']['sha256']='0'*64
        bad=self.row(self.build());self.assertFalse(bad['stages']['receipt_pinned'])
        raw=b'{"synthetic_unsupported":true}';pin=self.artifacts[self.mid]['receipt']
        pin.update(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw));self.artifacts[self.mid]['raw']=raw
        unsupported=self.row(self.build())
        self.assertTrue(unsupported['stages']['receipt_pinned']);self.assertFalse(unsupported['stages']['format_audit_verified'])
        self.assertTrue(bad['gaps']);self.assertTrue(unsupported['gaps'])

    def test_persisted_current_batch_without_reviews_is_not_complete_review(self):
        self.add(self.mid);row=self.row(self.build())
        self.assertTrue(row['stages']['current_batch_validated'])
        self.assertFalse(row['stages']['complete_provisional_review_linkage'])

    def test_complete_current_review_keeps_all_other_roster_gaps(self):
        self.add(self.mid,review=True);result=self.build();row=self.row(result)
        self.assertTrue(all(row['stages'].values()))
        self.assertFalse(self.row(result,self.committee)['stages']['artifact_supplied'])
        self.assertEqual(1,result['summary']['complete_provisional_review_linkage'])
        self.assertEqual(0,result['summary']['accepted_positions']);self.assertEqual(0,result['summary']['comparison_eligible'])

    def test_stale_review_does_not_destroy_valid_audit_or_batch_stages(self):
        self.add(self.mid,review=True);self.review_inputs[self.mid][0]['text_sha256']='0'*64
        row=self.row(self.build())
        self.assertTrue(row['stages']['format_audit_verified']);self.assertTrue(row['stages']['current_batch_validated'])
        self.assertFalse(row['stages']['complete_provisional_review_linkage'])

    def test_current_method_change_is_reported_as_batch_gap_not_old_fallback(self):
        self.add(self.mid,review=True);changed={**B._methods(),'transcripts_un_batch.py':'0'*64}
        with patch.object(B,'_methods',return_value=changed):result=self.build()
        row=self.row(result)
        self.assertTrue(row['stages']['format_audit_verified']);self.assertFalse(row['stages']['current_batch_validated'])
        self.assertFalse(row['stages']['complete_provisional_review_linkage'])

    def test_changed_valid_raw_cannot_reuse_prior_current_batch(self):
        self.add(self.mid,review=True)
        artifact=self.artifacts[self.mid];doc=json.loads(artifact['raw']);doc['metadata']['new_revision']=2
        artifact['raw']=json.dumps(doc).encode()
        artifact['receipt'].update(bytes=len(artifact['raw']),sha256=hashlib.sha256(artifact['raw']).hexdigest())
        row=self.row(self.build())
        self.assertTrue(row['stages']['receipt_pinned']);self.assertTrue(row['stages']['format_audit_verified'])
        self.assertFalse(row['stages']['current_batch_validated']);self.assertFalse(row['stages']['complete_provisional_review_linkage'])

    def test_receipt_role_mismatch_fails_pin_without_removing_meeting(self):
        self.add(self.mid,persist=False);self.artifacts[self.mid]['receipt']['source_role']='evaluation'
        result=self.build();self.assertEqual(2,len(result['meetings']))
        self.assertFalse(self.row(result)['stages']['receipt_pinned'])

    def test_canonical_committee_body_is_separate_from_plenary(self):
        self.add(self.committee);result=self.build();row=self.row(result,self.committee)
        self.assertEqual('GA_C3',row['body']);self.assertEqual('Third Committee',row['recorded_body'])
        body={r['body']:r for r in result['body_coverage']}
        self.assertEqual(1,body['GA']['eligible_meetings']);self.assertEqual(1,body['GA_C3']['eligible_meetings'])

    def test_multiple_meetings_with_same_country_never_add_country_weight(self):
        self.add(self.mid,review=True);self.add(self.committee,review=True)
        result=self.build();self.assertEqual(1,result['summary']['national_candidate_countries'])
        self.assertEqual(1,len(result['countries']))
        self.assertFalse(result['comparisons_eligible'])

    def test_collective_source_affiliation_is_not_a_country_candidate(self):
        self.add(self.mid,review=True,group='Synthetic group');result=self.build()
        self.assertEqual(0,result['summary']['national_candidate_countries']);self.assertFalse(result['countries'])
        self.assertEqual(1,len(result['groups']))

    def test_unsealed_or_duplicate_frame_and_out_of_cohort_inputs_rejected(self):
        frame=copy.deepcopy(self.frame);frame['sha256']='0'*64
        with self.assertRaises(ValueError):self.build(frame=frame)
        frame=copy.deepcopy(self.frame);frame['meetings'].append(copy.deepcopy(frame['meetings'][0]));frame=seal(frame)
        with self.assertRaises(ValueError):self.build(frame=frame)
        for field,value in [('artifacts',{'sc/9999':{'raw':b'notopened','receipt':{}}}),('review_inputs',{'sc/9999':[]})]:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.build(**{field:value})

    def test_read_only_wording_free_and_deterministic_json_result(self):
        self.add(self.mid,review=True);before=self.snapshot();result=self.build()
        self.assertEqual(before,self.snapshot());self.assertEqual(result,self.build())
        self.assertEqual(result,json.loads(json.dumps(result)))
        encoded=json.dumps(result)
        self.assertNotIn('Nigeria calls for safe humanitarian access',encoded)
        self.assertNotIn('"raw":',encoded);self.assertNotIn('"quote":',encoded)

    def test_holdout_metadata_is_excluded_and_cannot_authorize_artifact_intake(self):
        frame=copy.deepcopy(self.frame)
        frame['meetings'].append({**frame['meetings'][0],'meeting_id':'sc/9999','date':'2026-10-05',
            'split':'holdout','source_url':'https://transcripts.un.org/en/sc/9999',
            'json_url':'https://transcripts.un.org/en/sc/9999.json'})
        frame=seal(frame);result=self.build(frame=frame)
        self.assertEqual(2,result['summary']['eligible_meetings'])
        self.assertNotIn('sc/9999',[m['meeting_id'] for m in result['meetings']])
        with self.assertRaises(ValueError):self.build(frame=frame,artifacts={'sc/9999':{'raw':b'never_audited','receipt':{}}})

    def test_current_batch_change_during_rollup_cannot_leave_current_stage_claim(self):
        self.add(self.mid)
        batch=B.get_current_batch(self.store,self.mid,self.artifacts[self.mid]['receipt']['source_url'])
        before=self.snapshot()
        with patch.object(C,'get_current_batch',side_effect=[batch,None]):
            with self.assertRaises(ValueError):self.build()
        self.assertEqual(before,self.snapshot())


if __name__=='__main__':unittest.main()
