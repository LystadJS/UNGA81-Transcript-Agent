"""Publish only the static workspace and the already-public HLW report assets."""
import argparse, csv, hashlib, json, shutil
from pathlib import Path

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
    source=repo/'reports/hlw-cuba';dest=output/'reports/hlw-cuba';dest.mkdir(parents=True)
    for p in source.iterdir():
        if p.is_symlink():raise ValueError('Symlink in public report')
        if p.is_file() and p.suffix.lower() in ('.html','.css','.js','.json','.png','.svg','.txt','.pdf','.docx','.csv','.md'):
            shutil.copy2(p,dest/p.name)
    # Explicitly approved synthetic research browser assets. Never recurse
    # through site/: tests, draft reviews, local screenshots, private inputs,
    # and user-generated archives are not publishable Pages content.
    reviewed_research_assets = {
        'parallel/w05-browser/experimental/method-lab': (
            'index.html', 'contracts.js', 'adapters.js', 'task-controller.js',
            'method-lab.js', 'method-lab.css', 'worker.js'),
        'parallel/w05-browser/experimental/method-lab/fixtures': (
            'synthetic-contract.json',),
        'experimental/evidence-viz': (
            'index.html', 'styles.css', 'fixture.js',
            'evidence-viz.js', 'demo.js'),
    }
    for relative, names in reviewed_research_assets.items():
        source_dir = repo/'site'/relative
        target_dir = output/relative
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in names:
            original = source_dir/name
            if original.is_symlink() or not original.is_file():
                raise ValueError(f'Missing or symlinked reviewed research asset: {relative}/{name}')
            shutil.copy2(original, target_dir/name)
    (output/'.nojekyll').write_text('')
    return {'files':len(list(output.rglob('*'))),'private_review_work_included':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');a=p.parse_args();print(json.dumps(build(a.output)))
