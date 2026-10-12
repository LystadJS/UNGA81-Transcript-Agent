"""W4 -> W6 offline source-preserving actor-period read model (synthetic only).

W4 owns alignment, projection, source identities and comparison uncertainty.
This adapter may GROUP its already aligned source points using W4's declared
equal-meeting-within-genre/equal-genre weights; it NEVER refits the map,
changes the feature representation or invents an inferential interval.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import math

from research.longitudinal import framework as w4

MAX_ACTORS = 30
SCORE_BOUND = 1_000_000


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError("W4/W6: " + message)


def _eligible(row: dict) -> bool:
    return row["source_status"] == "available"


def _mean(values: list[list[float]]) -> list[float]:
    require(bool(values), "Cannot form an empty weighted mean")
    return [sum(v[i] for v in values) / len(values) for i in range(len(values[0]))]


def validate_source(source: dict, comparison: dict, envelope: dict) -> None:
    """Check original W4 identifiers, *including* alignment/output source rows."""
    w4.validate_panel(source)
    require(source["split"] == comparison.get("split") == "synthetic",
            "Only the fictional W4 panel is accepted")
    require(comparison.get("schema") == "un.longitudinal-comparison.v1" and
            comparison.get("publication_eligible") is False and
            comparison.get("evaluation_role") == "engineering_only",
            "W4 comparison is not an engineering-only longitudinal result")
    require(envelope.get("schema") == "un.parallel-analysis.v1" and
            envelope.get("contract_version") == "1.0.0" and
            envelope.get("publication_eligible") is False and
            envelope.get("evaluation_role") == "engineering_only",
            "W1-compatible complete interchange required")
    require(envelope["producer"]["workstream_id"] == "W4" and
            envelope["producer"]["fixture_kind"] == "synthetic" and
            envelope["upstream"]["source_schema"] == "synthetic.v1" and
            envelope["upstream"]["source_hash_basis"] == "synthetic" and
            envelope["cohort"]["split"] == "synthetic",
            "Real development or unlabeled source inputs cannot be published")
    require(comparison["provenance"]["panel_sha256"] == w4.digest(source),
            "W4 panel bytes/content not authenticated by comparison digest")
    ordered = [r for r in source["observations"]
               if r["period"] in (comparison["before"], comparison["after"])]
    require([r["id"] for r in ordered] ==
            comparison["provenance"]["included_observation_ids"] ==
            [r["id"] for r in envelope["observations"]],
            "Source frame order and W4 comparison population differ")
    require(envelope["upstream"]["source_sha256"] ==
            w4.digest([[r["id"], r["source_sha256"]] for r in ordered]) and
            envelope["upstream"]["selection_sha256"] ==
            w4.digest([r["id"] for r in ordered]),
            "W4 original source or selection digest differs")
    require(envelope["cohort"]["total_in_frame"] == len(ordered) and
            envelope["cohort"]["eligible"] == sum(_eligible(r) for r in ordered) and
            envelope["coverage"]["excluded"] == sum(not _eligible(r) for r in ordered),
            "W4 complete-frame denominators differ")
    require(len(envelope["models"]) == 2 and
            {m["model_id"] for m in envelope["models"]} ==
            {"W4-imported-" + comparison["before"], "W4-imported-" + comparison["after"]},
            "W4 models must remain imported source partitions")
    for a, b in zip(ordered, envelope["observations"]):
        require(all(b[k] == a.get(k) for k in
                    ("id", "text_sha256", "parent_id", "meeting_id",
                     "source_family_id", "source_url", "json_pointer", "date", "country")),
                "Interchange source ID, SHA, URL or meeting lineage differs")
        require(b["source_url"] is None and "text" not in b,
                "No original URL or transcript text in synthetic browser")
    require(envelope["cohort"]["weighting"] == "equal_meeting",
            "W4's declared per-meeting weighting was changed")
    expected = {r["id"]: r for r in ordered if _eligible(r)}
    coordinate_rows = comparison.get("aligned_coordinates", [])
    by_id = {}
    for row in coordinate_rows:
        original = expected.get(row["observation_id"])
        require(original is not None and row["observation_id"] not in by_id,
                "W4 aligned row absent, duplicated, excluded or unavailable")
        require(row["period"] == original["period"] and
                row["actor_id"] == original["actor_id"] and
                row["meeting_id"] == original["meeting_id"] and
                row["source_family_id"] == original["source_family_id"] and
                row["map_fit_id"] == original["map_fit_id"] and
                row["coordinate_kind"] == "aligned_display_only",
                "W4 aligned point lost actor, meeting, map or source lineage")
        coords = row["coordinates"]
        require(isinstance(coords, list) and len(coords) == source["map_space"]["dimension"] and
                all(isinstance(v, (float, int)) and math.isfinite(v) and
                    abs(v) <= SCORE_BOUND for v in coords),
                "W4 aligned coordinates are nonfinite or incompatible")
        by_id[row["observation_id"]] = row
    if comparison.get("comparison_status") != "withheld":
        require(set(by_id) == set(expected),
                "W4 source-linked coordinate coverage is incomplete")
    for m in envelope["models"]:
        require(m["representation_id"] == source["feature_space"]["id"] and
                m["representation_version"] == source["feature_space"]["version"],
                "Frozen input representation does not match the imported fit")
        fit_rows = [r for r in envelope["results"] if r["model_id"] == m["model_id"]]
        require(len(fit_rows) == len(ordered) and
                {r["observation_id"] for r in fit_rows} == {r["id"] for r in ordered},
                "A W4 imported fit silently dropped source/missing records")


def to_w6_longitudinal(source: dict, comparison: dict, envelope: dict,
                       *, selection_checked: bool = False) -> dict:
    """Produce an evidence-linked W6 panel with explicit withholding.

    selection_checked is an *engineering-fixture* assertion; the implementation
    separately checks overlapping source-family series and matched genres.
    It is not automatically generalized to a real historical sampling design.
    """
    validate_source(source, comparison, envelope)
    require(type(selection_checked) is bool, "Explicit selection-check flag required")
    before, after = comparison["before"], comparison["after"]
    periods = {p["id"]: {"start": p["start"], "end": p["end"]}
               for p in source["periods"] if p["id"] in (before, after)}
    raw = [r for r in source["observations"] if r["period"] in (before, after)]
    available = [r for r in raw if _eligible(r) and r.get("actor_id")]
    actors = sorted({r["actor_id"] for r in available})
    require(len(actors) <= MAX_ACTORS,
            "Actor count exceeds W6's 30-actor limit: withhold, never sample")
    by_coord = {r["observation_id"]: r["coordinates"]
                for r in comparison["aligned_coordinates"]}
    by_period = {period: [r for r in available if r["period"] == period]
                 for period in (before, after)}
    source_groups = [
        {r["source_family_id"] for r in by_period[period]} for period in (before, after)
    ]
    paired_groups = source_groups[0] & source_groups[1]
    genres = w4.matched_genres(raw, before, after)
    comparable = bool(selection_checked and paired_groups)
    mode = comparison["alignment"].get("mode")
    full_refit = mode == "rigid_full_refit"
    pinned = mode == "identity_pinned_transform"
    required_anchors = source["map_space"]["dimension"] + 2
    all_map_fits = {r["map_fit_id"] for r in available}
    map_good = pinned and len(all_map_fits) == 1
    if full_refit:
        diag = comparison["alignment"]
        cond = diag.get("condition_number")
        residual = diag.get("anchor_relative_rmse")
        map_good = (isinstance(cond, (float, int)) and math.isfinite(cond)
                    and cond <= 1e7 and isinstance(residual, (float, int))
                    and math.isfinite(residual) and residual <= .15
                    and diag.get("anchor_count", 0) >= required_anchors
                    and not diag.get("scaling_applied", True))
    status = "passed" if map_good and comparable else "failed"
    why = None if status == "passed" else (
        "No independently declared shared synthetic source-series selection"
        if not comparable else "Pinned transform or stable full-rank alignment not verified"
    )
    rows = []
    for actor in actors:
        own = {period: [r for r in by_period[period] if r["actor_id"] == actor]
               for period in (before, after)}
        present = [period for period in (before, after) if own[period]]
        roster = ("matched" if len(present) == 2 and genres.get(actor) else
                  "changing_roster" if len(present) == 2 else
                  "arrival" if present == [after] else "departure")
        # W4 aggregate weighting is exactly equal meeting within genre then
        # equal genre within actor-period. For matched actors, use only genres
        # observed in BOTH periods, as W4 actor_distances() does.
        used = {}
        for period in (before, after):
            own_rows = own[period]
            if len(present) == 2:
                selected = [r for r in own_rows if r["genre"] in genres.get(actor, set())]
            else:
                selected = own_rows
            used[period] = selected
        positions = []
        for period in (before, after):
            selected = used[period]
            if not selected:
                omitted = own[period]
                positions.append({
                    "period": period, "status": "withheld" if omitted else "missing",
                    "xy": None, "radius": None, "n": len(omitted),
                    "observation_ids": [r["id"] for r in omitted],
                    "reason": ("No matched genre across periods" if omitted else
                               "Actor missing in this period")
                })
                continue
            if not map_good or not comparable:
                positions.append({
                    "period": period, "status": "withheld", "xy": None,
                    "radius": None, "n": len(selected),
                    "observation_ids": [r["id"] for r in selected],
                    "reason": why
                })
                continue
            # Adapt W4's own equal-meeting/equal-genre vector aggregator to
            # already-aligned display coordinates, not a high-dimensional
            # refit. The result remains descriptive (no uncertainty circle).
            records = [{**r, "vector": by_coord[r["id"]]} for r in selected]
            xy = w4._actor_map(records, period, vector_key="vector")[actor]
            require(len(xy) == 2 and all(math.isfinite(float(x)) for x in xy),
                    "Invalid weighted W4 actor map")
            positions.append({
                "period": period, "status": "observed", "xy": [float(x) for x in xy],
                "radius": None, "n": len(selected),
                "observation_ids": [r["id"] for r in selected],
                "reason": None
            })
        rows.append({
            "id": actor, "label": actor, "roster_status": roster,
            "attribution_status": "Synthetic actor only; not a verified diplomat/country",
            "positions": positions
        })
    model = envelope["models"][0]
    panel = {
        "kind": "longitudinal",
        "status": "ready" if map_good and comparable else "withheld",
        "reason": why,
        "measure": "Pre-aligned source-level W4 display coordinates; actor-period positions " +
                   "are equal-meeting-within-genre then equal-genre descriptive means, " +
                   "restricted to shared genres for matched actors. Not high-dimensional " +
                   "movement, a political position or a confidence region.",
        "identity": {
            "source_schema": envelope["upstream"]["source_schema"],
            "source_hash_basis": envelope["upstream"]["source_hash_basis"],
            "source_sha256": envelope["upstream"]["source_sha256"],
            "selection_sha256": envelope["upstream"]["selection_sha256"],
            "unit": envelope["cohort"]["unit"],
            "weighting": envelope["cohort"]["weighting"],
            "representation_id": model["representation_id"],
            "representation_version": model["representation_version"],
            "observation_refs": [
                {"id": r["id"], "text_sha256": r["text_sha256"]}
                for r in envelope["observations"] if _eligible(r)
            ]
        },
        "coverage": {
            "frame": envelope["cohort"]["total_in_frame"],
            "eligible": envelope["cohort"]["eligible"],
            "included": sum(len(p["observation_ids"]) for a in rows for p in a["positions"]
                            if p["status"] == "observed") if map_good and comparable else 0,
            "excluded": envelope["coverage"]["excluded"],
            "missing": envelope["coverage"]["unavailable_sources"]
        },
        "warnings": [
            "Synthetic engineering only; W4 display geometry is not calibrated political motion.",
            "Roster shift and changing genre/source coverage can change group positions.",
            "Aligned source points have no actor-level confidence circles; radius withheld.",
            f"Paired source-family series: {len(paired_groups)}. Synthetic source-selection review: " +
            ("declared" if selection_checked else "NOT assessed"),
            "W4 grouped uncertainty: " + comparison["uncertainty"]["status"] +
            "; sensitivity, never a sampling confidence interval."
        ],
        "periods": [before, after], "period_bounds": periods,
        "alignments": [{
            "from": before, "to": after,
            "mode": mode, "map_dimension": source["map_space"]["dimension"],
            "anchors": comparison["alignment"].get("anchor_count", 0),
            "reference_basis": model["representation_id"],
            "selection_comparability": "checked" if comparable else "not_assessed",
            "status": status, "rank_ok": bool(map_good),
            "degeneracy_ok": bool(map_good),
            "uncertainty_status": comparison["uncertainty"]["status"]
        }],
        "actors": rows
    }
    require(panel["coverage"]["included"] <= panel["coverage"]["eligible"],
            "W4 display source denominator exceeds original eligibility")
    return panel
