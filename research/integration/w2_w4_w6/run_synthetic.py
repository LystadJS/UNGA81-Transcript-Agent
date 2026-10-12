"""Generate synthetic W4 source-bound W6-read models, never private outputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from research.longitudinal.fixtures import make_panel
from research.longitudinal.framework import compare, to_interchange_v1
from research.integration.w2_w4_w6.w4_bridge import to_w6_longitudinal


def generate(folder: Path, *, fit_policy: str = "full_refit") -> dict:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    if list(folder.iterdir()):
        raise ValueError("Refuse to overwrite a non-empty synthetic output directory")
    source = make_panel(motion=True, fit_policy=fit_policy)
    comparison = compare(source, "p0", "p1",
                         anchor_ids=[f"A{i}" for i in range(6)],
                         bootstrap_reps=50, bootstrap_seed=30092026)
    envelope = to_interchange_v1(source, comparison)
    result = to_w6_longitudinal(source, comparison, envelope,
                               selection_checked=True)
    for name, data in (
        ("w4-envelope.json", envelope),
        ("w4-panel.json", result),
    ):
        (folder / name).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    receipt = {
        "workstream": "W4", "result": "synthetic_only",
        "source_records": len(envelope["observations"]),
        "eligible": envelope["coverage"]["eligible"],
        "excluded": envelope["coverage"]["excluded"],
        "actors": len(result["actors"]),
        "map_mode": result["alignments"][0]["mode"],
        "uncertainty": result["alignments"][0]["uncertainty_status"],
        "publication_eligible": False, "holdout_transcripts_opened": 0
    }
    (folder / "w4-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pinned", action="store_true")
    args = parser.parse_args()
    print(json.dumps(generate(args.output, fit_policy=(
        "transformed_reference" if args.pinned else "full_refit"))))


if __name__ == "__main__":
    main()
