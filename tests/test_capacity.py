"""Synthetic metadata-only accounting; payloads and private paths never escape."""
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch
from un_transcript.capacity import measure_capacity, CapacityIncomplete

A='a'*40;B='b'*40;C='c'*40


def regular(blob,size):return NS(path='PRIVATE/annotation-name',blob_id=blob,size=size,lfs=None)
def large(blob,sha,size):return NS(path='PRIVATE/transcript-name',blob_id=blob,size=size,lfs=NS(sha256=sha,size=size,pointer_size=130))


def store(provider=200):
    api=Mock()
    refs=NS(branches=[NS(ref='refs/heads/main',target_commit=C)],tags=[],converts=[],pull_requests=[])
    api.list_repo_refs.return_value=refs
    api.list_repo_commits.return_value=[NS(commit_id=x) for x in (C,B,A)]
    trees={A:[regular('1'*40,20),large('2'*40,'a'*64,100)],
           B:[regular('1'*40,20),large('3'*40,'b'*64,200)],
           C:[regular('4'*40,30),large('3'*40,'b'*64,200)]}
    api.list_repo_tree.side_effect=lambda *a,**kw:iter(trees[kw['revision']])
    return NS(api=api,repo_id='owner/private',private=True,budget_bytes=10000,
              info=Mock(return_value=(NS(sha=C),provider))),trees,refs


class Capacity(unittest.TestCase):
    def test_history_deduplicates_objects_and_preserves_deleted_versions(self):
        storage,_,_=store();value=measure_capacity(storage)
        self.assertEqual(value['current_tree_logical_bytes'],230)
        self.assertEqual(value['reachable_unique_git_blob_bytes'],310)
        self.assertEqual(value['reachable_unique_large_bytes'],300)
        self.assertEqual(value['budget_basis_bytes'],610)
        self.assertEqual(value['reachable_commits'],3)
        self.assertNotIn('PRIVATE',str(value));self.assertNotIn('annotation-name',str(value))
        self.assertFalse(value['account_capacity_accepted']);self.assertFalse(value['source_contents_read'])
        storage.api.list_repo_refs.assert_called_with('owner/private',repo_type='dataset',include_pull_requests=True)

    def test_larger_provider_meter_is_retained_conservatively(self):
        storage,_,_=store(1000)
        self.assertEqual(measure_capacity(storage)['budget_basis_bytes'],1310)

    def test_zero_provider_reading_does_not_erase_regular_git_files(self):
        storage,trees,_=store(0)
        for revision in trees:trees[revision]=[regular('1'*40,20)]
        value=measure_capacity(storage)
        self.assertEqual(value['provider_reported_bytes'],0)
        self.assertEqual(value['budget_basis_bytes'],20)
        self.assertEqual(value['reachable_unique_git_objects'],1)

    def test_changed_ref_or_head_invalidates_measurement(self):
        storage,_,refs=store()
        storage.info.side_effect=[(NS(sha=C),200),(NS(sha=B),200)]
        with self.assertRaises(CapacityIncomplete):measure_capacity(storage)
        storage,_,refs=store()
        changed=NS(branches=[NS(ref='refs/heads/main',target_commit=B)],tags=[],converts=[],pull_requests=[])
        storage.api.list_repo_refs.side_effect=[refs,changed]
        with self.assertRaises(CapacityIncomplete):measure_capacity(storage)

    def test_bounds_and_incomplete_ref_listing_fail_closed(self):
        for kwargs in ({'max_refs':0},{'max_commits':2},{'max_entries':2}):
            storage,_,_=store()
            with self.assertRaises(CapacityIncomplete):measure_capacity(storage,**kwargs)
        storage,_,refs=store();refs.pull_requests=None
        with self.assertRaises(CapacityIncomplete):measure_capacity(storage)

    def test_conflicting_object_sizes_and_invalid_metadata_rejected(self):
        storage,trees,_=store();trees[B][0].size=21
        with self.assertRaises(CapacityIncomplete):measure_capacity(storage)
        storage,trees,_=store();trees[C][1].lfs.size=199
        with self.assertRaises(CapacityIncomplete):measure_capacity(storage)
        storage,trees,_=store();trees[C][0].blob_id='main'
        with self.assertRaises(CapacityIncomplete):measure_capacity(storage)

    def test_ancestors_across_refs_are_not_double_counted(self):
        storage,_,refs=store();refs.tags=[NS(ref='refs/tags/old',target_commit=A)]
        storage.api.list_repo_commits.side_effect=lambda *a,**kw:[NS(commit_id=x) for x in ((A,) if kw['revision']==A else (C,B,A))]
        value=measure_capacity(storage)
        self.assertEqual(value['reachable_refs'],2)
        self.assertEqual(value['reachable_commits'],3)
        self.assertEqual(storage.api.list_repo_tree.call_count,3)

    def test_budget_rechecks_head_and_retains_late_provider_increase(self):
        from un_transcript.snapshots import HFStorage
        storage,_,_=store()
        report=measure_capacity(storage)
        with patch('un_transcript.capacity.measure_capacity',return_value=report.copy()):
            storage.info.return_value=(NS(sha=B),200)
            with self.assertRaises(CapacityIncomplete):HFStorage.budget_info(storage)
        with patch('un_transcript.capacity.measure_capacity',return_value=report.copy()):
            storage.info.return_value=(NS(sha=C),1000)
            _,used=HFStorage.budget_info(storage)
            self.assertEqual(used,1310)
            self.assertEqual(storage.last_capacity_measurement['provider_reported_bytes'],1000)

    def test_metadata_http_failures_include_only_fixed_operation_and_status(self):
        from un_transcript.snapshots import StorageRequestError
        class ProviderError(Exception):
            response=NS(status_code=429,url='https://private/?token=SECRET',text='PRIVATE')
        for method,operation in (('list_repo_refs','capacity_refs'),('list_repo_commits','capacity_commits'),('list_repo_tree','capacity_tree')):
            storage,_,_=store()
            getattr(storage.api,method).side_effect=ProviderError('SECRET PRIVATE')
            with self.assertRaises(StorageRequestError) as raised:measure_capacity(storage)
            self.assertEqual(raised.exception.operation,operation)
            self.assertEqual(raised.exception.status_code,429)
            self.assertNotIn('SECRET',str(raised.exception))
            self.assertNotIn('PRIVATE',str(raised.exception))

    def test_lazy_tree_page_failure_keeps_safe_diagnostics(self):
        from un_transcript.snapshots import StorageRequestError
        class ProviderError(Exception):response=NS(status_code=503)
        def pages(*args,**kwargs):
            yield regular('1'*40,20)
            raise ProviderError('PRIVATE signed URL')
        storage,_,_=store();storage.api.list_repo_tree.side_effect=pages
        with self.assertRaises(StorageRequestError) as raised:measure_capacity(storage)
        self.assertEqual(raised.exception.operation,'capacity_tree')
        self.assertEqual(raised.exception.status_code,503)
        self.assertNotIn('PRIVATE',str(raised.exception))
