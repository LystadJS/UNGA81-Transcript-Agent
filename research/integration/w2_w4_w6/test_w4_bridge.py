"""Native offline W4->W6 source, alignment and weighting acceptance."""
from copy import deepcopy
import math
import unittest

from research.longitudinal.fixtures import make_panel
from research.longitudinal.framework import compare, to_interchange_v1
from research.integration.w2_w4_w6.w4_bridge import validate_source, to_w6_longitudinal

ANCHORS = [f"A{i}" for i in range(6)]


def inputs(*, motion=False, fit_policy="full_refit", missing=None, roster=True):
    raw = make_panel(motion=motion, fit_policy=fit_policy,
                     unavailable_family=missing, roster=roster)
    comparison = compare(raw, "p0", "p1", anchor_ids=ANCHORS,
                         bootstrap_reps=50, bootstrap_seed=30092026)
    envelope = to_interchange_v1(raw, comparison)
    return raw, comparison, envelope


def actor(result, actor_id, period):
    source = next(a for a in result["actors"] if a["id"] == actor_id)
    return next(p for p in source["positions"] if p["period"] == period)


class W4W6Acceptance(unittest.TestCase):
    def test_original_full_refit_tracks_matched_genres_with_exact_source_counts(self):
        raw, comparison, envelope = inputs()
        validate_source(raw, comparison, envelope)
        p = to_w6_longitudinal(raw, comparison, envelope, selection_checked=True)
        self.assertEqual(p["status"], "ready")
        self.assertEqual(p["alignments"][0]["mode"], "rigid_full_refit")
        self.assertGreaterEqual(p["alignments"][0]["anchors"], 4)
        self.assertEqual(p["periods"], ["p0", "p1"])
        self.assertEqual(p["coverage"]["frame"], envelope["cohort"]["total_in_frame"])
        self.assertEqual(p["coverage"]["eligible"], envelope["cohort"]["eligible"])
        self.assertEqual(p["period_bounds"]["p0"]["start"], "2026-01-01")
        self.assertEqual(actor(p, "T0", "p0")["n"], 8)
        self.assertEqual(actor(p, "T0", "p1")["n"], 8)
        self.assertEqual(actor(p, "T0", "p0")["status"], "observed")
        self.assertEqual(actor(p, "T0", "p1")["status"], "observed")
        self.assertAlmostEqual(actor(p, "T0", "p0")["xy"][0], .5, places=8)
        self.assertAlmostEqual(actor(p, "T0", "p1")["xy"][0], .5, places=8)
        self.assertEqual(actor(p, "N0", "p0")["status"], "missing")
        self.assertEqual(actor(p, "N0", "p1")["status"], "observed")
        self.assertIsNone(actor(p, "T0", "p0")["radius"])
        self.assertFalse(p["warnings"][0].find("political motion") < 0)

    def test_known_motion_only_on_declared_fictional_target(self):
        raw, comparison, envelope = inputs(motion=True)
        p = to_w6_longitudinal(raw, comparison, envelope, selection_checked=True)
        before = actor(p, "T0", "p0")["xy"]
        after = actor(p, "T0", "p1")["xy"]
        self.assertAlmostEqual(after[0]-before[0], .8, places=8)
        self.assertAlmostEqual(after[1]-before[1], .2, places=8)
        control = actor(p, "A1", "p0")["xy"]
        same = actor(p, "A1", "p1")["xy"]
        self.assertAlmostEqual(math.dist(control, same), 0, places=8)

    def test_same_pinned_map_requires_no_fabricated_anchors(self):
        raw, comparison, envelope = inputs(fit_policy="transformed_reference")
        p = to_w6_longitudinal(raw, comparison, envelope, selection_checked=True)
        self.assertEqual(p["status"], "ready")
        self.assertEqual(p["alignments"][0]["mode"], "identity_pinned_transform")
        self.assertEqual(p["alignments"][0]["anchors"], 0)
        self.assertEqual(p["alignments"][0]["status"], "passed")

    def test_selection_not_authenticated_withholds_all_position_coordinates(self):
        raw, comparison, envelope = inputs()
        p = to_w6_longitudinal(raw, comparison, envelope)
        self.assertEqual(p["status"], "withheld")
        self.assertEqual(p["coverage"]["included"], 0)
        self.assertEqual(p["alignments"][0]["selection_comparability"], "not_assessed")
        self.assertTrue(all(q["xy"] is None for a in p["actors"] for q in a["positions"]))

    def test_unavailable_source_not_imputed_as_zero(self):
        raw, comparison, envelope = inputs(missing=("p1", 7))
        p = to_w6_longitudinal(raw, comparison, envelope, selection_checked=True)
        self.assertEqual(p["coverage"]["excluded"], envelope["coverage"]["excluded"])
        self.assertGreater(p["coverage"]["missing"], 0)
        self.assertTrue(all(o["xy"] is None for a in p["actors"]
                            for o in a["positions"] if o["status"] != "observed"))
        self.assertEqual(actor(p, "T1", "p1")["n"], 7)

    def test_corruption_of_source_selection_and_fit_identity_is_rejected(self):
        raw, comparison, envelope = inputs()
        changed = deepcopy(envelope)
        changed["upstream"]["selection_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "source or selection"):
            validate_source(raw, comparison, changed)
        changed = deepcopy(comparison)
        changed["aligned_coordinates"][0]["actor_id"] = "wrong"
        with self.assertRaisesRegex(ValueError, "actor"):
            validate_source(raw, changed, envelope)
        changed = deepcopy(envelope)
        changed["models"][0]["representation_id"] = "unrelated-vocabulary"
        with self.assertRaisesRegex(ValueError, "Frozen input representation"):
            validate_source(raw, comparison, changed)
        changed = deepcopy(raw)
        changed["observations"][0]["source_family_id"] = "not-the-original"
        with self.assertRaisesRegex(ValueError, "panel bytes/content"):
            validate_source(changed, comparison, envelope)

    def test_non_synthetic_public_export_is_forbidden(self):
        raw, comparison, envelope = inputs()
        copy = deepcopy(envelope)
        copy["producer"]["fixture_kind"] = "private_development"
        with self.assertRaisesRegex(ValueError, "Real development"):
            validate_source(raw, comparison, copy)


if __name__ == "__main__":
    unittest.main()
