"""Publish only the static workspace and the already-public HLW report assets."""
import argparse, json, shutil
from pathlib import Path

def build(output):
    repo=Path(__file__).resolve().parents[1];output=Path(output)
    if output.exists():raise FileExistsError('Use a new Pages output directory')
    output.mkdir(parents=True)
    for p in (repo/'site').iterdir():
        if p.is_file():shutil.copy2(p,output/p.name)
    source=repo/'reports/hlw-cuba';dest=output/'reports/hlw-cuba';dest.mkdir(parents=True)
    for p in source.iterdir():
        if p.is_symlink():raise ValueError('Symlink in public report')
        if p.is_file() and p.suffix.lower() in ('.html','.css','.js','.json','.png','.svg','.txt','.pdf','.docx','.csv','.md'):
            shutil.copy2(p,dest/p.name)
    (output/'.nojekyll').write_text('')
    return {'files':len(list(output.rglob('*'))),'private_review_work_included':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');a=p.parse_args();print(json.dumps(build(a.output)))
