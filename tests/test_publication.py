import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock
from un_transcript.exports import export_snapshot
from un_transcript.publication import provision_public, validate_target, load_publication_config, CARD
from un_transcript.snapshots import RemoteEntryMissing, prepare_public_bundle
from un_transcript.warehouse import Warehouse


class HttpError(Exception):
    def __init__(self, code):
        self.response = SimpleNamespace(status_code=code)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        with Warehouse(self.root/'live/warehouse.sqlite3') as db:
            export_snapshot(db, self.root/'snapshot', 'synthetic', '2026-11-12T00:00:00Z')
        self.directory = self.root/'snapshot/public'
        self.api = Mock()
        self.info = SimpleNamespace(private=False, sha='a'*40)
        self.api.repo_info.return_value = self.info
        self.api.list_repo_files.return_value = ['.gitattributes']
        self.public = Mock()
        self.public.info.return_value = (self.info, 0)
        self.public.read.side_effect = RemoteEntryMissing()
        self.public.publish_public.return_value = prepare_public_bundle(self.directory)[2]
        self.factory = Mock(return_value=self.public)

    def tearDown(self):
        self.temp.cleanup()

    def run_provision(self):
        return provision_public('owner/UN-Transcript-Agent-Private', 'owner/UN-Transcript-Agent-Public',
                                self.directory, api=self.api, storage_factory=self.factory)

    def test_creates_only_missing_dedicated_public_repo(self):
        self.api.repo_info.side_effect = HttpError(404)
        result = self.run_provision()
        self.api.create_repo.assert_called_once_with(repo_id='owner/UN-Transcript-Agent-Public',
            repo_type='dataset', private=False, exist_ok=False)
        self.assertTrue(result['created'])
        self.assertFalse(result['source_text_published'])
        self.public.publish_public.assert_called_once_with(self.directory)

    def test_permissions_block_without_any_write(self):
        self.api.repo_info.side_effect = HttpError(403)
        with self.assertRaises(HttpError):
            self.run_provision()
        self.api.create_repo.assert_not_called()
        self.api.upload_file.assert_not_called()
        self.public.publish_public.assert_not_called()

    def test_never_changes_existing_private_visibility(self):
        self.api.repo_info.return_value = SimpleNamespace(private=True)
        with self.assertRaisesRegex(ValueError, 'visibility'):
            self.run_provision()
        self.api.create_repo.assert_not_called()
        self.factory.assert_not_called()

    def test_rejects_unrecognized_existing_repo(self):
        self.api.list_repo_files.return_value = ['README.md']
        self.public.read.side_effect = None
        self.public.read.return_value = b'Unrelated project'
        with self.assertRaisesRegex(ValueError, 'unexpected project marker'):
            self.run_provision()
        self.public.publish_public.assert_not_called()
        self.api.upload_file.assert_not_called()

    def test_private_field_rejected_before_repo_creation(self):
        path = self.directory/'manifest.json'
        data = json.loads(path.read_bytes()); data['private_annotation'] = 'synthetic secret'
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.run_provision()
        self.api.repo_info.assert_not_called()

    def test_repeat_verifies_existing_bytes_without_new_commit(self):
        self.api.list_repo_files.return_value = ['README.md', 'latest.json']
        expected = prepare_public_bundle(self.directory)[2]
        self.public.read.side_effect = lambda path, *_: CARD if path == 'README.md' else json.dumps(expected).encode()
        self.run_provision()
        self.public._verify_remote.assert_called_once()
        self.public.publish_public.assert_not_called()
        self.api.upload_file.assert_not_called()

    def test_target_must_be_dedicated_same_owner_public_repo(self):
        for target in ('other/UN-Transcript-Agent-Public', 'owner/UN-Transcript-Agent-Private', 'owner/unrelated'):
            with self.assertRaises(ValueError):
                validate_target('owner/UN-Transcript-Agent-Private', target)

    def test_versioned_configuration_matches_public_browser_and_private_owner(self):
        config = load_publication_config('config/publication.json', 'LystadJS/UN-Transcript-Agent-Private')
        browser = json.loads(Path('site/archive-config.json').read_bytes())
        self.assertEqual(config['manifest_url'], browser['manifest_url'])
        with self.assertRaises(ValueError):
            load_publication_config('config/publication.json', 'other/UN-Transcript-Agent-Private')
        with self.assertRaises(ValueError):
            load_publication_config('config/publication.json', 'LystadJS/UN-Transcript-Agent-Private', 'other/public')

    def test_configuration_rejects_credential_bearing_or_mismatched_url(self):
        path = self.root/'publication.json'
        path.write_text(json.dumps({'schema':'un.publication.v1', 'public_repo':'owner/UN-Transcript-Agent-Public',
                                    'manifest_url':'https://user:secret@huggingface.co/datasets/other/latest.json'}))
        with self.assertRaises(ValueError):
            load_publication_config(path, 'owner/UN-Transcript-Agent-Private')
