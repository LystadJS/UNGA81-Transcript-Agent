"""Auditable source-bound graph construction. No transcript, network or browser IO."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import hashlib
import json
from typing import Any

import numpy as np
from scipy.sparse.csgraph import connected_components
from sklearn.metrics import pairwise_distances

MAX_OBSERVATIONS = 600
SHA_LENGTH = 64
RESERVED_DATES = {"2026-10-05", "2026-10-06"}
SOURCE_SCHEMAS = {
    "synthetic.v1", "un.browser.corpus.v1", "un.latent-comparison.v1",
    "un.passage-corpus.v1", "un.review.v1",
}


class GraphError(ValueError):
    """Explicit refusal with optional numerical diagnostics."""

    def __init__(self, message: str, diagnostics: dict[str, Any] | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def matrix_digest(values: np.ndarray) -> str:
    x = np.ascontiguousarray(values, dtype="<f8")
    return hashlib.sha256(
        json.dumps(list(x.shape), separators=(",", ":")).encode("ascii") + x.tobytes()
    ).hexdigest()


def is_sha(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == SHA_LENGTH
        and all(char in "0123456789abcdef" for char in value)
    )


def validate_input(manifest: dict, values: np.ndarray) -> dict:
    """Verify exact row, representation and matrix identity; never infer speech ownership.

    Source digests are *declared upstream hashes*, not recomputed from unavailable
    original transcripts. This validator verifies the declared matrix and ID/hash join.
    """
    if manifest.get("schema") != "un.graph-input.v1":
        raise GraphError("Unsupported graph-input schema")
    if manifest.get("split") not in {"synthetic", "development"}:
        raise GraphError("Only synthetic or authorized development inputs are allowed")
    upstream = manifest.get("upstream")
    if not isinstance(upstream, dict) or upstream.get("source_schema") not in SOURCE_SCHEMAS:
        raise GraphError("Explicit original upstream schema required")
    if not is_sha(upstream.get("source_sha256")) or not is_sha(upstream.get("selection_sha256")):
        raise GraphError("Missing upstream source or selection digest")
    if upstream.get("source_hash_basis") not in {
        "synthetic", "utf8_corpus_export", "raw_response_bytes",
        "utf8_response_text", "canonical_source_text", "source_text_file_bytes",
    }:
        raise GraphError("Unknown upstream hash basis")
    if manifest["split"] == "synthetic" and upstream["source_schema"] != "synthetic.v1":
        raise GraphError("Synthetic data must use a synthetic source identity")
    if manifest["split"] == "development" and upstream["source_schema"] == "synthetic.v1":
        raise GraphError("Development data cannot use a synthetic source identity")
    rep = manifest.get("representation")
    if not isinstance(rep, dict) or not all(
        isinstance(rep.get(key), str) and rep[key]
        for key in ("id", "version", "feature_basis", "training_selection_sha256")
    ):
        raise GraphError("Pinned representation ID, version, basis and training selection required")
    if not all(is_sha(rep.get(key)) for key in ("matrix_sha256", "training_selection_sha256")):
        raise GraphError("Missing representation/matrix integrity hashes")
    if rep.get("distance_geometry") not in {"euclidean", "cosine"}:
        raise GraphError("Representation must name an explicit distance geometry")
    if rep["feature_basis"] not in {"tfidf_pca", "tfidf_lsa", "minilm_pinned", "synthetic"}:
        raise GraphError("Unrecognized feature basis; no implicit basis alignment")
    if rep["feature_basis"] == "minilm_pinned" and not is_sha(rep.get("model_revision_sha256")):
        raise GraphError("MiniLM comparisons require a pinned model checkpoint fingerprint")
    if manifest["split"] == "synthetic" and rep["feature_basis"] != "synthetic":
        raise GraphError("Synthetic fixture must identify synthetic geometry")
    rows = manifest.get("observations")
    if not isinstance(rows, list) or not rows or len(rows) > MAX_OBSERVATIONS:
        raise GraphError("Observation population empty or exceeds bounded research limit")
    extras = manifest.get("excluded_observations", [])
    if not isinstance(extras, list):
        raise GraphError("Excluded observation frame must be an explicit metadata list")
    if manifest.get("total_in_frame") != len(rows) + len(extras):
        raise GraphError("Frame denominator differs from included plus explicitly excluded rows")
    ids: set[str] = set()
    for row in rows + extras:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"]:
            raise GraphError("Every observation needs an explicit unique ID")
        if row["id"] in ids:
            raise GraphError("Duplicate observation ID")
        ids.add(row["id"])
        if not is_sha(row.get("text_sha256")):
            raise GraphError("Missing source-linked observation text hash")
        if row in extras and not row.get("exclusion_reasons"):
            raise GraphError("Excluded observations require explicit exclusion reasons")
        stamp = row.get("date")
        if not isinstance(stamp, str) or len(stamp) != 10:
            raise GraphError("Missing complete observation date; do not impute one")
        try:
            if date.fromisoformat(stamp).isoformat() != stamp:
                raise ValueError("Noncanonical date")
        except ValueError as exc:
            raise GraphError("Invalid canonical ISO observation date") from exc
        if stamp in RESERVED_DATES or row.get("split", manifest["split"]) != manifest["split"]:
            raise GraphError("Reserved 5–6 October observations and cross-split rows prohibited")
        if any(field in row for field in ("text", "transcript", "quote")):
            raise GraphError("Graph manifests must contain metadata only, never source text")
        if row.get("source_url") is not None and not (
            isinstance(row["source_url"], str) and row["source_url"].startswith("https://")
        ):
            raise GraphError("Invalid original HTTPS source link")
        start, end = row.get("start"), row.get("end")
        if (start is None) != (end is None) or (
            start is not None and (not isinstance(start, int) or not isinstance(end, int) or
                                   start < 0 or end <= start)
        ):
            raise GraphError("Invalid source offsets (zero-based, end-exclusive code points)")
    joins = [[r["id"], r["text_sha256"]] for r in rows]
    if digest(joins) != manifest.get("observation_join_sha256"):
        raise GraphError("Observation ID/text-hash/order join differs from pinned manifest")
    if extras:
        frame_join = [[r["id"], r["text_sha256"]] for r in rows + extras]
        if digest(frame_join) != manifest.get("frame_join_sha256"):
            raise GraphError("Full frame/exclusion identity differs from pinned frame digest")
    x = np.asarray(values)
    if x.ndim != 2 or x.shape[0] != len(rows) or x.shape[1] < 1 or x.size > 2_000_000:
        raise GraphError("Matrix shape/row count or cell budget invalid")
    if not np.issubdtype(x.dtype, np.number) or not np.isfinite(x).all():
        raise GraphError("Features must be finite numeric values")
    x = np.asarray(x, dtype=np.float64)
    if matrix_digest(x) != rep["matrix_sha256"]:
        raise GraphError("Feature matrix digest differs from pinned representation")
    return {"n": len(rows), "p": x.shape[1], "join_sha256": digest(joins),
            "matrix_sha256": matrix_digest(x), "representation_id": rep["id"]}


@dataclass(frozen=True)
class GraphPolicy:
    n_neighbors: int = 8
    metric: str = "euclidean"  # or cosine; cosine requires nonzero input norms
    symmetrize: str = "union"  # union or mutual
    kernel: str = "gaussian"  # gaussian or local_gaussian
    bandwidth: float = 1.0  # Euclidean / cosine units; only gaussian
    local_scale_floor: float = 1e-8  # declared regularizer for tied distances

    def validate(self, n: int) -> None:
        if n < 4 or n > MAX_OBSERVATIONS:
            raise GraphError("At least four and no more than 600 observations required")
        if not isinstance(self.n_neighbors, int) or not 1 <= self.n_neighbors < n:
            raise GraphError("Invalid k-nearest-neighbor count")
        if self.metric not in {"euclidean", "cosine"}:
            raise GraphError("Unsupported distance metric")
        if self.symmetrize not in {"union", "mutual"}:
            raise GraphError("Unsupported graph symmetrization")
        if self.kernel not in {"gaussian", "local_gaussian"}:
            raise GraphError("Unsupported distance kernel")
        if not np.isfinite(self.bandwidth) or self.bandwidth <= 0:
            raise GraphError("Kernel bandwidth must be positive and finite")
        if not np.isfinite(self.local_scale_floor) or self.local_scale_floor <= 0:
            raise GraphError("Local kernel floor must be positive and finite")


@dataclass
class Affinity:
    weights: np.ndarray
    distances: np.ndarray
    neighbors: np.ndarray
    components: np.ndarray
    policy: GraphPolicy
    diagnostics: dict

    def summary(self) -> dict:
        return {**asdict(self.policy), **self.diagnostics}


def build_affinity(values: np.ndarray, policy: GraphPolicy) -> Affinity:
    x = np.asarray(values, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] < 1 or not np.isfinite(x).all():
        raise GraphError("Graph needs a finite 2D feature matrix")
    n = len(x)
    policy.validate(n)
    if policy.metric == "cosine" and np.any(np.linalg.norm(x, axis=1) <= 1e-14):
        raise GraphError("Cosine geometry requires all nonzero feature vectors")
    d = pairwise_distances(x, metric=policy.metric)
    d = np.maximum(0.0, (d + d.T) / 2.0)
    np.fill_diagonal(d, 0)
    order = np.argsort(np.where(np.eye(n, dtype=bool), np.inf, d), axis=1, kind="stable")
    neighbors = order[:, :policy.n_neighbors]
    chosen = np.zeros((n, n), dtype=bool)
    chosen[np.arange(n)[:, None], neighbors] = True
    edges = chosen | chosen.T if policy.symmetrize == "union" else chosen & chosen.T
    scales = d[np.arange(n), neighbors[:, -1]]
    if policy.kernel == "gaussian":
        w = np.exp(-0.5 * (d / policy.bandwidth) ** 2)
    else:
        safe = np.maximum(scales, policy.local_scale_floor)
        w = np.exp(-(d ** 2) / np.outer(safe, safe))
    w[~edges] = 0.0
    np.fill_diagonal(w, 0.0)
    w = (w + w.T) / 2.0
    degree = np.sum(w, axis=1)
    binary_degree = np.count_nonzero(w > 0, axis=1)
    component_count, component_labels = connected_components(w, directed=False)
    group_sizes = np.bincount(component_labels).tolist()
    mean_degree = float(np.mean(degree))
    sorted_degree = np.sort(degree)
    degree_gini = (
        float(np.sum((2 * np.arange(1, n + 1) - n - 1) * sorted_degree) /
              (n * np.sum(sorted_degree))) if np.sum(sorted_degree) > 0 else None
    )
    diagnostics = {
        "n_nodes": n,
        "edge_count": int(np.count_nonzero(np.triu(w, k=1))),
        "connected_components": int(component_count),
        "component_sizes": group_sizes,
        "isolated_count": int(np.count_nonzero(degree == 0)),
        "zero_distance_pairs": int(np.count_nonzero(np.triu(d <= 1e-12, k=1))),
        "zero_knn_radius_count": int(np.count_nonzero(scales <= 1e-12)),
        "minimum_weighted_degree": float(np.min(degree)),
        "maximum_weighted_degree": float(np.max(degree)),
        "degree_concentration_ratio": (
            float(np.max(degree) / mean_degree) if mean_degree > 0 else None
        ),
        "degree_gini": degree_gini,
        "max_binary_degree": int(binary_degree.max()),
        "min_binary_degree": int(binary_degree.min()),
        "knn_tie_policy": "distance then input row ID order",
        "diagonal_self_loops": False,
        "eigensolver": "scipy.linalg.eigh dense symmetric",
    }
    return Affinity(w, d, neighbors, component_labels, policy, diagnostics)


def require_connected(graph: Affinity, allow_components: bool = False) -> None:
    if graph.diagnostics["isolated_count"]:
        raise GraphError("Isolated graph node; no silent deletion", graph.summary())
    if not allow_components and graph.diagnostics["connected_components"] != 1:
        raise GraphError("Disconnected graph; require an explicit component policy", graph.summary())


def equal_population(left: dict, right: dict) -> None:
    """Refuse any source-bound comparison with mismatched provenance or row identities."""
    for key in ("split", "observation_join_sha256"):
        if left.get(key) != right.get(key):
            raise GraphError("Incompatible selection or ordered source-linked observation IDs")
    if left.get("upstream") != right.get("upstream"):
        raise GraphError("Incompatible source/selection hash, source schema or hash basis")
    for a, b in zip(left["observations"], right["observations"]):
        if (a["id"], a["text_sha256"], a.get("parent_id"), a.get("meeting_id")) != (
            b["id"], b["text_sha256"], b.get("parent_id"), b.get("meeting_id")
        ):
            raise GraphError("Incompatible parent/meeting provenance")
    a, b = left["representation"], right["representation"]
    if a.get("distance_geometry") != b.get("distance_geometry") or a.get("distance_geometry") not in {
        "euclidean", "cosine"
    }:
        raise GraphError("Geometries differ; no implicit cross-representation alignment")
