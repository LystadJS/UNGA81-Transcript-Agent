"""Invented tar archives test exact Harvard v14 identity and refusal gates."""
from __future__ import annotations
import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

from research.integration.p3_harvard_archive_audit import verify


def make_tar(path, entries):
    with tarfile.open(path,"w:gz") as z:
        for name, text in entries:
            b=text.encode()
            record=tarfile.TarInfo(name=name)
            record.size=len(b)
            z.addfile(record,io.BytesIO(b))


def inspect_fake(path):
    raw=path.read_bytes()
    return verify(path,expected_sha=hashlib.sha256(raw).hexdigest(),
                  expected_md5=hashlib.md5(raw,usedforsecurity=False).hexdigest(),
                  strict=False)


class HarvardV14ArchiveTests(unittest.TestCase):
    def test_invented_archive_sha_and_source_count(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"fake.tar.gz"
            make_tar(f,[("UNGDC_1946-2025/USA_71_2016.txt","invented text"),
                        ("UNGDC_1946-2025/CAN_72_2017.txt","synthetic text")])
            out=inspect_fake(f)
            self.assertEqual(out["country_speeches_2016_2025"],2)
            self.assertEqual(out["country_speeches_by_year_2016_2025"]["2016"],1)
            self.assertEqual(out["country_speeches_by_year_2016_2025"]["2017"],1)
            self.assertFalse(out["W1_real_source_frame_independently_validated"])
            self.assertEqual(out["W4_model_fit"],"WITHHELD")

    def test_wrong_exact_sha_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"fake.tar.gz"
            make_tar(f,[("USA_71_2016.txt","fake")])
            with self.assertRaisesRegex(ValueError,"SHA256 or MD5"):
                verify(f)

    def test_duplicate_country_session_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"fake.tar.gz"
            make_tar(f,[("x/USA_71_2016.txt","a"),("y/USA_71_2016.txt","b")])
            with self.assertRaisesRegex(ValueError,"Duplicate"):
                inspect_fake(f)

    def test_wrong_session_year_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"fake.tar.gz"
            make_tar(f,[("USA_71_2024.txt","fake")])
            with self.assertRaisesRegex(ValueError,"session/year"):
                inspect_fake(f)

    def test_path_traversal_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"fake.tar.gz"
            make_tar(f,[("../USA_71_2016.txt","fake")])
            with self.assertRaisesRegex(ValueError,"traversal"):
                inspect_fake(f)

    def test_link_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"fake.tar.gz"
            with tarfile.open(f,"w:gz") as z:
                t=tarfile.TarInfo("USA_71_2016.txt")
                t.type=tarfile.SYMTYPE
                t.linkname="/etc/passwd"
                z.addfile(t)
            with self.assertRaisesRegex(ValueError,"link or device"):
                inspect_fake(f)


if __name__ == "__main__":
    unittest.main()
