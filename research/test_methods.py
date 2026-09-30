import copy
import json
from pathlib import Path
import unittest
from methods import inventory


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads(Path(__file__).with_name('catalog.json').read_text())

    def test_actual_inventory(self):
        self.assertEqual(inventory(), {'registered':42, 'daily_adapters':12, 'r_research_kernels':27, 'python_research_kernels':2, 'remaining':['M26'], 'publication_change':False})

    def test_wrong_count(self):
        self.catalog['synthetic_kernels'] = 30
        with self.assertRaisesRegex(ValueError, 'count mismatch'): inventory(catalog=self.catalog)

    def test_gate_removed(self):
        self.catalog['methods'][0]['required_gates'].pop()
        with self.assertRaisesRegex(ValueError, 'prerequisites'): inventory(catalog=self.catalog)

    def test_false_completion(self):
        next(m for m in self.catalog['methods'] if m['id']=='M26')['research_kernel']='synthetic_tested'
        with self.assertRaisesRegex(ValueError, 'implementation mismatch'): inventory(catalog=self.catalog)

    def test_publication_promoted(self):
        self.catalog['methods'][0]['publication_eligible'] = True
        with self.assertRaisesRegex(ValueError, 'promotes publication'): inventory(catalog=self.catalog)

    def test_duplicate_id(self):
        self.catalog['methods'].append(copy.deepcopy(self.catalog['methods'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'): inventory(catalog=self.catalog)

    def test_wrong_runner(self):
        next(m for m in self.catalog['methods'] if m['id']=='M16')['runner']='run.R'
        with self.assertRaisesRegex(ValueError, 'runner'): inventory(catalog=self.catalog)


if __name__ == '__main__':
    unittest.main(verbosity=2)
