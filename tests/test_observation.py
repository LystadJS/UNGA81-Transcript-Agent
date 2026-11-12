"""Synthetic workflow histories test missingness and timing, not service uptime."""
from datetime import date
import copy
import unittest
from un_transcript.observation import observe, public_freshness
from tools.observe_operational_runs import fetch_runs


def run(identifier=1, event='schedule', status='completed', conclusion='success',
        created='2026-11-12T11:19:00Z', started='2026-11-12T11:20:00Z', attempt=1):
    return {'id':identifier,'event':event,'status':status,'conclusion':conclusion,
            'created_at':created,'run_started_at':started,'run_attempt':attempt,
            'html_url':'https://untrusted.invalid/SECRET','actor':{'token':'SECRET'}}


def report(rows,now='2026-11-12T14:00:00Z',**kwargs):
    return observe(rows,'2026-11-12','2026-11-25',now,**kwargs)


class Observation(unittest.TestCase):
    def test_manual_retry_never_fills_missing_scheduled_date(self):
        result=report([run(event='workflow_dispatch')])
        self.assertEqual(result['days'][0]['state'],'missing')
        self.assertEqual(result['scheduled_dates_successful'],0)
        self.assertEqual(len(result['manual_runs']),1)
        self.assertFalse(result['operational_acceptance'])
        self.assertTrue(all(d['state']=='not_due' for d in result['days'][1:]))
        self.assertNotIn('SECRET',str(result))

    def test_scheduled_failure_remains_after_successful_manual_retry(self):
        result=report([run(conclusion='failure'),run(2,event='workflow_dispatch')])
        self.assertEqual(result['days'][0]['state'],'unsuccessful')
        self.assertEqual(result['latest_successful_workflow']['run_id'],2)

    def test_due_grace_and_future_are_distinct(self):
        self.assertEqual(report([],now='2026-11-12T11:16:00Z')['days'][0]['state'],'not_due')
        self.assertEqual(report([],now='2026-11-12T11:18:00Z')['days'][0]['state'],'awaiting_start')
        self.assertEqual(report([],inventory_complete=False)['days'][0]['state'],'inventory_incomplete')

    def test_delayed_queued_run_is_not_success(self):
        result=report([run(status='queued',conclusion=None,created='2026-11-12T11:40:00Z',started=None)])
        day=result['days'][0]
        self.assertEqual(day['state'],'running_or_queued')
        self.assertTrue(day['scheduled_runs'][0]['delayed_over_15_minutes'])
        self.assertIsNone(day['scheduled_runs'][0]['started_at'])

    def test_rerun_does_not_invent_earlier_attempt_history(self):
        day=report([run(attempt=2)])['days'][0]
        self.assertEqual(day['state'],'successful')
        self.assertTrue(day['scheduled_runs'][0]['earlier_attempts_not_inspected'])

    def test_duplicate_attempt_and_invalid_window_rejected(self):
        with self.assertRaises(ValueError):report([run(),run()])
        with self.assertRaises(ValueError):observe([],'2026-11-12','2026-12-25','2026-11-12T14:00:00Z')
        with self.assertRaises(ValueError):report([],now='2026-11-12T14:00:00')

    def test_complete_pagination_and_failure_at_bound(self):
        calls=[]
        def api(endpoint):
            calls.append(endpoint)
            return {'workflow_runs':[run(i) for i in range(1,101)] if len(calls)==1 else []}
        self.assertEqual(len(fetch_runs(date(2026,11,12),api)),100)
        self.assertEqual(len(calls),2)
        with self.assertRaisesRegex(RuntimeError,'completeness'):
            fetch_runs(date(2026,11,12),lambda _: {'workflow_runs':[run(i) for i in range(1,101)]})

    def test_public_freshness_does_not_infer_stance_or_current_position(self):
        manifest={'schema':'un.archive.v1','snapshot_id':'20261112T110000Z-abcdef123456',
                  'generated_at':'2026-11-12T11:00:00Z','status':'partial','model_status':'not_validated',
                  'coverage':{'meetings':8,'stored_meetings':3,'segments':30},'private':'SECRET'}
        result=public_freshness(manifest,'2026-11-15T11:00:00Z')
        self.assertTrue(result['older_than_48_hours'])
        self.assertFalse(result['model_accepted'])
        self.assertNotIn('SECRET',str(result))
        with self.assertRaises(ValueError):public_freshness(manifest,'2026-11-12T10:00:00Z')
