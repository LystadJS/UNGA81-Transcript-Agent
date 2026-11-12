"""Authored synthetic contrasts and a deliberately non-neural test double.

The test double MUST NOT be reported as MiniLM performance. No UN source content.
"""
from __future__ import annotations
import hashlib
import math
import re

try:
    from .pipeline import FRAME_SCHEMA, sha, digest
except ImportError:
    from pipeline import FRAME_SCHEMA, sha, digest

CONTRASTS = [
    {"id":"policy", "anchor":"We support ending financial restrictions.",
     "paraphrase":"Our delegation favors removal of economic barriers.",
     "opposite":"We oppose ending financial restrictions.",
     "protocol":"Thank you Chair; we oppose ending financial restrictions."},
    {"id":"ceasefire", "anchor":"We support an immediate ceasefire to protect civilians.",
     "paraphrase":"Our delegation favors stopping fighting now to safeguard civilians.",
     "opposite":"We reject an immediate ceasefire to protect civilians.",
     "protocol":"Thank you Chair; we reject an immediate ceasefire to protect civilians."},
    {"id":"climate", "anchor":"We support adaptation financing for vulnerable countries.",
     "paraphrase":"Our delegation favors resilience funding for exposed nations.",
     "opposite":"We oppose adaptation financing for vulnerable countries.",
     "protocol":"Thank you Chair; we oppose adaptation financing for vulnerable countries."},
    {"id":"inspection", "anchor":"We endorse independent nuclear inspections.",
     "paraphrase":"Our delegation favors impartial monitoring of atomic sites.",
     "opposite":"We reject independent nuclear inspections.",
     "protocol":"Thank you Chair; we reject independent nuclear inspections."},
]


def fixture_frame(contrasts=CONTRASTS, suffix="") -> dict:
    rows=[]
    for i, case in enumerate(contrasts):
        for role in ("anchor","paraphrase","opposite","protocol"):
            text=case[role]+suffix
            rows.append({"id":f"{case['id']}:{role}","text":text,"text_sha256":sha(text.encode("utf-8")),
                         "source_id":f"fixture-{case['id']}-{role}","source_sha256":digest({"case":case["id"],"role":role}),
                         "unit":"synthetic","split":"synthetic","source_status":"available", "exclusion_reasons":[],
                         "missing_reason":None, "review_status":"not_applicable", "language":"en", "source_url":None,
                         "meeting_id":f"synthetic-{i%2}","source_family_id":f"fixture-{i}","country":None,
                         "parent_id":None,"parent_text_sha256":None,"parent_length":None,"start":None,"end":None,
                         "speech_id":None})
    return {"schema":FRAME_SCHEMA,"split":"synthetic","source_schema":"synthetic.v1",
            "source_hash_basis":"synthetic","source_sha256":digest({"fixture":"v1","cases":contrasts}),
            "selection_sha256":digest([r["id"] for r in rows]), "population":"authored_synthetic_contrast_cases",
            "unit":"synthetic","source_group_unit":"synthetic_meeting","weighting":"equal_synthetic_observation",
            "selection_policy":"all_authored_cases_no_holdout","duplicate_policy":"retain_all", "inventory_total":len(rows),"rows":rows}


FIXTURE_MODEL = {"schema":"un.synthetic-model-lock.v1","repository":"fixture-vectorizer-not-minilm",
                 "revision":"fixture-v2-no-trained-weights","license":"synthetic-test-only"}
LEXICAL_MODEL = {"schema":"un.synthetic-model-lock.v1","repository":"fixture-word-count-baseline",
                 "revision":"fixture-v2-not-tfidf-lsa","license":"synthetic-test-only"}
SEMANTIC_SETTINGS = {"metric":"cosine","pooling":"fixture_token_weighted", "preprocessing":"verbatim_original_utf8", "context_tokens":254}
LEXICAL_SETTINGS = {"metric":"cosine","pooling":"fixture_token_weighted", "preprocessing":"verbatim_original_utf8", "context_tokens":254, "lexical_test_double":True}


