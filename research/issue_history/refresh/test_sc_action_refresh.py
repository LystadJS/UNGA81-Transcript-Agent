"""Synthetic private refresh acceptance; no network or original source writes."""
import json
import os
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
from . import test_sc_action_cache as fixtures
from . import sc_action_cache as cache
from . import sc_action_refresh as refresh


class ActionRefreshTests(unittest.TestCase):
    def setUp(self):
        # Module qualification avoids collecting the fixture's own TestCase twice.
        self.fixture = fixtures.ActionCacheTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.state_dir = self.fixture.base/'private-refresh'
        self.options = {**self.fixture.options, 'state_dir':self.state_dir,
                        'source_watermark':'2024-01-02'}

    def call(self, **changes):
        return refresh.refresh_selected_actions(**{**self.options, **changes})

    def files(self, base):
        return {str(p.relative_to(base)):p.read_bytes() for p in base.rglob('*') if p.is_file()}

    def test_cold_acceptance_then_warm_checkpoint_reuse_without_builder(self):
        with patch.object(cache, 'crosswalk_files', wraps=cache.crosswalk_files) as builder:
            cold = self.call()
        self.assertEqual(1, builder.call_count)
        self.assertEqual('accepted', cold['status'])
        self.assertEqual('built', cold['cache_status'])
        before = self.files(self.state_dir)
        with patch.object(cache, 'crosswalk_files', side_effect=AssertionError('warm refresh invoked builder')):
            warm = self.call()
        self.assertEqual('unchanged', warm['status'])
        self.assertEqual('hit', warm['cache_status'])
        self.assertEqual(cold['checkpoint'], warm['checkpoint'])
        # Health may change, accepted checkpoint generations must not.
        for name, content in before.items():
            if 'health' not in name:
                self.assertEqual(content, (self.state_dir/name).read_bytes())
        self.assertTrue(all(fixtures.sha(p)==s for p,s in self.fixture.original_hashes.items()))

    def test_valid_input_revision_advances_checkpoint_preserving_old_cache(self):
        cold = self.call(); old_cache = self.fixture.state()
        self.fixture.collection['synthetic_note'] = 'new source revision metadata'
        self.fixture.write_collection()
        new = self.call(source_watermark='2024-01-03')
        self.assertEqual('accepted', new['status'])
        self.assertNotEqual(cold['checkpoint'], new['checkpoint'])
        for name, content in old_cache.items():
            self.assertEqual(content, (self.fixture.root/name).read_bytes())

    def test_updated_primary_proof_advances_checkpoint(self):
        review_file, proof = self.fixture.install_review()
        self.options['review_file'] = review_file
        cold = self.call()
        receipt = json.loads(proof.read_bytes()); receipt['retrieval_note'] += ' Additional synthetic custody note.'
        proof.write_text(json.dumps(receipt), encoding='utf-8')
        review = json.loads(review_file.read_bytes())
        review['corrections'][0]['source']['sha256'] = fixtures.sha(proof)
        review_file.write_text(json.dumps(review), encoding='utf-8')
        new = self.call()
        self.assertEqual('accepted', new['status'])
        self.assertNotEqual(cold['checkpoint'], new['checkpoint'])

    def test_low_space_rejects_refresh_before_builder_preserving_cache(self):
        self.call(); before = self.fixture.state()
        usage = shutil._ntuple_diskusage(total=1000, used=999, free=1)
        with patch.object(cache.shutil, 'disk_usage', return_value=usage):
            with patch.object(cache, 'crosswalk_files', side_effect=AssertionError('low-space refresh invoked builder')):
                failed = self.call(force_refresh=True)
        self.assertEqual('failed', failed['status'])
        self.assertEqual(before, self.fixture.state())

    def test_no_public_export_and_original_inputs_preserved(self):
        with patch('research.issue_history.store.IssueStore.export_bundle', side_effect=AssertionError('Private refresh attempted public export')):
            self.call()
        self.assertFalse((self.fixture.base/'public').exists())
        self.assertFalse(list(self.fixture.base.rglob('manifest.json')))
        self.assertTrue(all(fixtures.sha(p)==s for p,s in self.fixture.original_hashes.items()))

    def test_failed_cache_refresh_preserves_accepted_checkpoint_and_sanitizes_health(self):
        cold = self.call(); pointer = self.state_dir/'checkpoint.json'
        checkpoint = pointer.read_bytes(); before = self.fixture.state()
        secret = 'PRIVATE-SYNTHETIC-DETAIL '+str(self.fixture.database)
        with patch.object(refresh, 'cached_crosswalk', side_effect=RuntimeError(secret)):
            failed = self.call(force_refresh=True)
        self.assertEqual('failed', failed['status'])
        self.assertEqual(cold['checkpoint'], failed['checkpoint'])
        self.assertEqual(checkpoint, pointer.read_bytes())
        self.assertEqual(before, self.fixture.state())
        health = json.loads((self.state_dir/'health.json').read_bytes())
        self.assertEqual('failed', health['status'])
        self.assertEqual({key:cold['checkpoint'][key] for key in ('generation','cache_key','artifact_sha256')}, health['checkpoint'])
        self.assertNotIn(secret, json.dumps(health))
        self.assertEqual('unchanged', self.call()['status'])

    def test_checkpoint_interruption_retains_prior_acceptance_then_reuses_built_cache(self):
        self.call(); pointer = self.state_dir/'checkpoint.json'
        old_pointer = pointer.read_bytes(); old_cache = self.fixture.state()
        self.fixture.collection['synthetic_note'] = 'second revision'
        self.fixture.write_collection()
        atomic = refresh._atomic
        def fail_checkpoint(path, content):
            if Path(path) == pointer: raise OSError('Synthetic checkpoint interruption')
            return atomic(path, content)
        with patch.object(refresh, '_atomic', side_effect=fail_checkpoint):
            failed = self.call()
        self.assertEqual('failed', failed['status'])
        self.assertEqual(old_pointer, pointer.read_bytes())
        for name, content in old_cache.items():
            self.assertEqual(content, (self.fixture.root/name).read_bytes())
        with patch.object(cache, 'crosswalk_files', side_effect=AssertionError('Retry rebuilt valid cache')):
            retry = self.call()
        self.assertEqual('accepted', retry['status'])
        self.assertEqual('hit', retry['cache_status'])
        self.assertNotEqual(old_pointer, pointer.read_bytes())

    def test_state_root_guards_reject_repository_inputs_and_cache_overlap(self):
        for location in (Path.cwd()/'forbidden-refresh-state', self.fixture.base,
                         self.fixture.root, self.fixture.root/'nested'):
            with self.subTest(location=str(location)):
                with self.assertRaises(ValueError): self.call(state_dir=location)
        self.assertTrue(all(fixtures.sha(p)==s for p,s in self.fixture.original_hashes.items()))

    def test_bad_proof_cannot_replace_checkpoint_or_cache(self):
        review_file, proof = self.fixture.install_review(); self.options['review_file'] = review_file
        self.call(); pointer = self.state_dir/'checkpoint.json'
        old_pointer = pointer.read_bytes(); old_cache = self.fixture.state()
        proof.write_bytes(proof.read_bytes()+b' ')
        self.assertEqual('failed', self.call()['status'])
        self.assertEqual(old_pointer, pointer.read_bytes())
        self.assertEqual(old_cache, self.fixture.state())

    def test_rejected_watermark_cannot_update_checkpoint(self):
        self.call(); before = self.files(self.state_dir)
        for invalid in ('not-a-date', '2024-02-30', [], 'x'*501):
            with self.subTest(watermark=invalid):
                with self.assertRaises(ValueError): self.call(source_watermark=invalid)
        self.assertEqual(before['checkpoint.json'], (self.state_dir/'checkpoint.json').read_bytes())

    def test_forced_refresh_advances_checkpoint_and_preserves_prior_cache_generation(self):
        old = self.call(); before = self.fixture.state()
        new = self.call(force_refresh=True)
        self.assertEqual('accepted', new['status'])
        self.assertEqual('refreshed', new['cache_status'])
        self.assertNotEqual(old['checkpoint'], new['checkpoint'])
        for name, content in before.items():
            if not name.endswith('.index.json'):
                self.assertEqual(content, (self.fixture.root/name).read_bytes())

    def test_health_write_failure_reports_new_authoritative_checkpoint(self):
        old = self.call()
        self.fixture.collection['synthetic_note'] = 'accepted despite unavailable health write'
        self.fixture.write_collection()
        atomic = refresh._atomic
        def fail_health(path, content):
            if Path(path) == self.state_dir/'health.json': raise OSError('Synthetic health write interruption')
            return atomic(path, content)
        with patch.object(refresh, '_atomic', side_effect=fail_health):
            new = self.call()
        self.assertEqual('accepted', new['status'])
        self.assertFalse(new['health_persisted'])
        self.assertNotEqual(old['checkpoint'], new['checkpoint'])
        with patch.object(cache, 'crosswalk_files', side_effect=AssertionError('Committed checkpoint retry rebuilt cache')):
            retry = self.call()
        self.assertEqual('unchanged', retry['status'])
        self.assertEqual(new['checkpoint'], retry['checkpoint'])

    def test_corrupt_accepted_checkpoint_is_rejected_without_overwrite(self):
        self.call(); pointer = self.state_dir/'checkpoint.json'
        pointer.write_bytes(b'{')
        before = self.files(self.state_dir); old_cache = self.fixture.state()
        with self.assertRaises(ValueError): self.call()
        self.assertEqual(before, self.files(self.state_dir))
        self.assertEqual(old_cache, self.fixture.state())

    def test_input_mutation_before_checkpoint_commit_keeps_prior_acceptance(self):
        self.call(); pointer = self.state_dir/'checkpoint.json'
        old_pointer = pointer.read_bytes(); original = self.fixture.collection_file.read_bytes()
        atomic = refresh._atomic
        def mutate_after_record(path, content):
            atomic(path, content)
            if Path(path).parent == self.state_dir and Path(path).name[0].isdigit():
                self.fixture.collection_file.write_bytes(original+b'\n')
        with patch.object(refresh, '_atomic', side_effect=mutate_after_record):
            failed = self.call(force_refresh=True)
        self.assertEqual('failed', failed['status'])
        self.assertEqual(old_pointer, pointer.read_bytes())
        self.fixture.collection_file.write_bytes(original)
        with patch.object(cache, 'crosswalk_files', side_effect=AssertionError('restored original must use cache')):
            self.assertEqual('unchanged', self.call()['status'])

    def test_changed_workflow_version_requires_fresh_acceptance_without_rebuilding_cache(self):
        original_hash = cache._hash
        def versioned_hash(version):
            def digest(path):
                return version if Path(path).resolve() == Path(refresh.__file__).resolve() else original_hash(path)
            return digest
        with patch.object(cache, '_hash', side_effect=versioned_hash('a'*64)):
            old = self.call()
        with patch.object(cache, '_hash', side_effect=versioned_hash('b'*64)):
            with patch.object(cache, 'crosswalk_files', side_effect=AssertionError('Workflow change rebuilt source cache')):
                new = self.call()
        self.assertEqual('accepted', new['status'])
        self.assertEqual('hit', new['cache_status'])
        self.assertEqual(old['checkpoint']['cache_key'], new['checkpoint']['cache_key'])
        self.assertNotEqual(old['checkpoint']['workflow_sha256'], new['checkpoint']['workflow_sha256'])
        self.assertEqual(old['checkpoint']['generation']+1, new['checkpoint']['generation'])

    def test_new_caller_declared_snapshot_date_advances_acceptance_not_source_freshness(self):
        old = self.call()
        with patch.object(cache, 'crosswalk_files', side_effect=AssertionError('Snapshot marker rebuilt source cache')):
            new = self.call(source_watermark='2024-01-03')
        self.assertEqual('accepted', new['status'])
        self.assertEqual('hit', new['cache_status'])
        self.assertEqual(old['checkpoint']['cache_key'], new['checkpoint']['cache_key'])
        self.assertEqual('2024-01-03', new['checkpoint']['source_watermark'])
        self.assertIn('not_verified_freshness', new['checkpoint']['source_watermark_scope'])

    def test_tampered_new_cache_generation_cannot_replace_accepted_checkpoint(self):
        old = self.call(); pointer = self.state_dir/'checkpoint.json'
        old_pointer = pointer.read_bytes()
        old_artifact = Path(old['checkpoint']['artifact_path'])
        old_bytes = old_artifact.read_bytes()
        cached = refresh.cached_crosswalk
        def tamper_new_generation(*args, **kwargs):
            result = cached(*args, **kwargs)
            artifact = Path(result['artifact_path'])
            self.assertNotEqual(old_artifact, artifact)
            envelope = json.loads(artifact.read_bytes())
            envelope['version'] = 'synthetic-unknown-version'
            artifact.write_bytes(cache._bytes(envelope))
            return result
        with patch.object(refresh, 'cached_crosswalk', side_effect=tamper_new_generation):
            failed = self.call(force_refresh=True)
        self.assertEqual('failed', failed['status'])
        self.assertEqual(old['checkpoint'], failed['checkpoint'])
        self.assertEqual(old_pointer, pointer.read_bytes())
        self.assertEqual(old_bytes, old_artifact.read_bytes())


if __name__ == '__main__':
    unittest.main()
