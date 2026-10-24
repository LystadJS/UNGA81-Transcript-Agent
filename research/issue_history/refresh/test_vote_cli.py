import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from ..store import IssueStore
from .vote_cli import ingest_votes


class PrivateVoteCliTests(unittest.TestCase):
    def test_bounded_private_unbound_roundtrip(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            base = Path(directory)
            source = base / "source.csv"
            source.write_bytes(b"Invented CSV fixture only\n")
            rows = [dict(resolution_id="A/RES/FIXTURE",resolution_version="1",stage="adopted_resolution",country_id="Example",
                date="2024-01-01",source_url="https://digitallibrary.un.org/record/fixture",vote="unknown",eligible=None,
                raw_vote_code="X",country_code="XXX")]
            normalized = base / "normalized.json"
            normalized.write_text(json.dumps(rows), encoding="utf-8")
            options = dict(normalized_file=normalized, source_file=source, expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                database=base / "history.sqlite", checkpoint=base / "cursor.json", provenance_file=base / "provenance.json", year=2024)
            result = ingest_votes(**options)
            self.assertTrue(result["complete"])
            self.assertEqual("private_only", result["publication"])
            self.assertEqual("withheld_unbound", result["policy_binding"])
            ingest_votes(**options)
            store = IssueStore(options["database"])
            try:
                records = store.db.execute("SELECT payload FROM evidence").fetchall()
                self.assertEqual(1, len(records))
                vote = json.loads(records[0][0])
                self.assertEqual("unknown", vote["vote"])
                self.assertIsNone(vote["eligible"])
                self.assertEqual("X", vote["raw_vote_code"])
                self.assertEqual("unbound", vote["policy"])
                self.assertEqual(0, store.export_bundle(base / "test-export", "test")["counts"]["votes"])
            finally:
                store.close()
            with self.assertRaises(ValueError):
                ingest_votes(**{**options,"expected_sha256":"0"*64})
            with self.assertRaises(ValueError):
                ingest_votes(**{**options,"year":2025})


if __name__ == "__main__":
    unittest.main()
