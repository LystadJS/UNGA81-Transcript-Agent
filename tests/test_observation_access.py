"""Monitoring failures preserve prior evidence and never echo provider secrets."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from tools.observe_operational_runs import ObservationAccessError, api_json, main


class ObservationAccess(unittest.TestCase):
    def test_http_status_is_numeric_without_provider_body(self):
        response=SimpleNamespace(returncode=1,stdout=b'{"token":"SECRET"}',
            stderr=b'gh: SECRET https://private.invalid/token (HTTP 403)')
        with patch('tools.observe_operational_runs.subprocess.run',return_value=response):
            with self.assertRaises(ObservationAccessError) as error:api_json('synthetic')
        self.assertEqual(error.exception.http_status,403)
        self.assertEqual(error.exception.reason,'request_failed')
        self.assertNotIn('SECRET',str(error.exception))

    def test_timeout_and_malformed_response_have_fixed_diagnostics(self):
        cases=[(subprocess.TimeoutExpired(['SECRET'],45,stderr=b'SECRET'),'timeout'),
               (FileNotFoundError('SECRET'),'client_unavailable')]
        for value,reason in cases:
            with self.subTest(reason=reason), patch('tools.observe_operational_runs.subprocess.run',side_effect=value):
                with self.assertRaises(ObservationAccessError) as error:api_json('synthetic')
                self.assertEqual(error.exception.reason,reason)
                self.assertIsNone(error.exception.http_status)
                self.assertNotIn('SECRET',str(error.exception))
        with patch('tools.observe_operational_runs.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout=b'SECRET',stderr=b'')):
            with self.assertRaises(ObservationAccessError) as error:api_json('synthetic')
            self.assertEqual(error.exception.reason,'invalid_json')

    def test_failed_inventory_preserves_existing_report_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'observation.json'; prior=b'previous report bytes\n';output.write_bytes(prior)
            stream=io.StringIO()
            with patch('sys.argv',['observe','--output',str(output)]), redirect_stdout(stream), \
                 patch('tools.observe_operational_runs.fetch_runs',side_effect=ObservationAccessError('request_failed',403)), \
                 patch('tools.observe_operational_runs.urlopen',side_effect=AssertionError('Do not probe unrelated data')):
                self.assertEqual(main(),1)
            self.assertEqual(output.read_bytes(),prior)
            receipt=json.loads(output.with_name(output.name+'.error.json').read_text())
            self.assertTrue(receipt['previous_report_preserved'])
            self.assertFalse(receipt['operational_acceptance'])
            self.assertEqual(receipt['http_status'],403)
            self.assertEqual(receipt['status'],'unavailable')
            self.assertEqual(json.loads(stream.getvalue()),receipt)

    def test_failed_first_observation_does_not_invent_previous_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'nested/first.json'
            with patch('sys.argv',['observe','--output',str(output)]), redirect_stdout(io.StringIO()), \
                 patch('tools.observe_operational_runs.fetch_runs',side_effect=ValueError('SECRET malformed payload')):
                self.assertEqual(main(),1)
            self.assertFalse(output.exists())
            raw=output.with_name(output.name+'.error.json').read_text()
            self.assertNotIn('SECRET',raw)
            self.assertFalse(json.loads(raw)['previous_report_preserved'])

    def test_public_failure_retains_workflow_evidence_and_sanitized_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'observation.json'
            error=HTTPError('https://private.invalid/SECRET',503,'SECRET',{},None)
            with patch('sys.argv',['observe','--output',str(output)]), redirect_stdout(io.StringIO()), \
                 patch('tools.observe_operational_runs.fetch_runs',return_value=[]), \
                 patch('tools.observe_operational_runs.urlopen',side_effect=error):
                self.assertEqual(main(),0)
            raw=output.read_text();self.assertNotIn('SECRET',raw)
            report=json.loads(raw)
            self.assertTrue(report['run_inventory_complete'])
            self.assertFalse(report['public_manifest_available'])
            self.assertEqual(report['public_manifest_error']['http_status'],503)
            self.assertEqual(len(report['days']),14)
