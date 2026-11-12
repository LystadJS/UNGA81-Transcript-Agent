"""Same-observation geometry, negative-control and instability diagnostics.

Descriptive only: no claims of stance, coalition, significance or replication.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from itertools import combinations
import math
import random
from typing import Any

try:
    from .pipeline import SCHEMA, _assert, _vector, digest
except ImportError:
    from pipeline import SCHEMA, _assert, _vector, digest

PROTOCOL = "same-observation-lexical-semantic-v1"


def validate_paired(left: dict, right: dict) -> dict:
    _assert(left.get("schema") == SCHEMA and right.get("schema") == SCHEMA, "result schema mismatch")
    for field in ("frame_sha256", "source_schema", "source_hash_basis", "source_sha256",
                  "selection_sha256", "split", "population", "unit", "source_group_unit", "weighting"):
        _assert(left.get(field) == right.get(field), "incompatible " + field)
    _assert(left.get("representation_id") != right.get("representation_id"), "indistinct representation identities")
    _assert(left.get("representation_basis_id") == left.get("representation_id") and
            right.get("representation_basis_id") == right.get("representation_id"), "wrong representation basis")
    a, b = left.get("rows"), right.get("rows")
    _assert(isinstance(a,list) and isinstance(b,list) and len(a)==len(b), "observation population mismatch")
    _assert(a and len({x.get("id") for x in a})==len(a), "empty/duplicate observation ids")
    for x, y in zip(a,b):
        for field in ("id", "source_id", "source_sha256", "text_sha256", "unit", "meeting_id", "parent_id", "source_family_id"):
            _assert(x.get(field)==y.get(field), "paired observation lineage mismatch: " + field)
        _assert(x.get("status") in {"encoded", "not_fitted", "excluded", "unavailable"} and
                y.get("status") in {"encoded", "not_fitted", "excluded", "unavailable"}, "unknown row status")
        for z in (x,y):
            if z["status"] == "encoded":
                _assert(z.get("vector") is not None and digest(z["vector"])==z.get("vector_sha256"), "vector hash changed")
                vals=_vector(z["vector"])
                _assert(len(vals)==len(z["vector"]) and all(abs(v-w)<1e-8 for v,w in zip(vals,z["vector"])), "non-unit vector")
            else:
                _assert(z.get("vector") is None, "not-fitted vector present")
    usable = [i for i,(x,y) in enumerate(zip(a,b)) if x["status"]=="encoded" and y["status"]=="encoded"]
    _assert(usable or not any(x["status"]=="encoded" for x in a+b), "no common paired vectors")
    return {"frame":len(a), "eligible":left["coverage"]["eligible"],
            "paired":len(usable), "unpaired_left":sum(x["status"]=="encoded" and y["status"]!="encoded" for x,y in zip(a,b)),
            "unpaired_right":sum(y["status"]=="encoded" and x["status"]!="encoded" for x,y in zip(a,b)),
            "excluded":left["coverage"]["excluded"], "unavailable":left["coverage"]["unavailable"],
            "not_in_frame":left["coverage"]["not_in_frame"], "indices":usable}


def cosine(x: list[float], y: list[float]) -> float:
    _assert(len(x)==len(y), "within-representation dimension mismatch")
    return sum(a*b for a,b in zip(x,y))


def neighborhood(left: dict, right: dict, k: int, exclusion: str = "self") -> dict:
    counts = validate_paired(left,right)
    _assert(type(k) is int and k>=1 and exclusion in {"self", "meeting", "parent", "source_family"}, "invalid neighborhood policy")
    rows_a,rows_b=left["rows"],right["rows"]
    usable=counts.pop("indices")
    _assert(k < len(usable), "not enough paired observations for k")
    key={"meeting":"meeting_id", "parent":"parent_id", "source_family":"source_family_id"}.get(exclusion)
    matches=[]
    withheld=[]
    for i in usable:
        possible=[]
        for j in usable:
            if j==i:continue
            if key is not None:
                _assert(rows_a[i].get(key) is not None, "source-group exclusion without verified grouping")
                _assert(rows_a[j].get(key) is not None, "source-group exclusion without verified grouping")
                if rows_a[i][key]==rows_a[j][key]:continue
            possible.append(j)
        if len(possible)<k:
            withheld.append(rows_a[i]["id"])
            continue
        def top(rows):
            return sorted(possible,key=lambda j:(-round(cosine(rows[i]["vector"],rows[j]["vector"]),12),rows[j]["id"]))[:k]
        near_a=top(rows_a);near_b=top(rows_b)
        matches.append({"id":rows_a[i]["id"],"overlap":len(set(near_a)&set(near_b))/k,
                        "lexical_neighbors":[rows_a[j]["id"] for j in near_a],
                        "semantic_neighbors":[rows_a[j]["id"] for j in near_b]})
    return {"protocol":PROTOCOL,"exclusion":exclusion,"k":k,"counts":counts,
            "assessable":len(matches),"withheld":len(withheld),"withheld_ids":withheld,
            "overlap_mean":sum(r["overlap"] for r in matches)/len(matches) if matches else None,
            "points":matches,"status":"descriptive" if matches else "withheld",
            "interpretation":"same-observation geometry only; semantic neighbors do not indicate agreement"}


def choose2(n: int) -> int:
    return n*(n-1)//2


def adjusted_rand(labels_a: list, labels_b: list) -> float | None:
    """Label-invariant ARI, null for mathematically degenerate expected denominator."""
    _assert(len(labels_a)==len(labels_b) and len(labels_a)>=2, "ARI population mismatch")
    contingency=Counter(zip(labels_a,labels_b))
    a=Counter(labels_a);b=Counter(labels_b)
    pairs=choose2(len(labels_a))
    matches=sum(choose2(v) for v in contingency.values())
    expected=sum(choose2(v) for v in a.values())*sum(choose2(v) for v in b.values())/pairs
    maximum=(sum(choose2(v) for v in a.values())+sum(choose2(v) for v in b.values()))/2
    denom=maximum-expected
    if abs(denom)<1e-12:
        return 1.0 if labels_a==labels_b else None
    return (matches-expected)/denom


def medoid_fit(view: dict, k: int, seed: int, max_iterations: int = 40) -> dict:
    """Small synthetic-only deterministic PAM-style diagnostic, not production clustering.

    Records all attempts; all points remain assigned or the fit fails explicitly.
    """
    _assert(view.get("schema")==SCHEMA,"unknown representation result")
    rows=[r for r in view["rows"] if r["status"]=="encoded"]
    _assert(len(rows)>=3 and 2<=k<len(rows),"insufficient eligible fit observations")
    _assert(type(seed) is int and type(max_iterations) is int and max_iterations>0, "seed/iterations")
    values=[r["vector"] for r in rows]
    _assert(len({len(x) for x in values})==1,"dimension drift")
    distances=[[max(0.0,1-cosine(a,b)) for b in values] for a in values]
    rng=random.Random(seed)
    medoids=rng.sample(range(len(rows)),k)
    seen=set()
    for iteration in range(1,max_iterations+1):
        labels=[min(range(k), key=lambda c:(distances[i][medoids[c]],c)) for i in range(len(rows))]
        clusters=[[i for i,c in enumerate(labels) if c==cluster] for cluster in range(k)]
        if any(not c for c in clusters):
            return {"status":"failed","seed":seed,"reason":"empty cluster", "attempted":1,"successful":0,"failed":1,"unassigned":len(rows)}
        updated=[min(cluster,key=lambda candidate:(sum(distances[candidate][j] for j in cluster),rows[candidate]["id"])) for cluster in clusters]
        if updated==medoids:
            return {"status":"fitted","seed":seed,"attempted":1,"successful":1,"failed":0,
                    "iterations":iteration,"converged":True,"labels":{row["id"]:labels[i]+1 for i,row in enumerate(rows)},
                    "medoid_ids":[rows[i]["id"] for i in medoids],"eligible":len(rows),"assigned":len(rows),"unassigned":0}
        signature=tuple(updated)
        if signature in seen:
            return {"status":"failed","seed":seed,"reason":"medoid cycle", "attempted":1,"successful":0,"failed":1,"unassigned":len(rows)}
        seen.add(signature)
        medoids=updated
    return {"status":"failed","seed":seed,"reason":"iteration limit", "attempted":1,"successful":0,"failed":1,"unassigned":len(rows)}


def clustering_sensitivity(left: dict, right: dict, k: int, seeds=(17,23,31,47)) -> dict:
    counts=validate_paired(left,right)
    _assert(counts["paired"] == counts["eligible"] and counts["eligible"]>=k+1,
            "unpaired/missing eligible clustering comparison forbidden")
    results={"lexical":[],"semantic":[]}
    for label,view in (("lexical",left),("semantic",right)):
        for seed in seeds:
            results[label].append(medoid_fit(view,k,seed))
    comparisons=[]
    for lf in results["lexical"]:
        for sf in results["semantic"]:
            if lf["status"] != "fitted" or sf["status"] != "fitted":
                comparisons.append({"status":"withheld", "ari":None,"reason":"failed fit"})
                continue
            ids=[r["id"] for r in left["rows"] if r["status"]=="encoded"]
            comparisons.append({"status":"descriptive", "ari":adjusted_rand([lf["labels"][i] for i in ids],[sf["labels"][i] for i in ids]),"reason":None})
    within={}
    for name,runs in results.items():
        fits=[r for r in runs if r["status"]=="fitted"]
        scores=[]
        for a,b in combinations(fits,2):
            ids=list(a["labels"])
            scores.append(adjusted_rand([a["labels"][i] for i in ids],[b["labels"][i] for i in ids]))
        within[name]={"attempted":len(runs),"successful":len(fits),"failed":len(runs)-len(fits),
                      "ari_mean":sum(x for x in scores if x is not None)/sum(x is not None for x in scores) if any(x is not None for x in scores) else None,
                      "assessable_pairs":sum(x is not None for x in scores)}
    fit_scores=[x["ari"] for x in comparisons if x["ari"] is not None]
    return {"protocol":PROTOCOL,"k":k,"counts":{k:v for k,v in counts.items() if k!="indices"},
            "fits":results,"within_representation":within,"pairwise_comparisons":comparisons,
            "cross_representation_ari_mean":sum(fit_scores)/len(fit_scores) if fit_scores else None,
            "assessable_cross_pairs":len(fit_scores),"planned_cross_pairs":len(seeds)**2,
            "interpretation":"seed sensitivity and cluster-label-invariant comparison, not stability significance or independent replication"}
