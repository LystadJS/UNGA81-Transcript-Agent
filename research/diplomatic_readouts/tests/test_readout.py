import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from readout import render, normalize, validate
def sample():
 return dict(title="Synthetic",template="emerging_themes",population="Synthetic",period="Synthetic",denominator=2,exclusions=0,missingness=0,sources=[dict(id="s1",sha256="a"*64,accepted=True,privacy="public")],gates=dict(source=True,statistical=True,review=True),findings=[dict(label="Test",supporting=[dict(source_id="s1",start=0,end=2)],contrary=[],interpretation="Synthetic inference",interpretation_supported=True)])
class Tests(unittest.TestCase):
 def test_complete(self):
  r=sample();self.assertEqual(validate(r),[]);self.assertEqual(normalize(r)["release_state"],"qualified_experimental")
 def test_missing(self):
  r=sample();r["findings"][0]["supporting"]=[];self.assertEqual(normalize(r)["release_state"],"withheld")
 def test_source(self):
  r=sample();r["sources"][0]["accepted"]=False;self.assertEqual(normalize(r)["release_state"],"withheld")
 def test_gate(self):
  r=sample();r["gates"]["statistical"]=False;self.assertNotIn("Synthetic inference",render(r,"html"))
 def test_stance(self):
  r=sample();r["findings"][0]["stance"]="support";self.assertEqual(normalize(r)["release_state"],"withheld")
 def test_private(self):
  r=sample();r["sources"][0]["text"]="SECRET";self.assertNotIn("SECRET",render(r,"json"))
 def test_formats(self):
  r=sample()
  for f in ("json","markdown","html"):self.assertEqual(render(r,f),render(r,f))
if __name__=="__main__":unittest.main()
