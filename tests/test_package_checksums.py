"""Protect the tracked package inventory from runtime data and accidental rewrites."""
import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('package_checksums', Path(__file__).resolve().parents[1] / 'tools/package_checksums.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PackageChecksumTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.git('init', '--quiet', '--initial-branch=main')
        (self.root / 'un').mkdir()
        (self.root / '.gitignore').write_text('/un/output/\n')
        (self.root / 'un/README.md').write_text('abc')
        (self.root / 'un/SHA256SUMS_D1_I4_ORIGINAL.txt').write_text('frozen original\n')
        self.manifest = self.root / 'un/SHA256SUMS.txt'
        self.manifest.write_text('')
        self.git('add', '.')
        for name, value in [('ROOT', self.root), ('MANIFEST', self.manifest)]:
            target = patch.object(MODULE, name, value)
            target.start()
            self.addCleanup(target.stop)

    def git(self, *args):
        subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def run_tool(self, write=False):
        with patch('sys.argv', ['package_checksums.py', *(['--write'] if write else [])]), contextlib.redirect_stdout(io.StringIO()):
            MODULE.main()

    def test_refresh_and_check_preserve_original(self):
        self.run_tool(True)
        self.assertIn('ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad  README.md\n', self.manifest.read_text())
        self.assertEqual((self.root / 'un/SHA256SUMS_D1_I4_ORIGINAL.txt').read_text(), 'frozen original\n')
        self.assertEqual(len(self.manifest.read_text().splitlines()), 2)
        self.run_tool()

    def test_runtime_private_output_is_excluded(self):
        (self.root / 'un/output').mkdir()
        (self.root / 'un/output/private.json').write_text('PRIVATE SOURCE')
        self.run_tool(True)
        self.assertNotIn('output/', self.manifest.read_text())
        self.assertNotIn('PRIVATE SOURCE', self.manifest.read_text())
        self.run_tool()

    def test_unstaged_change_cannot_refresh_silently(self):
        self.run_tool(True)
        before = self.manifest.read_bytes()
        (self.root / 'un/README.md').write_text('unreviewed change')
        with self.assertRaisesRegex(ValueError, 'Stage intended'):
            self.run_tool(True)
        self.assertEqual(self.manifest.read_bytes(), before)
        with self.assertRaisesRegex(ValueError, 'differ'):
            self.run_tool()

    def test_staged_addition_and_deletion_update_inventory(self):
        (self.root / 'un/README.md').unlink()
        self.git('add', '-u', 'un/README.md')
        (self.root / 'un/current.R').write_text('invisible(TRUE)\n')
        self.git('add', 'un/current.R')
        self.run_tool(True)
        self.assertNotIn('README.md', self.manifest.read_text())
        self.assertIn('current.R', self.manifest.read_text())
        self.run_tool()

    def test_missing_tracked_payload_is_rejected(self):
        (self.root / 'un/README.md').unlink()
        with self.assertRaisesRegex(ValueError, 'Stage package'):
            MODULE.inventory()

    def test_symlink_cannot_include_external_data(self):
        outside = self.root / 'outside.txt'
        outside.write_text('PRIVATE OUTSIDE DATA')
        try:
            (self.root / 'un/link').symlink_to(outside)
        except OSError:
            self.skipTest('Symlinks unavailable')
        self.git('add', 'un/link')
        with self.assertRaisesRegex(ValueError, 'resolve conflicts'):
            MODULE.inventory()


if __name__ == '__main__':
    unittest.main()
