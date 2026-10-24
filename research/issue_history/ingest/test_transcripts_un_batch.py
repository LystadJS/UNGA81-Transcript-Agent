"""Whole-artifact metadata persistence using invented native-format fixtures."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ..store import IssueStore
from . import test_transcripts_un_audit as fixtures
from . import transcripts_un_batch as B


class ArtifactBatchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.environ.get('SC_ACTION_TEST_ROOT'))
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'history.sqlite';self.store=IssueStore(self.path)
        self.addCleanup(lambda:self.store.close())
        self.doc,self.receipt,self.frame=fixtures.fixture()

    def persist(self,doc=None):
        raw=json.dumps(self.doc if doc is None else doc,ensure_ascii=False).encode()
        receipt={**self.receipt,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        return B.persist_artifact(self.store,raw,receipt,self.frame)

    def current(self):
        return B.get_current_batch(self.store,self.frame['meeting_id'],self.receipt['source_url'])

    def snapshot(self):
        return {name:[tuple(r) for r in self.store.db.execute('SELECT * FROM '+name+' ORDER BY 1,2')]
                for name in ('sources','source_revisions','artifacts','dependencies','evidence')}

    def revise(self,count):
        doc=copy.deepcopy(self.doc);seed=doc['transcript']['data'][0]
        doc['metadata']['synthetic_revision']='new-'+str(count)
        doc['transcript']['data']=[{**copy.deepcopy(seed),'statement_number':i+1} for i in range(count)]
        return doc

    def test_complete_batch_manifest_and_current_members_are_exact(self):
        before=copy.deepcopy((self.doc,self.receipt,self.frame));result=self.persist()
        self.assertEqual(result,self.current());self.assertEqual(2,result['member_count'])
        self.assertEqual(2,len(result['members']))
        self.assertEqual(2,len({m['source_id'] for m in result['members']}))
        self.assertEqual(3,self.store.db.execute('SELECT count(*) FROM sources').fetchone()[0])
        self.assertTrue(self.store.artifact_valid(result['batch_artifact_id']))
        self.assertTrue(all(self.store.artifact_valid(m['provenance_artifact_id']) for m in result['members']))
        self.assertEqual(before,(self.doc,self.receipt,self.frame))

    def test_repeated_whole_artifact_is_idempotent(self):
        first=self.persist();before=self.snapshot()
        self.assertEqual(first,self.persist());self.assertEqual(before,self.snapshot())

    def test_current_batch_survives_database_close_and_reopen(self):
        first=self.persist();self.store.close();self.store=IssueStore(self.path)
        self.assertEqual(first,self.current())

    def test_second_child_failure_rolls_back_entire_new_batch(self):
        before=self.snapshot();upsert=self.store.upsert_source;children=0
        def fail_second(source):
            nonlocal children
            if source.get('family')=='un_transcript_segment':
                children+=1
                if children==2:raise RuntimeError('Synthetic second-child persistence failure')
            return upsert(source)
        with patch.object(self.store,'upsert_source',side_effect=fail_second):
            with self.assertRaises(RuntimeError):self.persist()
        self.assertEqual(2,children);self.assertEqual(before,self.snapshot())

    def test_malformed_last_native_record_rejected_before_any_database_write(self):
        doc=copy.deepcopy(self.doc);doc['transcript']['data'][-1]['paragraphs'][0]['sentences'][0]['text']=None
        before=self.snapshot()
        with self.assertRaises(ValueError):self.persist(doc)
        self.assertEqual(before,self.snapshot())

    def test_changed_artifact_adds_and_omits_current_members_without_deleting_old_metadata(self):
        first=self.persist();first_members={m['source_id'] for m in first['members']}
        second=self.persist(self.revise(3));second_members={m['source_id'] for m in second['members']}
        self.assertEqual(3,second['member_count']);self.assertTrue(first_members.isdisjoint(second_members))
        self.assertFalse(self.store.artifact_valid(first['batch_artifact_id']))
        self.assertTrue(all(not self.store.artifact_valid(m['provenance_artifact_id']) for m in first['members']))
        third=self.persist(self.revise(1));self.assertEqual(1,third['member_count'])
        self.assertEqual(third,self.current());self.assertFalse(self.store.artifact_valid(second['batch_artifact_id']))
        for source_id in first_members|second_members:
            self.assertIsNotNone(self.store.db.execute('SELECT id FROM sources WHERE id=?',(source_id,)).fetchone())
        self.assertNotEqual(first['parent_source_revision'],third['parent_source_revision'])

    def test_historical_parent_replay_rejected_without_reverting_current_members(self):
        self.persist();current=self.persist(self.revise(3));before=self.snapshot()
        with self.assertRaises(ValueError):self.persist()
        self.assertEqual(before,self.snapshot());self.assertEqual(current,self.current())

    def test_current_child_revision_tampering_fails_closed(self):
        result=self.persist();member=result['members'][0]
        self.store.db.execute('UPDATE sources SET revision=? WHERE id=?',('0'*64,member['source_id']));self.store.db.commit()
        with self.assertRaises(ValueError):self.current()

    def test_invalidated_current_child_provenance_fails_closed(self):
        result=self.persist();member=result['members'][0]
        self.store.db.execute('UPDATE artifacts SET valid=0 WHERE id=?',(member['provenance_artifact_id'],));self.store.db.commit()
        with self.assertRaises(ValueError):self.current()

    def test_tampered_manifest_payload_cannot_change_member_count(self):
        result=self.persist();identity=result['batch_artifact_id']
        payload=json.loads(self.store.db.execute('SELECT payload FROM artifacts WHERE id=?',(identity,)).fetchone()[0])
        payload['member_count']=999
        self.store.db.execute('UPDATE artifacts SET payload=? WHERE id=?',(json.dumps(payload),identity));self.store.db.commit()
        with self.assertRaises(ValueError):self.current()

    def test_missing_manifest_dependency_fails_closed(self):
        result=self.persist();identity=result['batch_artifact_id']
        self.store.db.execute('DELETE FROM dependencies WHERE artifact_id=? AND dependency_id=?',
                              (identity,result['members'][0]['provenance_artifact_id']));self.store.db.commit()
        with self.assertRaises(ValueError):self.current()

    def test_only_private_unknown_capacity_metadata_persists_no_wording_or_opinions(self):
        result=self.persist();encoded=json.dumps(self.snapshot())
        self.assertNotIn('Synthetic first.',encoded);self.assertNotIn('Invented second turn.',encoded)
        sources=[json.loads(r[0]) for r in self.store.db.execute('SELECT payload FROM source_revisions')]
        self.assertTrue(all(s['access']=='private' and s.get('countries',[])==[] for s in sources))
        self.assertEqual(0,self.store.db.execute('SELECT count(*) FROM evidence').fetchone()[0])
        self.assertFalse(result['comparisons_eligible']);self.assertFalse(result['production_intake_accepted'])
        manifest=self.store.export_bundle(Path(self.temp.name)/'public','synthetic-batch-private')
        self.assertEqual(0,manifest['counts']['sources']);self.assertEqual(0,manifest['counts']['observations'])

    def test_empty_segments_are_retained_with_explicit_gap(self):
        doc=copy.deepcopy(self.doc);doc['transcript']['data'][0]['paragraphs']=[]
        result=self.persist(doc)
        self.assertEqual(2,result['member_count'])
        self.assertTrue(any(g['reason']=='empty_segment' for g in result['gaps']))

    def test_empty_whole_artifact_remains_explicit_not_complete_meeting_evidence(self):
        doc=copy.deepcopy(self.doc);doc['transcript']['data']=[]
        result=self.persist(doc)
        self.assertEqual(0,result['member_count']);self.assertEqual([],result['members'])
        self.assertTrue(any(g['reason']=='empty_artifact' for g in result['gaps']))
        self.assertEqual(result,self.current())
        self.assertIn('not_server_meeting_or_archive',result['completeness_scope'])

    def test_two_valid_manifests_for_current_parent_are_ambiguous_and_rejected(self):
        result=self.persist()
        payload=json.loads(self.store.db.execute('SELECT payload FROM artifacts WHERE id=?',(result['batch_artifact_id'],)).fetchone()[0])
        payload['synthetic_ambiguity']='second purported current manifest'
        deps=[r[0] for r in self.store.db.execute('SELECT dependency_id FROM dependencies WHERE artifact_id=?',(result['batch_artifact_id'],))]
        self.store.put_artifact(B.KIND,payload,deps)
        with self.assertRaises(ValueError):self.current()

    def test_current_method_pin_change_rejects_prior_batch_until_explicit_revalidation(self):
        original=self.persist();before=self.snapshot()
        changed={**B._methods(),'transcripts_un_batch.py':'0'*64}
        with patch.object(B,'_methods',return_value=changed):
            with self.assertRaises(ValueError):self.current()
        self.assertEqual(before,self.snapshot())
        self.assertEqual(original,self.current())


if __name__=='__main__':unittest.main()
