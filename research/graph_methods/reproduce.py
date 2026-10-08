"""Reproduce bounded synthetic graph experiments or inspect a local authorized cohort.

CLI must never fetch transcripts, run model inference, or access the reserved holdout.
Output is local; never commit development source-linked rows or fitted coordinates.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import make_blobs

from .algorithms import (
    DiffusionPolicy, SpectralPolicy, baseline_comparison, diffusion_map,
    fidelity, grouped_leave_one_out, parameter_sensitivity, spectral_clustering,
)
from .core import GraphError, GraphPolicy, build_affinity, digest, matrix_digest, validate_input
from .interchange import code_digest, paired_representations, to_interchange_v1


def fixture(seed: int = 81) -> tuple[dict, np.ndarray, np.ndarray]:
    """Invented points and IDs; no UN text, country assertions or pseudogold."""
    x, labels = make_blobs(
        n_samples=96, centers=np.array([[-1.35, 0], [0, 0.3], [1.35, 0]]),
        cluster_std=0.69, random_state=seed,
    )
    # Preserve exact row-to-source correspondence; grouping is synthetic, not IID.
    rows = []
    for i in range(len(x)):
        rows.append({
            "id": f"fictional-{i:04d}",
            "text_sha256": hashlib.sha256(f"invented-geometry-{seed}-{i}".encode()).hexdigest(),
            "parent_id": f"fictional-parent-{i // 3:03d}",
            "parent_text_sha256": hashlib.sha256(f"fictional-parent-{i // 3:03d}".encode()).hexdigest(),
            "meeting_id": f"fictional-meeting-{i % 6}", "speech_id": None,
            "source_family_id": f"fictional-family-{i % 4}", "date": "2026-10-01",
            "country": None, "source_url": None, "json_pointer": None,
            "start": None, "end": None, "review_status": "not_applicable",
            "source_status": "available", "unit": "synthetic", "split": "synthetic",
        })
    sha = digest(rows)
    source_identity = digest({"fixture": sha, "seed": seed})
    m = {
        "schema": "un.graph-input.v1", "split": "synthetic",
        "upstream": {
            "source_schema": "synthetic.v1", "source_engine": "synthetic-blobs-v1",
            "source_hash_basis": "synthetic", "source_sha256": source_identity,
            "selection_sha256": digest([[r["id"], r["text_sha256"]] for r in rows]),
            "frame_sha256": None, "corpus_sha256": None, "review_sha256": None,
        },
        "representation": {
            "id": f"fictional-blob-geometry-seed-{seed}",
            "version": "1", "feature_basis": "synthetic", "distance_geometry": "euclidean",
            "matrix_sha256": matrix_digest(x),
            "training_selection_sha256": digest(["geometry-fit", source_identity]),
        },
        "population": "fictional_overlapping_blobs", "unit": "synthetic",
        "source_group_unit": "meeting", "selection_policy": "all 96 invented points",
        "weighting": "equal_passage", "duplicate_policy": "retain_and_audit",
        "inventory_meetings": 6, "total_in_frame": len(x), "unavailable_sources": 0,
        "observations": rows, "observation_join_sha256": digest(
            [[r["id"], r["text_sha256"]] for r in rows]),
    }
    validate_input(m, x)
    return m, x, labels


def local_source(manifest_path: Path, vectors_path: Path) -> tuple[dict, np.ndarray]:
    """Allow only explicitly supplied files; no URL loading or transcript parsing."""
    if manifest_path.stat().st_size > 2_000_000 or vectors_path.stat().st_size > 32_000_000:
        raise GraphError("Local manifest/matrix exceeds bounded input size")
    manifest = json.loads(manifest_path.read_text(encoding="utf8"))
    if manifest.get("split") != "development":
        raise GraphError("Use --fixture for synthetic; external inputs must be authorized development")
    with np.load(vectors_path, allow_pickle=False) as f:
        if set(f.files) != {"X"}:
            raise GraphError("Vector archive must contain precisely X; no object arrays")
        x = f["X"].astype(np.float64)
    validate_input(manifest, x)
    return manifest, x


def variations(policy: GraphPolicy, n: int) -> list[GraphPolicy]:
    variants = [
        replace(policy, n_neighbors=max(1, policy.n_neighbors - 4)),
        replace(policy, n_neighbors=min(n - 1, policy.n_neighbors + 4)),
        replace(policy, bandwidth=policy.bandwidth / 2),
        replace(policy, bandwidth=policy.bandwidth * 2),
    ]
    unique = {digest(asdict(p)): p for p in variants if p != policy}
    return list(unique.values())


def jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {key: jsonable(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(value) for value in obj]
    if isinstance(obj, np.ndarray):
        return jsonable(obj.tolist())
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, Path):
        return str(obj)
    return obj


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(jsonable(value), indent=2, sort_keys=True,
                               allow_nan=False) + "\n", encoding="utf8")


def source_edges(manifest: dict, graph) -> list[dict]:
    rows = manifest["observations"]
    i, j = np.where(np.triu(graph.weights, k=1) > 0)
    return [{
        "from_id": rows[a]["id"], "from_text_sha256": rows[a]["text_sha256"],
        "from_parent_id": rows[a].get("parent_id"), "from_meeting_id": rows[a].get("meeting_id"),
        "from_source_url": rows[a].get("source_url"),
        "to_id": rows[b]["id"], "to_text_sha256": rows[b]["text_sha256"],
        "to_parent_id": rows[b].get("parent_id"), "to_meeting_id": rows[b].get("meeting_id"),
        "to_source_url": rows[b].get("source_url"),
        "weight": float(graph.weights[a, b]),
        "metric_distance": float(graph.distances[a, b]),
        "graph_policy_sha256": digest(asdict(graph.policy)),
    } for a, b in zip(i, j)]


def fit_or_record(method: str, graph, policy) -> dict:
    try:
        return spectral_clustering(graph, policy) if method == "spectral" else diffusion_map(graph, policy)
    except (GraphError, np.linalg.LinAlgError) as exc:
        result = {"method": method, "status": "failed", "reason": str(exc),
                  "parameters": {**asdict(graph.policy), **asdict(policy)},
                  "diagnostics": {"graph": graph.summary()}}
        if isinstance(exc, GraphError):
            result["failure_diagnostics"] = exc.diagnostics
        return result


def make_plots(output: Path, x: np.ndarray, truth: np.ndarray | None, graph,
               spectral: dict, diffusion: dict, baseline: dict | None,
               sensitivity: dict) -> list[str]:
    """Source-free charts; layout coordinates have no political meaning."""
    paths = []
    fig, ax = plt.subplots(figsize=(6.5, 5.1))
    ax.imshow(graph.weights, cmap="viridis", interpolation="none", aspect="auto")
    ax.set(title="Synthetic weighted kNN affinity", xlabel="Observation row", ylabel="Observation row")
    fig.tight_layout()
    fig.savefig(output / "affinity.svg")
    paths.append("affinity.svg")
    plt.close(fig)

    if diffusion["status"] == "fitted":
        z = diffusion["coordinates"]
        fig, ax = plt.subplots(figsize=(6.5, 5.1))
        ax.scatter(z[:, 0], z[:, 1] if z.shape[1] > 1 else np.zeros(len(z)),
                   c=truth if truth is not None else np.arange(len(z)),
                   cmap="viridis", alpha=0.8, s=19)
        ax.set(title="Synthetic geometric diffusion map",
               xlabel="First diffusion coordinate",
               ylabel="Second diffusion coordinate")
        fig.tight_layout()
        fig.savefig(output / "diffusion.svg")
        paths.append("diffusion.svg")
        plt.close(fig)

    if baseline is not None:
        fig, ax = plt.subplots(figsize=(6.5, 3.7))
        names = ["k-means", "PAM"]
        scores = [baseline["kmeans"]["ari_to_spectral"], baseline["pam"]["ari_to_spectral"]]
        ax.bar(names, scores, color=["#597EA5", "#B98C58"])
        ax.axhline(0, color="gray", linewidth=0.8)
        ax.set(ylim=(-1, 1), ylabel="ARI against spectral partition",
               title="Source-matched algorithm agreement (synthetic)")
        fig.tight_layout()
        fig.savefig(output / "baselines.svg")
        paths.append("baselines.svg")
        plt.close(fig)

    attempts = sensitivity.get("attempts", [])
    if attempts:
        fig, ax = plt.subplots(figsize=(7.0, 3.7))
        vals = [
            a.get("ari", np.nan) if "ari" in a else a.get("procrustes_disparity", np.nan)
            for a in attempts
        ]
        ax.bar(range(len(attempts)), vals, color="#597EA5")
        ax.set(xticks=range(len(attempts)),
               xticklabels=[
                   f"k={a['graph']['n_neighbors']}\nσ={a['graph']['bandwidth']:g}"
                   for a in attempts],
               title="Graph-policy sensitivity; failed fits retained as gaps",
               ylabel="ARI or Procrustes disparity")
        fig.tight_layout()
        fig.savefig(output / "sensitivity.svg")
        paths.append("sensitivity.svg")
        plt.close(fig)
    return paths


def run(manifest: dict, x: np.ndarray, output: Path, seed: int = 81,
        synthetic_labels: np.ndarray | None = None,
        peer: tuple[dict, np.ndarray] | None = None) -> dict:
    validate_input(manifest, x)
    if output.exists() and any(output.iterdir()):
        raise GraphError("Output directory must be empty; do not overwrite evidence")
    output.mkdir(parents=True, exist_ok=True)
    n = len(x)
    graph_policy = GraphPolicy(n_neighbors=min(16, n - 1),
                               metric=manifest["representation"]["distance_geometry"],
                               kernel="gaussian", bandwidth=1.4)
    spectral_policy = SpectralPolicy(n_clusters=3, seed=seed)
    diffusion_policy = DiffusionPolicy(alpha=0.5, time=2, dimensions=2)
    graph = build_affinity(x, graph_policy)
    spectral = fit_or_record("spectral", graph, spectral_policy)
    diffusion = fit_or_record("diffusion_map", graph, diffusion_policy)
    baseline = None
    grouped = {}
    sensitivity = {}
    for method, fit, policy in (
        ("spectral", spectral, spectral_policy),
        ("diffusion", diffusion, diffusion_policy),
    ):
        if fit["status"] == "fitted":
            grouped[method] = grouped_leave_one_out(
                x, manifest["observations"], graph_policy, policy, fit)
            sensitivity[method] = parameter_sensitivity(
                x, fit, graph_policy, policy, variations(graph_policy, n))
        else:
            grouped[method] = {"status": "withheld", "reason": fit["reason"]}
            sensitivity[method] = {"status": "withheld", "reason": fit["reason"]}
    if spectral["status"] == "fitted":
        baseline = baseline_comparison(x, graph, spectral, seed)
    geometry = {}
    for name, fit in (("spectral", spectral), ("diffusion", diffusion)):
        if fit["status"] == "fitted":
            geometry[name] = fidelity(x, fit["coordinates"], graph_policy.metric)
        else:
            geometry[name] = {"status": "withheld", "reason": fit["reason"]}
    paired = None
    if peer:
        paired = paired_representations(
            manifest, x, peer[0], peer[1], graph_policy, spectral_policy, diffusion_policy)
    # Metadata adapter has no raw source strings; row-level output remains local.
    envelope = to_interchange_v1(
        manifest, x, {"w3-spectral-v1": spectral, "w3-diffusion-v1": diffusion},
        generated_at="2026-10-08T00:00:00Z" if manifest["split"] == "synthetic" else None,
    )
    write_json(output / "interchange-v1.json", envelope)
    write_json(output / "source-linked-edges.json", source_edges(manifest, graph))
    write_json(output / "fit-geometry.json", {
        name: {
            "status": fit["status"], "source_ordered_ids": [r["id"] for r in manifest["observations"]],
            "coordinates": fit.get("coordinates"), "eigenvalues": fit.get("eigenvalues"),
            "labels": fit.get("labels"), "reason": fit.get("reason"),
            "diagnostics": fit.get("diagnostics"), "parameters": fit.get("parameters"),
            "out_of_sample": fit.get("out_of_sample"),
        } for name, fit in (("spectral", spectral), ("diffusion", diffusion))
    })
    write_json(output / "source-group-sensitivity.json", grouped)
    write_json(output / "graph-policy-sensitivity.json", sensitivity)
    if paired is not None:
        write_json(output / "paired-representations.json", paired)
    plot_paths = make_plots(output, x, synthetic_labels, graph, spectral, diffusion,
                            baseline, sensitivity.get("spectral", {}))
    receipt = {
        "schema": "un.graph-methods-receipt.v1", "seed": seed,
        "split": manifest["split"], "fixture_or_source_sha256": manifest["upstream"]["source_sha256"],
        "source_hash_basis": manifest["upstream"]["source_hash_basis"],
        "observation_join_sha256": manifest["observation_join_sha256"],
        "representation": manifest["representation"],
        "graph": graph.summary(),
        "spectral": {key: value for key, value in spectral.items() if key not in {"labels", "coordinates"}},
        "diffusion": {key: value for key, value in diffusion.items() if key != "coordinates"},
        "fidelity": geometry, "baselines": baseline,
        "group_sensitivity": {
            key: {k: v for k, v in obj.items() if k != "attempts"} for key, obj in grouped.items()
        },
        "parameter_sensitivity": {
            key: {k: v for k, v in obj.items() if k != "attempts"} for key, obj in sensitivity.items()
        },
        "attempts": {"planned_primary": 2,
                     "successful_primary": sum(
                         f["status"] == "fitted" for f in (spectral, diffusion)),
                     "failed_primary": sum(
                         f["status"] != "fitted" for f in (spectral, diffusion))},
        "synthetic_known_label_ari": (
            float(__import__("sklearn.metrics", fromlist=["adjusted_rand_score"])
                  .adjusted_rand_score(synthetic_labels, spectral["labels"]))
            if synthetic_labels is not None and spectral["status"] == "fitted" else None
        ),
        "code_sha256": code_digest(),
        "runtime": platform.python_version(),
        "dependencies": {
            p: importlib.metadata.version(p)
            for p in ("numpy", "scipy", "scikit-learn", "matplotlib", "jsonschema")
        },
        "plot_files": plot_paths, "heldout_transcripts_opened": 0,
        "publication_eligible": False,
        "limit": ("Statistical geometry only; no political influence/policy transmission. "
                  "Source-group refits are not independent evaluations."),
    }
    write_json(output / "receipt.json", receipt)
    # The manifest contains only computed outputs, not self-referential SHA data.
    write_json(output / "SHA256.json", {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(output.iterdir()) if p.is_file()
    })
    return receipt


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--fixture", choices=["blobs"])
    group.add_argument("--input-manifest", type=Path)
    ap.add_argument("--vectors", type=Path)
    ap.add_argument("--compare-manifest", type=Path)
    ap.add_argument("--compare-vectors", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=81)
    args = ap.parse_args()
    if args.fixture:
        if args.vectors:
            ap.error("--fixture cannot accept supplied vectors")
        manifest, x, known = fixture(args.seed)
    else:
        if args.vectors is None:
            ap.error("--vectors required for local manifest")
        manifest, x = local_source(args.input_manifest, args.vectors)
        known = None
    peer = None
    if args.compare_manifest or args.compare_vectors:
        if not args.compare_manifest or not args.compare_vectors or args.fixture:
            ap.error("Comparison requires two local authorized development representations")
        peer = local_source(args.compare_manifest, args.compare_vectors)
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        receipt = run(manifest, x, args.output, args.seed, known, peer)
    print(json.dumps({
        "receipt": str(args.output / "receipt.json"),
        "source_population": len(x),
        "graph": receipt["graph"],
        "attempts": receipt["attempts"],
        "synthetic_known_label_ari": receipt["synthetic_known_label_ari"],
    }, indent=2))
    if receipt["attempts"]["failed_primary"]:
        raise SystemExit("One or more primary graph methods refused fitting; inspect failure receipt")


if __name__ == "__main__":
    main()
