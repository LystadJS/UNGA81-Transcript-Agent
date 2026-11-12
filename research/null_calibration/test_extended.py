"""Additional complete-attempt denominator, duplicate-vote, provenance controls."""
import unittest
from calibration import consensus, calibrate


def fake(seed, statistic=.5, **changes):
    entry = dict(seed=seed, statistic=statistic, groups=24, nuisance_converged=True,
                 identifiable=True, generator_hash='generator-v2', estimator_hash='estimator-v2')
    entry.update(changes)
    return entry


class CompleteAttemptTests(unittest.TestCase):
    def test_nested_family_method_configuration_balancing(self):
        ids = ['p', 'q']
        left = {'p': 1, 'q': 1}
        right = {'p': 1, 'q': 2}
        fits = [dict(family='partition', method='kmeans', configuration_id='k2', seed=i,
                     status='converged', labels=left) for i in range(20)]
        fits.append(dict(family='medoid', method='pam', configuration_id='k2', seed=1,
                         status='converged', labels=right))
        result = consensus(fits, ids)
        self.assertAlmostEqual(result['pairs'][0]['coassignment'], .5)
        self.assertEqual(result['pairs'][0]['planned_fit_pairs'], 21)
        self.assertEqual(result['converged_fits'], 21)
        self.assertFalse(result['ready'])

    def test_failed_and_unassigned_remain_planned_opportunities(self):
        ids = ['p', 'q']
        fits = [dict(family='a', status='converged', labels={'p': 1, 'q': 1}),
                dict(family='b', status='converged', labels={'p': 0, 'q': 1}),
                dict(family='c', status='nonconverged')]
        out = consensus(fits, ids)
        p = out['pairs'][0]
        self.assertEqual(p['planned_fit_pairs'], 3)
        self.assertEqual(p['eligible_fit_pairs'], 1)
        self.assertAlmostEqual(p['assignment_coverage'], 1/3)
        self.assertEqual(out['failed_or_unfitted'], 1)

    def test_duplicate_fit_not_extra_vote(self):
        a = dict(family='a', method='kmeans', configuration_id='k2', seed=10,
                 status='converged', labels={'p': 1, 'q': 1})
        res = consensus([a, dict(a)], ['p', 'q'])
        self.assertEqual(res['duplicates_excluded'], 1)
        self.assertEqual(res['unique_planned_fits'], 1)
        self.assertEqual(res['attempted_fits'], 2)
        with self.assertRaises(ValueError):
            consensus([a, dict(a, labels={'p': 1, 'q': 2})], ['p', 'q'])

    def test_null_calibration_guards(self):
        train = [fake(i, i / 100) for i in range(120)]
        hold = [fake(i + 1000, i / 100) for i in range(120)]
        self.assertTrue(calibrate(train, hold)['ready'])
        self.assertFalse(calibrate(train, hold[:99])['ready'])
        self.assertFalse(calibrate(train, [dict(hold[0], estimator_hash='wrong')] + hold[1:])['ready'])
        self.assertFalse(calibrate(train, [dict(hold[0], nuisance_converged=False)] + hold[1:])['ready'])
        self.assertFalse(calibrate(train, [dict(hold[0], identifiable=False)] + hold[1:])['ready'])
        self.assertFalse(calibrate(train, train)['ready'])
        self.assertFalse(calibrate(train, [dict(hold[0], groups=2)] + hold[1:])['ready'])

    def test_invalid_partial_label_not_success(self):
        out = consensus([dict(family='a', status='converged', labels={'p': 1})], ['p', 'q'])
        self.assertEqual(out['failed_or_unfitted'], 1)
        self.assertEqual(out['pairs'][0]['planned_fit_pairs'], 1)
        self.assertIsNone(out['pairs'][0]['coassignment'])


if __name__ == '__main__':
    unittest.main()
