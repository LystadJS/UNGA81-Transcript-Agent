"""Publish only the static workspace and the already-public HLW report assets."""
import argparse, csv, hashlib, json, shutil
from pathlib import Path

# Exact allowlist: only browser runtime source and invented fixtures.
# No review ledgers, local runs, raw transcript data, preview screenshots or
# analytical outputs may enter Pages through these nested directories.
RESEARCH_ASSETS = (
    "parallel/w05-browser/experimental/method-lab/index.html",
    "parallel/w05-browser/experimental/method-lab/method-lab.css",
    "parallel/w05-browser/experimental/method-lab/contracts.js",
    "parallel/w05-browser/experimental/method-lab/adapters.js",
    "parallel/w05-browser/experimental/method-lab/task-controller.js",
    "parallel/w05-browser/experimental/method-lab/method-lab.js",
    "parallel/w05-browser/experimental/method-lab/worker.js",
    "parallel/w05-browser/experimental/method-lab/fixtures/synthetic-contract.json",
    "experimental/evidence-viz/index.html",
    "experimental/evidence-viz/styles.css",
    "experimental/evidence-viz/fixture.js",
    "experimental/evidence-viz/evidence-viz.js",
    "experimental/evidence-viz/demo.js",
)

def copy_research_runtime(repo, output):
    for name in RESEARCH_ASSETS:
        source=repo/'site'/name
        if source.is_symlink() or not source.is_file() or source.stat().st_size>512_000:
            raise ValueError('Research runtime missing, linked or oversized: '+name)
        dest=output/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,dest)


def build(output):
    repo=Path(__file__).resolve().parents[1];output=Path(output)
    numeric_manifest=json.loads((repo/'site/numerics-manifest.json').read_text(encoding='utf-8'))
    if hashlib.sha256((repo/'site/numerics.js').read_bytes()).hexdigest()!=numeric_manifest['sha256']:
        raise ValueError('Numerical bundle hash mismatch; rebuild with tools/browser-deps/build.cjs')
    registry=list(csv.DictReader((repo/'un/config/countries.csv').open(encoding='utf-8-sig')))
    if json.loads((repo/'site/countries.json').read_text(encoding='utf-8'))!=registry:
        raise ValueError('Browser country registry is stale; regenerate site/countries.json from un/config/countries.csv')
    if output.exists():raise FileExistsError('Use a new Pages output directory')
    output.mkdir(parents=True)
    for p in (repo/'site').iterdir():
        if p.is_file():shutil.copy2(p,output/p.name)
    copy_research_runtime(repo,output)
    source=repo/'reports/hlw-cuba';dest=output/'reports/hlw-cuba';dest.mkdir(parents=True)
    for p in source.iterdir():
        if p.is_symlink():raise ValueError('Symlink in public report')
        if p.is_file() and p.suffix.lower() in ('.html','.css','.js','.json','.png','.svg','.txt','.pdf','.docx','.csv','.md'):
            shutil.copy2(p,dest/p.name)
    (output/'.nojekyll').write_text('')
    return {'files':len(list(output.rglob('*'))),'private_review_work_included':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');a=p.parse_args();print(json.dumps(build(a.output)))
