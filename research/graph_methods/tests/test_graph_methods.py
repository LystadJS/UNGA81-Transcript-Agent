"""Only synthetic, text-free numerical/integrity and contract tests."""
from __future__ import annotations

from dataclasses import replace
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from scipy.linalg import LinAlgError
from sklearn.datasets import make_moons
from sklearn.metrics import adjusted_rand_score

from research.graph_methods import (
    GraphError, GraphPolicy, SpectralPolicy, DiffusionPolicy, build_affinity,
    validate_input, spectral_clustering, diffusion_map, fidelity,
    baseline_comparison, grouped_leave_one_out, parameter_sensitivity,
    to_interchange_v1, equal_population, w1_availability, compare_w1_partition,
)
from research.graph_methods.algorithms import pam_partition, procrustes_disparity, diffusion_policy_sensitivity
from research.graph_methods.core import matrix_digest, digest
from research.graph_methods.reproduce import (
    fixture, fit_or_record, run, source_edges, source_concentration, variations,
)
from research.graph_methods.interchange import paired_representations
from research.graph_methods.w1_bridge import _compare_identities, _require_approval


class SourceIdentityTests(unittest.TestCase):
    def setUp(self):
        self.m, self.x, self.y = fixture(81)

    def test_source_matrix_join(self):
        result = validate_input(self.m, self.x)
        self.assertEqual(result["n"], len(self.x))
        self.assertEqual(result["join_sha256"], self.m["observation_join_sha256"])

    def test_corrupt_matrix(self):
        bad = self.x.copy()
        bad[0, 0] += 0.0001
        with self.assertRaisesRegex(GraphError, "digest"):
            validate_input(self.m, bad)

    def test_duplicate_identity(self):
        bad = copy.deepcopy(self.m)
        bad["observations"][1]["id"] = bad["observations"][0]["id"]
        with self.assertRaisesRegex(GraphError, "Duplicate"):
            validate_input(bad, self.x)

    def test_changed_text_hash(self):
        bad = copy.deepcopy(self.m)
        bad["observations"][0]["text_sha256"] = "a" * 64
        with self.assertRaisesRegex(GraphError, "join"):
            validate_input(bad, self.x)

    def test_reserved_dates(self):
        for date in ("2026-10-05", "2026-10-06"):
            bad = copy.deepcopy(self.m)
            bad["observations"][0]["date"] = date
            with self.assertRaisesRegex(GraphError, "Reserved"):
                validate_input(bad, self.x)

    def test_holdout_refused(self):
        bad = copy.deepcopy(self.m)
        bad["split"] = "holdout"
        with self.assertRaisesRegex(GraphError, "authorized"):
            validate_input(bad, self.x)

    def test_parent_offset_refused(self):
        bad = copy.deepcopy(self.m)
        bad["observations"][0].update(start=5, end=2)
        with self.assertRaisesRegex(GraphError, "offset"):
            validate_input(bad, self.x)

    def test_source_text_never_in_manifest(self):
        bad = copy.deepcopy(self.m)
        bad["observations"][0]["text"] = "invented private-looking text"
        with self.assertRaisesRegex(GraphError, "metadata only"):
            validate_input(bad, self.x)

    def test_mismatched_metric_or_parent(self):
        other = copy.deepcopy(self.m)
        other["representation"]["distance_geometry"] = "cosine"
        with self.assertRaises(GraphError):
            equal_population(self.m, other)
        other = copy.deepcopy(self.m)
        other["observations"][0]["parent_id"] = "replaced"
        with self.assertRaises(GraphError):
            equal_population(self.m, other)

    def test_unpinned_semantic_model(self):
        bad = copy.deepcopy(self.m)
        bad["split"] = "development"
        bad["upstream"]["source_schema"] = "un.passage-corpus.v1"
        bad["representation"]["feature_basis"] = "minilm_pinned"
        with self.assertRaisesRegex(GraphError, "pinned"):
            validate_input(bad, self.x)

    def test_invalid_date_refused(self):
        bad = copy.deepcopy(self.m)
        del bad["observations"][0]["date"]
        with self.assertRaisesRegex(GraphError, "date"):
            validate_input(bad, self.x)
        bad = copy.deepcopy(self.m)
        bad["observations"][0]["date"] = "2026-02-30"
        with self.assertRaisesRegex(GraphError, "date"):
            validate_input(bad, self.x)

    def test_unavailable_frame_source_has_null_hash_not_zero(self):
        excluded = {
            **copy.deepcopy(self.m["observations"][0]),
            "id": "fictional-unavailable",
            "text_sha256": None,
            "parent_id": None,
            "parent_text_sha256": None,
            "source_status": "unavailable",
            "missing_reason": "The invented meeting contains no collected text",
            "exclusion_reasons": ["source_not_collected"],
        }
        full = copy.deepcopy(self.m)
        full["excluded_observations"] = [excluded]
        full["total_in_frame"] += 1
        full["unavailable_sources"] = 1
        full["frame_join_sha256"] = digest([
            [r["id"], r["text_sha256"]]
            for r in full["observations"] + full["excluded_observations"]
        ])
        validate_input(full, self.x)
        env = to_interchange_v1(full, self.x, {
            "w3": {"method": "spectral", "status": "failed",
                   "reason": "independently recorded failed fit"}
        }, generated_at="2026-10-08T00:00:00Z")
        self.assertEqual(env["observations"][-1]["text_sha256"], None)
        self.assertEqual(env["coverage"]["unavailable_sources"], 1)
        self.assertEqual(env["results"][-1]["status"], "excluded")

    def test_development_requires_parent_and_verified_speech(self):
        bad = copy.deepcopy(self.m)
        bad["observations"][0]["speech_id"] = "unverified-speech"
        with self.assertRaisesRegex(GraphError, "speech"):
            validate_input(bad, self.x)
        bad = copy.deepcopy(self.m)
        bad["observations"][0]["parent_text_sha256"] = None
        with self.assertRaisesRegex(GraphError, "parent"):
            validate_input(bad, self.x)

    def test_frame_exclusion_requires_explicit_lineage(self):
        excluded = {
            **copy.deepcopy(self.m["observations"][0]),
            "id": "fictional-excluded-001",
            "text_sha256": hashlib.sha256(b"fictional-excluded").hexdigest(),
            "exclusion_reasons": ["short_or_procedural"],
        }
        bad = copy.deepcopy(self.m)
        bad["total_in_frame"] += 1
        with self.assertRaisesRegex(GraphError, "Frame denominator"):
            validate_input(bad, self.x)
        valid = copy.deepcopy(bad)
        valid["excluded_observations"] = [excluded]
        valid["frame_join_sha256"] = digest([
            [r["id"], r["text_sha256"]]
            for r in valid["observations"] + valid["excluded_observations"]
        ])
        self.assertEqual(validate_input(valid, self.x)["n"], len(self.x))
        failed = {"method": "spectral", "status": "failed", "reason": "test"}
        env = to_interchange_v1(valid, self.x, {"failed": failed},
                                generated_at="2026-10-08T00:00:00Z")
        self.assertEqual(env["coverage"]["excluded"], 1)
        self.assertEqual(len(env["observations"]), len(self.x) + 1)
        self.assertEqual(env["results"][-1]["status"], "excluded")

    def test_unknown_population(self):
        bad = copy.deepcopy(self.m)
        bad["upstream"]["source_sha256"] = None
        with self.assertRaises(GraphError):
            validate_input(bad, self.x)


