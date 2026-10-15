"""Independent synthetic negative controls and real-Git composition probes."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import gate as g
from run_suites import unittest_result, tap_result, runtimes

POLICY = g.load(g.ROOT/'policy.json')


def event():
    return {'repository':{'full_name':POLICY['repository']},'pull_request':{'number':95,
            'head':{'sha':'1'*40,'repo':{'full_name':POLICY['repository']}},
            'base':{'sha':'2'*40,'ref':'main'}}}


def identity():
    return g.event_identity(event(),'pull_request','3'*40,123,1)


def bundles():
    e = identity(); result = {}
    for mode in g.MODES:
        stage = 'integrated' if mode == 'combined' else 'bootstrap'
        i = {**e,'mode':mode,'stage':stage,'coverage':'gate_bootstrap_only' if stage=='bootstrap' else 'offline_synthetic_product',
             'tested_tree':'4'*40,'refs_unchanged':True,'controller_index_unchanged':True}
        suites = {k:{'result':'pass','tests':v,'skipped':0,'errors':0,'failures':0} for k,v in g.required_suites(stage).items()}
        r = {'mode':mode,'stage':stage,'coverage':i['coverage'],'identity_sha256':'a'*64,
             'result':'pass','errors':[],'skipped':[],'suites':suites,'holds':copy.deepcopy(g.HOLD)}
        result[mode] = {'identity':i,'receipt':r,'identity_sha256':'a'*64,'evidence_verified':True}
    return result


class FinalizerTests(unittest.TestCase):
    def validate(self,b=None,n=None):
        return g.validate_final(identity(), b if b is not None else bundles(), n if n is not None else {'checks':{'result':'success'}})
    def test_complete_bootstrap_is_not_product_authorization(self):
        r=self.validate();self.assertEqual(r['actual_stage'],'bootstrap');self.assertFalse(r['merge_authorized'])
    def test_failed_skipped_cancelled_or_missing_jobs_cannot_pass(self):
        for status in ('failure','skipped','cancelled',None,'neutral','timed_out'):
            with self.subTest(status=status),self.assertRaises(g.Rejected):self.validate(n={'checks':{'result':status}})
        with self.assertRaises(g.Rejected):self.validate(n={})
    def test_missing_extra_duplicate_mode_receipts(self):
        for mode in g.MODES:
            b=bundles();del b[mode]
            with self.assertRaises(g.Rejected):self.validate(b)
        b=bundles();b['extra']=b['head']
        with self.assertRaises(g.Rejected):self.validate(b)
    def test_stale_base_head_status_or_run_identity(self):
        for key in ('head','base','status_sha','run_id','attempt','event','freshness'):
            b=bundles();b['combined']['identity'][key]='wrong'
            with self.subTest(key=key),self.assertRaises(g.Rejected):self.validate(b)
    def test_failed_receipt_or_nonzero_errors(self):
        for key,value in [('result','fail'),('errors',['bad']),('skipped',['R']),('mode','other')]:
            b=bundles();b['head']['receipt'][key]=value
            with self.assertRaises(g.Rejected):self.validate(b)
    def test_suite_removed_failed_skipped_empty_or_fewer_tests(self):
        for key,value in [('tests',0),('result','skip'),('skipped',1),('errors',1),('failures',1)]:
            b=bundles();b['combined']['receipt']['suites']['browser'][key]=value
            with self.assertRaises(g.Rejected):self.validate(b)
        b=bundles();del b['combined']['receipt']['suites']['pr87']
        with self.assertRaises(g.Rejected):self.validate(b)
    def test_missing_native_r_or_browser_is_a_required_suite_failure(self):
        for suite in ('phase1','browser','pr93'):
            b=bundles();b['combined']['receipt']['suites'].pop(suite)
            with self.assertRaises(g.Rejected):self.validate(b)
    def test_missing_artifact_and_wrong_binding(self):
        b=bundles();b['head']['evidence_verified']=False
        with self.assertRaises(g.Rejected):self.validate(b)
        b=bundles();b['head']['receipt']['identity_sha256']='f'*64
        with self.assertRaises(g.Rejected):self.validate(b)
    def test_authority_escalation_and_stage_downgrade(self):
        b=bundles();b['head']['receipt']['holds']['merge_authorized']=True
        with self.assertRaises(g.Rejected):self.validate(b)
        b=bundles();b['combined']['identity']['stage']='bootstrap'
        with self.assertRaises(g.Rejected):self.validate(b)
    def test_unknown_stage_and_runtime_absence(self):
        with self.assertRaises(g.Rejected):g.required_suites('whatever')
        with patch('shutil.which',return_value=None),self.assertRaises(g.Rejected):runtimes(POLICY)


class ParserTests(unittest.TestCase):
    def test_retargeted_event_uses_actual_base(self):
        e=event();e['pull_request']['base']={'sha':'9'*40,'ref':'other'}
        r=g.event_identity(e,'pull_request','3'*40,123,1)
        self.assertEqual(r['base'],'9'*40);self.assertEqual(r['freshness']['base_ref'],'refs/heads/other')
    def test_push_and_merge_queue_identity(self):
        e={'repository':event()['repository'],'ref':'refs/heads/main','before':'2'*40,'after':'1'*40}
        self.assertEqual(g.event_identity(e,'push','1'*40,1,1)['base'],'2'*40)
        e['merge_group']={'head_sha':'1'*40,'base_sha':'2'*40,'head_ref':'refs/heads/gh-readonly-queue/x','base_ref':'refs/heads/main'}
        self.assertEqual(g.event_identity(e,'merge_group','1'*40,1,1)['head'],'1'*40)
    def test_manual_event_wrong_repository_fork_and_zero_sha_rejected(self):
        with self.assertRaises(g.Rejected):g.event_identity(event(),'workflow_dispatch','3'*40,1,1)
        for change in ('fork','repo','zero'):
            e=event()
            if change=='fork':e['pull_request']['head']['repo']['full_name']='evil/repo'
            elif change=='repo':e['repository']['full_name']='evil/repo'
            else:e['pull_request']['base']['sha']='0'*40
            with self.assertRaises(g.Rejected):g.event_identity(e,'pull_request','3'*40,1,1)
    def test_unittest_raw_ids_fail_on_skip_failure_or_duplicate(self):
        text='test_one (Sample.test_one) ... ok\n\nRan 1 test in 0.1s\n\nOK\n'
        self.assertEqual(unittest_result(text,1)['tests'],1)
        for bad in (text.replace('OK','OK (skipped=1)'),text.replace('... ok','... skipped'),text.replace('Ran 1 test','Ran 0 tests'),text+text):
            with self.assertRaises(g.Rejected):unittest_result(bad,1)
    def test_tap_is_complete_and_zero_skip(self):
        text='ok 1 - case\n# tests 1\n# pass 1\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 0\n'
        self.assertEqual(tap_result(text,1)['test_ids'],['case'])
        for key in ('fail','cancelled','skipped','todo'):
            with self.assertRaises(g.Rejected):tap_result(text.replace('# '+key+' 0','# '+key+' 1'),1)
    def test_missing_empty_duplicate_and_symlink_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x'
            with self.assertRaises(g.Rejected):g.load(p)
            for raw in ('','{"x":1,"x":2}'):
                p.write_text(raw)
                with self.assertRaises(g.Rejected):g.load(p)
            p.unlink();q=Path(d)/'y';q.write_text('{}');p.symlink_to(q)
            with self.assertRaises(g.Rejected):g.load(p)
    def test_output_cannot_overlap_repo_or_stale_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d)/'repo';r.mkdir()
            for p in (r,r/'nested',Path(d)):
                with self.assertRaises(g.Rejected):g.safe_output(p,[r])
            o=Path(d)/'out';g.safe_output(o,[r])
            with self.assertRaises(g.Rejected):g.safe_output(o,[r])
    def test_artifact_digest_path_and_absence_are_checked(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);g.dump(p/'identity.json',{})
            (p/'e.log').write_text('synthetic')
            g.dump(p/'receipt.json',{'files':{'e.log':g.sha(b'synthetic')}})
            self.assertTrue(g.read_bundle(p)['evidence_verified'])
            (p/'e.log').write_text('tamper')
            with self.assertRaises(g.Rejected):g.read_bundle(p)
            for name in ('../outside','/absolute'):
                g.dump(p/'receipt.json',{'files':{name:'x'}})
                with self.assertRaises(g.Rejected):g.read_bundle(p)
    def test_live_stale_base_is_fatal(self):
        i={'freshness':{'base_ref':'refs/heads/main'},'head':'1'*40,'base':'2'*40}
        with patch.object(g,'git',return_value=('9'*40+'\trefs/heads/main\n').encode()),self.assertRaises(g.Rejected):g.check_fresh('.',i)


class GitCompositionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.home=Path(self.tmp.name);self.repo=self.home/'repo';self.repo.mkdir()
        g.git(self.repo,'init','-q');g.git(self.repo,'config','user.name','Synthetic');g.git(self.repo,'config','user.email','synthetic@example.invalid')
        self.p=copy.deepcopy(POLICY)
        bridge=POLICY['payloads'][0]['integration_paths'][0]
        self.put(bridge,b'original synthetic bridge\n');self.put('data/do-not-open.txt',b'fictional sealed sentinel\n')
        self.base=self.commit('base');self.p['historical_main']=self.base
        source=g.ROOT.parents[3]
        for n in self.p['gate_paths']:self.put(n,(source/n).read_bytes())
        self.head=self.commit('gate')
        for payload in self.p['payloads']:
            g.git(self.repo,'checkout','--detach','-q',self.base if payload['number']==93 else self.base if payload['number']==82 else self.p['payloads'][0]['head_sha'])
            for name in payload['integration_paths']:self.put(name,('synthetic '+name+'\n').encode())
            payload['head_sha']=self.commit('payload-'+str(payload['number']))
        self.p['pr87']={'head_sha':self.p['payloads'][2]['head_sha'],'source_path':'research/integration/w2_w4_w6/pr92_review/test_review.py'}
        g.git(self.repo,'checkout','--detach','-q',self.head)
        self.e={**identity(),'head':self.head,'base':self.base}
    def tearDown(self):self.tmp.cleanup()
    def put(self,name,raw):
        f=self.repo/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw)
    def commit(self,label):
        g.git(self.repo,'add','.');g.git(self.repo,'commit','-qm',label)
        return g.git(self.repo,'rev-parse','HEAD').decode().strip()
    def test_combined_order_all_payloads_and_refs_are_preserved(self):
        before=g.git(self.repo,'show-ref');index=g.git(self.repo,'write-tree')
        r=g.prepare(self.repo,self.repo,self.home/'out','combined',self.e,self.p)
        self.assertEqual([x['pr'] for x in r['assembly']],[82,92,93]);self.assertEqual(r['stage'],'integrated')
        self.assertEqual(g.git(self.repo,'show-ref'),before);self.assertEqual(g.git(self.repo,'write-tree'),index)
        self.assertNotIn('data/do-not-open.txt',r['materialized_paths'])
        self.assertEqual(g.listing(self.repo,r['tested_tree'])['data/do-not-open.txt'],g.listing(self.repo,self.base)['data/do-not-open.txt'])
    def test_head_and_effective_bootstrap_are_not_combined_coverage(self):
        for mode in ('head','effective-tree'):
            r=g.prepare(self.repo,self.repo,self.home/mode,mode,self.e,self.p)
            self.assertEqual(r['coverage'],'gate_bootstrap_only');self.assertEqual(r['assembly'],[])
    def test_deleted_gate_or_stage_rejected(self):
        (self.repo/g.STAGE).unlink();bad=self.commit('remove-stage')
        with self.assertRaises(g.Rejected):g.stage_in(self.repo,bad,self.p)
        g.git(self.repo,'checkout','--detach','-q',self.head)
        (self.repo/self.p['gate_paths'][0]).unlink();bad=self.commit('remove-gate')
        with self.assertRaises(g.Rejected):g.stage_in(self.repo,bad,self.p)
    def test_partial_product_cannot_be_bootstrap(self):
        self.put(self.p['payloads'][0]['integration_paths'][1],b'partial\n');bad=self.commit('partial')
        with self.assertRaises(g.Rejected):g.stage_in(self.repo,bad,self.p)
    def test_missing_product_does_not_downgrade_complete_stage(self):
        ref=g.merged(self.repo,self.head,self.p['payloads'][0]['head_sha'])
        t=g.set_stage(self.repo,ref,'phase1');self.assertEqual(g.stage_in(self.repo,t,self.p),'phase1')
        with self.assertRaises(g.Rejected):g.stage_in(self.repo,g.set_stage(self.repo,ref,'phase2'),self.p)
    def test_conflict_is_not_a_successful_dry_run(self):
        name=self.p['payloads'][0]['integration_paths'][0]
        self.put(name,b'conflicting coordinator version\n');bad=self.commit('conflict')
        with self.assertRaises(g.Rejected):g.merged(self.repo,bad,self.p['payloads'][0]['head_sha'])
    def test_symlink_mode_is_not_accepted_as_gate_code(self):
        p=self.repo/self.p['gate_paths'][0];p.unlink();p.symlink_to('policy.json');bad=self.commit('symlink')
        with self.assertRaises(g.Rejected):g.stage_in(self.repo,bad,self.p)


class WorkflowTests(unittest.TestCase):
    def test_required_workflow_has_no_optional_or_publishing_path(self):
        source=g.ROOT.parents[3];text=(source/'.github/workflows/coord-us-relative-integration.yml').read_text()
        for token in ('pull_request:','edited','push:','merge_group:','contents: read','name: usref-integration-required','needs: [checks]','if: always()'):
            self.assertIn(token,text)
        for token in ('continue-on-error','paths-ignore:','\n    paths:','pull_request_target:','workflow_dispatch:',
                      'pages: write','id-token: write','deploy-pages','build_pages.py','git push','gh pr merge'):
            self.assertNotIn(token,text)
        self.assertIn('--require-complete',(g.ROOT/'run_suites.py').read_text())
        self.assertEqual(len({p for x in POLICY['payloads'] for p in x['integration_paths']}),31)


if __name__=='__main__':unittest.main()
