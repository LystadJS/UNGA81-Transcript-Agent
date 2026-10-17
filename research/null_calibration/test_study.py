import unittest
from study import seeded, world, estimate, digest, bootstrap, stat, evaluate, summary, wilson, smoke

class StudyTests(unittest.TestCase):
    def test_deterministic_fixture(self):
        self.assertEqual(digest(world(31)),digest(world(31)))
        self.assertNotEqual(digest(world(31)),digest(world(32)))
        self.assertNotEqual(seeded(810081,"balanced_null","development",0),
                            seeded(810081,"balanced_null","holdout",0))
    def test_nuisance_reestimated_without_oracle(self):
        data=world(31)
        fitted=estimate(data)
        self.assertTrue(fitted["ready"])
        self.assertFalse(fitted["year_rho_identified"])
        self.assertAlmostEqual(stat(bootstrap(data,fitted,45)),stat(bootstrap(data,fitted,45)))
    def test_negative_controls(self):
        self.assertEqual(estimate(world(31,years=8))["reason"],"weak_year_identification")
        self.assertEqual(estimate(world(31,cross_family=True))["reason"],"cross_meeting_family")
        self.assertEqual(estimate(world(31,mnar=True))["reason"],"unknown_selection_mechanism")
    def test_corruption_rejected(self):
        data=world(31)
        data[1]["id"]=data[0]["id"]
        self.assertEqual(estimate(data)["reason"],"duplicate_id")
        data=world(31)
        data[0]["representation"]="invalid"
        self.assertEqual(estimate(data)["reason"],"representation_mismatch")
        data=world(31)
        data[0]["count"]=-1
        self.assertEqual(estimate(data)["reason"],"invalid_counts")
    def test_attempts_and_missingness(self):
        a=evaluate(31,"balanced_null","holdout",2,9)
        self.assertEqual(summary(a)["attempted"],2)
        b=evaluate(31,"eight_years","holdout",2,9,years=8)
        self.assertEqual(summary(b)["withheld"],2)
        self.assertIsNone(summary(b)["unconditional_rate"])
        self.assertEqual(summary(b)["reference_attempted"],0)
    def test_wilson(self):
        self.assertIsNone(wilson(0,0))
        self.assertLess(wilson(0,50)[1],.1)
    def test_smoke_denominators(self):
        x=smoke(worlds=1,references=9)
        self.assertEqual(len(x["scenarios"]),7)
        self.assertFalse(x["scientific_ready"])
        self.assertEqual(x["scenarios"]["cross_family"]["holdout"]["summary"]["withheld"],1)

if __name__=="__main__": unittest.main()
