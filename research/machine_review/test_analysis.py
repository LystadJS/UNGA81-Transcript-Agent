"""Numerical smoke tests use synthetic development records only."""
import copy, unittest, tempfile
from pathlib import Path
import numpy as np
from sklearn.decomposition import NMF
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits
from analysis import PLAN, fit, shares, weights, select_rows, vectorizer, save_arrays


def rows():
    topics=['climate energy carbon renewable emissions warming adaptation ocean finance resilience',
            'justice courts judiciary victims crime police criminal law accountability investigation',
            'education schools youth teachers learning literacy students classroom skills university',
            'health hospital medicine disease treatment vaccine healthcare patients epidemic prevention']
    result=[]
    for i in range(80):
        words=topics[i%4].split();words+=['access','cooperation','public','resources']
        text=' '.join(words+words[:(i%7)+2])
        result.append({'id':f'r{i}','text':text,'parent_id':f'p{i//2}','meeting_id':f'm{i//10}',
                       'split':'development','strict_eligible':True,'inclusive_eligible':True,'baseline_eligible':True})
    return result


class NumericalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=rows();cls.spec={'id':'synthetic','population':'strict','dimensions':8,'k':4,'method':'kmeans'}
        with threadpool_limits(limits=1):cls.fit=fit(cls.rows,cls.spec,PLAN)
    def test_all_observations(self):self.assertEqual(len(self.fit['rows']),80)
    def test_normalized(self):np.testing.assert_allclose(np.linalg.norm(self.fit['Z'],axis=1),1)
    def test_four_groups(self):self.assertEqual(len(set(self.fit['labels'])),4)
    def test_repeatability(self):
        with threadpool_limits(limits=1):other=fit(self.rows,self.spec,PLAN)
        np.testing.assert_array_equal(other['labels'],self.fit['labels'])
        np.testing.assert_allclose(other['raw'],self.fit['raw'])
    def test_meeting_weight_total(self):self.assertAlmostEqual(weights(self.rows,'equal_meeting').sum(),1)
    def test_parent_weight_total(self):self.assertAlmostEqual(weights(self.rows,'equal_observed_parent').sum(),1)
    def test_parent_equal(self):
        w=weights(self.rows,'equal_observed_parent');self.assertAlmostEqual(w[:2].sum(),1/40)
    def test_composition_mass(self):
        out=shares(self.fit)
        for mode in PLAN['summary_weights']:self.assertAlmostEqual(sum(r['share'] for r in out if r['weighting']==mode),1)
    def test_missing_fit_mass(self):
        f=dict(self.fit);f['rows']=f['rows'][:-1];f['labels']=f['labels'][:-1]
        out=shares(f);mass=next(r['share'] for r in out if r['weighting']=='equal_passage' and r['cluster']=='not_fitted')
        self.assertAlmostEqual(mass,1/80)
    def test_no_sampling_on_overflow(self):
        p=copy.deepcopy(PLAN);p['max_observations']=79
        with self.assertRaises(ValueError):fit(self.rows,self.spec,p)
    def test_no_rank_substitution(self):
        s={**self.spec,'dimensions':500}
        with self.assertRaises(ValueError):fit(self.rows,s,PLAN)
    def test_unknown_population(self):
        with self.assertRaises(ValueError):select_rows(self.rows,'holdout')
    def test_negation_retained(self):self.assertTrue(all(x not in PLAN['vectorizer']['stop_words'] for x in ['no','not','nor','never']))
    def test_nmf_component_scale(self):
        with threadpool_limits(limits=1):
            m=NMF(n_components=4,init='nndsvda',random_state=1,max_iter=600);W=m.fit_transform(self.fit['X']);H=m.components_
        scale=np.array([2.,3.,4.,5.]);a=W*H.sum(axis=1);b=(W/scale)*(H*scale[:,None]).sum(axis=1)
        np.testing.assert_allclose(a,b)
    def test_numeric_archive_without_pickle(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fit.npz'
            save_arrays(p, terms=self.fit['v'].get_feature_names_out(), geometry=self.fit['Z'])
            with np.load(p, allow_pickle=False) as stored:
                np.testing.assert_array_equal(stored['terms'],self.fit['v'].get_feature_names_out())
                np.testing.assert_array_equal(stored['geometry'],self.fit['Z'])
                self.assertTrue(all(not stored[k].dtype.hasobject for k in stored.files))
    def test_reject_object_archive(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                save_arrays(Path(d)/'unsafe.npz', unsafe=np.array([{'do':'not deserialize'}],dtype=object))
    def test_holdout_fit_rejected(self):
        rs=copy.deepcopy(self.rows);rs[0]['split']='holdout'
        with self.assertRaises(ValueError):fit(rs,self.spec,PLAN)
    def test_ari_relabeling(self):self.assertAlmostEqual(adjusted_rand_score(self.fit['labels'],self.fit['labels']+10),1)

if __name__=='__main__':unittest.main(verbosity=2)
