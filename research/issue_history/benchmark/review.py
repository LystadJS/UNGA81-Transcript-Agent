"""Deterministic source-level holdouts and owner-review packet metadata."""
import hashlib

SPLIT_VERSION="source-hash-split-v1"

def split_for(source_id):
    # All revisions, sentences and countries from a source stay together.
    bucket=int(hashlib.sha256(source_id.encode()).hexdigest()[:8],16)%100
    return "train" if bucket<60 else "validation" if bucket<80 else "test"

def prepare(records):
    seen=set();items=[]
    for r in records:
        source=r.get("source_id") or r["id"].split("#")[0]
        key=(source,r["id"],r["text_sha256"])
        if key in seen: continue
        seen.add(key)
        items.append({"record_id":r["id"],"source_id":source,"text_sha256":r["text_sha256"],"date":r["date"],"split":split_for(source),"country":r.get("country"),"language":r.get("language"),"source_url":r["source_url"],"strata":{"year":r["date"][:4],"body":r.get("body","unknown"),"language":r.get("language","unknown"),"national_status":r.get("attribution",{}).get("country_status","unknown")},"annotation":None,"review_state":"unreviewed"})
    return {"schema":"un.issue-review-packet.v1","split_version":SPLIT_VERSION,"items":items,"human_confirmed_count":0,"acceptance":"withheld_until_owner_confirmation"}

def confirm(item,annotation,receipt):
    if not isinstance(receipt,str) or not receipt.strip(): raise ValueError("Explicit owner confirmation receipt required")
    if annotation.get("stance") not in ("support","oppose","qualified","unknown"): raise ValueError("Invalid stance")
    if annotation.get("attribution") not in ("national","collective","unclear"): raise ValueError("Invalid attribution")
    if not annotation.get("policy_id") or not annotation.get("context_id"): raise ValueError("Policy and context required")
    return {**item,"annotation":annotation,"review_state":"owner_confirmed","owner_confirmation_id":receipt}


def temporal_splits(records,train_end,validation_end):
    """Source-blocked temporal split; sources spanning boundaries are withheld."""
    from datetime import date
    date.fromisoformat(train_end);date.fromisoformat(validation_end)
    if train_end>=validation_end: raise ValueError("Temporal boundaries must increase")
    groups={}
    for r in records:
        date.fromisoformat(r["date"])
        source=r.get("source_id") or r["id"].split("#")[0]
        groups.setdefault(source,[]).append(r["date"])
    result={}
    for source,dates in groups.items():
        labels={"train" if d<=train_end else "validation" if d<=validation_end else "test" for d in dates}
        result[source]=next(iter(labels)) if len(labels)==1 else "withheld_cross_boundary"
    return {"version":"source-blocked-temporal-v1","train_end":train_end,"validation_end":validation_end,"sources":result}
