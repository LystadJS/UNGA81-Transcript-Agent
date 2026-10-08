"""Independent hand and metamorphic oracles for dependency-sensitive retrieval."""
import unittest
import numpy as np
from dependency_controls import neighbors,series,clean,calculate,overlap

def metadata(n=8):
    return [{'parent_id':str(i),'meeting_id':str(i),'series':'a' if i<4 else 'b',
             'speaker_proxy':'x' if i%2 else 'y','formula':()} for i in range(n)]
class DependencyTests(unittest.TestCase):
    def test_known_cosine_neighbors(self):
        v=np.array([[1,0],[.9,.1],[-1,0],[0,1]],float);m=metadata(4)
        a,_=neighbors(v,m,k=1);self.assertEqual(a,{0:[1],1:[0],2:[3],3:[1]})
    def test_unknown_proxy_is_not_same_or_different_person(self):
        m=metadata();m[0]['speaker_proxy']=None
        a,c=neighbors(np.eye(8),m,'different_speaker_proxy',1)
        self.assertNotIn(0,a);self.assertTrue(all(0 not in ns for ns in a.values()));self.assertEqual(c['unknown_control_queries'],1)
    def test_no_same_meeting(self):
        m=metadata();m[1]['meeting_id']='0';a,_=neighbors(np.eye(8),m,k=1);self.assertNotIn(1,a[0])
    def test_series_proxies_not_generic_genre(self):
        self.assertEqual(series('ga/c3/81/5'),'ga:c3');self.assertNotEqual(series('ga/c3/81/5'),series('ga/c4/81/1'))
        self.assertIsNone(series('asset/unidentified'))
    def test_ties_are_row_order_invariant(self):
        m=metadata();v=np.eye(8);a,_=neighbors(v,m,k=2);order=np.arange(8)[::-1]
        b,_=neighbors(v[order],[m[i] for i in order],k=2)
        for i in range(8):self.assertEqual(a[int(order[i])],[int(order[j]) for j in b[i]])
    def test_no_backfill(self):
        a,c=neighbors(np.eye(8),metadata(),'different_series_and_proxy',3)
        self.assertEqual(a,{});self.assertEqual(c['insufficient_queries'],8)
    def test_empty_is_missing_not_zero(self):self.assertIsNone(overlap({}, {}, [],15))
    def test_meeting_cap(self):
        m=metadata(10)
        for i in range(1,7):m[i]['meeting_id']='dominating'
        a,_=neighbors(np.eye(10),m,'cap_two_neighbors_per_meeting',4)
        self.assertLessEqual(sum(m[j]['meeting_id']=='dominating' for j in a[0]),2)
    def test_identical_views_and_common_query_denominator(self):
        out=calculate(metadata(),np.eye(8),np.eye(8),k=1)
        self.assertTrue(all(r['overlap']==1 and r['same_query_baseline']==1 for r in out if r['queries']))
    def test_invalid_and_zero_geometry_fail(self):
        for v in [np.zeros((8,2)),np.full((8,2),np.nan)]:
            with self.assertRaises(ValueError):neighbors(v,metadata())
    def test_duplicate_identity_fails(self):
        m=metadata();m[1]['parent_id']='0'
        with self.assertRaises(ValueError):neighbors(np.eye(8),m)
    def test_uniform_reference_matches_candidate_pool(self):
        _,c=neighbors(np.eye(8),metadata(),k=2)
        self.assertAlmostEqual(c['uniform_overlap_expected'],2/7)
        _,c=neighbors(np.eye(8),metadata(),'different_series',k=2)
        self.assertAlmostEqual(c['uniform_overlap_expected'],.5)
    def test_missing_normalization(self):
        for s in [' Unknown ',None,'N/A','']:self.assertIsNone(clean(s))
if __name__=='__main__':unittest.main()
