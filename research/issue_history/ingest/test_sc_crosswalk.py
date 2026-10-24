"""Synthetic cross-source event identity; not political-agreement validation."""
import copy
import unittest
import json
import tempfile
from pathlib import Path
from ..store import IssueStore
from .sc_drafts import adapt
from . import test_sc_drafts as draft_fixture
from .sc_crosswalk import normalize_resolution, build_crosswalk, crosswalk_files


def fixture(unanimous=False):
    row=draft_fixture.DraftTests().row(outcome='Adopted unanimously' if unanimous else 'Adopted by majority')
    event=adapt(row,source_sha256='a'*64)
    collection={'schema':'un.sc-draft-collection.v1','dataset_id':'DPPA-SCVOTES','source_url':'https://psdata.un.org/dataset/DPPA-SCVOTES','source_sha256':'a'*64,'window':{'start':'2024-01-01','end':'2024-12-31'},'events':[event],'quarantined':[]}
    ddl=[{'id':'synthetic-'+v['country_code'],'source_id':'ddl-'+v['country_code'],'source_revision':'b'*64,'country':v['country'],'country_code':v['country_code'],'date':event['date'],'resolution':'S/RES/9999(2024)','stage':'adopted_resolution','modality':'Vote','vote':'yes','eligible':True} for v in event['votes']]
    return collection,ddl


