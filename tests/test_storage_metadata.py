"""Immutable metadata batching must preserve actual byte and revision checks."""
from types import SimpleNamespace
from unittest.mock import Mock
import unittest
from un_transcript.snapshots import HFStorage, RemoteEntryMissing


class Metadata(unittest.TestCase):
    def store(self, blobs):
        api=Mock()
        api.get_paths_info.side_effect=lambda repo,paths,**kwargs:[SimpleNamespace(path=p,size=len(blobs[p])) for p in paths if p in blobs]
        download=Mock(side_effect=lambda path,revision:blobs[path])
        return HFStorage('owner/private',api=api,downloader=download),api,download

    def test_250_verified_files_use_three_metadata_requests(self):
        blobs={f'raw/{i}.json':str(i).encode() for i in range(250)}
        store,api,download=self.store(blobs)
        store._verify_remote(blobs,'a'*40)
        self.assertEqual(api.get_paths_info.call_count,3)
        self.assertTrue(all(len(c.args[1])<=100 for c in api.get_paths_info.call_args_list))
        self.assertEqual(download.call_count,250)  # Every actual byte/hash check remains.
        store._verify_remote(blobs,'a'*40)
        self.assertEqual(api.get_paths_info.call_count,3)
        self.assertEqual(download.call_count,500)

    def test_changed_revision_cannot_reuse_metadata_or_absence(self):
        blobs={};store,api,download=self.store(blobs)
        with self.assertRaises(RemoteEntryMissing):store.read('new.json','a'*40)
        blobs['new.json']=b'new'
        self.assertEqual(store.read('new.json','b'*40),b'new')
        self.assertEqual(api.get_paths_info.call_count,2)
        self.assertEqual(download.call_count,1)

    def test_failure_is_not_cached_as_missing(self):
        store,api,_=self.store({'item':b'x'})
        normal=api.get_paths_info.side_effect
        api.get_paths_info.side_effect=PermissionError('synthetic')
        with self.assertRaises(PermissionError):store.read('item','a'*40)
        api.get_paths_info.side_effect=normal
        self.assertEqual(store.read('item','a'*40),b'x')
        self.assertEqual(api.get_paths_info.call_count,2)

    def test_cached_size_cannot_bypass_download_validation(self):
        store,api,download=self.store({'item':b'x'})
        store._entries(['item'],'a'*40)
        download.side_effect=lambda *args:b'longer'
        with self.assertRaisesRegex(ValueError,'size differs'):store.read('item','a'*40)
        self.assertEqual(api.get_paths_info.call_count,1)

    def test_cached_metadata_outage_still_checks_downloaded_hashes(self):
        blobs={'item':b'x'};store,api,download=self.store(blobs)
        store._verify_remote(blobs,'a'*40)
        api.get_paths_info.side_effect=ConnectionError('synthetic outage')
        store._verify_remote(blobs,'a'*40)
        download.side_effect=lambda *args:b'y'
        with self.assertRaisesRegex(ValueError,'verification failed'):
            store._verify_remote(blobs,'a'*40)

    def test_mutable_ref_and_unexpected_metadata_are_rejected(self):
        store,api,_=self.store({'item':b'x'})
        with self.assertRaisesRegex(ValueError,'immutable'):store.read('item','main')
        api.get_paths_info.assert_not_called()
        for entries in ([SimpleNamespace(path='other',size=1)],
                        [SimpleNamespace(path='item',size=1)]*2):
            api.get_paths_info.side_effect=None;api.get_paths_info.return_value=entries
            with self.assertRaisesRegex(ValueError,'metadata path'):store.read('item','a'*40)
        self.assertEqual(store._entry_cache,{})
