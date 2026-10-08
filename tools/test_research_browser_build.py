"""Check the exact static runtime allowlist and exclusion of research artifacts."""
from __future__ import annotations
from pathlib import Path
import tempfile,subprocess,sys,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_pages
def main():
  assets=set(build_pages.RESEARCH_ASSETS)
  assert len(assets)==13
  w5='parallel/w05-browser/experimental/method-lab/'
  w6='experimental/evidence-viz/'
  assert all(p.startswith((w5,w6)) for p in assets)
  assert all(not any(q in p for q in ('README','test-','tests.cjs','previews','browser_smoke')) for p in assets)
  with tempfile.TemporaryDirectory(prefix='research-build-') as tmp:
    out=Path(tmp)/'_site'
    subprocess.run([sys.executable,str(ROOT/'tools/build_pages.py'),str(out)],cwd=ROOT,check=True,capture_output=True)
    for p in assets:
      a=ROOT/'site'/p;b=out/p
      assert b.is_file() and hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest(),p
    files={p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()}
    nested={p for p in files if p.startswith((w5,w6))}
    assert nested==assets,(nested^assets)
    for p in ('research.html','research.css','research-browser.js','index.html','latent.html'):
      assert p in files,p
    for p in ('index.html','latent.html'):
      assert 'href="research.html"' in (out/p).read_text(encoding='utf-8')
    fixture=json.loads((out/w5/'fixtures/synthetic-contract.json').read_text(encoding='utf-8'))
    assert fixture['producer']['fixture_kind']=='synthetic'
    assert fixture['upstream']['source_schema']=='synthetic.v1'
    assert fixture['publication_eligible'] is False
    assert all(row['source_url'] is None and 'text' not in row for row in fixture['observations'])
    print(json.dumps({'status':'PASS','runtime_assets':len(assets),'private_research_artifacts':0}))
if __name__=='__main__':main()
