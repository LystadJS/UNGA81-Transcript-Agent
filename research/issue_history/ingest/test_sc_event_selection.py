"""Source-free action-selection checks; no actual voting records."""
import copy
import unittest
from .test_sc_crosswalk import fixture
from .sc_crosswalk import build_crosswalk
from .sc_event_selection import select_events


def run(c, rows):
    return select_events(c, rows, build_crosswalk(c, rows))


class SelectionTests(unittest.TestCase):
    def test_matched_count_once_deterministic_and_immutable(self):
        c,r=fixture();before=copy.deepcopy((c,r));a=run(c,r)
        self.assertEqual(a,run(c,r));self.assertEqual(before,(c,r))
        self.assertEqual(1,len(a['events']));e=a['events'][0]
        self.assertEqual('matched_adopted',e['status']);self.assertEqual('ddl',e['representative_source'])
        self.assertEqual(r,e['representative_ballots']);self.assertEqual(c['events'][0],e['alternatives'][0]['event'])
        self.assertFalse(e['comparisons_eligible']);self.assertFalse(a['summary']['political_scores_computed'])

    def test_unanimous_alternative_unknown_never_upgraded(self):
        c,r=fixture(True);a=run(c,r);alternative=a['events'][0]['alternatives'][0]['event']
        self.assertTrue(all(v['vote']=='unknown' and v['eligible'] is None for v in alternative['votes']))
        self.assertTrue(all(v['vote']=='yes' for v in a['events'][0]['representative_ballots']))

    def test_failed_drafts_retained_separately(self):
        c,r=fixture();e=copy.deepcopy(c['events'][0]);e.update(id='failed',resolution='',outcome='Not adopted - veto');c['events'].append(e)
        a=run(c,r);self.assertEqual(2,len(a['events']));f=next(x for x in a['events'] if x['status']=='failed_draft')
        self.assertEqual('dppa',f['representative_source']);self.assertEqual('Not adopted - veto',f['representative_event']['outcome'])

    def test_source_only_events_retained_with_coverage_gap(self):
        c,r=fixture();a=run({**c,'events':[]},r)
        self.assertEqual('ddl_only_adopted',a['events'][0]['status']);self.assertTrue(a['events'][0]['coverage_gap'])
        b=run(c,[]);self.assertEqual('dppa_only_adopted',b['events'][0]['status'])

    def test_unknown_ddl_vote_stays_unknown_not_absent(self):
        c,r=fixture();r[0].update(vote='unknown',eligible=None)
        a=run(c,r);self.assertEqual('unknown',a['events'][0]['representative_ballots'][0]['vote'])
        self.assertIsNone(a['events'][0]['representative_ballots'][0]['eligible'])

    def test_ballot_and_reference_conflicts_withhold_both_sources(self):
        for field,value in [('vote','no'),('draft','S/2024/123')]:
            c,r=fixture();r[0][field]=value;a=run(c,r)
            self.assertFalse(a['events']);self.assertTrue(a['withheld'])
            self.assertEqual(15,len(a['withheld'][0]['ddl_rows']))

    def test_different_date_same_resolution_and_malformed_withheld(self):
        c,r=fixture();c['events'][0]['date']='2024-01-02';a=run(c,r)
        self.assertFalse(a['events']);self.assertEqual('possible_same_action_date_conflict',a['withheld'][0]['reason'])
        c,r=fixture();c['events'][0]['resolution']='unreadable';a=run(c,[])
        self.assertFalse(a['events']);self.assertEqual(1,len(a['withheld']))

    def test_stale_or_modified_crosswalk_rejected(self):
        c,r=fixture();x=build_crosswalk(c,r);x['links'][0]['deduplication_eligible']=False
        with self.assertRaises(ValueError):select_events(c,r,x)
        x=build_crosswalk(c,r);r[0]['vote']='no'
        with self.assertRaises(ValueError):select_events(c,r,x)

    def test_provenance_only_change_invalidates_old_crosswalk(self):
        c,r=fixture();x=build_crosswalk(c,r);r[0]['source_revision']='d'*64
        with self.assertRaises(ValueError):select_events(c,r,x)
        c,r=fixture();x=build_crosswalk(c,r);c['events'][0]['last_update']='2026-10-24'
        with self.assertRaises(ValueError):select_events(c,r,x)

    def test_source_only_same_resolution_multiple_dates_withheld(self):
        c,r=fixture();other=copy.deepcopy(r)
        for row in other:
            row.update(id=row['id']+'-other',source_id=row['source_id']+'-other',date='2024-01-02')
        a=run({**c,'events':[]},r+other);self.assertFalse(a['events'])
        self.assertEqual('possible_same_action_date_conflict',a['withheld'][0]['reason'])
        e=copy.deepcopy(c['events'][0]);e.update(id='other',date='2024-01-02');c['events'].append(e)
        self.assertFalse(run(c,[])['events'])

    def test_failed_outcome_cannot_carry_adopted_reference(self):
        c,r=fixture();c['events'][0]['outcome']='Not adopted - veto'
        a=run(c,[]);self.assertFalse(a['events']);self.assertTrue(a['withheld'])

    def test_draft_meeting_and_source_url_contracts(self):
        for field,value in [('draft','not-a-symbol'),('meeting_record','not-a-reference'),('source_url','https://example.com/')]:
            c,r=fixture();c['events'][0][field]=value;self.assertFalse(run(c,[])['events'])
        for meeting in ['S/PV.','S/PV.9999 (Resumption 1)','S/2024/9999']:
            c,r=fixture();c['events'][0]['meeting_record']=meeting
            self.assertEqual(1,len(run(c,[])['events']))

    def test_duplicate_source_only_records_withheld(self):
        c,r=fixture();r.append(copy.deepcopy(r[0]));a=run({**c,'events':[]},r)
        self.assertFalse(a['events']);self.assertTrue(a['withheld'])
        c,r=fixture();c['events'].append(copy.deepcopy(c['events'][0]));a=run(c,[])
        self.assertFalse(a['events']);self.assertEqual(2,len(a['withheld']))

    def test_supported_nonparticipation_preserved_as_note(self):
        c,r=fixture();v=c['events'][0]['votes'].pop();r[-1].update(vote='unknown',eligible=None)
        c['events'][0]['nonparticipation']=[{'country':v['country'],'country_code':v['country_code'],
          'kind':'confirmed_nonparticipation','source_url':'https://press.un.org/en/2024/fixture.htm',
          'source_sha256':'f'*64,'hash_scope':'tool_extracted_primary_metadata','anchor':'Synthetic fixture',
          'review_state':'assistant_provisional'}]
        a=run(c,r);self.assertEqual(1,len(a['events']));e=a['events'][0]
        self.assertEqual(14,len(e['alternatives'][0]['event']['votes']));self.assertEqual(1,len(e['nonparticipation']))
        self.assertEqual('unknown',e['representative_ballots'][-1]['vote'])


if __name__=='__main__':unittest.main()
