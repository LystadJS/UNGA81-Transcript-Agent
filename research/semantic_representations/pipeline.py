"""Offline, source-bound semantic representation research. Python 3.11+ stdlib core."""
import hashlib, json, math, os, pathlib, tempfile, unicodedata

SCHEMA = "un.semantic-representation.v1"
def canonical(x): return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
def digest(x): return hashlib.sha256(x if isinstance(x, bytes) else canonical(x)).hexdigest()
def normalize(text):
    if not isinstance(text, str): raise ValueError("text required")
    return unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n").strip()
def segments(text, max_chars=900):
    if max_chars < 1: raise ValueError("max_chars")
    text = normalize(text)
    return [text[i:i+max_chars] for i in range(0,len(text),max_chars)] or []
def validate(rows):
    if not rows: raise ValueError("empty observations")
    seen=set()
    for row in rows:
        if row["id"] in seen: raise ValueError("duplicate observation")
        seen.add(row["id"])
        if row["unit"] not in ("synthetic","passage","reviewed_speech","source_segment"): raise ValueError("unit")
        if digest(normalize(row["text"]).encode()) != row["text_sha256"]: raise ValueError("text checksum")
        if not row.get("source_sha256") or not row.get("selection_sha256") or not row.get("source_schema"): raise ValueError("missing source lineage")
def identity(rows, model):
    validate(rows)
    return digest({"model":model,"observations":[{k:r[k] for k in ("id","text_sha256","source_sha256","selection_sha256","source_schema","unit")} for r in rows]})
def encode(rows, model, encoder, cache_dir, max_chars=900, batch_size=16):
    validate(rows)
    if batch_size < 1: raise ValueError("batch_size")
    root=pathlib.Path(cache_dir); root.mkdir(parents=True,exist_ok=True)
    output=[]
    for row in rows:
        passages=segments(row["text"],max_chars)
        key=digest({"model":model,"text_sha256":row["text_sha256"],"source_sha256":row["source_sha256"],"selection_sha256":row["selection_sha256"],"unit":row["unit"],"max_chars":max_chars})
        path=root/(key+".json")
        if path.exists():
            record=json.loads(path.read_text())
            if record["key"]!=key or digest(record["vector"])!=record["vector_sha256"]: raise ValueError("corrupted cache")
        else:
            vectors=[]
            for i in range(0,len(passages),batch_size):
                vectors.extend(encoder(passages[i:i+batch_size]))
            if len(vectors)!=len(passages) or not vectors: raise ValueError("inference coverage")
            if len({len(v) for v in vectors})!=1 or any(not math.isfinite(float(x)) for v in vectors for x in v): raise ValueError("invalid vectors")
            # Character-weighted pooling, then L2 normalization.
            pooled=[sum(len(p)*float(v[j]) for p,v in zip(passages,vectors))/sum(map(len,passages)) for j in range(len(vectors[0]))]
            norm=math.sqrt(sum(x*x for x in pooled))
            if not norm: raise ValueError("zero vector")
            vector=[x/norm for x in pooled]
            record={"key":key,"vector":vector,"vector_sha256":digest(vector),"passage_count":len(passages)}
            fd,tmp=tempfile.mkstemp(dir=root)
            try:
                with os.fdopen(fd,"w") as f: json.dump(record,f,sort_keys=True)
                os.replace(tmp,path)
            finally:
                if os.path.exists(tmp): os.unlink(tmp)
        output.append({"id":row["id"],"text_sha256":row["text_sha256"],"source_sha256":row["source_sha256"],"unit":row["unit"],**record})
    return {"schema":SCHEMA,"representation_id":identity(rows,model),"model":model,"rows":output,"publication_eligible":False,"evaluation_role":"engineering_only"}
def compare(a,b,k=1):
    if a["schema"]!=SCHEMA or b["schema"]!=SCHEMA: raise ValueError("schema mismatch")
    if a["model"]==b["model"]: raise ValueError("expected distinct representations")
    aa=a["rows"]; bb=b["rows"]
    if len(aa)!=len(bb) or len(aa)<3 or not 1<=k<len(aa): raise ValueError("population or k mismatch")
    for x,y in zip(aa,bb):
        if any(x[field]!=y[field] for field in ("id","text_sha256","source_sha256","unit")): raise ValueError("source or observation mismatch")
    def neighbors(rows,i):
        v=rows[i]["vector"]
        if any(len(z["vector"])!=len(v) for z in rows): raise ValueError("dimension mismatch")
        return sorted((j for j in range(len(rows)) if j!=i),key=lambda j:(-sum(x*y for x,y in zip(v,rows[j]["vector"])),rows[j]["id"]))[:k]
    overlap=sum(len(set(neighbors(aa,i))&set(neighbors(bb,i))) for i in range(len(aa)))/(len(aa)*k)
    return {"n":len(aa),"k":k,"neighborhood_overlap":overlap,"missing_coverage":0,"interpretation":"geometry only; similarity is not diplomatic agreement"}
def fixture_encoder(passages):
    # Explicit deterministic TEST DOUBLE, not a semantic checkpoint.
    return [[float(len(p)),float(sum(map(ord,p))%997),float(p.count("not"))] for p in passages]
def interchange(result):
    return {"schema":SCHEMA,"representation_id":result["representation_id"],"observations":[{k:r[k] for k in ("id","text_sha256","source_sha256","unit","vector_sha256")} for r in result["rows"]],"publication_eligible":False,"evaluation_role":"engineering_only"}
