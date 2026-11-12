"""Independent diagnostic of temporal covariance preservation; synthetic only.

Not a null calibration and not the 99-draw locked holdout. Uses PUBLIC study.py
interface, no oracle generating parameter is supplied to the estimator.
"""
import hashlib
import json
import math
import statistics
from collections import defaultdict

from study import world, estimate, bootstrap, seeded


def lag_one(rows):
    by_year = defaultdict(list)
    for row in rows:
        by_year[row["year"]].append(row)
    years = sorted(by_year)
    if len(years) < 3:
        raise ValueError("Too few years")
    total_count = sum(row["count"] for row in rows)
    total_length = sum(row["length"] for row in rows)
    mean = total_count / total_length
    deviations = [
        sum(r["count"] for r in by_year[year]) /
        sum(r["length"] for r in by_year[year]) - mean
        for year in years
    ]
    left, right = deviations[:-1], deviations[1:]
    va = sum(v * v for v in left)
    vb = sum(v * v for v in right)
    return sum(a * b for a, b in zip(left, right)) / math.sqrt(va * vb) if va * vb else None


def run(master=810081, worlds=200):
    if worlds < 2:
        raise ValueError("at least two independent synthetic worlds required")
    observed, references, failures = [], [], []
    for index in range(worlds):
        seed = seeded(master, "temporal_covariance_diagnostic", "development", index)
        rows = world(seed, years=16)
        fitted = estimate(rows)
        if not fitted["ready"]:
            failures.append({"index": index, "reason": fitted["reason"]})
            continue
        # This estimator documents that AR1 is not identified.
        if fitted.get("year_rho_identified") is not False:
            raise AssertionError("Unexpected nuisance identification contract")
        ref_seed = seeded(master, "temporal_covariance_diagnostic", "reference", index)
        sampled = bootstrap(rows, fitted, ref_seed)
        observed.append(lag_one(rows))
        references.append(lag_one(sampled))
    if failures or any(v is None or not math.isfinite(v) for v in observed + references):
        return {"ready": False, "attempted": worlds, "complete": len(observed),
                "failures": failures, "reason": "incomplete_or_nonfinite"}
    differences = [a - b for a, b in zip(observed, references)]
    return {
        "schema": "un.null-calibration.temporal-covariance-diagnostic.v1",
        "ready": False,
        "engineering_diagnostic_complete": True,
        "scientific_inference_eligible": False,
        "master_seed": master,
        "attempted": worlds,
        "complete": len(observed),
        "failures": failures,
        "generator_year_rho": 0.55,
        "year_rho_estimated": False,
        "mean_observed_lag1": statistics.mean(observed),
        "mean_bootstrap_lag1": statistics.mean(references),
        "mean_paired_difference": statistics.mean(differences),
        "paired_difference_standard_error": statistics.stdev(differences) / math.sqrt(worlds),
        "limitations": [
            "Lag-one diagnostic is descriptive, not a calibrated test",
            "Estimator has no estimated year AR1 parameter",
            "No token representation covariance or independent source replication",
            "No frozen PR57 threshold or holdout used",
            "No empirical speech text or original source accessed"
        ]
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--worlds", type=int, default=200)
    parser.add_argument("--master", type=int, default=810081)
    args = parser.parse_args()
    result = run(master=args.master, worlds=args.worlds)
    output = json.dumps(result, sort_keys=True, indent=2, allow_nan=False)
    print(output)
    print("diagnostic_json_sha256", hashlib.sha256(output.encode()).hexdigest())
