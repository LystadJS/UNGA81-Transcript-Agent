"""Independent SciPy hierarchy and R cluster::pam checks of exported browser scores.

Usage: python tools/check_partition_reference.py analysis.json [RSCRIPT]
Requires scipy/numpy/sklearn plus R cluster and jsonlite; never uploads inputs.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import linkage, cut_tree
from scipy.spatial.distance import cdist
from sklearn.metrics import adjusted_rand_score, silhouette_score


def check(path, rscript="Rscript"):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    first = data["methods"]["clusters"]
    fits = [first] + ([first["comparison"]["alternative"]] if "comparison" in first else [])
    results = []
    for fit in fits:
        method, algorithm = fit["representation"], fit["algorithm"]
        x = np.asarray([p[method] for p in fit["points"]])
        labels = np.asarray([p["cluster"] for p in fit["points"]])
        k = fit["clustering"]["k"]
        sil = float(silhouette_score(x, labels, metric="euclidean"))
        assert abs(sil-fit["clustering"]["silhouette"]) < 1e-9
        result = {"representation": method, "algorithm": algorithm, "passages": len(x), "silhouette_error": abs(sil-fit["clustering"]["silhouette"])}
        if algorithm == "pam":
            # Run the original BUILD+SWAP R implementation, not its faster variant.
            with tempfile.TemporaryDirectory() as directory:
                directory = Path(directory)
                (directory/"scores.json").write_text(json.dumps(x.tolist()), encoding="utf-8")
                (directory/"reference.R").write_text('''args <- commandArgs(trailingOnly=TRUE)
x <- jsonlite::fromJSON(args[1])
fit <- cluster::pam(x, k=as.integer(args[2]), metric="euclidean", stand=FALSE,
                    do.swap=TRUE, pamonce=0, keep.diss=FALSE, keep.data=FALSE)
cat(jsonlite::toJSON(list(labels=unname(fit$clustering), medoids=fit$id.med,
                        mean_distance=unname(fit$objective[2])), auto_unbox=TRUE, digits=16))
''', encoding="utf-8")
                reference = json.loads(subprocess.check_output([rscript, "--vanilla", str(directory/"reference.R"), str(directory/"scores.json"), str(k)], text=True))
            d = cdist(x, x)
            medoids = np.asarray(fit["pam"]["medoid_indices"])
            objective = float(d[:, medoids].min(axis=1).sum())
            assert abs(objective-fit["pam"]["total_distance"]) < 1e-8
            best_delta = 0.0
            for position in range(k):
                other = np.delete(medoids, position)
                kept = d[:, other].min(axis=1)
                for candidate in range(len(x)):
                    if candidate not in medoids:
                        best_delta = min(best_delta, float(np.minimum(kept, d[:, candidate]).sum())-objective)
            assert best_delta >= -1e-8
            error = abs(objective/len(x)-reference["mean_distance"])
            result.update(r_mean_distance=reference["mean_distance"], browser_mean_distance=objective/len(x),
                          objective_error=error, reference_ari=float(adjusted_rand_score(labels, reference["labels"])),
                          exhaustive_best_swap_delta=best_delta)
            assert error < 1e-8, result
        else:
            mode=fit["hierarchical"]["linkage"]
            z=linkage(x,method=mode,metric="euclidean",optimal_ordering=False)
            heights=np.asarray([m["height"] for m in fit["hierarchical"]["merges"]])
            error=float(np.max(np.abs(z[:,2]-heights)))
            reference=cut_tree(z,n_clusters=[k]).ravel()
            agreement=float(adjusted_rand_score(labels,reference))
            result.update(linkage=mode,merge_height_max_error=error,reference_ari=agreement)
            assert error < 1e-8, result
            assert agreement > 1-1e-10, result
            # Every browser node partitions exactly the union of its children.
            members={i:{i} for i in range(len(x))}
            for m in fit["hierarchical"]["merges"]:
                a,b=members[m["left"]],members[m["right"]]
                assert not a.intersection(b)
                members[m["node"]]=a|b
                assert len(a|b)==m["size"]
            for c,node in enumerate(fit["hierarchical"]["cut_nodes"],1):
                assert members[node]==set(np.flatnonzero(labels==c))
        results.append(result)
    return {"independent_references":results,"status":"PASS"}


if __name__=="__main__":
    print(json.dumps(check(*sys.argv[1:]),indent=2))
