"""Build native W3 source-linked synthetic artifacts for coordinator-only QA.

Creates three W3-generated cohorts: small full (24), small with one explicitly
unavailable source (24+1), and untrimmed (96). No download or real transcripts.
"""
from __future__ import annotations

import argparse
import copy
from pathlib import Path

from research.graph_methods.core import digest, matrix_digest, validate_input
from research.graph_methods.reproduce import fixture, run


def small(kind: str):
    manifest, x, labels = fixture(81)
    if kind == "large":
        return manifest, x, labels
    if kind not in {"small", "missing"}:
        raise ValueError("Only explicitly synthetic scenarios allowed")
    m = copy.deepcopy(manifest)
    x = x[:24, :].copy()
    labels = labels[:24].copy()
    m["observations"] = m["observations"][:24]
    pairs = [[o["id"], o["text_sha256"]] for o in m["observations"]]
    m["observation_join_sha256"] = digest(pairs)
    m["upstream"]["source_sha256"] = digest({"kind": kind, "rows": pairs, "version": 1})
    m["upstream"]["selection_sha256"] = digest(pairs)
    m["representation"]["id"] = "fictional-graph-geometry-24-" + kind
    m["representation"]["matrix_sha256"] = matrix_digest(x)
    m["representation"]["training_selection_sha256"] = digest(
        {"source": m["upstream"]["source_sha256"], "basis": "synthetic-fixture-v1"}
    )
    m["total_in_frame"] = len(x)
    m["selection_policy"] = "first 24 fictional rows, no real transcripts"
    m["unavailable_sources"] = 0
    if kind == "missing":
        extra = {
            "id": "fictional-unavailable-001",
            "text_sha256": None,
            "parent_id": None, "parent_text_sha256": None,
            "meeting_id": "fictional-missing-meeting",
            "speech_id": None, "source_family_id": "fictional-missing-family",
            "date": "2026-10-01", "country": None,
            "source_url": None, "json_pointer": None,
            "start": None, "end": None,
            "unit": "synthetic", "split": "synthetic",
            "review_status": "not_applicable",
            "exclusion_reasons": ["source_unavailable"],
            "source_status": "unavailable",
            "missing_reason": "Fictional meeting: no source text collected",
        }
        m["excluded_observations"] = [extra]
        m["frame_join_sha256"] = digest(pairs + [[extra["id"], None]])
        m["inventory_meetings"] = 7
        m["total_in_frame"] = 25
        m["unavailable_sources"] = 1
        m["selection_policy"] += "; one explicit missing inventory source"
    validate_input(m, x)
    return m, x, labels


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    destination = args.output.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Fixture output directory must be empty")
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("small", "missing", "large"):
        m, x, labels = small(name)
        result = run(m, x, destination / name, seed=81, synthetic_labels=labels)
        assert result["publication_eligible"] is False
        assert result["heldout_transcripts_opened"] == 0
        assert result["attempts"]["planned_primary"] == 2
        print(f"SYNTHETIC W3 {name}: eligible={len(x)} frame={m['total_in_frame']} "
              f"graph_edges={result['graph']['edge_count']} "
              f"fits={result['attempts']['successful_primary']}/2")


if __name__ == "__main__":
    main()
