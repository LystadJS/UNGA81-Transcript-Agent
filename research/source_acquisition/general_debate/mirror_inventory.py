#!/usr/bin/env python3
"""PINNED THIRD-PARTY FALLBACK, 2016–2022 ONLY. Not UN official reconciliation.

Do not substitute this derived RDS mirror for Harvard v14 or the UN speaker CSV.
Never put the source, text, or source-linked row-level output in public GitHub.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.request

# Snapshot of Jihyeonbae/UNGDC/main inspected 2026-10-08. This is a derived
# corpus (reported 1946–2022), not original UN source bytes.
MIRROR_COMMIT = "62df50941fd7afc00cb75256e1f91fe1ae690011"
MIRROR_BLOB = "1325ee6b0d6ff2d8a85b11807a514b9fb7d86871"
MIRROR_URL = (
    "https://raw.githubusercontent.com/Jihyeonbae/UNGDC/"
    + MIRROR_COMMIT + "/data/interim/UNGDC.rds"
)
REPO_ROOT = Path(__file__).resolve().parents[3]
YEARS = tuple(range(2016, 2026))


class MirrorError(RuntimeError):
    """Mirror acquisition or release identity mismatch; fail closed."""


def checked_download(target: Path) -> dict:
    request = urllib.request.Request(MIRROR_URL, headers={
        "User-Agent": "UNGA81-general-debate-fallback/0.1",
    })
    digest = hashlib.sha256()
    size = 0
    temp = target.with_suffix(".part")
    try:
        with urllib.request.urlopen(request, timeout=120) as response, temp.open("xb") as output:
            while block := response.read(1024 * 1024):
                size += len(block)
                if size > 120_000_000:
                    raise MirrorError("Mirror larger than permitted pinned maximum")
                output.write(block)
                digest.update(block)
        if size < 1_000_000:
            raise MirrorError("Mirror unexpectedly small; reject.")
        git_digest = hashlib.sha1()
        git_digest.update(("blob %d\0" % size).encode("ascii"))
        with temp.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                git_digest.update(block)
        if git_digest.hexdigest() != MIRROR_BLOB:
            raise MirrorError("Mirror bytes differ from pinned Git blob identity")
        temp.replace(target)
        return {"sha256": digest.hexdigest(), "bytes": size,
                "verified_git_blob": True, "git_blob_sha1": MIRROR_BLOB}
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def inventory(source: Path, out: Path) -> dict:
    try:
        import pyreadr
    except ImportError as exc:
        raise MirrorError("Install pinned pyreadr dependency") from exc
    try:
        values = pyreadr.read_r(str(source))
        frame = next(iter(values.values()))
    except (OSError, ValueError, IndexError, StopIteration) as exc:
        raise MirrorError("RDS cannot be read; do not treat as valid corpus") from exc
    cols = {str(c).lower(): c for c in frame.columns}
    required = ("ccode_iso", "year", "session", "text")
    if not all(c in cols for c in required):
        raise MirrorError("RDS lacks expected country, session, year or transcript fields")
    counts = {year: {"year": year, "session": year - 1945, "mirror_rows": 0,
                     "distinct_iso3": 0, "invalid_country_code_rows": 0,
                     "duplicate_country_session": 0,
                     "mirror_scope": "reported_release_1946_2022" if year <= 2022
                                     else "outside_mirror_release_not_missing_speech"}
              for year in YEARS}
    keys: dict[int, set[str]] = {year: set() for year in YEARS}
    seen: dict[tuple[int, str], int] = {}
    errors = {"bad_numeric_year_or_session": 0, "session_year_mismatch": 0,
              "invalid_iso3": 0, "blank_text": 0, "outside_requested_2016_2025": 0,
              "outside_documented_2022_release": 0}
    private_rows, exceptions = [], []
    for row_index, row in frame.iterrows():
        try:
            year, session = int(row[cols["year"]]), int(row[cols["session"]])
        except (ValueError, TypeError):
            errors["bad_numeric_year_or_session"] += 1
            continue
        if year not in YEARS:
            errors["outside_requested_2016_2025"] += 1
            continue
        if year > 2022:
            errors["outside_documented_2022_release"] += 1
            continue
        if session != year - 1945:
            errors["session_year_mismatch"] += 1
            continue
        iso = str(row[cols["ccode_iso"]]).strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", iso):
            errors["invalid_iso3"] += 1
            counts[year]["invalid_country_code_rows"] += 1
            exceptions.append({"year": year, "session": session, "source_row": str(row_index),
                               "original_code": iso, "reason": "invalid_or_unresolved_iso3_format"})
            continue
        text = row[cols["text"]]
        if not isinstance(text, str) or not text.strip():
            errors["blank_text"] += 1
            continue
        raw = text.encode("utf-8")
        key = (year, iso)
        seen[key] = seen.get(key, 0) + 1
        keys[year].add(iso)
        counts[year]["mirror_rows"] += 1
        private_rows.append({
            "year": year, "session": session, "iso3": iso,
            "third_party_derived_text_sha256": hashlib.sha256(raw).hexdigest(),
            "text_bytes": len(raw), "official_source_hash": None,
            "speaker_id": None, "original_meeting_symbol": None,
            "verified_against_un": False
        })
    for year in YEARS:
        counts[year]["distinct_iso3"] = len(keys[year])
        counts[year]["duplicate_country_session"] = sum(
            max(0, n - 1) for (yr, _), n in seen.items() if yr == year
        )
    output = out / "private"
    output.mkdir()
    with (output / "third_party_mirror_rows_private.csv").open(
        "x", newline="", encoding="utf-8"
    ) as stream:
        names = list(private_rows[0]) if private_rows else [
            "year", "session", "iso3", "third_party_derived_text_sha256",
            "text_bytes", "official_source_hash", "speaker_id",
            "original_meeting_symbol", "verified_against_un"
        ]
        writer = csv.DictWriter(stream, fieldnames=names)
        writer.writeheader()
        writer.writerows(private_rows)
    with (output / "mirror_code_exceptions_private.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["year", "session", "source_row",
                                                    "original_code", "reason"])
        writer.writeheader()
        writer.writerows(exceptions)
    public = out / "public_aggregate"
    public.mkdir()
    with (public / "mirror_per_year_aggregate.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(next(iter(counts.values()))))
        writer.writeheader()
        writer.writerows(counts.values())
    return {"per_year": list(counts.values()), "quality": errors,
            "selected_rows": len(private_rows),
            "source_snapshot_rows": len(frame),
            "excluded_invalid_code_rows": len(exceptions),
            "selected_distinct_country_session_pairs": len(seen)}


def run(out: Path, *, source: Path | None = None) -> dict:
    out = out.resolve()
    if out == REPO_ROOT or REPO_ROOT in out.parents:
        raise MirrorError("Private source output under public GitHub checkout is prohibited")
    out.mkdir(parents=True, exist_ok=False)
    local = out / "downloaded_sources"
    local.mkdir()
    if source is None:
        rds = local / "UNGDC_1946_2022_derived_mirror.rds"
        source_status = "downloaded_pinned_third_party_mirror"
        source_record = checked_download(rds)
    else:
        rds = source.resolve()
        if not rds.is_file():
            raise MirrorError("Supplied local mirror not found")
        source_status = "supplied_local_mirror_not_git_blob_verified"
        source_record = {"sha256": hashlib.sha256(rds.read_bytes()).hexdigest(),
                         "bytes": rds.stat().st_size, "verified_git_blob": False}
    counts = inventory(rds, out)
    report = {
        "schema": "un.p0p1.third-party-mirror.v1",
        "status": source_status, "snapshot_commit": MIRROR_COMMIT,
        "source_url": MIRROR_URL, "source_git_blob_sha1": MIRROR_BLOB,
        "bytes": source_record["bytes"], "archive_sha256": source_record["sha256"],
        "git_blob_verified": source_record["verified_git_blob"],
        "source_kind": "third_party_derived_not_harvard_v14_and_not_original_un",
        "coverage": counts,
        "primary_harvard_version_verified": False,
        "independent_un_source_crosswalk_complete": False,
        "original_un_document_hashes_verified": False,
        "publication_eligible": False, "holdout_access": False,
        "limitations": [
            "Mirror README documents only through 2022, not 2023–2025; unknown not absent.",
            "Public Git blob byte identity authenticates the copy, not UN transcript fidelity.",
            "No independent official UN speaker index or person validation attached.",
            "No W4 longitudinal statistical inference is eligible from this source reconnaissance."
        ]
    }
    (out / "receipt_private.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    public_receipt = {k: v for k, v in report.items() if k != "source_url"}
    (out / "public_aggregate" / "mirror_receipt.json").write_text(
        json.dumps(public_receipt, indent=2) + "\n", encoding="utf-8"
    )
    return public_receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        r = run(args.out, source=args.source)
    except (OSError, ValueError, MirrorError) as exc:
        print(json.dumps({"status": "blocked", "reason": type(exc).__name__,
                          "detail": str(exc)[:180], "holdout_access": False}))
        return 3
    print(json.dumps({
        "status": r["status"], "source_kind": r["source_kind"],
        "archive_sha256": r["archive_sha256"],
        "selected_rows": r["coverage"]["selected_rows"],
        "per_year": r["coverage"]["per_year"],
        "publication_eligible": False, "holdout_access": False
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
