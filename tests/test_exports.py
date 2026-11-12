import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from un_transcript.warehouse import Warehouse
from un_transcript.exports import export_snapshot


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Warehouse(self.root/"warehouse.sqlite")
        self.meeting = dict(meeting_id="ga/81/synthetic",date="2026-11-01",title="Synthetic meeting",body="GA",source_url="https://transcripts.un.org/en/ga/81/synthetic",json_url="https://transcripts.un.org/en/ga/81/synthetic.json")
        self.secret_text = 'Private synthetic text, with "quotes" and\nnewlines: support.'
        self.revision = self.store.ingest(self.meeting,b'{"synthetic":"raw-private-marker"}',[dict(text=self.secret_text,language="en",speaker="private-speaker-marker",country="XXX",capacity="unknown",json_pointer="/transcript/data/0")],"2026-11-01T12:00:00Z")
        self.store.start_run("run1",{"synthetic":True},"2026-11-01T12:00:00Z")
        self.store.record_coverage("run1",self.meeting["meeting_id"],"collected","private-detail-marker")
        self.store.record_coverage("run1","ga/unavailable","not_published","private-failure-marker")
        self.store.finish_run("run1","partial","2026-11-01T12:01:00Z")

    def tearDown(self):
        self.store.close();self.temp.cleanup()

    def test_snapshot_privacy_and_csv_roundtrip(self):
        output = self.root/"snapshot"
        manifest = export_snapshot(self.store,output,"snapshot-1","2026-11-01T12:02:00Z")
        self.assertEqual(manifest["schema"],"un.archive.v1")
        self.assertEqual(manifest["status"],"partial")
        self.assertEqual(manifest["model_status"],"not_validated")
        public_bytes = b"".join(p.read_bytes() for p in (output/"public").rglob("*") if p.is_file())
        for private in (self.secret_text,"private-speaker-marker","raw-private-marker","private-detail-marker","private-failure-marker"):
            self.assertNotIn(private.encode(),public_bytes)
        with (output/"private/segments.csv").open(newline="",encoding="utf-8") as stream:
            self.assertEqual(list(csv.DictReader(stream))[0]["text"],self.secret_text)
        for receipt in manifest["partitions"]+manifest["downloads"]:
            data = (output/"public"/receipt["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),receipt["sha256"])
            self.assertEqual(len(data),receipt["bytes"])
        self.assertEqual(manifest["coverage"]["meetings"],2)
        partition = json.loads((output/"public"/manifest["partitions"][0]["path"]).read_text())
        self.assertTrue(all(r["positions"] == [] for r in partition["meetings"]))

    def test_inventory_checks_are_not_meetings_and_history_is_preserved(self):
        self.store.record_coverage('run1','inventory:2026-11-01','inventory_failed','private inventory error')
        self.store.start_run('run2',{},'2026-11-02T00:00:00Z')
        self.store.record_coverage('run2','inventory:2026-11-01','inventory_complete','private inventory count')
        self.store.record_coverage('run2','inventory:2026-11-02','deferred','private budget')
        self.store.finish_run('run2','partial','2026-11-02T00:01:00Z')
        out=self.root/'inventory';m=export_snapshot(self.store,out,'inventory','2026-11-02T00:02:00Z')
        self.assertEqual(m['coverage']['meetings'],2)
        self.assertEqual(m['coverage']['stored_meetings'],1)
        self.assertEqual(m['coverage']['inventory_dates'],2)
        self.assertEqual(m['coverage']['inventory_statuses'],{'inventory_complete':1,'deferred':1})
        self.assertNotIn('inventory_complete',m['coverage']['statuses'])
        with (out/'public/meetings.csv').open() as f:
            self.assertFalse(any(r['meeting_id'].startswith('inventory:') for r in csv.DictReader(f)))
        with (out/'private/coverage.csv').open() as f:
            self.assertEqual(sum(r['meeting_id'].startswith('inventory:') for r in csv.DictReader(f)),3)

    def test_immutable_export_and_repeatability(self):
        one,two = self.root/"one",self.root/"two"
        first = export_snapshot(self.store,one,"fixed","2026-11-01T12:02:00Z")
        second = export_snapshot(self.store,two,"fixed","2026-11-01T12:02:00Z")
        self.assertEqual(first,second)
        self.assertEqual((one/"private/manifest.json").read_bytes(),(two/"private/manifest.json").read_bytes())
        before = (one/"public/manifest.json").read_bytes()
        with self.assertRaises(FileExistsError):
            export_snapshot(self.store,one,"other","2026-11-01T12:03:00Z")
        self.assertEqual(before,(one/"public/manifest.json").read_bytes())

    def test_failed_snapshot_has_no_partial_output(self):
        self.store.db.execute("PRAGMA foreign_keys=OFF")
        with self.store.db:
            self.store.db.execute("INSERT INTO coverage VALUES('missing-run','x','failed','')")
        output = self.root/"bad"
        with self.assertRaisesRegex(ValueError,"foreign-key"):
            export_snapshot(self.store,output,"bad","2026-11-01T12:02:00Z")
        self.assertFalse(output.exists())
        self.assertFalse(list(self.root.glob(".snapshot-*")))

    def test_only_release_approved_current_national_predictions_are_public(self):
        revision = self.store.ingest(self.meeting,b'{"synthetic":"national"}',[dict(text=self.secret_text,language="en",speaker="private-speaker-marker",country="FRA",capacity="national",json_pointer="/transcript/data/0")],"2026-11-02T12:00:00Z")
        segment = self.store.current_segments()[0]
        issue = dict(issue_id="access",version="1",label="Humanitarian access",definition="Support humanitarian access")
        self.store.upsert_issue(issue)
        prediction = dict(revision_id=revision,segment_id=segment["segment_id"],issue_id="access",issue_version="1",model_version="synthetic-model",stance="support",status="validated",created_at="2026-11-02T12:01:00Z",evidence=[dict(start=0,end=len(self.secret_text),quote=self.secret_text)])
        self.store.add_prediction(prediction)
        before = export_snapshot(self.store,self.root/"before","before","2026-11-02T12:02:00Z")
        self.assertEqual(before["model_status"],"not_validated")
        self.assertEqual(json.loads((self.root/"before/public"/before["partitions"][0]["path"]).read_text())["meetings"][-1]["positions"],[])
        analysis = dict(model_status=dict(accepted=True,release_approved=True,model_id="synthetic-model",acceptance_sha256="a"*64),predictions=[prediction],issues=[issue],issue_candidates=[dict(candidate_id="topic",source_id=revision,segment_id=segment["segment_id"],issue_id="access",catalog_version="1",status="retrieval_candidate_not_stance")])
        self.store.record_analysis(analysis,created_at="2026-11-02T12:02:00Z")
        after = export_snapshot(self.store,self.root/"after","after","2026-11-02T12:03:00Z")
        self.assertEqual(after["model_status"],"accepted")
        meetings = json.loads((self.root/"after/public"/after["partitions"][0]["path"]).read_text())["meetings"]
        published = next(r for r in meetings if r["meeting_id"]==self.meeting["meeting_id"])
        self.assertEqual(published["positions"][0]["label"],"support")
        self.assertEqual(published["issues"][0]["kind"],"retrieval_candidate_not_stance")
        self.assertNotIn(self.secret_text,json.dumps(published))
        self.store.record_analysis({"model_status":{"accepted":False}},created_at="2026-11-02T12:04:00Z")
        withheld = export_snapshot(self.store,self.root/"withheld","withheld","2026-11-02T12:05:00Z")
        self.assertEqual(withheld["model_status"],"not_validated")
        rows = json.loads((self.root/"withheld/public"/withheld["partitions"][0]["path"]).read_text())["meetings"]
        self.assertTrue(all(r["positions"]==[] for r in rows))

    def test_public_csv_does_not_execute_source_titles_as_formulas(self):
        meeting = {**self.meeting,"title":"=SYNTHETIC(1)"}
        self.store.ingest(meeting,b'{}',[],"2026-11-02T12:00:00Z")
        manifest = export_snapshot(self.store,self.root/"safe","safe","2026-11-02T12:01:00Z")
        with (self.root/"safe/public/meetings.csv").open(newline="") as stream:
            rows=list(csv.DictReader(stream))
        row=next(r for r in rows if r["meeting_id"]==meeting["meeting_id"])
        self.assertEqual(row["title"],"'=SYNTHETIC(1)")
        data=json.loads((self.root/"safe/public"/manifest["partitions"][0]["path"]).read_text())
        row=next(r for r in data["meetings"] if r["meeting_id"]==meeting["meeting_id"])
        self.assertEqual(row["title"],"=SYNTHETIC(1)")

    def test_country_issue_panel_deduplicates_and_preserves_conflicts(self):
        text="We support humanitarian access."
        revision=self.store.ingest(self.meeting,b'{"synthetic":"two-segments"}',[
            dict(segment_id="s1",text=text,language="en",country="France",capacity="national",json_pointer="/transcript/data/0"),
            dict(segment_id="s2",text=text,language="en",country="FRA",capacity="national",json_pointer="/transcript/data/1")],"2026-11-03T12:00:00Z")
        issue=dict(issue_id="access",version="1",label="Access",definition="Support access")
        predictions=[dict(revision_id=revision,segment_id=s,issue_id="access",issue_version="1",model_version="synthetic-model",stance=stance,status="validated",created_at="2026-11-03T12:01:00Z",evidence=[dict(start=0,end=len(text),quote=text)]) for s,stance in (("s1","support"),("s2","oppose"))]
        self.store.record_analysis(dict(issues=[issue],predictions=predictions,model_status=dict(accepted=True,release_approved=True,model_id="synthetic-model",acceptance_sha256="a"*64)),created_at="2026-11-03T12:02:00Z")
        manifest=export_snapshot(self.store,self.root/"panel","panel","2026-11-03T12:03:00Z")
        with (self.root/"panel/private/country_issue_observations.csv").open(newline="") as stream:
            rows=list(csv.DictReader(stream))
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["country"],"FRA")
        self.assertEqual(rows[0]["status"],"mixed")
        self.assertEqual(rows[0]["stance"],"")
        self.assertEqual(json.loads(rows[0]["source_segment_ids"]),["s1","s2"])
        partition=json.loads((self.root/"panel/public"/manifest["partitions"][0]["path"]).read_text())
        positions=[p for m in partition["meetings"] for p in m["positions"]]
        self.assertEqual(len(positions),1)
        self.assertEqual(positions[0]["status"],"mixed")
        pilot=json.loads((self.root/"panel/private/current_segments.json").read_text())
        self.assertEqual(len(pilot["segments"]),2)
        self.assertEqual({r["revision_id"] for r in pilot["segments"]},{revision})

    def test_derived_national_capacity_requires_evaluated_attribution_binding(self):
        from un_transcript.attribution import infer_capacity
        text="I speak on behalf of the Government of France. We support humanitarian access."
        segment=dict(segment_id="derived",text=text,language="en",country="France",capacity="unknown",json_pointer="/transcript/data/0")
        attributed=infer_capacity(segment)
        revision=self.store.ingest(self.meeting,b'{"synthetic":"derived"}',[segment],"2026-11-03T12:00:00Z")
        issue=dict(issue_id="access",version="1",label="Access",definition="Support access")
        prediction=dict(revision_id=revision,segment_id="derived",issue_id="access",issue_version="1",model_version="derived-model",stance="support",status="validated",created_at="2026-11-03T12:01:00Z",evidence=[dict(start=0,end=len(text),quote=text)])
        status=dict(accepted=True,release_approved=True,model_id="derived-model",acceptance_sha256="b"*64)
        self.store.record_analysis(dict(issues=[issue],predictions=[prediction],model_status=status),created_at="2026-11-03T12:02:00Z")
        before=export_snapshot(self.store,self.root/"derived-before","derived-before","2026-11-03T12:03:00Z")
        data=json.loads((self.root/"derived-before/public"/before["partitions"][0]["path"]).read_text())
        self.assertTrue(all(not r["positions"] for r in data["meetings"]))
        # New release identity binds the actual inference method and registry.
        status.update(model_id="derived-model-v2",acceptance_sha256="c"*64,
            **{k:attributed[k] for k in ("attribution_method_version","attribution_registry_sha256")})
        prediction["model_version"]="derived-model-v2"
        self.store.record_analysis(dict(issues=[issue],predictions=[prediction],model_status=status),created_at="2026-11-03T12:04:00Z")
        after=export_snapshot(self.store,self.root/"derived-after","derived-after","2026-11-03T12:05:00Z")
        data=json.loads((self.root/"derived-after/public"/after["partitions"][0]["path"]).read_text())
        positions=[p for r in data["meetings"] for p in r["positions"]]
        self.assertEqual(len(positions),1)
        self.assertEqual(positions[0]["country"],"FRA")
        self.assertEqual(self.store.current_segments()[0]["capacity"],"unknown")


if __name__ == "__main__":
    unittest.main()
