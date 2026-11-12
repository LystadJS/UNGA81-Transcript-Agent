"""Synthetic-only source lineage negative controls; no original documents read."""
import unittest
from source_adapter import audit_manifest, IncompatibleCohort

H = 'a' * 64

def fixture():
    return {
        'schema': 'un.historical-source-audit.v1',
        'frames': [{'id':'frame','year':2015,'meeting_design':'synthetic','genre':'debate',
            'language':'en','translation_modality':'unknown','roster_definition':'synthetic',
            'selection_design':'sampled'}],
        'receipts': [{'document_id':'doc','meeting_id':'PV','year':2015,
            'available':True,'transcript_available':True,'sha256':H,'text_sha256':H}],
        'observations': [{'id':'obs1','frame_id':'frame','document_id':'doc','meeting_id':'PV',
            'speech_id':'speech1','country':'SYN','year':2015,'attribution':'unverified',
            'outcome_available':True,'inclusion_probability':2/3,
            'speech_length':100,'text_sha256':H}]
    }

class SourceIdentityRegressions(unittest.TestCase):
    def test_valid_synthetic_fixture(self):
        self.assertEqual(audit_manifest(fixture())['frames'][0]['metadata_eligible'], 1)
    def test_distinct_row_id_cannot_duplicate_speech(self):
        data=fixture()
        second=dict(data['observations'][0],id='obs2')
        data['observations'].append(second)
        with self.assertRaisesRegex(IncompatibleCohort,'duplicate original meeting/speech lineage'):
            audit_manifest(data)
    def test_two_distinct_speeches_same_original_meeting_allowed(self):
        data=fixture()
        data['observations'].append(dict(data['observations'][0],id='obs2',speech_id='speech2'))
        self.assertEqual(audit_manifest(data)['frames'][0]['metadata_eligible'], 2)
    def test_boolean_year_rejected_for_frame(self):
        data=fixture()
        data['frames'][0]['year']=True
        with self.assertRaises(IncompatibleCohort):audit_manifest(data)
    def test_boolean_year_rejected_for_receipt(self):
        data=fixture()
        data['receipts'][0]['year']=True
        with self.assertRaises(IncompatibleCohort):audit_manifest(data)
    def test_boolean_year_rejected_for_observation(self):
        data=fixture()
        data['observations'][0]['year']=True
        with self.assertRaises(IncompatibleCohort):audit_manifest(data)
    def test_boolean_speech_length_rejected(self):
        data=fixture()
        data['observations'][0]['speech_length']=True
        with self.assertRaises(IncompatibleCohort):audit_manifest(data)

if __name__ == '__main__':
    unittest.main()
