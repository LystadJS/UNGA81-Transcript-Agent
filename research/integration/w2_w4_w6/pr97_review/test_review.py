"""Independent PR97 evidence-boundary review; no product edits or real sources.

The immutable successful artifacts are positive controls, not fresh native-R or
Chromium execution. Mutations are confined to new temporary copies. Rejection
assertions intentionally fail on the reviewed candidate; they are not xfails.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HEAD = 'ab559b74842e9a9165bf619f4869015d90588e8c'
BASE = 'da4ab9ed11dba3693d11aa12f5333963b1b85478'
PREFIX = 'research/integration/w2_w4_w6/usref_integration/'
PINS = {
 'gate.py':'be9f08e6d6cc7f9d53d27d87de66c16ba7aee684',
 'run_suites.py':'b7e037f5ed67b836be19c91c0c687302d90302c9',
 'test_gate.py':'4c247360736a2bcda8f5a944fd2ae9c66fcb53d1',
 'policy.json':'b93aad2160c5a5d1c223737c47da952b68759d0e',
 'stage.json':'98e1cee7ddaee8581e1c694ca24f10ae4dcaf5a4',
 'README.md':'6c7669c77e35dfcd683e72a3c61d2ddb8a2250c9',
}
WORKFLOW_PIN = '8ede9e6bbbd2c2f3808b85900f25ef9cdff08650'
MODES = ('head','effective-tree','combined')
EVENT_KEYS = ('event','status_sha','head','base','run_id','attempt','freshness')
OBSERVATIONS = []
G = S = POLICY = ARTIFACTS = OUTPUT = None


def read(path):
    return json.loads(Path(path).read_text())


def write(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def initialize(gate_root, artifacts, output):
    global G, S, POLICY, ARTIFACTS, OUTPUT
    root = gate_root.resolve()
    for name, expected in PINS.items():
        raw = (root/name).read_bytes()
        actual = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if actual != expected:
            raise ValueError('Candidate source changed: '+name)
    raw = (root.parents[3]/'.github/workflows/coord-us-relative-integration.yml').read_bytes()
    if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() != WORKFLOW_PIN:
        raise ValueError('Candidate workflow changed')
    sys.path.insert(0, str(root))
    G = importlib.import_module('gate'); S = importlib.import_module('run_suites')
    POLICY = read(root/'policy.json'); ARTIFACTS = artifacts.resolve(); OUTPUT = output.resolve()
    OUTPUT.mkdir(parents=True, exist_ok=True)


def acceptance(home):
    """Use all three actual finalizer validators, never mocked acceptance counts."""
    bundles = {}
    for mode in MODES:
        directory = home/('usref-gate-'+mode)
        bundle = G.read_bundle(directory)
        S.audit_bundle(directory, bundle, POLICY)
        bundles[mode] = bundle
    event = {k: bundles['head']['identity'][k] for k in EVENT_KEYS}
    return G.validate_final(event, bundles, {'checks': {'result': 'success'}})


def verify_pristine():
    """Independent archive-member/semantic checks in addition to candidate replay."""
    identities = []
    members = 0
    for mode in MODES:
        home = ARTIFACTS/('usref-gate-'+mode)
        identity = read(home/'identity.json'); receipt = read(home/'receipt.json')
        assert identity['head'] == HEAD and identity['base'] == BASE
        assert identity['run_id'] == '38806920470' and identity['attempt'] == '1'
        assert receipt['identity_sha256'] == sha(home/'identity.json')
        for name, expected in receipt['files'].items():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            assert sha(home/name) == expected
            members += 1
        assert receipt['result'] == 'pass' and not receipt['errors'] and not receipt['skipped']
        identities.append(identity)
    combined = ARTIFACTS/'usref-gate-combined'
    observed = read(combined/'evidence/independent/observations.json')
    assert observed['historical_targets'] == observed['resolved_historical_targets'] == 444
    assert observed['independent_ready_profiles'] == 168
    assert observed['independent_comparisons'] == 240 and observed['independent_transitions'] == 192
    axe = read(combined/'evidence/browser/axe-results.json')
    assert len(axe) == 9 and all(not scan['violations'] for scan in axe)
    resolution = read(combined/'evidence/independent/contrast-resolution.json')
    historical = [r for x in resolution if x['source']=='historical-axe-targets' for r in x['records']]
    assert len(historical) == 444
    assert all(r['passed'] is True and r['minimum_ratio'] >= r['threshold'] for r in historical)
    for rel in ('evidence/phase1-original.json','evidence/pr87-original.json',
                'evidence/browser/browser-receipt.json','evidence/independent/review-receipt.json'):
        rec = read(combined/rel)
        assert rec['result'] == 'pass' and not rec['failures'] and not rec['errors'] and not rec['skipped']
    assert read(combined/'evidence/phase1-original.json')['head_sha'] == HEAD
    decision = acceptance(ARTIFACTS)
    assert decision['combined_tree'] == 'e9f9dc9d4b8951059d6a210f7a99d3425c699f87'
    assert not decision['merge_authorized'] and not decision['publication_authorized']
    result = {'source_pins':7,'verified_evidence_members':members,'result':'pass',
              'historical_run':'38806920470','candidate':HEAD,'base':BASE,
              'native_and_browser_execution':'historical_receipts_reverified_not_rerun',
              'decision_replay':decision}
    write(OUTPUT/'pristine-verification.json', result)
    return result


def verify_git(repo):
    """Reconstruct each tree independently with Git, not candidate tree helpers.

    Only metadata, stage.json and allowlisted blob identities are inspected.
    Temporary commit objects and a temporary index are never attached to refs.
    """
    env = {**os.environ, 'GIT_AUTHOR_NAME':'Independent synthetic tree review',
           'GIT_COMMITTER_NAME':'Independent synthetic tree review',
           'GIT_AUTHOR_EMAIL':'synthetic@example.invalid','GIT_COMMITTER_EMAIL':'synthetic@example.invalid',
           'GIT_AUTHOR_DATE':'2000-01-01T00:00:00Z','GIT_COMMITTER_DATE':'2000-01-01T00:00:00Z'}
    def git(*args, data=None, extra=None):
        proc = subprocess.run(['git','-C',str(repo),*args],input=data,capture_output=True,
                              env={**env,**(extra or {})},timeout=120,check=True)
        return proc.stdout
    def tree(ref):return git('rev-parse',ref+'^{tree}').decode().strip()
    def merge(left,right):
        t=git('merge-tree','--write-tree',left,right).decode().strip()
        return git('commit-tree',t,'-p',left,'-p',right,data=b'Independent unreachable tree envelope\n').decode().strip()
    def listing(ref):
        result={}
        for row in git('ls-tree','-rz',ref).split(b'\0'):
            if row:
                meta,name=row.split(b'\t',1);result[name.decode()]=meta.decode().split()
        return result
    before_refs=git('show-ref'); before_index=git('write-tree')
    effective=merge(HEAD,BASE)
    actual={'head':tree(HEAD),'effective-tree':tree(effective)}
    ref=effective; stages=[]
    for payload in POLICY['payloads']:
        ref=merge(ref,payload['head_sha']);stages.append({'pr':payload['number'],'tree':tree(ref)})
    with tempfile.TemporaryDirectory(prefix='pr97-independent-index-') as tmp:
        isolated={'GIT_INDEX_FILE':str(Path(tmp)/'index')}
        git('read-tree',ref,extra=isolated)
        stage=(json.dumps({'schema':'un.usref-adoption-stage.v1','stage':'integrated'},indent=2)+'\n').encode()
        blob=git('hash-object','-w','--stdin',data=stage).decode().strip()
        git('update-index','--add','--cacheinfo','100644,'+blob+','+PREFIX+'stage.json',extra=isolated)
        actual['combined']=git('write-tree',extra=isolated).decode().strip()
    for mode,t in actual.items():
        assert t==read(ARTIFACTS/('usref-gate-'+mode)/'identity.json')['tested_tree']
    result_listing=listing(actual['combined']); initial_listing=listing(actual['effective-tree'])
    paths={path for p in POLICY['payloads'] for path in p['integration_paths']}
    changed={p for p in set(initial_listing)|set(result_listing) if initial_listing.get(p)!=result_listing.get(p)}
    assert changed <= paths|{PREFIX+'stage.json'} and set(initial_listing)<=set(result_listing)
    for p in POLICY['payloads']:
        original=listing(p['head_sha'])
        for name in p['integration_paths']:assert result_listing[name]==original[name]
    assert git('show-ref')==before_refs and git('write-tree')==before_index
    assert len(paths)==31
    write(OUTPUT/'independent-trees.json',{'result':'pass','trees':actual,'assembly':stages,
         'payload_paths':31,'refs_unchanged':True,'controller_index_unchanged':True,
         'real_sources_opened':0})


class IndependentRejectionTests(unittest.TestCase):
    def mutate(self, kind):
        with tempfile.TemporaryDirectory(prefix='pr97-synthetic-evidence-') as tmp:
            home=Path(tmp)/'evidence';shutil.copytree(ARTIFACTS,home)
            c=home/'usref-gate-combined';r=read(c/'receipt.json')
            def replace(rel,value):
                write(c/rel,value);r['files'][rel]=sha(c/rel)
            if kind=='missing-build':
                shutil.rmtree(c/'evidence/build')
                r['files']={k:v for k,v in r['files'].items() if not k.startswith('evidence/build/')}
            elif kind=='missing-observations':
                rel='evidence/independent/observations.json';(c/rel).unlink();del r['files'][rel]
            elif kind=='failed-contrast':
                rel='evidence/independent/contrast-resolution.json';v=read(c/rel)
                v[0]['records'][0]['passed']=False;v[0]['records'][0]['minimum_ratio']=1.0;replace(rel,v)
            elif kind=='axe-violation':
                rel='evidence/browser/axe-results.json';v=read(c/rel)
                v[0]['violations']=[{'id':'color-contrast','impact':'serious','nodes':[]}];replace(rel,v)
            elif kind=='wrong-native-head':
                rel='evidence/phase1-original.json';v=read(c/rel);v['head_sha']='f'*40;replace(rel,v)
            elif kind=='mismatched-native-count':
                rel='evidence/phase1-original.json';v=read(c/rel);v['tests_run']=999;replace(rel,v)
            elif kind=='renamed-r1-test':
                rel='evidence/logs/phase1.log'
                old='test_original_meeting_collision_and_additional_opaque_ids';new='test_unrelated_placeholder'
                raw=(c/rel).read_text();assert old in raw
                (c/rel).write_text(raw.replace(old,new));r['files'][rel]=sha(c/rel)
                r['suites']['phase1']['log_sha256']=r['files'][rel]
                r['suites']['phase1']['test_ids']=[x.replace(old,new) for x in r['suites']['phase1']['test_ids']]
            elif kind=='bad-log-hash':
                (c/'evidence/logs/phase1.log').write_text('damaged')
            elif kind=='missing-mode':shutil.rmtree(home/'usref-gate-head')
            elif kind=='missing-log':
                rel='evidence/logs/phase1.log';(c/rel).unlink();del r['files'][rel]
            elif kind=='skipped-native':
                rel='evidence/phase1-original.json';v=read(c/rel);v['skipped']=['R absent'];replace(rel,v)
            elif kind=='wrong-outer-head':
                path=c/'identity.json';v=read(path);v['head']='f'*40;write(path,v);r['identity_sha256']=sha(path)
            elif kind=='authority':r['holds']['merge_authorized']=True
            else:raise ValueError(kind)
            write(c/'receipt.json',r)
            for mode in MODES:
                p=home/('usref-gate-'+mode)/'identity.json'
                if p.exists() and kind!='wrong-outer-head':
                    assert p.read_bytes()==(ARTIFACTS/('usref-gate-'+mode)/'identity.json').read_bytes()
            try:
                verdict=acceptance(home); rejected=False;message=verdict['result']
            except (G.Rejected,FileNotFoundError) as exc:
                rejected=True;message=str(exc)
            OBSERVATIONS.append({'probe':kind,'expected':'reject','actual':'rejected' if rejected else 'accepted',
                                 'detail':message,'pristine_inputs_changed':False})
            return rejected

    def test_01_pristine_evidence_is_accepted(self):self.assertEqual(acceptance(ARTIFACTS)['result'],'pass')
    def test_02_missing_mode_is_rejected(self):self.assertTrue(self.mutate('missing-mode'))
    def test_03_missing_raw_log_is_rejected(self):self.assertTrue(self.mutate('missing-log'))
    def test_04_corrupt_log_hash_is_rejected(self):self.assertTrue(self.mutate('bad-log-hash'))
    def test_05_skipped_native_test_is_rejected(self):self.assertTrue(self.mutate('skipped-native'))
    def test_06_stale_outer_identity_is_rejected(self):self.assertTrue(self.mutate('wrong-outer-head'))
    def test_07_authority_escalation_is_rejected(self):self.assertTrue(self.mutate('authority'))
    def test_08_missing_mandatory_build_is_rejected(self):self.assertTrue(self.mutate('missing-build'),'Finalizer accepted missing build/manifest evidence')
    def test_09_missing_observation_coverage_is_rejected(self):self.assertTrue(self.mutate('missing-observations'),'Finalizer accepted missing coverage evidence')
    def test_10_failed_measured_contrast_is_rejected(self):self.assertTrue(self.mutate('failed-contrast'),'Finalizer accepted a measured contrast failure')
    def test_11_axe_violation_is_rejected(self):self.assertTrue(self.mutate('axe-violation'),'Finalizer accepted an explicit axe violation')
    def test_12_native_head_must_match_execution(self):self.assertTrue(self.mutate('wrong-native-head'),'Finalizer accepted wrong native execution head')
    def test_13_native_count_must_match_raw_log(self):self.assertTrue(self.mutate('mismatched-native-count'),'Finalizer accepted 999 native tests against 40 raw IDs')
    def test_14_required_regression_id_cannot_be_replaced(self):self.assertTrue(self.mutate('renamed-r1-test'),'Finalizer accepted a replaced retained R1 regression ID')
    def test_15_unlisted_source_like_file_is_not_materialized(self):
        with tempfile.TemporaryDirectory(prefix='pr97-synthetic-source-') as temp:
            root=Path(temp);repo=root/'toy';repo.mkdir()
            G.git(repo,'init','-q')
            name='research/longitudinal/private/synthetic-transcript.txt'
            p=repo/name;p.parent.mkdir(parents=True);p.write_text('FICTIONAL sentinel only; no real transcript.\n')
            G.git(repo,'add','.');G.git(repo,'commit','-qm','Synthetic source boundary probe')
            ref=G.git(repo,'rev-parse','HEAD').decode().strip()
            refs=G.git(repo,'show-ref');index=G.git(repo,'write-tree')
            try:
                materialized=G.materialize(repo,ref,root/'output',POLICY)
                leaked=name in materialized and (root/'output'/name).is_file()
            except G.Rejected:
                leaked=False
            assert G.git(repo,'show-ref')==refs and G.git(repo,'write-tree')==index
            OBSERVATIONS.append({'probe':'unlisted-source-like-file','expected':'exclude_or_reject',
                                 'actual':'materialized' if leaked else 'excluded','real_sources_opened':0})
            self.assertFalse(leaked,'Prefix/suffix policy materialized an unreviewed source-like file')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gate-root',type=Path,required=True)
    parser.add_argument('--artifacts',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--metadata-repo',type=Path)
    args=parser.parse_args();initialize(args.gate_root,args.artifacts,args.out)
    verify_pristine()
    if args.metadata_repo:verify_git(args.metadata_repo)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(IndependentRejectionTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    write(OUTPUT/'probes.json',OBSERVATIONS)
    write(OUTPUT/'review-receipt.json',{'schema':'un.pr97-independent-review.v1','candidate':HEAD,'base':BASE,
         'reviewer_commit':os.environ.get('REVIEWER_SHA'),'review_run':os.environ.get('GITHUB_RUN_ID'),
         'mode':os.environ.get('REVIEW_MODE','local_source_copy'),'tests_run':result.testsRun,
         'failures':[str(t) for t,_ in result.failures],'errors':[str(t) for t,_ in result.errors],
         'skipped':[str(t) for t,_ in result.skipped],
         'result':'pass' if result.wasSuccessful() and not result.skipped else 'changes_required',
         'metadata_reconstruction':'pass' if args.metadata_repo else 'not_executed_locally',
         'native_R_Chromium_suites':'historical_evidence_verified_not_rerun',
         'adoption_authorized':False,'merge_authorized':False,'publication_authorized':False,'real_sources_opened':0})
    return 0 if result.wasSuccessful() and not result.skipped else 1


if __name__=='__main__':raise SystemExit(main())