class FixtureEncoder:
    """Fixed local deterministic wordpiece proxy; tests plumbing, not linguistic quality."""
    CONCEPTS = (
        ("economic", ("financial","economic","restrictions","barriers","removal","ending")),
        ("ceasefire", ("ceasefire","stopping","fighting","civilians","safeguard","protect")),
        ("climate", ("adaptation","resilience","funding","financing","vulnerable","exposed")),
        ("nuclear", ("nuclear","atomic","inspections","monitoring","sites","impartial")),
    )
    POSITIVE={"support","favors","favor","endorse","endorses"}
    NEGATIVE={"oppose","reject","opposes","rejects","not"}

    def __init__(self, lexical=False, fail_text=None):
        self.lexical=lexical
        self.fail_text=fail_text
        self.calls=0

    def encode(self, rows: list[dict], batch_size=16):
        self.calls+=1
        if self.fail_text is not None and any(self.fail_text in r["text"] for r in rows):
            raise RuntimeError("synthetic deliberate batch failure")
        chunks=[];vectors=[];wordpieces=0
        for row in rows:
            text=row["text"]
            matches=list(re.finditer(r"\S+",text))
            if not matches: raise ValueError("tokenizer produced no tokens")
            ids=list(range(len(matches)))
            wordpieces+=len(ids)
            for start in range(0,len(ids),254):
                end=min(len(ids),start+254)
                a=0 if start==0 else matches[start].start()
                b=len(text) if end==len(ids) else matches[end].start()
                chunks.append({"id":row["id"],"token_start":start,"token_end":end,
                               "coverage_start":a,"coverage_end":b,"chunk_sha256":sha(text[a:b].encode("utf-8")),
                               "token_ids_sha256":digest(ids[start:end])})
            words=set(w.strip(".,;:!?").lower() for w in text.split())
            if self.lexical:
                # Deliberately transparent word-pattern baseline, NOT actual TF-IDF/LSA.
                terms=("support","favors","oppose","reject","financial","ceasefire","nuclear","adaptation", "chair")
                vec=[float(w in words) for w in terms]
            else:
                vec=[float(sum(word in words for word in items)) for _,items in self.CONCEPTS]
                vec.extend([2.0 if words & self.POSITIVE else 0.0,
                            2.0 if words & self.NEGATIVE else 0.0,
                            float("chair" in words)*0.2,
                            math.log1p(len(matches))*0.03])
            norm=math.sqrt(sum(x*x for x in vec))
            if norm < 1e-12: vec[0]=1.0;norm=1.0
            vectors.append([x/norm for x in vec])
        return vectors,chunks,{"passages":len(rows),"chunks":len(chunks),"wordpieces":wordpieces,
                               "truncated_wordpieces":0,"test_double":True}


def contrast_audit(semantic_view: dict) -> dict:
    """Source-label-specific synthetic checks: never treat cosine as stance."""
    rows={r["id"]:r for r in semantic_view["rows"] if r["status"]=="encoded"}
    def dot(a,b): return sum(x*y for x,y in zip(rows[a]["vector"],rows[b]["vector"]))
    cases=[]
    for case in CONTRASTS:
        key=case["id"]
        a=key+":anchor"
        case_out={"id":key,"same_issue_opposite_stance_is_negative_control":True,
                  "paraphrase_cosine":dot(a,key+":paraphrase"),
                  "opposite_cosine":dot(a,key+":opposite"),
                  "shared_protocol_cosine":dot(a,key+":protocol"),
                  "stance_classification":"withheld"}
        cases.append(case_out)
    passed=sum(c["paraphrase_cosine"]>c["opposite_cosine"] for c in cases)
    return {"cases":cases,"denominator":len(cases),"paraphrase_closer_than_opposite":passed,
            "protocol_confounds_explicitly_included":len(cases),"fixture_only":True,
            "checkpoint_execution":"NOT_RUN","interpretation":"No diplomatic agreement inferred; authored fixtures cannot establish semantic checkpoint performance"}
