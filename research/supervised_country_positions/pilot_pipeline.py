#!/usr/bin/env python3
"""Private source-verified supervised annotation pilot and grouped temporal split.

The tool never downloads a transcript, creates a human label, fits a model,
opens sealed meeting texts, or writes private evidence into public Git.
Only the explicit owner-reviewed draft can be counted as owner-attested review.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

import prepare_review as review

SCHEMA = "un.country-positions.pilot-plan.v1"
QUALITY_HEADERS = (
    "source_id official_document_symbol original_pdf_sha256 match_status "
    "source_method country_capacity source_family_id verification_basis"
).split()
SPLITS = ("train", "calibration", "test")
YEARS = {"train": (2016, 2019), "calibration": (2020, 2021), "test": (2022, 2023)}
SHARES = (0.60, 0.20, 0.20)
RESERVED = {"2026-10-05", "2026-10-06"}
OFFICIAL_HOSTS = {"digitallibrary.un.org", "documents.un.org", "gadebate.un.org"}
CUES = {
    "cub_embargo": ("cuba", "cuban", "embargo", "blockade", "havana",
                   "helms-burton"),
    "ukr_sovereignty": ("ukraine", "ukrainian", "crimea", "donbas",
                      "territorial integrity", "russian federation"),
}
PLAN_PROP_IDS = tuple(CUES)
FRAME_POLICY = "2016-2023_original_pv_strong_individual_english_v1"
HEX = re.compile(r"^[a-f0-9]{64}$")
PV = re.compile(r"^A/[0-9]{2,3}/PV\.[0-9]{1,4}$")
COUNTRY = re.compile(r"^[A-Z]{3}$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def write_new(path: Path, data: bytes) -> None:
    review.write_private(path, data)


def load_table(path: Path, headers: list[str]) -> list[dict[str, str]]:
    import csv
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == headers, "Unexpected headers in " + path.name)
        result = []
        for row in reader:
            require(len(result) < 100000, "Table resource limit exceeded")
            require(None not in row and all(v is not None for v in row.values()),
                    "Malformed CSV row in " + path.name)
            result.append(row)
    return result


def utc_date(value: str) -> str:
    require(isinstance(value, str), "Invalid date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Invalid ISO event date") from exc
    require(parsed.isoformat() == value, "Invalid event date format")
    return value


def source_is_official(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except (TypeError, ValueError):
        return False
    return (parsed.scheme == "https" and parsed.hostname in OFFICIAL_HOSTS
            and not parsed.username and not parsed.password)


def private_workspace(path: Path) -> Path:
    root = path.resolve()
    require(root.is_dir(), "Private source workspace is missing")
    require(root != review.REPOSITORY and review.REPOSITORY not in root.parents,
            "Private source workspace cannot be inside the public checkout")
    return root


def verified_plan(data: dict) -> dict:
    require(data.get("schema") == SCHEMA, "Unknown pilot-plan schema")
    claimed = data.get("plan_sha256")
    require(isinstance(claimed, str) and HEX.fullmatch(claimed),
            "Pilot plan lacks digest")
    body = {key: val for key, val in data.items() if key != "plan_sha256"}
    require(digest(stable(body)) == claimed, "Frozen pilot-plan digest mismatch")
    require(data.get("publication_eligible") is False and
            data.get("human_stance_labels") == 0 and
            data.get("evaluation_role") == "allocation_only",
            "Pilot plan is not a fitted or reviewed model")
    return data


def load_source_frame(workspace: Path) -> tuple[list[dict], dict[str, dict], dict[str, str]]:
    """Validate *metadata* first. Do not open excluded/held-out sources."""
    workspace = private_workspace(workspace)
    sources_path = workspace / "sources.csv"
    quality_path = workspace / "source_quality.csv"
    sources = load_table(sources_path, review.FIELDS["sources"].split())
    qualities = load_table(quality_path, QUALITY_HEADERS)
    q_index = {}
    for q in qualities:
        sid = q["source_id"]
        require(sid and sid not in q_index, "Repeated source_quality source_id")
        q_index[sid] = q
    ids = [s["source_id"] for s in sources]
    require(all(ids) and len(set(ids)) == len(ids), "Missing/duplicate source IDs")
    require(set(q_index).issubset(set(ids)), "Quality ledger has unregistered source")
    return sources, q_index, {
        "sources_csv_sha256": digest(sources_path.read_bytes()),
        "source_quality_csv_sha256": digest(quality_path.read_bytes())
    }


def classify_source(src: dict, quality: dict | None) -> str | None:
    """The source validator does not independently authenticate human identity."""
    date_str = utc_date(src["event_date"])
    if date_str in RESERVED:
        return "reserved_meeting_metadata_only"
    year = int(date_str[:4])
    if year < 2016 or year > 2023:
        return "out_of_comparable_period"
    require(COUNTRY.fullmatch(src["iso3"]) is not None, "Invalid country ISO3")
    if src["genre"] != "general_debate" or src["language"].lower() != "en":
        return "noncomparable_genre_or_language"
    if quality is None:
        return "original_source_quality_missing"
    if (quality["match_status"] != "strong" or
            quality["source_method"] != "official_pv" or
            quality["verification_basis"] != "original_pv_full_speech" or
            quality["country_capacity"] != "individual"):
        return "original_source_or_attribution_not_eligible"
    if not PV.fullmatch(quality["official_document_symbol"]):
        return "official_document_symbol_unverified"
    if (not HEX.fullmatch(quality["original_pdf_sha256"]) or
            not quality["source_family_id"]):
        return "original_pdf_hash_or_family_missing"
    if (not src["text_path"] or not HEX.fullmatch(src["text_sha256"]) or
            not source_is_official(src["source_url"])):
        return "canonical_text_hash_or_official_url_missing"
    return None


def window(year: int) -> str | None:
    return next((name for name, (lo, hi) in YEARS.items()
                 if lo <= year <= hi), None)


def allocate_countries(country_ids: list[str], seed: int) -> dict[str, str]:
    require(len(country_ids) >= 6,
            "At least six distinct eligible country affiliations required")
    ranked = sorted(country_ids, key=lambda country: (
        digest(f"{seed}|country|{country}".encode()), country))
    n = len(ranked)
    cal = max(2, round(n * SHARES[1]))
    test = max(2, round(n * SHARES[2]))
    require(n - cal - test >= 2, "Insufficient groups for three partitions")
    train = n - cal - test
    return {iso: split for iso, split in
            zip(ranked, ["train"] * train + ["calibration"] * cal +
                ["test"] * test, strict=True)}


def make_plan(workspace: Path, codebook_path: Path, seed: int) -> tuple[dict, list[dict]]:
    workspace = private_workspace(workspace)
    props = review.load_codebook(codebook_path)
    props_by_id = {item["proposition_id"] for item in props["propositions"]}
    require(set(PLAN_PROP_IDS).issubset(props_by_id),
            "Target propositions absent from reviewed draft codebook")
    require(0 <= seed < (1 << 31), "Invalid prespecified random seed")
    sources, qualities, manifests = load_source_frame(workspace)
    ledger: list[dict] = []
    eligible: list[dict] = []
    for src in sources:
        q = qualities.get(src["source_id"])
        reason = classify_source(src, q)
        row = {
            "source_id": src["source_id"], "iso3": src["iso3"],
            "event_date": src["event_date"], "text_sha256": src["text_sha256"],
            "source_family_id": (q or {}).get("source_family_id"),
            "split": "withheld", "reason": reason,
        }
        ledger.append(row)
        if reason is not None:
            continue
        # Only sources passing the metadata/source-quality eligibility checks
        # are opened. Original UN PDFs themselves remain in private archives;
        # a PDF hash supplied by the quality ledger is NOT replayed here.
        review.safe_source_text(
            workspace, src["text_path"], src["text_sha256"]
        )
        eligible.append(row)

    # A family or canonical text reused across distinct affiliations can
    # create cross-actor leakage or an erroneous speaker attribution.
    by_family: dict[str, set[str]] = defaultdict(set)
    by_hash: dict[str, set[str]] = defaultdict(set)
    for row in eligible:
        by_family[row["source_family_id"]].add(row["iso3"])
        by_hash[row["text_sha256"]].add(row["iso3"])
    for row in eligible:
        if (len(by_family[row["source_family_id"]]) > 1 or
                len(by_hash[row["text_sha256"]]) > 1):
            row["reason"] = "cross_actor_duplicate_or_family"
    eligible = [row for row in eligible if row["reason"] is None]
    countries = allocate_countries(sorted({x["iso3"] for x in eligible}), seed)
    for row in eligible:
        period = window(int(row["event_date"][:4]))
        assigned = countries[row["iso3"]]
        if period != assigned:
            row["reason"] = "country_reserved_for_different_period"
        else:
            row["split"] = assigned
            row["reason"] = None

    kept = [row for row in ledger if row["split"] in SPLITS]
    group_counts = {name: len({r["iso3"] for r in kept if r["split"] == name})
                    for name in SPLITS}
    source_counts = {name: sum(r["split"] == name for r in kept) for name in SPLITS}
    require(all(group_counts[s] >= 2 for s in SPLITS),
            f"Grouped period support insufficient: {group_counts}")
    require(all(source_counts[s] >= 2 for s in SPLITS),
            f"Source support insufficient: {source_counts}")
    dates = {name: sorted(r["event_date"] for r in kept if r["split"] == name)
             for name in SPLITS}
    require(max(dates["train"]) < min(dates["calibration"]) and
            max(dates["calibration"]) < min(dates["test"]),
            "Temporal source split is not strictly forward")
    country_sets = [
        {r["iso3"] for r in kept if r["split"] == s} for s in SPLITS
    ]
    require(not any(country_sets[i] & country_sets[j]
                    for i in range(3) for j in range(i)),
            "Country leakage across partitions")
    hash_groups: dict[str, set[str]] = defaultdict(set)
    for row in kept:
        hash_groups[row["text_sha256"]].add(row["split"])
        hash_groups[row["source_family_id"]].add(row["split"])
    require(all(len(splits) == 1 for splits in hash_groups.values()),
            "Original text or family leaked across partitions")

    counts = Counter(row["reason"] or row["split"] for row in ledger)
    manifest = {
        "schema": SCHEMA, "source_schema": "un.review.v1",
        "dataset_kind": "source_review_candidate",
        "evaluation_role": "allocation_only",
        "publication_eligible": False, "daily_adapter_integrated": False,
        "model_fitted": False, "human_stance_labels": 0,
        "gold_stance_labels": 0,
        "frame_policy": FRAME_POLICY,
        "validation_scheme": "time_and_country",
        "observation_unit": "original_source_speech",
        "country_identity_kind": "recorded_affiliation_not_person_or_policy",
        "seed": seed, "periods": YEARS,
        "population": {
            "sources_in_inventory": len(sources),
            "sources_accepted": len(kept),
            "sources_withheld": len(ledger) - len(kept),
            "countries_by_split": group_counts,
            "sources_by_split": source_counts,
            "disposition_counts": dict(sorted(counts.items())),
        },
        "codebook_sha256": digest(codebook_path.read_bytes()),
        **manifests,
        "assignment": sorted(ledger, key=lambda x: x["source_id"]),
        "limitations": [
            "Only verified-original-PV-strong English 2016–2023 inputs may be allocated.",
            "PDF byte digests are privately asserted quality evidence; this code checks "
            "canonical transcript text hashes, not the private original PDFs.",
            "Restricted historical source verification and country selection are nonrandom.",
            "Missing/unverified text is withheld, never negative issue or stance evidence.",
            "A country affiliation is not an authenticated individual or government-wide view.",
            "Source-separated allocations are not reviewed labels or statistical calibration."
        ]
    }
    manifest["plan_sha256"] = digest(stable(manifest))
    return manifest, kept


def write_plan(workspace: Path, quality_codebook: Path, outdir: Path, seed: int) -> dict:
    outdir = outdir.resolve()
    review.require(outdir != review.REPOSITORY and
                   review.REPOSITORY not in outdir.parents,
                   "Do not export private source identifiers into public Git")
    require(not outdir.exists(), "Refusing to overwrite pilot-plan directory")
    plan, kept = make_plan(workspace, quality_codebook, seed)
    import csv
    outdir.mkdir(parents=True, exist_ok=False)
    manifest_path = outdir / "pilot_plan.json"
    write_new(manifest_path, json.dumps(
        plan, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    with (outdir / "splits.csv").open("x", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["source_id", "split"])
        writer.writeheader()
        writer.writerows({"source_id": r["source_id"], "split": r["split"]}
                         for r in sorted(kept, key=lambda x: x["source_id"]))
    return {
        "plan_directory": str(outdir), "plan_sha256": plan["plan_sha256"],
        "population": plan["population"],
        "status": "FROZEN_SOURCE_SPLITS_ONLY; NO_HUMAN_STANCE_LABELS"
    }


def check_plan_against_sources(plan: dict, workspace: Path, codebook_path: Path) -> dict:
    plan = verified_plan(plan)
    workspace = private_workspace(workspace)
    _, _, hashes = load_source_frame(workspace)
    for key in hashes:
        require(plan[key] == hashes[key], "Source/QC CSV drift: " + key)
    require(plan["codebook_sha256"] == digest(codebook_path.read_bytes()),
            "Proposition codebook changed after split freeze")
    return plan


def chosen(candidates: list[dict], count: int, seed: int, tag: str) -> list[dict]:
    """Round-robin source-family selection for one named sampling route."""
    sorted_rows = sorted(candidates, key=lambda r:
        (digest(f"{seed}|{tag}|{r['source_id']}|{r['passage_id']}".encode()),
         r["passage_id"]))
    by_family: dict[str, list[dict]] = defaultdict(list)
    for row in sorted_rows:
        by_family[row["source_family_id"]].append(row)
    order = sorted(by_family, key=lambda fam:
        digest(f"{seed}|family|{tag}|{fam}".encode()))
    out: list[dict] = []
    for _ in range(2):  # no more than 2 passages per source family per route
        for fam in order:
            if by_family[fam] and len(out) < count:
                out.append(by_family[fam].pop(0))
        if len(out) >= count:
            break
    return out


def make_packet(workspace: Path, plan_path: Path, codebook_path: Path,
                split: str, count_per_proposition: int, seed: int,
                allow_test: bool) -> dict:
    require(split in SPLITS, "Invalid split")
    require(split != "test" or allow_test,
            "Frozen test packet requires --authorize-test-review")
    require(1 <= count_per_proposition <= 100, "Per-proposition count must be 1–100")
    require(seed >= 0, "Invalid packet seed")
    plan = check_plan_against_sources(review.load_json(plan_path), workspace,
                                      codebook_path)
    codebook = review.load_codebook(codebook_path)
    prop_map = {p["proposition_id"]: p for p in codebook["propositions"]}
    eligible_sources = {r["source_id"]: r for r in plan["assignment"]
                        if r["split"] == split}
    require(bool(eligible_sources), "No eligible source group in requested split")
    all_sources, _, _ = load_source_frame(workspace)
    source_index = {r["source_id"]: r for r in all_sources}
    excerpts = load_table(workspace / "passages.csv",
                          review.FIELDS["passages"].split())
    parents: dict[str, str] = {}
    candidates = []
    seen = set()
    for passage in excerpts:
        sid = passage["source_id"]
        if sid not in eligible_sources:
            continue
        pid = passage["passage_id"]
        require(pid and (sid, pid) not in seen, "Duplicate source passage")
        seen.add((sid, pid))
        record = source_index[sid]
        if sid not in parents:
            parents[sid] = review.safe_source_text(
                workspace, record["text_path"], record["text_sha256"])
        text = parents[sid]
        try:
            start, end = int(passage["start"]), int(passage["end"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Malformed codepoint offsets") from exc
        require(0 <= start < end <= len(text) and
                text[start:end] == passage["quote"],
                "Source quote/offset drift in " + pid)
        candidates.append({
            "source_id": sid, "passage_id": pid,
            "source_family_id": eligible_sources[sid]["source_family_id"],
            "start": start, "end": end, "quote": passage["quote"],
            "before": text[max(0, start - 220):start],
            "after": text[end:min(len(text), end + 220)]
        })
    require(bool(candidates), "No text-verified passages for selected split")

    sampled = []
    audit = {}
    for prop_id in PLAN_PROP_IDS:
        prop = prop_map[prop_id]
        screen = [row for row in candidates if any(
            cue in row["quote"].casefold() for cue in CUES[prop_id])]
        control = [row for row in candidates if row not in screen]
        primary_target = round(count_per_proposition * .70)
        primary = chosen(screen, primary_target, seed, prop_id + "|screen")
        controls = chosen(control, count_per_proposition - len(primary),
                          seed, prop_id + "|control")
        # Do not label any screen hit as relevant or any control as irrelevant.
        pools = [(row, "lexical_screen") for row in primary] + [
            (row, "unfiltered_control") for row in controls]
        audit[prop_id] = {
            "requested": count_per_proposition, "selected": len(pools),
            "lexical_screen": len(primary), "unfiltered_control": len(controls),
            "available_passages": len(candidates),
            "screen_matches": len(screen), "nonmatches": len(control),
            "missing_quota": count_per_proposition - len(pools),
        }
        for row, route in pools:
            src = source_index[row["source_id"]]
            ident = "|".join((plan["plan_sha256"], split, prop_id,
                              row["source_id"], row["passage_id"]))
            sampled.append({
                "item_id": "item-" + digest(ident.encode())[:24],
                "passage_id": row["passage_id"], "source_id": row["source_id"],
                "source_family_id": row["source_family_id"],
                "country_affiliation": src["iso3"],
                "actor_capacity": "recorded_affiliation_only",
                "source_url": src["source_url"], "event_date": src["event_date"],
                "genre": src["genre"], "language": src["language"],
                "source_text_sha256": src["text_sha256"],
                "start": row["start"], "end": row["end"],
                "quote": row["quote"],
                "context_before": row["before"], "context_after": row["after"],
                "issue_id": prop["issue_id"], "proposition_id": prop_id,
                "proposition_version": prop["version"],
                "proposition": prop["proposition"], "scope": prop["scope"],
                "exclusion_rule": prop["exclusion_rule"],
                "selection_route": route,
            })
    require(bool(sampled), "No reviewable proposition-passage pairs")

    packet = {
        "schema": review.SCHEMA, "source_schema": "un.review.v1",
        "dataset_kind": "unreviewed", "review_mode": "single_reviewer_pilot",
        "publication_eligible": False, "evaluation_role": "annotation_only",
        "model_predictions_included": False,
        "human_stance_labels": 0, "gold_stance_labels": 0,
        "codebook_version": codebook["version"],
        "source_plan_sha256": plan["plan_sha256"], "source_split": split,
        "source_frame_policy": FRAME_POLICY,
        "sampling": {
            "policy": "predeclared_lexical_screen_plus_unfiltered_controls",
            "seed": seed, "by_proposition": audit,
            "country_group_separated": True, "time_forward": True,
            "nonprobability_enrichment": True,
            "selection_route_is_not_ground_truth": True,
        },
        "items": sorted(sampled, key=lambda item: digest(
            (str(seed) + "|" + item["item_id"]).encode())),
    }
    packet["packet_sha256"] = digest(stable(packet))
    return packet


def inspect_draft(packet: dict, draft: dict) -> dict:
    """Counts ACTUAL asserted review decisions; never calls them independent gold."""
    require(packet.get("schema") == review.SCHEMA and
            digest(stable({k: v for k, v in packet.items()
                           if k != "packet_sha256"})) == packet.get("packet_sha256"),
            "Review packet hash mismatch")
    require(draft.get("schema") == review.DRAFT and
            draft.get("packet_sha256") == packet["packet_sha256"],
            "Owner review does not match packet")
    require(draft.get("human_confirmation") is True and
            draft.get("finalized") is False and draft.get("human_gold") is False,
            "An explicit reviewer attestation is required; draft is not gold")
    reviewer_id = draft.get("reviewer_id")
    require(isinstance(reviewer_id, str) and
            re.fullmatch(r"[A-Za-z0-9_.-]{3,80}", reviewer_id),
            "Pseudonymous reviewer identity required")
    items = {it["item_id"]: it for it in packet["items"]}
    seen = set()
    counts = Counter()
    for choice in draft.get("decisions", []):
        key = choice.get("item_id")
        require(key in items and key not in seen, "Unknown/duplicate owner decision")
        seen.add(key)
        issue = choice.get("issue_label")
        stance = choice.get("stance_label") or None
        require(issue in review.ISSUE_LABELS, "Unreviewed/invalid issue label")
        require(stance is None or stance in review.STANCE_LABELS,
                "Invalid stance label")
        require(issue == "relevant" or stance in (None, "insufficient"),
                "A nonrelevant passage cannot endorse the policy object")
        require(len((choice.get("rationale") or "").strip()) >= 8,
                "Explicit decision rationale required")
        stamp = choice.get("reviewed_at")
        require(isinstance(stamp, str) and stamp.endswith("Z"),
                "Missing UTC review timestamp")
        try:
            datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Invalid reviewed_at timestamp") from exc
        counts["issue_" + issue] += 1
        if stance:
            counts["stance_" + stance] += 1
        else:
            counts["stance_unreviewed"] += 1
    return {
        "schema": "un.country-positions.review-audit.v1",
        "plan_sha256": packet.get("source_plan_sha256"),
        "packet_sha256": packet["packet_sha256"],
        "split": packet.get("source_split"),
        "owner_review_attested": True, "independent_gold": False,
        "publication_eligible": False, "model_training_eligible": False,
        "selected_items": len(items), "reviewed_items": len(seen),
        "unreviewed_items": len(items) - len(seen),
        "counts": dict(sorted(counts.items())),
        "limitations": "Self-attestation only; not verified independent gold, no model fitting."
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    p = subs.add_parser("plan", help="Create private source-bound train/cal/test allocations")
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--codebook", type=Path,
                   default=Path(__file__).with_name("propositions.v1.json"))
    p.add_argument("--outdir", type=Path, required=True)
    p.add_argument("--seed", type=int, default=20261009)
    q = subs.add_parser("packet", help="Produce a blind private split-specific review packet")
    q.add_argument("--workspace", type=Path, required=True)
    q.add_argument("--plan", type=Path, required=True)
    q.add_argument("--codebook", type=Path,
                   default=Path(__file__).with_name("propositions.v1.json"))
    q.add_argument("--split", choices=SPLITS, required=True)
    q.add_argument("--count-per-proposition", type=int, default=48)
    q.add_argument("--seed", type=int, default=20261009)
    q.add_argument("--authorize-test-review", action="store_true")
    q.add_argument("--output", type=Path, required=True)
    a = subs.add_parser("audit", help="Audit an owner-attested, unfinalized review draft")
    a.add_argument("--packet", type=Path, required=True)
    a.add_argument("--draft", type=Path, required=True)
    a.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "plan":
            result = write_plan(args.workspace, args.codebook, args.outdir, args.seed)
        elif args.command == "packet":
            packet = make_packet(args.workspace, args.plan, args.codebook, args.split,
                                 args.count_per_proposition, args.seed,
                                 args.authorize_test_review)
            write_new(args.output, json.dumps(packet, ensure_ascii=False,
                                              indent=2).encode("utf-8") + b"\n")
            result = {
                "output": str(args.output), "packet_sha256": packet["packet_sha256"],
                "split": packet["source_split"], "sampled_pairs": len(packet["items"]),
                "sampling": packet["sampling"],
                "status": "UNREVIEWED; EMPIRICAL PUBLICATION WITHHELD",
            }
        else:
            audit = inspect_draft(review.load_json(args.packet),
                                  review.load_json(args.draft))
            write_new(args.output, json.dumps(audit, indent=2).encode() + b"\n")
            result = audit
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
