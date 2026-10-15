import tempfile
import unittest
from pathlib import Path
from controls import verify_checkpoint, token_windows, negative_control_metrics, sha256

class FakeTokenizer:
    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        return list(text.encode("utf-8"))

class Tests(unittest.TestCase):
    def test_integrity_and_extra_files(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            (path / "tokenizer.json").write_text("synthetic")
            (path / "config.json").write_text("{}")
            manifest = {"revision": "a" * 40, "artifacts": {p.name: sha256(p.read_bytes()) for p in path.iterdir()}}
            self.assertEqual(len(verify_checkpoint(path, manifest)), 64)
            (path / "unexpected.txt").write_text("bad")
            with self.assertRaises(ValueError): verify_checkpoint(path, manifest)
            (path / "unexpected.txt").unlink()
            (path / "config.json").write_text("tampered")
            with self.assertRaises(ValueError): verify_checkpoint(path, manifest)
    def test_length_and_overlap(self):
        windows = token_windows("abcdefghijkl", FakeTokenizer(), 5, 2)
        self.assertEqual([w["start_token"] for w in windows], [0,3,6,9])
        self.assertTrue(all(len(w["token_ids"]) <= 5 for w in windows))
        with self.assertRaises(ValueError): token_windows("abc", FakeTokenizer(), 5, 5)
    def test_controls(self):
        ids=["A","B","C"]
        distances={"A":{"B":0.1,"C":0.9},"B":{"A":0.1,"C":0.8},"C":{"A":0.9,"B":0.8}}
        output=negative_control_metrics(ids,distances,distances,[{"case":"negation","anchor":"A","target":"B"}])
        self.assertEqual(output["neighbor_overlap"],1)
        self.assertFalse(output["controls"][0]["stance_inference_permitted"])
        with self.assertRaises(ValueError): negative_control_metrics(ids,distances,{"A":{}},[])

if __name__ == "__main__": unittest.main()