class GraphQualityTests(unittest.TestCase):
    def test_neighbor_symmetry_diagonal_identity(self):
        _, x, _ = fixture()
        g = build_affinity(x, GraphPolicy(n_neighbors=12, bandwidth=1.4))
        np.testing.assert_allclose(g.weights, g.weights.T)
        self.assertTrue(np.all(np.diag(g.weights) == 0))
        self.assertEqual(g.neighbors.shape, (len(x), 12))
        self.assertTrue(np.isfinite(g.weights).all())

    def test_star_degree_concentration(self):
        x = np.vstack([np.zeros((1, 30)), np.eye(30)])
        g = build_affinity(x, GraphPolicy(n_neighbors=1, bandwidth=2))
        self.assertEqual(g.diagnostics["connected_components"], 1)
        self.assertGreater(g.diagnostics["degree_concentration_ratio"], 8)
        self.assertEqual(g.diagnostics["isolated_count"], 0)

    def test_isolated_mutual(self):
        x = np.vstack([np.zeros((1, 30)), np.eye(30)])
        g = build_affinity(x, GraphPolicy(n_neighbors=1, symmetrize="mutual"))
        self.assertGreater(g.diagnostics["isolated_count"], 0)
        with self.assertRaisesRegex(GraphError, "Isolated"):
            spectral_clustering(g, SpectralPolicy(n_clusters=2))

    def test_disconnected_refused_and_declared(self):
        x = np.array([[0., 0], [.1, 0], [.2, 0], [.3, 0],
                      [100, 0], [100.1, 0], [100.2, 0], [100.3, 0]])
        g = build_affinity(x, GraphPolicy(n_neighbors=2, bandwidth=1.0))
        self.assertEqual(g.diagnostics["connected_components"], 2)
        with self.assertRaisesRegex(GraphError, "Disconnected"):
            diffusion_map(g, DiffusionPolicy(dimensions=2))
        with self.assertRaisesRegex(GraphError, "Disconnected"):
            spectral_clustering(g, SpectralPolicy(n_clusters=2))

    def test_duplicate_vectors_never_lost(self):
        x = np.array([[0., 0], [0., 0], [1., 0], [2., 0], [3., 0], [4., 0]])
        g = build_affinity(x, GraphPolicy(n_neighbors=3))
        self.assertEqual(g.diagnostics["zero_distance_pairs"], 1)
        self.assertEqual(len(g.components), len(x))
        self.assertGreater(g.weights[0, 1], 0)

    def test_kernel_bandwidth_and_k_sensitivity(self):
        _, x, _ = fixture()
        a = build_affinity(x, GraphPolicy(n_neighbors=8, bandwidth=.4))
        b = build_affinity(x, GraphPolicy(n_neighbors=8, bandwidth=2))
        c = build_affinity(x, GraphPolicy(n_neighbors=12, bandwidth=2))
        self.assertGreater(np.linalg.norm(a.weights - b.weights), .1)
        self.assertGreaterEqual(c.diagnostics["edge_count"], b.diagnostics["edge_count"])

    def test_local_kernel_with_duplicates(self):
        x = np.vstack([np.zeros((4, 2)), np.arange(4)[:, None] * np.ones((1, 2))])
        g = build_affinity(x, GraphPolicy(n_neighbors=3, kernel="local_gaussian"))
        self.assertTrue(np.isfinite(g.weights).all())
        self.assertGreater(g.diagnostics["zero_knn_radius_count"], 0)

    def test_less_than_four_fails(self):
        with self.assertRaisesRegex(GraphError, "four"):
            build_affinity(np.zeros((3, 2)), GraphPolicy(n_neighbors=1))

    def test_cosine_requires_nonzero(self):
        with self.assertRaisesRegex(GraphError, "nonzero"):
            build_affinity(np.array([[0., 0], [1, 0], [0, 1], [1, 1]]),
                           GraphPolicy(n_neighbors=2, metric="cosine"))

    def test_recorded_source_concentration_and_duplicate_hash(self):
        m, x, _ = fixture()
        graph = build_affinity(x, GraphPolicy(n_neighbors=8))
        report = source_concentration(m["observations"], graph)
        self.assertEqual(report["edge_count"], graph.diagnostics["edge_count"])
        self.assertEqual(report["duplicate_text_hash_observations"], 0)
        self.assertEqual(report["recorded_group_fields"]["meeting_id"]["known_node_count"], len(x))
        self.assertIsNone(report["recorded_group_fields"]["country"]["within_group_share"])
        self.assertTrue(0 <= report["recorded_group_fields"]["parent_id"]["within_group_share"] <= 1)

    def test_source_linked_edges(self):
        m, x, _ = fixture()
        g = build_affinity(x, GraphPolicy(n_neighbors=8))
        edges = source_edges(m, g)
        self.assertEqual(len(edges), g.diagnostics["edge_count"])
        self.assertEqual(edges[0]["from_text_sha256"],
                         m["observations"][int(edges[0]["from_id"].split("-")[1])]["text_sha256"])


