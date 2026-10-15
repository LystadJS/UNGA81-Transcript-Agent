"""Metadata-only ownership guard for this C0 commit, not a repository content scan."""
import json
import subprocess
import sys
import re

PREFIXES = ('research/integration/product_contracts/',)
EXACT = {
    '.github/workflows/c0-product-contracts.yml',
    'docs/parallel-work/C0_PRODUCT_OWNERSHIP.md',
    'docs/parallel-work/C0_WORKER_HANDOFFS.md',
    'docs/parallel-work/C0_IMPLEMENTATION_ACCEPTANCE_2026-10-15.md',
    'docs/parallel-work/c0-ownership.json',
}

def allowed(path):
    return (not path.startswith('/') and '\\' not in path and
            all(part not in ('.', '..') for part in path.split('/')) and
            (path in EXACT or path.startswith(PREFIXES)))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python guard_changes.py BASE_COMMIT')
    base = sys.argv[1]
    if not re.fullmatch(r'[a-f0-9]{40}', base):
        raise SystemExit('Expected immutable base commit SHA')
    raw = subprocess.check_output(['git', 'diff', '--name-only', '-z', base + '...HEAD'])
    paths = [p.decode('utf8') for p in raw.split(b'\0') if p]
    if not paths or not all(allowed(p) for p in paths):
        raise SystemExit('C0 path ownership violation or empty change set')
    for path in paths:
        tree = subprocess.check_output(['git', 'ls-tree', 'HEAD', '--', path]).decode()
        if not tree.startswith('100644 blob '):
            raise SystemExit('Deleted/nonregular C0 path: ' + path)
    print(json.dumps({'changed_files': len(paths), 'owned_paths': True,
                      'frozen_shared_changes': 0, 'private_source_reads': 0}))
