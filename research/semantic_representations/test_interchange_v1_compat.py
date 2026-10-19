"""Official v1 contract compatibility: synthetic null lineage and minor versions."""
import copy
import json
import pathlib
import unittest
from interchange import check_parallel_v1

EXAMPLE = pathlib.Path(__file__).with_name("official_v1_synthetic.json")

class ContractCompatibility(unittest.TestCase):
    def fixture(self):
        return json.loads(EXAMPLE.read_text())
    def test_official_example(self):
        self.assertEqual(check_parallel_v1(self.fixture())["observation_count"], 1)
    def test_missing_source_with_reason_is_read_only(self):
        case = self.fixture()
        case["upstream"]["source_sha256"] = None
        case["upstream"]["missing_reason"] = "original source not authenticated"
        self.assertTrue(check_parallel_v1(case)["read_only"])
    def test_missing_selection_with_reason_is_read_only(self):
        case = self.fixture()
        case["upstream"]["selection_sha256"] = None
        case["upstream"]["missing_reason"] = "selection inventory incomplete"
        self.assertTrue(check_parallel_v1(case)["read_only"])
    def test_missing_hash_without_reason_rejected(self):
        case = self.fixture()
        case["upstream"]["source_sha256"] = None
        with self.assertRaises(ValueError):check_parallel_v1(case)
    def test_malformed_nonnull_hash_rejected(self):
        case = self.fixture()
        case["upstream"]["source_sha256"] = "not-a-hash"
        case["upstream"]["missing_reason"] = "a reason cannot fix a corrupt hash"
        with self.assertRaises(ValueError):check_parallel_v1(case)
    def test_v1_minor_version(self):
        case = self.fixture()
        case["contract_version"] = "1.1.0"
        self.assertTrue(check_parallel_v1(case)["read_only"])
    def test_wrong_major_version_rejected(self):
        case = self.fixture()
        case["contract_version"] = "2.0.0"
        with self.assertRaises(ValueError):check_parallel_v1(case)

if __name__ == "__main__": unittest.main()
