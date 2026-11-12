import io
import hashlib
import json
import unittest
from unittest.mock import Mock
import zipfile
from un_transcript.monitoring import operational_receipt
from un_transcript.run_inspection import inspect_run, receipt_from_zip
from test_monitoring import fixture


def receipt():
    return operational_receipt(fixture(),run_id=123,attempt=1,event='schedule',processing_status='success')


def zipped(value, name='operational-receipt.json'):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as archive:archive.writestr(name,json.dumps(value))
    return stream.getvalue()


class Inspection(unittest.TestCase):
    def apis(self, artifact=True):
        value=receipt();data=zipped(value)
        def api(endpoint):
            if '/jobs?' in endpoint:
                return {'total_count':1,'jobs':[{'status':'completed','completed_at':'2026-11-12T12:02:00Z','private':'SECRET'}]}
            if '/artifacts?' in endpoint:
                return {'total_count':1 if artifact else 0,'artifacts':[{'id':456,'name':'operational-receipt-1','size_in_bytes':len(data),'expired':False,'archive_download_url':'https://untrusted/SECRET'}] if artifact else []}
            return {'id':123,'run_attempt':1,'path':'.github/workflows/operational-pipeline.yml',
                    'event':'schedule','status':'completed','conclusion':'success',
                    'created_at':'2026-11-12T11:17:00Z','run_started_at':'2026-11-12T11:18:00Z'}
        return api,Mock(return_value=data)

    def test_actual_attempt_artifact_and_job_timing_are_bound(self):
        api,binary=self.apis();value=inspect_run(123,api=api,binary=binary)
        self.assertEqual(value['receipt_state'],'verified')
        self.assertEqual(value['last_job_completed_at'],'2026-11-12T12:02:00Z')
        self.assertNotIn('SECRET',json.dumps(value))
        self.assertFalse(value['operational_acceptance'])
        self.assertEqual(binary.call_args.args[0],'repos/LystadJS/UNGA81-Transcript-Agent/actions/artifacts/456/zip')

    def test_old_success_without_receipt_is_explicitly_missing(self):
        api,binary=self.apis(False);value=inspect_run(123,api=api,binary=binary)
        self.assertEqual(value['conclusion'],'success')
        self.assertEqual(value['receipt_state'],'missing')
        self.assertIsNone(value['receipt']);binary.assert_not_called()

    def test_extra_private_fields_and_wrong_attempt_rejected(self):
        value=receipt();value['private_annotations']=['SECRET']
        with self.assertRaises(ValueError):receipt_from_zip(zipped(value),run_id=123,attempt=1,event='schedule')
        with self.assertRaises(ValueError):receipt_from_zip(zipped(receipt()),run_id=123,attempt=2,event='schedule')
        value=receipt();value['snapshot']['coverage']['private']='SECRET'
        with self.assertRaises(ValueError):receipt_from_zip(zipped(value),run_id=123,attempt=1,event='schedule')

    def test_wrong_archive_member_and_oversize_rejected(self):
        for data in (zipped(receipt(),'../operational-receipt.json'), b'x'*262145, zipped({'x':'x'*65536})):
            with self.assertRaises(ValueError):receipt_from_zip(data,run_id=123,attempt=1,event='schedule')

    def test_expired_artifact_is_not_downloaded(self):
        original,binary=self.apis()
        def api(endpoint):
            value=original(endpoint)
            if '/artifacts?' in endpoint:value['artifacts'][0]['expired']=True
            return value
        self.assertEqual(inspect_run(123,api=api,binary=binary)['receipt_state'],'expired')
        binary.assert_not_called()

    def test_unrelated_workflow_and_truncated_inventory_rejected(self):
        original,binary=self.apis()
        def wrong(endpoint):
            value=original(endpoint);value['path']='.github/workflows/unrelated.yml';return value
        with self.assertRaises(ValueError):inspect_run(123,api=wrong,binary=binary)
        def truncated(endpoint):
            value=original(endpoint)
            if '/jobs?' in endpoint:value['total_count']=101
            return value
        with self.assertRaises(ValueError):inspect_run(123,api=truncated,binary=binary)
        binary.assert_not_called()

    def test_transport_failure_retains_outcome_without_claiming_receipt_absence(self):
        api,binary=self.apis();binary.side_effect=RuntimeError('SECRET signed URL')
        value=inspect_run(123,api=api,binary=binary)
        self.assertEqual(value['receipt_state'],'unavailable')
        self.assertEqual(value['conclusion'],'success');self.assertTrue(value['job_timing_available'])
        self.assertEqual(value['receipt_artifact']['id'],456)
        self.assertIsNone(value['receipt']);self.assertNotIn('SECRET',json.dumps(value))

    def test_connector_download_requires_matching_live_digest_and_strict_receipt(self):
        original,binary=self.apis();data=binary.return_value
        def api(endpoint):
            value=original(endpoint)
            if '/artifacts?' in endpoint:value['artifacts'][0]['digest']='sha256:'+hashlib.sha256(data).hexdigest()
            return value
        value=inspect_run(123,api=api,binary=binary,receipt_zip=data)
        self.assertEqual(value['receipt_state'],'verified');binary.assert_not_called()
        value=inspect_run(123,api=api,binary=binary,receipt_zip=data+b'tampered')
        self.assertEqual(value['receipt_state'],'invalid');self.assertIsNone(value['receipt'])
        with self.assertRaisesRegex(ValueError,'provider digest'):
            inspect_run(123,api=original,binary=binary,receipt_zip=data)

    def test_nonzip_response_and_private_receipt_remain_invalid_not_success(self):
        api,binary=self.apis()
        for data in (b'Forbidden',zipped({**receipt(),'private_annotations':['SECRET']})):
            binary.return_value=data
            value=inspect_run(123,api=api,binary=binary)
            self.assertEqual(value['receipt_state'],'invalid');self.assertIsNone(value['receipt'])
            self.assertFalse(value['operational_acceptance']);self.assertNotIn('SECRET',json.dumps(value))

    def test_cli_reports_failed_evidence_without_losing_run_status(self):
        import importlib.util
        import tempfile
        from pathlib import Path
        from contextlib import redirect_stdout
        from unittest.mock import patch
        spec=importlib.util.spec_from_file_location('inspection_cli',Path(__file__).resolve().parents[1]/'tools/inspect_operational_run.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        api,binary=self.apis();binary.side_effect=RuntimeError('Unavailable')
        value=inspect_run(123,api=api,binary=binary)
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'result.json'
            for state in ('unavailable','invalid'):
                value['receipt_state']=state
                with patch('sys.argv',['inspect','--run-id','123','--output',str(output)]), patch.object(module,'inspect_run',return_value=value), redirect_stdout(io.StringIO()):
                    self.assertEqual(module.main(),1)
                saved=json.loads(output.read_text())
                self.assertEqual(saved['conclusion'],'success');self.assertIsNone(saved['receipt'])
