#!/usr/bin/env python3
"""W4 P1: retrieve predeclared 2008–2015 UN General Debate PV originals.

Strict ONLY session 63–70 official PVs. Does NOT access 2026 reserved meetings.
Selection is computed from the frozen hash split BEFORE source retrieval. The
working memory contains UN original PDF bytes but only authenticated X25519 /
AES-GCM sealed ZIP bytes are written to Actions artifacts. Country/speaker row
records and text are never uploaded, printed, or placed in public Git.
"""
from __future__ import annotations
import argparse,base64,collections,concurrent.futures,hashlib,io,json,math,os,re,time,urllib.error,urllib.parse,urllib.request,zipfile
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey,X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes,serialization

NAMESPACE="W4-EXT-AUDIT-20261013"
SPLIT_SHA256="9f82613e7057a66f9ca7ccb550fade49797d4457fd67ada2443ef6a00edb9ef5"
OFFICIAL_RANGES={2008:((5,16),),2009:((3,13),),2010:((11,12),(14,17),(19,24)),
                 2011:((11,13),(15,16),(18,30)),2012:((6,21),),2013:((5,10),(12,23)),
                 2014:((6,20),),2015:((13,28),)}
EXPECTED_DEV=90
EXPECTED_RESERVED=28
ALLOWED_HOSTS={"documents.un.org","digitallibrary.un.org"}
MAGIC=b"W4P1PV\x00\x01"
MAX_BYTES=25_000_000

def digest(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def freeze_symbols():
    all_groups=[]
    for year,segments in OFFICIAL_RANGES.items():
        items=[f"A/{year-1945}/PV.{number}" for lo,hi in segments for number in range(lo,hi+1)]
        ranked=sorted(items,key=lambda sym:(digest((NAMESPACE+"\x00"+str(year)+"\x00"+sym).encode()),sym))
        reserved=set(ranked[:max(1,math.ceil(.2*len(items)))])
        for sym in items:
            all_groups.append({"year":year,"symbol":sym,
                "phase":"independent_source_auth_quality_audit" if sym in reserved else "development_acquisition"})
    raw=json.dumps(all_groups,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    assert len(all_groups)==118 and digest(raw)==SPLIT_SHA256,"Index partition differs from preregistered SHA"
    assert sum(x["phase"]=="development_acquisition" for x in all_groups)==EXPECTED_DEV
    assert sum(x["phase"]=="independent_source_auth_quality_audit" for x in all_groups)==EXPECTED_RESERVED
    return all_groups

def official_url(symbol):
    if not re.fullmatch(r"A/(?:6[3-9]|70)/PV\.[1-9][0-9]?",symbol):
        raise ValueError("Only predeclared historical UN General Debate originals")
    return ("https://documents.un.org/api/symbol/access?"
            "l=en&s="+urllib.parse.quote(symbol,safe="")+"&t=pdf")

def fetch_document(item):
    symbol=item["symbol"];year=item["year"]
    assert item["phase"]=="development_acquisition"
    assert int(symbol.split("/")[1])==year-1945
    url=official_url(symbol)
    failures=[]
    for attempt in range(2):
        try:
            req=urllib.request.Request(url,headers={
                "Accept":"application/pdf,application/octet-stream",
                "User-Agent":"Mozilla/5.0 W4-P1-original-PV-source-research/0.1"})
            with urllib.request.urlopen(req,timeout=55) as resp:
                final=resp.url
                if urllib.parse.urlsplit(final).hostname not in ALLOWED_HOSTS:
                    raise ValueError("unsupported_redirect_host")
                data=resp.read(MAX_BYTES+1)
            if len(data)>MAX_BYTES:raise ValueError("oversized_PDF")
            if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-4096:]:
                raise ValueError("not_complete_original_PDF")
            return (symbol,data,{
                "symbol":symbol,"year":year,"source_url":url,
                "final_source_host":urllib.parse.urlsplit(final).hostname,
                "original_PDF_complete_header_eof":True,"original_PDF_bytes":len(data),
                "original_PDF_SHA256_raw_downloaded_bytes":digest(data),
                "original_PDF_first_page_symbol_checked":"NOT_RUN_OFFLINE_AFTER_DECRYPT",
                "original_PV_to_Harvard_text_comparison":"NOT_RUN_OFFLINE_AFTER_DECRYPT",
                "source_status":"original_bytes_locally_authenticated_pending_independent_document_crosscheck"
            })
        except urllib.error.HTTPError as e:
            failures.append("http_"+str(e.code))
            if e.code in (400,401,403,404,410):break
        except (urllib.error.URLError,TimeoutError,OSError,ValueError) as e:
            failures.append(type(e).__name__ if not isinstance(e,ValueError) else str(e))
        if attempt==0:time.sleep(1)
    return (symbol,None,{"symbol":symbol,"year":year,"source_status":"not_acquired",
            "failure_categories":sorted(set(failures))})

def seal(payload,public_key_b64):
    pubbytes=base64.b64decode(public_key_b64,validate=True)
    if len(pubbytes)!=32:raise ValueError("Invalid recipient public X25519 key length")
    pub=X25519PublicKey.from_public_bytes(pubbytes)
    ephemeral=X25519PrivateKey.generate()
    salt=os.urandom(16); nonce=os.urandom(12)
    key=HKDF(algorithm=hashes.SHA256(),length=32,salt=salt,
             info=b"W4-P1-2008-2015-original-PV-only").derive(ephemeral.exchange(pub))
    encoded=ephemeral.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)
    return MAGIC+encoded+salt+nonce+AESGCM(key).encrypt(nonce,payload,MAGIC)

