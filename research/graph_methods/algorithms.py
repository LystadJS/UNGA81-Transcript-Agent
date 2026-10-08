"""Spectral partitions, geometric diffusion, source-group sensitivity and baselines."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
import warnings

import numpy as np
from scipy.linalg import eigh, orthogonal_procrustes
from scipy.stats import spearmanr
from sklearn.cluster import KMeans
from sklearn.manifold import trustworthiness
from sklearn.metrics import adjusted_mutual_info_score, adjusted_rand_score

from .core import Affinity, GraphError, GraphPolicy, build_affinity, require_connected


@dataclass(frozen=True)
class SpectralPolicy:
    n_clusters: int = 3
    laplacian: str = "symmetric"  # symmetric, random_walk, unnormalized
    allow_disconnected: bool = False
    eigengap_tolerance: float = 1e-7
    residual_tolerance: float = 1e-7
    seed: int = 81

    def validate(self, n: int) -> None:
        if not isinstance(self.n_clusters, int) or not 2 <= self.n_clusters < n:
            raise GraphError("Require 2 <= clusters < observations; never clamp k")
        if self.laplacian not in {"symmetric", "random_walk", "unnormalized"}:
            raise GraphError("Unsupported Laplacian normalization")
        if not (0 < self.eigengap_tolerance < 0.1 and
                0 < self.residual_tolerance < 0.1):
            raise GraphError("Invalid positive numerical error tolerances")
        if not isinstance(self.seed, int) or not 0 <= self.seed < 2**32:
            raise GraphError("Invalid random seed")


@dataclass(frozen=True)
class DiffusionPolicy:
    alpha: float = 0.5  # anisotropic density normalization: q^-alpha K q^-alpha
    time: int = 1
    dimensions: int = 2
    eigengap_tolerance: float = 1e-7
    residual_tolerance: float = 1e-7

    def validate(self, n: int) -> None:
        if not np.isfinite(self.alpha) or not 0 <= self.alpha <= 1:
            raise GraphError("Diffusion alpha must lie in [0,1]")
        if not isinstance(self.time, int) or self.time < 1 or self.time > 1000:
            raise GraphError("Diffusion time must be an integer in [1,1000]")
        if not isinstance(self.dimensions, int) or not 1 <= self.dimensions < n - 1:
            raise GraphError("Retained diffusion dimensions must be smaller than n-1")
        if not (0 < self.eigengap_tolerance < 0.1 and
                0 < self.residual_tolerance < 0.1):
            raise GraphError("Invalid positive numerical error tolerances")


def eigencheck(operator: np.ndarray, eigenvalues: np.ndarray,
               vectors: np.ndarray, tolerance: float) -> dict:
    normalized = max(1.0, float(np.linalg.norm(operator, ord=2)))
    residual = float(np.linalg.norm(operator @ vectors - vectors * eigenvalues, ord="fro") /
                     (normalized * max(1.0, float(np.linalg.norm(vectors, ord="fro")))))
    orthogonality = float(np.linalg.norm(
        vectors.T @ vectors - np.eye(vectors.shape[1]), ord="fro"
    ))
    if residual > tolerance or orthogonality > tolerance * 10:
        raise GraphError("Dense symmetric eigensolver failed residual/orthogonality check",
                         {"relative_residual": residual, "orthogonality": orthogonality})
    return {"relative_residual": residual, "orthogonality": orthogonality,
            "eigensolver_converged": True}


def boundary_check(values: np.ndarray, stop: int, tolerance: float,
                   ascending: bool) -> dict:
    if not 0 < stop < len(values):
        raise GraphError("Insufficient eigenvalues for requested retained dimensions")
    gap = float(values[stop] - values[stop - 1]) if ascending else float(values[stop - 1] - values[stop])
    scaled = tolerance * max(1.0, float(np.max(np.abs(values))))
    if gap <= scaled:
        raise GraphError("Degenerate eigenspace at retained dimensional boundary",
                         {"boundary_eigengap": gap, "tolerance": scaled})
    internal_gaps = abs(np.diff(values[:stop]))
    return {"boundary_eigengap": gap, "eigenvalue_gap_threshold": scaled,
            "internal_eigenspace_degeneracy": bool(np.any(internal_gaps <= scaled))}


def seeded_kmeans(embedding: np.ndarray, k: int, seed: int) -> tuple[np.ndarray, dict]:
    if np.unique(embedding, axis=0).shape[0] < k:
        raise GraphError("Fewer unique embedded observations than clusters")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        estimator = KMeans(
            n_clusters=k, n_init=20, max_iter=300, random_state=seed, algorithm="lloyd"
        )
        labels = estimator.fit_predict(embedding).astype(int) + 1
    warnings_seen = [str(item.message) for item in caught]
    if len(set(labels)) != k:
        raise GraphError("Numerically collapsed k-means partition",
                         {"warnings": warnings_seen})
    if estimator.n_iter_ >= estimator.max_iter or warnings_seen:
        raise GraphError("K-means convergence not certified",
                         {"iterations": int(estimator.n_iter_), "warnings": warnings_seen})
    return labels, {"iterations": int(estimator.n_iter_), "inertia": float(estimator.inertia_),
                    "starts": 20, "seed": seed, "warnings": warnings_seen}


def spectral_clustering(graph: Affinity, policy: SpectralPolicy) -> dict:
    w = graph.weights
    n = len(w)
    policy.validate(n)
    require_connected(graph, policy.allow_disconnected)
    components = graph.diagnostics["connected_components"]
    if components > policy.n_clusters:
        raise GraphError("More graph components than requested clusters", graph.summary())
    degree = w.sum(axis=1)
    laplacian = np.diag(degree) - w
    if policy.laplacian in {"symmetric", "random_walk"}:
        invsqrt = np.diag(1 / np.sqrt(degree))
        operator = invsqrt @ laplacian @ invsqrt
    else:
        operator = laplacian
    evals, evecs = eigh(operator, check_finite=True)
    checks = eigencheck(operator, evals, evecs, policy.residual_tolerance)
    checks.update(boundary_check(evals, policy.n_clusters, policy.eigengap_tolerance, True))
    embedded = evecs[:, :policy.n_clusters].copy()
    if policy.laplacian == "symmetric":
        row_norm = np.linalg.norm(embedded, axis=1)
        if (row_norm < 1e-12).any():
            raise GraphError("Undefined Ng–Jordan–Weiss spectral row scaling", graph.summary())
        embedded /= row_norm[:, None]
    elif policy.laplacian == "random_walk":
        embedded /= np.sqrt(degree[:, None])
    labels, km = seeded_kmeans(embedded, policy.n_clusters, policy.seed)
    return {"method": "spectral", "status": "fitted", "labels": labels,
            "coordinates": embedded, "eigenvalues": evals.tolist(),
            "diagnostics": {**checks, "laplacian": policy.laplacian,
                            "zero_eigenvalues": int(np.count_nonzero(abs(evals) < 1e-8)),
                            "graph": graph.summary(), "kmeans": km},
            "parameters": {**asdict(graph.policy), **asdict(policy)},
            "publication_eligible": False}


def diffusion_map(graph: Affinity, policy: DiffusionPolicy) -> dict:
    w = graph.weights
    n = len(w)
    policy.validate(n)
    require_connected(graph)
    q = w.sum(axis=1)
    density = np.power(q, -policy.alpha)
    kernel = density[:, None] * w * density[None, :]
    degree = kernel.sum(axis=1)
    if (degree <= 0).any():
        raise GraphError("Anisotropic normalization created zero-degree graph")
    root = np.sqrt(degree)
    operator = kernel / np.outer(root, root)
    evals, u = eigh(operator, check_finite=True)
    evals, u = evals[::-1], u[:, ::-1]
    checks = eigencheck(operator, evals, u, policy.residual_tolerance)
    if abs(evals[0] - 1.0) > policy.residual_tolerance * 10:
        raise GraphError("Transition operator has no validated stationary eigenvalue")
    checks.update(boundary_check(evals, policy.dimensions + 1,
                                 policy.eigengap_tolerance, False))
    selected = evals[1:policy.dimensions + 1]
    if np.any(selected <= 1e-10):
        raise GraphError("Nonpositive retained diffusion eigenvalue: times not comparable")
    vectors = u[:, 1:policy.dimensions + 1] / root[:, None]
    # Normalize right eigenfunctions by their transition-stationary pi inner product.
    pi = degree / degree.sum()
    norms = np.sqrt((pi[:, None] * vectors**2).sum(axis=0))
    vectors /= norms[None, :]
    # Sign convention is for deterministic export only; near-degenerate internal
    # eigenspaces remain rotation-indeterminate and must be compared geometrically.
    for j in range(vectors.shape[1]):
        idx = int(np.argmax(abs(vectors[:, j])))
        if vectors[idx, j] < 0:
            vectors[:, j] *= -1
    coords = vectors * selected[None, :] ** policy.time
    return {"method": "diffusion_map", "status": "fitted",
            "coordinates": coords, "eigenvalues": evals.tolist(),
            "diagnostics": {**checks, "alpha": policy.alpha,
                            "diffusion_time": policy.time,
                            "stationary_eigenvalue": float(evals[0]),
                            "minimum_retained_eigenvalue": float(selected[-1]),
                            "negative_eigenvalues": int(np.count_nonzero(evals < -1e-9)),
                            "graph": graph.summary()},
            "parameters": {**asdict(graph.policy), **asdict(policy)},
            "publication_eligible": False,
            "out_of_sample": "Unavailable: rerun with a new declared source population; coordinates are transductive."}


def _ranked_neighbors(values: np.ndarray, k: int) -> np.ndarray:
    from sklearn.metrics import pairwise_distances
    d = pairwise_distances(values, metric="euclidean")
    np.fill_diagonal(d, np.inf)
    return np.argsort(d, axis=1, kind="stable")[:, :k]


def fidelity(original: np.ndarray, reduced: np.ndarray, metric: str = "euclidean") -> dict:
    """Two distinct local fidelity directions, not claims of topical correctness."""
    x = np.asarray(original, dtype=float)
    z = np.asarray(reduced, dtype=float)
    n = len(x)
    if len(z) != n or z.ndim != 2 or not np.isfinite(z).all():
        raise GraphError("Invalid source-aligned coordinates for fidelity")
    if metric == "cosine":
        norm = np.linalg.norm(x, axis=1)
        if (norm < 1e-12).any():
            raise GraphError("Cosine fidelity requires nonzero original vectors")
        x = x / norm[:, None]
    elif metric != "euclidean":
        raise GraphError("Unknown fidelity geometry")
    q = min(8, (n - 2) // 2)
    if q < 1:
        return {"status": "withheld", "reason": "Insufficient samples for neighborhood fidelity"}
    old = _ranked_neighbors(x, q)
    new = _ranked_neighbors(z, q)
    overlap = float(np.mean([len(set(a) & set(b)) / q for a, b in zip(old, new)]))
    return {"status": "descriptive", "neighbor_count": q, "neighbor_overlap": overlap,
            "trustworthiness": float(trustworthiness(x, z, n_neighbors=q)),
            "continuity": float(trustworthiness(z, x, n_neighbors=q)),
            "distance_geometry": metric}


def pam_partition(distances: np.ndarray, k: int, seed: int = 81,
                  max_swaps: int = 100) -> dict:
    """Deterministic swap-optimal k-medoids (PAM-style), not sklearn-extra."""
    d = np.asarray(distances, dtype=float)
    n = len(d)
    if d.shape != (n, n) or not np.isfinite(d).all() or np.any(d < 0) or \
            not np.allclose(d, d.T) or not np.allclose(np.diag(d), 0):
        raise GraphError("PAM requires symmetric nonnegative zero-diagonal distances")
    if not 2 <= k < n or not isinstance(seed, int):
        raise GraphError("Invalid PAM cluster count or seed")
    first = int(np.random.default_rng(seed).integers(n))
    medoids = [first]
    for _ in range(k - 1):
        choices = np.min(d[:, medoids], axis=1)
        choices[medoids] = -1
        medoids.append(int(np.argmax(choices)))
    history = []
    converged = False
    for iteration in range(max_swaps + 1):
        current = d[:, medoids]
        closest = np.argmin(current, axis=1)
        best = current[np.arange(n), closest]
        second = np.partition(current, 1, axis=1)[:, 1]
        old_cost = float(best.sum())
        history.append(old_cost)
        improvement = 1e-10
        swap = None
        for slot in range(k):
            remaining = np.where(closest == slot, second, best)
            for candidate in range(n):
                if candidate in medoids:
                    continue
                new_cost = float(np.minimum(remaining, d[:, candidate]).sum())
                if old_cost - new_cost > improvement:
                    improvement = old_cost - new_cost
                    swap = (slot, candidate)
        if swap is None:
            converged = True
            break
        medoids[swap[0]] = swap[1]
    if not converged:
        raise GraphError("PAM reached the swap limit without certification",
                         {"iterations": max_swaps, "cost_history": history})
    # Every medoid must own itself even under exact duplicate distance ties.
    assignments = np.argmin(d[:, medoids], axis=1)
    for i, m in enumerate(medoids):
        assignments[m] = i
    if len(np.unique(assignments)) != k:
        raise GraphError("PAM assignment collapsed due to duplicate-distance ties")
    return {"labels": assignments.astype(int) + 1, "medoids": medoids,
            "objective": float(d[np.arange(n), np.array(medoids)[assignments]].sum()),
            "iterations": len(history) - 1, "converged": converged,
            "cost_history": history}


def baseline_comparison(values: np.ndarray, graph: Affinity, spectral: dict,
                        seed: int) -> dict:
    """Only matched rows/metric: k-means and PAM comparisons are descriptive."""
    if spectral["method"] != "spectral":
        raise GraphError("Baseline comparison requires a spectral partition")
    k = len(np.unique(spectral["labels"]))
    x = np.asarray(values, dtype=float)
    if graph.policy.metric == "cosine":
        x = x / np.linalg.norm(x, axis=1)[:, None]
    km, kmeta = seeded_kmeans(x, k, seed)
    pam = pam_partition(graph.distances, k, seed)
    return {
        "population_n": len(x), "distance_metric": graph.policy.metric,
        "k": k, "same_source_rows_and_graph_geometry": True,
        "kmeans": {"ari_to_spectral": float(adjusted_rand_score(spectral["labels"], km)),
                   "ami_to_spectral": float(adjusted_mutual_info_score(spectral["labels"], km)),
                   "coverage": len(x), **kmeta},
        "pam": {"ari_to_spectral": float(adjusted_rand_score(
            spectral["labels"], pam["labels"])),
                "ami_to_spectral": float(adjusted_mutual_info_score(
                    spectral["labels"], pam["labels"])),
                "coverage": len(x), "objective": pam["objective"],
                "iterations": pam["iterations"]},
        "limitation": "In-sample algorithm agreement; not independent evidence of structure or influence.",
    }


def procrustes_disparity(reference: np.ndarray, fitted: np.ndarray) -> float:
    """Rotation/sign-invariant comparison on identical observations/dimensions."""
    a = np.asarray(reference, dtype=float)
    b = np.asarray(fitted, dtype=float)
    if a.shape != b.shape or a.ndim != 2 or not np.isfinite(a).all() or \
            not np.isfinite(b).all():
        raise GraphError("Procrustes comparison requires matched finite coordinates")
    a = a - a.mean(axis=0)
    b = b - b.mean(axis=0)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if min(na, nb) < 1e-12:
        raise GraphError("Degenerate embedding for Procrustes comparison")
    a, b = a / na, b / nb
    rotation, _ = orthogonal_procrustes(b, a)
    return float(np.linalg.norm(b @ rotation - a, ord="fro") ** 2)


def grouped_leave_one_out(values: np.ndarray, rows: list[dict], graph_policy: GraphPolicy,
                          model_policy: SpectralPolicy | DiffusionPolicy, reference: dict,
                          group_key: str = "meeting_id", max_groups: int = 30) -> dict:
    """Whole-group perturbation; failed fits remain in denominator."""
    if group_key not in {"meeting_id", "parent_id", "source_family_id", "country"}:
        raise GraphError("Unsupported group unit")
    groups = [row.get(group_key) for row in rows]
    if any(g is None or not str(g) for g in groups):
        return {"status": "withheld", "reason": "Group IDs absent; no row bootstrap fallback",
                "planned": 0, "successful": 0, "attempts": []}
    group_ids = sorted(set(groups))
    if len(group_ids) < 3 or len(group_ids) > max_groups:
        return {"status": "withheld", "reason": "Source group count outside declared range",
                "planned": 0, "successful": 0, "attempts": []}
    attempts = []
    for group in group_ids:
        keep = np.array([x != group for x in groups], dtype=bool)
        record: dict[str, Any] = {"omitted_group": group, "n_retained": int(keep.sum()),
                                  "status": "failed"}
        try:
            fitted_graph = build_affinity(values[keep], graph_policy)
            if isinstance(model_policy, SpectralPolicy):
                out = spectral_clustering(fitted_graph, model_policy)
                record["ari_on_shared_rows"] = float(adjusted_rand_score(
                    reference["labels"][keep], out["labels"]
                ))
            else:
                out = diffusion_map(fitted_graph, model_policy)
                record["procrustes_disparity"] = procrustes_disparity(
                    reference["coordinates"][keep], out["coordinates"]
                )
            record["status"] = "fitted"
        except (GraphError, ValueError, np.linalg.LinAlgError) as exc:
            record["reason"] = str(exc)
        attempts.append(record)
    success = [x for x in attempts if x["status"] == "fitted"]
    return {"status": "descriptive", "unit": group_key,
            "planned": len(attempts), "successful": len(success),
            "failed": len(attempts) - len(success),
            "success_fraction": len(success) / len(attempts),
            "attempts": attempts,
            "limitation": "Source-group omission is sensitivity, not held-out replication or confidence coverage."}


def parameter_sensitivity(values: np.ndarray, reference: dict,
                          graph_policy: GraphPolicy,
                          model_policy: SpectralPolicy | DiffusionPolicy,
                          variations: list[GraphPolicy]) -> dict:
    """Compare every requested graph policy; preserve refused fits and denominators."""
    attempts = []
    for policy in variations:
        r: dict[str, Any] = {"graph": asdict(policy), "status": "failed"}
        try:
            graph = build_affinity(values, policy)
            if isinstance(model_policy, SpectralPolicy):
                fitted = spectral_clustering(graph, model_policy)
                r["ari"] = float(adjusted_rand_score(reference["labels"], fitted["labels"]))
            else:
                fitted = diffusion_map(graph, model_policy)
                r["procrustes_disparity"] = procrustes_disparity(
                    reference["coordinates"], fitted["coordinates"])
                r["fidelity"] = fidelity(values, fitted["coordinates"], policy.metric)
            r["graph_quality"] = graph.summary()
            r["status"] = "fitted"
        except (GraphError, ValueError, np.linalg.LinAlgError) as exc:
            r["reason"] = str(exc)
            if isinstance(exc, GraphError):
                r["diagnostics"] = exc.diagnostics
        attempts.append(r)
    return {"status": "descriptive", "planned": len(attempts),
            "successful": sum(x["status"] == "fitted" for x in attempts),
            "attempts": attempts,
            "limitation": "Parameter sensitivity is not a null-hypothesis test."}


def diffusion_policy_sensitivity(
    values: np.ndarray, graph: Affinity, reference: dict,
    policies: list[DiffusionPolicy],
) -> dict:
    """Hold graph and observations fixed; report alpha/time/dimensional sensitivity.

    Procrustes is defined only at equal retained dimension. Different dimension
    counts are compared through their own source-space fidelity, not padded axes.
    """
    attempts = []
    for policy in policies:
        row: dict[str, Any] = {"policy": asdict(policy), "status": "failed"}
        try:
            fit = diffusion_map(graph, policy)
            row["eigenvalues_retained"] = fit["eigenvalues"][:policy.dimensions + 1]
            row["fidelity"] = fidelity(values, fit["coordinates"], graph.policy.metric)
            if reference["coordinates"].shape[1] == policy.dimensions:
                row["procrustes_disparity"] = procrustes_disparity(
                    reference["coordinates"], fit["coordinates"]
                )
            else:
                row["procrustes_disparity"] = None
                row["reason"] = "Different retained dimension; alignment withheld"
            row["status"] = "fitted"
        except (GraphError, ValueError, np.linalg.LinAlgError) as exc:
            row["reason"] = str(exc)
            if isinstance(exc, GraphError):
                row["diagnostics"] = exc.diagnostics
        attempts.append(row)
    return {
        "status": "descriptive", "planned": len(attempts),
        "successful": sum(r["status"] == "fitted" for r in attempts),
        "attempts": attempts,
        "limitation": "Alpha, time and retained-dimension changes are numerical sensitivity only.",
    }
