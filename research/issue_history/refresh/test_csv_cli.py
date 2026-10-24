import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import gzip
from types import SimpleNamespace
from unittest.mock import patch
from ..ingest.ga_votes import HEADERS
from ..store import IssueStore
from .csv_cli import ingest_csv
from .vote_cli import file_hash
from .review_cursor import review_cursor


class CsvCliTests(unittest.TestCase):
    @patch('research.issue_history.refresh.csv_cli.shutil.disk_usage', return_value=SimpleNamespace(free=10_000_000_000))
    def test_offset_resume_multiline_and_idempotency(self, _disk):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            base = Path(directory)
            source = base / "fixture.csv"
            with source.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream,fieldnames=HEADERS)
                writer.writeheader()
                for index,date in enumerate(("2024-01-01","2024-01-02","2010-01-01")):
                    row = dict.fromkeys(HEADERS, "")
                    row.update(undl_id="1",ms_code="AAA",ms_name="Example",ms_vote="X",date=date,resolution="A/RES/EXAMPLE"+str(index),undl_link="https://digitallibrary.un.org/record/1",title="Synthetic\nmultiline title")
                    writer.writerow(row)
            args = dict(source_file=source,expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                database=base / "history.sqlite",checkpoint=base / "cursor.json",provenance_file=base / "provenance.json",
                start="2024-01-01",end="2024-12-31",batch_size=1,max_batches=1)
            first = ingest_csv(**args)
            self.assertFalse(first["complete"])
            self.assertEqual(1,first["accepted"])
            compressed = base / "fixture.csv.gz"
            with gzip.open(compressed, 'wb') as stream:
                stream.write(source.read_bytes())
            args["source_file"] = compressed
            second = ingest_csv(**args)
            self.assertEqual(2,second["accepted"])
            third = ingest_csv(**args)
            self.assertTrue(third["complete"])
            self.assertEqual(3,third["scanned"])
            self.assertEqual(1,third["out_of_window"])
            repeated = ingest_csv(**args)
            self.assertEqual({k:v for k,v in third.items() if k != "free_bytes"}, {k:v for k,v in repeated.items() if k != "free_bytes"})
            store = IssueStore(args["database"])
            try:
                self.assertEqual(2,store.db.execute("SELECT count(*) FROM evidence").fetchone()[0])
            finally:
                store.close()
            with self.assertRaises(ValueError):
                ingest_csv(**{**args,"start":"2023-01-01"})
            def changed_dependency(path):
                return 'f'*64 if Path(path).name == 'adapters.py' else file_hash(path)
            with patch('research.issue_history.refresh.csv_cli.file_hash',side_effect=changed_dependency):
                with self.assertRaisesRegex(ValueError,'checkpoint input/window changed'):
                    ingest_csv(**args)
            with patch('research.issue_history.refresh.csv_cli.shutil.disk_usage',return_value=SimpleNamespace(free=209_715_200)):
                blocked = ingest_csv(**{**args,"checkpoint":base / "blocked-cursor.json"})
                self.assertTrue(blocked['storage_reserve_reached'])
                self.assertEqual(0,blocked['accepted'])
                self.assertFalse(blocked['complete'])
            saved = json.loads(args['checkpoint'].read_bytes())
            saved['identity'].pop('source_hashes')
            saved['identity']['adapter_sha256'] = '0'*64
            args['checkpoint'].write_text(json.dumps(saved),encoding='utf-8')
            receipt = review_cursor(source_file=compressed,database=args['database'],checkpoint=args['checkpoint'],receipt_file=base/'review.json')
            self.assertEqual('engineering_replay_verified',receipt['review_state'])
            self.assertEqual(2,receipt['verified_rows'])
            self.assertEqual(saved['offset'],json.loads(args['checkpoint'].read_bytes())['offset'])
            unchanged = args['checkpoint'].read_bytes()
            ledger = IssueStore(args['database'])
            with ledger.transaction():
                ledger.db.execute("UPDATE evidence SET payload=json_set(payload,'$.vote','no')")
            ledger.close()
            with self.assertRaisesRegex(ValueError,'evidence fields differ'):
                review_cursor(source_file=compressed,database=args['database'],checkpoint=args['checkpoint'],receipt_file=base/'bad-review.json')
            self.assertEqual(unchanged,args['checkpoint'].read_bytes())


if __name__ == "__main__":
    unittest.main()
