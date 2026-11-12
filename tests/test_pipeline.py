"""Source-free full pipeline tests: collection to coherent research/public snapshots."""
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlsplit

from un_transcript.cli import run_pipeline
from un_transcript.snapshots import verify_snapshot
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


if __name__=='__main__':unittest.main()
