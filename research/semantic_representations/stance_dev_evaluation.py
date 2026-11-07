"""Development-only preregistered contrast evaluation.

The parser is a deliberately narrow *handcrafted* sign diagnostic, not trained
stance inference. All observations are invented. No UN or held-out inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from fixtures import fixture_frame
from local_model import LocalModelEncoder, model_identity
from pipeline import encode

PROTOCOL = "un.stance-dev-protocol.v1"
STRATA_COUNTS = {"explicit":8, "negated":6, "conditional":4,
                 "quoted":4, "scope":4, "ambiguous":4}
ROLES = ("anchor","paraphrase","opposite","protocol")
SIGN = {"support":1, "endorse":1, "welcome":1, "favor":1, "favors":1,
        "oppose":-1, "reject":-1, "rejects":-1}
RULE = re.compile(r"^(?:thank you chair;\s*)?(?:we|our delegation)\s+(?:(do not|not)\s+)?(support|endorse|welcome|favor|favors|oppose|reject|rejects)\b", re.I)
GUARD = re.compile(r"\b(only if|provided that|unless|on condition|subject to|except|according to|observer|another delegation|reported|quoting|quoted)\b|[\"“”]",re.I)

# Case patterns are authored only for this committed synthetic protocol.
EXPLICIT = [
    ("public libraries", "improving community access to libraries"),
    ("coastal monitoring", "better observation of shorelines"),
    ("disaster warning systems", "strengthening early alerts for natural hazards"),
    ("satellite debris removal", "cleaning up orbital space junk"),
    ("regional rail improvements", "better cross-border train connections"),
    ("vaccination outreach", "community programs to expand immunization"),
    ("ocean plastics cleanup", "removing waste from marine ecosystems"),
    ("public research archives", "open access to scientific repositories"),
]
NEGATED = [
    ("new fees on basic medicines", "additional charges for essential drugs", "do not support", "rejects", "support"),
    ("restrictions on humanitarian deliveries", "barriers to relief shipments", "do not endorse", "rejects", "endorse"),
    ("closing shared scientific databases", "shutting down common research libraries", "do not favor", "rejects", "support"),
    ("emergency shelter funding", "rapid assistance for temporary housing", "do not oppose", "favors", "reject"),
    ("renewable energy grants", "funding for clean energy projects", "do not reject", "favors", "oppose"),
    ("clean drinking water initiatives", "improved access to safe water supplies", "do not oppose", "favors", "reject"),
]
CONDITIONAL = [
    ("protecting coastal forests","safeguarding shoreline woodland"),
    ("reducing freight emissions","lowering pollution from cargo transport"),
    ("expanding teacher training","more preparation for educators"),
    ("sharing disaster forecasting data","opening hazard prediction datasets"),
]
QUOTED = [
    ("medical supply corridors","channels for delivering clinical goods"),
    ("restoration of wetlands","repairing marsh ecosystems"),
    ("community language education","teaching minority languages locally"),
    ("improved recycling centers","better waste sorting facilities"),
]
SCOPE = [
    ("new public parks","repairing existing sidewalks","closing rural clinics"),
    ("urban rooftop gardens","school lunch services","removing public bus routes"),
    ("ocean research grants","housing rental assistance","commercial air routes"),
    ("municipal water treatment","public museum admissions","closing rail crossings"),
]
AMBIGUOUS = [
    ("revisiting public transport schedules","reviewing regional commute timetables"),
    ("exploring wetland inventories","assessing marsh mapping approaches"),
    ("considering hospital energy audits","evaluating power efficiency in clinics"),
    ("discussing shared meteorological data","talking about common weather records"),
]

def cases():
    out=[]
    for i,(topic,synonym) in enumerate(EXPLICIT,1):
        out.append(dict(id=f"E{i:02}",stratum="explicit",anchor=f"We support {topic}.",
                        paraphrase=f"Our delegation favors {synonym}.",
                        opposite=f"We oppose {topic}.",
                        protocol=f"Thank you Chair; we oppose {topic}."))
    for i,(topic,synonym,verb,paraverb,oppverb) in enumerate(NEGATED,1):
        out.append(dict(id=f"N{i:02}",stratum="negated",anchor=f"We {verb} {topic}.",
                        paraphrase=f"Our delegation {paraverb} {synonym}.",
                        opposite=f"We {oppverb} {topic}.",
                        protocol=f"Thank you Chair; we {oppverb} {topic}."))
    for i,(topic,synonym) in enumerate(CONDITIONAL,1):
        out.append(dict(id=f"C{i:02}",stratum="conditional",
                        anchor=f"We support {topic} only if an independent review agrees.",
                        paraphrase=f"Our delegation favors {synonym} provided that technical checks pass.",
                        opposite=f"We oppose {topic} unless conditions improve.",
                        protocol=f"Thank you Chair; we oppose {topic} unless conditions improve."))
    for i,(topic,synonym) in enumerate(QUOTED,1):
        out.append(dict(id=f"Q{i:02}",stratum="quoted",
                        anchor=f'The observer quoted "We support {topic}."',
                        paraphrase=f'The observer quoted "Our delegation favors {synonym}."',
                        opposite=f'The observer quoted "We oppose {topic}."',
                        protocol=f'Thank you Chair; the observer quoted "We oppose {topic}."'))
    for i,(a,b,c) in enumerate(SCOPE,1):
        out.append(dict(id=f"S{i:02}",stratum="scope",
                        anchor=f"We support {a}.",
                        paraphrase=f"Our delegation favors {b}.",
                        opposite=f"We oppose {c}.",
                        protocol=f"Thank you Chair; we oppose {c}."))
    for i,(topic,synonym) in enumerate(AMBIGUOUS,1):
        out.append(dict(id=f"A{i:02}",stratum="ambiguous",
                        anchor=f"It may be useful to consider {topic}.",
                        paraphrase=f"One option is to evaluate {synonym}.",
                        opposite=f"Some questions remain about {topic}.",
                        protocol=f"Thank you Chair; questions remain about {topic}."))
    assert len(out)==30 and len(set(x["id"] for x in out))==30
    assert {key:sum(c["stratum"]==key for c in out) for key in STRATA_COUNTS} == STRATA_COUNTS
    return out

def sign(text):
    if not isinstance(text,str) or GUARD.search(text):
        return None
    m=RULE.match(text)
    if not m:
        return None
    return SIGN[m.group(2).lower()] * (-1 if m.group(1) else 1)

def proposition(case, role):
    # A claim can only be compared under independently supplied proposition scope.
    if case["stratum"]=="scope":
        return case["id"]+":"+("other" if role=="paraphrase" else "different" if role in ("opposite","protocol") else "anchor")
    return case["id"]

def scored_pair(case, role, baseline, sign_weight=2.0):
    a,b=sign(case["anchor"]),sign(case[role])
    if a is None or b is None or proposition(case,"anchor") != proposition(case,role):
        return None
    # No model or threshold fitting. These are illustrative structured scores.
    if sign_weight == 0:
        return baseline if a==b else -1.0
    return (baseline+sign_weight**2*a*b)/(1+sign_weight**2)

def summarize(rows):
    outcome={"cases":len(rows),"ordered":sum(x["ordered"] is True for x in rows),
             "ties_or_incorrect":sum(x["ordered"] is False for x in rows),
             "abstained":sum(x["ordered"] is None for x in rows)}
    assert sum(outcome[k] for k in ("ordered","ties_or_incorrect","abstained"))==outcome["cases"]
    return outcome

def evaluate(checkpoint:Path):
    all_cases=cases()
    frame=fixture_frame(all_cases)
    texts=[r["text"] for r in frame["rows"]]
    assert len(texts)==120 and all(r["split"]=="synthetic" for r in frame["rows"])
    # This baseline is fit on same synthetic text, not archival UN lexical geometry.
    sparse=TfidfVectorizer(ngram_range=(1,2),lowercase=True,norm="l2").fit_transform(texts)
    encoder=LocalModelEncoder(checkpoint)
    with tempfile.TemporaryDirectory() as d:
        observed=encode(frame,model_identity(),{"metric":"cosine","pooling":"upstream_chunk_token_weighted"},encoder,Path(d),batch_size=8)
    assert observed["coverage"]["encoded"]==len(texts),observed["coverage"]
    assert observed["coverage"]["not_fitted"]==0 and observed["coverage"]["failed_batches"]==0
    vectors={x["id"]:np.array(x["vector"],dtype=np.float64) for x in observed["rows"] if x["status"]=="encoded"}
    ix={r["id"]:i for i,r in enumerate(frame["rows"])}
    out=[]
    for case in all_cases:
        id=case["id"]
        pair={}
        for role in ROLES[1:]:
            anchor=id+":anchor";other=id+":"+role
            cosine=float(np.dot(vectors[anchor],vectors[other]))
            tfidf=float((sparse[ix[anchor]]@sparse[ix[other]].T).toarray()[0,0])
            pair[role]={"minilm":round(cosine,8),"lexical":round(tfidf,8),
                        "signed_minilm":None if (x:=scored_pair(case,role,cosine,0)) is None else round(x,8),
                        "signed_lexical":None if (x:=scored_pair(case,role,tfidf,2)) is None else round(x,8)}
        ordering={}
        for key in ("minilm","lexical","signed_minilm","signed_lexical"):
            a,b=pair["paraphrase"][key],pair["opposite"][key]
            ordering[key]=None if a is None or b is None else bool(a>b)
        out.append({"id":id,"stratum":case["stratum"],"pair_scores":pair,
                    "signs":{role:sign(case[role]) for role in ROLES},
                    "ordering":ordering})
    by_stratum={}
    for stratum,n in STRATA_COUNTS.items():
        rows=[r for r in out if r["stratum"]==stratum]
        by_stratum[stratum]={"families":n,"methods":{key:summarize([{"ordered":r["ordering"][key]} for r in rows]) for key in ("minilm","lexical","signed_minilm","signed_lexical")}}
    # 14 scored explicit/negated and 16 strict abstention families, no denominator loss.
    cue=[r for r in out if r["stratum"] in ("explicit","negated")]
    guards=[r for r in out if r["stratum"] not in ("explicit","negated")]
    safety={key:sum(all(r["pair_scores"][role][key] is None for role in ROLES[1:]) for r in guards)
            for key in ("signed_minilm","signed_lexical")}
    advance={}
    for key in safety:
        passed=sum(r["ordering"][key] is True for r in cue)
        advance[key]={"ordered":passed,"out_of":len(cue),"guard_abstentions":safety[key],
                      "guard_out_of":len(guards),"future_independent_synthetic_holdout_candidate":
                      passed>=13 and safety[key]>=15 and observed["coverage"]["failed_batches"]==0}
    return {"schema":PROTOCOL,"evaluation_role":"engineering_only","publication_eligible":False,
            "source_basis":"authored_synthetic_text_utf8","source_selection_sha256":frame["selection_sha256"],
            "checkpoint_revision":model_identity()["revision"],"representation_claim":"descriptive_only",
            "population":{"families":len(all_cases),"observations":len(texts),"cue_families":len(cue),
                          "guard_families":len(guards),"strata":STRATA_COUNTS},
            "coverage":{"attempted_encoder_rows":len(texts),"encoded":observed["coverage"]["encoded"],
                        "failed_batches":observed["coverage"]["failed_batches"],
                        "not_fitted":observed["coverage"]["not_fitted"]},
            "by_stratum":by_stratum,"advance":advance,"cases":out,
            "limitations":["These synthetic templates explicitly match handcrafted cue/parser design.",
                           "S1 and S2 share cue extraction and are not independent corroboration.",
                           "Fixed 2.0 signed coordinate is design choice, not fitted from text.",
                           "Proposition IDs are provided by artificial design, not inferred.",
                           "No blinded independent holdout, historical lexical transform or empirical diplomatic evaluation.",
                           "Do not use scores as government stance or publication evidence."]}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--checkpoint",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=evaluate(args.checkpoint)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({"population":result["population"],"coverage":result["coverage"],
                      "advance":result["advance"],"by_stratum":result["by_stratum"]},sort_keys=True))

if __name__=="__main__":
    main()