class CrosswalkTests(unittest.TestCase):
    def test_literal_resolution_normalization_only(self):
        for value in ['9999 (2024)','S/RES/9999(2024)','S/RES/9999 (2024)']:
            self.assertEqual('S/RES/9999(2024)',normalize_resolution(value))
        for value in ['9999 (2024','S/2024/9999','9999','S/RES/9999(2025)/Rev.1',None]:
            self.assertIsNone(normalize_resolution(value))

    def test_recorded_parity_determinism_and_input_immutability(self):
        c,rows=fixture();before=copy.deepcopy((c,rows));r=build_crosswalk(c,rows)
        self.assertEqual(1,len(r['links']));link=r['links'][0]
        self.assertEqual('exact_resolution_date_one_to_one',link['identity_status'])
        self.assertEqual('exact_recorded_match',link['ballot_status']);self.assertEqual(15,link['known_agreements'])
        self.assertEqual(before,(c,rows));self.assertEqual(r,build_crosswalk(c,list(reversed(rows))))
        self.assertTrue(link['reference_gaps'],'missing draft and meeting cross-checks stay explicit')

    def test_unanimous_never_becomes_affirmative_agreement(self):
        c,rows=fixture(True);r=build_crosswalk(c,rows);link=r['links'][0]
        self.assertEqual('unknown_or_modality_gap',link['ballot_status'])
        self.assertEqual(0,link['known_agreements']);self.assertEqual(15,len(link['unknown_countries']))
        self.assertEqual('unknown',c['events'][0]['votes'][0]['vote'])

    def test_date_and_malformed_symbol_do_not_fuzzy_match(self):
        c,rows=fixture();c['events'][0]['date']='2024-01-02'
        r=build_crosswalk(c,rows);self.assertFalse(r['links']);self.assertTrue(r['unmatched_dppa']);self.assertTrue(r['unmatched_ddl'])
        c,rows=fixture();c['events'][0]['resolution']='9999 (2024'
        r=build_crosswalk(c,rows);self.assertFalse(r['links']);self.assertTrue(r['unmatched_dppa'])

    def test_ballot_and_roster_conflicts_are_visible(self):
        c,rows=fixture();rows[0]['vote']='no';r=build_crosswalk(c,rows)
        self.assertEqual('ballot_conflict',r['links'][0]['ballot_status']);self.assertTrue(r['links'][0]['conflicting_countries'])
        c,rows=fixture();rows.pop();r=build_crosswalk(c,rows)
        self.assertEqual('roster_conflict',r['links'][0]['ballot_status']);self.assertTrue(r['links'][0]['roster_gaps'])

    def test_multiple_drafts_for_one_adopted_event_remain_unresolved(self):
        c,rows=fixture();second=copy.deepcopy(c['events'][0]);second['id']='2';second['draft']='S/2024/9998';c['events'].append(second)
        r=build_crosswalk(c,rows);self.assertFalse(r['links']);self.assertTrue(r['conflicts'])

    def test_duplicate_members_cannot_silently_overwrite_votes(self):
        c,rows=fixture();rows.append(copy.deepcopy(rows[0]))
        try:
            r=build_crosswalk(c,rows)
        except ValueError:
            return
        self.assertTrue(r['conflicts'])
        self.assertFalse(any(link['ballot_status']=='exact_recorded_match' for link in r['links']))

    def test_wrong_source_stage_and_missing_revision_are_rejected(self):
        c,rows=fixture();c['events'][0]['source_family']='un_statement'
        self.assertFalse(build_crosswalk(c,rows)['links'])
        c,rows=fixture();c['events'][0]['stage']='procedural'
        self.assertFalse(build_crosswalk(c,rows)['links'])
        c,rows=fixture();del rows[0]['source_revision']
        try:
            r=build_crosswalk(c,rows)
        except ValueError:
            return
        self.assertFalse(any(link['deduplication_eligible'] for link in r['links']))

    def test_mismatched_resolution_year_does_not_link(self):
        c,rows=fixture();c['events'][0]['resolution']='9999 (2025)'
        for row in rows:row['resolution']='S/RES/9999(2025)'
        r=build_crosswalk(c,rows);self.assertFalse(r['links'])

    def test_nonparticipation_requires_full_provenance(self):
        c,rows=fixture();v=c['events'][0]['votes'].pop()
        c['events'][0]['nonparticipation']=[{'country_code':v['country_code'],'kind':'confirmed_nonparticipation','review_state':'assistant_provisional','source_sha256':'x'}]
        try:
            r=build_crosswalk(c,rows)
        except ValueError:
            return
        self.assertFalse(any(link['deduplication_eligible'] for link in r['links']))

    def test_confirmed_nonparticipation_conflicts_with_recorded_ballot(self):
        c,rows=fixture();v=c['events'][0]['votes'].pop()
        c['events'][0]['nonparticipation']=[{'country':v['country'],'country_code':v['country_code'],'kind':'confirmed_nonparticipation','review_state':'assistant_provisional','source_sha256':'c'*64,'source_url':'https://press.un.org/en/2024/synthetic.doc.htm','anchor':'Synthetic primary fixture only','hash_scope':'browser_rendered_primary_text'}]
        r=build_crosswalk(c,rows);self.assertEqual(1,len(r['links']))
        self.assertFalse(r['links'][0]['deduplication_eligible'])
        self.assertTrue(r['conflicts'] or r['links'][0]['conflicting_countries'])
        rows[-1].update(vote='unknown',eligible=None)
        r=build_crosswalk(c,rows);self.assertFalse(r['links'][0]['conflicting_countries'])
        self.assertFalse(r['links'][0]['ballot_agreement_verified'])

    def test_file_wrapper_cannot_overwrite_inputs(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            root=Path(directory);db=root/'history.sqlite';store=IssueStore(db);store.close()
            c,_=fixture();source=root/'collection.json';source.write_text(json.dumps(c),encoding='utf-8')
            before=(db.read_bytes(),source.read_bytes())
            for output in (db,source):
                with self.assertRaises(ValueError):crosswalk_files(source,db,output)
                self.assertEqual(before,(db.read_bytes(),source.read_bytes()))

    def test_failed_drafts_never_match_adopted_events(self):
        c,rows=fixture();c['events'][0]['outcome']='Not adopted - veto';c['events'][0]['resolution']=''
        r=build_crosswalk(c,rows);self.assertFalse(r['links']);self.assertTrue(r['unmatched_dppa'])

if __name__=='__main__':unittest.main()
