"""Metadata-only export to the coordinator's un.parallel-analysis.v1 contract."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import platform

import numpy as np
from sklearn.metrics import adjusted_rand_score

from .core import GraphError, digest, equal_population, validate_input
from .algorithms import fidelity, spectral_clustering, diffusion_map
from .core import build_affinity, GraphPolicy
from .algorithms import SpectralPolicy, DiffusionPolicy


def code_digest() -> str:
    h = hashlib.sha256()
    root = Path(__file__).resolve().parent
    for filename in ("core.py", "algorithms.py", "interchange.py", "reproduce.py"):
        if (root / filename).exists():
            h.update(filename.encode())
            h.update((root / filename).read_bytes())
    return h.hexdigest()


def _observation(row: dict, split: str, unit: str) -> dict:
    return {
        "id": row["id"], "text_sha256": row["text_sha256"],
        "parent_id": row.get("parent_id"), "parent_text_sha256": row.get("parent_text_sha256"),
        "meeting_id": row.get("meeting_id"), "speech_id": row.get("speech_id"),
        "source_family_id": row.get("source_family_id"),
        "date": row["date"], "country": row.get("country"),
        "source_url": row.get("source_url"), "json_pointer": row.get("json_pointer"),
        "start": row.get("start"), "end": row.get("end"),
        "unit": row.get("unit", unit),
        "review_status": row.get("review_status", "not_applicable" if split == "synthetic" else "unreviewed"),
        "exclusion_reasons": row.get("exclusion_reasons", []),
        "source_status": row.get("source_status", "available"),
        "missing_reason": row.get("missing_reason"),
    }


def _diagnostics(model_id: str, fitted: dict) -> list[dict]:
    out = []

    def add(name: str, value: object, unit: str = "scalar") -> None:
        if isinstance(value, (float, np.floating)) and not np.isfinite(value):
            return
        if not (value is None or isinstance(value, (str, int, float, bool, np.number))):
            return
        out.append({
            "model_id": model_id, "name": name,
            "value": int(value) if isinstance(value, (int, bool, np.integer)) else
            float(value) if isinstance(value, (float, np.floating)) else value,
            "denominator": None, "unit": unit,
            "status": "descriptive", "reason": None,
        })

    for i, v in enumerate(fitted.get("eigenvalues", [])[:32], 1):
        add(f"eigenvalue_{i:02d}", v, "eigenvalue")
    summary = fitted.get("diagnostics", {})
    for name in ("boundary_eigengap", "relative_residual", "orthogonality",
                 "stationary_eigenvalue", "negative_eigenvalues", "diffusion_time"):
        if name in summary:
            add(name, summary[name])
    for name, value in summary.get("graph", {}).items():
        add("graph_" + name, value)
    return out


def to_interchange_v1(manifest: dict, values: np.ndarray, fits: dict[str, dict],
                      generated_at: str | None = None) -> dict:
    """All eligible IDs included even on failure; dimension reduction has no cluster."""
    identity = validate_input(manifest, values)
    split = manifest["split"]
    upstream = manifest["upstream"]
    n = identity["n"]
    rows = manifest["observations"]
    excluded_rows = manifest.get("excluded_observations", [])
    if not isinstance(manifest.get("total_in_frame"), int) or manifest["total_in_frame"] != n + len(excluded_rows):
        raise GraphError("Full observed frame must account for all eligible and excluded identities")
    if not isinstance(manifest.get("inventory_meetings"), int):
        raise GraphError("Meeting inventory count must be explicit")
    if not fits:
        raise GraphError("At least one attempted fit required")
    date = generated_at or datetime.now(timezone.utc).isoformat()
    models = []
    results = []
    coverage_models = []
    diagnostics = []
    ledger = []
    for model_id, record in fits.items():
        if not isinstance(model_id, str) or not model_id:
            raise GraphError("Model ID must be nonempty")
        method = record.get("method")
        if method not in {"spectral", "diffusion_map"}:
            raise GraphError("Unsupported model export; do not relabel unrelated fits")
        status = record.get("status")
        if status not in {"fitted", "failed", "skipped"}:
            raise GraphError("Every fit must declare its status")
        fitted = status == "fitted"
        if fitted and method == "spectral":
            labels = np.asarray(record.get("labels"))
            if labels.shape != (n,) or (labels < 1).any() or not np.issubdtype(labels.dtype, np.integer):
                raise GraphError("Invalid spectral assignments or coverage")
        else:
            labels = None
        if fitted:
            coords = np.asarray(record.get("coordinates"))
            if coords.ndim != 2 or coords.shape[0] != n or not np.isfinite(coords).all():
                raise GraphError("Invalid source-linked fitted coordinates")
        parameters = record.get("parameters", {})
        models.append({
            "model_id": model_id, "method_family": "graph_partition" if method == "spectral" else "geometry",
            "method": method, "representation_id": manifest["representation"]["id"],
            "representation_version": manifest["representation"]["version"],
            "fit_version": "graph-methods-0.1.0", "fit_split": split,
            "parameters_sha256": digest(parameters),
            "training_selection_sha256": manifest["representation"]["training_selection_sha256"],
            "diagnostic_basis": "Source-bound descriptive geometry; no independent test",
        })
        assigned = int(n if fitted and labels is not None else 0)
        unassigned = int(n if fitted and labels is None else 0)
        not_fitted = int(n if not fitted else 0)
        for i, row in enumerate(rows):
            row_status = "assigned" if labels is not None else "unassigned" if fitted else "not_fitted"
            results.append({
                "model_id": model_id, "observation_id": row["id"],
                "status": row_status,
                "cluster": int(labels[i]) if labels is not None else 0 if fitted else None,
                "membership_kind": "none", "memberships": None, "membership_strength": None,
                "representation_basis_id": manifest["representation"]["id"],
                "reason": ("Coordinates only; no partition or policy stance" if fitted and labels is None else
                           str(record.get("reason", "Fit unavailable")) if not fitted else None),
            })
        for row in excluded_rows:
            results.append({
                "model_id": model_id, "observation_id": row["id"],
                "status": "excluded", "cluster": None,
                "membership_kind": "none", "memberships": None, "membership_strength": None,
                "representation_basis_id": manifest["representation"]["id"],
                "reason": "; ".join(row["exclusion_reasons"]),
            })
        coverage_models.append({
            "model_id": model_id, "eligible": n, "assigned": assigned,
            "unassigned": unassigned, "not_fitted": not_fitted, "excluded": len(excluded_rows),
            "attempted_fits": int(status != "skipped"),
            "successful_fits": int(fitted), "failed_fits": int(status == "failed"),
            "skipped_fits": int(status == "skipped"),
        })
        if not fitted:
            ledger.append({
                "model_id": model_id, "attempt": 0,
                "status": "failed" if status == "failed" else "skipped",
                "reason": str(record.get("reason") or "No valid fit"),
                "seed": parameters.get("seed"), "source_group": None,
            })
        diagnostics.extend(_diagnostics(model_id, record))
        if fitted:
            fit_metrics = fidelity(values, record["coordinates"], manifest["representation"]["distance_geometry"])
            for name in ("neighbor_overlap", "trustworthiness", "continuity"):
                if name in fit_metrics:
                    diagnostics.append({
                        "model_id": model_id, "name": "geometry_" + name,
                        "value": fit_metrics[name], "denominator": n,
                        "unit": "proportion", "status": "descriptive", "reason": None,
                    })
    envelope = {
        "schema": "un.parallel-analysis.v1", "contract_version": "1.0.0",
        "producer": {
            "workstream_id": "W3", "adapter_version": "0.1.0",
            "code_sha256": code_digest(), "runtime": "Python " + platform.python_version(),
            "generated_at": date,
            "fixture_kind": "synthetic" if split == "synthetic" else "private_development",
        },
        "upstream": {
            "source_schema": upstream["source_schema"], "source_engine": upstream["source_engine"],
            "source_hash_basis": upstream["source_hash_basis"],
            "source_sha256": upstream["source_sha256"],
            "frame_sha256": upstream.get("frame_sha256"),
            "corpus_sha256": upstream.get("corpus_sha256"),
            "selection_sha256": upstream["selection_sha256"],
            "review_sha256": upstream.get("review_sha256"), "missing_reason": None,
        },
        "cohort": {
            "split": split, "population": manifest["population"],
            "unit": manifest.get("unit", "synthetic" if split == "synthetic" else "passage"),
            "selection_policy": manifest["selection_policy"],
            "weighting": manifest.get("weighting", "equal_passage"),
            "source_group_unit": manifest.get("source_group_unit", "meeting"),
            "duplicate_policy": manifest.get("duplicate_policy", "retain_and_audit"),
            "total_in_frame": manifest["total_in_frame"], "eligible": n,
        },
        "observations": [_observation(row, split, manifest.get("unit", "synthetic"))
                         for row in rows + excluded_rows],
        "models": models, "results": results,
        "coverage": {
            "inventory_meetings": manifest["inventory_meetings"],
            "observations_total": manifest["total_in_frame"],
            "eligible": n, "excluded": len(excluded_rows),
            "unavailable_sources": manifest.get("unavailable_sources", 0),
            "models": coverage_models, "failure_ledger": ledger,
        },
        "evidence": [], "diagnostics": diagnostics,
        "limitations": [
            {"code": "development_only", "scope": "all",
             "description": "Synthetic or authorized development only; no held-out evaluation."},
            {"code": "no_policy_inference", "scope": "all",
             "description": "Text-space similarity and geometric diffusion are not political influence, policy transmission, or government stance."},
            {"code": "transductive", "scope": "diffusion",
             "description": "Diffusion maps have no validated out-of-sample extension."},
            {"code": "unknown_attribution", "scope": "provenance",
             "description": "Recorded affiliation is not verified speaker or speech attribution."},
            {"code": "no_significance", "scope": "statistics",
             "description": "Unsupervised structure and refit stability are descriptive, not null-calibrated evidence."},
        ],
        "publication_eligible": False,
        "evaluation_role": "engineering_only",
    }
    # Relational checks beyond structural JSON Schema.
    assert len(envelope["results"]) == (n + len(excluded_rows)) * len(fits)
    assert all(sum(x[k] for k in ("assigned", "unassigned", "not_fitted")) ==
               x["eligible"] for x in coverage_models)
    assert all(x["excluded"] == len(excluded_rows) for x in coverage_models)
    return envelope


def paired_representations(manifest_a: dict, xa: np.ndarray,
                           manifest_b: dict, xb: np.ndarray,
                           graph_policy: GraphPolicy,
                           spectral_policy: SpectralPolicy,
                           diffusion_policy: DiffusionPolicy) -> dict:
    """Source/hash/metric-matched comparison, not a merged or aligned model space."""
    validate_input(manifest_a, xa)
    validate_input(manifest_b, xb)
    equal_population(manifest_a, manifest_b)
    if graph_policy.metric != manifest_a["representation"]["distance_geometry"]:
        raise GraphError("Declared graph metric differs from both representation geometries")
    ga = build_affinity(xa, graph_policy)
    gb = build_affinity(xb, graph_policy)
    sa, sb = spectral_clustering(ga, spectral_policy), spectral_clustering(gb, spectral_policy)
    da, db = diffusion_map(ga, diffusion_policy), diffusion_map(gb, diffusion_policy)
    q = min(8, (len(xa) - 2) // 2)
    # Same neighbor ranking policy on original graph distances.
    knn_a = np.argsort(np.where(np.eye(len(xa), dtype=bool), np.inf, ga.distances),
                       axis=1, kind="stable")[:, :q]
    knn_b = np.argsort(np.where(np.eye(len(xb), dtype=bool), np.inf, gb.distances),
                       axis=1, kind="stable")[:, :q]
    return {
        "status": "paired_source_only",
        "source_identity": manifest_a["observation_join_sha256"],
        "common_upstream": manifest_a["upstream"],
        "representation_a": manifest_a["representation"]["id"],
        "representation_b": manifest_b["representation"]["id"],
        "distance_policy": graph_policy.metric,
        "n_shared": len(xa),
        "spectral_ari": float(adjusted_rand_score(sa["labels"], sb["labels"])),
        "neighbor_overlap": float(np.mean([
            len(set(a) & set(b)) / q for a, b in zip(knn_a, knn_b)
        ])),
        "within_a_diffusion_fidelity": fidelity(xa, da["coordinates"], graph_policy.metric),
        "within_b_diffusion_fidelity": fidelity(xb, db["coordinates"], graph_policy.metric),
        "limitation": "Same sources and chosen distance *definition*, different fitted feature spaces; no coordinate-aligned motion, probability of agreement, or model superiority claim.",
    }
