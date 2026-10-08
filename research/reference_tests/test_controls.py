"""Synthetic-only tests for nuisance control, named-entity masking and dry-run guards."""
from __future__ import annotations
import copy, hashlib, json, tempfile, unittest
from pathlib import Path
import numpy as np
from negative_controls import fixed_code, make_nuisance_vectors
from mask_sensitivity import (aliases, matcher, mask_text, masked_rows, frozen_semantic,
                              centroid_assign, frozen_lexical)
from holdout_dryrun import fixture, check_fixture, evaluate_fixture, verify_frozen_lock
from reference import HERE, read, verify_seal


class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock=verify_frozen_lock()

    def test_lock_stays_unmodified_and_reserved(self):
        self.assertEqual(self.lock['reserved_meetings'],37)
        self.assertEqual(self.lock['holdout_state'],'reserved_not_downloaded')
        self.assertFalse(self.lock['evaluation_executed'])
        self.assertEqual(self.lock['predeclared_eligibility_gates']['min_crossmeeting_neighbors'],15)

    def test_codebook_determinism(self):
        self.assertTrue(np.array_equal(fixed_code('role:A',64,8),fixed_code('role:A',64,8)))
        self.assertFalse(np.array_equal(fixed_code('role:A',64,8),fixed_code('role:B',64,8)))

    def test_no_content_used_in_nuisance_vectors(self):
        meta=[{'role':'delegate','genre':'GA','length_bin':1,'meeting_id':'m','country':'A','text':'topic X'}]
        a=make_nuisance_vectors(meta,64,77)
        meta[0]['text']='completely opposing stance with no overlap'
        self.assertTrue(np.array_equal(a,make_nuisance_vectors(meta,64,77)))
        self.assertFalse(np.array_equal(a,make_nuisance_vectors(meta,64,77,True)))

    def test_alias_policy_omits_iso_codes_and_common_ambiguous_names(self):
        names=aliases([{'iso3':'USA','country':'United States of America','aliases':['USA','United States','U.S.']},
                       {'iso3':'GEO','country':'Georgia','aliases':['GEO','Georgia']},
                       {'iso3':'CUB','country':'Cuba','aliases':['CUB','Cuba']}])
        self.assertIn('United States',names)
        self.assertIn('Cuba',names)
        self.assertNotIn('GEO',names)
        self.assertNotIn('Georgia',names)
        self.assertNotIn('CUB',names)

    def test_unicode_and_word_boundaries(self):
        regex=matcher(['Cuba','Côte d’Ivoire','United States'])
        text='Cubana Cuba Côte d’Ivoire United States Cuban.'
        changed,spans=mask_text(text,regex)
        self.assertEqual(len(spans),3)
        self.assertIn('Cubana',changed)
        self.assertIn('Cuban',changed)
        self.assertEqual(changed.count('nation'),3)
        self.assertEqual(text[spans[0]['start']:spans[0]['end']],'Cuba')

    def test_mask_does_not_alter_original(self):
        src='The delegation of Cuba met another.'
        row={'split':'development','human_confirmed':False,'text':src,
             'text_sha256':hashlib.sha256(src.encode()).hexdigest(),
             'id':'dev-a','parent_id':'dev-parent','meeting_id':'m'}
        before=copy.deepcopy(row)
        masked,audit=masked_rows([row],matcher(['Cuba']))
        self.assertEqual(before,row)
        self.assertEqual(masked[0]['original_text_sha256'],row['text_sha256'])
        self.assertEqual(masked[0]['id'],row['id'])
        self.assertIn('nation',masked[0]['text'])
        self.assertEqual(audit[0]['matches'],1)

    def test_mask_rejects_future_or_tampered_record(self):
        row={'split':'holdout','human_confirmed':False,'text':'Cuba','text_sha256':hashlib.sha256(b'Cuba').hexdigest(),
             'id':'reserved','parent_id':'parent','meeting_id':'m'}
        with self.assertRaises(ValueError):masked_rows([row],matcher(['Cuba']))
        row['split']='development';row['human_confirmed']=True
        with self.assertRaises(ValueError):masked_rows([row],matcher(['Cuba']))
        row['human_confirmed']=False;row['text_sha256']='f'*64
        with self.assertRaises(ValueError):masked_rows([row],matcher(['Cuba']))

    def test_frozen_lexical_uses_saved_idf(self):
        rows=[{'text':'cuba protects rights'}, {'text':'rights and obligations'}]
        saved={'terms':np.array(['cuba','rights','protects','obligations']),
               'idf':np.array([2.,1.,3.,4.]),'svd_components':np.eye(4)}
        out=frozen_lexical(rows,saved,{'ngram_range':[1,1],'stop_words':[],'strip_accents':'unicode'})
        self.assertEqual(out.shape,(2,4));self.assertTrue(np.isfinite(out).all())
        self.assertGreater(out[0,2],out[0,0])

    def test_frozen_semantic_and_centroid_assignment(self):
        mean=np.zeros(384);pcs=np.eye(384)[:64]
        data=np.zeros((3,384));data[0,0]=1;data[1,1]=1;data[2,0]=-1
        z=frozen_semantic(data,{'pca_mean':mean,'pca_components':pcs})
        self.assertEqual(z.shape,(3,64))
        self.assertEqual(centroid_assign(z,z[:2]).tolist(),[0,1,1])

    def test_normal_synthetic_fixture_accounts_for_all_meetings(self):
        f=fixture();check_fixture(f,self.lock)
        self.assertEqual(len(f['meetings']),37)
        self.assertTrue(all(m['meeting_id'].startswith('SYNTHETIC-') for m in f['meetings']))
        self.assertNotIn('text',f['parents'][0])

    def test_dry_run_has_valid_positive_and_negative_synthetic_branches(self):
        for variant in ['nominal','correlated']:
            r=evaluate_fixture(fixture(variant=variant),self.lock)
            self.assertTrue(r['decision'].startswith('SYNTHETIC_GATE_'))
            self.assertEqual(r['reserved_transcripts_opened'],0)
            self.assertEqual(r['all_meetings'],37)
            self.assertFalse(r['actual_replication_claim'])
            self.assertIsNotNone(r['secondary'])
        r=evaluate_fixture(fixture(variant='correlated'),self.lock)
        self.assertEqual(r['decision'],'SYNTHETIC_GATE_WOULD_PASS')

    def test_insufficient_and_unavailable_are_inconclusive(self):
        for variant in ['insufficient','all_unavailable']:
            r=evaluate_fixture(fixture(variant=variant),self.lock)
            self.assertEqual(r['decision'],'INCONCLUSIVE_SYNTHETIC')
            self.assertTrue(r['withheld_reasons'])
            self.assertEqual(sum(r['source_status_counts'].values()),37)

    def test_rejects_any_real_identifiers_or_transcript_fields(self):
        for change in ['url','identity','date','split','source','duplicate','count']:
            f=fixture();
            if change=='url':f['transcript_url']='https://transcripts.un.org/en/ga/81/1'
            elif change=='identity':f['meetings'][0]['meeting_id']='ga/81/1'
            elif change=='date':f['meetings'][0]['date']='2026-10-05'
            elif change=='split':f['parents'][0]['split']='holdout'
            elif change=='source':f['parents'][0]['source_kind']='transcript'
            elif change=='duplicate':f['parents'][1]['parent_id']=f['parents'][0]['parent_id']
            elif change=='count':f['meetings'].pop()
            with self.subTest(change=change),self.assertRaises(ValueError):check_fixture(f,self.lock)

    def test_bad_lock_and_tampered_pvalue_draws_rejected(self):
        f=fixture()
        with self.assertRaises(ValueError):evaluate_fixture(f,self.lock,draws=100)
        bad=copy.deepcopy(self.lock);bad['replication_floor_excess']=0
        with self.assertRaises(ValueError):evaluate_fixture(f,bad)

    def test_input_payload_never_can_supply_false_authorization(self):
        f=fixture();f['authorization']=True
        with self.assertRaises(ValueError):check_fixture(f,self.lock)

