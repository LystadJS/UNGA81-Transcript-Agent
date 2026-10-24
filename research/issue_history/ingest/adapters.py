"""Strict normalized JSON adapter. Raw UN formats need dedicated verified adapters."""
import hashlib
import json
from datetime import date
from urllib.parse import urlparse

class SourceError(ValueError):
    pass

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def transcript_record(row):
    required=("id","date","country","language","text","text_sha256","source_url")
    if any(not isinstance(row.get(k),str) or not row[k] for k in required):
        raise SourceError("Missing normalized transcript fields")
    date.fromisoformat(row["date"])
    url=urlparse(row["source_url"])
    if url.scheme!="https" or not (url.hostname=="un.org" or (url.hostname or "").endswith(".un.org")):
        raise SourceError("Source must be a direct official HTTPS UN reference")
    if hashlib.sha256(row["text"].encode()).hexdigest()!=row["text_sha256"]:
        raise SourceError("Transcript text hash mismatch")
    if row.get("source_kind","un_statement")!="un_statement":
        raise SourceError("Official policy documents require a separate evidence channel")
    revision=digest({k:row.get(k) for k in sorted(row) if k not in ("fetched_at",)})
    return {**row,"source_id":row.get("source_id",row["id"]),"source_revision_id":row["id"]+"@"+revision,"source_kind":"un_statement"}

def vote_record(row):
    for k in ("resolution_id","resolution_version","stage","country_id","date","source_url"):
        if not isinstance(row.get(k),str) or not row[k].strip(): raise SourceError("Missing vote provenance: "+k)
    date.fromisoformat(row["date"])
    if row.get("vote") not in ("yes","no","abstain","absent","not_eligible","unknown"):
        raise SourceError("Unknown vote category; consensus must not become an individual yes")
    if row.get("stage") not in ("adopted_resolution","adopted_decision","draft_resolution","amendment","procedural"):
        raise SourceError("Unknown resolution stage")
    if (row["stage"]=="adopted_decision")!=row["resolution_id"].startswith("A/DEC/"): raise SourceError("Adopted decision stage requires an exact A/DEC source symbol")
    if row.get("eligible") is not None and type(row.get("eligible")) is not bool: raise SourceError("Invalid eligibility")
    if row["vote"]=="not_eligible" and row.get("eligible") is not False: raise SourceError("Non-eligibility requires explicit evidence")
    if row["vote"] in ("yes","no","abstain","absent") and row.get("eligible") is not True: raise SourceError("Recorded vote requires eligibility")
    url=urlparse(row["source_url"])
    if url.scheme!="https" or not (url.hostname=="un.org" or (url.hostname or "").endswith(".un.org")): raise SourceError("Invalid official vote source")
    return {**row,"source_kind":"un_vote","vote_id":digest(row)}


def bind_resolution(row):
    """Accept explicit reviewed bindings, never infer issue from a shared keyword."""
    required=("resolution_id","resolution_version","stage","policy_id","context_id","source_url","rationale","review_state")
    if any(not isinstance(row.get(k),str) or not row[k].strip() for k in required): raise SourceError("Incomplete policy binding provenance")
    if row["policy_id"] not in ("humanitarian_access","civilian_protection"): raise SourceError("Unsupported humanitarian policy")
    if row["stage"] not in ("adopted_resolution","adopted_decision","draft_resolution","amendment","procedural"): raise SourceError("Invalid binding stage")
    if (row["stage"]=="adopted_decision")!=row["resolution_id"].startswith("A/DEC/"): raise SourceError("Decision binding stage/source symbol mismatch")
    if row["review_state"] not in ("assistant_provisional","owner_confirmed"): raise SourceError("Unknown review state")
    if row["review_state"]=="owner_confirmed" and not row.get("owner_confirmation_id"): raise SourceError("Owner confirmation receipt required")
    url=urlparse(row["source_url"])
    if url.scheme!="https" or not (url.hostname=="un.org" or (url.hostname or "").endswith(".un.org")): raise SourceError("Invalid official binding source")
    if row.get("confidence") is not None and (type(row["confidence"]) not in (int,float) or not 0<=row["confidence"]<=1): raise SourceError("Invalid binding confidence")
    if row["context_id"] in ("unspecified","domestic"): comparable=False
    else: comparable=True
    return {**row,"binding_id":digest(row),"comparable":comparable,"ontology_version":"humanitarian-ontology-1"}


def vote_to_store(row,binding,source_id,source_revision):
    """Normalize a vote into the ledger without losing resolution identity."""
    vote=vote_record(row); bound=bind_resolution(binding)
    for key in ("resolution_id","resolution_version","stage"):
        if vote[key]!=bound[key]: raise SourceError("Vote/binding identity mismatch: "+key)
    if not source_id or not source_revision: raise SourceError("Canonical source identity and revision required")
    return {"id":digest([vote["vote_id"],bound["binding_id"],source_id,source_revision]),"source_id":source_id,"source_revision":source_revision,"country":vote["country_id"],"date":vote["date"],"policy":bound["policy_id"],"context":bound["context_id"],"vote":vote["vote"],"eligible":vote.get("eligible"),"resolution":vote["resolution_id"],"resolution_version":vote["resolution_version"],"stage":vote["stage"],"binding_id":bound["binding_id"],"binding_review_state":bound["review_state"]}
