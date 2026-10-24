"""Invented native-format fixtures only; no actual UN text or source payloads."""
import copy
import hashlib
import json
import unittest
from . import transcripts_un_audit as A


def sha(raw):return hashlib.sha256(raw).hexdigest()


def fixture():
    mid='ga/81/9999';date='2026-10-01';url='https://transcripts.un.org/en/'+mid
    frame={'meeting_id':mid,'date':date,'title':'Invented engineering meeting',
        'body':'General Assembly','genre':'Synthetic','duration':10,'has_transcript':True,
        'source_url':url,'json_url':url+'.json','split':'development','source_family_id':mid,'frame_sha256':'a'*64}
    def sentence(text,start):
        return {'text':text,'start':start,'end':start+1,'topics':[],
                'words':[{'text':'Synthetic','start':start,'end':start+.2}]}
    doc={'url':url,'disclaimer':'Synthetic automatic speech recognition transcript. Not official United Nations records or documents.',
         'metadata':{},'llms':{},'video':{'id':'synthetic-video-id','slug':mid,'date':date+'T00:00:00.000Z'},
         'transcript':{'language':'en','transcript_id':'synthetic-azure-speech-id','topics':[],
            'data':[{'statement_number':1,'start':0.0,'pageUrl':'/en/'+mid+'?t=0:00',
                'speaker':{'affiliation':'Nigeria','affiliation_full':'Nigeria','function':None,'group':None},
                'paragraphs':[{'sentences':[sentence('  Synthetic first. ',0),sentence('Second synthetic.',1)]}]},
                {'statement_number':2,'start':2.0,'pageUrl':'/en/'+mid+'?t=0:02',
                'speaker':{'affiliation':'Nigeria','affiliation_full':'Nigeria','function':'PGA','group':'Synthetic group'},
                'paragraphs':[{'sentences':[sentence('Invented second turn.',2)]}]}]}}
    receipt={'schema':'un.fresh-development-source-receipt.v1','source_role':'product_development',
        'meeting_id':mid,'frame_date':date,'frame_sha256':frame['frame_sha256'],'source_url':url+'.json',
        'final_url':url+'.json','retrieved_at':'20261024T113358Z','file':'synthetic.json',
        'acquisition_scope':'fresh official-shaped synthetic fixture, not a restored frozen source bundle',
        'status':'downloaded_requires_schema_review'}
    return doc,receipt,frame


