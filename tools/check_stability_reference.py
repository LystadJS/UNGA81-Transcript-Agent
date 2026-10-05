"""Independent numerical audit of an exported stability run (NumPy/scikit-learn).

Usage: python tools/check_stability_reference.py path/to/analysis.json
No model is fitted, no corpus is uploaded, and input files remain unchanged.
"""
import json
import sys

import numpy as np
from sklearn.metrics import adjusted_rand_score


def check(path, representation=None):
    with open(path, encoding="utf-8") as stream:
        result = json.load(stream)
    fit = result["methods"]["clusters"]
    if representation == "lsa" and "comparison" in fit:
        fit = fit["comparison"]["alternative"]
    if representation is not None:
        assert fit.get("representation", "pca") == representation
    stability = fit["stability"]
    reference = np.array(stability["reference_clusters"])
    n = len(reference)
    observed = np.zeros((n, n), dtype=int)
    together = np.zeros((n, n), dtype=int)
    included = np.zeros(n, dtype=int)
    noise = fit.get("algorithm") == "hdbscan"
    co_assigned = np.zeros((n, n), dtype=int)
    assigned = np.zeros(n, dtype=int)
    errors = []
    checked = 0
    for run in stability["runs"]:
        if "skipped" in run:
            continue
        indices = np.array(run["indices"])
        labels = np.array(run["labels"])
        ref = reference[indices]
        shared=(ref>0)&(labels>=0) if noise else np.ones(len(labels),dtype=bool)
        assessable=not (noise or fit.get("algorithm")=="gmm") or (shared.sum()>=2 and len(np.unique(ref[shared]))>=2 and len(np.unique(labels[shared]))>=2)
        if assessable:
            errors.append(abs(adjusted_rand_score(ref[shared], labels[shared]) - run["ari"]))
        else:
            assert run["ari"] is None
        if noise:
            assert int(shared.sum()) == run["assignment"]["shared_assigned_for_ari"]
            assert int(sum(labels<0)) == run["assignment"]["unassigned_count"]
        for cluster in run["jaccards"]:
            members = ref == cluster["cluster"]
            if members.sum() < 2:
                assert cluster["jaccard"] is None
                continue
            expected = max((
                np.logical_and(members, labels == c).sum()
                / np.logical_or(members, labels == c).sum()
                for c in np.unique(labels) if not noise or c>=0
            ),default=0)
            errors.append(abs(expected - cluster["jaccard"]))
        positions = np.ix_(indices, indices)
        observed[positions] += 1
        both=(labels[:,None]>=0)&(labels[None,:]>=0) if noise else np.ones((len(labels),len(labels)),dtype=bool)
        together[positions] += (labels[:, None] == labels[None, :]) & both
        co_assigned[positions] += both
        assigned[indices] += labels>=0
        included[indices] += 1
        checked += 1
    lower = np.tril_indices(n, -1)
    consensus = stability["consensus"]
    np.testing.assert_array_equal(observed[lower], consensus["co_observed"])
    np.testing.assert_array_equal(together[lower], consensus["co_clustered"])
    np.testing.assert_array_equal(included, [p["included"] for p in consensus["points"]])
    if noise:
        np.testing.assert_array_equal(co_assigned[lower],consensus["co_assigned"])
        np.testing.assert_array_equal(assigned,[p["assigned"] for p in consensus["points"]])
        np.testing.assert_array_equal(included-assigned,[p["unassigned"] for p in consensus["points"]])
        for i,p in enumerate(consensus["points"]):
            if reference[i]==0: assert p["within_cluster"] is None and p["margin"] is None
    assert max(errors, default=0) < 1e-12
    return {"successful_samples_checked": checked, "passages": n,
            "pair_denominators_checked": n * (n - 1) // 2,
            "max_ari_or_jaccard_error": max(errors, default=0),
            "noise_aware":noise,
            "reference": "NumPy pair reconstruction and scikit-learn adjusted_rand_score"}


if __name__ == "__main__":
    print(json.dumps(check(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None), indent=2))
