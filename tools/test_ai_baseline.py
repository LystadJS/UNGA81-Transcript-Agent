import json,unittest
from pathlib import Path
from evaluate_ai_baseline import metrics,predict

class BaselineTests(unittest.TestCase):
    def setUp(self):self.spec=json.loads((Path(__file__).resolve().parents[1]/'research/ai_baseline_v1.json').read_text())
    def test_positive(self):self.assertEqual(predict('Governance of Artificial Intelligence',self.spec),1)
    def test_boundaries(self):self.assertEqual(predict('Aid for digital transformation',self.spec),0)
    def test_acronym(self):self.assertEqual(predict('AI risks',self.spec),1)
    def test_matrix(self):
        m=metrics([1,1,0,0],[1,0,1,0]);self.assertEqual([m[k] for k in ['true_positive','false_positive','false_negative','true_negative']],[1,1,1,1]);self.assertEqual(m['f1'],.5)
    def test_undefined_precision(self):self.assertIsNone(metrics([1,0],[0,0])['precision'])
    def test_no_positive_truth(self):self.assertIsNone(metrics([0,0],[0,1])['recall'])
    def test_misalignment(self):
        with self.assertRaises(ValueError):metrics([1],[1,0])
    def test_unresolved(self):
        with self.assertRaises(ValueError):metrics([None],[0])

if __name__=='__main__':unittest.main()
