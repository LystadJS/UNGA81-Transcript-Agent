import json
from pathlib import Path
import tempfile
import unittest
from un_transcript.exports import export_snapshot
from un_transcript.restore_audit import audit_restored_exports
from un_transcript.snapshots import atomic_json, file_sha, seal_snapshot
from un_transcript.warehouse import Warehouse


class RestoreAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        with Warehouse(self.root/'live/warehouse.sqlite3') as db:
            db.start_run('synthetic', {'synthetic': True}, '2026-11-12T00:00:00Z')
            db.record_coverage('synthetic', 'inventory:2026-11-11', 'inventory_complete')
            db.record_coverage('synthetic', 'ga/synthetic', 'unavailable')
            db.finish_run('synthetic', 'partial', '2026-11-12T00:01:00Z')
            self.snapshot = self.root/'snapshot'
            export_snapshot(db, self.snapshot, 'synthetic', '2026-11-12T00:01:00Z')
            seal_snapshot(db, self.snapshot, {}, 'synthetic', '2026-11-12T00:01:00Z')

    def tearDown(self):
        self.temp.cleanup()

    def test_reproduces_without_mutating_database(self):
        before = file_sha(self.snapshot/'warehouse.sqlite3')
        result = audit_restored_exports(self.snapshot, self.root/'reproduced')
        self.assertTrue(result['byte_identical_exports'])
        self.assertGreater(result['csv_files_verified'], 10)
        self.assertEqual(before, file_sha(self.snapshot/'warehouse.sqlite3'))

    def test_detects_self_consistent_seal_with_incoherent_export(self):
        # Hash validation alone would accept this sealed but stale CSV.
        path = self.snapshot/'private/coverage.csv'
        path.write_bytes(path.read_bytes().replace(b'unavailable', b'not_published'))
        manifest = json.loads((self.snapshot/'snapshot.json').read_bytes())
        for item in manifest['files']:
            if item['path'] == 'private/coverage.csv':
                item.update(sha256=file_sha(path), bytes=path.stat().st_size)
        atomic_json(self.snapshot/'snapshot.json', manifest)
        with self.assertRaisesRegex(ValueError, 'do not reproduce'):
            audit_restored_exports(self.snapshot, self.root/'reproduced')

    def test_refuses_to_overwrite_existing_replay(self):
        target = self.root/'existing'; target.mkdir()
        with self.assertRaises(FileExistsError):
            audit_restored_exports(self.snapshot, target)

    def test_refuses_replay_inside_immutable_snapshot(self):
        with self.assertRaisesRegex(ValueError, 'outside the immutable snapshot'):
            audit_restored_exports(self.snapshot, self.snapshot/'reproduced')
