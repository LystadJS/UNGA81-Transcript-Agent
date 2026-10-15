import unittest
from calibration import generate, digest, consensus, calibrate

class CalibrationTests(unittest.TestCase):
    def test_determinism_and_controls(self):
        a = generate(31)
        self.assertEqual(digest(a), digest(generate(31)))
        self.assertNotEqual(digest(a), digest(generate(32)))
        self.assertNotEqual(digest(a), digest(generate(31, signal=1)))
        self.assertEqual(len(a), 96)

    def test_balanced_families(self):
        ids = ["a", "b"]
        fits = [{"family":"lexical","status":"converged","labels":{"a":1,"b":1}} for _ in range(10)]
        fits += [{"family":"graph","status":"converged","labels":{"a":1,"b":2}}]
        out = consensus(fits, ids)
        self.assertAlmostEqual(out["pairs"][0]["coassignment"], .5)
        self.assertEqual(out["pairs"][0]["eligible_fit_pairs"], 11)
        self.assertEqual(len(out["ledger"]), 11)

    def test_fail_closed(self):
        def record(seed, value=0, groups=12, identifiable=True):
            return dict(seed=seed, statistic=value, groups=groups,
                        nuisance_converged=True, identifiable=identifiable,
                        generator_hash="a", estimator_hash="b")
        dev = [record(i, i / 1000) for i in range(200)]
        hold = [record(i+1000, i / 1000) for i in range(200)]
        ok = calibrate(dev, hold)
        self.assertTrue(ok["ready"])
        self.assertEqual(ok["attempted_holdout"], 200)
        self.assertFalse(calibrate(dev, dev)["ready"])
        self.assertFalse(calibrate(dev, hold[:20])["ready"])
        self.assertFalse(calibrate(dev, [dict(hold[0], identifiable=False)] + hold[1:])["ready"])
        self.assertFalse(calibrate(dev, [dict(hold[0], groups=3)] + hold[1:])["ready"])

    def test_unassigned(self):
        x = consensus([{"family":"a","status":"converged",
                        "labels":{"a":0,"b":1}}], ["a","b"])
        self.assertIsNone(x["pairs"][0]["coassignment"])
        self.assertEqual(x["pairs"][0]["eligible_fit_pairs"], 0)

if __name__ == "__main__":
    unittest.main()
