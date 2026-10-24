"""Synthetic acceptance tests; no original transcripts or scientific gold labels."""
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
from .repository import IssueStore, canonical_bytes, stable_id


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.store = IssueStore(Path(self.temp.name) / "history.sqlite")
        self.source = dict(id="synthetic-source", published_date="2024-01-01", body="SC", family="synthetic",
                           url="https://example.invalid/source", content_hash="a" * 64, access="public_approved", countries=["Example", "UnknownExample"], text="DO NOT EXPORT")
        self.revision = self.store.upsert_source(self.source)
        self.observation = dict(id="expression-1", source_id=self.source["id"], source_revision=self.revision,
                                country="Example", date="2024-01-01", policy="humanitarian_access", context="Sudan",
                                stance="support", review_state="assistant_provisional", attribution="national", unresolved=True, qualification_codes=["subject_to_law"], private_note="DO NOT EXPORT")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_idempotency_and_transitive_invalidation(self):
        self.assertEqual(self.revision, self.store.upsert_source(self.source))
        self.store.put_observation(self.observation)
        self.store.put_observation(self.observation)
        self.assertEqual(1, self.store.db.execute("SELECT count(*) FROM evidence").fetchone()[0])
        model = self.store.put_artifact("model", {"version": 1}, ["expression-1"])
        report = self.store.put_artifact("report", {"version": 1}, [model])
        independent = self.store.put_artifact("report", {"version": 2}, [])
        self.store.upsert_source({**self.source, "content_hash": "b" * 64})
        self.assertFalse(self.store.artifact_valid(model))
        self.assertFalse(self.store.artifact_valid(report))
        self.assertTrue(self.store.artifact_valid(independent))
        stale = self.store.put_artifact("model", {"version": 2}, ["expression-1"])
        self.assertFalse(self.store.artifact_valid(stale))
        with self.assertRaises(ValueError):
            self.store.put_artifact("model", {"version": 3}, ["missing-dependency"])
        self.assertEqual(2, self.store.db.execute("SELECT count(*) FROM source_revisions").fetchone()[0])
        with self.assertRaises(ValueError):
            self.store.put_observation(self.observation)

    def test_public_export_hash_privacy_snapshot(self):
        self.store.put_observation(self.observation)
        private = {**self.source, "id": "private-source", "access": "private"}
        self.store.upsert_source(private)
        dest = Path(self.temp.name) / "bundles"
        manifest = self.store.export_bundle(dest, "v1", {"status": "fixture", "notes": "DO NOT EXPORT"})
        shard = manifest["shards"][0]
        raw = (dest / shard["url"]).read_bytes()
        self.assertEqual(shard["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(shard["bytes"], len(raw))
        self.assertNotIn(b"DO NOT EXPORT", raw)
        self.assertNotIn(b"private-source", raw)
        decoded = json.loads(raw)
        self.assertIn("UnknownExample", decoded["sources"][0]["countries"])
        self.assertTrue(decoded["observations"][0]["unresolved"])
        self.assertEqual(["subject_to_law"], decoded["observations"][0]["qualification_codes"])
        self.assertEqual(manifest, self.store.export_bundle(dest, "v1", {"status": "fixture"}))
        self.store.upsert_source({**self.source, "content_hash": "c" * 64})
        with self.assertRaises(ValueError):
            self.store.export_bundle(dest, "v1")
        changed = self.store.export_bundle(dest, "v2")
        self.assertEqual(0, changed["counts"]["observations"])

    def test_eligibility_votes_backup(self):
        self.store.put_membership("Example", "SC", "2023-01-01", "2024-12-31")
        self.store.put_membership("Example", "SC", "2023-01-01", "2024-12-31")
        self.assertEqual(1, self.store.db.execute("SELECT count(*) FROM memberships").fetchone()[0])
        with self.assertRaises(ValueError):
            self.store.put_membership("Example", "SC", "2024-01-01", "2025-12-31")
        vote = {k: v for k, v in self.observation.items() if k in ("id", "source_id", "source_revision", "country", "date", "policy", "context")}
        self.store.put_vote({**vote, "id": "vote-1", "vote": "not_eligible", "resolution": "S/example", "resolution_version": "1", "stage": "adopted_resolution", "eligible": False})
        with self.assertRaises(ValueError):
            self.store.put_vote({**vote, "vote": "consensus", "resolution": "x", "stage": "adoption"})
        backup = Path(self.temp.name) / "rollback.sqlite"
        self.store.backup(backup)
        restored = IssueStore(backup)
        self.assertEqual(1, restored.db.execute("SELECT count(*) FROM evidence").fetchone()[0])
        restored.close()

    def test_canonical_identity(self):
        self.assertEqual(stable_id("source", {"a": 1, "b": 2}), stable_id("source", {"b": 2, "a": 1}))
        with self.assertRaises(ValueError):
            canonical_bytes({"unsupported": float("nan")})

    def test_bulk_transaction_rollback(self):
        with self.assertRaises(RuntimeError):
            with self.store.transaction():
                self.store.upsert_source({**self.source, "id": "rolled-back"})
                raise RuntimeError("synthetic sink failure")
        self.assertIsNone(self.store.db.execute("SELECT id FROM sources WHERE id='rolled-back'").fetchone())

    def test_provisional_binding_separate_from_votes(self):
        binding = dict(resolution_id="S/RES/EXAMPLE",resolution_version="as_adopted",stage="adopted_resolution",
            policy_id="humanitarian_access",context_id="thematic_armed_conflict",source_url="https://digitallibrary.un.org/record/fixture",
            rationale="Invented operative access requirement",review_state="assistant_provisional",source_sha256="a"*64,source_anchor="Synthetic paragraph 1")
        artifact = self.store.put_policy_binding(binding,published_date="2024-01-01",body="SC")
        self.assertEqual(artifact,self.store.put_policy_binding(binding,published_date="2024-01-01",body="SC"))
        self.assertTrue(self.store.artifact_valid(artifact))
        self.assertEqual(0,self.store.db.execute("SELECT count(*) FROM evidence").fetchone()[0])
        self.assertEqual(1,self.store.export_bundle(Path(self.temp.name)/"public-binding-test","binding-test")["counts"]["sources"])
        with self.assertRaises(ValueError):
            self.store.put_policy_binding({**binding,"review_state":"owner_confirmed"},published_date="2024-01-01",body="SC")

    def test_bounded_partitions_and_browser_query_parity(self):
        for i in range(4):
            source = {**self.source, "id": "source-" + str(i), "published_date": f"202{3 + i % 2}-01-01", "body": "SC" if i % 2 else "GA"}
            revision = self.store.upsert_source(source)
            self.store.put_observation({**self.observation, "id": "obs-" + str(i), "source_id": source["id"], "source_revision": revision, "date": source["published_date"]})
        dest = Path(self.temp.name) / "partitioned"
        manifest = self.store.export_bundle(dest, "partitioned", partition=True, max_rows=2, max_bytes=3000)
        shards = [json.loads((dest / s["url"]).read_bytes()) for s in manifest["shards"]]
        for spec, shard in zip(manifest["shards"], shards):
            self.assertLessEqual(spec["bytes"], 3000)
            self.assertLessEqual(sum(len(shard[k]) for k in ("sources", "observations", "votes", "memberships", "roster")), 2)
        snapshot = {"manifest": manifest, **{key: [row for shard in shards for row in shard[key]] for key in ("sources", "observations", "votes")}}
        script = "const H=require('./site/issue-history-client.js');let s='';process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>console.log(JSON.stringify(H.query(JSON.parse(s),{start:'2024-01-01',end:'2024-12-31',bodies:['SC'],policies:['humanitarian_access']}))));"
        result = subprocess.run(["node", "-e", script], input=json.dumps(snapshot), capture_output=True, text=True, check=True)
        actual = json.loads(result.stdout)
        self.assertEqual(["obs-1", "obs-3"], sorted(row["id"] for row in actual["observations"]))
        previous = (dest / "manifest.json").read_bytes()
        with self.assertRaises(ValueError):
            self.store.export_bundle(dest, "too-small", partition=True, max_rows=1)
        self.assertEqual(previous, (dest / "manifest.json").read_bytes())

    def test_selective_roster_and_version_provenance(self):
        self.store.put_observation({**self.observation,"ontology_version":"ontology-1","extractor_version":"rules-1"})
        self.store.put_observation({**self.observation,"id":"other-policy","policy":"civilian_protection"})
        self.store.upsert_source({**self.source,"id":"without-positions","countries":["ThirdExample"],"private_note":"DO NOT EXPORT"})
        self.store.upsert_source({**self.source,"id":"private-roster","countries":["PrivateOnly"],"access":"private"})
        dest=Path(self.temp.name)/"selective"
        manifest=self.store.export_bundle(dest,"selective",partition=True,max_rows=2,max_bytes=3000)
        self.assertEqual("policy-year-body-v1",manifest["selection_protocol"])
        self.assertEqual(["legacy","ontology-1"],manifest["versions"]["ontology_version"])
        self.assertEqual(["legacy","rules-1"],manifest["versions"]["extractor_version"])
        selected=[spec for spec in manifest["shards"] if spec["policy"] in ("_roster","humanitarian_access")]
        shards=[json.loads((dest/spec["url"]).read_bytes()) for spec in selected]
        roster=[row for shard in shards for row in shard["roster"]]
        self.assertEqual([{"date":"2024-01-01","body":"SC","family":"synthetic","countries":["Example","ThirdExample","UnknownExample"],"source_count":2}],roster)
        observed=[row for shard in shards for row in shard["observations"]]
        self.assertEqual(1,len(observed))
        self.assertEqual("ontology-1",observed[0]["ontology_version"])
        self.assertNotIn("PrivateOnly",json.dumps(shards))
        self.assertNotIn("DO NOT EXPORT",json.dumps(shards))
        legacy=self.store.export_bundle(Path(self.temp.name)/"all","unpartitioned")
        all_shard=json.loads((Path(self.temp.name)/"all"/legacy["shards"][0]["url"]).read_bytes())
        self.assertEqual(roster,all_shard["roster"])
        self.assertNotIn("selection_protocol",legacy)
        prior=(dest/"manifest.json").read_bytes()
        self.store.put_observation({**self.observation,"ontology_version":"https://private.invalid/not-an-id"})
        with self.assertRaisesRegex(ValueError,"Version identities"):
            self.store.export_bundle(dest,"unsafe",partition=True)
        self.assertEqual(prior,(dest/"manifest.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
