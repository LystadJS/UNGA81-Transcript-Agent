"""Synthetic integrity/numerical tests. Optional real encoder tests use invented text."""
from __future__ import annotations
import copy, json, os, socket, tempfile, unittest
from pathlib import Path
import numpy as np
from encoder import (LocalEncoder, check_rows, sha, normalized, offline, split_encoding,
                     save_cache, load_cache, verify_model)
from compare import fit_geometry, partition, neighbors, overlap, pair
ROOT=Path(__file__).resolve().parent
LOCK=json.loads((ROOT/'model-lock.json').read_text())


def row(i=0,text='Climate resilience and humanitarian protection.'):
    return {'id':str(i),'text':text,'text_sha256':sha(text.encode()),'split':'development','language':'en',
            'meeting_id':'dev-'+str(i%3),'parent_id':'p-'+str(i),'parent_start':0,'parent_end':len(text)}


class SourceTests(unittest.TestCase):
    def test_valid_rows(self):check_rows([row()])
    def test_empty_population(self):
        with self.assertRaises(ValueError):check_rows([])
    def test_duplicate(self):
        with self.assertRaises(ValueError):check_rows([row(),row()])
    def test_hash(self):
        r=row();r['text']+='changed'
        with self.assertRaises(ValueError):check_rows([r])
    def test_holdout(self):
        r=row();r['split']='holdout'
        with self.assertRaises(ValueError):check_rows([r])
    def test_missing_split(self):
        r=row();del r['split']
        with self.assertRaises(ValueError):check_rows([r])
    def test_nonenglish(self):
        r=row();r['language']='fr'
        with self.assertRaises(ValueError):check_rows([r])
    def test_empty_text(self):
        with self.assertRaises(ValueError):check_rows([row(text=' ')])
    def test_network_block(self):
        with offline() as attempts:
            with self.assertRaises(RuntimeError):socket.create_connection(('example.com',443))
            self.assertEqual(len(attempts),1)
    def test_network_restored(self):
        before=socket.create_connection
        with offline():pass
        self.assertIs(before,socket.create_connection)
    def test_wrong_revision(self):
        lock=copy.deepcopy(LOCK);lock['revision']='main'
        with self.assertRaises(ValueError):verify_model(Path('/nonexistent'),lock)
    def test_tampered_lock(self):
        lock=copy.deepcopy(LOCK);lock['files']['tokenizer.json']['sha256']='0'*64
        with self.assertRaises(ValueError):verify_model(Path('/nonexistent'),lock)


