"""Source-safe, fail-closed W1/W2 and coordinator integration runner."""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

FROZEN = {
    'research/integration/w1_w2/null_calibration/protocol.v1.locked.json': '95ee908bd710b7a6f075b685f0181a6fc979c33e',
    'research/integration/w1_w2/nuisance_estimation/design.candidate.v0.json': 'eac3c87b2de555db55202d91cf440eaef228e4d0',
}
SUITES = {
    'owned': ['python3', '-m', 'unittest', 'discover', '-s', 'research/null_calibration', '-p', 'test_*.py', '-v'],
    'pr57': ['node', 'research/integration/w1_w2/null_calibration/test-null.cjs'],
    'pr60': ['node', 'research/integration/w1_w2/nuisance_estimation/test_estimator.cjs'],
    'interchange': ['node', 'docs/parallel-work/validate-contract.cjs'],
}

def call(root, argv, timeout):
    try:
        completed = subprocess.run(argv, cwd=root, text=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, timeout=timeout, check=False)
        return {'status': 'PASS' if completed.returncode == 0 else 'FAIL',
                'exit_code': completed.returncode,
                'stdout_sha256': hashlib.sha256(completed.stdout.encode()).hexdigest(),
                'tail': completed.stdout[-2000:]}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'status': 'NOT_RUN', 'reason': type(error).__name__}

def validate(root, head, main, timeout=300):
    root = pathlib.Path(root).resolve()
    out = {'schema':'un.null-calibration.integration-receipt.v1', 'expected_head':head,
           'expected_main':main, 'publication_eligible':False, 'suites':{}, 'ready':False}
    if not (root / '.git').exists():
        return dict(out,blocker='no_git_checkout')
    checks = [call(root,['git','rev-parse',ref],timeout) for ref in ('HEAD','main')]
    refs = [v.get('tail','').strip() if v['status']=='PASS' else None for v in checks]
    out['actual_head'],out['actual_main'] = refs
    if refs != [head,main]:
        return dict(out,blocker='wrong_head_or_main')
    out['frozen'] = {}
    for path,sha in FROZEN.items():
        found = call(root,['git','hash-object',path],timeout) if (root/path).is_file() else {}
        out['frozen'][path] = {'status':'PASS' if found.get('tail','').strip()==sha else 'FAIL',
                               'expected_blob':sha,'actual_blob':found.get('tail','').strip()}
    if any(v['status']!='PASS' for v in out['frozen'].values()):
        return dict(out,blocker='frozen_hash_mismatch')
    for name,argv in SUITES.items():
        missing = [f for f in argv if f.startswith(('research/','docs/')) and not (root/f).is_file()]
        out['suites'][name] = {'status':'NOT_RUN','reason':'missing_file','paths':missing} if missing else call(root,argv,timeout)
    out['ready'] = all(v['status']=='PASS' for v in out['suites'].values())
    return dict(out, blocker=None if out['ready'] else 'regression_unverified_or_failed')

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True)
    parser.add_argument('--head',required=True)
    parser.add_argument('--main',required=True)
    parser.add_argument('--receipt')
    args=parser.parse_args()
    result=validate(args.root,args.head,args.main)
    body=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if args.receipt:
        with open(args.receipt,'x',encoding='utf-8') as fp: fp.write(body)
    print(body)
    sys.exit(0 if result['ready'] else 1)
