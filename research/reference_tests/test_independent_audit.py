"""Data-free tests for independent read-only audit's scoring functions."""
import unittest
import numpy as np
from independent_audit import knn, shared, category_match, expected_category

class AuditMetricTests(unittest.TestCase):
    def test_shared_order_invariance_and_exact(self):
        a=np.array([[1,2],[2,0],[0,1]])
        b=np.array([[2,1],[0,2],[1,0]])
        self.assertEqual(shared(a,b),1.0)
        c=np.array([[1,3],[2,0],[0,1]])
        self.assertAlmostEqual(shared(a,c),5/6)
    def test_no_same_meeting_neighbors(self):
        x=np.array([[1.,0.],[.9,.1],[0.,1.],[.1,.9]])
        meetings=['A','A','B','B']
        nn=knn(x,meetings,k=2)
        self.assertEqual(nn.shape,(4,2))
        for i,row in enumerate(nn):
            self.assertTrue(all(meetings[j]!=meetings[i] for j in row))
    def test_missing_other_meeting_abstains(self):
        with self.assertRaises(ValueError):knn(np.ones((3,2)),['A','A','A'],1)
    def test_expected_uniform_crossmeeting_baseline(self):
        meetings=['a','a','b','c'];cats=['X','Y','X','Y']
        # query 0: 1/2 match; query1: 1/2; query2: 1/3; query3: 1/3
        self.assertAlmostEqual(expected_category(meetings,cats),5/12)
    def test_category_denominator(self):
        labels=['a','b','a']
        n=np.array([[1,2],[0,2],[0,1]])
        out=category_match(n,labels)
        self.assertEqual(out['pairs'],6)
        self.assertAlmostEqual(out['share'],2/6)
if __name__ == '__main__':unittest.main()
