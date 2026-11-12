"""Provider diagnostics must not print signed URLs, tokens or private responses."""
import io
import json
import unittest
from contextlib import redirect_stderr
from types import SimpleNamespace
from unittest.mock import Mock, patch
from un_transcript.cli import main
from un_transcript.snapshots import _provider_call, StorageRequestError, HFStorage


class StorageDiagnostics(unittest.TestCase):
    def error(self, status):
        error = RuntimeError('PRIVATE body https://host/?token=SECRET')
        error.response = SimpleNamespace(status_code=status)
        return error

    def test_cli_only_emits_operation_and_numeric_status(self):
        with patch('un_transcript.cli.run_pipeline', side_effect=StorageRequestError('stage_snapshot', 429)):
            output = io.StringIO()
            with redirect_stderr(output):
                self.assertEqual(main(['run', '--workspace', '/tmp/synthetic-diagnostics']), 1)
        value = json.loads(output.getvalue())
        self.assertEqual(value['storage_operation'], 'stage_snapshot')
        self.assertEqual(value['http_status'], 429)
        self.assertNotIn('SECRET', output.getvalue())

    def test_provider_body_and_url_are_removed(self):
        for status in (403, 409, 429, 500, 503):
            with self.subTest(status=status):
                with self.assertRaises(StorageRequestError) as raised:
                    _provider_call('artifact_download', Mock(side_effect=self.error(status)))
                self.assertEqual(raised.exception.status_code, status)
                self.assertNotIn('PRIVATE', str(raised.exception))
                self.assertNotIn('SECRET', str(raised.exception))
                self.assertTrue(raised.exception.__suppress_context__)

    def test_non_http_validation_failures_keep_identity(self):
        error = ValueError('Invalid checksum')
        with self.assertRaises(ValueError) as raised:
            _provider_call('artifact_download', Mock(side_effect=error))
        self.assertIs(raised.exception, error)

    def test_commit_stage_and_activation_are_distinct(self):
        api = Mock()
        api.create_commit.side_effect = self.error(429)
        storage = HFStorage('owner/private', api=api)
        for files, operation in (({'snapshots/test/state.json': b'{}'}, 'stage_snapshot'),
                                 ({'latest.json': b'{}'}, 'activate_pointer')):
            with patch.dict('sys.modules', {'huggingface_hub': SimpleNamespace(CommitOperationAdd=Mock())}):
                with self.assertRaises(StorageRequestError) as raised:
                    storage._commit(files, 'a'*40, 'Synthetic')
            self.assertEqual(raised.exception.operation, operation)
