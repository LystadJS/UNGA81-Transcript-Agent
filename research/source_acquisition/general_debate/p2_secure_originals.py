#!/usr/bin/env python3
"""Retrieve ONLY named 2016-2024 GA PV originals and seal their bytes for private verification.

No October 2026 meeting access, no transcript-derived inputs, no public raw PDF
artifacts, no storage credentials. The sealed artifact can be decrypted only by
the recipient's X25519 private key, which is never sent to GitHub Actions.
"""
from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time
from urllib.parse import quote
import urllib.error
import urllib.request
import zipfile

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import os

MAGIC = b"UNW4P2\x00\x01"
SYMBOL = re.compile(r"^A/(7[1-9])/PV\.([1-9][0-9]?)$")
MAX_BYTES = 25_000_000
SOURCE_HOSTS = ("documents.un.org", "digitallibrary.un.org")
FALLBACK = {
    "A/78/PV.11": (
        "https://digitallibrary.un.org/record/4037056/files/"
        "A_78_PV.11-EN.pdf"
    )
}


def document_urls(symbol):
    encoded = quote(symbol, safe="")
    primary = (
        "https://documents.un.org/api/symbol/access"
        "?l=en&s=" + encoded + "&t=pdf"
    )
    return [primary] + ([FALLBACK[symbol]] if symbol in FALLBACK else [])


def fetch_one(symbol):
    problems = []
    for url in document_urls(symbol):
        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "Mozilla/5.0 UN-research-source-audit/0.1",
                                  "Accept": "application/pdf,*/*"}
                )
                with urllib.request.urlopen(req, timeout=45) as response:
                    if response.geturl().split("/")[2].lower() not in SOURCE_HOSTS:
                        problems.append("unexpected_redirect_host")
                        break
                    payload = response.read(MAX_BYTES + 1)
                    status = response.status
                if len(payload) > MAX_BYTES:
                    problems.append("exceeds_max_bytes")
                    break
                if not payload.startswith(b"%PDF-") or b"%%EOF" not in payload[-4096:]:
                    problems.append("non_pdf_or_incomplete_http_" + str(status))
                    break
                # The PDF is fully downloaded and byte hashed before any text parsing.
                record = {
                    "symbol": symbol, "source_url": url,
                    "bytes": len(payload),
                    "original_pdf_sha256": hashlib.sha256(payload).hexdigest(),
                    "download_complete_pdf_header_and_eof": True,
                    "downloaded_utc": datetime.now(timezone.utc).isoformat(),
                }
                with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
                    tmp.write(payload)
                    tmp.flush()
                    try:
                        info = subprocess.run(
                            ["pdfinfo", tmp.name], capture_output=True, text=True,
                            timeout=25, check=True
                        )
                        m = re.search(r"^Pages:\s*(\d+)", info.stdout, re.M)
                        record["pages"] = int(m.group(1)) if m else None
                        text = subprocess.run(
                            ["pdftotext", "-enc", "UTF-8", tmp.name, "-"],
                            capture_output=True, timeout=35, check=True
                        ).stdout.decode("utf-8", "replace")
                        record["full_pdf_extracted_text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
                        record["extracted_chars"] = len(text)
                        record["extracted_text_available"] = len(text) >= 300
                        record["symbol_found_in_extracted_text"] = (
                            symbol.replace("/", "").replace(".", "").lower()
                            in re.sub(r"[^a-zA-Z0-9]", "", text[:3000]).lower()
                        )
                    except (subprocess.SubprocessError, FileNotFoundError) as exc:
                        record["extracted_text_available"] = False
                        record["extraction_error_kind"] = type(exc).__name__
                return symbol, payload, record
            except urllib.error.HTTPError as exc:
                problems.append("http_" + str(exc.code))
                if exc.code in (400, 401, 403, 404, 410):
                    break
            except (OSError, urllib.error.URLError, ValueError, TimeoutError) as exc:
                problems.append("transport_" + type(exc).__name__)
                if attempt == 0:
                    time.sleep(1)
    return symbol, None, {"symbol": symbol, "status": "not_acquired",
                           "reason_kinds": sorted(set(problems))}


def seal(data, recipient_public_key):
    pub = X25519PublicKey.from_public_bytes(base64.b64decode(recipient_public_key))
    ephemeral = X25519PrivateKey.generate()
    salt, nonce = os.urandom(16), os.urandom(12)
    aeskey = HKDF(algorithm=hashes.SHA256(), length=32, salt=salt,
                  info=b"UNGA81-W4-original-PV-v1").derive(ephemeral.exchange(pub))
    ciphertext = AESGCM(aeskey).encrypt(nonce, data, MAGIC)
    return (MAGIC + ephemeral.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw)
            + salt + nonce + ciphertext)


