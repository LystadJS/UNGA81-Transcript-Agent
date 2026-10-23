import unittest
from .assessment import assess,CLASSES
class AssessmentTests(unittest.TestCase):
    def data(self):
        items=[];predictions=[]
        for k,stance in enumerate(CLASSES):
            label=dict(stance=stance,attribution="national",policy_id="humanitarian_access",context_id="sudan")
            items.append(dict(record_id=str(k),text_sha256="a"*64,source_id="s"+str(k),date="2024-01-01",split="test",annotation=label,review_state="owner_confirmed",owner_confirmation_id="SYNTHETIC-RECEIPT"))
            predictions.append(dict(record_id=str(k),text_sha256="a"*64,**label))
        return items,predictions
    def test_synthetic_cannot_promote(self):
        items,p=self.data();result=assess(items,p,minimum_per_class=1)
        self.assertEqual(result["status"],"withheld");self.assertIn("synthetic_not_promotable",result["failures"])
        self.assertFalse(result["promotion_applied"])
    def test_missing_and_abstention_count_as_errors(self):
        items,p=self.data();result=assess(items,p[1:],minimum_per_class=1)
        self.assertEqual(result["metrics"]["stance"]["accuracy"],.75)
        self.assertEqual(result["per_class"]["support"]["abstentions"],1)
    def test_receipts_and_source_leakage(self):
        items,p=self.data();items[0]["owner_confirmation_id"]="";items[1]["source_id"]="s2";items[1]["split"]="validation"
        result=assess(items,p,minimum_per_class=1)
        self.assertIn("unconfirmed_labels",result["failures"]);self.assertIn("source_split_leakage",result["failures"])
    def test_temporal_protocol_enforced(self):
        items,p=self.data();items[0]["date"]="2020-01-01"
        result=assess(items,p,minimum_per_class=1,split_protocol=dict(version="source-blocked-temporal-v1",train_end="2021-12-31",validation_end="2023-12-31"))
        self.assertIn("temporal_split_leakage",result["failures"])
    def test_duplicate_predictions_rejected(self):
        items,p=self.data()
        with self.assertRaises(ValueError):assess(items,p+[p[0]])
if __name__=="__main__":unittest.main()
