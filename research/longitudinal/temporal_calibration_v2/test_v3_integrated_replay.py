"""Full independent NEW development replay: exact Markov likelihood vs sharp set.

All results source-free; every method/scenario/replicate refusal preserved.
Neither tests nor this suite can generate a v3 holdout or read v2 frozen data.
"""
from __future__ import annotations
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import unittest
from .v3_integrated_study import SCENARIOS,METHODS,run_development

REPETITIONS=12

def compact_failures(ledger):
    groups=defaultdict(int)
    for item in ledger:
        rep=item["replicate"]
        if type(rep) is not int or not 0<=rep<REPETITIONS:
            raise ValueError("invalid new development repetition")
        key=(item["scenario"],item["method"],item["reason"],
             item["expected_refusal"])
        if groups[key] & (1<<rep):
            raise ValueError("duplicate failed fit identity")
        groups[key]|=1<<rep
    return [{"scenario":k[0],"method":k[1],"reason":k[2],
             "expected_refusal":k[3],"replicate_mask_hex":format(v,"x")}
            for k,v in sorted(groups.items())]

class IndependentIntegratedAndPartialReplay(unittest.TestCase):
    def test_full_development_replay_all_refusals(self):
        report,failed=run_development(REPETITIONS)
        masks=compact_failures(failed)
        self.assertEqual(report["attempted_method_fits"],
                REPETITIONS*len(SCENARIOS)*len(METHODS))
        self.assertEqual(report["attempted_method_fits"],
                report["completed_method_fits"]+report["refused_method_fits"])
        self.assertEqual(len(failed),report["failure_ledger_count"])
        self.assertEqual(len(failed),sum(int(x["replicate_mask_hex"],16).bit_count()
                                       for x in masks))
        self.assertEqual(report["v3_holdout_attempted"],0)
        self.assertEqual(report["original_source_bytes_read"],0)
        self.assertFalse(report["statistical_freeze_accepted"])
        self.assertFalse(report["historical_fit_authorized"])
        for case in ("weak_audit_T16","no_audit_T16","actor_effect_stress_T16"):
            rows=[x for x in report["scenarios"] if x["scenario"]==case]
            self.assertEqual(len(rows),len(METHODS))
            self.assertTrue(all(x["completed"]==0 and x["refused"]==REPETITIONS for x in rows))
        correct=[x for x in report["scenarios"] if x["scenario"]=="correlated_states_T16"]
        for row in correct:
            self.assertEqual(row["completed"],REPETITIONS)
            self.assertFalse(row["bootstrap_or_Fisher_information_interval_approved"])
        numerical=[x for x in correct if x["method"]=="integrated_two_state_year_markov"][0]
        partial=[x for x in correct if x["method"]=="formal_gamma_set_or_no_fit"][0]
        self.assertIsNotNone(numerical["gamma_rmse_completed"])
        self.assertGreater(partial["median_gamma_set_width"],1)
        self.assertTrue(0<=partial["partial_gamma_hit_completed"]<=1)
        self.assertEqual(report["attempted_method_fits"],192)
        # An ordinary same-runtime replay hash excludes all original source rows.
        checksum=hashlib.sha256(json.dumps(failed,sort_keys=True,
                              separators=(",",":")).encode()).hexdigest()
        core={**report,"full_failures_sha256":checksum,
              "failed_method_replicate_masks":masks,
              "external_human_statistical_review":"NOT_OBTAINED",
              "v3_holdout_attempted":0,"statistical_freeze_accepted":False}
        path=Path(__file__).resolve().parent/"v3_integrated_development_receipt.json"
        if path.exists():
            prior=json.loads(path.read_text())
            self.assertEqual(prior["attempted_method_fits"],report["attempted_method_fits"])
            self.assertEqual(prior["refused_method_fits"],len(failed))
            self.assertEqual(prior["failed_method_replicate_masks"],masks)
            self.assertEqual(prior["full_failures_sha256"],checksum)
            self.assertFalse(prior["statistical_freeze_accepted"])
            self.assertEqual(prior["v3_holdout_attempted"],0)
        print("V3_INTEGRATED_DEVELOPMENT_REPLAY="+json.dumps(core,sort_keys=True,
                  separators=(",",":")))

if __name__=="__main__":
    unittest.main()
