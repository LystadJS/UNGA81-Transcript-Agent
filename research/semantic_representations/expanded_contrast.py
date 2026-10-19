"""Prospective invented-text comparison: topical cosine is not stance inference.

No original UN inputs; no empirical model fitting or publication eligibility.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from fixtures import fixture_frame, CONTRASTS
from local_model import LocalModelEncoder, model_identity
from pipeline import encode, sha

# Fixed before execution; none selected on the previous four examples.
NEW = [
    ("education", "We support increasing school funding.", "Our delegation favors more resources for schools.", "We oppose increasing school funding.", "Thank you Chair; we oppose increasing school funding."),
    ("refugees", "We welcome additional refugee admissions.", "Our delegation favors accepting more displaced families.", "We reject additional refugee admissions.", "Thank you Chair; we reject additional refugee admissions."),
    ("oceans", "We support limits on deep sea mining.", "Our delegation favors restrictions on seabed extraction.", "We oppose limits on deep sea mining.", "Thank you Chair; we oppose limits on deep sea mining."),
    ("health", "We endorse expanding vaccine access.", "Our delegation favors broader availability of immunization.", "We reject expanding vaccine access.", "Thank you Chair; we reject expanding vaccine access."),
    ("debt", "We support restructuring sovereign debt.", "Our delegation favors renegotiating national borrowing obligations.", "We oppose restructuring sovereign debt.", "Thank you Chair; we oppose restructuring sovereign debt."),
    ("energy", "We support accelerating renewable energy deployment.", "Our delegation favors a faster shift to clean power.", "We oppose accelerating renewable energy deployment.", "Thank you Chair; we oppose accelerating renewable energy deployment."),
    ("cyber", "We endorse a ban on attacks against hospitals.", "Our delegation favors prohibiting cyber operations targeting medical facilities.", "We reject a ban on attacks against hospitals.", "Thank you Chair; we reject a ban on attacks against hospitals."),
    ("food", "We support emergency food assistance.", "Our delegation favors urgent aid to address hunger.", "We oppose emergency food assistance.", "Thank you Chair; we oppose emergency food assistance."),
    ("arms", "We support stricter arms export controls.", "Our delegation favors tighter rules for weapons shipments.", "We oppose stricter arms export controls.", "Thank you Chair; we oppose stricter arms export controls."),
    ("water", "We endorse protections for shared rivers.", "Our delegation favors safeguards for transboundary waterways.", "We reject protections for shared rivers.", "Thank you Chair; we reject protections for shared rivers."),
    ("labor", "We support stronger workplace safety standards.", "Our delegation favors better protections for workers.", "We oppose stronger workplace safety standards.", "Thank you Chair; we oppose stronger workplace safety standards."),
    ("heritage", "We endorse protecting cultural heritage sites.", "Our delegation favors safeguarding historical landmarks.", "We reject protecting cultural heritage sites.", "Thank you Chair; we reject protecting cultural heritage sites."),
]
ROLES = ("anchor", "paraphrase", "opposite", "protocol")
POLARITY = {"support":1,"endorse":1,"welcome":1,"favors":1,"oppose":-1,"reject":-1}

def polarity(text):
    words = re.findall(r"[a-z]+", text.lower())
    cues = [POLARITY[w] for w in words if w in POLARITY]
    return cues[-1] if len(set(cues)) == 1 else None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--checkpoint",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    cases=[*CONTRASTS,*[dict(zip(("id",)+ROLES, x)) for x in NEW]]
    ids=[c["id"] for c in cases]
    assert len(ids)==len(set(ids))==16
    frame=fixture_frame(cases)
    texts=[r["text"] for r in frame["rows"]]
    # One source-matched, development-only lexical fit, not a pre-existing archived reference.
    lexical=TfidfVectorizer(ngram_range=(1,2),norm="l2",lowercase=True).fit_transform(texts)
    enc=LocalModelEncoder(args.checkpoint)
    with tempfile.TemporaryDirectory() as tmp:
        out=encode(frame,model_identity(),{"metric":"cosine","pooling":"upstream_chunk_token_weighted"},enc,Path(tmp),batch_size=8)
        assert out["coverage"]["encoded"]==64 and out["coverage"]["not_fitted"]==0
        records={r["id"]:np.array(r["vector"],dtype=float) for r in out["rows"]}
        assert len(records)==64
        index={r["id"]:i for i,r in enumerate(frame["rows"])}
        results=[]
        for c in cases:
            key=c["id"]
            rows={}
            for role in ROLES[1:]:
                a,b=index[key+":anchor"],index[key+":"+role]
                rows[role]={
                  "minilm":round(float(np.dot(records[key+":anchor"],records[key+":"+role])),8),
                  "lexical_tfidf":round(float((lexical[a]@lexical[b].T).toarray()[0,0]),8)}
            # Explicit polarity cue is diagnostic only, not a trained stance model.
            pa=polarity(c["anchor"])
            cues={role:polarity(c[role]) for role in ROLES[1:]}
            results.append({"id":key,"comparisons":rows,"cue_anchor":pa,"cue_others":cues,
               "minilm_paraphrase_closer":rows["paraphrase"]["minilm"]>rows["opposite"]["minilm"],
               "lexical_paraphrase_closer":rows["paraphrase"]["lexical_tfidf"]>rows["opposite"]["lexical_tfidf"],
               "cue_contrast_detected":pa is not None and cues["paraphrase"]==pa and cues["opposite"]==-pa})
        summary={"schema":"un.semantic-contrast-development.v1","evaluation_role":"engineering_only","publication_eligible":False,
          "fixture_kind":"synthetic","cohort":"authored development examples","source_selection_sha256":frame["selection_sha256"],
          "model_revision":model_identity()["revision"],"assessed_cases":len(results),"original_cases":4,"new_cases":12,
          "observations":len(texts),"failures":out["coverage"]["failed_batches"],
          "minilm_order_pass":sum(x["minilm_paraphrase_closer"] for x in results),
          "lexical_order_pass":sum(x["lexical_paraphrase_closer"] for x in results),
          "polarity_cue_detected":sum(x["cue_contrast_detected"] for x in results),
          "limitations":["Authored synthetic cases are not a random independent holdout.",
            "TFIDF fitted on these same synthetic 64 strings, not the archived source lexical baseline.",
            "Lexical cue diagnostic is a narrow hand-specified contrast, not stance prediction.",
            "No thresholds tuned; no national position, policy alignment or significance inferred."],
          "results":results}
        args.output.write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n")
        print(json.dumps({k:v for k,v in summary.items() if k not in ("results","limitations")},sort_keys=True))

if __name__=="__main__":
    main()
