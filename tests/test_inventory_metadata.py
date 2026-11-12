"""Synthetic source-bound inventories, additive migration and export compatibility."""
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from un_transcript.collection import _meeting
from un_transcript.exports import export_snapshot
from un_transcript.restore_audit import audit_restored_exports
from un_transcript.snapshots import file_sha, seal_snapshot, prepare_public_bundle
from un_transcript.warehouse import Warehouse

DAY = '2026-11-10'
STAMP = DAY + 'T12:00:00Z'
MID = 'ga/81/42'


def original(title='Synthetic inventory title', **extra):
    return dict(slug=MID, date=DAY, title=title, body='GA', hasTranscript=False, **extra)


class InventoryMetadataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.store = Warehouse(self.root/'live/warehouse.sqlite3')

    def tearDown(self):
        self.store.close(); self.tmp.cleanup()

    def inventory(self, run='run1', rows=None, status='inventory_complete', **payload_changes):
        rows = [original()] if rows is None else rows
        self.store.start_run(run, {'synthetic': True}, STAMP)
        payload = dict(page=1, total=len(rows), hasMore=False, meetings=rows)
        payload.update(payload_changes)
        receipt = self.store.record_inventory(run, dict(raw=json.dumps(payload).encode(), date=DAY,
            page=1, retrieved_at=STAMP, source_url='https://transcripts.un.org/en/meetings.json?date='+DAY))
        self.store.record_coverage(run, 'inventory:'+DAY, status)
        self.store.record_coverage(run, MID, 'unavailable')
        self.store.finish_run(run, 'partial', STAMP)
        selected = {r['slug']:_meeting(r, DAY) for r in rows}
        return receipt, selected

    def export(self, name='snapshot'):
        output = self.root/name
        manifest = export_snapshot(self.store, output, name, STAMP)
        meetings = json.loads((output/'public'/manifest['partitions'][0]['path']).read_text())['meetings']
        return output, meetings

    def test_unavailable_meeting_has_metadata_and_exact_inventory_provenance(self):
        receipt, selected = self.inventory()
        self.store.record_inventory_meetings('run1', selected)
        self.store.record_inventory_meetings('run1', selected)
        output, rows = self.export()
        row = rows[0]
        self.assertEqual((row['date'], row['body'], row['title']), (DAY, 'GA', 'Synthetic inventory title'))
        self.assertEqual((row['status'], row['segments'], row['positions']), ('unavailable', 0, []))
        self.assertEqual(row['source_url'], 'https://transcripts.un.org/en/'+MID)
        with (output/'private/inventory_meetings.csv').open(newline='') as stream:
            ledger = list(csv.DictReader(stream))
        self.assertEqual(len(ledger), 1)
        self.assertEqual(ledger[0]['receipt_id'], receipt)
        self.assertEqual(ledger[0]['has_transcript'], '0')
        self.assertFalse(self.store.db.execute('SELECT * FROM meetings').fetchall())
        self.assertEqual(json.loads((output/'private/manifest.json').read_text())['warehouse_schema'], 2)
        prepare_public_bundle(output/'public')
        seal_snapshot(self.store, output, {}, 'snapshot', STAMP)
        before = file_sha(output/'warehouse.sqlite3')
        self.assertTrue(audit_restored_exports(output, self.root/'replayed')['byte_identical_exports'])
        self.assertEqual(before, file_sha(output/'warehouse.sqlite3'))

    def test_partial_inventory_is_retained_but_not_used_as_metadata(self):
        _, selected = self.inventory(status='inventory_failed')
        self.assertEqual(self.store.record_inventory_meetings('run1', selected), 0)
        _, rows = self.export()
        self.assertIsNone(rows[0]['date'])
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM inventory_receipts').fetchone()[0], 1)

    def test_incomplete_pagination_and_forged_selected_values_fail_atomically(self):
        _, selected = self.inventory(hasMore=True)
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            self.store.record_inventory_meetings('run1', selected)
        self.assertFalse(self.store.db.execute('SELECT * FROM inventory_meetings').fetchall())
        _, selected = self.inventory('run2')
        selected[MID]['title'] = 'Fabricated metadata'
        with self.assertRaisesRegex(ValueError, 'differs'):
            self.store.record_inventory_meetings('run2', selected)
        self.assertFalse(self.store.db.execute('SELECT * FROM inventory_meetings').fetchall())

    def test_unselected_and_reserved_ids_do_not_enter_normalized_inventory(self):
        reserved = original(); reserved['slug'] = 'ga/c1/81/1'
        _, selected = self.inventory(rows=[original(), reserved])
        selected.pop(MID)
        self.assertEqual(self.store.record_inventory_meetings('run1', selected), 0)

    def test_late_metadata_revision_keeps_history_and_removal_keeps_last_known(self):
        first, selected = self.inventory()
        self.store.record_inventory_meetings('run1', selected)
        second, selected = self.inventory('run2', [original(title='Revised inventory title')])
        self.store.record_inventory_meetings('run2', selected)
        self.store.start_run('run3', {}, STAMP)
        self.store.record_coverage('run3', MID, 'no_longer_listed')
        self.store.finish_run('run3', 'partial', STAMP)
        _, rows = self.export()
        self.assertEqual(rows[0]['title'], 'Revised inventory title')
        self.assertEqual(rows[0]['status'], 'no_longer_listed')
        stored = self.store.db.execute('SELECT receipt_id,title FROM inventory_meetings ORDER BY title').fetchall()
        self.assertEqual({r['receipt_id'] for r in stored}, {first, second})
        self.assertEqual({r['title'] for r in stored}, {'Synthetic inventory title', 'Revised inventory title'})

    def test_inventory_does_not_rewrite_stored_source_revision_metadata(self):
        _, selected = self.inventory()
        self.store.record_inventory_meetings('run1', selected)
        meeting = dict(selected[MID], title='Title bound to source revision')
        self.store.ingest(meeting, b'{"synthetic":"private transcript"}', [], STAMP)
        _, rows = self.export()
        self.assertEqual(rows[0]['title'], 'Title bound to source revision')
        self.assertEqual(rows[0]['segments'], 0)

    def test_tampered_original_rejected_before_metadata_write(self):
        receipt, selected = self.inventory()
        raw_hash = self.store.db.execute('SELECT raw_sha256 FROM inventory_receipts WHERE receipt_id=?', (receipt,)).fetchone()[0]
        (self.store.raw_directory/(raw_hash+'.json')).write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, 'integrity'):
            self.store.record_inventory_meetings('run1', selected)

    def test_complete_pagination_binds_each_meeting_to_its_original_page(self):
        self.store.start_run('pages', {}, STAMP)
        rows = [original(), dict(original(), slug='sc/99999')]
        receipt_ids = []
        for page, row in enumerate(rows, 1):
            payload = dict(page=page, total=2, hasMore=page == 1, meetings=[row])
            receipt_ids.append(self.store.record_inventory('pages', dict(raw=json.dumps(payload).encode(),
                date=DAY, page=page, retrieved_at=STAMP,
                source_url='https://transcripts.un.org/en/meetings.json?date='+DAY+'&page='+str(page))))
        self.store.record_coverage('pages', 'inventory:'+DAY, 'inventory_complete')
        self.store.record_inventory_meetings('pages', {r['slug']:_meeting(r, DAY) for r in rows})
        actual = dict(self.store.db.execute('SELECT meeting_id,receipt_id FROM inventory_meetings'))
        self.assertEqual(actual, dict(zip((r['slug'] for r in rows), receipt_ids)))

    def test_reserved_date_rejected_before_any_original_file_read(self):
        from unittest.mock import patch
        self.store.start_run('reserved', {}, STAMP)
        self.store.record_inventory('reserved', dict(raw=b'{}', date='2026-10-05',
            page=1, retrieved_at=STAMP, source_url='https://transcripts.un.org/en/meetings.json?date=2026-10-05'))
        self.store.record_coverage('reserved', 'inventory:2026-10-05', 'inventory_complete')
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('Must not open reserved data')):
            with self.assertRaisesRegex(ValueError, 'Reserved'):
                self.store.record_inventory_meetings('reserved', {})

    def test_legacy_replay_remains_unchanged_and_working_copy_migration_is_additive(self):
        self.inventory(status='inventory_failed')
        self.store.db.execute('DROP TABLE inventory_meetings')
        self.store.db.execute('PRAGMA user_version=1')
        self.store.db.commit()
        output, rows = self.export('legacy')
        self.assertIsNone(rows[0]['date'])
        self.assertFalse((output/'private/inventory_meetings.csv').exists())
        # Captured from the pre-migration exporter at source main 1e55505.
        tree = {p.relative_to(output).as_posix():file_sha(p) for p in output.rglob('*') if p.is_file()}
        combined = hashlib.sha256(json.dumps(tree, sort_keys=True).encode()).hexdigest()
        self.assertEqual(combined, 'f869a1f5de1882b233cc90424e004db0216d0d2ae8ce40b6a220ab060fd0cf92')
        seal_snapshot(self.store, output, {}, 'legacy', STAMP)
        before = file_sha(output/'warehouse.sqlite3')
        self.assertTrue(audit_restored_exports(output, self.root/'legacy-replayed')['byte_identical_exports'])
        self.store.close()
        self.store = Warehouse(self.root/'live/warehouse.sqlite3')
        self.assertEqual(self.store.db.execute('PRAGMA user_version').fetchone()[0], 2)
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM inventory_receipts').fetchone()[0], 1)
        self.assertFalse(self.store.db.execute('SELECT * FROM inventory_meetings').fetchall())
        self.assertEqual(before, file_sha(output/'warehouse.sqlite3'))
