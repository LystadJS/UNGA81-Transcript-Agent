"""Independent numerical audit of an exported stability run (NumPy/scikit-learn).

Usage: python tools/check_stability_reference.py path/to/analysis.json
No model is fitted, no corpus is uploaded, and input files remain unchanged.
"""
import json
import sys

import numpy as np
from sklearn.metrics import adjusted_rand_score


def check(path):
    with open(path, encoding="utf-8") as stream:
        result = json.load(stream)
    stability = result["methods"]["clusters"]["stability"]
    reference = np.array(stability["reference_clusters"])
    n = len(reference)
    observed = np.zeros((n, n), dtype=int)
    together = np.zeros((n, n), dtype=int)
    included = np.zeros(n, dtype=int)
    errors = []
    checked = 0
    for run in stability["runs"]:
        if "skipped" in run:
            continue
        indices = np.array(run["indices"])
        labels = np.array(run["labels"])
        ref = reference[indices]
        errors.append(abs(adjusted_rand_score(ref, labels) - run["ari"]))
        for cluster in run["jaccards"]:
            members = ref == cluster["cluster"]
            if members.sum() < 2:
                assert cluster["jaccard"] is None
                continue
            expected = max(
                np.logical_and(members, labels == c).sum()
                / np.logical_or(members, labels == c).sum()
                for c in np.unique(labels)
            )
            errors.append(abs(expected - cluster["jaccard"]))
        positions = np.ix_(indices, indices)
        observed[positions] += 1
        together[positions] += labels[:, None] == labels[None, :]
        included[indices] += 1
        checked += 1
    lower = np.tril_indices(n, -1)
    consensus = stability["consensus"]
    np.testing.assert_array_equal(observed[lower], consensus["co_observed"])
    np.testing.assert_array_equal(together[lower], consensus["co_clustered"])
    np.testing.assert_array_equal(included, [p["included"] for p in consensus["points"]])
    assert max(errors, default=0) < 1e-12
    return {"successful_samples_checked": checked, "passages": n,
            "pair_denominators_checked": n * (n - 1) // 2,
            "max_ari_or_jaccard_error": max(errors, default=0),
            "reference": "NumPy pair reconstruction and scikit-learn adjusted_rand_score"}


if __name__ == "__main__":
    print(json.dumps(check(sys.argv[1]), indent=2))
