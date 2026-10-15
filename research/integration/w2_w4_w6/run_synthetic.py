"""Generate synthetic W4 source-bound W6-read models, never private outputs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from research.longitudinal.fixtures import make_panel
from research.longitudinal.framework import compare, to_interchange_v1
from research.integration.w2_w4_w6.w4_bridge import to_w6_longitudinal


def generate(folder: Path, *, fit_policy: str = "full_refit",
             unavailable_family: tuple[str, int] | None = None) -> dict:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    if list(folder.iterdir()):
        raise ValueError("Refuse to overwrite a non-empty synthetic output directory")
    source = make_panel(motion=True, fit_policy=fit_policy,
                        unavailable_family=unavailable_family)
    comparison = compare(source, "p0", "p1",
                         anchor_ids=[f"A{i}" for i in range(6)],
                         bootstrap_reps=50, bootstrap_seed=30092026)
    envelope = to_interchange_v1(source, comparison)
    result = to_w6_longitudinal(source, comparison, envelope,
                               selection_checked=True)
    # Publishable *only as user-selected synthetic test inputs*. No real
    # transcripts, private rows or model embeddings may enter this producer.
    # The companion manifest binds exact file bytes, not original UN source
    # provenance or a cryptographic signature. The browser verifies all four.
    originals = (
        ("w4-source-panel.json", source),
        ("w4-analysis.json", comparison),
        ("w4-envelope.json", envelope),
        ("w4-panel.json", result),
    )
    checksums = {}
    for name, data in originals:
        payload = (json.dumps(data, indent=2, allow_nan=False) + "\n").encode("utf-8")
        (folder / name).write_bytes(payload)
        checksums[name] = hashlib.sha256(payload).hexdigest()
    (folder / "SHA256.json").write_text(
        json.dumps(checksums, indent=2) + "\n", encoding="utf-8"
    )
    receipt = {
        "workstream": "W4", "result": "synthetic_only",
        "source_records": len(envelope["observations"]),
        "eligible": envelope["coverage"]["eligible"],
        "excluded": envelope["coverage"]["excluded"],
        "unavailable_source_groups": envelope["coverage"]["unavailable_sources"],
        "unavailable_observation_rows": sum(o["source_status"] != "available"
                                            for o in envelope["observations"]),
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
    parser.add_argument("--missing-late-family", action="store_true",
                        help="Create 11 missing synthetic observations from one source family")
    args = parser.parse_args()
    print(json.dumps(generate(args.output, fit_policy=(
        "transformed_reference" if args.pinned else "full_refit"),
        unavailable_family=("p1", 7) if args.missing_late_family else None)))


if __name__ == "__main__":
    main()
