"""True W1↔W3 source-bound synthetic interoperability on the merged checkout.

Requires W1 files on the SAME Git tree; no fetch, unmerged module import or
private data. On a W3 push-only branch without merged W1, these tests skip and
the PR-checkout merge CI has a separate gate requiring their execution.
"""
from __future__ import annotations

import copy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np
from sklearn.metrics import adjusted_mutual_info_score, adjusted_rand_score

from research.graph_methods.algorithms import SpectralPolicy, spectral_clustering
from research.graph_methods.core import GraphError, GraphPolicy, build_affinity, digest, matrix_digest, validate_input
from research.graph_methods.w1_bridge import compare_w1_partition, availability

ROOT = Path(__file__).resolve().parents[3]
W1_MERGED_SHA = "87dedd6ee7b30fb7cd1e26e8ef26e30ee8e52329"
MODEL_ID = "synthetic-semantic-hdbscan"

# W1's authentic synthetic fixture/runner/adapter are invoked from the merged
# checkout. No duplicate W1 metric logic or copying W1 source into W3.
W1_FIXTURE_SCRIPT = r"""
'use strict';
const {makeFixture,SETTINGS}=require('./research/validation_framework/examples/synthetic_fixture.cjs');
const {run}=require('./research/validation_framework/runner.cjs');
const {toInterchangeV1}=require('./research/validation_framework/interchange.cjs');
const fixture=makeFixture();
const setting=SETTINGS.filter(s=>s.id==='synthetic-semantic-hdbscan');
if(setting.length!==1)throw Error('Pinned W1 synthetic reference model absent');
run(fixture.frame,setting,{saved:fixture.saved,group_units:[],replicates:2,group_seed:31})
  .then(out=>{
    const envelope=toInterchangeV1(out);
    process.stdout.write(JSON.stringify({envelope,saved:fixture.saved}));
  })
  .catch(e=>{console.error(String(e.stack||e));process.exit(1)});
"""


def w1_reference():
    if availability(ROOT)["status"] == "withheld":
        raise unittest.SkipTest("W1 is absent from checkout; PR merged-tree gate requires it")
    proc = subprocess.run(
        ["node", "-e", W1_FIXTURE_SCRIPT], cwd=ROOT,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=60, check=False,
    )
    if proc.returncode:
        raise RuntimeError("Actual installed W1 fixture failed: " + proc.stderr[:1200])
    return json.loads(proc.stdout)


def paired_fixture():
    original = w1_reference()
    env, saved = original["envelope"], original["saved"]
    eligible = [r for r in env["observations"] if
                r["source_status"] == "available" and not r["exclusion_reasons"]]
    excluded = [r for r in env["observations"] if
                r["source_status"] != "available" or r["exclusion_reasons"]]
    if len(eligible) != 24 or len(excluded) != 1:
        raise AssertionError("W1 synthetic eligibility unexpectedly changed")
    vectors = {r["id"]: r for r in saved["rows"]}
    x = np.asarray([vectors[r["id"]]["vector"] for r in eligible], dtype=float)
    for row in eligible:
        if row["text_sha256"] != vectors[row["id"]]["text_sha256"]:
            raise AssertionError("W1 invented saved vector's original hash differs")
    model = next(m for m in env["models"] if m["model_id"] == MODEL_ID)
    m = {
        "schema": "un.graph-input.v1",
        "split": "synthetic",
        "upstream": copy.deepcopy(env["upstream"]),
        "representation": {
            "id": model["representation_id"],
            "version": model["representation_version"],
            "feature_basis": "synthetic",
            "distance_geometry": "euclidean",
            "matrix_sha256": matrix_digest(x),
            "training_selection_sha256": model["training_selection_sha256"],
        },
        "population": "w1_merged_synthetic_fixture",
        "unit": "synthetic", "source_group_unit": "meeting",
        "selection_policy": "same eligible W1 source+text identities",
        "weighting": "equal_passage", "duplicate_policy": "retain_and_audit",
        "inventory_meetings": env["coverage"]["inventory_meetings"],
        "total_in_frame": env["coverage"]["observations_total"],
        "unavailable_sources": env["coverage"]["unavailable_sources"],
        "observations": eligible, "excluded_observations": excluded,
        "observation_join_sha256": digest(
            [[r["id"], r["text_sha256"]] for r in eligible]),
        "frame_join_sha256": digest(
            [[r["id"], r["text_sha256"]] for r in eligible + excluded]),
    }
    validate_input(m, x)
    if m["upstream"]["selection_sha256"] != m["observation_join_sha256"]:
        raise AssertionError("JS↔Python canonical ordered source pair digest differs")
    return m, x, env


def actual_approval():
    file = ROOT / "research/validation_framework/runner.cjs"
    return {
        "schema": "un.w1-approval.v1",
        "accepted": True,
        "adapter_version": "source-validation-1.0.0",
        "w1_producer_code_sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
        "w1_merged_commit_sha": W1_MERGED_SHA,
    }


