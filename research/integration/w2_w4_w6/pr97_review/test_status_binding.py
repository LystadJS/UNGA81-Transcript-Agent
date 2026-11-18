"""Independent source-free status/base binding tests using disposable Git objects."""
import copy
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(os.environ['PR97_GATE_ROOT']).resolve()
sys.path.insert(0,str(ROOT))
g=importlib.import_module('gate')
original=importlib.import_module('test_gate')

class StatusBaseBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='pr97-status-binding-')
        self.repo=Path(self.temp.name)/'toy';self.repo.mkdir()
        g.git(self.repo,'init','-q')
        (self.repo/'fictional.txt').write_text('Synthetic metadata probe.\n')
        self.base=self.commit('base')
        (self.repo/'head.txt').write_text('Fictional proposed code.\n')
        self.head=self.commit('head')
        g.git(self.repo,'checkout','--detach','-q',self.base)
        (self.repo/'base.txt').write_text('Fictional base update.\n')
        self.newbase=self.commit('base advancement')
        merged=g.git(self.repo,'merge-tree','--write-tree',self.newbase,self.head).decode().strip()
        self.status=g.git(self.repo,'commit-tree',merged,'-p',self.newbase,'-p',self.head,data=b'Synthetic status envelope\n').decode().strip()
        self.identity={'event':'pull_request','status_sha':self.status,'head':self.head,'base':self.base,
                       'run_id':'1','attempt':'1','freshness':{'base_ref':'refs/heads/main'}}
    def tearDown(self):self.temp.cleanup()
    def commit(self,name):
        g.git(self.repo,'add','.')
        g.git(self.repo,'commit','-qm',name)
        return g.git(self.repo,'rev-parse','HEAD').decode().strip()
    def test_01_ancestor_event_base_resolves_only_to_proven_status_parent(self):
        refs=g.git(self.repo,'show-ref');index=g.git(self.repo,'write-tree')
        saved=copy.deepcopy(self.identity)
        actual=g.bind_pr_status_base(self.repo,self.identity)
        self.assertEqual(actual['base'],self.newbase)
        self.assertEqual(actual['event_base_sha'],self.base)
        self.assertEqual(actual['status_sha'],self.status)
        self.assertEqual(self.identity,saved)
        self.assertEqual(g.git(self.repo,'show-ref'),refs)
        self.assertEqual(g.git(self.repo,'write-tree'),index)
    def test_02_matching_event_base_is_preserved(self):
        self.identity['base']=self.newbase
        actual=g.bind_pr_status_base(self.repo,self.identity)
        self.assertEqual(actual['base'],actual['event_base_sha'])
    def test_03_wrong_status_head_is_rejected(self):
        self.identity['head']=self.base
        with self.assertRaises(g.Rejected):g.bind_pr_status_base(self.repo,self.identity)
    def test_04_single_parent_status_is_rejected(self):
        self.identity['status_sha']=self.newbase
        with self.assertRaises(g.Rejected):g.bind_pr_status_base(self.repo,self.identity)
    def test_05_nonancestor_event_base_is_rejected(self):
        self.identity['base']=self.head
        with self.assertRaises(g.Rejected):g.bind_pr_status_base(self.repo,self.identity)
    def test_06_forged_status_tree_is_rejected(self):
        bad=g.git(self.repo,'commit-tree',g.tree(self.repo,self.base),'-p',self.newbase,'-p',self.head,data=b'Wrong synthetic tree\n').decode().strip()
        self.identity['status_sha']=bad
        with self.assertRaises(g.Rejected):g.bind_pr_status_base(self.repo,self.identity)
    def test_07_new_live_base_after_resolution_still_fails_freshness(self):
        actual=g.bind_pr_status_base(self.repo,self.identity)
        with patch.object(g,'git',return_value=(self.base+'\trefs/heads/main\n').encode()):
            with self.assertRaises(g.Rejected):g.check_fresh(self.repo,actual)
    def test_08_snapshot_and_resolution_fields_are_bound_by_finalizer(self):
        for field in ('event_base_sha','base_resolution'):
            event=original.identity();records=original.bundles()
            event.update(event_base_sha='5'*40,base_resolution='verified_status_merge_first_parent')
            for b in records.values():b['identity'].update({k:event[k] for k in ('event_base_sha','base_resolution')})
            records['combined']['identity'][field]='wrong'
            with self.assertRaises(g.Rejected):g.validate_final(event,records,{'checks':{'result':'success'}})
    def test_09_push_and_merge_group_do_not_resolve_from_pr_parents(self):
        for event in ('push','merge_group'):
            ident={**self.identity,'event':event}
            with patch.object(g,'git',side_effect=AssertionError('Unexpected PR-only lookup')):
                self.assertEqual(g.bind_pr_status_base(self.repo,ident),ident)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(StatusBaseBindingTests))
    record={'suite':'independent-pr97-status-base-binding','tests_run':result.testsRun,
            'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
            'result':'pass' if result.wasSuccessful() and not result.skipped else 'fail',
            'real_sources_opened':0,'adoption_authorized':False,'merge_authorized':False,'publication_authorized':False}
    if os.environ.get('PR97_STATUS_RECEIPT'):Path(os.environ['PR97_STATUS_RECEIPT']).write_text(json.dumps(record,indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful() or bool(result.skipped))
