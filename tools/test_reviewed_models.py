import json, unittest
from pathlib import Path
from compare_reviewed_models import logistic, separate, labels

class ReviewedModelTests(unittest.TestCase):
    def setUp(self):self.p=json.loads((Path(__file__).resolve().parents[1]/'research/reviewed_comparison_v1.json').read_text())
    def test_unseen_text_does_not_fit_vocabulary(self):
        train=[dict(quote='artificial intelligence systems',binary_label=1),dict(quote='climate finance cooperation',binary_label=0)]
        m=logistic(train,self.p);before=dict(m.named_steps['tfidf'].vocabulary_)
        m.predict_proba(['heldoutonly novelword']);self.assertEqual(before,m.named_steps['tfidf'].vocabulary_);self.assertNotIn('heldoutonly',before)
    def test_unresolved_rejected(self):
        with self.assertRaises(ValueError):labels([dict(binary_label=None)])
    def test_country_overlap_rejected(self):
        with self.assertRaises(ValueError):separate([dict(iso3='AAA',text_sha256='a',event_date='2026-09-23')],[dict(iso3='AAA',text_sha256='b',event_date='2026-09-28')])
    def test_content_overlap_rejected(self):
        with self.assertRaises(ValueError):separate([dict(iso3='AAA',text_sha256='a',event_date='2026-09-23')],[dict(iso3='BBB',text_sha256='a',event_date='2026-09-28')])
    def test_date_overlap_rejected(self):
        with self.assertRaises(ValueError):separate([dict(iso3='AAA',text_sha256='a',event_date='2026-09-28')],[dict(iso3='BBB',text_sha256='b',event_date='2026-09-28')])
    def test_forward_split(self):separate([dict(iso3='AAA',text_sha256='a',event_date='2026-09-23')],[dict(iso3='BBB',text_sha256='b',event_date='2026-09-28')])

if __name__=='__main__':unittest.main()
