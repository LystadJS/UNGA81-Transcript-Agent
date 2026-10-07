"""Synthetic regression checks; no real-source human decisions are created."""
import copy, hashlib, unittest
from review import classify, role, validate_ledger, selections, SCHEMA


def source(text='Thank you. We support equal access to education and protection of human rights. '*15, **kwargs):
    r={'split':'development','id':'development#0','meeting_id':'development','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
       'raw_sha256':'a'*64,'source_url':'https://transcripts.un.org/en/development','json_pointer':'/transcript/data/0',
       'speaker_metadata':{'function':None},'genre':'General Assembly','affiliation_raw':'AA','country':'A','timestamps_flagged':False}
    r.update(kwargs);return r


def fixture():
    r=source();a=classify(r,None,None)
    c={'sha256':'c'*64,'source_bundle':{'sha256':'b'*64},'parents':[r],
       'passages':[{'id':'development#0@0:1','parent_id':r['id'],'exclusions':[],'text_sha256':r['text_sha256']} ]}
    l={'schema':SCHEMA,'corpus_sha256':c['sha256'],'source_bundle_sha256':'b'*64,'annotations':[a]}
    return c,l


class MachineReviewTests(unittest.TestCase):
    def test_provisional(self):
        a=classify(source(),None,None);self.assertFalse(a['human_confirmed']);self.assertEqual(a['extent'],'unknown');self.assertIsNone(a['speech_id'])
    def test_country_chair(self):
        a=classify(source('I give the floor to the next speaker. Thank you.',speaker_metadata={'function':'Chair'}),None,None)
        self.assertEqual(a['suggested_type'],'procedure');self.assertIn('country_metadata_not_national_policy_voice',a['flags'])
    def test_long_chair(self):self.assertEqual(classify(source(speaker_metadata={'function':'Chair'}),None,None)['suggested_type'],'mixed_speech_procedure')
    def test_journalist(self):self.assertEqual(classify(source(speaker_metadata={'function':'Journalist'}),None,None)['suggested_type'],'press_question')
    def test_reply(self):self.assertEqual(classify(source('I exercise my right of reply. '+source()['text']),None,None)['suggested_type'],'right_of_reply')
    def test_point_order(self):self.assertEqual(classify(source('We raise a point of order. '+source()['text']),None,None)['suggested_type'],'mixed_speech_procedure')
    def test_audio_marker(self):self.assertEqual(classify(source('[inaudible] '+source()['text']),None,None)['suggested_type'],'suspected_transcription_issue')
    def test_short(self):self.assertEqual(classify(source('Thank you.'),None,None)['suggested_type'],'uncertain')
    def test_unknown_affiliation(self):self.assertEqual(role(source(country=None,affiliation_raw='')),'unresolved_affiliation')
    def test_noncountry_not_unknown(self):self.assertEqual(role(source(country=None,affiliation_raw='NGO')),'other_recorded_affiliation')
    def test_rapporteur_not_country(self):self.assertEqual(role(source(speaker_metadata={'function':'Rapporteur'})),'recorded_official_role')
    def test_press_official(self):self.assertEqual(role(source(genre='Press Conferences')),'official_press_response')
    def test_no_auto_join(self):
        r=source();a=classify(r,r,None);self.assertIsNone(a['speech_id']);self.assertIn('adjacent_same_metadata_not_automatically_same_speech',a['flags'])
    def test_unicode_offsets(self):
        text='😀 é — I exercise my right of reply. '+source()['text'];a=classify(source(text),None,None)
        for e in a['evidence']:self.assertEqual(text[e['start']:e['end']],e['quote'])
    def test_no_complete_from_closing(self):self.assertEqual(classify(source(),None,None)['extent'],'unknown')
    def test_valid_ledger(self):c,l=fixture();validate_ledger(c,l)
    def reject(self,mutate):
        c,l=fixture();mutate(c,l)
        with self.assertRaises(ValueError):validate_ledger(c,l)
    def test_reject_holdout_corpus(self):self.reject(lambda c,l:c['parents'][0].update(split='holdout'))
    def test_reject_human_schema(self):self.reject(lambda c,l:l.update(schema='un.corpus-boundary-review.v1'))
    def test_reject_source_hash(self):self.reject(lambda c,l:l.update(source_bundle_sha256='d'*64))
    def test_reject_corpus_hash(self):self.reject(lambda c,l:l.update(corpus_sha256='d'*64))
    def test_reject_human_confirmation(self):self.reject(lambda c,l:l['annotations'][0].update(human_confirmed=True))
    def test_reject_human_actor(self):self.reject(lambda c,l:l['annotations'][0].update(actor_kind='human'))
    def test_reject_complete_extent(self):self.reject(lambda c,l:l['annotations'][0].update(extent='complete'))
    def test_reject_speech_id(self):self.reject(lambda c,l:l['annotations'][0].update(speech_id='fake'))
    def test_reject_text_hash(self):self.reject(lambda c,l:l['annotations'][0].update(text_sha256='d'*64))
    def test_reject_raw_hash(self):self.reject(lambda c,l:l['annotations'][0].update(raw_sha256='d'*64))
    def test_reject_meeting(self):self.reject(lambda c,l:l['annotations'][0].update(meeting_id='holdout'))
    def test_reject_source_url(self):self.reject(lambda c,l:l['annotations'][0].update(source_url='https://example.com'))
    def test_reject_pointer(self):self.reject(lambda c,l:l['annotations'][0].update(json_pointer='/wrong'))
    def test_reject_missing(self):self.reject(lambda c,l:l.update(annotations=[]))
    def test_reject_duplicate(self):self.reject(lambda c,l:l['annotations'].append(copy.deepcopy(l['annotations'][0])))
    def test_reject_type(self):self.reject(lambda c,l:l['annotations'][0].update(suggested_type='approved'))
    def test_reject_context(self):self.reject(lambda c,l:l['annotations'][0].update(previous_id='holdout#0'))
    def test_reject_quote(self):self.reject(lambda c,l:l['annotations'][0].update(evidence=[{'start':0,'end':2,'quote':'wrong'}]))
    def test_strict_subset(self):
        c,l=fixture();rs=selections(c,l);self.assertTrue(rs[0]['strict_eligible']);self.assertTrue(rs[0]['inclusive_eligible'])
    def test_procedure_excluded_not_deleted(self):
        c,l=fixture();l['annotations'][0]['suggested_type']='procedure';rs=selections(c,l)
        self.assertEqual(len(rs),1);self.assertFalse(rs[0]['strict_eligible']);self.assertTrue(rs[0]['baseline_eligible'])
    def test_inherited_exclusion(self):
        c,l=fixture();c['passages'][0]['exclusions']=['short_partition'];rs=selections(c,l)
        self.assertFalse(rs[0]['strict_eligible']);self.assertFalse(rs[0]['inclusive_eligible']);self.assertFalse(rs[0]['baseline_eligible'])
    def test_truncation_excluded_strict_only(self):
        c,l=fixture();l['annotations'][0]['flags'].append('possible_truncated_ending');rs=selections(c,l)
        self.assertFalse(rs[0]['strict_eligible']);self.assertTrue(rs[0]['inclusive_eligible'])
    def test_press_not_formal(self):
        c,l=fixture();l['annotations'][0]['actor_role']='official_press_response';self.assertFalse(selections(c,l)[0]['strict_eligible'])

if __name__=='__main__':unittest.main(verbosity=2)
