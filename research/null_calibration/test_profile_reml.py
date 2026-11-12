import math
import unittest
from study import world
from profile_reml import profile_reml

class REMLTests(unittest.TestCase):
    def test_reproducible_and_finite(self):
        rows=world(31,years=24,per_year=4)
        a=profile_reml(rows)
        b=profile_reml(rows)
        self.assertEqual(a,b)
        self.assertIn('ready',a)
        self.assertGreater(a['evaluations'],0)
        if a['ready']:
            self.assertTrue(math.isfinite(a['rho']))
            self.assertLess(abs(a['rho']),.85)
            self.assertLessEqual(a['ci'][0],a['rho'])
            self.assertGreaterEqual(a['ci'][1],a['rho'])
    def test_weak_year_fail_closed(self):
        self.assertEqual(profile_reml(world(31,years=8))['reason'],'insufficient_or_gapped_years')
    def test_family_crossing_fail_closed(self):
        self.assertEqual(profile_reml(world(31,years=24,cross_family=True))['reason'],'cross_meeting_family')
    def test_mnar_fail_closed(self):
        self.assertEqual(profile_reml(world(31,years=24,mnar=True))['reason'],'source_or_selection_invalid')
    def test_one_meeting_per_year_fail_closed(self):
        self.assertEqual(profile_reml(world(31,years=24,per_year=1))['reason'],'one_meeting_per_year')

if __name__=='__main__':unittest.main()
