"""Synthetic-only integration acceptance; no real transcript URL is queried."""
import copy, json, subprocess, sys, tempfile, unittest
from pathlib import Path
import numpy as np
from production_synthetic import run, validate_artificial_corpus, machine_populations, source_status, HERE
from nuisance_stress import conditional_knn, share_categories, SENSITIVITY_ONLY
from holdout_dryrun import verify_frozen_lock


class SyntheticProductionAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.source=Path(cls.tmp.name)/'synthetic'
        subprocess.run(['node',str(HERE/'synthetic_un_fixture.cjs'),str(cls.source)],check=True,capture_output=True,text=True)
        cls.corpus=json.loads((cls.source/'corpus.json').read_text())
        cls.report=run(None,None,None)

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_exact_37_fake_meetings(self):
        self.assertEqual(len(self.corpus['coverage']),37)
        self.assertEqual(self.report['source_coverage']['all_meetings'],37)
        self.assertEqual(self.corpus['counts']['reserved_meetings'],1) # fake frame sentinel, never actual holdout

    def test_synthetic_only_date_and_names(self):
        validate_artificial_corpus(self.corpus)
        for m in self.corpus['coverage']:
            self.assertRegex(m['meeting_id'],r'^synthetic_fixture_/meeting_\d\d$')
            self.assertEqual(m['date'],'2099-01-05')

    def test_download_unavailable_failed_accounted(self):
        c=self.report['source_coverage']['statuses']
        self.assertEqual(c,{'collected':34,'inventory_unavailable':2,'failed':1})

    def test_raw_response_hash_binding(self):
        from hashlib import sha256
        for row in self.corpus['source_bundle']['sources']:
            if row['status']=='downloaded':
                from base64 import b64decode
                self.assertEqual(sha256(b64decode(row['raw_base64'])).hexdigest(),row['raw_sha256'])

    def test_transcript_text_codepoints_exhaustive(self):
        self.assertTrue(self.report['source_coverage']['all_observed_partitions_accounted'])
        self.assertEqual(self.report['source_parents'],442)
        self.assertEqual(self.report['source_passages'],412)

    def test_machine_role_review_without_human_labels(self):
        rows,annotations=machine_populations(self.corpus)
        strict=[r for r in rows if r['strict_eligible']]
        self.assertEqual(len(strict),220)
        self.assertEqual(len({r['parent_id'] for r in strict}),216)
        self.assertEqual(len({r['meeting_id'] for r in strict}),27)
        self.assertEqual(len(annotations),442)
        self.assertFalse(any(a['human_confirmed'] for a in annotations))

    def test_transcript_flags_and_missing_attribution_not_zero(self):
        c=self.report['source_coverage']
        self.assertGreater(c['non_english_source_parents'],0)
        self.assertGreater(c['timestamp_flagged_source_parents'],0)
        self.assertGreater(c['unknown_country_source_parents'],0)

    def test_real_date_rejected(self):
        c=copy.deepcopy(self.corpus)
        c['coverage'][0]['date']='2026-10-05'
        with self.assertRaisesRegex(ValueError,'Non-synthetic'):validate_artificial_corpus(c)

    def test_nonfake_id_rejected(self):
        c=copy.deepcopy(self.corpus)
        c['parents'][0]['id']='hrc/99/11#0'
        with self.assertRaisesRegex(ValueError,'Real or human-reviewed'):validate_artificial_corpus(c)

    def test_human_confirmation_rejected(self):
        c=copy.deepcopy(self.corpus)
        c['parents'][0]['speech_id']='fabricated-confirmation'
        with self.assertRaisesRegex(ValueError,'Real or human-reviewed'):validate_artificial_corpus(c)

    def test_nonfake_source_url_rejected(self):
        c=copy.deepcopy(self.corpus)
        c['parents'][0]['source_url']='https://transcripts.un.org/en/hrc/63/25'
        with self.assertRaisesRegex(ValueError,'Unsafe source'):validate_artificial_corpus(c)

    def test_partial_status_roster_rejected(self):
        c=copy.deepcopy(self.corpus)
        c['coverage']=c['coverage'][:-1]
        with self.assertRaisesRegex(ValueError,'Exactly 37'):validate_artificial_corpus(c)

    def test_frozen_lock_verified_without_holdout_open(self):
        lock=verify_frozen_lock()
        self.assertEqual(lock['reserved_meetings'],37)
        self.assertFalse(lock['evaluation_executed'])
        self.assertEqual(self.report['reserved_meetings_opened'],0)

    def test_no_semantic_claim_without_encoder(self):
        self.assertEqual(self.report['full_frozen_inference'],'NOT_RUN_REQUIRES_PINNED_LOCAL_MODEL_AND_SAVED_DEVELOPMENT_ARRAYS')
        self.assertNotIn('inference',self.report)

    def test_genre_source_missingness_preserved(self):
        c=self.report['source_coverage']
        self.assertGreater(c['genres'].get('Press Conferences',0),0)
        self.assertGreater(c['genres'].get('Security Council',0),0)
        self.assertEqual(c['source_failure_count'],1)

    def test_all_artificial_dates_fail_if_swapped(self):
        c=copy.deepcopy(self.corpus)
        c['frame']['plan']['development_dates']=['2026-10-05']
        with self.assertRaisesRegex(ValueError,'Real dates'):validate_artificial_corpus(c)


class NuisanceControlTests(unittest.TestCase):
    def test_genre_and_role_exclusion(self):
        meta=[{'meeting_id':'a','genre':'g1','role':'r1'},{'meeting_id':'b','genre':'g1','role':'r2'},
              {'meeting_id':'c','genre':'g2','role':'r1'},{'meeting_id':'d','genre':'g2','role':'r2'}]
        V=np.eye(4)
        q,n,p=conditional_knn(V,meta,('genre','role'),k=1)
        self.assertEqual(q.tolist(),[0,1,2,3]);self.assertEqual(n[:,0].tolist(),[3,2,1,0])

    def test_inadequate_retrieval_is_withheld(self):
        meta=[{'meeting_id':'a','genre':'g1','role':'x'}, {'meeting_id':'b','genre':'g1','role':'x'},
              {'meeting_id':'c','genre':'g2','role':'x'}]
        q,n,_=conditional_knn(np.eye(3),meta,('role',),k=1)
        self.assertEqual(len(q),0)

    def test_alias_ambiguity_policy(self):
        self.assertEqual(SENSITIVITY_ONLY,{'island','thai'})

    def test_category_rate_does_not_invent_zero(self):
        self.assertIsNone(share_categories(np.array([],dtype=int),np.empty((0,1),dtype=int),[], 'genre'))


if __name__=='__main__':unittest.main()
