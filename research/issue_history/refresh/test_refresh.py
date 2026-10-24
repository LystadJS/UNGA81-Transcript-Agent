import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from ..ingest.adapters import transcript_record
from ..store import IssueStore
from .runner import refresh, transcript_sink


class RefreshTests(unittest.TestCase):
    def test_adapter_store_resume_and_failed_publish_preserves_manifest(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            base = Path(directory)
            store = IssueStore(base / "store.sqlite")
            try:
                text = "Invented fixture only"
                row = dict(id="fixture", date="2024-01-01", country="Example", language="en", text=text,
                    text_sha256=hashlib.sha256(text.encode()).hexdigest(), source_url="https://transcripts.un.org/en/fixture")
                rows = [row, {**row, "id": "fixture2", "country": "OtherExample"}]
                def extraction(item):
                    return [dict(id=item["id"] + "-position", country=item["country"], date=item["date"],
                        policy="humanitarian_access", context="sudan", stance="support", review_state="assistant_provisional", attribution="national")]
                sink = transcript_sink(store, "SC", "public_approved", extraction)
                options = dict(rows=rows, adapter=transcript_record, persist=sink, store=store,
                    checkpoint=base / "cursor.json", bundle_directory=base / "public", snapshot_id="snapshot1",
                    health_path=base / "health.json", limit=1, watermark="2024-01-02")
                self.assertEqual("incomplete", refresh(**options)["status"])
                self.assertFalse((base / "public" / "manifest.json").exists())
                self.assertEqual("published", refresh(**options)["status"])
                manifest_path = base / "public" / "manifest.json"
                published = manifest_path.read_bytes()
                manifest = json.loads(published)
                shards = [json.loads((base / "public" / spec["url"]).read_bytes()) for spec in manifest["shards"]]
                observations = [row for shard in shards for row in shard["observations"]]
                sources = {row["id"]:row for shard in shards for row in shard["sources"]}
                self.assertEqual(2, len(observations))
                for observation in observations:
                    self.assertEqual(sources[observation["source_id"]]["revision"], observation["source_revision"])
                self.assertEqual(2,sum(row["source_count"] for shard in shards for row in shard["roster"]))
                self.assertNotIn(text, (base / "health.json").read_text())
                bad = {**row, "text": "corrupted private text"}
                failed = refresh(**{**options, "rows": [bad], "checkpoint": base / "bad-cursor.json", "snapshot_id": "bad"})
                self.assertEqual("quarantined", failed["status"])
                self.assertEqual("snapshot1", failed["last_published_snapshot"])
                self.assertEqual(published, manifest_path.read_bytes())
                with self.assertRaises(ValueError):
                    refresh(**{**options, "rows": [row], "checkpoint": base / "changed.json", "snapshot_id": "snapshot1"})
                self.assertEqual(published, manifest_path.read_bytes())
                self.assertEqual("failed", json.loads((base / "health.json").read_bytes())["status"])
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
