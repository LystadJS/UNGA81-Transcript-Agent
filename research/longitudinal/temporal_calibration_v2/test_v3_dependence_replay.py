"""Independent exact-head development replay: numerical evidence, never holdout.

Counts are checked with both panel and method denominators. Monte Carlo
performance is NOT turned into an acceptance threshold or real-fit permission.
"""
import unittest
import json
from pathlib import Path
from collections import Counter
from .v3_dependence_study import run_development, GAMMA_WORLDS, COV_WORLDS, METHODS

class DevelopmentReplay(unittest.TestCase):
    def test_full_development_attempts_and_failures(self):
        result, ledger=run_development(60)
        self.assertEqual(result["gamma_panel_attempts"],420)
        self.assertEqual(result["gamma_method_attempts"],1680)
        self.assertEqual(result["covariance_panel_attempts"],480)
        self.assertEqual(result["gamma_method_attempts"],
            result["gamma_method_completed"]+result["gamma_method_refusals"])
        self.assertEqual(result["covariance_panel_attempts"],
            result["covariance_panel_completed"]+result["covariance_panel_refusals"])
        self.assertEqual(len(ledger),result["gamma_method_refusals"]+
                         result["covariance_panel_refusals"])
        self.assertEqual(result["gamma_scenarios"],len(GAMMA_WORLDS))
        self.assertEqual(result["covariance_scenarios"],len(COV_WORLDS))
        q0=[x for x in result["gamma"] if x["scenario"]=="no_audit_T16"]
        self.assertEqual(len(q0),len(METHODS))
        for x in q0:
            self.assertEqual(x["completed"],0)
            self.assertEqual(x["refused"],60)
        self.assertTrue(all(not x["statistical_acceptance"] for x in
                            result["gamma"]+result["covariance"]))
        self.assertFalse(result["v3_thresholds_frozen"])
        self.assertFalse(result["fitted_year_gamma_intervals_approved"])
        self.assertFalse(result["year_nugget_identified"])
        self.assertEqual(result["holdout_attempted"],0)
        self.assertEqual(result["real_original_sources_read"],0)
        self.assertFalse(result["real_fit_authorized"])
        ids={(x["type"],x["scenario"],x["replicate"],
              x.get("method",tuple(x.get("methods",[])))) for x in ledger}
        self.assertEqual(len(ids),len(ledger),"duplicate failure attempt ledger key")
        kinds=Counter(x["type"] for x in ledger)
        self.assertEqual(kinds["gamma_method"],result["gamma_method_refusals"])
        self.assertEqual(kinds["covariance_panel"],result["covariance_panel_refusals"])
        # Retain and independently match EVERY original failed replicate/method,
        # not merely aggregate failure categories or inflated denominators.
        manifest=json.loads((Path(__file__).resolve().parent /
                             "v3_development_failure_masks.json").read_text())
        self.assertEqual(manifest["total_failed_method_attempts"],len(ledger))
        self.assertEqual(manifest["holdout_attempted"],0)
        label=manifest["reason_labels"]
        expected=set()
        for case,reason,mask in manifest["gamma"]:
            self.assertLess(int(mask,16),1<<60)
            for method in manifest["gamma_methods"]:
                for rep in range(60):
                    if int(mask,16)&(1<<rep):
                        expected.add(("gamma_method",case,method,rep,label[reason]))
        for case,reason,mask in manifest["covariance"]:
            self.assertLess(int(mask,16),1<<60)
            for rep in range(60):
                if int(mask,16)&(1<<rep):
                    expected.add(("covariance_panel",case,
                                  "within_era_quasi_moment",rep,label[reason]))
        actual={(x["type"],x["scenario"],
                 x["method"] if "method" in x else x["methods"][0],
                 x["replicate"],x["reason"]) for x in ledger}
        self.assertEqual(len(actual),len(ledger),"duplicate failed method record")
        self.assertEqual(actual,expected,"synthetic failure masks differ from replay")

if __name__=="__main__":
    unittest.main()
