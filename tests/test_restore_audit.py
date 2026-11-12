import json
from pathlib import Path
import tempfile
import sqlite3
import unittest
from un_transcript.exports import export_snapshot
from un_transcript.restore_audit import audit_restored_exports, summarize_backfill
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


class BackfillSummaryTests(unittest.TestCase):
    def test_last_inventory_claim_and_stored_identity_define_disjoint_counts(self):
        with sqlite3.connect(':memory:') as db:
            db.row_factory=sqlite3.Row
            db.executescript("""
                PRAGMA user_version=2;
                CREATE TABLE collection_runs(run_id TEXT, started_at TEXT);
                CREATE TABLE inventory_receipts(receipt_id TEXT, run_id TEXT, page INTEGER);
                CREATE TABLE inventory_meetings(receipt_id TEXT, meeting_id TEXT, has_transcript INTEGER);
                CREATE TABLE meetings(meeting_id TEXT PRIMARY KEY);
                INSERT INTO collection_runs VALUES ('old','2026-11-10'),('new','2026-11-11');
                INSERT INTO inventory_receipts VALUES ('r1','old',1),('r2','new',1);
                INSERT INTO inventory_meetings VALUES
                    ('r1','retained',1),('r1','revised',1),
                    ('r2','retained',1),('r2','revised',0),('r2','backfill',1),('r2','unavailable',0);
                INSERT INTO meetings VALUES ('retained'),('revised');
            """)
            result=summarize_backfill(db)
            self.assertEqual(result['inventory_meetings'],4)
            for key in ('advertised_with_stored_source','advertised_without_stored_source',
                        'not_advertised_with_stored_source','not_advertised_without_stored_source'):
                self.assertEqual(result[key],1)
            self.assertFalse(result['current_download_availability_verified'])
            self.assertNotIn('retained',json.dumps(result))

    def test_legacy_schema_reports_unknown_instead_of_zero_backlog(self):
        with sqlite3.connect(':memory:') as db:
            db.execute('PRAGMA user_version=1')
            self.assertEqual(summarize_backfill(db),
                             {'available':False,'reason':'inventory_metadata_not_recorded'})
