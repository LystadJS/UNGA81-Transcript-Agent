"""Coordinator-frozen synthetic holdout scorer for unchanged PR #66 methods.

No learner retraining or method selection. Never reads private or reserved text.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

EXPECTED = {"direct","indirect","nested_negation","attributed","conditional","scope_shift","cue_free"}
ROLES = ("anchor","paraphrase","opposite","protocol")
METHODS = ("minilm","lexical","S1_polarity_gated_minilm","S2_signed_lexical")

def locked_fixture(path:Path):
    raw=path.read_bytes()
    x=json.loads(raw)
    if x.get("schema")!="un.coordinator-independent-synthetic-stance-holdout.v1" or x.get("role")!="engineering_only" or x.get("publication_eligible") is not False or x.get("design_locked_before_execution") is not True or x.get("source_scope")!="invented_english_only":
        raise ValueError("holdout authority/identity invalid")
    f=x.get("families")
    if not isinstance(f,list) or len(f)!=42 or len({z.get("id") for z in f})!=42:
        raise ValueError("fixed holdout size/IDs invalid")
    if set(z.get("stratum") for z in f)!=EXPECTED or Counter(z.get("stratum") for z in f)!=Counter({key:6 for key in EXPECTED}):
        raise ValueError("frozen strata altered")
    if x.get("expected_counts")!={"families":42,"observations":168,"evaluable":18,"guard":24,"guard_pair_opportunities":72}:
        raise ValueError("holdout denominators altered")
    for z in f:
        role="evaluable" if z["stratum"] in ("direct","indirect","nested_negation") else "guard"
        if z.get("decision_role")!=role or any(not isinstance(z.get(k),str) or not z[k].strip() for k in ROLES):
            raise ValueError("holdout label or text altered")
        if any("A/81/PV" in z[k] or "https://" in z[k] for k in ROLES):
            raise ValueError("real-source-like marker prohibited")
    return x,sha(raw)

def assess(fixture_path:Path, checkpoint_path:Path)->dict:
    root=Path(__file__).resolve().parents[3]
    sys.path.insert(0,str(root/"research/semantic_representations"))
    from fixtures import fixture_frame
    from pipeline import encode
    from local_model import model_identity,LocalModelEncoder
    from stance_dev_evaluation import scored_pair

    fixture,fixture_digest=locked_fixture(fixture_path)
    cases=fixture["families"]
    frame=fixture_frame(cases)
    texts=[r["text"] for r in frame["rows"]]
    if len(texts)!=168 or any(r["split"]!="synthetic" for r in frame["rows"]):
        raise ValueError("synthetic cohort identity mismatch")
    lexical=TfidfVectorizer(lowercase=True,ngram_range=(1,2),norm="l2").fit_transform(texts)
    model=LocalModelEncoder(checkpoint_path)
    with tempfile.TemporaryDirectory() as td:
        encoded=encode(frame,model_identity(),{"metric":"cosine","pooling":"upstream_chunk_token_weighted"},model,Path(td),batch_size=8)
    coverage=encoded["coverage"]
    # No denominator-based cherry picking; fail if any original observation unavailable.
    if coverage["encoded"]!=168 or coverage["not_fitted"] or coverage["failed_batches"]:
        raise ValueError("holdout model incomplete; never compare selected subset")
    vectors={r["id"]:np.asarray(r["vector"],dtype=np.float64) for r in encoded["rows"] if r["status"]=="encoded"}
    index={r["id"]:i for i,r in enumerate(frame["rows"])}
    if len(vectors)!=168:raise ValueError("duplicate or missing model observation")
    result=[]
    for c in cases:
        pair={}
        for role in ROLES[1:]:
            a,b=c["id"]+":anchor",c["id"]+":"+role
            raw_m=float(np.dot(vectors[a],vectors[b]))
            raw_l=float((lexical[index[a]]@lexical[index[b]].T).toarray()[0,0])
            pair[role]={
                "minilm":round(raw_m,8),"lexical":round(raw_l,8),
                "S1_polarity_gated_minilm":None if (v:=scored_pair(c,role,raw_m,0)) is None else round(v,8),
                "S2_signed_lexical":None if (v:=scored_pair(c,role,raw_l,2)) is None else round(v,8)}
        ordering={}
        for method in METHODS:
            x,y=pair["paraphrase"][method],pair["opposite"][method]
            ordering[method]="abstained" if x is None or y is None else "correct" if x>y else "tie" if x==y else "reversed"
        result.append({"id":c["id"],"stratum":c["stratum"],"declared_role":c["decision_role"],
                       "ordering":ordering,"scores":pair})
    strata={}
    for s in sorted(EXPECTED):
        rs=[r for r in result if r["stratum"]==s]
        strata[s]={"families":len(rs),"methods":{m:dict(Counter(r["ordering"][m] for r in rs)) for m in METHODS}}
    cue=[r for r in result if r["declared_role"]=="evaluable"]
    guard=[r for r in result if r["declared_role"]=="guard"]
    assert len(cue)==18 and len(guard)==24
    metrics={}
    for m in METHODS:
        counts=Counter(r["ordering"][m] for r in cue)
        guard_full=sum(all(r["scores"][role][m] is None for role in ROLES[1:]) for r in guard)
        guard_pair_abstain=sum(r["scores"][role][m] is None for r in guard for role in ROLES[1:])
        nonabstain_guard=72-guard_pair_abstain
        promotable=m.startswith(("S1_","S2_")) and counts["correct"]>=16 and guard_full>=23 and nonabstain_guard==0 and coverage["failed_batches"]==0
        metrics[m]={"evaluable_families":18,"correct":counts["correct"],"reversed":counts["reversed"],
                    "ties":counts["tie"],"abstained_evaluable":counts["abstained"],
                    "guard_families":24,"complete_guard_abstentions":guard_full,
                    "guard_pairs":72,"abstained_guard_pairs":guard_pair_abstain,
                    "unsupported_confident_guard_pairs":nonabstain_guard,
                    "eligible_for_third_party_synthetic_design":bool(promotable)}
    return {"schema":"un.separate-synthetic-holdout-audit.v1",
            "evaluation_role":"engineering_only","publication_eligible":False,"holdout_kind":"coordinator_authored_synthetic_not_human_blinded",
            "fixture_sha256":fixture_digest,"selection_sha256":frame["selection_sha256"],
            "model_revision":model_identity()["revision"],"methods":metrics,"strata":strata,
            "counts":{"families":42,"observations":168,"evaluable_families":18,"guard_families":24,"guard_pairs":72,
                      "successful_observation_encodings":coverage["encoded"],"failed_batches":coverage["failed_batches"],
                      "not_fitted":coverage["not_fitted"],"excluded":coverage["excluded"],"unavailable":coverage["unavailable"]},
            "case_ledger":result,
            "limitations":["Synthetic text/labels separately coordinator-authored, not third-party human-blinded.",
                           "Raw cosine geometry is descriptive, not an applied stance classifier.",
                           "S1/S2 reused unchanged development rule/parsers; no tuning permitted.",
                           "The case ID supplies trusted proposition identity artificially; real text cannot automatically supply it.",
                           "This is a synthetic-only holdout and never authorizes use of the 37 reserved actual meetings.",
                           "Source-matched TF-IDF newly fitted to synthetic holdout, not the archival historical lexical reference."]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fixture",type=Path,required=True)
    p.add_argument("--checkpoint",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    receipt=assess(a.fixture,a.checkpoint)
    raw=(json.dumps(receipt,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode()
    a.out.write_bytes(raw)
    print("HOLDOUT_METRICS="+json.dumps(receipt["methods"],sort_keys=True))
    print("HOLDOUT_RECEIPT_SHA256="+sha(raw))
    print("HOLDOUT_FIXTURE_SHA256="+receipt["fixture_sha256"])
    print("HOLDOUT_STRATA="+json.dumps(receipt["strata"],sort_keys=True))
if __name__=="__main__":main()
