"""Resumable bounded batches with quarantine; caller owns fetching and durable writes."""
from .adapters import digest

def run_batch(rows, adapter, persist, state=None, limit=100, max_attempts=3):
    if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=500: raise ValueError("Batch limit must be 1..500")
    if not isinstance(max_attempts,int) or isinstance(max_attempts,bool) or max_attempts<1: raise ValueError("Retry bound must be a positive integer")
    snapshot=digest(rows)
    state=state or {"snapshot":snapshot,"cursor":0,"accepted":0,"quarantine":[],"attempts":{}}
    if state["snapshot"]!=snapshot: raise ValueError("Input snapshot changed; start a new cursor")
    state={**state,"quarantine":list(state["quarantine"]),"attempts":dict(state["attempts"])}
    if not 0<=state["cursor"]<=len(rows): raise ValueError("Invalid cursor")
    processed=0
    while state["cursor"]<len(rows) and processed<limit:
        i=state["cursor"]; processed+=1
        try:
            item=adapter(rows[i])
        except (ValueError,TypeError,KeyError) as exc:
            state["quarantine"].append({"index":i,"row_sha256":digest(rows[i]),"reason":str(exc)[:200]})
            state["cursor"]+=1
            continue
        try:
            persist(item)
        except Exception:
            # Idempotent sink is required: retry may follow a committed write.
            key=str(i);state["attempts"][key]=state["attempts"].get(key,0)+1
            if state["attempts"][key]<max_attempts: break
            state["quarantine"].append({"index":i,"row_sha256":digest(rows[i]),"reason":"sink_failed_after_retries"})
            state["cursor"]+=1
            continue
        state["accepted"]+=1;state["cursor"]+=1
    state["complete"]=state["cursor"]==len(rows)
    state["coverage"]={"expected":len(rows),"processed":state["cursor"],"accepted":state["accepted"],"quarantined":len(state["quarantine"]),"remaining":len(rows)-state["cursor"]}
    return state


def run_checkpointed(rows,adapter,persist,checkpoint,limit=100,max_attempts=3):
    """Atomically persist a resumable metadata checkpoint after one bounded batch."""
    import json
    import os
    import tempfile
    from pathlib import Path
    path=Path(checkpoint)
    previous=json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    state=run_batch(rows,adapter,persist,previous,limit,max_attempts)
    path.parent.mkdir(parents=True,exist_ok=True)
    handle,name=tempfile.mkstemp(dir=path.parent,prefix=path.name+".",suffix=".tmp")
    try:
        with os.fdopen(handle,"w",encoding="utf-8",newline="\n") as stream:
            json.dump(state,stream,sort_keys=True,allow_nan=False)
            stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)
    return state
