"""Synthetic notice text verifies retention; no actual model training occurs."""
from pathlib import Path
import tempfile
import unittest
from un_transcript.models.notices import load_upstream_notices, preserve_upstream_notices
from un_transcript.models.contracts import digest


class Notices(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.base=self.root/'base';self.base.mkdir()
        (self.base/'LICENSE').write_bytes(b'Synthetic license fixture only.\n')
        (self.base/'README.md').write_bytes(b'---\nlicense: apache-2.0\n---\nSynthetic model card.\n')
        self.out=self.root/'candidate';self.out.mkdir()

    def tearDown(self):self.tmp.cleanup()

    def test_exact_bytes_hashes_and_declared_scope_are_retained(self):
        (self.base/'NOTICE').write_bytes(b'Synthetic additional notice.\n')
        record,files=load_upstream_notices(self.base,'a'*40)
        preserve_upstream_notices(self.out,files)
        self.assertEqual(record['declared_license'],'apache-2.0')
        self.assertIn('no UN transcript',record['scope'])
        for name,data in files.items():
            self.assertEqual((self.out/name).read_bytes(),data)
            self.assertEqual(record['notice_sha256'][name],digest(data))
        self.assertEqual(len(files),3)

    def test_resume_preserves_exact_notices_and_rejects_replacement(self):
        _,files=load_upstream_notices(self.base,'a'*40)
        preserve_upstream_notices(self.out,files);preserve_upstream_notices(self.out,files)
        (self.out/'UPSTREAM_LICENSE').write_bytes(b'changed')
        with self.assertRaises(ValueError):preserve_upstream_notices(self.out,files)
        self.assertEqual((self.out/'UPSTREAM_LICENSE').read_bytes(),b'changed')

    def test_missing_license_and_undeclared_model_card_fail_closed(self):
        (self.base/'README.md').write_text('No declared license')
        with self.assertRaises(ValueError):load_upstream_notices(self.base,'a'*40)
        (self.base/'LICENSE').unlink()
        with self.assertRaises(ValueError):load_upstream_notices(self.base,'a'*40)

    def test_symlink_oversize_and_mutable_revision_rejected(self):
        with self.assertRaises(ValueError):load_upstream_notices(self.base,'main')
        (self.base/'LICENSE').unlink();(self.base/'LICENSE').symlink_to(self.base/'README.md')
        with self.assertRaises(ValueError):load_upstream_notices(self.base,'a'*40)
        (self.base/'LICENSE').unlink();(self.base/'LICENSE').write_bytes(b'x'*(1024*1024+1))
        with self.assertRaises(ValueError):load_upstream_notices(self.base,'a'*40)
