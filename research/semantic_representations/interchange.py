"""Private read-only consumers of accepted source interfaces; no browser writes."""
from __future__ import annotations
from pathlib import Path
from typing import Any

try:
    from .pipeline import (SCHEMA, _assert, _hash, _nonempty, _vector, digest,
                           frame_identity, eligible, validate_frame)
except ImportError:
    from pipeline import (SCHEMA, _assert, _hash, _nonempty, _vector, digest,
                          frame_identity, eligible, validate_frame)

LEXICAL = "un.lexical-saved-reference.v1"
READONLY = "un.semantic-readonly.v1"


def lexical_reference(frame: dict, saved: dict) -> dict:
    """Accept lexical vectors ONLY if extracted from an already source-bound saved fit.

    Deliberately does not vectorize text or refit PCA/LSA. No implicit alignment.
    """
    coverage=validate_frame(frame)
    _assert(saved.get("schema")==LEXICAL and saved.get("fit_source")=="archived_saved_fit", "lexical reference must be saved, never refit")
    _assert(saved.get("method") in {"tfidf", "pca", "lsa"}, "not a lexical baseline")
    _assert(saved.get("frame_sha256")==frame_identity(frame), "lexical frame population mismatch")
    for key in ("source_schema", "source_hash_basis", "source_sha256", "selection_sha256", "unit", "population"):
        _assert(saved.get(key)==frame[key], "lexical mismatch: "+key)
    for key in ("representation_id", "representation_basis_id", "fit_version", "parameters_sha256", "model_sha256"):
        _nonempty(saved.get(key),key)
    _assert(saved["representation_id"]==saved["representation_basis_id"], "wrong saved lexical basis")
    _hash(saved["parameters_sha256"], "saved parameters")
    _hash(saved["model_sha256"], "saved numerical transform")
    _assert(saved.get("source_observation_order")==[r["id"] for r in frame["rows"]], "saved observation order changed")
    vecs=saved.get("vectors")
    _assert(isinstance(vecs, list) and len(vecs)==coverage["eligible"], "saved lexical coverage mismatch")
    keys=[r["id"] for r in frame["rows"] if eligible(r)]
    _assert([v.get("id") for v in vecs]==keys, "lexical vector IDs/order mismatch")
    dim=None
    lookup={}
    for observed, reference in zip((r for r in frame["rows"] if eligible(r)),vecs):
        _assert(reference.get("text_sha256")==observed["text_sha256"] and reference.get("source_sha256")==observed["source_sha256"], "saved lexical text/source hash mismatch")
        raw=reference.get("vector")
        _assert(digest(raw)==reference.get("vector_sha256"), "lexical saved vector digest mismatch")
        unit=_vector(raw,dim)
        _assert(all(abs(x-y)<1e-8 for x,y in zip(unit,raw)), "lexical saved geometry not L2 normalized")
        dim=len(unit)
        lookup[reference["id"]]=unit
    rows=[]
    for row in frame["rows"]:
        vector=lookup.get(row["id"])
        rows.append({"id":row["id"],"source_id":row["source_id"],"source_sha256":row["source_sha256"],
                     "text_sha256":row.get("text_sha256"),"unit":row["unit"],
                     "status":"encoded" if vector is not None else "excluded" if row["source_status"]=="available" else "unavailable",
                     "vector":vector,"vector_sha256":digest(vector) if vector is not None else None,
                     "meeting_id":row.get("meeting_id"),"parent_id":row.get("parent_id"),
                     "source_family_id":row.get("source_family_id"),"reason":None if vector is not None else row.get("missing_reason")})
    coverage |= {"encoded":len(vecs),"not_fitted":0,"cache_hits":0,"cache_misses":0,
                 "attempted_batches":0,"successful_batches":0,"failed_batches":0}
    return {"schema":SCHEMA,"representation_id":saved["representation_id"],
            "representation_basis_id":saved["representation_basis_id"],"frame_sha256":frame_identity(frame),
            "source_schema":frame["source_schema"],"source_hash_basis":frame["source_hash_basis"],
            "source_sha256":frame["source_sha256"],"selection_sha256":frame["selection_sha256"],
            "split":frame["split"],"population":frame["population"],"unit":frame["unit"],
            "source_group_unit":frame["source_group_unit"],"weighting":frame["weighting"],
            "model":{"schema":"un.lexical-model-lock.v1","repository":saved["method"],"revision":saved["model_sha256"]},
            "settings":{"metric":"cosine","pooling":"saved_lexical","fit_version":saved["fit_version"],
                        "parameters_sha256":saved["parameters_sha256"]},
            "rows":rows,"coverage":coverage,"failure_ledger":[],
            "publication_eligible":False,"evaluation_role":"engineering_only"}


