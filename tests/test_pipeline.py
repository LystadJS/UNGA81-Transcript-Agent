"""Source-free full pipeline tests: collection to coherent research/public snapshots."""
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlsplit

from un_transcript.cli import run_pipeline, main
from unittest.mock import Mock, patch
from contextlib import redirect_stdout
import io
from un_transcript.snapshots import verify_snapshot, StorageRequestError
from un_transcript.warehouse import Warehouse


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.config=json.loads(Path('config/collection.json').read_text())
        self.config.update(start_date='2026-11-10',end_date='2026-11-10',selection_mode='meetings',
                           meetings=[{'meeting_id':'ga/81/42','date':'2026-11-10'}])
        self.config_path=self.root/'config.json';self.config_path.write_text(json.dumps(self.config))
        self.text='We support unhindered humanitarian access.'

    def tearDown(self):self.tmp.cleanup()

    def transport(self,url):
        if urlsplit(url).path=='/en/meetings.json':
            data={'page':1,'total':1,'hasMore':False,'meetings':[{'slug':'ga/81/42','date':'2026-11-10',
                  'title':'Synthetic proceedings','hasTranscript':True,'pageUrl':'/en/ga/81/42',
                  'jsonUrl':'/en/ga/81/42.json'}]}
        else:
            data={'video':{'slug':'ga/81/42','date':'2026-11-10'},'transcript':{'language':'en','data':[
                {'speaker':{'affiliation':'KEN'},'paragraphs':[{'sentences':[{'text':self.text}]}]}]}}
        return {'raw':json.dumps(data).encode(),'retrieved_at':'2026-11-11T00:00:00Z','headers':{}}

    def run_pipeline(self):
        return run_pipeline(self.config_path,self.root/'runtime',as_of=date(2026,11,10),transport=self.transport)

    def test_repeat_and_revision_keep_raw_history_and_consistent_exports(self):
        first=self.run_pipeline();verify_snapshot(first['snapshot'])
        second=self.run_pipeline();verify_snapshot(second['snapshot'])
        with Warehouse(self.root/'runtime/data/warehouse.sqlite3') as db:
            self.assertEqual(db.db.execute('SELECT COUNT(*) FROM source_revisions').fetchone()[0],1)
            self.assertEqual(db.db.execute('SELECT COUNT(*) FROM inventory_receipts').fetchone()[0],2)
            self.assertEqual(db.db.execute('SELECT COUNT(*) FROM predictions').fetchone()[0],0)
            self.assertGreater(db.db.execute('SELECT COUNT(*) FROM issue_candidates').fetchone()[0],0)
        self.text='We oppose restrictions on humanitarian access.'
        third=self.run_pipeline();verify_snapshot(third['snapshot'])
        with Warehouse(self.root/'runtime/data/warehouse.sqlite3') as db:
            self.assertEqual(db.db.execute('SELECT COUNT(*) FROM source_revisions').fetchone()[0],2)
            self.assertEqual(db.current_segments()[0]['text'],self.text)
        for result in (first,second,third):
            self.assertEqual(result['coverage']['stored_meetings'],1)
            self.assertEqual(result['coverage']['meetings'],1)
            self.assertEqual(result['coverage']['inventory_dates'],1)
            self.assertEqual(result['coverage']['inventory_statuses'],{'inventory_complete':1})
            self.assertEqual(result['coverage']['segments'],1)
            public_manifest=json.loads((Path(result['snapshot'])/'public/manifest.json').read_bytes())
            self.assertEqual(result['coverage'],public_manifest['coverage'])
            public=Path(result['snapshot'])/'public'
            for path in public.rglob('*'):
                if path.is_file():self.assertNotIn(b'We support unhindered',path.read_bytes())

    def test_inventory_outage_retains_prior_sources_and_reports_partial(self):
        first=self.run_pipeline()
        def broken(url):raise TimeoutError('synthetic outage')
        failed=run_pipeline(self.config_path,self.root/'runtime',as_of=date(2026,11,10),transport=broken)
        self.assertEqual(failed['status'],'partial')
        self.assertEqual(failed['coverage']['stored_meetings'],1)
        self.assertEqual(failed['meetings_downloaded'],0)
        self.assertEqual(failed['coverage']['inventory_statuses'],{'inventory_failed':1})
        self.assertNotIn('inventory_failed',failed['coverage']['statuses'])
        with Warehouse(self.root/'runtime/data/warehouse.sqlite3') as db:
            self.assertEqual(len(db.current_segments()),1)
        verify_snapshot(failed['snapshot']);verify_snapshot(first['snapshot'])

    def test_incomplete_capacity_stops_before_restore_or_source_downloads(self):
        from un_transcript.capacity import CapacityIncomplete
        private=Mock(repo_id='owner/private',budget_bytes=80_000_000_000)
        private.budget_info.side_effect=CapacityIncomplete('metadata unavailable')
        transport=Mock()
        with self.assertRaises(CapacityIncomplete):
            run_pipeline(self.config_path,self.root/'runtime',as_of=date(2026,11,10),
                         transport=transport,remote=private)
        transport.assert_not_called()
        private.restore.assert_not_called()
        private.publish.assert_not_called()
        self.assertFalse((self.root/'runtime/data').exists())

    def test_public_outage_preserves_private_publication_and_failure_receipt(self):
        private = Mock(repo_id='owner/private', budget_bytes=80_000_000_000)
        private.info.return_value = (None, 0)
        private.budget_info.return_value = (None, 0)
        private.publish.side_effect = lambda directory: {'snapshot_id': directory.name}
        public = Mock(repo_id='owner/public')
        public.publish_public.side_effect = PermissionError('secret signed URL must not reach receipt')
        result = run_pipeline(self.config_path, self.root/'runtime', as_of=date(2026,11,10),
                              transport=self.transport, remote=private, public_remote=public)
        private.publish.assert_called_once()
        public.info.assert_not_called()
        self.assertEqual(result['private_publication'], 'published')
        self.assertEqual(result['public_publication'], 'failed')
        self.assertEqual(result['public_error_type'], 'PermissionError')
        receipt = json.loads((self.root/'runtime/last-run.json').read_bytes())
        self.assertEqual(receipt, result)
        self.assertNotIn('secret signed URL', json.dumps(receipt))
        self.assertEqual(json.loads((self.root/'runtime/latest.json').read_bytes())['snapshot_id'], result['run_id'])
        verify_snapshot(result['snapshot'])

    def test_public_provider_failure_retains_sanitized_diagnostics(self):
        private = Mock(repo_id='owner/private', budget_bytes=80_000_000_000)
        private.info.return_value = (None, 0)
        private.budget_info.return_value = (None, 0)
        private.publish.side_effect = lambda directory: {'snapshot_id': directory.name}
        public = Mock(repo_id='owner/public')
        error = StorageRequestError('activate_pointer', 429)
        error.response = {'body':'PRIVATE', 'url':'https://host/?token=SECRET'}
        public.publish_public.side_effect = error
        result = run_pipeline(self.config_path, self.root/'runtime', as_of=date(2026,11,10),
                              transport=self.transport, remote=private, public_remote=public)
        self.assertEqual(result['private_publication'], 'published')
        self.assertEqual(result['public_publication'], 'failed')
        self.assertEqual(result['public_storage_operation'], 'activate_pointer')
        self.assertEqual(result['public_http_status'], 429)
        self.assertNotIn('PRIVATE', json.dumps(result))
        self.assertNotIn('SECRET', json.dumps(result))
        self.assertEqual(json.loads((self.root/'runtime/last-run.json').read_bytes()), result)

    def test_private_failure_does_not_attempt_public_publication(self):
        private = Mock(repo_id='owner/private', budget_bytes=80_000_000_000)
        private.info.return_value = (None, 0)
        private.budget_info.return_value = (None, 0)
        private.publish.side_effect = TimeoutError('synthetic private outage')
        public = Mock(repo_id='owner/public')
        with self.assertRaises(TimeoutError):
            run_pipeline(self.config_path, self.root/'runtime', as_of=date(2026,11,10),
                         transport=self.transport, remote=private, public_remote=public)
        public.publish_public.assert_not_called()
        self.assertFalse((self.root/'runtime/latest.json').exists())

    def test_cli_reports_nonzero_when_only_public_publication_failed(self):
        with patch('un_transcript.cli.run_pipeline', return_value={'public_publication':'failed'}), redirect_stdout(io.StringIO()):
            self.assertEqual(main(['run', '--workspace', str(self.root/'cli')]), 1)


if __name__=='__main__':unittest.main()
