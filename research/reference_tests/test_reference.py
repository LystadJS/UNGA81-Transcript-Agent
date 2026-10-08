"""Data-free synthetic checks for source-group nuisance references and immutable holdout lock."""
from __future__ import annotations
import copy, tempfile, unittest
from pathlib import Path
import numpy as np
from reference import (HERE, agreement, blocks, calculate, coverage, country_population,
                       empirical_p, freeze, holm, parents, permuted_neighbor_agreement,
                       read, same_country, seal, shuffle_within, validate_plan, verify_seal)


class ReferenceChecks(unittest.TestCase):
    def setUp(self):
        self.plan=read(HERE/'plan.json')
        self.future=read(HERE/'evaluation_plan.json')

    def test_committed_metadata_only_lock_and_development_aggregate(self):
        import hashlib,json
        from reference import canonical,digest
        lock=read(HERE/'evaluation-lock.json')
        verify_seal(lock,'un.heldout-evaluation-lock.v1')
        record=read(HERE/'development-reference.json')
        verify_seal(record,'un.development-reference-results.v1')
        self.assertEqual(lock['reference_aggregate_sha256'],digest(canonical({k:v for k,v in record.items() if k!='sha256'})))
        self.assertEqual(lock['reference_implementation_sha256'],digest((HERE/'reference.py').read_bytes()))
        self.assertEqual(lock['reference_plan_sha256'],digest((HERE/'plan.json').read_bytes()))
        self.assertEqual(lock['evaluation_plan_sha256'],digest((HERE/'evaluation_plan.json').read_bytes()))
        self.assertEqual(lock['reserved_meetings'],37)
        self.assertFalse(lock['evaluation_executed'])
        self.assertNotIn('raw_base64',json.dumps(lock))
        self.assertNotIn('"text"',json.dumps(record))

    def test_plan_lock_and_separation(self):
        validate_plan(self.plan,self.future)
        for field,value in [('permutations',100),('holdout_access',True),('neighbors',2),('holdout_meetings',36)]:
            with self.subTest(field=field),self.assertRaises(ValueError):
                candidate=copy.deepcopy(self.plan);candidate[field]=value
                validate_plan(candidate,self.future)
        changed=copy.deepcopy(self.future);changed['state']='running_on_holdout'
        with self.assertRaises(ValueError):validate_plan(self.plan,changed)

    def test_aggregation_integrity_and_weighting(self):
        rows=[{'id':'p1','parent_id':'p','meeting_id':'m','country':'A','machine_actor_role':'country_delegation',
               'genre':'GA','tokens':1,'split':'development','human_confirmed':False,'text_sha256':'f'},
              {'id':'p2','parent_id':'p','meeting_id':'m','country':'A','machine_actor_role':'country_delegation',
               'genre':'GA','tokens':3,'split':'development','human_confirmed':False,'text_sha256':'g'},
              {'id':'q1','parent_id':'q','meeting_id':'n','country':'B','machine_actor_role':'country_delegation',
               'genre':'GA','tokens':4,'split':'development','human_confirmed':False,'text_sha256':'h'}]
        xyz=np.array([[1.,0.],[0.,1.],[1.,1.]])
        meta,L,S=parents(rows,xyz,xyz,[2,4])
        self.assertEqual([r['count'] for r in meta],[2,1])
        np.testing.assert_allclose(L[0],np.array([1.,3.])/np.sqrt(10))
        np.testing.assert_array_equal(L,S)
        wrong=copy.deepcopy(rows);wrong[1]['meeting_id']='other'
        with self.assertRaises(ValueError):parents(wrong,xyz,xyz,[2,4])
        wrong=copy.deepcopy(rows);wrong[1]['split']='holdout'
        with self.assertRaises(ValueError):parents(wrong,xyz,xyz,[2,4])

    def test_permutation_respects_conditional_blocks(self):
        meta=[{'meeting_id':m,'length_bin':b,'role': 'a' if i%2 else 'b'}
              for m in ['m1','m2'] for b in [0,1,2] for i in range(4)]
        groups=blocks(meta,('meeting_id','length_bin'))
        self.assertEqual(len(groups),6)
        self.assertEqual(coverage(groups,len(meta))['movable_fraction'],1)
        perm=shuffle_within(groups,len(meta),np.random.default_rng(5))
        self.assertEqual(sorted(perm.tolist()),list(range(len(meta))))
        for i,j in enumerate(perm):
            self.assertEqual((meta[i]['meeting_id'],meta[i]['length_bin']),
                             (meta[j]['meeting_id'],meta[j]['length_bin']))
        self.assertEqual(coverage(blocks(meta,('meeting_id','length_bin','role')),len(meta))['movable'],24)

    def test_fast_reference_matches_independent_refitted_similarity_order(self):
        rng=np.random.default_rng(84)
        meta=[{'meeting_id':f'm{i//12}','length_bin':i%3,'role':'delegate'} for i in range(48)]
        from reference import crossmeeting_knn, normalized
        a=normalized(rng.normal(size=(48,16)))
        b=normalized(rng.normal(size=(48,16)))
        lex=crossmeeting_knn(a,meta,5)
        sem=crossmeeting_knn(b,meta,5)
        perm=shuffle_within(blocks(meta,('meeting_id','length_bin')),48,rng)
        accelerated=permuted_neighbor_agreement(lex,sem,perm)
        recomputed=agreement(lex,crossmeeting_knn(b[perm],meta,5))
        self.assertAlmostEqual(accelerated,recomputed,places=13)

    def test_country_selection_needs_repeated_source_meetings(self):
        meta=[{'meeting_id':'m','country':'A'}, {'meeting_id':'n','country':'A'},
              {'meeting_id':'m','country':'B'}, {'meeting_id':'m','country':None}]
        indices,rows,countries=country_population(meta)
        self.assertEqual(indices,[0,1]);self.assertEqual(countries,1)
        self.assertEqual([r['country'] for r in rows],['A','A'])

    def test_neighbor_relabel_mapping_and_exact_scores(self):
        left=np.array([[1,2],[0,2],[0,1]])
        right=np.array([[2,1],[2,0],[1,0]])
        self.assertEqual(agreement(left,left),1)
        self.assertEqual(agreement(left,right),1)
        self.assertEqual(permuted_neighbor_agreement(left,left,np.arange(3)),1)
        self.assertEqual(same_country(left,np.array(['A','A','B'])),2/6)
        self.assertAlmostEqual(empirical_p(0.8,np.array([0.6,0.8,0.3])),.5)
        self.assertEqual(holm([.01,.03,.5]),[.03,.06,.5])

    def test_frozen_lock_uses_only_heldout_metadata(self):
        records=[{'meeting_id':f'ga/id/{i}','date':'2026-10-05' if i<20 else '2026-10-06','split':'holdout'} for i in range(37)]
        frame={'sha256':'frame','holdout_state':'reserved_not_downloaded','meetings':records}
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'final-analysis').mkdir();(root/'strict_semantic_pca64_k10.npz').write_bytes(b'sem')
            (root/'strict_semantic_raw384_k10.npz').write_bytes(b'raw')
            (root/'final-analysis/strict_lsa64_k10.npz').write_bytes(b'lex')
            reference={'primary':{'excess_above_reference_mean':.4}}
            lock=freeze(frame,root,root,reference,self.plan,self.future)
            verify_seal(lock,'un.heldout-evaluation-lock.v1')
            self.assertEqual(lock['replication_floor_excess'],.2)
            self.assertTrue(lock['no_holdout_acquisition_performed'])
            self.assertFalse(lock['evaluation_executed'])
            altered=copy.deepcopy(lock);altered['reserved_meetings']=36
            with self.assertRaises(ValueError):verify_seal(altered,'un.heldout-evaluation-lock.v1')
            frame['meetings'][0]['split']='development'
            with self.assertRaises(ValueError):freeze(frame,root,root,reference,self.plan,self.future)

    def test_positive_cross_meeting_structure_fixture(self):
        rng=np.random.default_rng(6)
        n=144;dims=24;k=10
        themes=np.tile(np.arange(12),12)
        centers=rng.normal(size=(12,dims))
        meta=[{'meeting_id':f'm{i//24}','length_bin':i%3,'country':f'c{themes[i]}','role':'country_delegation','count':1} for i in range(n)]
        lexical=centers[themes]+rng.normal(0,.1,(n,dims))
        semantic=centers[themes]+rng.normal(0,.1,(n,dims))
        from reference import crossmeeting_knn, normalized
        a=crossmeeting_knn(normalized(lexical),meta,k)
        b=crossmeeting_knn(normalized(semantic),meta,k)
        observed=agreement(a,b)
        groups=blocks(meta,('meeting_id','length_bin'))
        draws=[permuted_neighbor_agreement(a,b,shuffle_within(groups,n,rng)) for _ in range(99)]
        self.assertGreater(observed,np.percentile(draws,95))
        self.assertLessEqual(empirical_p(observed,np.asarray(draws)),.05)

    def test_network_block_is_active_during_development(self):
        import socket
        from encoder import offline
        with offline() as attempts:
            with self.assertRaises(RuntimeError):
                socket.create_connection(('localhost',80),timeout=0.001)
        self.assertEqual(attempts,['blocked network connection'])

    def test_eligible_group_gates_fail_closed(self):
        tiny=[{'meeting_id':f'm{i%2}','length_bin':0,'role':'x','country':None,'count':1} for i in range(30)]
        data=np.tile([1.,0.,0.],(30,1))
        with self.assertRaisesRegex(ValueError,'Not enough distinct'):calculate(tiny,data,data,self.plan)


if __name__ == '__main__':unittest.main(verbosity=2)
