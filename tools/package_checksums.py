"""Check or refresh the current tracked R-package inventory; never alter old receipts."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'un' / 'SHA256SUMS.txt'


def inventory() -> str:
    records = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '--stage', '-z', '--', 'un/']).split(b'\0')
    rows = []
    for record in records:
        if not record:
            continue
        metadata, raw_path = record.split(b'\t', 1)
        mode, _, stage = metadata.decode().split()
        path = ROOT / raw_path.decode('utf-8')
        if path == MANIFEST:
            continue
        if stage != '0' or mode not in ('100644', '100755') or path.is_symlink() or not path.is_file():
            raise ValueError('Stage package additions/deletions and resolve conflicts first: ' + str(path.relative_to(ROOT)))
        relative = path.relative_to(ROOT / 'un').as_posix()
        rows.append((relative, hashlib.sha256(path.read_bytes()).hexdigest()))
    if not rows:
        raise ValueError('No tracked R-package payload found')
    return ''.join(digest + '  ' + relative + '\n' for relative, digest in sorted(rows))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='refresh only un/SHA256SUMS.txt after staging package changes')
    args = parser.parse_args()
    content = inventory()
    if args.write:
        unstaged = subprocess.check_output(['git', '-C', str(ROOT), 'diff', '--name-only', '-z', '--', 'un/']).split(b'\0')
        if any(p and p != b'un/SHA256SUMS.txt' for p in unstaged):
            raise ValueError('Stage intended package changes before refreshing checksums')
        MANIFEST.write_text(content, encoding='utf-8', newline='\n')
    elif MANIFEST.read_text(encoding='utf-8') != content:
        raise ValueError('Current package checksums or tracked inventory differ; review changes before using --write')
    print(('Updated' if args.write else 'Verified') + ' ' + str(len(content.splitlines())) + ' tracked R-package checksums; historical records unchanged')


if __name__ == '__main__':
    main()