class AcceptedW1InteropTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.x, cls.envelope = paired_fixture()
        cls.approval = actual_approval()
        cls.graph = build_affinity(
            cls.x, GraphPolicy(n_neighbors=len(cls.x) - 1,
                               metric="euclidean", bandwidth=5.0),
        )
        cls.spectral = spectral_clustering(
            cls.graph, SpectralPolicy(n_clusters=3, seed=81),
        )

    def test_authentic_w1_native_metrics_and_denominators(self):
        result = compare_w1_partition(
            self.manifest, self.x, self.spectral, self.envelope,
            self.approval, w1_model_id=MODEL_ID, repo_root=ROOT,
        )
        self.assertEqual(result["schema"], "un.w1-w3-comparison.v1")
        self.assertEqual(result["status"], "descriptive")
        self.assertEqual(result["observation_count"], 24)
        self.assertEqual(result["w1_accepted_commit_sha"], W1_MERGED_SHA)
        metrics = result["metrics"]
        self.assertEqual(metrics["observations"], 24)
        self.assertEqual(metrics["transitions"]["both_assigned"], 24)
        self.assertEqual(metrics["pair_opportunities_all"], 276)
        self.assertEqual(metrics["pair_opportunities_assigned_both"], 276)
        self.assertEqual(metrics["assignment_coverage_left"], 1)
        self.assertEqual(metrics["assignment_coverage_right"], 1)
        self.assertEqual(result["source_validation"]["eligible"], 24)
        self.assertEqual(result["source_validation"]["excluded"], 1)
        self.assertEqual(result["source_validation"]["selection_sha256"],
                         self.manifest["upstream"]["selection_sha256"])
        self.assertEqual(result["source_validation"]["meeting_group_schedule"]["status"],
                         "scheduled")
        self.assertEqual(result["source_validation"]["meeting_group_schedule"]["groups"], 6)
        self.assertEqual(result["source_validation"]["meeting_group_schedule"]["attempted"], 2)
        w1_rows = {r["observation_id"]: r for r in self.envelope["results"]
                   if r["model_id"] == MODEL_ID}
        labels = [w1_rows[o["id"]]["cluster"] for o in self.manifest["observations"]]
        self.assertAlmostEqual(
            metrics["ari"], adjusted_rand_score(labels, self.spectral["labels"]), places=9)
        self.assertAlmostEqual(
            metrics["adjusted_mutual_information"],
            adjusted_mutual_info_score(labels, self.spectral["labels"]), places=9)
        self.assertFalse(result["publication_eligible"])
        self.assertEqual(result["comparison_protocol"],
                         "same_source_and_underlying_representation_identity")

    def test_missing_is_explicitly_excluded_not_zero(self):
        self.assertEqual(self.manifest["total_in_frame"], 25)
        self.assertEqual(self.manifest["unavailable_sources"], 1)
        self.assertEqual(len(self.manifest["excluded_observations"]), 1)
        row = self.manifest["excluded_observations"][0]
        self.assertIsNone(row["text_sha256"])
        self.assertEqual(row["source_status"], "unavailable")
        self.assertTrue(row["missing_reason"])
        self.assertEqual(self.envelope["coverage"]["excluded"], 1)

    def test_refuse_source_and_selection_swaps(self):
        for key in ("source_sha256", "source_hash_basis", "selection_sha256"):
            with self.subTest(field=key):
                bad = copy.deepcopy(self.manifest)
                bad["upstream"][key] = ("0" * 64 if key != "source_hash_basis"
                                         else "canonical_source_text")
                with self.assertRaises(GraphError):
                    compare_w1_partition(bad, self.x, self.spectral, self.envelope,
                                         self.approval, w1_model_id=MODEL_ID, repo_root=ROOT)

    def test_refuse_mismatched_parent_affiliation_or_missing_coverage(self):
        for where, field, value in (
            ("observations", "meeting_id", "other-invented-meeting"),
            ("observations", "parent_id", "other-parent"),
            ("observations", "source_family_id", "other-family"),
            ("observations", "country", "invented-other-affiliation"),
            ("observations", "start", 4),
            ("excluded_observations", "missing_reason", "invented revised availability"),
        ):
            with self.subTest(where=where, field=field):
                bad = copy.deepcopy(self.manifest)
                bad[where][0][field] = value
                with self.assertRaises(GraphError):
                    compare_w1_partition(
                        bad, self.x, self.spectral, self.envelope, self.approval,
                        w1_model_id=MODEL_ID, repo_root=ROOT)

    def test_refuse_representation_and_unapproved_commit(self):
        bad = copy.deepcopy(self.manifest)
        bad["representation"]["version"] = "invented-other-version"
        with self.assertRaises(GraphError):
            compare_w1_partition(
                bad, self.x, self.spectral, self.envelope,
                self.approval, w1_model_id=MODEL_ID, repo_root=ROOT)
        for change in (
            {"accepted": False},
            {"w1_merged_commit_sha": "a" * 40},
            {"w1_producer_code_sha256": "0" * 64},
        ):
            with self.subTest(change=change):
                with self.assertRaises(GraphError):
                    compare_w1_partition(
                        self.manifest, self.x, self.spectral, self.envelope,
                        {**self.approval, **change}, w1_model_id=MODEL_ID,
                        repo_root=ROOT)

    def test_refuse_forged_W1_model_or_producer(self):
        for key in ("id", "training", "producer"):
            with self.subTest(key=key):
                e = copy.deepcopy(self.envelope)
                if key == "id":
                    e["models"][0]["representation_id"] = "invented-foreign-fit"
                elif key == "training":
                    e["models"][0]["training_selection_sha256"] = "0" * 64
                else:
                    e["producer"]["code_sha256"] = "0" * 64
                with self.assertRaises(GraphError):
                    compare_w1_partition(
                        self.manifest, self.x, self.spectral, e, self.approval,
                        w1_model_id=MODEL_ID, repo_root=ROOT)

    def test_refuse_partial_observation_assignments(self):
        bad = copy.deepcopy(self.envelope)
        bad["results"] = bad["results"][1:]
        with self.assertRaises(GraphError):
            compare_w1_partition(
                self.manifest, self.x, self.spectral, bad, self.approval,
                w1_model_id=MODEL_ID, repo_root=ROOT)