class SpectralTests(unittest.TestCase):
    def test_known_two_moons(self):
        x, truth = make_moons(n_samples=100, noise=.035, random_state=12)
        graph = build_affinity(x, GraphPolicy(n_neighbors=10, bandwidth=.3))
        p = SpectralPolicy(n_clusters=2, allow_disconnected=True, seed=81)
        fit = spectral_clustering(graph, p)
        self.assertEqual(set(np.unique(fit["labels"])), {1, 2})
        self.assertGreater(adjusted_rand_score(truth, fit["labels"]), .80)

    def test_all_supported_laplacians(self):
        x = np.arange(24, dtype=float)[:, None] / 12
        graph = build_affinity(x, GraphPolicy(n_neighbors=4, bandwidth=.5))
        for kind in ("symmetric", "random_walk", "unnormalized"):
            with self.subTest(kind=kind):
                fit = spectral_clustering(graph, SpectralPolicy(n_clusters=2, laplacian=kind))
                self.assertEqual(len(fit["labels"]), 24)
                self.assertLess(fit["diagnostics"]["relative_residual"], 1e-7)

    def test_boundary_degeneracy(self):
        # Regular simplex: complete graph with identical off-diagonal affinities.
        x = np.eye(8)
        g = build_affinity(x, GraphPolicy(n_neighbors=7, bandwidth=1))
        with self.assertRaisesRegex(GraphError, "Degenerate"):
            spectral_clustering(g, SpectralPolicy(n_clusters=2))

    def test_k_constraint(self):
        g = build_affinity(np.arange(6, dtype=float)[:, None],
                           GraphPolicy(n_neighbors=3))
        with self.assertRaisesRegex(GraphError, "clusters"):
            spectral_clustering(g, SpectralPolicy(n_clusters=6))

    def test_baselines_and_seed(self):
        x = np.arange(24, dtype=float)[:, None] / 12
        graph = build_affinity(x, GraphPolicy(n_neighbors=4, bandwidth=.5))
        fit = spectral_clustering(graph, SpectralPolicy(n_clusters=2))
        second = spectral_clustering(graph, SpectralPolicy(n_clusters=2))
        np.testing.assert_array_equal(fit["labels"], second["labels"])
        baseline = baseline_comparison(x, graph, fit, 81)
        self.assertEqual(baseline["population_n"], 24)
        self.assertEqual(baseline["pam"]["coverage"], 24)
        self.assertTrue(-1 <= baseline["pam"]["ari_to_spectral"] <= 1)

    def test_pam_swap_nonincrease(self):
        x = np.arange(15, dtype=float)[:, None]
        d = abs(x - x.T)
        p = pam_partition(d, 3)
        history = p["cost_history"]
        self.assertTrue(all(a >= b - 1e-8 for a, b in zip(history, history[1:])))

    def test_numerical_solver_failure_record(self):
        _, x, _ = fixture()
        graph = build_affinity(x, GraphPolicy(n_neighbors=12))
        with patch("research.graph_methods.algorithms.eigh", side_effect=LinAlgError("failed")):
            record = fit_or_record("spectral", graph, SpectralPolicy(n_clusters=3))
        self.assertEqual(record["status"], "failed")
        self.assertIn("failed", record["reason"])


