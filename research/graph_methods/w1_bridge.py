"""Optional W1 source-aware validation bridge; refuses unaccepted/unavailable code.

W1 is maintained in a different workstream (Node). This adapter calls the actual
checkout's accepted W1 validators, not an independent approximation of its metrics.
W1 files must be integrated into this checkout by the coordinator first; caller
must supply a coordinator-pinned W1 runner SHA-256 matching both code and receipt.
No unmerged branch import, source-text exposure, or network access is performed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import numpy as np

from .core import GraphError, is_sha, validate_input

ROOT = Path(__file__).resolve().parents[2]
W1_DIR = Path("research/validation_framework")
ALLOWED_W1_ADAPTER = "source-validation-1.0.0"
ALLOWED_W1_ENVELOPE = "un.parallel-analysis.v1"

# Only strict, source-linked, experimental, data-free evidence may be paired.
W1_NODE_CODE = r"""
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const root=process.cwd();
const I=require(path.join(root,'research/validation_framework/interchange.cjs'));
const M=require(path.join(root,'research/validation_framework/metrics.cjs'));
const F=require(path.join(root,'research/validation_framework/frame.cjs'));
const payload=JSON.parse(fs.readFileSync(0,'utf8'));
I.validateRelational(payload.envelope);
const population=F.validateFrame(payload.frame);
if(population.selection_sha256!==payload.envelope.upstream.selection_sha256)
  throw Error('W1 raw frame/selected IDs and interchange export disagree');
if(population.eligible.length!==payload.left.length||
   population.excluded.length!==payload.envelope.coverage.excluded)
  throw Error('W1 native validated-frame denominator mismatch');