def readonly_browser(result: dict, public: bool = False) -> dict:
    """JSON metadata-only: source-bearing development records are never public."""
    _assert(result.get("schema")==SCHEMA and result.get("publication_eligible") is False, "untrusted result")
    if public:
        _assert(result.get("split")=="synthetic", "development metadata may not be made public")
    _assert(result.get("evaluation_role")=="engineering_only", "no release eligibility")
    _hash(result.get("frame_sha256"),"frame")
    seen=set()
    rows=[]
    for r in result["rows"]:
        _nonempty(r.get("id"),"row id")
        _assert(r["id"] not in seen,"duplicate row id")
        seen.add(r["id"])
        rows.append({k:r.get(k) for k in ("id", "source_id", "source_sha256", "text_sha256", "unit",
                                           "status", "vector_sha256", "meeting_id", "parent_id", "source_family_id", "reason")})
    _assert(len(rows)==result["coverage"]["frame_rows"], "readonly coverage mismatch")
    return {"schema":READONLY,"version":"1.0.0","source_schema":result["source_schema"],
            "frame_sha256":result["frame_sha256"],"source_hash_basis":result["source_hash_basis"],
            "source_sha256":result["source_sha256"],"selection_sha256":result["selection_sha256"],
            "representation_id":result["representation_id"],"representation_basis_id":result["representation_basis_id"],
            "unit":result["unit"],"split":result["split"],"coverage":result["coverage"],
            "rows":rows,"failure_ledger":result["failure_ledger"],
            "publication_eligible":False,"evaluation_role":"engineering_only",
            "limitations":["Vectors omitted; local private retrieval requires matching source and representation hashes.",
                           "Similarity does not demonstrate diplomatic agreement, position, causal influence, replication or significance.",
                           "Empty/missing source is unknown, not a zero substantive issue occurrence."]}


def check_parallel_v1(envelope: dict) -> dict:
    """Read-only structural and relational subset; coordinator schema remains authoritative.

    We refuse malformed input even if a downstream browser only needs row metadata.
    Call coordinator validate-contract.cjs as an additional integration gate.
    """
    _assert(isinstance(envelope,dict) and envelope.get("schema")=="un.parallel-analysis.v1" and
            envelope.get("publication_eligible") is False and envelope.get("evaluation_role")=="engineering_only", "unsafe upstream interchange")
    _assert(envelope.get("contract_version") == "1.0.0", "v1 contract mismatch")
    producer=envelope.get("producer",{})
    _assert(producer.get("workstream_id") in {"W1","W2","W3","W4","W5","W6","W7"}, "unregistered workstream")
    upstream=envelope.get("upstream",{})
    _assert(upstream.get("source_schema") in {"synthetic.v1","un.browser.corpus.v1","un.latent-comparison.v1","un.passage-corpus.v1","un.review.v1"}, "upstream source schema")
    _nonempty(upstream.get("source_hash_basis"),"upstream hash basis")
    _hash(upstream.get("selection_sha256"),"upstream selection")
    _hash(upstream.get("source_sha256"),"upstream source")
    cohort=envelope.get("cohort",{})
    _assert(cohort.get("split") in {"synthetic","development"}, "upstream holdout forbidden")
    observations=envelope.get("observations")
    models=envelope.get("models")
    results=envelope.get("results")
    coverage=envelope.get("coverage",{})
    _assert(isinstance(observations,list) and isinstance(models,list) and isinstance(results,list),"upstream arrays")
    ids=[o.get("id") for o in observations]
    _assert(len(set(ids))==len(ids), "duplicate upstream source IDs")
    model_ids=[m.get("model_id") for m in models]
    _assert(len(set(model_ids))==len(model_ids),"duplicate upstream model IDs")
    _assert(coverage.get("observations_total")==len(ids) and coverage.get("eligible",0)+coverage.get("excluded",0)==len(ids),"upstream denominator drift")
    _assert(coverage.get("eligible")==cohort.get("eligible"),"upstream eligible count drift")
    _assert(len(coverage.get("models",[]))==len(models),"missing coverage model")
    identity=set(ids); mids=set(model_ids); keys=set()
    for observation in observations:
        if observation.get("text_sha256") is not None:_hash(observation["text_sha256"],"upstream text identity")
        _assert(observation.get("unit")==cohort.get("unit"),"upstream unit drift")
        a,b=observation.get("start"),observation.get("end")
        _assert((a is None and b is None) or (type(a) is int and type(b) is int and 0<=a<b),"upstream Unicode offsets")
    for model in models:
        _nonempty(model.get("representation_id"),"model representation")
    for r in results:
        _assert(r.get("model_id") in mids and r.get("observation_id") in identity,"orphan result")
        key=(r["model_id"],r["observation_id"])
        _assert(key not in keys,"duplicate model-observation pair")
        keys.add(key)
        model=next(m for m in models if m["model_id"]==r["model_id"])
        _assert(r.get("representation_basis_id")==model["representation_id"],"wrong model representation basis")
        state=r.get("status")
        _assert(state in {"assigned","unassigned","not_fitted","excluded"},"invalid result status")
        label=r.get("cluster")
        _assert((state=="assigned" and type(label) is int and label>=1) or
                (state=="unassigned" and label==0) or
                (state in {"not_fitted","excluded"} and label is None and bool(r.get("reason"))), "bad assignment/noise/missing status")
    for m in coverage["models"]:
        _assert(m.get("model_id") in mids,"orphan coverage")
        _assert(m.get("assigned",0)+m.get("unassigned",0)+m.get("not_fitted",0)==m.get("eligible"),"fit eligible denominator")
        _assert(m.get("attempted_fits")==m.get("successful_fits",0)+m.get("failed_fits",0),"fit attempt denominator")
        _assert(m.get("excluded")==coverage["excluded"],"excluded denominator")
        for status in ("assigned","unassigned","not_fitted","excluded"):
            _assert(sum(r["status"]==status and r["model_id"]==m["model_id"] for r in results)==m.get(status,0),"upstream result state count mismatch")
        _assert(sum(r["model_id"]==m["model_id"] for r in results)==len(ids),"missing upstream result rows")
    return {"schema":"un.parallel-analysis.v1","observation_count":len(ids),"model_count":len(models),
            "upstream_sha256":digest(envelope),"read_only":True}
