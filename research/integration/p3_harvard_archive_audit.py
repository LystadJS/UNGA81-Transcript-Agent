#!/usr/bin/env python3
"""Verify exact Harvard UNGDC v14 original archive without exporting speech text.

Works only with an explicitly supplied tar.gz (not an invented replacement).
Checks the previously accepted Dataverse-v14 publisher MD5, locally recorded
SHA-256, member path safety, duplicate country/session/year identities and
the 2016–2025 country-speech inventory. Output is public-safe aggregates.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile


ARCHIVE_MD5 = "81bdd06086d9e7c4e67026acb7325df3"
ARCHIVE_SHA256 = "55077dccf7242cdf544aa95c4797c68e443b0c37344c9c112a2e2392ddfcf8e5"
DATAVERSE_DOI = "doi:10.7910/DVN/0TJX8Y"
DATAVERSE_FILE_ID = 13591895
FILENAME = re.compile(r"^([A-Z]{3})_(\d{1,3})_(\d{4})\.txt$")


def digest_file(path: Path) -> tuple[str, str, int]:
    sha = hashlib.sha256()
    md5 = hashlib.md5(usedforsecurity=False)
    count = 0
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            sha.update(block)
            md5.update(block)
            count += len(block)
    return sha.hexdigest(), md5.hexdigest(), count


def verify(path: Path, *, expected_sha=ARCHIVE_SHA256,
           expected_md5=ARCHIVE_MD5, strict=True) -> dict:
    if not path.is_file() or path.is_symlink():
        raise ValueError("Original source archive file absent or symlinked")
    sha, md5, size = digest_file(path)
    if strict and (sha != expected_sha or md5 != expected_md5):
        raise ValueError("Exact Harvard v14 archive SHA256 or MD5 mismatch")
    if size > 500_000_000:
        raise ValueError("Harvard archive exceeds bounded input")
    counts = Counter()
    member_count = 0
    matched_ids = set()
    text_bytes = 0
    with tarfile.open(path, mode="r:gz") as archive:
        for member in archive:
            member_count += 1
            if member_count > 30_000:
                raise ValueError("Unexpectedly many tar members")
            name = PurePosixPath(member.name)
            if name.is_absolute() or ".." in name.parts or "\\" in member.name:
                raise ValueError("Archive path traversal")
            if member.issym() or member.islnk() or member.isdev():
                raise ValueError("Archive link or device prohibited")
            if not member.isfile():
                continue
            base = name.name
            if base.startswith("._") or "__MACOSX" in name.parts:
                continue
            m = FILENAME.fullmatch(base)
            if not m:
                continue
            iso, session, year = m.groups()
            year, session = int(year), int(session)
            if session != year - 1945:
                raise ValueError("Country-speech filename session/year conflict")
            if (iso, session, year) in matched_ids:
                raise ValueError("Duplicate Harvard country-session-year identity")
            matched_ids.add((iso, session, year))
            if member.size < 0 or member.size > 500_000:
                raise ValueError("Unexpected speech byte length")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("Unreadable country speech")
            raw = stream.read(member.size + 1)
            if len(raw) != member.size:
                raise ValueError("Truncated speech")
            text_bytes += len(raw)
            if 2016 <= year <= 2025:
                try:
                    raw.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise ValueError("Harvard text is not UTF-8") from exc
                counts[year] += 1

    in_window = sum(counts.values())
    if strict and in_window != 1926:
        raise ValueError(f"Published 2016–2025 v14 cohort count changed: {in_window}")
    if strict and any(y not in counts for y in range(2016, 2026)):
        raise ValueError("Expected annual Harvard source-year coverage missing")
    return {
        "schema": "un.harvard-v14.original-archive.audit.v1",
        "publisher": "Harvard Dataverse",
        "persistent_id": DATAVERSE_DOI,
        "datafile_id": DATAVERSE_FILE_ID,
        "archive_sha256": sha,
        "archive_md5": md5,
        "archive_compressed_bytes": size,
        "archive_sha256_matches_accepted_prior": sha == expected_sha,
        "archive_md5_matches_accepted_prior": md5 == expected_md5,
        "country_speech_text_files_total": len(matched_ids),
        "country_speeches_2016_2025": in_window,
        "country_speeches_by_year_2016_2025": {
            str(y): counts[y] for y in range(2016, 2026)
        },
        "tar_members_inspected": member_count,
        "individual_country_or_speaker_records_public": False,
        "source_text_artifact_published": False,
        "original_UN_PV_comparison_in_this_run": "NOT_RUN_NO_PRIVATE_PVS",
        "W1_real_source_frame_independently_validated": False,
        "W4_model_fit": "WITHHELD",
        "frozen_37_heldout_meetings_opened": 0,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--aggregate-output", type=Path)
    args = p.parse_args()
    result = verify(args.archive)
    data = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.aggregate_output:
        dest = args.aggregate_output
        if dest.exists() or dest.is_symlink():
            p.error("Refusing to overwrite existing archive audit receipt")
        dest.write_text(data, encoding="utf-8")
    else:
        print(data, end="")


if __name__ == "__main__":
    main()
