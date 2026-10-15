#!/usr/bin/env python3
"""P0/P1 UN General Debate source inventory. No fit, held-out or public text export.

Pinned, allowlisted source files are read only when --download is explicit.
The original archive and person/source-linked tables stay OUTSIDE the git checkout.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import re
import sys
import tarfile
import unicodedata
import urllib.error
import urllib.request

YEARS_ALLOWED = tuple(range(2016, 2026))
CORPUS_URL = "https://dataverse.harvard.edu/api/access/datafile/13591895"
CORPUS_METADATA_URL = (
    "https://dataverse.harvard.edu/api/datasets/:persistentId/"
    "?persistentId=doi:10.7910/DVN/0TJX8Y"
)
OFFICIAL_URL = (
    "https://digitallibrary.un.org/record/4067189/files/"
    "GA_debate_speech_dataset_20260129.csv"
)
FILE_PATTERN = re.compile(r"^([A-Za-z]{3})_(\d{1,3})_(\d{4})\.txt$")
OFFICIAL_FIELDS = (
    "Name", "Salutation", "Member State", "GA Session", "Meeting Date",
    "Meeting Symbol", "Agenda Items", "UNDL ID", "UNDL Link"
)
REPO_ROOT = Path(__file__).resolve().parents[3]
# Exact-name overrides only; there is no fuzzy country-to-speaker matching.
ALIASES = {
    "bolivia plurinational state of": "BOL",
    "brunei darussalam": "BRN",
    "cabo verde": "CPV",
    "cape verde": "CPV",
    "cote d ivoire": "CIV",
    "democratic peoples republic of korea": "PRK",
    "democratic republic of the congo": "COD",
    "congo": "COG",
    "eswatini": "SWZ",
    "holy see": "VAT",
    "iran islamic republic of": "IRN",
    "korea republic of": "KOR",
    "lao peoples democratic republic": "LAO",
    "micronesia federated states of": "FSM",
    "moldova republic of": "MDA",
    "myanmar": "MMR",
    "north macedonia": "MKD",
    "palestine": "PSE",
    "state of palestine": "PSE",
    "russian federation": "RUS",
    "syrian arab republic": "SYR",
    "tanzania united republic of": "TZA",
    "timor leste": "TLS",
    "turkiye": "TUR",
    "united kingdom of great britain and northern ireland": "GBR",
    "united states of america": "USA",
    "venezuela bolivarian republic of": "VEN",
    "viet nam": "VNM",
}


class AcquisitionError(RuntimeError):
    """Unavailable, invalid or inconsistent archive; never infer completeness."""


def sha256_path(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def normalized_name(name: str) -> str:
    value = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    value = value.replace("’", "'").lower().replace("&", " and ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value)).strip()


def resolve_iso3(name: str) -> tuple[str | None, str]:
    norm = normalized_name(name)
    if norm in ALIASES:
        return ALIASES[norm], "declared_alias"
    try:
        import pycountry
    except ImportError as exc:
        raise AcquisitionError("pycountry is required for explicit ISO-3 resolution") from exc
    try:
        return pycountry.countries.lookup(name).alpha_3, "iso3166_exact_or_alias"
    except LookupError:
        return None, "unresolved_not_fuzzy_matched"


def download(url: str, destination: Path, max_bytes: int) -> dict:
    """Allowlisted HTTPS only; bound bytes, reject HTML error pages and partial files."""
    if url not in (CORPUS_URL, OFFICIAL_URL):
        raise AcquisitionError("Source URL is not on the fixed public-source allowlist")
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={
        "User-Agent": "UNGA81-historical-data-audit/0.1 (research, metadata and checksums)"
    })
    temporary = destination.with_suffix(destination.suffix + ".part")
    size = 0
    sha = hashlib.sha256()
    try:
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open("xb") as handle:
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                size += len(chunk)
                if size > max_bytes:
                    raise AcquisitionError("Downloaded source exceeds bounded file size")
                if size == len(chunk) and chunk.lstrip().lower().startswith((b"<!doctype html", b"<html")):
                    raise AcquisitionError("Archive endpoint returned HTML rather than a data file")
                handle.write(chunk)
                sha.update(chunk)
        if size < 100:
            raise AcquisitionError("Archive unexpectedly small")
        temporary.replace(destination)
        return {"status": "downloaded", "bytes": size, "sha256": sha.hexdigest()}
    except (OSError, urllib.error.URLError, AcquisitionError):
        temporary.unlink(missing_ok=True)
        raise


def dataverse_version_metadata() -> dict:
    """Best-effort version check. Failure never becomes an invented version claim."""
    try:
        request = urllib.request.Request(CORPUS_METADATA_URL, headers={
            "Accept": "application/json", "User-Agent": "UNGA81-historical-data-audit/0.1"
        })
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(io.TextIOWrapper(response, encoding="utf-8"))
        version = data["data"]["latestVersion"]
        files = [f for f in version.get("files", [])
                 if f.get("dataFile", {}).get("id") == 13591895]
        return {
            "status": "file_id_found_in_latest_published" if files else "file_id_not_in_latest_version",
            "dataset_version": "%s.%s" % (version.get("versionNumber"), version.get("versionMinorNumber")),
            "dataset_release_time": version.get("releaseTime"),
            "file_id": 13591895, "file_name": files[0]["dataFile"].get("filename") if files else None,
            "file_size": files[0]["dataFile"].get("filesize") if files else None,
            "file_checksum": files[0]["dataFile"].get("checksum") if files else None,
        }
    except (OSError, ValueError, KeyError, TypeError, urllib.error.URLError):
        return {"status": "metadata_not_verified", "dataset_version": None,
                "file_id": 13591895, "file_name": None, "file_checksum": None}


def corpus_inventory(tar_path: Path, selected_years: set[int]) -> tuple[list[dict], dict]:
    """Read approved years only. No extraction and no source text in returned index."""
    keys, issues = [], Counter()
    try:
        with tarfile.open(tar_path, mode="r:gz") as archive:
            for member in archive:
                if not member.isfile():
                    continue
                match = FILE_PATTERN.fullmatch(Path(member.name).name)
                if not match:
                    issues["nonmatching_tar_members"] += 1
                    continue
                iso3, session, year = match.group(1).upper(), int(match.group(2)), int(match.group(3))
                if year not in selected_years:
                    continue
                if session != year - 1945:
                    issues["session_year_conflicts"] += 1
                    continue
                if member.size <= 0 or member.size > 3_000_000:
                    issues["empty_or_oversized_source"] += 1
                    continue
                stream = archive.extractfile(member)
                if stream is None:
                    issues["unreadable_source_members"] += 1
                    continue
                hasher = hashlib.sha256()
                size = 0
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    hasher.update(block)
                    size += len(block)
                keys.append({"year": year, "session": session, "iso3": iso3,
                             "tar_member": member.name, "corpus_text_sha256": hasher.hexdigest(),
                             "text_bytes": size, "text_kind": "third_party_edited_transcript",
                             "independently_verified": False})
    except (tarfile.TarError, OSError, ValueError) as exc:
        raise AcquisitionError("Corpus is not a readable pinned tar.gz archive") from exc
    issues["indexed_corpus_members"] = len(keys)
    issues["duplicate_country_session_keys"] = sum(n - 1 for n in Counter(
        (x["session"], x["iso3"]) for x in keys).values() if n > 1)
    return keys, dict(issues)


def official_inventory(csv_path: Path, selected_years: set[int]) -> tuple[list[dict], dict]:
    """Parse UN authority metadata. Unverified person identities stay unverified."""
    rows, issues = [], Counter()
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not {"Name", "Member State", "GA Session"}.issubset(reader.fieldnames):
            raise AcquisitionError("Official speaker index missing critical expected CSV fields")
        issues["official_missing_optional_headers"] = len(set(OFFICIAL_FIELDS) - set(reader.fieldnames))
        for row in reader:
            try:
                session = int((row.get("GA Session") or "").strip())
            except ValueError:
                issues["official_session_invalid"] += 1
                continue
            year = session + 1945
            if year not in selected_years:
                continue
            iso, status = resolve_iso3((row.get("Member State") or "").strip())
            if iso is None:
                issues["official_country_unresolved"] += 1
            if not (row.get("Name") or "").strip():
                issues["official_speaker_name_missing"] += 1
            meeting = (row.get("Meeting Symbol") or "").strip()
            # Do not manufacture official symbols from date, year or meeting titles.
            if meeting and not re.fullmatch(r"A/\d{1,3}/PV\.\d+", meeting, re.IGNORECASE):
                issues["unusual_official_meeting_symbols"] += 1
            rows.append({"year": year, "session": session, "iso3": iso,
                         "resolution_kind": status, "original_member_state": row.get("Member State") or "",
                         "recorded_speaker_name": row.get("Name") or "",
                         "recorded_salutation": row.get("Salutation") or "",
                         "meeting_date": row.get("Meeting Date") or "",
                         "meeting_symbol": meeting or None,
                         "agenda_items": row.get("Agenda Items") or "",
                         "undl_id": row.get("UNDL ID") or "",
                         "undl_link": row.get("UNDL Link") or "",
                         "personal_identity_verified": False})
    issues["indexed_official_rows"] = len(rows)
    issues["multiple_speaker_rows_same_country_session"] = sum(n - 1 for n in Counter(
        (x["session"], x["iso3"]) for x in rows if x["iso3"]).values() if n > 1)
    return rows, dict(issues)


def csv_write(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("x", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_crosswalk(corpus: list[dict], official: list[dict],
                    years: list[int], private: Path, aggregate: Path) -> dict:
    """P0 candidate observed-union grid, NOT an authoritative membership census."""
    by_corpus = defaultdict(list)
    by_official = defaultdict(list)
    for row in corpus:
        by_corpus[(row["session"], row["iso3"])].append(row)
    for row in official:
        if row["iso3"]:
            by_official[(row["session"], row["iso3"])].append(row)
    # One observed candidate ISO3 anywhere, not a claimed UN membership roster.
    candidates = sorted({iso for _, iso in by_corpus} | {iso for _, iso in by_official})
    crosswalk, per_year = [], []
    for year in years:
        session = year - 1945
        entries = []
        for iso in candidates:
            cs, os_ = by_corpus.get((session, iso), []), by_official.get((session, iso), [])
            if year == 2025:
                status = "corpus_with_uncovered_official_index" if cs else "not_observed_index_out_of_scope"
            elif len(cs) > 1 or len(os_) > 1:
                status = "duplicate_or_multiple_record_needs_adjudication"
            elif cs and os_:
                status = "key_match_not_text_verified"
            elif cs:
                status = "corpus_only_no_official_key"
            elif os_:
                status = "official_only_no_corpus_text"
            else:
                status = "neither_observed_not_confirmed_absent"
            entries.append({"year": year, "session": session, "iso3": iso, "status": status,
                            "corpus_records": len(cs), "official_records": len(os_),
                            "meeting_symbol": os_[0]["meeting_symbol"] if len(os_) == 1 else None,
                            "undl_id": os_[0]["undl_id"] if len(os_) == 1 else None,
                            "original_member_state": os_[0]["original_member_state"] if len(os_) == 1 else None,
                            "corpus_text_sha256": cs[0]["corpus_text_sha256"] if len(cs) == 1 else None,
                            "original_un_document_sha256": None,
                            "reason_not_un_source_verified": "UN original/PV text not yet byte-verified"})
        crosswalk.extend(entries)
        stats = Counter(x["status"] for x in entries)
        per_year.append({
            "year": year, "session": session, "candidate_union_countries": len(candidates),
            "corpus_country_keys": len({k[1] for k in by_corpus if k[0] == session}),
            "official_country_keys": len({k[1] for k in by_official if k[0] == session}),
            "key_matches_not_text_verified": stats["key_match_not_text_verified"],
            "corpus_only_no_official_key": stats["corpus_only_no_official_key"],
            "official_only_no_corpus_text": stats["official_only_no_corpus_text"],
            "duplicate_or_multiple": stats["duplicate_or_multiple_record_needs_adjudication"],
            "corpus_with_uncovered_index": stats["corpus_with_uncovered_official_index"],
            "unobserved_not_confirmed_absent": (
                stats["neither_observed_not_confirmed_absent"] +
                stats["not_observed_index_out_of_scope"]),
            "official_index_scope": "not_published_in_20260129_index" if year == 2025 else "within_published_scope"
        })
    private.mkdir(parents=True, exist_ok=False)
    aggregate.mkdir(parents=True, exist_ok=False)
    csv_write(private / "corpus_members_private.csv",
              ["year", "session", "iso3", "tar_member", "corpus_text_sha256", "text_bytes",
               "text_kind", "independently_verified"], corpus)
    csv_write(private / "un_official_speakers_private.csv",
              ["year", "session", "iso3", "resolution_kind", "original_member_state",
               "recorded_speaker_name", "recorded_salutation", "meeting_date", "meeting_symbol",
               "agenda_items", "undl_id", "undl_link", "personal_identity_verified"], official)
    csv_write(private / "candidate_crosswalk_private.csv",
              ["year", "session", "iso3", "status", "corpus_records", "official_records",
               "meeting_symbol", "undl_id", "original_member_state", "corpus_text_sha256",
               "original_un_document_sha256", "reason_not_un_source_verified"], crosswalk)
    csv_write(aggregate / "per_year_aggregate.csv", list(per_year[0]), per_year)
    totals = Counter(x["status"] for x in crosswalk)
    return {"candidate_union_country_count": len(candidates),
            "candidate_grid_cells": len(crosswalk),
            "status_counts": dict(sorted(totals.items())),
            "per_year": per_year,
            "unresolved_official_country_rows": sum(x["iso3"] is None for x in official),
            "limitations": [
                "Observed-union candidates are not a verified UN membership census.",
                "Country-year key matches do not establish the exact original delivered text.",
                "Speaker names are recorded metadata, not independently authenticated people.",
                "2016–2024 official-index comparison only; the index excludes 2025.",
                "Unobserved country-years are unknown, not verified absence.",
                "No reserved October 5–6, 2026 source entered the 2016–2025 ingest window."
            ]}


def run(corpus_path: Path | None, official_path: Path | None, out: Path,
        years: list[int], allow_download: bool = False, *, version_query: bool = True) -> dict:
    out = out.resolve()
    if out == REPO_ROOT or REPO_ROOT in out.parents:
        raise AcquisitionError("Source acquisition output must stay outside the public git checkout")
    out.mkdir(parents=True, exist_ok=False)
    downloads = out / "downloaded_sources"
    downloads.mkdir()
    sources, failures = {}, {}
    for kind, supplied, url, name, limit in (
        ("harvard_corpus", corpus_path, CORPUS_URL, "UNGDC_1946-2025.tar.gz", 300_000_000),
        ("undl_official", official_path, OFFICIAL_URL, "GA_debate_speech_dataset_20260129.csv", 15_000_000),
    ):
        if supplied is not None:
            f = supplied.resolve()
            if not f.is_file():
                failures[kind] = "missing_local_source_file"
                continue
            sources[kind] = {"status": "supplied_local", "path": f,
                             "bytes": f.stat().st_size, "sha256": sha256_path(f), "url": url}
        elif allow_download:
            f = downloads / name
            try:
                result = download(url, f, limit)
                sources[kind] = {**result, "path": f, "url": url}
            except urllib.error.HTTPError as exc:
                failures[kind] = "http_status_" + str(exc.code)
            except urllib.error.URLError as exc:
                failures[kind] = "network_unavailable_" + type(exc.reason).__name__
            except (AcquisitionError, OSError) as exc:
                failures[kind] = "file_invalid_" + type(exc).__name__
        else:
            failures[kind] = "file_not_supplied_and_download_not_authorized"
    corpus, official = [], []
    cqa, oqa = {}, {}
    if "harvard_corpus" in sources:
        try:
            corpus, cqa = corpus_inventory(sources["harvard_corpus"]["path"], set(years))
        except AcquisitionError:
            failures["harvard_corpus"] = "downloaded_archive_failed_validation"
            del sources["harvard_corpus"]
    if "undl_official" in sources:
        try:
            official, oqa = official_inventory(sources["undl_official"]["path"], set(years))
        except (AcquisitionError, OSError, UnicodeError):
            failures["undl_official"] = "downloaded_csv_failed_validation"
            del sources["undl_official"]
    # Aggregate only if at least one source was acquired. Never manufacture both-source matches.
    crosswalk = None
    if sources:
        crosswalk = build_crosswalk(corpus, official, years, out / "private",
                                    out / "public_aggregate")
    metadata = dataverse_version_metadata() if allow_download and version_query and "harvard_corpus" in sources else {
        "status": "not_queried", "file_id": 13591895, "dataset_version": None
    }
    status = "both_sources_indexed_not_originally_verified" if len(sources) == 2 else (
        "partial_only_no_independent_reconciliation" if sources else "blocked_no_sources")
    manifest = {
        "schema": "un.p0p1.general-debate-acquisition.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "requested_years": years, "status": status,
        "dataverse_version_check": metadata,
        "sources": {k: {x: v for x, v in s.items() if x != "path"} for k, s in sources.items()},
        "failures": failures, "corpus_quality": cqa, "official_quality": oqa,
        "crosswalk": crosswalk,
        "independent_text_verification_complete": False,
        "independent_speaker_identity_verification_complete": False,
        "authoritative_member_state_census_verified": False,
        "statistical_inference_eligible": False, "publication_eligible": False,
        "privacy": "No full text or source-linked row-level table is permitted in public GitHub.",
        "source_license": "UN metadata: copyright United Nations, non-commercial attribution; verify corpus terms.",
        "holdout_access": False,
    }
    (out / "acquisition_manifest_private.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    public = {k: v for k, v in manifest.items() if k not in ("sources", "crosswalk")}
    public["source_digest_receipts"] = {k: {"status": s["status"], "sha256": s["sha256"], "bytes": s["bytes"]}
                                        for k, s in sources.items()}
    public["crosswalk_aggregate"] = None if crosswalk is None else {
        k: v for k, v in crosswalk.items() if k in (
            "candidate_union_country_count", "candidate_grid_cells", "status_counts", "per_year",
            "unresolved_official_country_rows", "limitations")}
    public_dir = out / "public_aggregate"
    public_dir.mkdir(exist_ok=True)
    (public_dir / "acquisition_receipt.json").write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    return public


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, help="Locally acquired pinned tar.gz")
    parser.add_argument("--official", type=Path, help="Locally acquired UN speaker-index CSV")
    parser.add_argument("--download", action="store_true", help="Fetch both pinned, allowlisted public URLs")
    parser.add_argument("--out", type=Path, required=True, help="New PRIVATE output directory outside git")
    parser.add_argument("--start-year", type=int, default=2016)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--skip-version-query", action="store_true")
    args = parser.parse_args()
    if not (2016 <= args.start_year <= args.end_year <= 2025):
        parser.error("Strict historical window is 2016–2025; excludes all October 2026 held-out material")
    os.umask(0o077)
    try:
        report = run(args.corpus, args.official, args.out,
                     list(range(args.start_year, args.end_year + 1)), args.download,
                     version_query=not args.skip_version_query)
    except (AcquisitionError, OSError) as exc:
        print(json.dumps({"status": "blocked", "error": type(exc).__name__,
                          "detail": str(exc)[:200], "holdout_access": False}))
        return 2
    print(json.dumps({
        "schema": report["schema"], "status": report["status"],
        "source_statuses": {k: v["status"] for k, v in report.get("source_digest_receipts", {}).items()},
        "failures": report["failures"],
        "per_year": report.get("crosswalk_aggregate", {}).get("per_year", []) if report.get("crosswalk_aggregate") else [],
        "independent_text_verification_complete": False, "publication_eligible": False,
        "holdout_access": False
    }))
    return 0 if report["status"] == "both_sources_indexed_not_originally_verified" else 3


if __name__ == "__main__":
    sys.exit(main())