const audit=F.auditSources(population.eligible);
const schedule=F.schedule(population.eligible,'meeting',2,0.8,31);
if(payload.left!==null && payload.right!==null){
  const result=M.evaluateAssignments(payload.left,payload.right);
  process.stdout.write(JSON.stringify({status:'validated',metrics:result,
    source_validation:{
      eligible:population.eligible.length,excluded:population.excluded.length,
      selection_sha256:population.selection_sha256,
      meeting_group_schedule:{
        status:schedule.status,groups:schedule.groups,
        attempted:schedule.attempted,reason:schedule.reason||null
      },
      largest_meeting_share:audit.largest_meeting_share,
      duplicate_text_groups:audit.duplicate_text_groups,
      missing_affiliation_count:audit.missing_affiliation_count
    }}));
}else{
  process.stdout.write(JSON.stringify({status:'validated',metrics:null}));
}
"""


def _w1_files(repo_root: Path) -> tuple[Path, Path]:
    root = repo_root.resolve()
    directory = root / W1_DIR
    runner = directory / "runner.cjs"
    bridge = directory / "interchange.cjs"
    metrics = directory / "metrics.cjs"
    frame = directory / "frame.cjs"
    if not all(p.is_file() and not p.is_symlink() for p in (runner, bridge, metrics, frame)):
        raise GraphError(
            "W1 unavailable: coordinator must merge and accept PR #19 before the graph bridge can activate"
        )
    if not all(p.resolve().is_relative_to(root) for p in (runner, bridge, metrics, frame)):
        raise GraphError("Refuse W1 code outside the declared repository checkout")
    return runner, bridge


def availability(repo_root: Path = ROOT) -> dict:
    """Read-only gate; does not infer approval from passing upstream CI."""
    try:
        _w1_files(repo_root)
    except GraphError as exc:
        return {"status": "withheld", "reason": str(exc),
                "upstream_pr": 19, "needed": "coordinator-merged W1 + pinned producer SHA"}
    return {"status": "installed_unapproved",
            "reason": "Installed files alone are not coordinator acceptance",
            "upstream_pr": 19, "needed": "pinned SHA and matched W1 receipt"}


def _require_approval(approval: dict, code_sha: str) -> None:
    if not isinstance(approval, dict) or approval.get("schema") != "un.w1-approval.v1":
        raise GraphError("Coordinator W1 approval record is required; never auto-approve")
    if (approval.get("adapter_version") != ALLOWED_W1_ADAPTER or
            approval.get("w1_producer_code_sha256") != code_sha or
            not is_sha(code_sha)):
        raise GraphError("W1 approved adapter version / executable hash mismatch")
    merged_sha = approval.get("w1_merged_commit_sha")
    if not (isinstance(merged_sha, str) and len(merged_sha) == 40 and
            all(char in "0123456789abcdef" for char in merged_sha)):
        raise GraphError("W1 merged commit SHA-1 (40 hexadecimal characters) required")
    if approval.get("accepted") is not True:
        raise GraphError("W1 acceptance not granted")
    # Approval remains a coordinator-controlled local decision; verifying
    # checkout ancestry additionally blocks arbitrary/unmerged commit claims.


def _load_w1_model(envelope: dict, model_id: str, manifest: dict) -> tuple[list[int], dict]:
    model = next((m for m in envelope["models"] if m["model_id"] == model_id), None)
    if model is None:
        raise GraphError("Named W1 comparison model absent")
    rep = manifest["representation"]
    if model["representation_id"] != rep["id"] or model["representation_version"] != rep["version"]:
        raise GraphError("W1 and W3 do not share a pinned representation basis/version")
    if model.get("training_selection_sha256") != rep["training_selection_sha256"]:
        raise GraphError("W1 and W3 fitted-representation training selections differ")
    if model.get("fit_split") != manifest["split"]:
        raise GraphError("W1 model was fitted on a different source split")
    n = len(manifest["observations"])
    mapping: dict[str, dict] = {}
    for row in envelope["results"]:
        if row["model_id"] != model_id:
            continue
        if row["observation_id"] in mapping:
            raise GraphError("W1 duplicate model-observation result")
        mapping[row["observation_id"]] = row
    out = []
    for row in manifest["observations"]:
        found = mapping.get(row["id"])
        if found is None or found["status"] not in {"assigned", "unassigned"}:
            raise GraphError("W1 reference model does not cover all comparable graph observations")
        value = found["cluster"]
        if not isinstance(value, int) or value < 0 or (
            found["status"] == "assigned" and value < 1
        ) or (found["status"] == "unassigned" and value != 0):
            raise GraphError("W1 hard assignments must be valid and explicitly unassigned when noise")
        out.append(value)
    if len(out) != n:
        raise GraphError("Unmatched W1 source population")
    return out, model


def _compare_identities(manifest: dict, envelope: dict) -> None:
    if envelope.get("schema") != ALLOWED_W1_ENVELOPE or envelope.get("contract_version") != "1.0.0":
        raise GraphError("W1 result has incompatible interchange contract")
    if envelope.get("publication_eligible") is not False or envelope.get("evaluation_role") != "engineering_only":
        raise GraphError("W1 export attempted to promote statistical/publication claims")
    cohort = envelope["cohort"]
    if cohort["split"] != manifest["split"]:
        raise GraphError("W1/W3 source split mismatch")
    if cohort["eligible"] != len(manifest["observations"]):
        raise GraphError("W1/W3 eligible cohort denominator differs")
    total = len(manifest["observations"]) + len(manifest.get("excluded_observations", []))
    if cohort["total_in_frame"] != manifest["total_in_frame"] or total != len(envelope["observations"]):
        raise GraphError("W1/W3 source frame and missingness denominator differ")
    for key in ("source_schema", "source_engine", "source_hash_basis",
                "source_sha256", "selection_sha256"):
        if envelope["upstream"].get(key) != manifest["upstream"].get(key):
            raise GraphError("W1/W3 upstream source/hash/selection lineage mismatch: " + key)
    # If one producer cannot declare a frame/review digest, do not assert that
    # presence on only the other side constitutes a verified exact match.
    for key in ("frame_sha256", "corpus_sha256", "review_sha256"):
        a, b = envelope["upstream"].get(key), manifest["upstream"].get(key)
        if a is not None and b is not None and a != b:
            raise GraphError("W1/W3 upstream optional digest differs: " + key)
    def pairs(rows: list[dict]) -> list[tuple[str, str | None]]:
        return [(r["id"], r.get("text_sha256")) for r in rows]
    included = [r for r in envelope["observations"]
                if r["source_status"] == "available" and not r["exclusion_reasons"]]
    excluded = [r for r in envelope["observations"]
                if r["source_status"] != "available" or r["exclusion_reasons"]]
    if pairs(included) != pairs(manifest["observations"]):
        raise GraphError("W1/W3 included observation order, IDs or original text hashes differ")
    if pairs(excluded) != pairs(manifest.get("excluded_observations", [])):
        raise GraphError("W1/W3 excluded/missing observation identities differ")
    for w1, w3 in zip(included + excluded,
                      manifest["observations"] + manifest.get("excluded_observations", [])):
        for key in ("parent_id", "parent_text_sha256", "meeting_id", "source_family_id",
                    "speech_id", "date", "source_status", "source_url", "json_pointer",
                    "start", "end", "country", "missing_reason",
                    "review_status", "exclusion_reasons"):
            left = w1.get(key, []) if key == "exclusion_reasons" else w1.get(key)
            right = w3.get(key, []) if key == "exclusion_reasons" else w3.get(key)
            if left != right:
                raise GraphError("W1/W3 source identity/attribution mismatch: " + key)
    if (envelope["coverage"]["eligible"] != len(included) or
            envelope["coverage"]["excluded"] != len(excluded) or
            envelope["coverage"]["unavailable_sources"] !=
            manifest.get("unavailable_sources", 0)):
        raise GraphError("W1/W3 coverage inventory mismatch")


def _w1_source_frame(manifest: dict) -> dict:
    """Construct W1's metadata-only *real* source-frame validator input."""
    schema = manifest["upstream"]["source_schema"]
    if schema == "synthetic.v1":
        schema = "un.source-validation.synthetic.v1"
    if schema not in {
        "un.source-validation.synthetic.v1", "un.browser.corpus.v1",
        "un.passage-corpus.v1", "un.review.v1",
    }:
        raise GraphError("W1 frame validator lacks an accepted adapter for this source schema")
    observations = [
        {**row, "split": manifest["split"],
         "exclusion_reasons": row.get("exclusion_reasons", [])}
        for row in manifest["observations"] + manifest.get("excluded_observations", [])
    ]
    upstream = manifest["upstream"]
    return {
        "schema": "un.source-validation.frame.v1",
        "split": manifest["split"], "source_schema": schema,
        "source_engine": upstream["source_engine"],
        "source_hash_basis": upstream["source_hash_basis"],
        "source_sha256": upstream["source_sha256"],
        "selection_sha256": upstream["selection_sha256"],
        "unit": manifest.get("unit", "passage"),
        "inventory_meetings": manifest["inventory_meetings"],
        "observations": observations,
    }


