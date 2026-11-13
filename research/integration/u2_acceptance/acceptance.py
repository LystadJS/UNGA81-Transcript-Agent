"""Coordinator-only full-checkout execution. Never modifies branch refs or release files."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True);p.add_argument('--mode',choices=['worker-head','effective-tree'],required=True);a=p.parse_args()
root=Path(a.root).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
review=Path(__file__).resolve().parent
head=os.environ['U2_HEAD'];c0=os.environ['C0_HEAD'];main=os.environ['MAIN_HEAD'];u1=os.environ['U1_HEAD']
def git(*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def require(ok,message):
    if not ok:raise RuntimeError(message)
def temporary_commit(tree,left,right):
    return git('-c','user.name=Synthetic coordinator QA','-c','user.email=qa@example.invalid','commit-tree',tree,'-p',left,'-p',right,'-m','Disposable acceptance tree; no branch mutation')
require(git('rev-parse','HEAD')==head,'wrong U2 checkout')
require(git('rev-parse','origin/main')==main,'refresh main pin before accepting')
for tip in [head,u1]:subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',c0,tip],check=True)
paths=git('diff','--name-only',c0,head).splitlines()
require(paths and all(x.startswith('research/integration/question_router/') for x in paths),'U2 ownership violation')
require(all(x.startswith('100644 blob ') for x in git('ls-tree','-r',head,'--','research/integration/question_router').splitlines()),'U2 nonordinary files')
subprocess.run([sys.executable,str(root/'research/integration/question_router/tests/guard_owned.py'),'--head',head],cwd=root,check=True,stdout=(out/'worker-ownership.json').open('w'))
consumer=out.parent/('u1-consumer-'+a.mode)
subprocess.run(['git','-C',str(root),'worktree','add','--detach',str(consumer),u1],check=True)
require(subprocess.check_output(['git','-C',str(consumer),'rev-parse','HEAD'],text=True).strip()==u1,'wrong consumer checkout')
main_tree=git('merge-tree','--write-tree',main,head)
main_composition=temporary_commit(main_tree,main,head)
combined_tree=git('merge-tree','--write-tree',main_composition,u1)
if a.mode=='effective-tree':
    commit=temporary_commit(combined_tree,main_composition,u1)
    subprocess.run(['git','-C',str(root),'checkout','--detach',commit],check=True)
    require(git('rev-parse','HEAD^{tree}')==combined_tree,'wrong composed tree')
    require(not git('diff',u1,'HEAD','--','site/parallel/w07-diplomat-ux'),'consumer was changed')
    allowed=('research/integration/product_contracts/','research/integration/question_router/','site/parallel/w07-diplomat-ux/')
    named={'docs/parallel-work/C0_PRODUCT_OWNERSHIP.md','docs/parallel-work/C0_WORKER_HANDOFFS.md','docs/parallel-work/C0_IMPLEMENTATION_ACCEPTANCE_2026-10-15.md','docs/parallel-work/c0-ownership.json','.github/workflows/c0-product-contracts.yml'}
    require(all(x.startswith(allowed) or x in named for x in git('diff','--name-only',main,'HEAD').splitlines()),'unexpected effective-tree change')
    consumer=root
require(not git('diff',c0,'HEAD','--','research/integration/product_contracts','docs/parallel-work/source-inventory-v1.cjs','docs/parallel-work/source-inventory-v1.schema.json'),'protected dependency changed')
identities={'mode':a.mode,'worker':head,'c0':c0,'main':main,'consumer':u1,'actual_head':git('rev-parse','HEAD'),'actual_tree':git('rev-parse','HEAD^{tree}'),'main_u2_tree':main_tree,'u1_u2_effective_tree':combined_tree,'u2_changed_paths':paths,'synthetic_only':True,'publication_eligible':False}
(out/'identities.json').write_text(json.dumps(identities,indent=2)+'\n')
(out/'u2-blobs.txt').write_text(git('ls-tree','-r','HEAD','--','research/integration/question_router')+'\n')
(out/'u1-blobs.txt').write_text(git('ls-tree','-r',u1,'--','site/parallel/w07-diplomat-ux')+'\n')
env=os.environ.copy();env.update(U2_CHECKOUT=str(root),U1_CHECKOUT=str(consumer))
commands=[
 ('dependencies',['node','research/integration/question_router/tests/verify_dependencies.mjs','--with-u1']),
 ('u2',['node','--test','research/integration/question_router/tests/test_router.mjs']),
 ('u1-integration',['node','--test','research/integration/question_router/tests/test_u1_integration.mjs']),
 ('u1-original',['node','--test',str(consumer/'site/parallel/w07-diplomat-ux/tests/test_controller.mjs')]),
 ('c0',['node','--test',*[str(x) for x in sorted((root/'research/integration/product_contracts').glob('test_*.mjs'))]]),
 ('emission',['node','research/integration/product_contracts/emit_contracts.mjs',str(out/'emission')]),
 ('schemas',[sys.executable,'research/integration/product_contracts/check_schemas.py',str(out/'emission')]),
 ('emission-replay',['node','research/integration/product_contracts/emit_contracts.mjs',str(out/'emission-replay')]),
 ('schema-replay',['diff','-rq',str(out/'emission'),str(out/'emission-replay')]),
 ('interchange',['node','docs/parallel-work/validate-contract.cjs']),
 ('inventory',['node','docs/parallel-work/test-source-inventory-v1.cjs']),
 ('comparability',['node','--test','research/source_comparability/audit.test.cjs','research/source_comparability/audit.integration.test.cjs']),
 ('w1',['node','research/validation_framework/tests/test_historical_link.cjs']),
 ('pr71',[sys.executable,'-m','unittest','discover','-s','research/reproducibility_audit','-p','test_*.py','-v']),
 ('demo-1',['node','research/integration/question_router/demo.mjs']),
 ('demo-2',['node','research/integration/question_router/demo.mjs']),
 ('demo-replay',['cmp',str(out/'demo-1.log'),str(out/'demo-2.log')]),
 ('independent',['node','--test',str(review/'test_review.mjs')]),
 ('browser',[sys.executable,str(review/'browser_composition.py'),'--output',str(out/'browser')]),
 ('unchanged-tracked-files',['git','diff','--exit-code']),
]
results=[]
for name,command in commands:
    try:
        completed=subprocess.run(command,cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180)
        text=completed.stdout;code=completed.returncode
    except subprocess.TimeoutExpired as error:
        text=str(error);code=124
    (out/(name+'.log')).write_text(text)
    result={'name':name,'command':command,'exit_code':code}
    matches=dict(re.findall(r'^# (tests|pass|fail|skipped|cancelled) (\d+)$',text,re.M))
    if matches:
        result['counts']={k:int(v) for k,v in matches.items()}
        if int(matches.get('skipped',0)) or int(matches.get('cancelled',0)):result['acceptance_error']='skipped_or_cancelled'
    results.append(result);print(json.dumps(result),flush=True)
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
for file in review.glob('*'):
    if file.is_file():(out/('reviewer-'+file.name+'.sha256')).write_text(hashlib.sha256(file.read_bytes()).hexdigest()+'\n')
status='PASS' if all(r['exit_code']==0 and 'acceptance_error' not in r for r in results) else 'FAIL'
(out/'decision.json').write_text(json.dumps({'status':status,'scope':'synthetic_execution_only','independent_engineering_review_required':True,'publication_eligible':False},indent=2)+'\n')
manifest={str(x.relative_to(out)):hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(out.rglob('*')) if x.is_file()}
(out/'SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
raise SystemExit(0 if status=='PASS' else 1)
