import unittest
from temporal_ar1 import estimate_ar1, resample_ar1
from study import world, digest

class TemporalAR1Tests(unittest.TestCase):
    def test_estimation_never_accepts_oracle(self):
        a = world(31, years=24, per_year=4)
        fitted = estimate_ar1(a)
        self.assertTrue(fitted['ready'], fitted)
        self.assertIn('rho', fitted)
        self.assertNotIn('truth', fitted)
        b = resample_ar1(a, fitted, 43)
        self.assertEqual(digest(b), digest(resample_ar1(a, fitted, 43)))
        self.assertNotEqual(digest(a), digest(b))
    def test_cross_family_refusal(self):
        self.assertEqual(estimate_ar1(world(31, years=24, cross_family=True))['reason'], 'cross_meeting_family')
    def test_short_year_refusal(self):
        self.assertEqual(estimate_ar1(world(31, years=8))['reason'], 'insufficient_or_gapped_years')
    def test_selection_refusal(self):
        self.assertEqual(estimate_ar1(world(31, years=24, mnar=True))['reason'], 'source_or_selection_invalid')
    def test_duplicate_refusal(self):
        a=world(31,years=24)
        a[1]['id']=a[0]['id']
        self.assertEqual(estimate_ar1(a)['reason'], 'empty_or_duplicate_ids')
    def test_one_meeting_per_year(self):
        self.assertEqual(estimate_ar1(world(31,years=24,per_year=1))['reason'], 'one_meeting_per_year')

if __name__=='__main__': unittest.main()
