"""Official UN Security Council voting CSV Version 7 adapter.

UN Dag Hammarskjold Library, United Nations, October 2026.
Non-commercial use with attribution. Original downloaded records stay private.
X is non-voting, not evidence of absence or ineligibility. Without-vote Y codes
are preserved as raw codes but never become individual affirmative votes.
"""
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from .adapters import SourceError, vote_record
from .countries import map_country

DATASET_URL = "https://digitallibrary.un.org/record/4055387/files/2026_10_16_sc_votes.csv"
METADATA_URL = "https://digitallibrary.un.org/record/4055387/files/2026_10_16_sc_voting_md.md"
HEADERS = ("undl_id", "ms_code", "ms_name", "permanent_member", "ms_vote", "date", "resolution", "draft", "meeting", "description", "agenda", "subjects", "vote_note", "total_yes", "total_no", "total_abstentions", "total_non_voting", "total_ms", "modality", "undl_link")


def validate_headers(headers):
    if tuple(headers or ()) != HEADERS:
        raise SourceError("SC v7 header schema mismatch; review a new adapter version")


def adapt(row):
    if set(row) != set(HEADERS):
        raise SourceError("SC v7 row/header mismatch")
    if not re.fullmatch(r"[A-Z]{3}", row["ms_code"] or "") or not row["ms_name"].strip():
        raise SourceError("Invalid recorded historical Member State identity")
    if row["permanent_member"] not in ("True", "False"):
        raise SourceError("Unknown permanent-member field")
    if not re.fullmatch(r"S/RES/\d+ ?\(\d{4}\)", row["resolution"] or ""):
        raise SourceError("Invalid adopted SC resolution symbol")
    if not re.fullmatch(r"\d+", row["undl_id"] or "") or row["undl_link"] != "https://digitallibrary.un.org/record/" + row["undl_id"]:
        raise SourceError("UN Digital Library record identity mismatch")
    code, modality = row["ms_vote"], row["modality"]
    if code not in ("Y", "N", "A", "X") or modality not in ("Vote", "Without Vote"):
        raise SourceError("Unknown vote code or modality")
    for key in ("total_yes", "total_no", "total_abstentions", "total_non_voting", "total_ms"):
        if not re.fullmatch(r"\d+", row[key] or ""):
            raise SourceError("Invalid resolution vote total")
    individual = modality == "Vote" and code in ("Y", "N", "A")
    return vote_record({
        "resolution_id": row["resolution"].replace(" ", ""), "recorded_resolution_symbol": row["resolution"], "resolution_version": "as_adopted", "stage": "adopted_resolution",
        **map_country(row["ms_code"], row["ms_name"]),
        "date": row["date"], "source_url": row["undl_link"],
        "vote": {"Y": "yes", "N": "no", "A": "abstain"}[code] if individual else "unknown",
        "eligible": True if individual else None,
        "raw_vote_code": code, "non_voting_reported": code == "X", "modality": modality,
        "individual_vote_recorded": individual, "vote_note_present": bool(row["vote_note"].strip()),
        "dataset_version": "7", "adapter_version": "sc-v7-csv-1", "body": "SC",
    })


def select_batch(source_file, *, start, end, limit=500, cursor=0):
    """Select whole adopted-resolution groups, newest first, within a row bound.

    The cursor is a resolution-group index in this exact hashed source/window.
    Every selected group reconciles raw categories against publisher totals.
    A conflict stops the batch; no partial or silently corrected group is emitted.
    """
    from datetime import date
    if date.fromisoformat(start) > date.fromisoformat(end):
        raise SourceError("Reversed source window")
    if type(limit) is not int or not 1 <= limit <= 500 or type(cursor) is not int or cursor < 0:
        raise SourceError("Choose a bounded 1..500 row batch and nonnegative cursor")
    source = Path(source_file)
    if source.stat().st_size > 50_000_000:
        raise SourceError("SC source exceeds 50 MB adapter bound")
    data = source.read_bytes()
    groups = defaultdict(list)
    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        validate_headers(reader.fieldnames)
        total_rows = 0
        for row in reader:
            total_rows += 1
            if start <= row["date"] <= end:
                groups[(row["date"], row["resolution"], row["undl_id"])].append(row)
    ordered = sorted(groups, reverse=True)
    selected, resolutions, current = [], [], cursor
    while current < len(ordered):
        group = groups[ordered[current]]
        if len(selected) + len(group) > limit:
            break
        normalized = [adapt(row) for row in group]
        counts = Counter(row["ms_vote"] for row in group)
        first = group[0]
        total_fields = ("total_yes", "total_no", "total_abstentions", "total_non_voting", "total_ms")
        if any(any(row[k] != first[k] for k in (*total_fields, "modality", "meeting")) for row in group):
            raise SourceError("Conflicting resolution metadata")
        if len({row["ms_code"] for row in group}) != len(group):
            raise SourceError("Duplicate Member State in resolution group")
        expected = dict(zip(("Y", "N", "A", "X"), (int(first[k]) for k in total_fields[:4])))
        if len(group) != int(first["total_ms"]) or sum(expected.values()) != len(group) or any(counts[k] != expected[k] for k in expected):
            raise SourceError("Resolution group does not reconcile with published totals")
        selected.extend(normalized)
        resolutions.append({"resolution": first["resolution"], "date": first["date"], "rows": len(group), "raw_counts": dict(counts), "modality": first["modality"]})
        current += 1
    if not selected and current < len(ordered):
        raise SourceError("Row limit cannot accommodate the next complete resolution group")
    reconciliation = {"schema": "un.sc-v7.private-batch.v1", "source_sha256": hashlib.sha256(data).hexdigest(), "source_bytes": len(data), "source_rows": total_rows, "window": {"start": start, "end": end}, "window_rows": sum(map(len, groups.values())), "window_resolutions": len(groups), "cursor": cursor, "next_cursor": current, "complete": current == len(ordered), "selected_rows": len(selected), "selected_resolutions": resolutions, "normalized_counts": dict(Counter(row["vote"] for row in selected)), "policy_binding": "withheld_unbound", "publication": "private_only"}
    return selected, reconciliation


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source-file", "start", "end", "normalized-file", "reconciliation-file"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--cursor", type=int, default=0)
    args = parser.parse_args()
    normalized, reconciliation = select_batch(args.source_file, start=args.start, end=args.end, limit=args.limit, cursor=args.cursor)
    Path(args.normalized_file).write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.reconciliation_file).write_text(json.dumps(reconciliation, indent=2), encoding="utf-8")
    print(json.dumps({k: reconciliation[k] for k in ("source_sha256", "selected_rows", "cursor", "next_cursor", "complete", "normalized_counts")}, indent=2))
