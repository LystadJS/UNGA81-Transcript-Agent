"""Exact-head full *development* replay and compact failed-fit evidence.

No holdout or historical paths. Every refused method and bootstrap refit has a
recoverable (scenario, method, world replicate, bootstrap replicate, reason) key.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import hashlib
import json
import unittest
from .v3_finite_year_study import run_development,GAMMA_WORLDS,COV_WORLDS

REPETITIONS=12
BOOTSTRAP=20

def failure_masks(ledger):
    """Lossless bitset representation across development world x bootstrap attempts.

    Bit index r*(BOOTSTRAP+1)+(b+1) for bootstrap attempt b,
    or bit r*(BOOTSTRAP+1) for top-level method refusals.
    """
    groups=defaultdict(int)
    for f in ledger:
        r=f["replicate"];b=f.get("bootstrap_rep")
        if type(r) is not int or not 0<=r<REPETITIONS:
            raise ValueError("invalid development replicate")
        if b is not None and (type(b) is not int or not 0<=b<BOOTSTRAP):
            raise ValueError("invalid bootstrap replicate")
        key=(f["study"],f["scenario"],f["method"],f["reason"])
        offset=r*(BOOTSTRAP+1)+(0 if b is None else b+1)
        bit=1<<offset
        if groups[key]&bit:
            raise ValueError("duplicate failed method/bootstrap record")
        groups[key]|=bit
    return [{"study":k[0],"scenario":k[1],"method":k[2],
             "reason":k[3],"mask_hex":format(v,"x")}
            for k,v in sorted(groups.items())]

class FullIndependentFiniteYearReplay(unittest.TestCase):
    def test_full_development_replay_with_every_failure_retained(self):
        report,ledger=run_development(REPETITIONS,BOOTSTRAP)
        masks=failure_masks(ledger)
        recovered=sum(int(x["mask_hex"],16).bit_count() for x in masks)
        self.assertEqual(recovered,len(ledger))
        self.assertEqual(report["failure_ledger_entries"],len(ledger))
        self.assertEqual(report["gamma_method_attempted"],len(GAMMA_WORLDS)*3*REPETITIONS)
        self.assertEqual(report["covariance_method_attempted"],len(COV_WORLDS)*2*REPETITIONS)
        self.assertEqual(report["gamma_method_attempted"],
                         report["gamma_method_completed"]+report["gamma_method_refused"])
        self.assertEqual(report["gamma_bootstrap_attempted"],
                         report["gamma_bootstrap_completed"]+report["gamma_bootstrap_failed"])
        self.assertEqual(report["failure_ledger_entries"],
                         report["gamma_method_refused"]+report["gamma_bootstrap_failed"]+
                         report["covariance_method_refused"])
        self.assertEqual(report["v3_holdout_attempted"],0)
        self.assertFalse(report["statistical_acceptance"])
        self.assertEqual(report["real_original_sources_opened"],0)
        digest=hashlib.sha256(json.dumps(ledger,sort_keys=True,
                                         separators=(",",":")).encode()).hexdigest()
        core={"schema":"un.w4.v3.finite-year-development-replay.v1",
              "world_repetitions":REPETITIONS,"bootstrap_per_attempt":BOOTSTRAP,
              "gamma_methods_attempted":report["gamma_method_attempted"],
              "gamma_methods_completed":report["gamma_method_completed"],
              "gamma_methods_refused":report["gamma_method_refused"],
              "gamma_bootstrap_attempted":report["gamma_bootstrap_attempted"],
              "gamma_bootstrap_completed":report["gamma_bootstrap_completed"],
              "gamma_bootstrap_failed":report["gamma_bootstrap_failed"],
              "cov_methods_attempted":report["covariance_method_attempted"],
              "cov_methods_completed":report["covariance_method_completed"],
              "cov_methods_refused":report["covariance_method_refused"],
              "failure_ledger_count":len(ledger),
              "failure_ledger_canonical_sha256":digest,
              "gamma":report["gamma_scenarios"],
              "covariance":report["covariance_scenarios"],
              "holdout_attempted":0,"statistical_acceptance":False}
        # Output a source-free aggregate and lossless failure bitsets in CI logs,
        # not hidden original documents or full raw synthetic source rows.
        print("V3_FINITE_YEAR_REPLAY_AGGREGATE="+json.dumps(core,sort_keys=True,separators=(",",":")))
        print("V3_FINITE_YEAR_REPLAY_FAILURE_MASKS="+json.dumps(masks,sort_keys=True,separators=(",",":")))

if __name__=="__main__":
    unittest.main()
