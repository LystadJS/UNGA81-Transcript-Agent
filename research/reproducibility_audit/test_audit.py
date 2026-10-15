import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from audit import check_envelope, check_isolation, check_population, check_replay, scan_public, sha256, qa_summary

H="a"*64
def fixture():
    return {"schema":"un.parallel-analysis.v1","upstream":{"source_schema":"un.browser.corpus.v1","source_hash_basis":"decoded_utf8","source_sha256":H,"selection_sha256":H},"cohort":{"population":"synthetic","unit":"synthetic"},"observations":[{"id":"a","text_sha256":H,"start":0,"end":3}],"models":[{"model_id":"m"}],"results":[{"model_id":"m","observation_id":"a","status":"unassigned","cluster":0}],"publication_eligible":False,"evaluation_role":"engineering_only"}

class AuditTests(unittest.TestCase):
    def test_valid(self): self.assertEqual(check_envelope(fixture()),[])
    def test_missing_identity(self):
        d=fixture();del d["observations"][0]["id"];self.assertIn("missing/duplicate observation id",check_envelope(d))
    def test_duplicate(self):
        d=fixture();d["observations"].append(copy.deepcopy(d["observations"][0]));self.assertIn("missing/duplicate observation id",check_envelope(d))
    def test_bad_hash(self):
        d=fixture();d["upstream"]["source_sha256"]="bad";self.assertIn("invalid hash: source_sha256",check_envelope(d))
    def test_partial_fit(self):
        d=fixture();d["results"]=[];self.assertTrue(any("missing eligible result" in e for e in check_envelope(d)))
    def test_unassigned(self):
        d=fixture();d["results"][0]["cluster"]=None;self.assertIn("unassigned cluster",check_envelope(d))
    def test_denominator(self):
        d=fixture();d["results"][0]["memberships"]=[.4,.4];self.assertIn("membership normalization",check_envelope(d))
    def test_population(self):
        self.assertIn("incompatible source_sha256",check_population({"source_sha256":H},{"source_sha256":"b"*64}))
    def test_leakage(self):
        self.assertIn("leakage: source_family_id",check_isolation([{"id":"a","source_family_id":"s"}],[{"id":"b","source_family_id":"s"}]))
    def test_replay(self):
        b=b"fixture";r={"seed":1,"runtime":"python","dependency_versions":{},"fixture_sha256":sha256(b),"output_sha256":sha256(b)}
        self.assertEqual(check_replay(r,b),[])
        self.assertIn("replay mismatch",check_replay(r,b"changed"))
    def test_sentinel(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,"public.json").write_text("SYNTHETIC_PRIVATE_TRANSCRIPT_SENTINEL")
            self.assertTrue(scan_public(d))
    def test_status(self):
        self.assertFalse(qa_summary({"runtime":"NOT RUN"})["release_authorized"])
if __name__=="__main__": unittest.main()