def selftest():
    entries=freeze_symbols()
    assert len(set(x["symbol"] for x in entries))==118
    assert all(2008<=x["year"]<=2015 for x in entries)
    for invalid in ("A/81/PV.5","A/71/PV.8","A/63/PV.99","S/PV.1","../../other"):
        # The first three must be refused either by exact roster or session boundary.
        assert invalid not in {z["symbol"] for z in entries}
    assert all(official_url(x["symbol"]).startswith("https://documents.un.org/") for x in entries if x["phase"]=="development_acquisition")
    priv=X25519PrivateKey.generate()
    pub=base64.b64encode(priv.public_key().public_bytes(
        serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
    payload=b"fictional-unit-test-no-real-transcript"*40
    ciphertext=seal(payload,pub)
    assert not payload in ciphertext
    theirs=X25519PublicKey.from_public_bytes(ciphertext[8:40])
    key=HKDF(algorithm=hashes.SHA256(),length=32,salt=ciphertext[40:56],
        info=b"W4-P1-2008-2015-original-PV-only").derive(priv.exchange(theirs))
    assert AESGCM(key).decrypt(ciphertext[56:68],ciphertext[68:],MAGIC)==payload
    print(json.dumps({"fictional_controls":"PASS","frozen_split_sha256":SPLIT_SHA256,
        "predeclared_symbols":len(entries),"development":EXPECTED_DEV,
        "independent_source_audit":EXPECTED_RESERVED,"no_real_sources_read":True,
        "original_2026_reserved_reads":0}))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--public-recipient-key")
    p.add_argument("--sealed-output")
    p.add_argument("--workers",type=int,default=4)
    x=p.parse_args()
    if x.selftest:return selftest()
    if not x.public_recipient_key or not x.sealed_output or x.workers not in range(1,7):
        p.error("Recipient PUBLIC key, sealed output, 1..6 workers required")
    selected=[s for s in freeze_symbols() if s["phase"]=="development_acquisition"]
    rows=[];raw_files={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=x.workers) as pool:
        futures=[pool.submit(fetch_document,s) for s in selected]
        for fut in concurrent.futures.as_completed(futures):
            sym,payload,meta=fut.result()
            rows.append(meta)
            if payload is not None:raw_files[sym]=payload
    private_manifest={
        "schema":"un.w4.p1.2008-2015.original-PV-byte-authentication.private.v1",
        "p1_split_sha256":SPLIT_SHA256,
        "official_un_document_years":[2008,2009,2010,2011,2012,2013,2014,2015],
        "all_28_independent_audit_meetings_heldout_and_unread":True,
        "archive_receipts":sorted(rows,key=lambda z:(z["year"],int(z["symbol"].split(".")[-1]))),
        "publisher_signed_sha256_proof":False,
        "source_transcript_Harvard_full_speech_identity":"NOT_RUN",
        "reserved_october_2026_meetings_accessed":False
    }
    memory=io.BytesIO()
    with zipfile.ZipFile(memory,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        archive.writestr("P1_original_PV_private_manifest.json",json.dumps(private_manifest,sort_keys=True,indent=2))
        for sym,pdf in sorted(raw_files.items()):
            archive.writestr("original_UN_PV_development/"+sym.replace("/","_")+".pdf",pdf)
    encrypted=seal(memory.getvalue(),x.public_recipient_key)
    with open(x.sealed_output,"xb") as f:f.write(encrypted)
    yearly=[]
    for year in OFFICIAL_RANGES:
        each=[z for z in rows if z["year"]==year]
        yearly.append({"year":year,"requested":len(each),
                       "complete_original_PDF_bytes":sum(z["source_status"]!="not_acquired" for z in each),
                       "not_acquired":sum(z["source_status"]=="not_acquired" for z in each)})
    print(json.dumps({"schema":"un.w4.p1.original-pv-encrypted-actions.aggregate.v1",
        "source_index_split_sha256":SPLIT_SHA256,"development_original_PV_requested":len(selected),
        "independent_audit_PV_opened":0,"heldout_oct_2026_transcripts_opened":0,
        "original_PV_bytes_acquired":len(raw_files),"original_PV_failures":len(selected)-len(raw_files),
        "yearly":yearly,"sealed_original_bytes_sha256":digest(encrypted),
        "sealed_bytes":len(encrypted),"recipient_private_key_ever_uploaded":False,
        "raw_original_PDF_public_artifacts":0,"country_speech_rows_public":0,
        "new_speech_correspondences_verified":0,"empirical_release_eligible":False}))
    if not raw_files:raise SystemExit("No approved original-PV bytes available")

if __name__=="__main__":
    main()
