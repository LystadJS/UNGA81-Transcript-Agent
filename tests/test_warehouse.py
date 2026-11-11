import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from un_transcript.warehouse import Warehouse


def meeting():
    return dict(meeting_id="ga/81/synthetic",date="2026-11-01",title="Synthetic meeting",
                body="GA",source_url="https://transcripts.un.org/en/ga/81/synthetic",
                json_url="https://transcripts.un.org/en/ga/81/synthetic.json")


def segments(text="We support humanitarian access."):
    return [dict(text=text,language="en",speaker="Invented speaker",country="XXX",
                 capacity="unknown",json_pointer="/transcript/data/0")]


class WarehouseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Warehouse(Path(self.temp.name)/"warehouse.sqlite")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def ingest(self,text="We support humanitarian access.",when="2026-11-01T12:00:00Z"):
        return self.store.ingest(meeting(),json.dumps({"synthetic":text}).encode(),segments(text),when)

    def test_idempotent_reingestion_and_exact_raw_bytes(self):
        revision = self.ingest()
        self.assertEqual(revision,self.ingest(when="2026-11-01T13:00:00Z"))
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM source_revisions").fetchone()[0],1)
        row = self.store.db.execute("SELECT raw_path FROM source_revisions").fetchone()
        self.assertEqual((self.store.path.parent/row[0]).read_bytes(),json.dumps({"synthetic":"We support humanitarian access."}).encode())

    def test_revised_source_preserves_history_and_excludes_old_predictions(self):
        first = self.ingest()
        segment = self.store.current_segments()[0]
        self.store.upsert_issue(dict(issue_id="access",version="1",label="Access",definition="Humanitarian access"))
        pid = self.store.add_prediction(dict(revision_id=first,segment_id=segment["segment_id"],issue_id="access",issue_version="1",model_version="synthetic-only",stance="support",status="unvalidated",created_at="2026-11-01T12:01:00Z",evidence=[{"start":0,"end":len(segment["text"]),"quote":segment["text"]}]))
        second = self.ingest("We oppose blocking humanitarian access.","2026-11-02T12:00:00Z")
        self.assertNotEqual(first,second)
        self.assertEqual(len(self.store.current_segments()),1)
        self.assertEqual(self.store.current_segments()[0]["revision_id"],second)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM predictions WHERE prediction_id=?",(pid,)).fetchone()[0],1)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM predictions p JOIN meetings m ON m.current_revision=p.revision_id").fetchone()[0],0)
        with self.assertRaisesRegex(ValueError,"Historical revision"):
            self.ingest(when="2026-11-03T12:00:00Z")

    def test_invalid_batch_keeps_current_pointer(self):
        revision = self.ingest()
        invalid = segments() * 2
        invalid[0] = {**invalid[0],"segment_id":"same"}
        invalid[1] = {**invalid[1],"segment_id":"same"}
        with self.assertRaises(ValueError):
            self.store.ingest(meeting(),b'{}',invalid,"2026-11-02T12:00:00Z")
        self.assertEqual(self.store.current_segments()[0]["revision_id"],revision)
        self.assertEqual(self.store.db.execute("PRAGMA foreign_key_check").fetchall(),[])

    def test_foreign_keys_and_run_history(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.record_coverage("missing","unknown","failed")
        self.store.start_run("run1",{"synthetic":True},"2026-11-01T12:00:00Z")
        self.store.record_coverage("run1","ga/unknown","not_published")
        self.store.finish_run("run1","partial","2026-11-01T12:01:00Z")
        with self.assertRaises(ValueError):
            self.store.finish_run("run1","complete","2026-11-01T12:02:00Z")

    def test_evidence_must_match_and_abstention_is_not_neutral(self):
        revision = self.ingest()
        segment = self.store.current_segments()[0]
        self.store.upsert_issue(dict(issue_id="access",version="1",label="Access",definition="Humanitarian access"))
        base = dict(revision_id=revision,segment_id=segment["segment_id"],issue_id="access",issue_version="1",model_version="synthetic-only",created_at="2026-11-01T12:01:00Z")
        with self.assertRaises(ValueError):
            self.store.add_prediction(dict(base,stance="support",evidence=[{"start":0,"end":2,"quote":"No"}]))
        with self.assertRaises(ValueError):
            self.store.add_prediction(dict(base,status="abstained",stance="neutral"))
        self.store.add_prediction(dict(base,status="abstained",stance=None))
        with self.assertRaises(ValueError):
            self.store.upsert_issue(dict(issue_id="access",version="1",label="Changed",definition="Changed"))

    def test_unrelated_database_is_not_migrated(self):
        path = Path(self.temp.name)/"research.sqlite"
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE frozen(value TEXT)")
        with self.assertRaises(ValueError):
            Warehouse(path)

    def test_headers_do_not_store_authentication(self):
        self.store.ingest(meeting(),b'{}',[],"2026-11-01T12:00:00Z",{"ETag":"123","Authorization":"secret","Set-Cookie":"private"})
        headers = json.loads(self.store.db.execute("SELECT headers_json FROM source_revisions").fetchone()[0])
        self.assertEqual(headers,{"etag":"123"})

    def test_inventory_receipts_and_analysis_are_atomic(self):
        revision = self.ingest()
        segment = self.store.current_segments()[0]
        self.store.start_run("inventory-run",{},"2026-11-01T12:00:00Z")
        entry = dict(date="2026-11-01",page=1,source_url="https://transcripts.un.org/en/meetings.json",raw=b'{"meetings":[]}',headers={},retrieved_at="2026-11-01T12:00:00Z")
        rid = self.store.record_inventory("inventory-run",entry)
        self.assertEqual(rid,self.store.record_inventory("inventory-run",entry))
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM inventory_receipts").fetchone()[0],1)
        analysis = {"issues":[dict(issue_id="access",version="1",label="Access",definition="Access question")],
                    "issue_candidates":[dict(candidate_id="good",source_id=revision,segment_id=segment["segment_id"],issue_id="access",catalog_version="1",status="retrieval_candidate_not_stance")],
                    "predictions":[dict(revision_id="missing",segment_id="missing")],
                    "model_status":{"accepted":False}}
        with self.assertRaises(ValueError):
            self.store.record_analysis(analysis,created_at="2026-11-01T12:01:00Z",run_id="inventory-run")
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM issues").fetchone()[0],0)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM issue_candidates").fetchone()[0],0)


if __name__ == "__main__":
    unittest.main()
