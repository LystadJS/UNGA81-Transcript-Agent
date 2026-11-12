"""Invented aggregate receipts; never real transcripts or owner labels."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
import io

from un_transcript.monitoring import operational_receipt


def fixture():
    return {'schema':'un.pipeline-run.v1', 'run_id':'20261112T120000Z-abcdef123456',
            'status':'partial', 'generated_at':'2026-11-12T12:00:10.123456Z',
            'private_publication':'published', 'public_publication':'published',
            'coverage':{'meetings':8, 'stored_meetings':3, 'segments':30, 'inventory_dates':2,
                        'statuses':{'collected':3, 'failed':1, 'pending':1, 'empty_transcript':1, 'excluded_reserved':2}},
            'meetings_downloaded':3, 'bytes_downloaded':10000,
            'model_status':{'accepted':False, 'reason':'SECRET internal reason'},
            'snapshot':'/private/SECRET/database', 'raw_text':'SECRET transcript',
            'annotation':{'label':'SECRET'}, 'public_error_type':'SECRET'}


class Monitoring(unittest.TestCase):
    def project(self, value, **kwargs):
        return operational_receipt(value, run_id='123', attempt='2', event='schedule',
                                   processing_status='success', recorded_at='2026-11-12T12:01:00Z', **kwargs)

    def test_allowlist_excludes_nested_private_material(self):
        result=self.project(fixture(), before={'retained_storage_bytes':100, 'storage_budget_bytes':1000,
                                               'token':'SECRET', 'private_url':'SECRET'})
        self.assertNotIn('SECRET', json.dumps(result))
        self.assertEqual(result['workflow_attempt'], 2)
        self.assertEqual(result['snapshot']['coverage']['meetings'], 8)
        self.assertFalse(result['snapshot']['model_accepted'])
        self.assertFalse(result['storage']['account_quota_verified'])

    def test_missing_completed_receipt_does_not_claim_snapshot(self):
        result=operational_receipt(None, run_id='123', attempt='1', event='workflow_dispatch', processing_status='failure')
        self.assertFalse(result['completed_pipeline_receipt'])
        self.assertIsNone(result['snapshot'])
        self.assertIsNone(result['storage']['private_after'])
        self.assertEqual(result['processing_status'],'failure')

    def test_public_failure_retains_private_success_and_safe_diagnostics(self):
        value=fixture();value.update(public_publication='failed', public_http_status=429,
                                     public_storage_operation='activate_pointer')
        result=self.project(value)['snapshot']
        self.assertEqual(result['private_publication'],'published')
        self.assertEqual(result['public_publication'],'failed')
        self.assertEqual(result['public_http_status'],429)
        self.assertEqual(result['public_storage_operation'],'activate_pointer')
        value.update(public_storage_operation='SECRET',public_http_status='SECRET')
        self.assertNotIn('SECRET',json.dumps(self.project(value)))

    def test_capacity_diagnostics_survive_strict_receipt_validation(self):
        from un_transcript.monitoring import validate_operational_receipt
        for operation in ('capacity_refs','capacity_commits','capacity_tree'):
            value=fixture();value.update(public_publication='failed',public_http_status=503,
                                         public_storage_operation=operation)
            result=self.project(value)
            self.assertEqual(result['snapshot']['public_storage_operation'],operation)
            self.assertEqual(validate_operational_receipt(result,run_id=123,attempt=2,event='schedule'),result)
            self.assertNotIn('SECRET',json.dumps(result))

    def test_unknown_status_and_incoherent_counts_fail_closed(self):
        for field, value in [('meetings',9), ('stored_meetings',9), ('segments',True)]:
            with self.subTest(field=field):
                item=fixture();item['coverage'][field]=value
                with self.assertRaises(ValueError):self.project(item)
        item=fixture();item['coverage']['statuses']['SECRET']=1
        with self.assertRaises(ValueError):self.project(item)

    def test_absent_and_removed_inventory_meetings_remain_visible(self):
        item=fixture()
        del item['coverage']['statuses']['failed']
        del item['coverage']['statuses']['pending']
        item['coverage']['statuses'].update(not_in_inventory=1,no_longer_listed=1)
        result=self.project(item)
        self.assertEqual(result['snapshot']['coverage']['statuses']['not_in_inventory'],1)
        self.assertEqual(result['snapshot']['coverage']['statuses']['no_longer_listed'],1)
        self.assertEqual(result['snapshot']['coverage']['meetings'],8)

    def test_private_path_cannot_be_snapshot_identity(self):
        item=fixture();item['run_id']='/private/SECRET'
        with self.assertRaises(ValueError) as error:self.project(item)
        self.assertNotIn('SECRET',str(error.exception))

    def test_workflow_tool_projects_exact_file_only(self):
        from tools.write_operational_receipt import main
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'un-warehouse').mkdir()
            (root/'un-warehouse/last-run.json').write_text(json.dumps(fixture()))
            (root/'un-warehouse/annotations.json').write_text('DO NOT READ')
            env={'RUNNER_TEMP':tmp,'GITHUB_RUN_ID':'123','GITHUB_RUN_ATTEMPT':'1',
                 'GITHUB_EVENT_NAME':'schedule','PROCESSING_STATUS':'success'}
            with patch.dict(os.environ,env),redirect_stdout(io.StringIO()):main()
            result=json.loads((root/'operational-receipt.json').read_text())
            self.assertNotIn('SECRET',json.dumps(result))
            self.assertTrue(result['completed_pipeline_receipt'])
