#!/usr/bin/env python3
"""Acquire ONLY the 28 pre-registered 2008-2015 PV quality-audit meetings.

Never accesses the separate 37 reserved October 2026 evaluation transcripts.
Only recipient-encrypted complete original PDF bytes leave this GitHub runner.
The source-audit roster remains withheld from all model selection and tuning.
"""
from __future__ import annotations
import argparse
import concurrent.futures
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import time
from urllib import error, parse, request
import zipfile

from encrypted_original_pv_intake import (
    freeze_symbols, official_url, seal, digest, MAX_BYTES, ALLOWED_HOSTS
)

SCHEMA="un.w4.p2.pre2016.independent-original-pv-quality-audit.private.v1"
PHASE="independent_source_auth_quality_audit"
MAX_WORKERS=4

def fetch_one(item):
    assert item["phase"]==PHASE and 2008<=item["year"]<=2015
    symbol=item["symbol"]
    url=official_url(symbol)
    failures=[]
    for attempt in range(2):
        try:
            req=request.Request(url,headers={
                "Accept":"application/pdf,application/octet-stream",
                "User-Agent":"Mozilla/5.0 UN-W4-independent-source-quality/0.1"
            })
            with request.urlopen(req,timeout=65) as response:
                final=response.geturl()
                if parse.urlsplit(final).hostname not in ALLOWED_HOSTS:
                    raise ValueError("unapproved_final_document_host")
                payload=response.read(MAX_BYTES+1)
            if len(payload)>MAX_BYTES:
                raise ValueError("source_document_oversized")
            if not payload.startswith(b"%PDF-") or b"%%EOF" not in payload[-4096:]:
                raise ValueError("invalid_or_incomplete_original_PDF")
            return symbol,payload,{
                "source":"original_UN_documents_un_org",
                "year":item["year"],
                "symbol":symbol,
                "download_url":url,
                "final_host":parse.urlsplit(final).hostname,
                "acquisition_utc":datetime.now(timezone.utc).isoformat(),
                "bytes":len(payload),
                "raw_complete_PDF_SHA256":digest(payload),
                "full_text_correspondence":"NOT_RUN_PENDING_INDEPENDENT_LOCAL_AUDIT",
                "source_quality_eligible_for_model_selection":False,
                "status":"downloaded_full_original_bytes_pending_local_independent_authentication"
            }
        except error.HTTPError as ex:
            failures.append("http_"+str(ex.code))
            if ex.code in (400,401,403,404,410):break
        except (error.URLError,TimeoutError,OSError,ValueError) as ex:
            failures.append(str(ex) if isinstance(ex,ValueError) else type(ex).__name__)
        if attempt==0:time.sleep(1)
    return symbol,None,{"symbol":symbol,"year":item["year"],
                        "status":"original_source_not_acquired",
                        "reason_codes":sorted(set(failures))}

def selftest():
    groups=freeze_symbols()  # Verifies exact SHA256 of the original committed audit split.
    audit=[g for g in groups if g["phase"]==PHASE]
    development=[g for g in groups if g["phase"]=="development_acquisition"]
    assert len(groups)==118 and len(audit)==28 and len(development)==90
    assert set(a["symbol"] for a in audit).isdisjoint(set(d["symbol"] for d in development))
    assert all(2008<=a["year"]<=2015 and a["symbol"].split("/")[1]==str(a["year"]-1945) for a in audit)
    assert all(official_url(a["symbol"]).startswith("https://documents.un.org/") for a in audit)
    assert all("2026" not in a["symbol"] and "A/81/" not in a["symbol"] for a in audit)
    print(json.dumps({"source_free_preflight":"PASS","audit_original_PV_meetings":len(audit),
                      "development_source_meetings_untouched":len(development),
                      "reserved_October_2026_meetings_opened":0,
                      "real_PDFs_read_in_selftest":0},sort_keys=True))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--recipient-public-key")
    p.add_argument("--sealed-output",type=Path)
    p.add_argument("--workers",type=int,default=4)
    a=p.parse_args()
    if a.selftest:
        selftest()
        return
    if not a.recipient_public_key or not a.sealed_output or not 1<=a.workers<=MAX_WORKERS:
        p.error("Use recipient public key, sealed-output, workers 1..4")
    all_groups=freeze_symbols()
    selected=[g for g in all_groups if g["phase"]==PHASE]
    assert len(selected)==28
    receipts=[]
    originals={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as executor:
        futures=[executor.submit(fetch_one,g) for g in selected]
        for f in concurrent.futures.as_completed(futures):
            symbol,data,receipt=f.result()
            receipts.append(receipt)
            if data is not None: originals[symbol]=data
    private_manifest={
        "schema":SCHEMA,
        "frozen_phase":"independent_source_auth_quality_audit",
        "original_selected":28,
        "original_development_meetings_reopened":0,
        "original_october_2026_reserved_meetings_opened":0,
        "original_heldout_source_use_for_model_selection":False,
        "acquisition_receipts":sorted(receipts,key=lambda x:(x["year"],int(x["symbol"].split(".")[-1]))),
        "no_UN_publisher_signed_SHA256_claim":True,
        "per_original_source_date_and_full_speech_checks":"NOT_RUN_UNTIL_PRIVATE_LOCAL_REPLAY"
    }
    memory=io.BytesIO()
    with zipfile.ZipFile(memory,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr("PRIVATE_28_original_PV_audit_manifest.json",json.dumps(private_manifest,indent=2,sort_keys=True))
        for symbol,data in sorted(originals.items()):
            z.writestr("independent_audit_original_PVs/"+symbol.replace("/","_")+".pdf",data)
    envelope=seal(memory.getvalue(),a.recipient_public_key)
    a.sealed_output.parent.mkdir(parents=True,exist_ok=True)
    with open(a.sealed_output,"xb") as f:f.write(envelope)
    yearly=[]
    for year in range(2008,2016):
        rows=[x for x in receipts if x["year"]==year]
        yearly.append({"year":year,"requested":len(rows),
                       "full_PDF_byte_downloads":sum(x["status"].startswith("downloaded_") for x in rows),
                       "acquisition_failures":sum(x["status"]=="original_source_not_acquired" for x in rows)})
    print(json.dumps({
        "schema":"un.w4.p2.independent-original-pv-download.aggregate.v1",
        "expected_meeting_symbols":28,"requested":len(receipts),
        "original_PDF_complete_bytes_acquired":len(originals),
        "failures":28-len(originals),
        "years":yearly,
        "sealed_artifact_bytes":len(envelope),"sealed_artifact_SHA256":digest(envelope),
        "source_quality_audit_only":True,
        "original_speech_to_Harvard_verification":"NOT_RUN",
        "source_model_fitting":"NOT_RUN",
        "original_development_meetings_opened":0,
        "original_2026_reserved_meetings_opened":0,
        "original_source_bytes_publicly_uploaded":0,
        "original_speech_text_publicly_uploaded":0,
        "public_empirical_release_eligible":False
    },sort_keys=True))
    if not originals:raise SystemExit("No audited original UN documents were acquired")

if __name__=="__main__":
    main()