class ChunkTests(unittest.TestCase):
    def test_all_tokens_and_whitespace(self):
        text=' '.join(['a']*510)+' '
        cs=split_encoding(text,list(range(510)),[(2*i,2*i+1) for i in range(510)])
        self.assertEqual([len(c['token_ids']) for c in cs],[254,254,2])
        self.assertEqual([t for c in cs for t in c['token_ids']],list(range(510)))
        self.assertEqual(''.join(text[c['coverage_start']:c['coverage_end']] for c in cs),text)
    def test_unicode(self):
        cs=split_encoding('a 🌍 é',[1,2,3],[(0,1),(2,3),(4,6)],2)
        self.assertEqual(cs[1]['coverage_start'],4)
    def test_exact_boundary(self):
        cs=split_encoding('a'*254,list(range(254)),[(i,i+1) for i in range(254)])
        self.assertEqual(len(cs),1)
    def test_empty_encoding(self):
        with self.assertRaises(ValueError):split_encoding(' ',[],[])
    def test_padding_offsets(self):
        with self.assertRaises(ValueError):split_encoding('a',[1],[(0,0)])
    def test_invalid_limit(self):
        with self.assertRaises(ValueError):split_encoding('a',[1],[(0,1)],300)
    def test_bad_offset_order(self):
        with self.assertRaises(ValueError):split_encoding('ab',[1,2],[(1,2),(0,1)])
    def test_normalize_zero(self):
        with self.assertRaises(ValueError):normalized(np.zeros((2,3)))
    def test_normalize_nan(self):
        with self.assertRaises(ValueError):normalized(np.array([[np.nan,1]]))


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.E=normalized(np.random.default_rng(71).normal(size=(45,20)))
        self.rows=[row(i) for i in range(45)]
    def test_pca_unit_norm(self):
        Z,m=fit_geometry(self.E,8);np.testing.assert_allclose(np.linalg.norm(Z,axis=1),1)
        self.assertEqual(m['components'].shape,(8,20))
    def test_raw(self):
        Z,m=fit_geometry(self.E,None);np.testing.assert_allclose(Z,self.E);self.assertEqual(m,{})
    def test_rank(self):
        with self.assertRaises(ValueError):fit_geometry(self.E,64)
    def test_kmeans_reproducibility(self):
        a,_=partition(self.E,'kmeans',4,7);b,_=partition(self.E,'kmeans',4,7);np.testing.assert_array_equal(a,b)
    def test_ward(self):
        a,_=partition(self.E,'ward',4,7);self.assertEqual(len(np.unique(a)),4)
    def test_unknown_method(self):
        with self.assertRaises(ValueError):partition(self.E,'invented',4,7)
    def test_identical_neighborhood(self):
        n=neighbors(self.E,self.rows,5);np.testing.assert_array_equal(overlap(n,n,5),np.ones(45))
    def test_no_self(self):
        n=neighbors(self.E,self.rows,5);self.assertTrue(all(i not in a for i,a in enumerate(n)))
    def test_meeting_exclusion(self):
        n=neighbors(self.E,self.rows,5,'meeting')
        self.assertTrue(all(self.rows[i]['meeting_id']!=self.rows[j]['meeting_id'] for i,a in enumerate(n) for j in a))
    def test_insufficient_neighbors(self):
        rows=[{**r,'meeting_id':'one'} for r in self.rows]
        with self.assertRaises(ValueError):neighbors(self.E,rows,5,'meeting')
    def test_label_permutation(self):
        a={'rows':self.rows,'labels':np.arange(45)%3};b={'rows':self.rows,'labels':(np.arange(45)%3+1)%3}
        self.assertEqual(pair('a','b',a,b)['ari'],1)
    def test_unpaired_ids(self):
        a={'rows':self.rows,'labels':np.arange(45)%3};b={'rows':self.rows[::-1],'labels':a['labels']}
        self.assertEqual(pair('a','b',a,b)['status'],'withheld')


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'cache';self.rows=[row()]
        self.E=normalized(np.ones((1,384))).astype(np.float32)
        save_cache(self.path,self.rows,self.E,[],{'test':True},LOCK)
    def tearDown(self):self.tmp.cleanup()
    def test_roundtrip(self):
        E,_=load_cache(self.path,self.rows,LOCK);np.testing.assert_array_equal(E,self.E)
    def test_changed_encoder(self):
        path=self.path/'manifest.json';m=json.loads(path.read_text());m['implementation_sha256']='0'*64;path.write_text(json.dumps(m))
        with self.assertRaises(ValueError):load_cache(self.path,self.rows,LOCK)
    def test_wrong_source(self):
        with self.assertRaises(ValueError):load_cache(self.path,[row(text='Other text')],LOCK)
    def test_altered_arrays(self):
        (self.path/'embeddings.npy').write_bytes(b'corrupt')
        with self.assertRaises(ValueError):load_cache(self.path,self.rows,LOCK)
    def test_altered_chunks(self):
        (self.path/'chunks.json').write_text('[]')
        with self.assertRaises(ValueError):load_cache(self.path,self.rows,LOCK)
    def test_wrong_model(self):
        lock=copy.deepcopy(LOCK);lock['revision']='changed'
        with self.assertRaises(ValueError):load_cache(self.path,self.rows,lock)
    def test_no_overwrite(self):
        with self.assertRaises(FileExistsError):save_cache(self.path,self.rows,self.E,[],{},LOCK)


@unittest.skipUnless(os.environ.get('SEMANTIC_MODEL_DIR'),'Pinned model not requested; no implicit download')
class EncoderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.encoder=LocalEncoder(Path(os.environ['SEMANTIC_MODEL_DIR']),LOCK)
    def test_tokenizer_defaults_disabled(self):
        self.assertIsNone(self.encoder.tokenizer.truncation);self.assertIsNone(self.encoder.tokenizer.padding)
    def test_full_token_coverage(self):
        r=row(text='Adaptation finance for climate resilience. '*100)
        with offline():E,ch,a=self.encoder.encode([r])
        self.assertGreater(a['chunks'],1);self.assertEqual(a['truncated_wordpieces'],0)
        self.assertEqual(sum(c['token_end']-c['token_start'] for c in ch),a['wordpieces'])
        self.assertEqual(''.join(r['text'][c['coverage_start']:c['coverage_end']] for c in ch),r['text'])
    def test_repeat_same_batch(self):
        with offline():a,_,_=self.encoder.encode([row()]);b,_,_=self.encoder.encode([row()])
        np.testing.assert_array_equal(a,b)
    def test_batch_padding_invariance(self):
        with offline():a,_,_=self.encoder.encode([row()]);b,_,_=self.encoder.encode([row(),row(1,'Policy '*100)])
        np.testing.assert_allclose(a[0],b[0],atol=1e-6)
    def test_synthetic_tail_changes_embedding(self):
        prefix='The committee considered financing and cooperation. '*80
        with offline():E,_,_=self.encoder.encode([row(0,prefix+'Protect civilians. '*40),row(1,prefix+'Improve nuclear safeguards. '*40)])
        self.assertLess(float(E[0]@E[1]),0.995)
    def test_unknown_unicode_visible(self):
        with offline():E,ch,a=self.encoder.encode([row(text='🌍 Peace — coopération é.')])
        self.assertEqual(E.shape,(1,384));self.assertGreater(a['wordpieces'],0)
    def test_never_encode_holdout(self):
        r=row();r['split']='holdout'
        with self.assertRaises(ValueError):self.encoder.encode([r])


if __name__=='__main__':
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):unittest.main(verbosity=2)