def compare_w1_partition(manifest: dict, values: np.ndarray, spectral: dict,
                         w1_envelope: dict, approval: dict, *,
                         w1_model_id: str, repo_root: Path = ROOT) -> dict:
    """Run W1's real assignment metrics only after coordinator-pinned integration.

    External approval is a local pin; the coordinator must separately prove the
    merge SHA is on main. This function does not merge or modify source/heldout.
    """
    validate_input(manifest, values)
    runner, _ = _w1_files(repo_root)
    code_sha = hashlib.sha256(runner.read_bytes()).hexdigest()
    _require_approval(approval, code_sha)
    # Explicit approval must also name an existing commit reachable from the
    # checkout. PR runs check out GitHub's synthetic merge, where W1 main
    # ancestry is retained; an unmerged W1 PR does not pass this gate.
    try:
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", approval["w1_merged_commit_sha"], "HEAD"],
            cwd=repo_root.resolve(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GraphError("Cannot verify accepted W1 merge is in checkout ancestry") from exc
    if ancestry.returncode != 0:
        raise GraphError("Approved W1 commit is not an ancestor of this checkout; refuse draft branch")
    if w1_envelope.get("producer", {}).get("workstream_id") != "W1" or (
        w1_envelope["producer"].get("adapter_version") != ALLOWED_W1_ADAPTER or
        w1_envelope["producer"].get("code_sha256") != code_sha
    ):
        raise GraphError("W1 producer identity/version/hash not pinned to accepted local code")
    _compare_identities(manifest, w1_envelope)
    if spectral.get("method") != "spectral" or spectral.get("status") != "fitted":
        raise GraphError("W3 reference is not a fitted spectral partition")
    s_labels = np.asarray(spectral.get("labels"))
    if s_labels.shape != (len(values),) or not np.issubdtype(s_labels.dtype, np.integer):
        raise GraphError("Spectral row labels invalid")
    w1_labels, ref_model = _load_w1_model(w1_envelope, w1_model_id, manifest)
    if np.any(s_labels < 1) or len(np.unique(s_labels)) < 2:
        raise GraphError("Spectral cluster IDs invalid or degenerate")
    try:
        from jsonschema import Draft202012Validator, FormatChecker
        schema_file = repo_root / "docs/parallel-work/interchange-v1.schema.json"
        schema = json.loads(schema_file.read_text(encoding="utf8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(w1_envelope)
    except Exception as exc:
        raise GraphError("W1 v1 structural schema verification refused") from exc
    payload = {"envelope": w1_envelope, "frame": _w1_source_frame(manifest),
               "left": w1_labels, "right": s_labels.tolist()}
    try:
        result = subprocess.run(
            ["node", "-e", W1_NODE_CODE], cwd=repo_root.resolve(),
            input=json.dumps(payload, separators=(",", ":"), allow_nan=False),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GraphError("Accepted W1 Node validator could not execute") from exc
    if result.returncode != 0:
        raise GraphError("Accepted W1 validator refused result: " + result.stderr.strip()[:240])
    try:
        validated = json.loads(result.stdout)
    except ValueError as exc:
        raise GraphError("Accepted W1 validator did not return JSON") from exc
    if validated.get("status") != "validated" or not isinstance(validated.get("metrics"), dict):
        raise GraphError("Accepted W1 metrics did not produce a validated comparison")
    assessable = (validated["metrics"].get("ari") is not None and
                  validated["metrics"].get("adjusted_mutual_information") is not None)
    return {
        "schema": "un.w1-w3-comparison.v1",
        "status": "descriptive" if assessable else "inconclusive",
        "w1_model_id": w1_model_id, "w1_model_basis": ref_model["representation_id"],
        "w1_version": ALLOWED_W1_ADAPTER, "w1_code_sha256": code_sha,
        "w1_accepted_commit_sha": approval["w1_merged_commit_sha"],
        "source_sha256": manifest["upstream"]["source_sha256"],
        "selection_sha256": manifest["upstream"]["selection_sha256"],
        "observation_count": len(values),
        "metrics": validated["metrics"],
        "source_validation": validated["source_validation"],
        "publication_eligible": False,
        "comparison_protocol": "same_source_and_underlying_representation_identity",
        "limitation": ("W1 assignment metrics on the same original IDs and pinned underlying "
                       "representation identity; W1 may refit PCA on that representation, "
                       "so this does not certify identical fitted distances or a shared "
                       "coordinate basis. Group resampling and null evidence are separate. "
                       "No political alignment, causal diffusion or p-value claimed."),
    }
