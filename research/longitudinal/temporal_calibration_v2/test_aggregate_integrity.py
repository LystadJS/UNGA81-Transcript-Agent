"""Read-only, synthetic-only independent reconciliation of committed holdout summaries.

Never regenerates worlds, edits frozen thresholds, accesses source records or authorizes fits.
"""
from __future__ import annotations
import csv
import json
from collections import Counter
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
METHODS = {"iid_year", "ar1_constrained", "ar1_nugget_ridge"}
YEARS = {16, 24, 32}
MASKS = {"near_census", "stratified_2_of_3"}
WORLDS = {"iid_MAR", "AR1_MAR", "AR1_MNAR_audited",
          "AR1_MNAR_no_audit", "AR1_nugget_MNAR_audited"}

def check_receipts(summary, failures, records):
    """Raise ValueError on conflicting synthetic published accounting."""
    def require(test, message):
        if not test:
            raise ValueError(message)
    require(summary.get("phase") == "holdout", "not a holdout receipt")
    require(set(summary.get("methods", [])) == METHODS, "method mismatch")
    require(summary.get("scenarios") == 30, "scenario count mismatch")
    require(len(records) == 90, "expected 30 scenarios x 3 methods")
    require(summary.get("panels_attempted") == 7200, "attempt denominator")
    require(summary.get("synthetic_T16_candidate_families_passing") == [],
            "incorrect inference authorization")
    require(summary.get("statistical_acceptance") is False and
            summary.get("empirical_publication_eligible") is False and
            summary.get("new_real_2008_2023_model_fit") is False,
            "release gate violated")
    require(summary.get("unsafe_no_audit_fits") == 0, "unsafe unidentifiable fit")
    require(failures.get("schema") == "un.w4.temporal_calibration_v2.failure_accounting.v1",
            "failure schema mismatch")
    require(failures.get("outcomes_fabricated") is False and
            failures.get("source") == "synthetic only", "unsafe source claim")
    categories = failures.get("categories", {})
    require(all(type(n) is int and n >= 0 for n in categories.values()),
            "invalid failure category count")
    require(sum(categories.values()) == failures.get("failed_attempts"),
            "failure categories do not reconcile")
    require(failures["total_attempted"] == summary["panels_attempted"],
            "failure denominator mismatch")
    triples = set()
    by_method = {m: [] for m in METHODS}
    for r in records:
        try:
            key = (int(r["years"]), r["mask"], r["world"])
            method = r["method"]
            attempted = int(r["attempted"])
            completed = int(r["completed"])
            support = int(r["support_failures"])
            abstained = int(r["expected_no_audit_abstentions"])
            unsafe = int(r["unsafe_unidentified_fits"])
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError("malformed scenario table") from e
        require(key[0] in YEARS and key[1] in MASKS and key[2] in WORLDS
                and method in METHODS, "unexpected scenario")
        tag = (*key, method)
        require(tag not in triples, "duplicate scenario-method row")
        triples.add(tag)
        require(attempted == 240 and min(completed, support, abstained, unsafe) >= 0,
                "invalid attempt accounting")
        require(attempted == completed + support + abstained,
                "scenario attempted/completed/failed totals disagree")
        require(unsafe == 0, "unsafe fit in scenario")
        require(abstained == (240 if key[2] == "AR1_MNAR_no_audit" else 0),
                "incorrect nonidentification abstentions")
        require(r["statistical_acceptance"] == "False", "scenario unexpectedly accepted")
        by_method[method].append(r)
    require(len(triples) == 90, "missing scenario-method cross product")
    for method, rows in by_method.items():
        require(len(rows) == 30, "missing method scenarios")
        require(sum(int(r["attempted"]) for r in rows) == summary["panels_attempted"],
                "method attempted totals mismatch")
        require(sum(int(r["completed"]) for r in rows) == summary["panels_completed"],
                "method completed totals mismatch")
        require(sum(int(r["support_failures"]) for r in rows) == summary["unexpected_failures"],
                "support failures mismatch")
        require(sum(int(r["expected_no_audit_abstentions"]) for r in rows) ==
                summary["expected_no_audit_abstentions"], "abstention mismatch")
        coverage = sum(r["passes_coverage"] == "True" for r in rows)
        recovery = sum(r["passes_rho_recovery"] == "True" for r in rows)
        require(coverage == summary["pass_coverage_scenarios"][method],
                "coverage scenario total disagrees")
        require(recovery == summary["pass_recovery_scenarios"][method],
                "rho recovery scenario total disagrees")
        require(not any(r["statistical_acceptance"] == "True" for r in rows if
                        int(r["years"]) == 16), "T16 unexpectedly accepted")
    require(summary["panels_attempted"] ==
            summary["panels_completed"] + failures["failed_attempts"],
            "holdout failure count mismatch")
    require(summary["unexpected_failures"] ==
            failures["failed_attempts"] - categories.get("EXPECTED_NO_AUDIT_NONIDENTIFICATION", 0),
            "unexpected failure accounting mismatch")
    require(summary["expected_no_audit_abstentions"] ==
            categories.get("EXPECTED_NO_AUDIT_NONIDENTIFICATION", 0),
            "no-audit refusal count mismatch")
    return {"scenario_method_rows": len(records),
            "attempted_panels": summary["panels_attempted"],
            "completed_panels": summary["panels_completed"],
            "expected_abstentions": summary["expected_no_audit_abstentions"],
            "other_failures": summary["unexpected_failures"],
            "statistical_approval": False}

def read_committed():
    summary = json.loads((ROOT / "holdout_aggregate_v2.json").read_text())
    failures = json.loads((ROOT / "holdout_failure_counts_v2.json").read_text())
    with (ROOT / "holdout_scenarios_v2.csv").open(newline="") as handle:
        records = list(csv.DictReader(handle))
    return summary, failures, records

class AggregateIntegrityTests(unittest.TestCase):
    def test_committed_holdout_receipts_reconcile(self):
        s, f, r = read_committed()
        result = check_receipts(s, f, r)
        self.assertEqual(result["scenario_method_rows"], 90)
    def test_tampered_completed_total_fails(self):
        s, f, r = read_committed()
        s["panels_completed"] += 1
        with self.assertRaisesRegex(ValueError, "completed totals"):
            check_receipts(s, f, r)
    def test_duplicate_method_scenario_fails(self):
        s, f, r = read_committed()
        r[1] = dict(r[0])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            check_receipts(s, f, r)
    def test_unsafe_no_audit_fit_fails(self):
        s, f, r = read_committed()
        changed = next(x for x in r if x["world"] == "AR1_MNAR_no_audit")
        changed["expected_no_audit_abstentions"] = "239"
        changed["completed"] = "1"
        with self.assertRaisesRegex(ValueError, "nonidentification"):
            check_receipts(s, f, r)
    def test_false_coverage_pass_fails(self):
        s, f, r = read_committed()
        first = next(x for x in r if x["passes_coverage"] == "False")
        first["passes_coverage"] = "True"
        with self.assertRaisesRegex(ValueError, "coverage scenario"):
            check_receipts(s, f, r)
    def test_release_gate_tamper_fails(self):
        s, f, r = read_committed()
        s["empirical_publication_eligible"] = True
        with self.assertRaisesRegex(ValueError, "release gate"):
            check_receipts(s, f, r)

if __name__ == "__main__":
    unittest.main()
