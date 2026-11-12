"""Publication failure and restoration tests use an in-memory remote, never HF."""
import json
import hashlib
import os
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from un_transcript.warehouse import Warehouse
from un_transcript.exports import export_snapshot
from un_transcript.snapshots import HFStorage, seal_snapshot, verify_snapshot, encode, MAX_FILE_BYTES, DISK_RESERVE_BYTES


class EntryNotFoundError(Exception):
    pass


class FakeRemote(HFStorage):
    def __init__(self, *, private=True, budget=10_000_000):
        self.head = '0' * 40
        self.revisions = {self.head:{}}
        self.used = 0
        self.visibility = private
        self.corrupt = False
        self.commits = 0
        self.committed_values = []
        self.downloads = []
        super().__init__('owner/private' if private else 'owner/public', private=private, budget_bytes=budget,
                         api=self,downloader=self.download)

    def repo_info(self,*a,**kw):
        return SimpleNamespace(private=self.visibility,sha=self.head,usedStorage=self.used)

    def get_paths_info(self,repo,paths,**kw):
        revision = self.revisions[kw['revision']]
        result = []
        for p in paths:
            if p in revision:
                result.append(SimpleNamespace(path=p, size=len(revision[p])))
            elif any(name.startswith(p + '/') for name in revision):
                result.append(SimpleNamespace(path=p, size=None))
        return result

    def download(self,path,revision):
        self.downloads.append(path)
        if path not in self.revisions[revision]:
            raise EntryNotFoundError(path)
        data = self.revisions[revision][path]
        return b'x' + data[1:] if self.corrupt and path.endswith('.sqlite3') else data

    def _commit(self,files,parent,message):
        if parent != self.head:
            raise ValueError('Concurrent writer conflict')
        self.commits += 1
        new = f'{self.commits:040x}'
        self.committed_values.extend(files.values())
        uploaded = {p: v.read_bytes() if isinstance(v,Path) else v for p,v in files.items()}
        self.revisions[new] = {**self.revisions[parent],**uploaded}
        self.head = new
        self.used += sum(map(len, uploaded.values()))
        return new


