"""Independent sklearn HDBSCAN reference on synthetic fixtures or exported scores."""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
import sklearn
from scipy.spatial.distance import cdist, squareform
from scipy.cluster.hierarchy import linkage, cophenet
from sklearn.cluster import HDBSCAN
from sklearn.cluster._hdbscan._tree import HIERARCHY_dtype, tree_to_labels
from sklearn.datasets import make_moons
from sklearn.metrics import adjusted_rand_score


def fixtures():
    rng=np.random.default_rng(71982)
    cases=[]
    for seed in range(12):
        x=np.vstack([rng.normal([0,0],[.09,.15],(24,2)),rng.normal([2,1],[.2,.12],(32,2)),rng.uniform(-2,4,(9,2))])
        cases.append(dict(name=f"density-{seed}",x=x.tolist(),options=dict(minClusterSize=5+seed%6,minSamples=3+seed%5,selection="eom" if seed%2 else "leaf")))
    for selection in ["eom","leaf"]:
        for name,x,minimum in [
            ("moons",make_moons(130,noise=.035,random_state=42)[0],8),
            ("all-identical",np.ones((16,2)),5),
            ("duplicate-groups",np.vstack([np.zeros((12,2)),np.ones((12,2))*4,[[12,12]]]),5),
            ("uniform-grid",np.asarray([(i,j) for i in range(5) for j in range(5)]),5),
            ("minimum-too-large",rng.normal(size=(20,3)),30),
        ]:
            cases.append(dict(name=name+"-"+selection,x=x.tolist(),options=dict(minClusterSize=minimum,minSamples=5,selection=selection)))
    return cases


def check(node,analysis=None):
    if analysis:
        data=json.loads(Path(analysis).read_text(encoding="utf-8-sig"))["methods"]["clusters"]
        fits=[data]+([data["comparison"]["alternative"]] if "comparison" in data else [])
        cases=[dict(name=f["representation"],x=[p[f["representation"]] for p in f["points"]],
                    options=f["parameters"]["hdbscan"]) for f in fits]
    else:
        fits=None;cases=fixtures()
    module=Path(__file__).resolve().parents[1]/"site/hdbscan-core.js"
    script="const H=require("+json.dumps(str(module))+ ");let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',async()=>{const out=[];for(const c of JSON.parse(s))out.push(await H.fit(c.x,c.options));process.stdout.write(JSON.stringify(out));});"
    actual=json.loads(subprocess.check_output([node,"-e",script],input=json.dumps(cases),text=True))
    checks=[]
    for i,(case,got) in enumerate(zip(cases,actual)):
        x=np.asarray(case["x"]);o=case["options"]
        ref=HDBSCAN(min_cluster_size=o["minClusterSize"],min_samples=o["minSamples"],cluster_selection_method=o["selection"],metric="euclidean",algorithm="kd_tree",allow_single_cluster=False).fit(x)
        np.testing.assert_allclose(got["diagnostics"]["core_distances"],np.sort(cdist(x,x),axis=1)[:,o["minSamples"]-1],atol=1e-12)
        core=np.asarray(got["diagnostics"]["core_distances"])
        reach=np.maximum(np.maximum(cdist(x,x),core[:,None]),core[None,:]);np.fill_diagonal(reach,0)
        reference_tree=linkage(squareform(reach),method="single")
        tree=np.asarray([(m["left"],m["right"],m["distance"],m["size"]) for m in got["diagnostics"]["single_linkage"]])
        # All pairwise single-linkage connection levels must agree, even when
        # binary resolutions of simultaneous merges differ between libraries.
        tree_error=float(np.max(np.abs(cophenet(tree)-cophenet(reference_tree))))
        assert tree_error<1e-10
        for edge in got["diagnostics"]["mst"]:
            assert abs(reach[edge["left"],edge["right"]]-edge["distance"])<1e-10
        np.testing.assert_allclose(tree[:,2].sum(),reference_tree[:,2].sum(),atol=1e-10)
        exact=np.asarray([tuple(row) for row in tree],dtype=HIERARCHY_dtype)
        selected_labels,selected_strength=tree_to_labels(exact,o["minClusterSize"],o["selection"],False)
        labels=np.asarray(got["labels"]);strength=np.asarray(got["strengths"])
        assert adjusted_rand_score(selected_labels,labels)>1-1e-12
        np.testing.assert_array_equal(selected_labels<0,labels<0)
        np.testing.assert_allclose(selected_strength,strength,atol=1e-10)
        agreement=float(adjusted_rand_score(ref.labels_,labels))
        noise_equal=bool(np.array_equal(ref.labels_<0,labels<0))
        error=float(np.max(np.abs(ref.probabilities_-strength)))
        row={"case":case["name"],"passages":len(x),"clusters":len(set(labels)-{-1}),"unassigned":int(sum(labels<0)),
             "reference_ari":agreement,"noise_mask_equal":noise_equal,"membership_strength_max_error":error,
             "single_linkage_cophenetic_max_error":tree_error,"selection_on_same_tree_matches":True,
             "cross_implementation_equal":agreement>1-1e-12 and noise_equal and error<1e-8}
        if not row["cross_implementation_equal"]:
            assert len(set(tree[:,2]))<len(tree),"Unexpected disagreement without tied hierarchy heights"
            row["portability_note"]="Equal-height binary merge order differs; the full single-linkage geometry and independent selection on the identical tree agree. No claim of cross-library label identity."
        if fits:
            np.testing.assert_array_equal(labels,np.asarray([p["cluster"]-1 for p in fits[i]["points"]]))
            np.testing.assert_allclose(strength,[p["membership_strength"] for p in fits[i]["points"]],atol=1e-12)
        checks.append(row)
    return {"status":"PASS staged algorithm checks","reference":"scikit-learn "+sklearn.__version__+" HDBSCAN; SciPy independently verifies every single-linkage connection level; sklearn validates condensation/selection on the identical tree", "checks":checks}


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--node",default="node");parser.add_argument("--analysis");args=parser.parse_args()
    print(json.dumps(check(args.node,args.analysis),indent=2))
