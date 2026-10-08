#!/usr/bin/env python3
"""Prepare private, blind proposition review packets from un.review.v1.

No model inference, automatic gold labels, source downloads, or public exports.
Run from the repository root, using a private workspace OUTSIDE the Git checkout.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

REPOSITORY = Path(__file__).resolve().parents[2]
SCHEMA = "un.country-positions.annotation-packet.v1"
DRAFT = "un.country-positions.annotation-draft.v1"
FIELDS = {
    "sources": "source_id iso3 event_date available_at genre language source_url text_path text_sha256 duplicate_group",
    "passages": "passage_id source_id start end quote",
}
ISSUE_LABELS = {"relevant", "not_relevant", "insufficient"}
STANCE_LABELS = {"support", "oppose", "conditional", "descriptive", "insufficient"}
SEALED_DATES = {"2026-10-05", "2026-10-06"}
SHA = re.compile(r"^[a-f0-9]{64}$")
ISO3 = re.compile(r"^[A-Z]{3}$")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def encoded(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "JSON object required: " + str(path))
    return value


def write_private(path: Path, content: bytes) -> None:
    real = path.resolve()
    require(real != REPOSITORY and REPOSITORY not in real.parents,
            "Private packet/annotations must not be written into public Git")
    require(not path.exists(), "Refusing to overwrite: " + str(path))
    real.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(content)


def read_table(path: Path, table: str) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == FIELDS[table].split(),
                table + " must preserve exact un.review.v1 headers")
        rows = []
        for row in reader:
            require(len(rows) < 100000, "Review table resource limit exceeded")
            require(None not in row and all(v is not None for v in row.values()),
                    table + ": missing or extra CSV cell")
            rows.append(row)
        return rows


def safe_source_text(workspace: Path, path: str, expected: str) -> str:
    require(SHA.fullmatch(expected) is not None, "Invalid original text SHA-256")
    base = workspace.resolve()
    original = workspace / path
    current = workspace
    for item in Path(path).parts:
        require(item not in (".", "..") and item != "",
                "Source path traversal")
        current = current / item
        require(not current.is_symlink(), "Source symlink refused")
    resolved = original.resolve()
    require(base in resolved.parents and resolved.is_file(),
            "Source must be a regular file inside workspace")
    raw = resolved.read_bytes()
    require(len(raw) <= 2_000_000, "Source byte cap exceeded")
    require(sha256(raw) == expected, "Original source checksum mismatch")
    return raw.decode("utf-8", errors="strict")


def load_codebook(path: Path) -> dict:
    data = load_json(path)
    require(data.get("schema") == "un.country-positions.propositions.v1"
            and data.get("release_status") == "draft"
            and data.get("publication_eligible") is False,
            "Only the versioned unpublished draft codebook is supported")
    props = data.get("propositions")
    require(isinstance(props, list) and 2 <= len(props) <= 100,
            "Invalid proposition list")
    ids = [p["proposition_id"] for p in props]
    require(len(set(ids)) == len(ids), "Duplicate proposition IDs")
    return data


def prepare(args: argparse.Namespace) -> dict:
    workspace = args.workspace.resolve()
    require(workspace.is_dir(), "un.review.v1 workspace not found")
    bundle = load_json(workspace / "bundle.json")
    require(bundle.get("schema") == "un.review.v1", "Expected un.review.v1")
    require(bundle.get("dataset_kind") in ("unreviewed", "real"),
            "Invalid review workspace kind")
    sources = read_table(workspace / "sources.csv", "sources")
    passages = read_table(workspace / "passages.csv", "passages")
    props = load_codebook(args.codebook)
    require(1 <= args.count <= 200, "Count must be in [1, 200]")
    by_source: dict[str, dict] = {}
    unavailable_sources = 0
    for source in sources:
        sid = source["source_id"]
        require(bool(sid) and sid not in by_source, "Duplicate/empty source identity")
        require(source["event_date"] not in SEALED_DATES,
                "Reserved 5-6 October 2026 meetings are not authorized")
        require(ISO3.fullmatch(source["iso3"]) is not None, "Invalid country code")
        # Missing URLs and unavailable text are coverage gaps, not non-mentions.
        if (not source["source_url"].startswith("https://") or
                not source["text_sha256"] or not source["text_path"]):
            unavailable_sources += 1
            continue
        try:
            text = safe_source_text(
                workspace, source["text_path"], source["text_sha256"])
        except (OSError, ValueError, UnicodeError) as exc:
            # Byte/hash problems invalidate the frame instead of being ignored.
            raise ValueError("Source integrity failed for " + sid + ": " + str(exc)) from exc
        by_source[sid] = {"metadata": source, "text": text}
    valid = []
    ids = set()
    uncollected_passages = 0
    for passage in passages:
        pid = passage["passage_id"]
        require(bool(pid) and pid not in ids, "Duplicate/empty passage ID")
        ids.add(pid)
        sid = passage["source_id"]
        if sid not in by_source:
            uncollected_passages += 1
            continue
        source = by_source[sid]
        try:
            start, end = int(passage["start"]), int(passage["end"])
        except ValueError as exc:
            raise ValueError("Invalid passage offsets: " + pid) from exc
        text = source["text"]
        require(0 <= start < end <= len(text) and
                text[start:end] == passage["quote"],
                "Unicode codepoint quote/offset mismatch: " + pid)
        score = sha256((str(args.seed) + "|" + sid + "|" + pid).encode("utf-8"))
        group = source["metadata"]["duplicate_group"] or sid
        valid.append((score, group, passage, source["metadata"]))
    require(bool(valid), "No source-verified candidate passages")

    # Source-family balanced deterministic selection, without keyword filtering.
    pools: dict[str, list] = {}
    for candidate in sorted(valid, key=lambda row: row[0]):
        pools.setdefault(candidate[1], []).append(candidate)
    selected = []
    while len(selected) < args.count and any(pools.values()):
        for group in sorted(pools, key=lambda name: sha256(
                (str(args.seed) + "|" + name).encode("utf-8"))):
            if pools[group] and len(selected) < args.count:
                selected.append(pools[group].pop(0))
    items = []
    for i, (_, group, passage, source) in enumerate(selected):
        prop = props["propositions"][i % len(props["propositions"])]
        identity = "|".join([passage["passage_id"], prop["proposition_id"],
                             prop["version"], source["text_sha256"]])
        items.append({
            "item_id": "item-" + sha256(identity.encode("utf-8"))[:20],
            "passage_id": passage["passage_id"],
            "source_id": passage["source_id"],
            "source_family_id": group,
            "country_affiliation": source["iso3"],
            "actor_capacity": "recorded_affiliation_only",
            "source_url": source["source_url"],
            "event_date": source["event_date"],
            "genre": source["genre"],
            "language": source["language"],
            "source_text_sha256": source["text_sha256"],
            "start": int(passage["start"]), "end": int(passage["end"]),
            "quote": passage["quote"],
            "issue_id": prop["issue_id"],
            "proposition_id": prop["proposition_id"],
            "proposition_version": prop["version"],
            "proposition": prop["proposition"],
            "scope": prop["scope"], "exclusion_rule": prop["exclusion_rule"],
        })
    packet = {
        "schema": SCHEMA, "source_schema": "un.review.v1",
        "dataset_kind": "unreviewed", "review_mode": "single_reviewer_pilot",
        "publication_eligible": False, "evaluation_role": "annotation_only",
        "model_predictions_included": False, "codebook_version": props["version"],
        "sampling": {
            "policy": "source_family_balanced_sha256_random_rank",
            "seed": args.seed, "eligible_passages": len(valid),
            "selected_passages": len(items), "source_rows": len(sources),
            "passages_outside_verified_source": uncollected_passages,
            "sources_without_recoverable_original": unavailable_sources,
            "not_a_probability_sample": True,
        },
        "items": items,
    }
    packet["packet_sha256"] = sha256(encoded(packet))
    write_private(args.output, json.dumps(
        packet, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    return {"packet": str(args.output), "selected": len(items),
            "packet_sha256": packet["packet_sha256"],
            "unverified_passages": uncollected_passages,
            "source_gaps": unavailable_sources}


def export(args: argparse.Namespace) -> dict:
    packet = load_json(args.packet)
    require(packet.get("schema") == SCHEMA and
            packet.get("publication_eligible") is False,
            "Invalid/private packet format")
    digest = packet.pop("packet_sha256", None)
    require(SHA.fullmatch(digest or "") is not None and
            digest == sha256(encoded(packet)), "Source packet checksum mismatch")
    draft = load_json(args.draft)
    require(draft.get("schema") == DRAFT and draft.get("packet_sha256") == digest,
            "Draft cannot be joined to this source packet")
    reviewer = draft.get("reviewer_id")
    require(isinstance(reviewer, str) and
            re.fullmatch(r"[A-Za-z0-9_.-]{3,80}", reviewer) is not None,
            "Explicit pseudonymous human reviewer ID required")
    items = {item["item_id"]: item for item in packet.get("items", [])}
    require(len(items) == len(packet.get("items", [])),
            "Duplicate packet item IDs")
    decisions = draft.get("decisions")
    require(isinstance(decisions, list), "Expected draft decisions array")
    seen = set()
    output_rows = []
    incomplete = 0
    for choice in decisions:
        item = choice.get("item_id")
        require(item in items and item not in seen, "Unknown/duplicate reviewed item")
        seen.add(item)
        issue = choice.get("issue_label") or None
        stance = choice.get("stance_label") or None
        if issue is None and stance is None:
            incomplete += 1
            continue
        require(issue in ISSUE_LABELS, "Issue relevance must be reviewed first")
        require(stance is None or stance in STANCE_LABELS, "Invalid stance")
        require(issue == "relevant" or stance in (None, "insufficient"),
                "An irrelevant/unclear item cannot be coded as policy endorsement")
        rationale = choice.get("rationale")
        require(isinstance(rationale, str) and len(rationale.strip()) >= 8,
                "Recorded human rationale is required")
        stamp = choice.get("reviewed_at")
        require(isinstance(stamp, str) and stamp.endswith("Z"),
                "UTC timestamp required")
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        require(parsed.tzinfo is not None, "UTC timestamp required")
        original = items[item]
        for task, label in [("issue", issue), ("stance", stance)]:
            if label is None:
                continue
            key = "|".join([item, task, reviewer])
            output_rows.append({
                "annotation_id": "ann-" + sha256(key.encode("utf-8"))[:20],
                "passage_id": original["passage_id"],
                "task": task, "proposition_id": original["proposition_id"],
                "label": label, "reviewer_id": reviewer,
                "reviewed_at": stamp, "rationale": rationale.strip(),
            })
    require(bool(output_rows), "No reviewed decisions to export")
    out = args.output
    real = out.resolve()
    require(REPOSITORY not in real.parents, "Candidate labels are private")
    require(not out.exists(), "Refusing to overwrite candidate annotations")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=(
            "annotation_id passage_id task proposition_id label "
            "reviewer_id reviewed_at rationale").split())
        writer.writeheader()
        writer.writerows(output_rows)
    return {
        "candidate_annotations": str(out), "rows": len(output_rows),
        "items_with_decisions": len(seen) - incomplete,
        "packet_items": len(items),
        "status": "UNFINALIZED; no adjudications or gold labels created",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    p = subs.add_parser("prepare", help="Create a blind source-verified review packet")
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--codebook", type=Path,
                   default=Path(__file__).with_name("propositions.v1.json"))
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--count", type=int, default=60)
    p.add_argument("--seed", type=int, default=20261008)
    e = subs.add_parser("export", help="Export UNFINALIZED un.review.v1-compatible CSV")
    e.add_argument("--packet", type=Path, required=True)
    e.add_argument("--draft", type=Path, required=True)
    e.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prepare(args) if args.command == "prepare" else export(args)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
