import hashlib
import unittest
from .adapters import transcript_record,vote_record,SourceError,bind_resolution,vote_to_store
from .runner import run_batch,run_checkpointed

class IngestionTests(unittest.TestCase):
    def row(self):
        text="Synthetic statement."
        return dict(id="fixture",date="2024-01-01",country="Kenya",language="en",text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest(),source_url="https://transcripts.un.org/en/fixture")
    def test_hash_and_metadata_revision(self):
        row=self.row(); first=transcript_record(row)
        self.assertNotEqual(first["source_revision_id"],transcript_record({**row,"country":"Ghana"})["source_revision_id"])
        with self.assertRaises(SourceError): transcript_record({**row,"text":"corrupted"})
    def test_resume_quarantine_and_snapshot(self):
        rows=[self.row(),{**self.row(),"text":"bad"},self.row()]; saved=[]
        a=run_batch(rows,transcript_record,saved.append,limit=1)
        self.assertEqual(a["cursor"],1)
        b=run_batch(rows,transcript_record,saved.append,a,limit=2)
        self.assertTrue(b["complete"]);self.assertEqual(b["coverage"]["accepted"],2);self.assertEqual(len(b["quarantine"]),1)
        with self.assertRaises(ValueError): run_batch(rows[:1],transcript_record,saved.append,b)
    def test_retry_retains_cursor(self):
        def fail(item): raise OSError("temporary")
        state=None
        for _ in range(3): state=run_batch([self.row()],transcript_record,fail,state)
        self.assertTrue(state["complete"]);self.assertEqual(state["accepted"],0)
    def test_vote_categories(self):
        v=dict(resolution_id="S/RES/FIXTURE",resolution_version="1",stage="adopted_resolution",country_id="Kenya",date="2024-01-01",source_url="https://digitallibrary.un.org/record/fixture",eligible=True,vote="abstain")
        self.assertEqual(vote_record(v)["vote"],"abstain")
        for vote in ("consensus","not_eligible"):
            with self.assertRaises(SourceError): vote_record({**v,"vote":vote})
    def test_policy_binding_confirmation_and_context(self):
        row=dict(resolution_id="FIXTURE",resolution_version="1",stage="adopted_resolution",policy_id="humanitarian_access",context_id="unspecified",source_url="https://digitallibrary.un.org/record/fixture",rationale="Synthetic explicit operative access clause",review_state="assistant_provisional")
        self.assertFalse(bind_resolution(row)["comparable"])
        with self.assertRaises(SourceError): bind_resolution({**row,"review_state":"owner_confirmed"})
        self.assertTrue(bind_resolution({**row,"context_id":"sudan"})["comparable"])
    def test_atomic_checkpoint_resume(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path=Path(directory)/"checkpoint.json"; saved=[];rows=[self.row(),self.row()]
            run_checkpointed(rows,transcript_record,saved.append,path,limit=1)
            state=run_checkpointed(rows,transcript_record,saved.append,path,limit=1)
            self.assertTrue(state["complete"]);self.assertEqual(len(saved),2)
            self.assertNotIn("Synthetic statement",path.read_text())
    def test_vote_store_binding_identity(self):
        row=dict(resolution_id="FIXTURE",resolution_version="2",stage="adopted_resolution",country_id="Kenya",date="2024-01-01",source_url="https://digitallibrary.un.org/record/fixture",eligible=True,vote="yes")
        binding=dict(resolution_id="FIXTURE",resolution_version="2",stage="adopted_resolution",policy_id="humanitarian_access",context_id="sudan",source_url=row["source_url"],rationale="Synthetic operative clause",review_state="assistant_provisional")
        event=vote_to_store(row,binding,"source","canonical-revision")
        self.assertEqual(event["country"],"Kenya");self.assertEqual(event["resolution_version"],"2");self.assertTrue(event["eligible"])
        with self.assertRaises(SourceError):vote_to_store(row,{**binding,"resolution_version":"1"},"source","revision")
    def test_bounded_catalog_discovery(self):
        from .discovery import discover_downloads
        result=discover_downloads("ga_adopted_votes",'<a href="/files/fixture.csv">Data</a><a href="https://evil.invalid/f.csv">External</a>')
        self.assertEqual(result["candidate_downloads"],["https://digitallibrary.un.org/files/fixture.csv"])
        self.assertEqual(result["adapter_status"],"remote_format_unverified")
        with self.assertRaises(ValueError):discover_downloads("ga_adopted_votes","x"*300000)
    def test_vote_adapter_database_roundtrip(self):
        import json,tempfile
        from pathlib import Path
        from ..store.repository import IssueStore
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            store=IssueStore(Path(directory)/"votes.sqlite")
            try:
                revision=store.upsert_source(dict(id="vote-source",published_date="2024-01-01",body="GA",family="synthetic_votes",url="https://digitallibrary.un.org/record/fixture",content_hash="a"*64,access="public_approved"))
                row=dict(resolution_id="FIXTURE",resolution_version="2",stage="adopted_resolution",country_id="Kenya",date="2024-01-01",source_url="https://digitallibrary.un.org/record/fixture",eligible=True,vote="abstain")
                binding=dict(resolution_id="FIXTURE",resolution_version="2",stage="adopted_resolution",policy_id="humanitarian_access",context_id="sudan",source_url=row["source_url"],rationale="Synthetic operative clause",review_state="assistant_provisional")
                event=vote_to_store(row,binding,"vote-source",revision)
                store.put_vote(event);store.put_vote(event)
                target=Path(directory)/"bundle";manifest=store.export_bundle(target,"test-vote-v1")
                data=json.loads((target/manifest["shards"][0]["url"]).read_text())
                self.assertEqual(len(data["votes"]),1)
                self.assertEqual(data["votes"][0]["resolution_version"],"2")
                self.assertTrue(data["votes"][0]["eligible"])
                self.assertEqual(data["votes"][0]["vote"],"abstain")
            finally:store.close()
    def test_official_transcript_inventory_metadata(self):
        import json
        from .discovery import transcript_inventory
        item=dict(slug="ga/c3/81/1",date="2026-10-01T00:00:00.000Z",body="Third Committee",category="General Assembly",hasTranscript=True,pageUrl="/en/ga/c3/81/1",jsonUrl="/en/ga/c3/81/1.json",textUrl="/en/ga/c3/81/1.txt")
        data=dict(page=1,total=1,hasMore=False,meetings=[item])
        result=transcript_inventory(json.dumps(data).encode(),"2026-10-01")
        self.assertEqual(result["meetings"][0]["body"],"GA_C3")
        self.assertFalse(result["transcript_text_fetched"])
        data["meetings"][0]["jsonUrl"]="/en/sc/999.json"
        with self.assertRaises(ValueError):transcript_inventory(json.dumps(data).encode(),"2026-10-01")
        empty=transcript_inventory(json.dumps(dict(page=1,total=0,hasMore=False,meetings=[])).encode(),"2016-09-22")
        self.assertEqual(empty["availability"],"no_entries_returned_not_verified_absence")
if __name__=="__main__": unittest.main()
