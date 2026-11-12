import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('pilot_tool',Path(__file__).parents[1]/'tools/prepare_private_pilot.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class Packet(unittest.TestCase):
    def test_private_review_is_blank_and_test_separate(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            row={'segment_id':'s','pair_id':'p','text':'=unsafe','label':None,'status':None}
            for split,count in [('train',180),('calibration',60),('test',60)]:
                (root/(split+'-draft.json')).write_text(json.dumps({'rows':[row]*count}))
            counts=module.review_files(root,{'segments':[{'segment_id':'s','speaker':'Speaker','source_url':'https://transcripts.un.org/'}]})
            self.assertEqual(sum(counts.values()),300)
            self.assertFalse((root/'test-draft.json').exists())
            self.assertTrue((root/'sealed/test-draft.json').exists())
            import csv
            with (root/'review/train-review.csv').open(encoding='utf-8-sig') as stream:
                rows=list(csv.DictReader(stream))
            self.assertEqual(rows[0]['text'],"'=unsafe")
            self.assertEqual(rows[0]['owner_confirmed'],'')
            self.assertEqual(rows[0]['label'],'')
            self.assertEqual(rows[0]['speaker'],'Speaker')

    def test_short_sample_cannot_be_published_as_300(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'train-draft.json').write_text('{"rows":[]}')
            with self.assertRaisesRegex(ValueError,'Insufficient'):
                module.review_files(root,{'segments':[]})
