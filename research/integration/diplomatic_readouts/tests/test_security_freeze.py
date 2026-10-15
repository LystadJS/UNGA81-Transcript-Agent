"""Data-free prospective synthetic security-freeze consistency checks.

Do not change source gate or holdout readiness. Git blob SHA-1 is a repository
byte-identity check, NOT a signature or a general source-authentication scheme.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha1
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parents[1]
CANDIDATE = HERE / "security_review_freeze_candidate.v0.json"


class ProspectiveFreezeChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(CANDIDATE.read_text(encoding="utf-8"))

    def test_01_immutable_synthetic_file_bases(self):
        for path, expected in self.record["source_blob_sha1"].items():
            with self.subTest(path=path):
                raw = (HERE / path).read_bytes()
                actual = sha1(b"blob " + str(len(raw)).encode("ascii") +
                              b"\0" + raw).hexdigest()
                self.assertEqual(actual, expected)

    def test_02_no_release_status_can_be_declared(self):
        rec = self.record
        self.assertEqual(rec["status"], "PROPOSED_NOT_APPROVED")
        self.assertEqual(rec["evaluation_role"], "synthetic_engineering_only")
        self.assertEqual(rec["authority"], "none")
        for name in ("authorized", "can_read_source", "can_issue_review",
                     "statistical_eligible", "publication_eligible", "delivery_eligible"):
            self.assertIs(rec[name], False)
        self.assertEqual(len(rec["gates"]), 13)
        self.assertEqual(set(rec["gates"].values()), {"NOT_RUN"})

    def test_03_sealed_holdout_and_nonreal_contract(self):
        lock = self.record["holdout"]
        self.assertEqual(lock, {
            "meetings_reserved": 37, "transcripts_opened": 0,
            "access_granted": False, "d1_o1_o5": "frozen",
        })
        self.assertEqual(self.record["scope"]["source_split"], "synthetic")
        self.assertTrue(self.record["scope"]["no_original_transcript_rows"])
        self.assertEqual(self.record["scope"]["readout_dependency_sha"],
                         "028e3d26f707401cbff498593ab27f64e2cc072a")

    def test_04_attack_matrix_is_complete_and_one_success_is_non_authorizing(self):
        cases = self.record["required_attacks"]
        self.assertEqual(len(cases), 13)
        self.assertEqual({c["case"] for c in cases},
                         {"T%02d" % i for i in range(1, 14)})
        positives = [c for c in cases if c["expected"] == "verified_no_authority"]
        self.assertEqual([c["case"] for c in positives], ["T10"])
        self.assertEqual(sum(c["expected"] == "withheld" for c in cases), 12)

    def test_05_byte_tampering_would_violate_source_identity(self):
        raw = (HERE / "synthetic_signatures.py").read_bytes()
        expected = self.record["source_blob_sha1"]["synthetic_signatures.py"]
        tampered = raw + b"# changed after candidate freeze\n"
        actual = sha1(b"blob " + str(len(tampered)).encode("ascii") +
                      b"\0" + tampered).hexdigest()
        self.assertNotEqual(actual, expected)

    def test_06_candidate_is_not_a_permission_token(self):
        altered = deepcopy(self.record)
        altered["authorized"] = True
        self.assertNotEqual(altered["authorized"], self.record["authorized"])
        self.assertNotIn("private_key", json.dumps(self.record))
        self.assertNotIn("original_bytes", json.dumps(self.record))
        self.assertNotIn("source_url", json.dumps(self.record))


if __name__ == "__main__":
    unittest.main()