class DiffusionTests(unittest.TestCase):
    def setUp(self):
        x = np.linspace(-3, 3, 45)
        self.x = np.column_stack((x, np.sin(x)))
        self.g = build_affinity(self.x, GraphPolicy(n_neighbors=8, bandwidth=1))

    def test_diffusion_stationary_and_dimensions(self):
        fit = diffusion_map(self.g, DiffusionPolicy(alpha=.5, time=2, dimensions=2))
        self.assertEqual(fit["coordinates"].shape, (45, 2))
        self.assertAlmostEqual(fit["eigenvalues"][0], 1, places=8)
        self.assertLess(fit["diagnostics"]["relative_residual"], 1e-7)
        self.assertFalse(fit["publication_eligible"])

    def test_time_and_normalization_sensitivity(self):
        early = diffusion_map(self.g, DiffusionPolicy(alpha=0, time=1, dimensions=2))
        late = diffusion_map(self.g, DiffusionPolicy(alpha=0, time=4, dimensions=2))
        self.assertLess(np.linalg.norm(late["coordinates"]),
                        np.linalg.norm(early["coordinates"]))
        other = diffusion_map(self.g, DiffusionPolicy(alpha=1, time=1, dimensions=2))
        self.assertFalse(np.allclose(early["coordinates"], other["coordinates"]))

    def test_fidelity_range(self):
        fit = diffusion_map(self.g, DiffusionPolicy(dimensions=2))
        report = fidelity(self.x, fit["coordinates"])
        self.assertTrue(0 <= report["neighbor_overlap"] <= 1)
        self.assertTrue(0 <= report["trustworthiness"] <= 1)
        self.assertTrue(0 <= report["continuity"] <= 1)

    def test_invalid_diffusion_dimension_and_time(self):
        with self.assertRaises(GraphError):
            diffusion_map(self.g, DiffusionPolicy(dimensions=44))
        with self.assertRaises(GraphError):
            diffusion_map(self.g, DiffusionPolicy(time=0))

    def test_diffusion_policy_sweep(self):
        fitted = diffusion_map(self.g, DiffusionPolicy(alpha=.5, time=2, dimensions=2))
        policies = [DiffusionPolicy(alpha=0, time=2, dimensions=2),
                    DiffusionPolicy(alpha=1, time=2, dimensions=2),
                    DiffusionPolicy(alpha=.5, time=4, dimensions=2),
                    DiffusionPolicy(alpha=.5, time=2, dimensions=1)]
        report = diffusion_policy_sensitivity(self.x, self.g, fitted, policies)
        self.assertEqual(report["planned"], 4)
        self.assertEqual(len(report["attempts"]), 4)
        self.assertEqual(sum(r["status"] == "fitted" for r in report["attempts"]),
                         report["successful"])
        self.assertIsNone(report["attempts"][3]["procrustes_disparity"])

    def test_rotation_invariance(self):
        x = np.random.default_rng(1).normal(size=(30, 2))
        theta = .4
        r = np.array([[np.cos(theta), -np.sin(theta)],
                      [np.sin(theta), np.cos(theta)]])
        self.assertLess(procrustes_disparity(x, x @ r), 1e-12)


