"""Render deterministic, source-free synthetic evidence-first demo reports.

Usage: python3 research/diplomatic_readouts/examples/generate.py --output /tmp/unga-demo
Only writes to a NEW or empty destination. No network or empirical UN sources.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from readout import TEMPLATES, export, normalize, report_digest  # noqa: E402
from fixtures import fixture, refresh  # noqa: E402


def scenarios():
    """Yield (name, report, authentic text receipts, independent synthetic verdict)."""
    report, proofs, decision = fixture()
    yield "complete", report, proofs, decision

    descriptive, proofs, decision = fixture("descriptive")
    exploratory, _, _ = fixture("exploratory")
    second = deepcopy(exploratory["findings"][0])
    second["id"] = "fictional:f2"
    descriptive["findings"].append(second)
    decision = replace(refresh(descriptive, decision), statistical_gate="fail")
    yield "partial", descriptive, proofs, decision

    report, proofs, decision = fixture()
    decision = replace(decision, source_gate="fail", reviewer_gate="not_run")
    yield "abstaining", report, proofs, decision

    report, proofs, decision = fixture()
    proofs["synthetic:A"] = replace(proofs["synthetic:A"], accepted=False)
    yield "failed_source", report, proofs, decision

    report, proofs, decision = fixture()
    report["findings"][0]["supporting"] = []
    yield "missing_evidence", report, proofs, refresh(report, decision)

    for template in TEMPLATES:
        report, proofs, decision = fixture()
        report["template"] = template
        yield "template_" + template, report, proofs, refresh(report, decision)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path,
                        help="New/empty local output directory (no overwrites)")
    args = parser.parse_args(argv)
    root = args.output
    if root.is_symlink() or root.exists() and (not root.is_dir() or any(root.iterdir())):
        parser.error("output must be a new or empty nonsymlink directory")
    cases = list(scenarios())
    root.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, report, proofs, decision in cases:
        result = normalize(report, proofs, decision)
        hashes = export(report, root / name, proofs=proofs, decision=decision)
        results[name] = {"release_state": result["release_state"],
                         "report_digest": report_digest(report), "files_sha256": hashes,
                         "validation_errors": result["validation_errors"]}
        print(f"{name:36} {result['release_state']}")
    assert results["complete"]["release_state"] == "synthetic_demo"
    assert results["partial"]["release_state"] == "descriptive_only"
    assert results["abstaining"]["release_state"] == "withheld"
    assert results["failed_source"]["release_state"] == "withheld"
    assert results["missing_evidence"]["release_state"] == "withheld"
    receipt = {"generator": "offline_synthetic_v1", "schema": "un.diplomatic-readout.v1",
               "publication_eligible": False, "cases": results}
    (root / "manifest.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print("manifest_sha256", sha256((root / "manifest.json").read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
