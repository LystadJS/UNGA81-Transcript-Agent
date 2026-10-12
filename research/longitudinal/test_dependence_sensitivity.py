"""Synthetic source/year-dependence controls; no UN speech sources."""
import unittest
from fixtures import make_panel
from framework import ContractError
from dependence_sensitivity import audit_meeting_year_dependence


def multi_year(*, motion=False, missing=False):
    p=make_panel(roster=False,motion=motion,fit_policy='transformed_reference',
        unavailable_family=('p1',3) if missing else None)
    p['periods']=[
        {'id':'p0','start':'2016-01-01','end':'2019-12-31'},
        {'id':'p1','start':'2020-01-01','end':'2023-12-31'}]
    for r in p['observations']:
        family=int(r['source_family_id'].split('-')[-1])
        year=(2016 if r['period']=='p0' else 2020)+(family%4)
        r['date']=f'{year}-09-20'
        if missing and r['source_status']!='available':
            r.update(source_status='unverified',date=None,meeting_id=None,
                source_family_id=None,source_sha256=None,text_sha256=None,
                representation_id=None,representation_version=None,
                representation_fingerprint=None)
    return p


class DependenceTests(unittest.TestCase):
    def test_no_movement_no_fake_interval(self):
        q=audit_meeting_year_dependence(multi_year(), 'p0','p1')
        self.assertEqual(q['population']['matched_original_actors'],9)
        self.assertEqual(q['population']['meeting_groups'],16)
        self.assertEqual(q['population']['year_blocks'],8)
        self.assertEqual(q['population']['years_per_period'],{'p0':4,'p1':4})
        self.assertEqual(q['meeting_delete_one']['successful'],16)
        self.assertEqual(q['year_delete_one']['successful'],8)
        self.assertEqual(q['one_year_per_period_delete']['successful'],16)
        self.assertAlmostEqual(q['baseline']['mean_within_actor_distance'],0)
        self.assertIsNone(q['inference']['bootstrap_interval'])
        self.assertIsNone(q['inference']['year_cluster_se'])
        self.assertFalse(q['publication_eligible'])

    def test_known_motion_detected_only_in_high_dimensional_features(self):
        q=audit_meeting_year_dependence(multi_year(motion=True), 'p0','p1')
        self.assertGreater(q['baseline']['mean_within_actor_distance'],0)
        self.assertEqual(q['one_year_per_period_delete']['attempted'],16)
        self.assertEqual(q['one_year_per_period_delete']['successful'],16)
        self.assertEqual(q['population']['actor_meeting_connected_components'],1)

    def test_true_missingness_never_converted_to_zero_vectors(self):
        q=audit_meeting_year_dependence(multi_year(missing=True), 'p0','p1')
        self.assertEqual(q['population']['source_status_by_period']['p1']['unverified'],9)
        self.assertEqual(q['population']['meeting_groups'],15)
        self.assertEqual(q['meeting_delete_one']['successful'],15)
        self.assertFalse(q['inference']['deletion_ranges_are_confidence_intervals'])

    def test_different_year_same_meeting_detected(self):
        p=multi_year()
        r=next(x for x in p['observations'] if x['period']=='p0' and
               x['meeting_id']=='fictional-meeting-p0-0')
        r['date']='2018-09-20'
        with self.assertRaisesRegex(ContractError,'Meeting has conflicting'):
            audit_meeting_year_dependence(p,'p0','p1')

    def test_refitted_display_basis_is_not_pinned_reference(self):
        p=make_panel(roster=False,fit_policy='full_refit')
        with self.assertRaisesRegex(ContractError,'Only saved reference'):
            audit_meeting_year_dependence(p,'p0','p1')

    def test_single_year_two_period_panel_withholds_pair_deletions(self):
        p=make_panel(roster=False,fit_policy='transformed_reference')
        q=audit_meeting_year_dependence(p,'p0','p1')
        self.assertEqual(q['one_year_per_period_delete']['attempted'],0)
        self.assertIsNone(q['one_year_per_period_delete']['mean_within_actor_distance']['range_min'])
        self.assertIsNone(q['inference']['p_value'])


if __name__=='__main__':
    unittest.main(verbosity=2)