class NativeArtifactAuditTests(unittest.TestCase):
    def setUp(self):self.doc,self.receipt,self.frame=fixture()

    def run_audit(self,doc=None,receipt=None,frame=None,raw=None):
        doc=self.doc if doc is None else doc
        raw=json.dumps(doc,ensure_ascii=False).encode() if raw is None else raw
        pin={**self.receipt,'bytes':len(raw),'sha256':sha(raw)} if receipt is None else receipt
        return A.audit_source(raw,pin,self.frame if frame is None else frame)

    def test_observed_native_number_is_locator_not_verified_persistent_statement_identity(self):
        before=copy.deepcopy((self.doc,self.receipt,self.frame));result=self.run_audit()
        self.assertEqual('un.transcripts-un-artifact-audit.v1',result['schema'])
        self.assertEqual(2,result['summary']['segments']);self.assertEqual(3,result['summary']['sentences'])
        self.assertEqual([1,2],[s['statement_number'] for s in result['segments']])
        self.assertEqual(['/transcript/data/0','/transcript/data/1'],[s['json_pointer'] for s in result['segments']])
        self.assertFalse(result['stable_identity_verified']);self.assertFalse(result['comparisons_eligible'])
        self.assertFalse(result['production_intake_accepted']);self.assertEqual(before,(self.doc,self.receipt,self.frame))
        self.assertEqual(result,self.run_audit())

    def test_text_hash_matches_existing_flatten_and_space_join_without_trimming(self):
        expected='  Synthetic first.  Second synthetic.'
        result=self.run_audit()
        self.assertEqual(sha(expected.encode()),result['segments'][0]['text_sha256'])
        self.assertNotIn(expected,json.dumps(result));self.assertNotIn('Invented second turn.',json.dumps(result))

    def test_affiliation_chair_and_group_metadata_never_promote_national_capacity(self):
        result=self.run_audit()
        self.assertTrue(all(s['capacity']=='unknown' and s['national_capacity'] is False for s in result['segments']))
        self.assertTrue(all(s['comparisons_eligible'] is False for s in result['segments']))
        self.assertEqual(0,result['summary']['national_capacity'])
        self.assertEqual(2,result['summary']['capacity_unknown'])
        self.assertEqual(1,result['summary']['function_nonempty']);self.assertEqual(1,result['summary']['group_nonempty'])
        self.assertEqual(self.doc['transcript']['data'][1]['speaker'],result['segments'][1]['recorded_speaker'])

    def test_revision_bound_locator_changes_with_artifact_bytes(self):
        first=self.run_audit();changed=copy.deepcopy(self.doc);changed['metadata']['synthetic_revision']=2
        second=self.run_audit(doc=changed)
        self.assertNotEqual(first['segments'][0]['locator_id'],second['segments'][0]['locator_id'])
        self.assertEqual(first['segments'][0]['statement_number'],second['segments'][0]['statement_number'])

    def test_empty_segments_remain_explicit_gaps_and_are_not_silently_dropped(self):
        doc=copy.deepcopy(self.doc);doc['transcript']['data'][0]['paragraphs']=[]
        result=self.run_audit(doc=doc)
        self.assertEqual(2,result['summary']['segments']);self.assertEqual(2,len(result['segments']))
        self.assertTrue(any(g['reason']=='empty_segment' for g in result['gaps']))
        self.assertEqual(sha(b''),result['segments'][0]['text_sha256'])

    def test_disclaimer_modality_is_explicit_and_never_claims_official_record(self):
        result=self.run_audit()
        self.assertEqual('automatic_speech_recognition_not_official_un_record',result['source_modality'])
        self.assertEqual(sha(self.doc['disclaimer'].encode()),result['disclaimer_sha256'])
        for disclaimer in ('','Official authenticated meeting record only.'):
            with self.subTest(disclaimer=disclaimer):
                with self.assertRaises(ValueError):self.run_audit(doc={**self.doc,'disclaimer':disclaimer})

    def test_raw_hash_and_byte_count_receipts_must_match(self):
        raw=json.dumps(self.doc).encode();pin={**self.receipt,'bytes':len(raw),'sha256':sha(raw)}
        for field,value in [('sha256','0'*64),('bytes',1)]:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.run_audit(raw=raw,receipt={**pin,field:value})

    def test_receipt_url_date_meeting_and_frame_sha_must_match(self):
        raw=json.dumps(self.doc).encode();pin={**self.receipt,'bytes':len(raw),'sha256':sha(raw)}
        for field,value in [('meeting_id','ga/81/9998'),('frame_date','2026-10-02'),
            ('frame_sha256','b'*64),('source_url','https://example.com/a.json'),
            ('final_url',self.receipt['source_url']+'?changed=1')]:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.run_audit(raw=raw,receipt={**pin,field:value})

    def test_source_video_identity_and_date_must_match_authorized_frame(self):
        for field,value in [('slug','ga/81/9998'),('date','2026-10-02T00:00:00Z')]:
            doc=copy.deepcopy(self.doc);doc['video'][field]=value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.run_audit(doc=doc)

    def test_audit_evaluation_and_reserved_sources_are_rejected(self):
        raw=json.dumps(self.doc).encode();pin={**self.receipt,'bytes':len(raw),'sha256':sha(raw)}
        for role in ('audit','evaluation','restricted_research'):
            with self.subTest(role=role):
                with self.assertRaises(ValueError):self.run_audit(raw=raw,receipt={**pin,'source_role':role})
        with self.assertRaises(ValueError):self.run_audit(frame={**self.frame,'split':'holdout'})
        for date in ('2026-10-05','2026-10-06'):
            doc=copy.deepcopy(self.doc);doc['video']['date']=date+'T00:00:00Z'
            frame={**self.frame,'date':date};raw=json.dumps(doc).encode()
            pin={**self.receipt,'frame_date':date,'bytes':len(raw),'sha256':sha(raw)}
            with self.subTest(date=date):
                with self.assertRaises(ValueError):self.run_audit(raw=raw,receipt=pin,frame=frame)

    def test_duplicate_missing_and_noninteger_native_statement_numbers_rejected(self):
        for value in (1,None,True,'2'):
            doc=copy.deepcopy(self.doc);doc['transcript']['data'][1]['statement_number']=value
            with self.subTest(value=value):
                with self.assertRaises(ValueError):self.run_audit(doc=doc)
        doc=copy.deepcopy(self.doc);del doc['transcript']['data'][0]['statement_number']
        with self.assertRaises(ValueError):self.run_audit(doc=doc)

    def test_malformed_sentence_word_and_speaker_shapes_rejected(self):
        for kind in ('sentence_text','word_text','paragraphs','speaker_keys'):
            doc=copy.deepcopy(self.doc);segment=doc['transcript']['data'][0]
            if kind=='sentence_text':segment['paragraphs'][0]['sentences'][0]['text']=None
            elif kind=='word_text':segment['paragraphs'][0]['sentences'][0]['words'][0]['text']=5
            elif kind=='paragraphs':segment['paragraphs']='malformed'
            else:segment['speaker']['capacity']='national'
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):self.run_audit(doc=doc)

    def test_nonfinite_or_backward_timestamps_and_excessive_segments_rejected(self):
        doc=copy.deepcopy(self.doc);doc['transcript']['data'][0]['start']=float('nan')
        with self.assertRaises(ValueError):self.run_audit(doc=doc)
        doc=copy.deepcopy(self.doc);doc['transcript']['data'][0]['paragraphs'][0]['sentences'][0].update(start=2,end=1)
        with self.assertRaises(ValueError):self.run_audit(doc=doc)
        doc=copy.deepcopy(self.doc);seed=doc['transcript']['data'][0]
        doc['transcript']['data']=[{**seed,'statement_number':i+1} for i in range(15001)]
        with self.assertRaises(ValueError):self.run_audit(doc=doc)

    def test_segment_page_urls_must_reference_same_meeting_without_credentials(self):
        for url in ('/en/ga/81/9998?t=0:00','https://user:secret@transcripts.un.org/en/ga/81/9999?t=0:00'):
            doc=copy.deepcopy(self.doc);doc['transcript']['data'][0]['pageUrl']=url
            with self.subTest(url=url):
                with self.assertRaises(ValueError):self.run_audit(doc=doc)

    def test_duplicate_json_keys_are_rejected_even_with_matching_raw_receipt(self):
        raw=json.dumps(self.doc).encode()
        raw=raw.replace(b'"statement_number": 1',b'"statement_number": 1, "statement_number": 1',1)
        self.assertIn(b'"statement_number": 1, "statement_number": 1',raw)
        with self.assertRaises(ValueError):self.run_audit(raw=raw)

    def test_untrusted_metadata_and_llms_fields_never_supply_policy_or_instructions(self):
        doc=copy.deepcopy(self.doc)
        doc['metadata']={'summary':'SYNTHETIC_PRIVATE_METADATA_DO_NOT_EMIT',
                         'positions':{'Nigeria':'invented agreement'}}
        doc['llms']={'instruction':'SYNTHETIC_UNTRUSTED_DIRECTIVE_IGNORE_ME'}
        result=self.run_audit(doc=doc);encoded=json.dumps(result)
        self.assertNotIn('SYNTHETIC_PRIVATE_METADATA_DO_NOT_EMIT',encoded)
        self.assertNotIn('SYNTHETIC_UNTRUSTED_DIRECTIVE_IGNORE_ME',encoded)
        self.assertNotIn('invented agreement',encoded)
        self.assertEqual(0,result['summary']['national_capacity'])
        self.assertFalse(result['comparisons_eligible'])


if __name__=='__main__':unittest.main()