def selftest():
    private = X25519PrivateKey.generate()
    pub = base64.b64encode(private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode("ascii")
    original = b"synthetic-without-a-transcript" * 42
    sealed = seal(original, pub)
    eph = X25519PublicKey.from_public_bytes(sealed[8:40])
    key = HKDF(algorithm=hashes.SHA256(), length=32, salt=sealed[40:56],
               info=b"UNGA81-W4-original-PV-v1").derive(private.exchange(eph))
    assert AESGCM(key).decrypt(sealed[56:68], sealed[68:], MAGIC) == original
    print("PASS: synthetic in-memory sealed-envelope authenticated-encryption roundtrip")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", type=Path)
    parser.add_argument("--public-key")
    parser.add_argument("--sealed-output", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.symbols or not args.sealed_output or not args.public_key:
        parser.error("symbols, public-key, sealed-output required")
    if args.workers not in (1, 2, 3, 4):
        parser.error("workers must be 1..4")
    raw_symbols = [s.strip() for s in args.symbols.read_text().splitlines()
                   if s.strip() and not s.lstrip().startswith("#")]
    if (len(raw_symbols) != len(set(raw_symbols)) or
            not 1 <= len(raw_symbols) <= 90 or
            any(not SYMBOL.fullmatch(s) for s in raw_symbols)):
        parser.error("Nonunique/invalid list or forbidden period; ONLY GA sessions 71–79")
    records, pdfs = [], {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_one, symbol): symbol for symbol in raw_symbols}
        for fut in as_completed(futures):
            symbol, payload, record = fut.result()
            records.append(record)
            if payload is not None:
                pdfs[symbol] = payload
    manifest = {
        "schema": "un.w4.p2.original-pv-byte-audit.v1",
        "scope": "2016-2024_GA_PV_only",
        "source_system": "UN Official Document System / Dag Hammarskjold Digital Library",
        "records": sorted(records, key=lambda r: r["symbol"]),
        "reserved_2026_meetings_accessed": False,
        "original_bytes_only_inside_sealed_artifact": True,
        "original_transcript_text_publicly_exported": False,
        "harvard_corpus_text_compared": False,
    }
    # Container in-memory, no unencrypted ZIP uploaded to public artifacts.
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("original_pv_manifest_private.json",
                         json.dumps(manifest, indent=2, sort_keys=True))
        for symbol, data in sorted(pdfs.items()):
            archive.writestr("original_un_pvs/" + symbol.replace("/", "_") + ".pdf", data)
    args.sealed_output.parent.mkdir(parents=True, exist_ok=True)
    sealed = seal(memory.getvalue(), args.public_key)
    args.sealed_output.write_bytes(sealed)
    failures = [r for r in records if "original_pdf_sha256" not in r]
    print(json.dumps({
        "status": "original_UN_bytes_acquired_encrypted" if not failures
                  else "partial_original_UN_bytes_acquired_encrypted",
        "expected_meeting_documents": len(raw_symbols),
        "acquired_full_PDF_files": len(pdfs),
        "failed_files": len(failures),
        "extractable_document_count": sum(r.get("extracted_text_available", False) for r in records),
        "sealed_artifact_bytes": len(sealed),
        "sealed_artifact_sha256": hashlib.sha256(sealed).hexdigest(),
        "private_key_never_in_runner": True,
        "raw_PDF_public_uploads": 0,
        "heldout_2026_meeting_reads": 0,
        "harvard_corpus_comparison_in_runner": "NOT_RUN",
    }))


if __name__ == "__main__":
    main()