def synthetic_receipt(destination: Path) -> dict:
    """Aggregate-only SHA-verifiable W1-W3 evidence; never export source rows."""
    manifest, x, envelope = paired_fixture()
    policy = GraphPolicy(n_neighbors=len(x)-1, metric="euclidean", bandwidth=5.0)
    fit = spectral_clustering(
        build_affinity(x, policy), SpectralPolicy(n_clusters=3, seed=81))
    comparison = compare_w1_partition(
        manifest, x, fit, envelope, actual_approval(),
        w1_model_id=MODEL_ID, repo_root=ROOT)
    index = {r["observation_id"]: r for r in envelope["results"]
             if r["model_id"] == MODEL_ID}
    w1_labels = [index[r["id"]]["cluster"] for r in manifest["observations"]]
    references = {
        "independent_sklearn_ari": float(adjusted_rand_score(w1_labels, fit["labels"])),
        "independent_sklearn_ami": float(adjusted_mutual_info_score(
            w1_labels, fit["labels"])),
    }
    if not np.isclose(comparison["metrics"]["ari"], references["independent_sklearn_ari"],
                      rtol=0, atol=1e-9):
        raise RuntimeError("W1-W3 ARI disagrees with independent reference")
    if not np.isclose(
        comparison["metrics"]["adjusted_mutual_information"],
        references["independent_sklearn_ami"], rtol=0, atol=1e-9
    ):
        raise RuntimeError("W1-W3 AMI disagrees with independent reference")
    receipt = {
        "schema": "un.w1-w3-synthetic-interoperability-receipt.v1",
        "fixture_kind": "synthetic", "source_schema": manifest["upstream"]["source_schema"],
        "source_sha256": manifest["upstream"]["source_sha256"],
        "source_hash_basis": manifest["upstream"]["source_hash_basis"],
        "selection_sha256": manifest["upstream"]["selection_sha256"],
        "w1": {
            "adapter_version": envelope["producer"]["adapter_version"],
            "merged_commit_sha": W1_MERGED_SHA,
            "producer_code_sha256": envelope["producer"]["code_sha256"],
            "model_id": MODEL_ID, "representation_id": manifest["representation"]["id"],
            "representation_version": manifest["representation"]["version"],
        },
        "w3": {
            "graph_policy": asdict(policy), "spectral_policy": asdict(
                SpectralPolicy(n_clusters=3, seed=81)),
            "matrix_sha256": manifest["representation"]["matrix_sha256"],
        },
        "frame": {"eligible": len(manifest["observations"]),
                  "excluded": len(manifest["excluded_observations"]),
                  "unavailable_sources": manifest["unavailable_sources"]},
        "comparison": comparison, "reference": references,
        "heldout_transcripts_opened": 0,
        "publication_eligible": False,
        "evaluation_role": "engineering_only",
    }
    # No invented fixture ID, row-level assignment, passage, or original text is
    # included in the public aggregate artifact.
    destination.write_text(json.dumps(receipt, sort_keys=True, indent=2,
                                      allow_nan=False) + "\n", encoding="utf8")
    return receipt


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--receipt":
        synthetic_receipt(Path(sys.argv[2]))
        print("Synthetic W1-W3 aggregate interoperability receipt generated")
    else:
        unittest.main()
