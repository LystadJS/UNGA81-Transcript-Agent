"""Read-only verification that restored research exports reproduce from SQLite."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

from .exports import export_snapshot
from .snapshots import file_sha, verify_snapshot
from .collection import _meeting, RESERVED_DATES, RESERVED_MEETINGS


def audit_inventory_provenance(db, raw_directory):
    """Reconstruct v2 metadata from original inventory bytes, read-only."""
    version = db.execute('PRAGMA user_version').fetchone()[0]
    report = {'warehouse_schema': version, 'inventory_provenance_verified': False,
              'inventory_metadata_rows_verified': 0, 'inventory_metadata_meetings_verified': 0,
              'inventory_metadata_runs_verified': 0}
    if version == 1:
        return report
    if version != 2:
        raise ValueError('Unsupported inventory audit version')
    rows = db.execute('''SELECT m.*,r.run_id FROM inventory_meetings m
                         JOIN inventory_receipts r ON r.receipt_id=m.receipt_id
                         ORDER BY r.run_id,m.receipt_id,m.meeting_id''').fetchall()
    by_inventory = {}
    fields = ('meeting_id','date','title','body','source_url','json_url','source_status')
    for row in rows:
        if row['date'] in RESERVED_DATES or row['meeting_id'] in RESERVED_MEETINGS:
            raise ValueError('Reserved inventory metadata cannot be audited')
        by_inventory.setdefault((row['run_id'], row['date']), []).append(row)
    for (run_id, day), observations in by_inventory.items():
        coverage = db.execute('SELECT status FROM coverage WHERE run_id=? AND meeting_id=?',
                              (run_id, 'inventory:'+day)).fetchone()
        if coverage is None or coverage['status'] != 'inventory_complete':
            raise ValueError('Inventory metadata lacks original complete receipts')
        pages = db.execute('SELECT * FROM inventory_receipts WHERE run_id=? AND date=? ORDER BY page',
                           (run_id, day)).fetchall()
        originals = {}; seen = set(); total = None
        for number, receipt in enumerate(pages, 1):
            path = Path(raw_directory)/(receipt['raw_sha256']+'.json')
            if path.is_symlink() or path.stat().st_size != receipt['byte_count'] or file_sha(path) != receipt['raw_sha256']:
                raise ValueError('Original inventory integrity failed')
            payload = json.loads(path.read_bytes().decode('utf-8-sig'))
            if (not isinstance(payload, dict) or receipt['page'] != number
                    or type(payload.get('page')) is not int or payload['page'] != number
                    or type(payload.get('total')) is not int or payload['total'] < 0
                    or type(payload.get('hasMore')) is not bool
                    or payload['hasMore'] != (number < len(pages))
                    or not isinstance(payload.get('meetings'), list)):
                raise ValueError('Incomplete original inventory')
            if total is not None and total != payload['total']:
                raise ValueError('Changing original inventory total')
            total = payload['total']
            for item in payload['meetings']:
                value = _meeting(item, day); mid = value['meeting_id']
                if mid in seen:
                    raise ValueError('Duplicate original inventory identity')
                seen.add(mid); originals[(receipt['receipt_id'], mid)] = value
        if len(seen) != total:
            raise ValueError('Incomplete original inventory count')
        for row in observations:
            value = {key:row[key] for key in fields}
            value['has_transcript'] = bool(row['has_transcript'])
            if (row['has_transcript'] not in (0,1) or row['normalization_version'] != 'un.inventory-normalization.v1'
                    or value != originals.get((row['receipt_id'], row['meeting_id']))):
                raise ValueError('Inventory metadata differs from original complete receipts')
    report.update(inventory_provenance_verified=True, inventory_metadata_rows_verified=len(rows),
                  inventory_metadata_meetings_verified=len({row['meeting_id'] for row in rows}),
                  inventory_metadata_runs_verified=len({row['run_id'] for row in rows}))
    return report


def audit_restored_exports(snapshot, output):
    snapshot, output = Path(snapshot), Path(output)
    if output.resolve().is_relative_to(snapshot.resolve()):
        raise ValueError('Replay must be outside the immutable snapshot')
    manifest = verify_snapshot(snapshot)
    expected = {item['path']: item['sha256'] for item in manifest['files']
                if item['path'].startswith(('private/', 'public/'))}
    if not expected or 'private/manifest.json' not in expected:
        raise ValueError('Snapshot has no research export contract')
    # The original restored database is never migrated or opened for writing.
    with closing(sqlite3.connect(snapshot.joinpath('warehouse.sqlite3').resolve().as_uri() + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        if [r[0] for r in db.execute('PRAGMA integrity_check')] != ['ok']:
            raise ValueError('Restored database integrity failed')
        if db.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('Restored database foreign keys failed')
        inventory = audit_inventory_provenance(db, snapshot/'raw')
        export_snapshot(SimpleNamespace(db=db), output, manifest['snapshot_id'], manifest['generated_at'])
    actual = {file.relative_to(output).as_posix(): file_sha(file)
              for file in output.rglob('*') if file.is_file()}
    if actual != expected:
        # Paths, contents and source-bearing differences stay out of job logs.
        raise ValueError('Restored exports do not reproduce under this exporter version')
    verify_snapshot(snapshot)
    private = json.loads((snapshot/'private/manifest.json').read_bytes())
    return {'schema': 'un.restored-export-audit.v1', 'status': 'passed', **inventory,
            'snapshot_id': manifest['snapshot_id'], 'generated_at': manifest['generated_at'],
            'export_files_verified': len(expected),
            'csv_files_verified': sum(path.endswith('.csv') for path in expected),
            'csv_rows_verified': sum(table['rows'] for table in private['tables']),
            'database_read_only': True, 'integrity_check': True, 'foreign_key_check': True,
            'byte_identical_exports': True, 'source_content_in_receipt': False}
