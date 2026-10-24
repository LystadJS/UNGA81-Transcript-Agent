"""Source-free private-cache acceptance; no original ledgers or network access."""
import copy
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from . import sc_action_cache as cache
from ..store import IssueStore
from ..ingest.test_sc_crosswalk import fixture
from ..ingest.un_sc_csv import HEADERS


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ActionCacheTests(unittest.TestCase):
    def setUp(self):
        # A private cache must not live inside the checked-out repository.
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get('SC_ACTION_TEST_ROOT'))
        self.base = Path(self.temp.name)
        self.collection, self.votes = fixture()
        self.collection_file = self.base / 'collection.json'
        self.raw = self.base / 'sc-synthetic.csv'
        self.database = self.base / 'history.sqlite'
        self.root = self.base / 'private-cache'
        event = self.collection['events'][0]
        with self.raw.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=HEADERS)
            writer.writeheader()
            for v in event['votes']:
                row = dict.fromkeys(HEADERS, '')
                row.update(undl_id='999999999', ms_code=v['country_code'], ms_name=v['country'].upper(), permanent_member='False', ms_vote='Y', date=event['date'], resolution='S/RES/9999(2024)', draft=event['draft'], meeting=event['meeting_record'], total_yes='15', total_no='0', total_abstentions='0', total_non_voting='0', total_ms='15', modality='Vote', undl_link='https://digitallibrary.un.org/record/999999999')
                writer.writerow(row)
        self.raw_hash = sha(self.raw)
        store = IssueStore(self.database)
        try:
            for row in self.votes:
                source = {'id':row['source_id'], 'published_date':row['date'], 'body':'SC', 'family':'un_recorded_vote', 'url':'https://digitallibrary.un.org/record/999999999', 'content_hash':'b'*64, 'access':'private', 'countries':[row['country']], 'download_sha256':self.raw_hash}
                revision = store.upsert_source(source)
                store.put_vote({**row, 'source_revision':revision, 'policy':'unbound', 'context':row['resolution'], 'resolution_version':'as_adopted'})
        finally:
            store.close()
        self.write_collection()
        self.options = {'collection_file':self.collection_file, 'ddl_database':self.database, 'cache_dir':self.root, 'ddl_raw_csv':self.raw, 'expected_ddl_source_sha256':self.raw_hash}
        self.original_hashes = {str(p):sha(p) for p in (self.collection_file,self.database,self.raw)}

    def tearDown(self):
        self.temp.cleanup()

    def write_collection(self):
        self.collection_file.write_text(json.dumps(self.collection), encoding='utf-8')

    def call(self, **changes):
        return cache.cached_crosswalk(**{**self.options, **changes})

    def state(self):
        return {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def install_review(self):
        event = self.collection['events'][0]
        correct = event['draft']
        event['draft'] = 'S/2024/9998'
        self.write_collection()
        proof = self.base / 'proof.json'
        url = 'https://docs.un.org/en/S/PV.9999'
        anchor = 'Invented fixture page 2; not a real primary review.'
        receipt = {'schema':'un.sc-primary-facts.v1', 'source_url':url, 'hash_scope':'tool_extracted_primary_metadata', 'facts':{'resolution':'S/RES/9999(2024)', 'date':event['date'], 'draft':correct, 'meeting_record':event['meeting_record']}, 'anchor':anchor, 'retrieval_note':'Synthetic engineering fixture only.'}
        proof.write_text(json.dumps(receipt), encoding='utf-8')
        review_file = self.base / 'review.json'
        review = {'schema':'un.sc-primary-review.v1', 'version':'sc-primary-review-2', 'input_pins':{'collection_sha256':sha(self.collection_file), 'ddl_database_sha256':sha(self.database), 'ddl_original_source_sha256':self.raw_hash}, 'corrections':[{'target':'dppa', 'event':{'resolution':'S/RES/9999(2024)', 'date':event['date'], 'dppa_event_id':event['id']}, 'field':'draft', 'before':event['draft'], 'after':correct, 'source':{'url':url, 'sha256':sha(proof), 'evidence_file':'proof.json', 'hash_scope':'tool_extracted_primary_metadata', 'anchor':anchor}, 'review_state':'assistant_provisional'}]}
        review_file.write_text(json.dumps(review), encoding='utf-8')
        self.options['review_file'] = review_file
        return review_file, proof

    def test_cold_then_warm_reuses_without_builder(self):
        with patch.object(cache, 'crosswalk_files', wraps=cache.crosswalk_files) as builder:
            cold = self.call()
            self.assertEqual('built', cold['cache_status'])
            self.assertEqual(1, builder.call_count)
        self.assertEqual(1, cold['report']['event_selection']['summary']['selected_actions'])
        with patch.object(cache, 'crosswalk_files', side_effect=AssertionError('warm path invoked builder')):
            warm = self.call()
        self.assertEqual('hit', warm['cache_status'])
        self.assertEqual(cold['report'], warm['report'])
        self.assertEqual(cold['artifact_path'], warm['artifact_path'])
        self.assertTrue(all(sha(p)==s for p,s in self.original_hashes.items()))

    def test_collection_bytes_change_selects_new_identity(self):
        old = self.call()
        self.collection['synthetic_note'] = 'new metadata revision'
        self.write_collection()
        with patch.object(cache, 'crosswalk_files', wraps=cache.crosswalk_files) as builder:
            new = self.call()
        self.assertEqual(1, builder.call_count)
        self.assertNotEqual(old['cache_key'], new['cache_key'])
        self.assertTrue(Path(old['artifact_path']).exists())

    def test_database_bytes_change_cannot_reuse_old_result(self):
        old = self.call()
        db = sqlite3.connect(self.database)
        db.execute('CREATE TABLE synthetic_revision(note TEXT)')
        db.commit(); db.close()
        new = self.call()
        self.assertNotEqual(old['cache_key'], new['cache_key'])

    def test_dependency_bytes_change_invalidates(self):
        dependency = self.base / 'synthetic-dependency.txt'
        dependency.write_text('version one', encoding='utf-8')
        mapping = {**cache._dependency_paths(), 'synthetic_dependency':dependency}
        with patch.object(cache, '_dependency_paths', return_value=mapping):
            old = self.call()
            dependency.write_text('version two', encoding='utf-8')
            with patch.object(cache, 'crosswalk_files', wraps=cache.crosswalk_files) as builder:
                new = self.call()
            self.assertEqual(1, builder.call_count)
        self.assertNotEqual(old['cache_key'], new['cache_key'])

    def test_raw_source_pin_mismatch_rejects_before_warm_reuse(self):
        self.call(); before = self.state()
        self.raw.write_bytes(self.raw.read_bytes()+b'\n')
        with patch.object(cache, 'crosswalk_files', side_effect=AssertionError('bad source entered builder')):
            with self.assertRaisesRegex(ValueError, 'source identity'):
                self.call()
        self.assertEqual(before, self.state())

    def test_primary_proof_change_with_updated_envelope_invalidates(self):
        review_file, proof = self.install_review()
        old = self.call()
        receipt = json.loads(proof.read_bytes()); receipt['retrieval_note'] += ' Additional source custody note.'
        proof.write_text(json.dumps(receipt), encoding='utf-8')
        review = json.loads(review_file.read_bytes()); review['corrections'][0]['source']['sha256'] = sha(proof)
        review_file.write_text(json.dumps(review), encoding='utf-8')
        new = self.call()
        self.assertNotEqual(old['cache_key'], new['cache_key'])
        self.assertEqual(old['report']['summary'], new['report']['summary'])

    def test_changed_proof_without_receipt_update_rejects_preserving_cache(self):
        _, proof = self.install_review(); self.call(); before = self.state()
        proof.write_bytes(proof.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError, 'receipt changed'):
            self.call()
        self.assertEqual(before, self.state())

    def test_review_envelope_change_invalidates_even_if_result_counts_same(self):
        review, _ = self.install_review(); old = self.call()
        value = json.loads(review.read_bytes()); value['limits'] = ['Synthetic review note added.']
        review.write_text(json.dumps(value), encoding='utf-8'); new = self.call()
        self.assertNotEqual(old['cache_key'], new['cache_key'])

    def test_corrupt_truncated_and_future_version_entries_rebuild(self):
        for kind in ('truncated','tampered_report','future_version'):
            with self.subTest(kind=kind):
                result = self.call()
                artifact = Path(result['artifact_path'])
                if kind == 'truncated': artifact.write_bytes(b'{')
                else:
                    value = json.loads(artifact.read_bytes())
                    if kind == 'tampered_report': value['report']['event_selection']['summary']['selected_actions'] = 999
                    else: value['version'] = 'unknown-future-version'
                    artifact.write_text(json.dumps(value), encoding='utf-8')
                    if kind == 'future_version':
                        index = self.root/(result['cache_key']+'.index.json')
                        pointer = json.loads(index.read_bytes()); pointer['entry_sha256'] = sha(artifact)
                        index.write_bytes(cache._bytes(pointer))
                corrupt = artifact.read_bytes()
                with patch.object(cache, 'crosswalk_files', wraps=cache.crosswalk_files) as builder:
                    rebuilt = self.call()
                self.assertEqual('rebuilt_corrupt', rebuilt['cache_status'])
                self.assertEqual(1, builder.call_count)
                self.assertEqual(1, rebuilt['report']['event_selection']['summary']['selected_actions'])
                self.assertEqual(corrupt, artifact.read_bytes(), 'corrupt immutable generation is retained for diagnosis')

    def test_corrupt_index_is_not_trusted(self):
        old = self.call(); index = self.root/(old['cache_key']+'.index.json')
        index.write_bytes(b'not json')
        rebuilt = self.call()
        self.assertEqual('rebuilt_corrupt', rebuilt['cache_status'])
        self.assertEqual(old['report'], rebuilt['report'])

    def test_failed_forced_refresh_preserves_valid_pointer_and_generation(self):
        old = self.call(); before = self.state()
        with patch.object(cache, 'crosswalk_files', side_effect=RuntimeError('interrupted synthetic refresh')):
            with self.assertRaisesRegex(RuntimeError, 'interrupted'):
                self.call(force_refresh=True)
        self.assertEqual(before, self.state())
        self.assertEqual(old['artifact_path'], self.call()['artifact_path'])

    def test_wrong_builder_provenance_cannot_replace_valid_generation(self):
        old = self.call(); before = self.state()
        wrong = copy.deepcopy(old['report'])
        wrong['input_provenance']['collection_sha256'] = '0'*64
        with patch.object(cache, 'crosswalk_files', return_value=wrong):
            with self.assertRaises(ValueError): self.call(force_refresh=True)
        self.assertEqual(before, self.state())
        self.assertEqual('hit', self.call()['cache_status'])

    def test_self_consistently_rehashed_wrong_source_entry_is_rebuilt(self):
        old = self.call(); artifact = Path(old['artifact_path'])
        index = self.root/(old['cache_key']+'.index.json')
        envelope = json.loads(artifact.read_bytes())
        envelope['report']['input_provenance']['collection_sha256'] = '0'*64
        envelope['report_sha256'] = hashlib.sha256(cache._bytes(envelope['report'])).hexdigest()
        artifact.write_bytes(cache._bytes(envelope))
        pointer = json.loads(index.read_bytes()); pointer['entry_sha256'] = sha(artifact)
        index.write_bytes(cache._bytes(pointer))
        with patch.object(cache, 'crosswalk_files', wraps=cache.crosswalk_files) as builder:
            rebuilt = self.call()
        self.assertEqual(1, builder.call_count)
        self.assertEqual('rebuilt_corrupt', rebuilt['cache_status'])
        self.assertEqual(old['report'], rebuilt['report'])

    def test_input_change_during_entry_write_preserves_previous_pointer(self):
        old = self.call(); index = self.root/(old['cache_key']+'.index.json')
        old_index = index.read_bytes(); old_entry = Path(old['artifact_path']).read_bytes()
        original = self.collection_file.read_bytes(); atomic = cache._atomic
        def mutate_after_entry(path, content):
            atomic(path, content)
            if Path(path).name.startswith(old['cache_key']+'.') and not str(path).endswith('.index.json'):
                self.collection_file.write_bytes(original+b'\n')
        with patch.object(cache, '_atomic', side_effect=mutate_after_entry):
            with self.assertRaisesRegex(ValueError, 'before index publication'):
                self.call(force_refresh=True)
        self.assertEqual(old_index, index.read_bytes())
        self.assertEqual(old_entry, Path(old['artifact_path']).read_bytes())
        self.collection_file.write_bytes(original)
        with patch.object(cache, 'crosswalk_files', side_effect=AssertionError('Restored identity must hit')):
            self.assertEqual('hit', self.call()['cache_status'])

    def test_forced_refresh_keeps_old_generation_and_deterministic_result(self):
        old = self.call(); old_bytes = Path(old['artifact_path']).read_bytes()
        new = self.call(force_refresh=True)
        self.assertEqual('refreshed', new['cache_status'])
        self.assertEqual(old['cache_key'], new['cache_key'])
        self.assertNotEqual(old['artifact_path'], new['artifact_path'])
        self.assertEqual(old['report'], new['report'])
        self.assertEqual(old_bytes, Path(old['artifact_path']).read_bytes())

    def test_interrupted_atomic_index_publish_preserves_old_hit(self):
        old = self.call(); index = self.root/(old['cache_key']+'.index.json'); old_index = index.read_bytes(); old_entry = Path(old['artifact_path']).read_bytes()
        replace = os.replace
        def interrupted(source, target):
            if Path(target) == index: raise OSError('synthetic index publication failure')
            return replace(source, target)
        with patch.object(cache.os, 'replace', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'publication failure'):
                self.call(force_refresh=True)
        self.assertEqual(old_index, index.read_bytes()); self.assertEqual(old_entry, Path(old['artifact_path']).read_bytes())
        self.assertEqual('hit', self.call()['cache_status'])
        self.assertFalse(list(self.root.glob('.cache-*')))

    def test_low_space_blocks_writes_but_existing_hit_remains_readable(self):
        self.call(); before = self.state()
        usage = shutil._ntuple_diskusage(total=1000, used=999, free=1)
        with patch.object(cache.shutil, 'disk_usage', return_value=usage):
            self.assertEqual('hit', self.call()['cache_status'])
            with self.assertRaisesRegex(OSError, 'free space'):
                self.call(force_refresh=True)
        self.assertEqual(before, self.state())
        with self.assertRaises(ValueError): self.call(min_free_bytes=1)

    def test_unsafe_root_containing_inputs_and_unowned_directory_rejected(self):
        with self.assertRaises(ValueError): self.call(cache_dir=self.base)
        self.root.mkdir(); unrelated = self.root/'unrelated.txt'; unrelated.write_bytes(b'preserve')
        with self.assertRaises(ValueError): self.call()
        self.assertEqual(b'preserve', unrelated.read_bytes())

    def test_index_hardlink_to_original_is_rejected_without_source_change(self):
        old = self.call(); index = self.root/(old['cache_key']+'.index.json'); index.unlink()
        try: os.link(self.collection_file, index)
        except OSError as error: self.skipTest('Hard links unavailable: '+str(error))
        original = self.collection_file.read_bytes()
        with self.assertRaises(ValueError): self.call()
        self.assertEqual(original, self.collection_file.read_bytes())

    def test_repository_cache_and_sqlite_sidecars_rejected(self):
        with self.assertRaisesRegex(ValueError, 'repository'): self.call(cache_dir=Path.cwd()/'synthetic-cache-forbidden')
        old = self.call(); before = self.state()
        for suffix in ('-wal','-journal','-shm'):
            sidecar = Path(str(self.database)+suffix); sidecar.write_bytes(b'pending synthetic writer')
            try:
                with patch.object(cache, 'crosswalk_files', side_effect=AssertionError('nonquiescent ledger reached builder')):
                    with self.assertRaisesRegex(ValueError, 'sidecar'): self.call()
            finally: sidecar.unlink()
        self.assertEqual(before, self.state()); self.assertEqual(old['artifact_path'], self.call()['artifact_path'])


if __name__ == '__main__':
    unittest.main()
