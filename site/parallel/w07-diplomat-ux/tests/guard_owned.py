"""Git-metadata guard for coordinator execution. No source/holdout contents are read."""
import argparse
import json
import subprocess

BASE = '884097997f89b0040e4418480378f077e3b65434'
PREFIX = 'site/parallel/w07-diplomat-ux/'
parser = argparse.ArgumentParser()
parser.add_argument('--head', required=True)
args = parser.parse_args()
def git(*parts):
    return subprocess.check_output(['git', *parts], text=True).strip()
try:
    actual = git('rev-parse', 'HEAD')
    if actual != args.head:
        raise ValueError('wrong_head')
    paths = git('diff', '--name-only', BASE, actual).splitlines()
    if not paths or any(not path.startswith(PREFIX) for path in paths):
        raise ValueError('ownership_violation')
    for path in paths:
        entry = git('ls-tree', actual, '--', path)
        if not entry.startswith('100644 blob '):
            raise ValueError('ordinary_file_required')
    print(json.dumps({'head':actual,'tree':git('rev-parse','HEAD^{tree}'),'c0':BASE,
                      'changed_files':len(paths),'owned_paths':True,'scope':'git_metadata_only'}))
except (subprocess.CalledProcessError, ValueError) as exc:
    print(json.dumps({'status':'BLOCKED_OR_FAILED','owned_paths':False,'error':type(exc).__name__}))
    raise SystemExit(1)
