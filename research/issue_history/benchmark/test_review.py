import unittest
from .review import prepare,confirm,temporal_splits
class ReviewTests(unittest.TestCase):
    def test_source_split_and_no_fake_gold(self):
        row=dict(id="source#1",text_sha256="a"*64,date="2024-01-01",source_url="https://transcripts.un.org/en/source")
        packet=prepare([row,{**row,"id":"source#2"},row])
        self.assertEqual(len(packet["items"]),2)
        self.assertEqual(len({x["split"] for x in packet["items"]}),1)
        self.assertEqual(packet["human_confirmed_count"],0)
        self.assertTrue(all(x["annotation"] is None for x in packet["items"]))
        with self.assertRaises(ValueError): confirm(packet["items"][0],{},"")
    def test_temporal_sources_do_not_leak(self):
        records=[dict(id="same#1",date="2020-01-01"),dict(id="same#2",date="2024-01-01"),dict(id="new#1",date="2025-01-01")]
        split=temporal_splits(records,"2021-12-31","2023-12-31")
        self.assertEqual(split["sources"]["same"],"withheld_cross_boundary")
        self.assertEqual(split["sources"]["new"],"test")
if __name__=="__main__": unittest.main()
