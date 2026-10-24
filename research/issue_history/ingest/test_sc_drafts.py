"""Invented DPPA-shaped fixtures; no empirical country-position benchmark."""
import csv
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from .sc_drafts import adapt,validate_headers,HEADERS,registry
from .adapters import SourceError
from ..store import IssueStore
from ..refresh.sc_drafts_cli import ingest,collect,load_overlays

NAMES='Algeria,China,Ecuador,France,Guyana,Japan,Malta,Mozambique,Republic of Korea,Sierra Leone,Russian Federation,Slovenia,Switzerland,United Kingdom,United States'


class DraftTests(unittest.TestCase):
    def row(self,**changes):
        row=dict.fromkeys(HEADERS,'')
        row.update(id='1',year='2024',date='2024-01-01',resolution='9999 (2024)',meeting_record='S/PV.9999',draft='S/2024/9999',outcome='Adopted unanimously',yes=NAMES,last_update='2026-10-23')
        return {**row,**changes}

    def test_unanimous_is_not_individual_yes(self):
        event=adapt(self.row(),source_sha256='a'*64)
        self.assertEqual('unanimous_ballot_unverified',event['modality'])
        self.assertTrue(all(v['vote']=='unknown' and v['eligible']is None and v['recorded_choice']=='yes' for v in event['votes']))
        self.assertEqual('United States',next(v for v in event['votes'] if v['country_code']=='USA')['country'])

    def test_recorded_choices_and_official_outcome(self):
        names=NAMES.split(',')
        row=self.row(outcome='Not adopted - veto',resolution='',yes=','.join(n for n in names if n not in ('Russian Federation','China')),no='Russian Federation',abstain='China')
        event=adapt(row,source_sha256='a'*64)
        self.assertEqual('no',next(v for v in event['votes'] if v['country_code']=='RUS')['vote'])
        insufficient=adapt({**row,'outcome':'Not adopted - failed to receive required number of votes'},source_sha256='a'*64)
        self.assertEqual('Not adopted - failed to receive required number of votes',insufficient['outcome'])
        self.assertNotIn('veto',insufficient)
        with self.assertRaises(SourceError):adapt({**row,'outcome':'Failed maybe'},source_sha256='a'*64)

    def test_exact_aliases_unknowns_and_duplicates(self):
        codes,aliases,_=registry()
        for name,code in [('Cape Verde','CPV'),('Turkey','TUR'),('Côte d’Ivoire','CIV')]:self.assertEqual({code},aliases[name])
        event=adapt(self.row(outcome='Adopted by majority',yes=NAMES.replace('Algeria','Atlantis')),source_sha256='a'*64)
        unknown=next(v for v in event['votes'] if v['recorded_country']=='Atlantis')
        self.assertIsNone(unknown['country_code']);self.assertEqual('unknown',unknown['vote']);self.assertIsNone(unknown['eligible'])
        with self.assertRaises(SourceError):adapt(self.row(yes=NAMES.replace('Algeria','China')),source_sha256='a'*64)
        with self.assertRaisesRegex(SourceError,'Incomplete source roster'):adapt(self.row(yes=','.join(NAMES.split(',')[:-1])),source_sha256='a'*64)

    def test_literal_references_and_headers(self):
        event=adapt(self.row(draft='\u00a0S/2024/9999\u00a0',resolution='9999 (2024',meeting_record='S/PV.'),source_sha256='a'*64)
        self.assertEqual('S/2024/9999',event['draft']);self.assertEqual('\u00a0S/2024/9999\u00a0',event['recorded_draft'])
        self.assertFalse(event['reference_valid']);self.assertEqual('unavailable',event['meeting_reference_kind'])
        written=adapt(self.row(meeting_record='S/2020/999'),source_sha256='a'*64)
        self.assertEqual('written_procedure_document',written['meeting_reference_kind'])
        with self.assertRaises(SourceError):validate_headers(HEADERS[:-1])

    def test_source_bound_nonparticipation_is_not_a_ballot(self):
        row=self.row(yes=','.join(NAMES.split(',')[1:]))
        overlay={'event':{'id':'1','date':row['date'],'draft':row['draft'],'meeting_record':row['meeting_record'],'outcome':row['outcome'],'source_sha256':'a'*64},'recorded_counts':{'yes':14,'no':0,'abstain':0},'note':{'country':'Algeria','country_code':'DZA','kind':'confirmed_nonparticipation','source_url':'https://press.un.org/en/2024/synthetic.doc.htm','source_sha256':'b'*64,'review_state':'assistant_provisional','anchor':'Invented fixture paragraph','hash_scope':'browser_rendered_primary_text'}}
        event=adapt(row,source_sha256='a'*64,overlays=[overlay])
        self.assertEqual(14,len(event['votes']));self.assertEqual(1,len(event['nonparticipation']));self.assertNotIn('eligible',event['nonparticipation'][0])
        self.assertTrue(all(v['country_code']!='DZA' for v in event['votes']))
        with self.assertRaisesRegex(SourceError,'identity mismatch'):adapt(row,source_sha256='a'*64,overlays=[{**overlay,'recorded_counts':{'yes':13,'no':0,'abstain':1}}])
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            base=Path(directory);primary=base/'primary.txt';primary.write_text('Invented primary fixture, not a real document. '*5,encoding='utf-8')
            overlay['note']['source_sha256']=hashlib.sha256(primary.read_bytes()).hexdigest();overlay['source_evidence_file']=primary.name
            metadata=base/'overlay.json';metadata.write_text(json.dumps({'schema':'un.sc-draft-nonparticipation.v1','overlays':[overlay]}),encoding='utf-8')
            self.assertEqual(1,len(load_overlays(metadata)))
            primary.write_text('tampered',encoding='utf-8')
            with self.assertRaises(SourceError):load_overlays(metadata)
            extract=base/'extract.json'
            receipt={'schema':'un.primary-metadata-extract.v1','source_url':overlay['note']['source_url'],'hash_scope':'tool_extracted_primary_metadata','source_pages':[1,2],'event':{'resolution':row['resolution'],'meeting_record':row['meeting_record'],'date':row['date'],'yes':14,'no':0,'abstain':0},'primary_footnote':'Invented fixture: Algeria did not participate in the voting.','review_state':'assistant_provisional'}
            extract.write_text(json.dumps(receipt),encoding='utf-8');overlay['source_evidence_file']=extract.name;overlay['recorded_adopted_resolution']=row['resolution'];overlay['note'].update(hash_scope='tool_extracted_primary_metadata',source_pages=[1,2],source_sha256=hashlib.sha256(extract.read_bytes()).hexdigest())
            metadata.write_text(json.dumps({'schema':'un.sc-draft-nonparticipation.v1','overlays':[overlay]}),encoding='utf-8')
            self.assertEqual(1,len(load_overlays(metadata)))
            overlay['note']['source_pages']=[99];metadata.write_text(json.dumps({'schema':'un.sc-draft-nonparticipation.v1','overlays':[overlay]}),encoding='utf-8')
            with self.assertRaisesRegex(SourceError,'resolution/page mismatch'):load_overlays(metadata)

    @patch('research.issue_history.refresh.sc_drafts_cli.shutil.disk_usage',return_value=SimpleNamespace(free=10_000_000_000))
    def test_isolated_private_import_and_resume(self,_disk):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            base=Path(directory);source=base/'source.csv'
            rows=[self.row(),self.row(id='2',draft='S/2024/9998'),self.row(id='3',draft='S/2024/9997',yes=','.join(NAMES.split(',')[:-1]))]
            with source.open('w',encoding='utf-8',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=HEADERS);writer.writeheader();writer.writerows(rows)
            sha=hashlib.sha256(source.read_bytes()).hexdigest()
            options=dict(source_file=source,expected_sha256=sha,database=base/'isolated.sqlite',checkpoint=base/'cursor.json',collection_file=base/'collection.json',receipt_file=base/'receipt.json',start='2024-01-01',end='2024-12-31')
            result=ingest(**options);self.assertTrue(result['complete']);self.assertEqual(2,result['accepted_events']);self.assertEqual(30,result['accepted_ballots']);self.assertEqual(1,len(result['quarantined']))
            self.assertEqual(result,ingest(**options))
            store=IssueStore(options['database'])
            try:
                self.assertEqual(30,store.db.execute('SELECT count(*) FROM evidence').fetchone()[0])
                self.assertTrue(all(json.loads(r[0])['policy']=='unbound' for r in store.db.execute('SELECT payload FROM evidence')))
                self.assertEqual(0,store.export_bundle(base/'public','test')['counts']['votes'])
            finally:store.close()
            with self.assertRaisesRegex(ValueError,'identity changed'):ingest(**{**options,'end':'2024-11-30'})
            with patch('research.issue_history.refresh.sc_drafts_cli.shutil.disk_usage',return_value=SimpleNamespace(free=200_000_000)):
                blocked=ingest(**{**options,'database':base/'blocked.sqlite','checkpoint':base/'blocked-cursor.json'})
                self.assertTrue(blocked['storage_reserve_reached']);self.assertEqual(0,blocked['accepted_ballots'])


if __name__=='__main__':unittest.main()
