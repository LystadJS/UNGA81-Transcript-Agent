"""Synthetic statement identity bridge checks; never reads an original transcript."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ..store import IssueStore
from .discovery import transcript_inventory
from . import statement_identity as S


def sha(value):
    return hashlib.sha256(value).hexdigest()


def fixture(native='synthetic-speech-1'):
    slug='sc/9999';day='2024-01-01'
    raw=json.dumps({'page':1,'total':1,'hasMore':False,'meetings':[{
        'slug':slug,'date':day+'T00:00:00.000Z','body':'Security Council','category':'Synthetic catalog',
        'hasTranscript':True,'pageUrl':'/en/'+slug,'jsonUrl':'/en/'+slug+'.json','textUrl':'/en/'+slug+'.txt'}]}).encode()
    inventory=transcript_inventory(raw,day);meeting=inventory['meetings'][0]
    text='Invented engineering fixture: We call for humanitarian access in Sudan.'
    receipt={'schema':'un.statement-artifact-receipt.v1','meeting_id':slug,'date':day,'body':'SC',
        'inventory_metadata_sha256':inventory['metadata_sha256'],'source_url':meeting['jsonUrl'],
        'retrieved':True,'hash_verified':True,'extraction_complete':True,'expected_sha256':'a'*64,
        'source_sha256':'a'*64,'normalized_sha256':'b'*64,'extraction_method_version':'synthetic-normalizer-1'}
    return {'schema':'un.normalized-statement.v1','parent_meeting':meeting,
        'inventory_metadata_sha256':inventory['metadata_sha256'],'artifact_receipt':receipt,
        'native_statement_id':native,'identity_scheme_version':'artifact-local-native-statement-1',
        'language':'en','text':text,'text_sha256':sha(text.encode()),'source_role':'product_development',
        'speaker':{'name':'Invented speaker','capacity':'national','recorded_affiliation':'Nigeria',
                   'country':'Nigeria','group':None}}


class StatementIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.environ.get('SC_ACTION_TEST_ROOT'))
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.store=IssueStore(self.root/'history.sqlite')
        self.addCleanup(self.store.close)
        self.row=fixture()

    def persist(self,row=None):
        return S.persist_statement(self.store,self.row if row is None else row)

    def current_sources(self):
        return [json.loads(r[0]) for r in self.store.db.execute('SELECT r.payload FROM sources s JOIN source_revisions r ON s.id=r.id AND s.revision=r.revision ORDER BY s.id')]

    def table_counts(self):
        return {name:self.store.db.execute('SELECT count(*) FROM '+name).fetchone()[0]
                for name in ('sources','source_revisions','artifacts','dependencies','evidence')}

    def test_two_native_speakers_share_meeting_without_overwriting_statement_sources(self):
        one=self.persist();two=self.persist(fixture('synthetic-speech-2'))
        self.assertNotEqual(one['source_id'],two['source_id'])
        self.assertEqual(one['parent_source_id'],two['parent_source_id'])
        self.assertEqual(3,self.table_counts()['sources'])
        self.assertTrue(self.store.artifact_valid(one['provenance_artifact_id']))
        self.assertTrue(self.store.artifact_valid(two['provenance_artifact_id']))

    def test_repeated_row_is_idempotent_and_does_not_mutate_inputs(self):
        before=copy.deepcopy(self.row);one=self.persist();counts=self.table_counts()
        self.assertEqual(one,self.persist());self.assertEqual(counts,self.table_counts())
        self.assertEqual(before,self.row)

    def test_revised_artifact_keeps_native_identity_changes_revision_and_invalidates_dependencies(self):
        one=self.persist();downstream=self.store.put_artifact('synthetic-report',{'version':'fixture-1'},[one['provenance_artifact_id']])
        revised=copy.deepcopy(self.row);revised['text']+=' Additional invented source wording.'
        revised['text_sha256']=sha(revised['text'].encode())
        revised['artifact_receipt'].update(source_sha256='c'*64,expected_sha256='c'*64,normalized_sha256='d'*64)
        two=self.persist(revised)
        self.assertEqual(one['source_id'],two['source_id']);self.assertEqual(one['parent_source_id'],two['parent_source_id'])
        self.assertNotEqual(one['source_revision'],two['source_revision'])
        self.assertNotEqual(one['parent_source_revision'],two['parent_source_revision'])
        self.assertFalse(self.store.artifact_valid(one['provenance_artifact_id']))
        self.assertFalse(self.store.artifact_valid(downstream))
        self.assertTrue(self.store.artifact_valid(two['provenance_artifact_id']))

    def test_collective_affiliation_never_creates_national_roster_or_observation(self):
        row=copy.deepcopy(self.row);row['speaker'].update(capacity='collective',country=None,group='Invented regional group')
        self.persist(row)
        self.assertTrue(all(s.get('countries',[])==[] for s in self.current_sources()))
        self.assertEqual(0,self.table_counts()['evidence'])

    def test_unknown_affiliation_never_creates_national_roster(self):
        row=copy.deepcopy(self.row);row['speaker'].update(name=None,capacity='unknown',country=None,group=None)
        self.persist(row)
        self.assertTrue(all(s.get('countries',[])==[] for s in self.current_sources()))

    def test_bridge_creates_only_private_metadata_without_raw_wording(self):
        result=self.persist();sources=self.current_sources()
        self.assertTrue(all(s['access']=='private' for s in sources))
        self.assertNotIn(self.row['text'],json.dumps(result));self.assertNotIn(self.row['text'],json.dumps(sources))
        artifact=self.store.db.execute('SELECT payload FROM artifacts WHERE id=?',(result['provenance_artifact_id'],)).fetchone()[0]
        self.assertNotIn(self.row['text'],artifact)
        manifest=self.store.export_bundle(self.root/'public','synthetic-private-bridge')
        self.assertEqual(0,manifest['counts']['sources']);self.assertEqual(0,manifest['counts']['observations'])

    def test_forged_caller_source_id_and_empty_native_keys_rejected(self):
        for field,value in [('source_id','forged-meeting-level-source'),('native_statement_id',''),
                            ('identity_scheme_version','unsupported')]:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.persist({**self.row,field:value})
        self.assertEqual(0,self.table_counts()['sources'])

    def test_parent_meeting_identity_date_body_and_url_must_match_receipt(self):
        for field,value in [('meeting_id','sc/9998'),('date','2024-01-02'),('body','GA'),
                            ('jsonUrl','https://transcripts.un.org/en/sc/9998.json')]:
            row=copy.deepcopy(self.row);row['parent_meeting'][field]=value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.persist(row)

    def test_receipt_hash_and_extraction_linkage_must_be_complete(self):
        for field,value in [('source_sha256','c'*64),('normalized_sha256',None),
                            ('inventory_metadata_sha256','c'*64),('hash_verified',False),
                            ('extraction_complete',False),('extraction_method_version',None),
                            ('source_url','https://example.com/fixture.json')]:
            row=copy.deepcopy(self.row);row['artifact_receipt'][field]=value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.persist(row)

    def test_text_hash_mismatch_rejected_before_any_write(self):
        row={**self.row,'text':self.row['text']+' unpinned change'}
        with self.assertRaises(ValueError):self.persist(row)
        self.assertEqual(0,self.table_counts()['sources'])

    def test_national_identity_requires_explicit_country_not_affiliation_guess(self):
        for speaker in ({**self.row['speaker'],'country':None},
                        {**self.row['speaker'],'country':'Invented unknown nation'},
                        {**self.row['speaker'],'capacity':'collective','group':'Group'},
                        {**self.row['speaker'],'capacity':'unknown'}):
            with self.subTest(speaker=speaker):
                with self.assertRaises(ValueError):self.persist({**self.row,'speaker':speaker})

    def test_no_caller_observations_or_public_approval_are_accepted(self):
        for field,value in [('observations',[{'attribution':'national'}]),('access','public_approved')]:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.persist({**self.row,field:value})

    def test_transaction_failure_rolls_back_sources_and_prior_artifact_invalidation(self):
        one=self.persist();before=self.table_counts()
        row=copy.deepcopy(self.row);row['artifact_receipt'].update(expected_sha256='c'*64,source_sha256='c'*64)
        with patch.object(self.store,'put_artifact',side_effect=RuntimeError('Synthetic provenance persistence failure')):
            with self.assertRaises(RuntimeError):self.persist(row)
        self.assertEqual(before,self.table_counts())
        self.assertTrue(self.store.artifact_valid(one['provenance_artifact_id']))
        current=self.store.db.execute('SELECT revision FROM sources WHERE id=?',(one['source_id'],)).fetchone()[0]
        self.assertEqual(one['source_revision'],current)

    def test_protected_roles_and_reserved_dates_are_rejected(self):
        for role in ('audit','evaluation','restricted_research',None):
            with self.subTest(role=role):
                with self.assertRaises(ValueError):self.persist({**self.row,'source_role':role})
        for date in ('2026-10-05','2026-10-06'):
            row=copy.deepcopy(self.row);row['parent_meeting']['date']=date;row['artifact_receipt']['date']=date
            with self.subTest(date=date):
                with self.assertRaises(ValueError):self.persist(row)

    def test_existing_adapter_and_store_files_are_never_rewritten(self):
        paths=[Path(__file__).with_name('adapters.py'),Path(__file__).parents[1]/'store'/'repository.py']
        before={str(p):sha(p.read_bytes()) for p in paths};self.persist()
        self.assertEqual(before,{str(p):sha(p.read_bytes()) for p in paths})

    def test_parent_revision_invalidates_other_speaker_provenance_without_rewriting_it(self):
        self.persist();other=self.persist(fixture('synthetic-speech-2'))
        revised=copy.deepcopy(self.row)
        revised['artifact_receipt'].update(source_sha256='c'*64,expected_sha256='c'*64,normalized_sha256='d'*64)
        self.persist(revised)
        revision=self.store.db.execute('SELECT revision FROM sources WHERE id=?',(other['source_id'],)).fetchone()[0]
        self.assertEqual(other['source_revision'],revision)
        self.assertFalse(self.store.artifact_valid(other['provenance_artifact_id']))

    def test_normalized_metadata_excludes_wording_and_declares_nonproduction_scope(self):
        normalized=S.normalize_statement(self.row)
        self.assertNotIn(self.row['text'],json.dumps(normalized))
        self.assertTrue(normalized['private_only'])
        self.assertFalse(normalized['production_intake_accepted'])
        self.assertIn('not_independent_source_authentication',normalized['verification_scope'])

    def test_stale_row_replay_cannot_restore_invalid_provenance_or_revert_current_sources(self):
        old=self.persist()
        revised=copy.deepcopy(self.row)
        revised['artifact_receipt'].update(source_sha256='c'*64,expected_sha256='c'*64,normalized_sha256='d'*64)
        new=self.persist(revised)
        current_before=self.current_sources();counts_before=self.table_counts()
        self.assertFalse(self.store.artifact_valid(old['provenance_artifact_id']))
        with self.assertRaises(ValueError):self.persist(self.row)
        self.assertEqual(current_before,self.current_sources())
        self.assertEqual(counts_before,self.table_counts())
        self.assertTrue(self.store.artifact_valid(new['provenance_artifact_id']))
        self.assertFalse(self.store.artifact_valid(old['provenance_artifact_id']))

    def test_new_native_key_cannot_revert_parent_to_known_historical_artifact(self):
        self.persist()
        revised=copy.deepcopy(self.row)
        revised['artifact_receipt'].update(source_sha256='c'*64,expected_sha256='c'*64,normalized_sha256='d'*64)
        current=self.persist(revised)
        stale_new_speaker=fixture('synthetic-new-native-key')
        incoming_id=S.normalize_statement(stale_new_speaker)['source_id']
        sources_before=self.current_sources();counts_before=self.table_counts()
        with self.assertRaises(ValueError):self.persist(stale_new_speaker)
        self.assertEqual(sources_before,self.current_sources())
        self.assertEqual(counts_before,self.table_counts())
        self.assertIsNone(self.store.db.execute('SELECT id FROM sources WHERE id=?',(incoming_id,)).fetchone())
        self.assertTrue(self.store.artifact_valid(current['provenance_artifact_id']))


if __name__=='__main__':unittest.main()
