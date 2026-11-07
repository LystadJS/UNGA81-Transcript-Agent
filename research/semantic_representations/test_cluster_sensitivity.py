import unittest
from cluster_sensitivity import adjusted_rand, sensitivity

class ClusterSensitivityTests(unittest.TestCase):
    def test_ari_label_permutation(self):
        self.assertAlmostEqual(adjusted_rand({'a':0,'b':0,'c':1,'d':1},{'a':2,'b':2,'c':3,'d':3}),1)
    def test_declared_denominator(self):
        rows=[{'id':str(i),'vector':[float(i),float(i%2)]} for i in range(8)]
        out=sensitivity(rows,rows,2,seeds=(3,5,7))
        self.assertEqual(out['attempted_pairs'],3)
        self.assertEqual(out['assessable_pairs']+out['failed_or_unpaired_pairs'],3)
        self.assertFalse(out['publication_eligible'])
    def test_mismatch_rejected(self):
        rows=[{'id':str(i),'vector':[float(i)]} for i in range(5)]
        with self.assertRaises(ValueError): sensitivity(rows,list(reversed(rows)),2)
    def test_invalid_geometry_rejected(self):
        rows=[{'id':str(i),'vector':[float(i)]} for i in range(5)]
        rows[2]['vector']=[float('nan')]
        with self.assertRaises(ValueError): sensitivity(rows,rows,2)
if __name__ == '__main__': unittest.main()
