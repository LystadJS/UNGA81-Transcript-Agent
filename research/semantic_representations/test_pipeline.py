import hashlib, tempfile, unittest
from pipeline import *
def row(i,text):
    return dict(id=str(i),text=text,text_sha256=digest(normalize(text).encode()),source_sha256="a"*64,selection_sha256="b"*64,source_schema="synthetic.v1",unit="synthetic")
class PipelineTests(unittest.TestCase):
    def test_replay_and_binding(self):
        rows=[row(i,t) for i,t in enumerate(["A diplomatic protocol","Protocol shared","We do not agree","We agree"])]
        with tempfile.TemporaryDirectory() as d:
            a=encode(rows,{"id":"fixture-lexical"},fixture_encoder,d,max_chars=8)
            b=encode(rows,{"id":"fixture-semantic"},fixture_encoder,d,max_chars=8)
            replay=encode(rows,{"id":"fixture-lexical"},lambda _: (_ for _ in ()).throw(RuntimeError("should not infer")),d,max_chars=8)
            self.assertEqual(a,replay)
            self.assertEqual(compare(a,b)["n"],4)
            self.assertGreater(a["rows"][0]["passage_count"],1)
            tampered=[dict(r) for r in rows];tampered[0]["source_sha256"]="c"*64
            with self.assertRaises(ValueError): compare(a,encode(tampered,{"id":"fixture-semantic"},fixture_encoder,d))
            altered=[dict(r) for r in rows];altered[0]["selection_sha256"]="d"*64
            with self.assertRaises(ValueError): compare(a,encode(altered,{"id":"fixture-semantic"},fixture_encoder,d))
            schema_changed=[dict(r) for r in rows];schema_changed[0]["source_schema"]="other.synthetic.v1"
            with self.assertRaises(ValueError): compare(a,encode(schema_changed,{"id":"fixture-semantic"},fixture_encoder,d))
            with self.assertRaises(ValueError): encode(rows+[rows[0]],{"id":"fixture"},fixture_encoder,d)
            with self.assertRaises(ValueError): encode([dict(rows[0],text="wrong")],{"id":"fixture"},fixture_encoder,d)
            cache=next(__import__("pathlib").Path(d).glob("*.json"));cache.write_text("{}")
            with self.assertRaises((ValueError,KeyError)): encode(rows,{"id":"fixture-lexical"},fixture_encoder,d,max_chars=8)
if __name__=="__main__": unittest.main()