class Snapshots(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.warehouse = Warehouse(self.root/'live'/'warehouse.sqlite3')
        self.warehouse.start_run('run',{},'2026-11-11T00:00:00Z')
        self.warehouse.ingest({'meeting_id':'ga/81/42','date':'2026-11-10','title':'Synthetic meeting','body':'ga',
                               'source_url':'https://transcripts.un.org/en/ga/81/42',
                               'json_url':'https://transcripts.un.org/en/ga/81/42.json'},
                              b'{"synthetic":true}',[{'text':'Synthetic text only','language':'en','speaker':'fictional',
                               'country':'','capacity':'unknown','json_pointer':'/transcript/data/0'}],
                              '2026-11-11T00:00:01Z')
        self.inventory_raw = b'{"meetings":[],"synthetic":true}'
        self.warehouse.record_inventory('run',{'raw':self.inventory_raw,'date':'2026-11-10','page':1,
            'source_url':'https://transcripts.un.org/en/meetings.json?date=2026-11-10&xlang=1&page=1',
            'retrieved_at':'2026-11-11T00:00:00Z','headers':{}})
        self.warehouse.record_coverage('run','ga/81/42','collected')
        self.warehouse.finish_run('run','complete','2026-11-11T00:00:02Z')
        self.snapshot = self.root/'snapshot'
        export_snapshot(self.warehouse,self.snapshot,'s1','2026-11-11T00:00:02Z')
        seal_snapshot(self.warehouse,self.snapshot,{'cursor':1},'s1','2026-11-11T00:00:02Z')

    def tearDown(self):
        self.warehouse.close(); self.tmp.cleanup()

    def test_roundtrip_hashes_database_and_cursor(self):
        remote = FakeRemote()
        remote.publish(self.snapshot)
        restored = self.root/'restored'
        remote.restore(restored)
        self.assertEqual(json.loads((restored/'data'/'state.json').read_bytes()),{'cursor':1})
        with Warehouse(restored/'data'/'warehouse.sqlite3') as db:
            self.assertEqual(len(db.current_segments()),1)
            self.assertEqual(db.current_segments()[0]['text'],'Synthetic text only')
        self.assertEqual(remote.commits,2)

    def test_remote_corruption_keeps_previous_pointer(self):
        remote = FakeRemote(); remote.corrupt = True
        with self.assertRaisesRegex(ValueError,'latest pointer unchanged'):
            remote.publish(self.snapshot)
        self.assertNotIn('latest.json',remote.revisions[remote.head])

    def test_quota_and_visibility_fail_before_commit(self):
        remote = FakeRemote(budget=10)
        with self.assertRaisesRegex(ValueError,'budget'): remote.publish(self.snapshot)
        self.assertEqual(remote.commits,0)
        remote = FakeRemote(); remote.visibility=False
        with self.assertRaisesRegex(ValueError,'visibility'): remote.publish(self.snapshot)
        self.assertEqual(remote.commits,0)

    def test_tamper_fails_before_any_restore_write(self):
        remote=FakeRemote(); remote.publish(self.snapshot); remote.corrupt=True
        target=self.root/'restored'
        with self.assertRaisesRegex(ValueError,'hash mismatch'): remote.restore(target)
        self.assertFalse((target/'data').exists())
        self.assertEqual(list(target.glob('.restore-*')),[])

    def test_path_traversal_rejected(self):
        m=json.loads((self.snapshot/'snapshot.json').read_bytes())
        m['files'][0]['path']='../escape'
        (self.snapshot/'snapshot.json').write_bytes(encode(m))
        with self.assertRaisesRegex(ValueError,'Unsafe'): verify_snapshot(self.snapshot)

    def test_private_bytes_not_in_public_publication(self):
        remote=FakeRemote(private=False)
        remote.publish_public(self.snapshot/'public')
        for path,data in remote.revisions[remote.head].items():
            self.assertNotIn('private/',path)
            self.assertNotIn('raw/',path)
            self.assertNotIn(b'Synthetic text only',data)
        self.assertEqual(json.loads(remote.revisions[remote.head]['latest.json'])['schema'],'un.archive.v1')

    def test_empty_remote_only_missing_entry_initializes(self):
        remote=FakeRemote()
        self.assertIsNone(remote.restore(self.root/'empty'))
        remote.publish(self.snapshot)
        remote.downloader=lambda *args: (_ for _ in ()).throw(PermissionError('denied'))
        with self.assertRaises(PermissionError):remote.restore(self.root/'denied')

    def test_nonempty_local_warehouse_not_overwritten(self):
        remote=FakeRemote();remote.publish(self.snapshot)
        (self.root/'nonempty'/'data').mkdir(parents=True)
        with self.assertRaises(FileExistsError): remote.restore(self.root/'nonempty')


    def _rewrite_remote_manifest(self, remote, transform):
        pointer = json.loads(remote.revisions[remote.head]['latest.json'])
        revision = remote.revisions[pointer['revision']]
        manifest = json.loads(revision[pointer['manifest_path']])
        transform(manifest)
        revision[pointer['manifest_path']] = encode(manifest)
        pointer['manifest_sha256'] = hashlib.sha256(encode(manifest)).hexdigest()
        remote.revisions[remote.head]['latest.json'] = encode(pointer)

    def test_inventory_original_is_required_sealed_and_restored(self):
        raw_hash = hashlib.sha256(self.inventory_raw).hexdigest()
        self.assertEqual((self.snapshot/'raw'/(raw_hash+'.json')).read_bytes(),self.inventory_raw)
        remote=FakeRemote();remote.publish(self.snapshot)
        remote.restore(self.root/'restored')
        self.assertEqual((self.root/'restored'/'data'/'raw'/(raw_hash+'.json')).read_bytes(),self.inventory_raw)
        manifest=json.loads((self.snapshot/'snapshot.json').read_bytes())
        manifest['files']=[r for r in manifest['files'] if r['path']!='raw/'+raw_hash+'.json']
        (self.snapshot/'snapshot.json').write_bytes(encode(manifest))
        with self.assertRaisesRegex(ValueError,'original source/inventory'):verify_snapshot(self.snapshot)

    def test_cas_sealing_uses_hardlinks_and_uploads_paths(self):
        for source in self.warehouse.raw_directory.glob('*.json'):
            self.assertEqual(source.stat().st_ino,(self.snapshot/'raw'/source.name).stat().st_ino)
        remote=FakeRemote();remote.publish(self.snapshot)
        self.assertTrue(all(isinstance(v,Path) for v in remote.committed_values[:-1]))
        self.assertIsInstance(remote.committed_values[-1],bytes)

    def test_repeated_snapshot_identity_refused_without_changing_pointer(self):
        for private in (True,False):
            remote=FakeRemote(private=private)
            publish=remote.publish if private else remote.publish_public
            directory=self.snapshot if private else self.snapshot/'public'
            publish(directory); original=remote.revisions[remote.head]['latest.json']
            with self.assertRaisesRegex(FileExistsError,'prefix'):publish(directory)
            self.assertEqual(remote.commits,2)
            self.assertEqual(remote.revisions[remote.head]['latest.json'],original)

    def test_existing_raw_is_not_reuploaded(self):
        remote=FakeRemote();remote.publish(self.snapshot)
        snapshot2=self.root/'snapshot2'
        export_snapshot(self.warehouse,snapshot2,'s2','2026-11-11T00:00:02Z')
        seal_snapshot(self.warehouse,snapshot2,{},'s2','2026-11-11T00:00:02Z')
        previous=len(remote.committed_values)
        remote.publish(snapshot2)
        for value in remote.committed_values[previous:]:
            if isinstance(value,Path):self.assertNotEqual(value.parent.name,'raw')

    def test_pointer_path_and_identity_validation_precedes_manifest_download(self):
        remote=FakeRemote();remote.publish(self.snapshot)
        pointer=json.loads(remote.revisions[remote.head]['latest.json'])
        pointer['manifest_path']='snapshots/unrelated/snapshot.json'
        remote.revisions[remote.head]['latest.json']=encode(pointer)
        remote.downloads.clear()
        with self.assertRaisesRegex(ValueError,'pointer identity'):remote.restore(self.root/'invalid')
        self.assertEqual(remote.downloads,['latest.json'])

    def test_negative_bool_and_oversized_descriptors_refused_before_artifact_download(self):
        for size in (-1,True,MAX_FILE_BYTES+1):
            remote=FakeRemote();remote.publish(self.snapshot)
            self._rewrite_remote_manifest(remote,lambda m:m['files'][0].update(bytes=size))
            remote.downloads.clear()
            with self.subTest(size=size),self.assertRaisesRegex(ValueError,'byte/count'):remote.restore(self.root/('invalid-'+str(size)))
            self.assertEqual(len(remote.downloads),2)

    def test_duplicate_descriptors_and_reserved_manifest_path_refused(self):
        for replacement in ('duplicate','snapshot.json'):
            remote=FakeRemote();remote.publish(self.snapshot)
            def alter(m):
                if replacement=='duplicate':m['files'].append(m['files'][0])
                else:m['files'][0]['path']=replacement
            self._rewrite_remote_manifest(remote,alter)
            with self.assertRaisesRegex(ValueError,'Duplicate or reserved'):remote.restore(self.root/replacement)

    def test_disk_reserve_and_metadata_errors_leave_no_data_tree(self):
        remote=FakeRemote();remote.publish(self.snapshot)
        with patch('un_transcript.snapshots.shutil.disk_usage',return_value=SimpleNamespace(free=DISK_RESERVE_BYTES)):
            with self.assertRaisesRegex(ValueError,'disk reserve'):remote.restore(self.root/'low-disk')
        self.assertFalse((self.root/'low-disk'/'data').exists())
        remote.get_paths_info=lambda *a,**kw:(_ for _ in ()).throw(ConnectionError('metadata unavailable'))
        with self.assertRaises(ConnectionError):remote.restore(self.root/'unavailable')

    def test_restore_promotes_exactly_one_complete_data_directory(self):
        remote=FakeRemote();remote.publish(self.snapshot)
        actual=os.replace;promotions=[]
        def replace(src,dst):
            if Path(dst).name=='data':
                self.assertTrue((Path(src)/'warehouse.sqlite3').exists())
                self.assertTrue((Path(src)/'state.json').exists())
                self.assertTrue((Path(src)/'restored.json').exists())
                promotions.append((src,dst))
            return actual(src,dst)
        with patch('un_transcript.snapshots.os.replace',side_effect=replace):remote.restore(self.root/'atomic')
        self.assertEqual(len(promotions),1)

    def test_immutable_public_manifest_preserves_relative_paths(self):
        remote=FakeRemote(private=False);latest=remote.publish_public(self.snapshot/'public')
        stored=json.loads(remote.revisions[remote.head]['snapshots/s1/manifest.json'])
        self.assertEqual(stored,json.loads((self.snapshot/'public'/'manifest.json').read_bytes()))
        self.assertTrue(latest['downloads'][0]['path'].startswith('snapshots/s1/'))
        self.assertEqual(stored['downloads'][0]['path'],'meetings.csv')

    def test_rehashed_public_private_fields_rejected_before_upload(self):
        manifest_path=self.snapshot/'public'/'manifest.json'
        manifest=json.loads(manifest_path.read_bytes())
        descriptor=manifest['partitions'][0];file=self.snapshot/'public'/descriptor['path']
        payload=json.loads(file.read_bytes());payload['meetings'][0]['annotation']='Private reviewer text'
        file.write_bytes(encode(payload));descriptor.update(bytes=file.stat().st_size,sha256=hashlib.sha256(file.read_bytes()).hexdigest())
        manifest_path.write_bytes(encode(manifest));remote=FakeRemote(private=False)
        with self.assertRaisesRegex(ValueError,'allowlist'):remote.publish_public(self.snapshot/'public')
        self.assertEqual(remote.commits,0)

    def test_public_csv_extra_columns_rejected_even_with_updated_hash(self):
        path=self.snapshot/'public'/'meetings.csv'
        path.write_text('meeting_id,private_text\nfixture,secret\n')
        manifest_path=self.snapshot/'public'/'manifest.json';manifest=json.loads(manifest_path.read_bytes())
        manifest['downloads'][0].update(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        manifest_path.write_bytes(encode(manifest));remote=FakeRemote(private=False)
        with self.assertRaisesRegex(ValueError,'allowlist'):remote.publish_public(self.snapshot/'public')
        self.assertEqual(remote.commits,0)

    def test_public_nested_object_in_safe_field_rejected(self):
        # Known field names cannot smuggle private dictionaries into display values.
        manifest_path=self.snapshot/'public'/'manifest.json';manifest=json.loads(manifest_path.read_bytes())
        descriptor=manifest['partitions'][0];file=self.snapshot/'public'/descriptor['path']
        payload=json.loads(file.read_bytes());payload['meetings'][0]['title']={'private_annotation':'secret'}
        file.write_bytes(encode(payload));descriptor.update(bytes=file.stat().st_size,sha256=hashlib.sha256(file.read_bytes()).hexdigest())
        manifest_path.write_bytes(encode(manifest));remote=FakeRemote(private=False)
        with self.assertRaisesRegex(ValueError,'public scalar'):remote.publish_public(self.snapshot/'public')



    def test_public_position_reference_arrays_cannot_contain_text_or_objects(self):
        manifest_path=self.snapshot/'public'/'manifest.json';manifest=json.loads(manifest_path.read_bytes())
        descriptor=manifest['partitions'][0];file=self.snapshot/'public'/descriptor['path']
        payload=json.loads(file.read_bytes())
        row=dict(country='USA',capacity='national',issue_id='test',issue_version='v1',issue_label='Synthetic issue',proposition='Synthetic proposal',
                 label='support',stance='support',status='clear',confidence=.95,model_version='synthetic',source_url='https://transcripts.un.org/en/ga/81/42',
                 source_revision_ids=['revision:abc'],source_segment_ids=['segment:def'],evidence_ids=['evidence:ghi'])
        payload['meetings'][0]['positions']=[row]
        for bad in (['Private annotation text'],[{'raw_text':'secret'}]):
            row['evidence_ids']=bad
            file.write_bytes(encode(payload));descriptor.update(bytes=file.stat().st_size,sha256=hashlib.sha256(file.read_bytes()).hexdigest())
            manifest_path.write_bytes(encode(manifest));remote=FakeRemote(private=False)
            with self.assertRaisesRegex(ValueError,'reference IDs'):remote.publish_public(self.snapshot/'public')
            self.assertEqual(remote.commits,0)



    def test_invalid_remote_head_cannot_restore_or_publish_without_parent(self):
        invalid = (None, '', 'main', 'a' * 39, 'a' * 41, 'z' * 40, 123, True)
        for revision in invalid:
            for private in (True, False):
                remote = FakeRemote(private=private)
                remote.repo_info = lambda *a, **kw: SimpleNamespace(private=private, sha=revision, usedStorage=0)
                with patch.object(remote, 'get_paths_info') as metadata:
                    publish = remote.publish if private else remote.publish_public
                    directory = self.snapshot if private else self.snapshot / 'public'
                    with self.subTest(revision=revision, private=private), self.assertRaisesRegex(ValueError, 'initialize a new dataset'):
                        publish(directory)
                    if private:
                        with self.assertRaisesRegex(ValueError, 'immutable commit SHA'):
                            remote.restore(self.root / 'invalid-head')
                    metadata.assert_not_called()
                self.assertEqual(remote.commits, 0)
                self.assertEqual(remote.downloads, [])
        self.assertFalse((self.root / 'invalid-head' / 'data').exists())

    def test_inventory_aggregate_cannot_smuggle_private_fields_or_wrong_counts(self):
        path=self.snapshot/'public/manifest.json'
        original=json.loads(path.read_bytes())
        for values in ({'private transcript':1},{'inventory_complete':'private text'},{'inventory_complete':2}):
            m=json.loads(json.dumps(original));m['coverage'].update(inventory_dates=1,inventory_statuses=values)
            path.write_bytes(encode(m))
            remote=FakeRemote(private=False)
            with self.assertRaises(ValueError):remote.publish_public(self.snapshot/'public')
            self.assertEqual(remote.commits,0)
        path.write_bytes(encode(original))

    def test_remote_head_accepts_full_lowercase_and_uppercase_hex(self):
        for revision in ('abcdef0123456789' * 2 + 'abcdef01', 'ABCDEF0123456789' * 2 + 'ABCDEF01'):
            remote = FakeRemote()
            remote.repo_info = lambda *a, **kw: SimpleNamespace(private=True, sha=revision, usedStorage=0)
            info, used = remote.info()
            self.assertEqual(info.sha, revision)
            self.assertEqual(used, 0)

    def test_valid_head_does_not_turn_unknown_storage_into_zero(self):
        remote = FakeRemote(); remote.used = None
        with self.assertRaisesRegex(ValueError, 'storage usage unavailable'):
            remote.publish(self.snapshot)
        self.assertEqual(remote.commits, 0)


if __name__=='__main__': unittest.main()
