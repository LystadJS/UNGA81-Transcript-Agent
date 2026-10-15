"""Offline, synthetic-only reproducibility and release safety checks."""
import hashlib
import json
import math
import re
from pathlib import Path

STATUSES = ("PASS", "FAIL", "NOT RUN", "NOT APPLICABLE")
HEX = re.compile(r"^[0-9a-f]{64}$")
SENTINELS = ("SYNTHETIC_PRIVATE_TRANSCRIPT_SENTINEL", "SYNTHETIC_SECRET_SENTINEL", "SYNTHETIC_CACHED_VECTOR_SENTINEL")

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def check_envelope(doc):
    errors = []
    if doc.get("schema") != "un.parallel-analysis.v1":
        errors.append("schema")
    upstream = doc.get("upstream") or {}
    for field in ("source_schema", "source_hash_basis"):
        if not upstream.get(field):
            errors.append("upstream." + field)
    if upstream.get("source_sha256") is None and not upstream.get("missing_reason"):
        errors.append("missing source identity reason")
    for field in ("source_sha256", "frame_sha256", "selection_sha256"):
        value = upstream.get(field)
        if value is not None and not HEX.fullmatch(str(value)):
            errors.append("invalid hash: " + field)
    cohort = doc.get("cohort") or {}
    if not cohort.get("population") or not cohort.get("unit"):
        errors.append("missing cohort identity")
    obs = doc.get("observations") or []
    ids = [o.get("id") for o in obs]
    if any(not x for x in ids) or len(set(ids)) != len(ids):
        errors.append("missing/duplicate observation id")
    for o in obs:
        if not HEX.fullmatch(str(o.get("text_sha256", ""))):
            errors.append("observation text hash")
        a,b=o.get("start"),o.get("end")
        if (a is None) != (b is None) or (a is not None and (not isinstance(a,int) or not isinstance(b,int) or a<0 or b<=a)):
            errors.append("offset bounds")
    models = doc.get("models") or []
    model_ids = [m.get("model_id") for m in models]
    if any(not x for x in model_ids) or len(set(model_ids)) != len(model_ids):
        errors.append("model identity")
    eligible = {o["id"] for o in obs if o.get("id") and not o.get("exclusion_reasons")}
    seen=set()
    for r in doc.get("results") or []:
        key=(r.get("model_id"),r.get("observation_id"))
        if key in seen: errors.append("duplicate model-observation result")
        seen.add(key)
        if key[0] not in model_ids or key[1] not in ids: errors.append("orphan result")
        status,cluster=r.get("status"),r.get("cluster")
        if status=="assigned" and (type(cluster)!=int or cluster<1): errors.append("assigned cluster")
        elif status=="unassigned" and cluster!=0: errors.append("unassigned cluster")
        elif status in ("excluded","not_fitted") and (cluster is not None or not r.get("reason")): errors.append("missing exclusion reason")
        elif status not in ("assigned","unassigned","excluded","not_fitted"): errors.append("result status")
        weights=r.get("memberships")
        if isinstance(weights,list) and weights and (any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in weights) or abs(sum(weights)-1)>1e-6):
            errors.append("membership normalization")
    for m in model_ids:
        if eligible and any((m,o) not in seen for o in eligible):
            errors.append("missing eligible result: "+str(m))
    if doc.get("publication_eligible") is not False or doc.get("evaluation_role")!="engineering_only":
        errors.append("release restriction")
    return sorted(set(errors))

def check_isolation(training, evaluation):
    if not training or not evaluation:
        return ["missing training/evaluation identities"]
    keys=("id","source_family_id","parent_id","text_sha256")
    errors=[]
    for key in keys:
        a={r.get(key) for r in training if r.get(key)}
        b={r.get(key) for r in evaluation if r.get(key)}
        if a & b: errors.append("leakage: "+key)
    return errors

def check_population(left,right):
    fields=("source_schema","source_hash_basis","source_sha256","selection_sha256")
    return ["incompatible "+k for k in fields if left.get(k)!=right.get(k)]

def check_replay(receipt, output):
    errors=[]
    for k in ("seed","runtime","dependency_versions","fixture_sha256","output_sha256"):
        if receipt.get(k) is None: errors.append("missing replay "+k)
    if receipt.get("output_sha256")!=sha256(output): errors.append("replay mismatch")
    return errors

def scan_public(root):
    root=Path(root)
    findings=[]
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink(): continue
        rel=path.relative_to(root).as_posix()
        if any(part in ("node_modules",".git") for part in path.parts): continue
        if path.suffix.lower() in (".npy",".npz",".pkl",".pickle",".safetensors",".pt",".bin"):
            findings.append((rel,"cached/binary research artifact"))
        if path.stat().st_size>5_000_000:
            findings.append((rel,"uninspected oversized artifact"))
            continue
        data=path.read_bytes()
        for marker in SENTINELS:
            if marker.encode() in data: findings.append((rel,"synthetic privacy sentinel"))
        if re.search(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",data):
            findings.append((rel,"private key"))
        if re.search(rb"gh[pousr]_[A-Za-z0-9]{30,}",data):
            findings.append((rel,"credential-shaped token"))
    return findings

def qa_summary(checks):
    if any(v not in STATUSES for v in checks.values()):
        raise ValueError("invalid QA status")
    return {"schema":"un.reproducibility-audit.v1","checks":checks,"release_authorized":False}
