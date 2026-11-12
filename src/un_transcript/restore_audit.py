"""Read-only verification that restored research exports reproduce from SQLite."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

from .exports import export_snapshot
from .snapshots import file_sha, verify_snapshot


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
        export_snapshot(SimpleNamespace(db=db), output, manifest['snapshot_id'], manifest['generated_at'])
    actual = {file.relative_to(output).as_posix(): file_sha(file)
              for file in output.rglob('*') if file.is_file()}
    if actual != expected:
        # Paths, contents and source-bearing differences stay out of job logs.
        raise ValueError('Restored exports do not reproduce under this exporter version')
    verify_snapshot(snapshot)
    private = json.loads((snapshot/'private/manifest.json').read_bytes())
    return {'schema': 'un.restored-export-audit.v1', 'status': 'passed',
            'snapshot_id': manifest['snapshot_id'], 'generated_at': manifest['generated_at'],
            'export_files_verified': len(expected),
            'csv_files_verified': sum(path.endswith('.csv') for path in expected),
            'csv_rows_verified': sum(table['rows'] for table in private['tables']),
            'database_read_only': True, 'integrity_check': True, 'foreign_key_check': True,
            'byte_identical_exports': True, 'source_content_in_receipt': False}
