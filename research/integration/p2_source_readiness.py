#!/usr/bin/env python3
"""Independently audit *metadata* for the real historical W4 P2 source cohort.

There are two separate gates:
  1. Aggregate-only: public internal consistency, NOT real-PDF byte replay.
  2. Private CSV+PDF: validate local P2 worksheet export and optionally reopen
     original UN PDF bytes, never print source/person/country rows or access
     the frozen 37 October 5–6 2026 meeting transcripts.

No model is fit, no source text is extracted, and no release flag is changed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import re
from statistics import median
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "docs/parallel-work/W4_P2_FULL_ORIGINALS_AGGREGATE_2026-10-08.json"
PV_SYMBOL = re.compile(r"^A/([0-9]{2})/PV\.([0-9]+)$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
ISO3 = re.compile(r"^[A-Z]{3}$")
CSV_TABS = (
    "Annual Verification",
    "Original PDF Manifest",
    "Stratified 120",
    "W4 Candidate 99",
    "Wrong PV Controls",
    "Priority 24",
)


class SourceGateError(ValueError):
    """A source or validation condition is not established."""


def require(ok: bool, why: str) -> None:
    if not ok:
        raise SourceGateError(why)


def private_path(value: Path, *, file: bool) -> Path:
    path = value.expanduser().absolute()
    require(not path.resolve().is_relative_to(ROOT.resolve()),
            "Historical private input/output must remain outside the public repository")
    require(not path.is_symlink(), "Symlinked private source is not authorized")
    require(path.is_file() if file else path.is_dir(), "Expected private file/directory is absent")
    return path


def read_public() -> dict:
    obj = json.loads(PUBLIC.read_text(encoding="utf8"))
    require(obj["schema"] == "un.w4.p2.full_original_pv.aggregate.v1",
            "Unrecognized prior aggregate provenance")
    return obj


def aggregate_invariants(a: dict) -> dict:
    original = a["official_originals"]
    comparison = a["comparison"]
    candidate = a["candidate"]
    sample = a["sample"]
    priority = a["priority"]
    controls = a["controls"]
    require(original["meetings"] == sum([7, 9, 6, 7, 7, 7, 7, 5, 8]) == 63,
            "Annual original-PV meeting count incompatible with aggregate")
    require(original["pages"] == 3370 and original["total_pdf_bytes"] == 53218960,
            "Original-PV page/byte inventory differs from accepted P2")
    require(len(comparison["years"]) == 9 and
            comparison["years"] == list(range(2016, 2025)),
            "Historical year range changed")
    require(sum(comparison["strong_counts_by_year"]) == comparison["strong_2016_2023"] == 840,
            "Source-strong year sum changed")
    require(comparison["strong_counts_by_year"][-1] == 0 and
            comparison["partial_2024"] + comparison["insufficient_2024"] == 144,
            "Non-comparable 2024 modality must remain excluded")
    require(candidate["country_affiliations"] == 99 and
            candidate["eight_year_country_slots"] == 99 * 8 == 792 and
            candidate["source_strong_matched_slots"] == 523 and
            candidate["not_verified_slots"] == 269 and
            523 + 269 == 792, "Country×year source coverage changed")
    require(candidate["minimum_verified_years_per_epoch"] == 2 and
            SHA256.fullmatch(candidate["selection_sha256"]),
            "Candidate declared selection provenance missing")
    require(sample["preselected_risk_stratified_cells"] == 120 and
            sum(sample[k] for k in (
                "strong_matches", "partial_or_insufficient_matches",
                "harvard_missing", "pv_not_acquired")) == 120,
            "Review sample denominators changed")
    require(priority["triaged"] == 24 and
            priority["workbook_source_affiliation_corroborated"] == 14 and
            priority["UN_speaker_index_omissions_corroborated"] == 3 and
            priority["harvard_corpus_omission_in_original_PV"] == 1 and
            priority["unresolved_global_method_gates"] == 6 and
            14 + 3 + 1 + 6 == 24,
            "Priority source disposition totals changed")
    require(controls["wrong_same_year_original_pv_trials"] == 96 and
            controls["wrong_pass_strong_gate"] == 0 and
            0 <= controls["max_wrong_overlap"] < .90,
            "Original PV wrong-meeting negative control changed")
    require(a["privacy"]["original_37_reserved_meeting_reads"] == 0 and
            a["gates"]["W4_real_descriptive_fit"] == "WITHHELD" and
            a["gates"]["W4_calibrated_inference"] == "WITHHELD" and
            a["gates"]["publication_eligible"] is False,
            "An unapproved source, fit or release gate changed")
    return {
        "aggregate_source": "published P2 aggregate only",
        "original_pv_documents": 63,
        "original_pages_reported": 3370,
        "original_pdf_bytes_reported": 53218960,
        "strong_speech_original_meeting_correspondences_2016_2023": 840,
        "year_2024_strong": 0,
        "year_2024_noncomparable": 144,
        "unretrieved_candidate_originals": 752,
        "candidate_country_affiliations": 99,
        "candidate_year_slots": 792,
        "strong_source_matched_candidate_cells": 523,
        "not_source_verified_candidate_cells": 269,
        "negative_control_trials": 96,
        "negative_control_false_strong_matches": 0,
        "real_pdf_bytes_replayed_in_this_run": False,
        "private_speech_text_available": False,
        "W1_source_frame_eligible": False,
        "W4_descriptive_fit_eligible": False,
        "W4_inference_eligible": False,
        "publication_eligible": False,
        "reserved_37_meetings_opened": 0,
    }


def load_csvs(directory: Path) -> dict[str, list[dict]]:
    root = private_path(directory, file=False)
    out = {}
    for name in CSV_TABS:
        p = private_path(root / (name + ".csv"), file=True)
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            table = list(csv.DictReader(f))
        require(table and all(isinstance(row, dict) for row in table),
                "Malformed private worksheet CSV")
        out[name] = table
    return out


def years(value: str) -> list[int]:
    return [int(y) for y in value.split(";") if y.strip()]


def audit_tables(t: dict, a: dict) -> dict:
    original, annual = t["Original PDF Manifest"], t["Annual Verification"]
    panel = t["W4 Candidate 99"]
    sample = t["Stratified 120"]
    priority = t["Priority 24"]
    controls = t["Wrong PV Controls"]
    require(len(original) == 63 and len(annual) == 9 and len(panel) == 99 and
            len(sample) == 120 and len(priority) == 24 and len(controls) == 96,
            "Private worksheet cardinalities differ from declared aggregate")
    sym = set()
    digest = set()
    year_count = Counter()
    bytes_count = 0
    pages = 0
    for row in original:
        year = int(row["Year"])
        match = PV_SYMBOL.fullmatch(row["Official symbol"])
        require(2016 <= year <= 2024 and match and int(match.group(1)) == year - 1945,
                "Official PV symbol/session/year identity mismatch")
        require(row["Official symbol"] not in sym, "Duplicate original UN PV symbol")
        require(SHA256.fullmatch(row["Original PDF SHA-256"]),
                "Invalid original PDF SHA256 digest shape")
        require(row["Original PDF SHA-256"] not in digest, "Duplicate source PDF digest")
        url = urlparse(row["Original official URL"])
        require(url.scheme == "https" and url.hostname == "documents.un.org",
                "Nonofficial or insecure original-PV URL")
        sym.add(row["Official symbol"])
        digest.add(row["Original PDF SHA-256"])
        year_count[year] += 1
        bytes_count += int(row["Raw bytes"])
        pages += int(row["Pages"])
    require([year_count[y] for y in range(2016, 2025)] ==
            [7, 9, 6, 7, 7, 7, 7, 5, 8] and pages == a["official_originals"]["pages"] and
            bytes_count == a["official_originals"]["total_pdf_bytes"],
            "Private original-PV manifest counts/bytes contradict public receipts")

    require([int(x["Year"]) for x in annual] == list(range(2016, 2025)),
            "Source year annual inventory is not ordered 2016–2024")
    sums = {key: sum(int(x[key]) for x in annual) for key in (
        "Strong full texts", "Variant partial", "Insufficient text", "PV not yet reviewed")}
    require(sums == {
        "Strong full texts": 840, "Variant partial": 94,
        "Insufficient text": 50, "PV not yet reviewed": 752,
    }, "Annual full-text source-review totals differ from aggregate")
    require(int(annual[-1]["Strong full texts"]) == 0 and
            [int(x["Original PV documents"]) for x in annual] ==
            [year_count[y] for y in range(2016, 2025)],
            "2024 modality or official PV inventory was silently pooled")

    country_ids=set()
    prior = later = verified = unreviewed = 0
    for row in panel:
        name = row["ISO3"]
        require(ISO3.fullmatch(name) and name not in country_ids,
                "Duplicate/invalid country-affiliation key in private candidate")
        country_ids.add(name)
        p = years(row["Verified years"])
        missing = years(row["Unreviewed years"])
        require(len(set(p + missing)) == 8 and set(p + missing) == set(range(2016, 2024)),
                "Country-year missingness complement invalid or duplicated")
        pcount = sum(2016 <= y <= 2019 for y in p)
        lcount = sum(2020 <= y <= 2023 for y in p)
        require(pcount == int(row["Prior verified"]) >= 2 and
                lcount == int(row["Later verified"]) >= 2 and
                len(p) == int(row["Total verified"]),
                "Wrong split-year count or one-sided country selection")
        require(row["W4 eligible"].strip().lower() == "false",
                "Candidate cannot be called model-eligible before W1 and feature fit")
        prior += pcount; later += lcount
        verified += len(p); unreviewed += len(missing)
    require((prior,later,verified,unreviewed) == (252,271,523,269),
            "Original-PV-verified country×year totals differ")
    sample_tally = Counter(r["Official full-PV check"] for r in sample)
    require(dict(sample_tally) == {
        "strong_full_speech_content_correspondence": 69,
        "no_official_source_download_for_sample_cell": 38,
        "insufficient_full_speech_text_overlap": 6,
        "no_corpus_text_for_comparison": 1,
        "partial_or_variant_transcription": 6,
    }, "Private sample disposition changed or missing was coded as zero")
    flags = Counter(r["Source adjudication"] for r in priority)
    require(dict(flags) == {
        "SOURCE_AUTHORITY_COUNTRY_AND_RECORDED_SPEAKER_CORROBORATED": 14,
        "CONFIRMED_UN_SPEAKER_INDEX_OMISSION_NOT_SPEECH_ABSENCE": 3,
        "CONFIRMED_HARVARD_CORPUS_TEXT_OMISSION_WITH_OFFICIAL_PV_PRESENT": 1,
        "UNRESOLVED_NEEDS_DOCUMENT_OR_MODALITY_REVIEW": 3,
        "GLOBAL_VALIDATION_GATE_STILL_OPEN": 3,
    }, "Private priority review categories do not reconcile")
    wrong = [float(x["Wrong 7gram overlap"]) for x in controls]
    require(len(wrong) == 96 and min(wrong) >= 0 and max(wrong) <= .02793 + 1e-7,
            "Wrong-document control overlap exceeds observed maximum")
    require(all(x < .9 for x in wrong), "At least one false strong original-PV match")

    return {
        "private_worksheet_tables_evaluated": len(CSV_TABS),
        "original_pdf_manifest_rows": len(original),
        "original_pdf_digests_shape_verified": len(digest),
        "original_pdf_source_urls_approved_domain": len(original),
        "candidate_affiliations": len(country_ids),
        "prior_verified": prior,
        "later_verified": later,
        "candidate_source_verified": verified,
        "candidate_unreviewed": unreviewed,
        "original_pdf_byte_digest_replay": "NOT_RUN_NO_PRIVATE_PDF_MAP",
        "original_pdf_publisher_signed_hash": "UNAVAILABLE",
        "speech_text_sha256_available": False,
        "speaker_identity_verified": False,
        "W1_source_frame_eligible": False,
        "W4_descriptive_fit_eligible": False,
        "publication_eligible": False,
        "reserved_37_meetings_opened": 0,
    }


def check_original_pdf_bytes(private_csv_dir: Path, pdf_map: Path, tables: dict) -> int:
    """PDF map is private JSON {original PV symbol: local PDF path}; no text extraction."""
    map_path = private_path(pdf_map, file=True)
    mapping = json.loads(map_path.read_text(encoding="utf8"))
    records = tables["Original PDF Manifest"]
    require(isinstance(mapping, dict) and
            set(mapping) == {r["Official symbol"] for r in records},
            "Incomplete original-PV PDF path inventory")
    completed=0
    for row in records:
        path = private_path(Path(mapping[row["Official symbol"]]), file=True)
        require(path.suffix.lower() == ".pdf", "Original PV mapping has a non-PDF file")
        h = hashlib.sha256()
        total=0
        with path.open("rb") as file:
            while chunk := file.read(1024 * 1024):
                total += len(chunk)
                h.update(chunk)
        require(total == int(row["Raw bytes"]) and
                h.hexdigest() == row["Original PDF SHA-256"],
                "Original UN-PV private byte digest/length mismatch")
        completed += 1
    return completed


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-csv-dir", type=Path)
    p.add_argument("--private-pdf-map", type=Path)
    p.add_argument("--private-output", type=Path)
    args = p.parse_args()
    public = read_public()
    result = aggregate_invariants(public)
    if args.private_pdf_map and not args.private_csv_dir:
        p.error("An original-PV byte audit requires the private worksheet CSVs")
    if args.private_csv_dir:
        t = load_csvs(args.private_csv_dir)
        result.update(audit_tables(t, public))
        if args.private_pdf_map:
            count = check_original_pdf_bytes(args.private_csv_dir, args.private_pdf_map, t)
            result["original_pdf_byte_digest_replay"] = "PASS_LOCAL_MATCH_TO_WORKSHEET"
            result["original_pdf_bytes_replayed_in_this_run"] = True
            result["original_pdf_count_replayed"] = count
        result["aggregate_source"] = "authorized private worksheet CSVs; no row output"
    else:
        result["private_worksheet_tables_evaluated"] = 0
        result["original_pdf_byte_digest_replay"] = "NOT_RUN_NO_PRIVATE_PDF_MAP"
    result["schema"] = "un.w4.p2.source-readiness.aggregate.v1"
    result["evaluation_role"] = "source_audit_only"
    result["scientific_claims_authorized"] = False
    result["unverified_source_cells_are_not_zero"] = True
    result["missing_source_and_modality_exclusions_preserved"] = True
    result["input_original_pdf_sha256_publisher_signed"] = False
    result["reserved_37_meetings_opened"] = 0
    result["publication_eligible"] = False
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.private_output:
        out = args.private_output.expanduser().absolute()
        require(not out.resolve().is_relative_to(ROOT.resolve()),
                "Private validation receipt cannot be written to public checkout")
        require(out.parent.is_dir() and not out.is_symlink(),
                "Private receipt parent missing or symlinked")
        with out.open("x", encoding="utf8") as f:
            f.write(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
