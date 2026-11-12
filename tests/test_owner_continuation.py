import copy
import unittest
from test_review_intake import packet
from tools.continue_owner_review import remaining
from tools.build_private_reviewer import render
from un_transcript.models.runtime import analyze_segments
import json
from pathlib import Path

class ContinuationTests(unittest.TestCase):
    def test_completed_removed_without_mutating_original_or_review(self):
        d,r,b,i=packet();saved=copy.deepcopy(b)
        todo,flags=remaining(d,b,i)
        self.assertEqual([x['pair_id'] for x in todo['rows']],['p1'])
        self.assertEqual(b,saved);self.assertEqual(len(d['rows']),2)
        html=render(todo,{},i,total_examples=2)
        payload=json.loads(html.split('<script id="packet" type="application/json">')[1].split('</script>')[0])
        self.assertEqual(payload['total_examples'],2)
        self.assertEqual([x['pair_id'] for x in payload['draft']['rows']],['p1'])

    def test_tampering_duplicate_and_progress_exports_are_rejected(self):
        for kind in ('source','boolean_offset','duplicate','progress','packet'):
            d,r,b,i=packet()
            if kind=='source':b['rows'][0]['text']='changed'
            if kind=='boolean_offset':b['rows'][0]['start']=False
            if kind=='duplicate':b['rows']*=2;b['review_export']['confirmed_examples']=2
            if kind=='progress':b['review_export']['kind']='progress'
            if kind=='packet':b['review_export']['packet']={**i,'manifest_sha256':'wrong'}
            with self.subTest(kind=kind),self.assertRaises(ValueError):remaining(d,b,i)

    def test_collective_conflict_preserves_owner_choice_and_removes_completed_row(self):
        d,r,b,i=packet();d['rows'][0]['capacity']='collective';b['rows'][0]['capacity']='collective'
        b['rows'][0]['national_attribution_valid']=True
        todo,flags=remaining(d,b,i)
        self.assertEqual(len(flags),1);self.assertTrue(b['rows'][0]['national_attribution_valid'])
        self.assertEqual(len(todo['rows']),1)

    def test_libya_candidate_needs_libya_specific_evidence(self):
        catalog=json.loads(Path('config/issues.json').read_text())
        for text,expected in [('We support the UN-facilitated political process in Syria.',False),
                              ('We support UNSMIL.',True),
                              ('We support the UN-facilitated Libyan political process.',True)]:
            out=analyze_segments([{'segment_id':'synthetic','revision_id':'synthetic','text':text}],catalog)
            self.assertEqual(any(x['issue_id']=='libya_un_mediation' for x in out['issue_candidates']),expected)
            self.assertEqual(out['predictions'],[])
