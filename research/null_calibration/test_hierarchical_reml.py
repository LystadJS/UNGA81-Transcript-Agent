import unittest
import math
from study import world
from hierarchical_reml import fit, design, objective

class HierarchicalREMLTests(unittest.TestCase):
    def test_objective_and_replay(self):
        rows=world(31,years=24,per_year=4)
        d=design(rows)
        self.assertTrue(d['ready'])
        self.assertTrue(math.isfinite(objective(d,.55,[math.log(.02),math.log(.02)])))
        a=fit(rows,grid_points=9)
        self.assertEqual(a,fit(rows,grid_points=9))
        self.assertEqual(a['grid_attempted'],9)
        self.assertEqual(a['grid_attempted'],a['grid_converged']+a['grid_failed'])
        if a['ready']:
            self.assertLessEqual(a['ci'][0],a['rho'])
            self.assertGreaterEqual(a['ci'][1],a['rho'])
    def test_guards(self):
        self.assertEqual(fit(world(31,years=8))['reason'],'insufficient_or_gapped_years')
        self.assertEqual(fit(world(31,years=24,cross_family=True))['reason'],'cross_meeting_family')
        self.assertEqual(fit(world(31,years=24,mnar=True))['reason'],'source_or_selection_invalid')
        self.assertEqual(fit(world(31,years=24,per_year=1))['reason'],'one_meeting_per_year')
    def test_grid_contract(self):
        with self.assertRaises(ValueError):fit(world(31,years=24),grid_points=4)

if __name__=='__main__': unittest.main()