if __name__=='__main__':unittest.main()

class AdditionalControls(unittest.TestCase):
    def test_bad_plan_digest_blocks_dryrun(self):
        from reference import digest
        self.assertEqual(verify_frozen_lock()['reference_plan_sha256'],digest((HERE/'plan.json').read_bytes()))

    def test_frozen_smoke_rejects_missing_saved_models(self):
        from holdout_dryrun import exercise_frozen_transforms
        with self.assertRaises(FileNotFoundError):
            exercise_frozen_transforms(fixture(),verify_frozen_lock(),Path('/nonexistent_dev'),Path('/nonexistent_sem'))

    def test_mask_alias_spans_original_unicode(self):
        rgx=matcher(['Côte d’Ivoire','U.S.','Cuba'])
        text="The Côte d’Ivoire delegate from Cuba discussed U.S. relations."
        masked,spans=mask_text(text,rgx)
        self.assertEqual(len(spans),3)
        self.assertEqual([text[p['start']:p['end']] for p in spans],[p['matched_alias'] for p in spans])
        self.assertNotIn('Cuba',masked)

    def test_frozen_mask_rejects_invalid_geometry(self):
        with self.assertRaises(ValueError):frozen_semantic(np.zeros((3,384)),{'pca_mean':np.zeros(384),'pca_components':np.zeros((64,384))})

    def test_min_crossmeeting_neighbor_is_not_silently_relaxed(self):
        from holdout_dryrun import evaluate_fixture
        f=fixture(variant='all_unavailable')
        r=evaluate_fixture(f,verify_frozen_lock())
        self.assertIsNone(r['primary']);self.assertEqual(r['all_meetings'],37)