class W1BridgeTests(unittest.TestCase):
    """W1 remains a draft PR: test the cross-language gate without importing it."""

    def setUp(self):
        self.m, self.x, _ = fixture()
        self.fitted = spectral_clustering(
            build_affinity(self.x, GraphPolicy(n_neighbors=16, bandwidth=1.4)),
            SpectralPolicy(n_clusters=3),
        )
        self.envelope = to_interchange_v1(
            self.m, self.x, {"pinned-model": self.fitted},
            generated_at="2026-10-08T00:00:00Z",
        )

    def test_unaccepted_w1_gates_refuse_import(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(w1_availability(Path(d))["status"], "withheld")
            with self.assertRaisesRegex(GraphError, "coordinator"):
                compare_w1_partition(
                    self.m, self.x, self.fitted, self.envelope, {},
                    w1_model_id="pinned-model", repo_root=Path(d),
                )

    def test_source_bound_w1_population_compatibility(self):
        _compare_identities(self.m, self.envelope)
        changed = copy.deepcopy(self.envelope)
        changed["observations"][0]["parent_id"] = "invented-different-parent"
        with self.assertRaisesRegex(GraphError, "parent"):
            _compare_identities(self.m, changed)
        changed = copy.deepcopy(self.envelope)
        changed["upstream"]["selection_sha256"] = "0" * 64
        with self.assertRaisesRegex(GraphError, "selection"):
            _compare_identities(self.m, changed)
        changed = copy.deepcopy(self.envelope)
        changed["observations"] = changed["observations"][::-1]
        with self.assertRaisesRegex(GraphError, "order"):
            _compare_identities(self.m, changed)

    def test_commit_not_confused_with_code_sha(self):
        sha = "c" * 64
        approved = {
            "schema": "un.w1-approval.v1", "adapter_version": "source-validation-1.0.0",
            "w1_producer_code_sha256": sha,
            "w1_merged_commit_sha": "d" * 40, "accepted": True,
        }
        _require_approval(approved, sha)
        with self.assertRaisesRegex(GraphError, "SHA"):
            _require_approval({**approved, "w1_merged_commit_sha": "d" * 64}, sha)
        with self.assertRaisesRegex(GraphError, "not granted"):
            _require_approval({**approved, "accepted": False}, sha)


class IntegrationTests(unittest.TestCase):
    def test_exactly_paired_representation_rotation(self):
        m, x, _ = fixture()
        transformed = x @ np.array([[0., -1.], [1., 0.]])
        peer = copy.deepcopy(m)
        peer["representation"]["id"] = "fictional-rotated-geometry"
        peer["representation"]["matrix_sha256"] = matrix_digest(transformed)
        outcome = paired_representations(
            m, x, peer, transformed,
            GraphPolicy(n_neighbors=16, bandwidth=1.4),
            SpectralPolicy(n_clusters=3), DiffusionPolicy(dimensions=2),
        )
        self.assertEqual(outcome["n_shared"], len(x))
        self.assertAlmostEqual(outcome["neighbor_overlap"], 1, places=8)
        self.assertEqual(outcome["status"], "paired_source_only")
        mismatched = copy.deepcopy(peer)
        mismatched["upstream"]["selection_sha256"] = "0" * 64
        with self.assertRaises(GraphError):
            paired_representations(
                m, x, mismatched, transformed,
                GraphPolicy(n_neighbors=16, bandwidth=1.4),
                SpectralPolicy(n_clusters=3), DiffusionPolicy(dimensions=2),
            )

    def test_group_resampling_never_uses_rows(self):
        m, x, _ = fixture()
        g = build_affinity(x, GraphPolicy(n_neighbors=16, bandwidth=1.4))
        fit = fit_or_record("spectral", g, SpectralPolicy(n_clusters=3))
        if fit["status"] != "fitted":
            self.skipTest("Fixture disconnected; failure ledger tested in CLI")
        group = grouped_leave_one_out(
            x, m["observations"], g.policy, SpectralPolicy(n_clusters=3), fit)
        self.assertEqual(group["planned"], 6)
        self.assertEqual(group["planned"], group["successful"] + group["failed"])
        self.assertTrue(all("omitted_group" in a for a in group["attempts"]))
        missing = copy.deepcopy(m["observations"])
        missing[0]["meeting_id"] = None
        withheld = grouped_leave_one_out(x, missing, g.policy, SpectralPolicy(), fit)
        self.assertEqual(withheld["status"], "withheld")

    def test_sensitivity_failures_counted(self):
        x = np.linspace(0, 1, 25)[:, None]
        gp = GraphPolicy(n_neighbors=5)
        s = spectral_clustering(build_affinity(x, gp), SpectralPolicy(n_clusters=2))
        variants = [GraphPolicy(n_neighbors=1, symmetrize="mutual"),
                    GraphPolicy(n_neighbors=8)]
        report = parameter_sensitivity(x, s, gp, SpectralPolicy(n_clusters=2), variants)
        self.assertEqual(report["planned"], 2)
        self.assertLessEqual(report["successful"], 2)
        self.assertEqual(len(report["attempts"]), 2)

    def test_v1_schema_and_coverage(self):
        import jsonschema
        m, x, _ = fixture()
        graph = build_affinity(x, GraphPolicy(n_neighbors=16, bandwidth=1.4))
        spect = fit_or_record("spectral", graph, SpectralPolicy(n_clusters=3))
        diff = fit_or_record("diffusion_map", graph, DiffusionPolicy())
        env = to_interchange_v1(m, x, {"s": spect, "d": diff},
                                generated_at="2026-10-08T00:00:00Z")
        schema = json.loads((Path(__file__).resolve().parents[3] /
                             "docs/parallel-work/interchange-v1.schema.json").read_text())
        jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(env)
        self.assertEqual(len(env["results"]), 2 * len(x))
        self.assertFalse(env["publication_eligible"])
        self.assertEqual(env["producer"]["workstream_id"], "W3")
        for row in env["coverage"]["models"]:
            self.assertEqual(row["assigned"] + row["unassigned"] + row["not_fitted"], len(x))

    def test_primary_failure_does_not_masquerade_as_empty_result(self):
        m, x, _ = fixture()
        failed = {"method": "spectral", "status": "failed", "reason": "deliberate",
                  "parameters": {"seed": 81}}
        env = to_interchange_v1(m, x, {"s": failed},
                                generated_at="2026-10-08T00:00:00Z")
        self.assertEqual(env["coverage"]["models"][0]["not_fitted"], len(x))
        self.assertEqual(env["coverage"]["models"][0]["failed_fits"], 1)
        self.assertEqual(env["coverage"]["failure_ledger"][0]["reason"], "deliberate")

    def test_replay_receipt_and_charts(self):
        m, x, truth = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "output"
            result = run(m, x, p, synthetic_labels=truth)
            self.assertEqual(result["heldout_transcripts_opened"], 0)
            self.assertTrue((p / "receipt.json").exists())
            self.assertTrue((p / "affinity.svg").exists())
            expected = json.loads((p / "SHA256.json").read_text())
            for name, h in expected.items():
                self.assertEqual(hashlib.sha256((p / name).read_bytes()).hexdigest(), h)
            with self.assertRaisesRegex(GraphError, "empty"):
                run(m, x, p, synthetic_labels=truth)

    def test_independent_replay_byte_identical(self):
        m, x, labels = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            p1, p2 = Path(tmp) / "r1", Path(tmp) / "r2"
            run(m, x, p1, synthetic_labels=labels)
            run(m, x, p2, synthetic_labels=labels)
            self.assertEqual(
                json.loads((p1 / "SHA256.json").read_text()),
                json.loads((p2 / "SHA256.json").read_text()))

    def test_private_development_never_writes_inside_repo(self):
        m, x, _ = fixture()
        m = copy.deepcopy(m)
        m["split"] = "development"
        m["upstream"]["source_schema"] = "un.passage-corpus.v1"
        m["upstream"]["source_hash_basis"] = "canonical_source_text"
        m["representation"]["feature_basis"] = "tfidf_lsa"
        for row in m["observations"]:
            row["split"] = "development"
        validate_input(m, x)
        repo = Path(__file__).resolve().parents[3]
        with self.assertRaisesRegex(GraphError, "outside Git"):
            run(m, x, repo / "forbidden-private-research-output")
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "private"
            report = run(m, x, folder)
            self.assertEqual(report["split"], "development")
            self.assertEqual(os.stat(folder).st_mode & 0o077, 0)
            self.assertEqual(os.stat(folder / "receipt.json").st_mode & 0o077, 0)
            self.assertNotEqual(report["w1_source_aware"]["status"], "validated")

    def test_nuisance_negative_control_is_not_significance_test(self):
        x = np.random.default_rng(29).normal(size=(40, 5))
        g = build_affinity(x, GraphPolicy(n_neighbors=12, bandwidth=2))
        s = fit_or_record("spectral", g, SpectralPolicy(n_clusters=2))
        self.assertNotIn("p_value", s)
        self.assertFalse(s.get("publication_eligible", False))
        self.assertNotIn("policy_influence", s)


if __name__ == "__main__":
    unittest.main()
