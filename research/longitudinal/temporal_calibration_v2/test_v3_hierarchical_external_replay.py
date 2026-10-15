"""Independent full NEW development study replay; never a prospective holdout.

Run 12 disjoint synthetic draws per prespecified development cell and report
per-method counts, full failed fits, calibration-bound coverage *diagnostics*.
CI writes source-free aggregate and lossless failed-attempt bitmasks to logs.
"""
from __future__ import annotations
from collections import defaultdict
import hashlib
import json
import unittest

from .v3_hierarchical_external_study import (
    GAMMA_WORLDS,COV_WORLDS,GAMMA_METHODS,COV_METHODS,development_study)

REPETITIONS=12

def masks_from_failures(ledger):
    groups=defaultdict(int)
    for x in ledger:
        r=x["replicate"]
        if type(r) is not int or not 0<=r<REPETITIONS:
            raise ValueError("invalid independent development replicate index")
        key=(x["study"],x["scenario"],x["method"],x["reason"],
             x["expected_nonidentification"])
        bit=1<<r
        if groups[key]&bit:
            raise ValueError("duplicate method refusal identity")
        groups[key]|=bit
    return [{"study":k[0],"scenario":k[1],"method":k[2],
             "reason":k[3],"expected_nonidentification":k[4],
             "failed_replicates_hex":format(value,"x")}
            for k,value in sorted(groups.items())]

class IndependentHierarchicalExternalReplay(unittest.TestCase):
    def test_full_new_development_failure_preservation(self):
        report,ledger=development_study(REPETITIONS)
        masks=masks_from_failures(ledger)
        self.assertEqual(sum(int(x["failed_replicates_hex"],16).bit_count()
                             for x in masks),len(ledger))
        self.assertEqual(report["failure_ledger_entries"],len(ledger))
        self.assertEqual(report["gamma_method_attempted"],
              REPETITIONS*len(GAMMA_WORLDS)*len(GAMMA_METHODS))
        self.assertEqual(report["covariance_method_attempted"],
              REPETITIONS*len(COV_WORLDS)*len(COV_METHODS))
        self.assertEqual(report["gamma_method_attempted"],
              report["gamma_method_completed"]+report["gamma_method_refused"])
        self.assertEqual(report["covariance_method_attempted"],
              report["covariance_method_completed"]+report["covariance_method_refused"])
        self.assertEqual(len(ledger),report["gamma_method_refused"]+
                         report["covariance_method_refused"])
        self.assertEqual(report["v3_holdout_attempted"],0)
        self.assertEqual(report["real_original_source_files_read"],0)
        self.assertFalse(report["statistical_freeze_accepted"])
        for method in GAMMA_METHODS:
            failed=next(x for x in report["gamma_scenarios"]
                 if x["scenario"]=="missing_outcome_audit_T16" and x["method"]==method)
            self.assertEqual(failed["completed"],0)
            self.assertEqual(failed["refused"],REPETITIONS)
        for method in COV_METHODS:
            for case in ("shifted_external_population_T16",
                         "dependent_external_worlds_T16"):
                row=next(x for x in report["covariance_scenarios"] if
                        x["scenario"]==case and x["method"]==method)
                self.assertEqual(row["completed"],0)
                self.assertEqual(row["refused"],REPETITIONS)
        canonical=hashlib.sha256(json.dumps(ledger,sort_keys=True,
                               separators=(",",":")).encode()).hexdigest()
        aggregate={
            "schema":"un.w4.v3.hierarchical-external-development-replay.v1",
            "repetitions":REPETITIONS,
            "gamma_attempted":report["gamma_method_attempted"],
            "gamma_completed":report["gamma_method_completed"],
            "gamma_refused":report["gamma_method_refused"],
            "cov_attempted":report["covariance_method_attempted"],
            "cov_completed":report["covariance_method_completed"],
            "cov_refused":report["covariance_method_refused"],
            "failure_count":len(ledger),
            "failure_canonical_sha256":canonical,
            "gamma_scenarios":report["gamma_scenarios"],
            "covariance_scenarios":report["covariance_scenarios"],
            "v3_holdout_attempted":0,
            "statistical_freeze_accepted":False,
            "empirical_fit_authorized":False
        }
        print("V3_HIERARCHICAL_DEV_AGGREGATE="+json.dumps(
            aggregate,sort_keys=True,separators=(",",":")))
        print("V3_HIERARCHICAL_DEV_FAILURE_MASKS="+json.dumps(
            masks,sort_keys=True,separators=(",",":")))

if __name__=="__main__":
    unittest.main()
