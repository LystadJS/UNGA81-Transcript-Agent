"""Scheduled-run evidence; manual success never fills a missing scheduled day."""
from datetime import date, datetime, time, timedelta, timezone
import re

REPOSITORY = 'LystadJS/UNGA81-Transcript-Agent'
STATUSES = {'queued', 'in_progress', 'completed', 'waiting', 'requested', 'pending'}
CONCLUSIONS = {'success', 'failure', 'cancelled', 'timed_out', 'skipped', 'action_required',
               'neutral', 'stale', 'startup_failure', None}


def moment(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00')) if isinstance(value,str) else value
    if not isinstance(parsed,datetime) or parsed.tzinfo is None:
        raise ValueError('Observation timestamps must include a timezone')
    return parsed.astimezone(timezone.utc)


def iso(value):
    return value.isoformat().replace('+00:00','Z')


def observe(runs, start, end, as_of, *, inventory_complete=True):
    start = date.fromisoformat(start) if isinstance(start,str) else start
    end = date.fromisoformat(end) if isinstance(end,str) else end
    now = moment(as_of)
    if not 0 <= (end-start).days < 31:
        raise ValueError('Observation window must contain 1–31 dates')
    records=[]; seen=set()
    for row in runs:
        event=row.get('event')
        if event not in ('schedule','workflow_dispatch'):
            continue
        created=moment(row['created_at'])
        if not start <= created.date() <= end or created > now:
            continue
        run_id=row['id']; attempt=row.get('run_attempt',1)
        if type(run_id) is not int or run_id <= 0 or type(attempt) is not int or attempt <= 0:
            raise ValueError('Invalid observed run identity')
        if (run_id,attempt) in seen:
            raise ValueError('Duplicate observed run attempt')
        seen.add((run_id,attempt))
        status=row['status']; conclusion=row.get('conclusion')
        if status not in STATUSES or conclusion not in CONCLUSIONS:
            raise ValueError('Unknown observed workflow status')
        started=moment(row['run_started_at']) if row.get('run_started_at') else None
        records.append({'run_id':run_id,'attempt':attempt,'event':event,'created_at':iso(created),
                        'started_at':iso(started) if started else None,'status':status,'conclusion':conclusion,
                        'url':f'https://github.com/{REPOSITORY}/actions/runs/{run_id}',
                        'earlier_attempts_not_inspected':attempt>1})
    records.sort(key=lambda r:(r['created_at'],r['run_id'],r['attempt']))
    days=[]
    for offset in range((end-start).days+1):
        day=start+timedelta(days=offset)
        expected=datetime.combine(day,time(11,17),timezone.utc)
        scheduled=[r for r in records if r['event']=='schedule' and moment(r['created_at']).date()==day]
        if expected > now:
            state='not_due'
        elif not scheduled:
            state='inventory_incomplete' if not inventory_complete else ('awaiting_start' if now<expected+timedelta(hours=2) else 'missing')
        elif any(r['status']!='completed' for r in scheduled):
            state='running_or_queued'
        elif all(r['conclusion']=='success' for r in scheduled):
            state='successful'
        else:
            state='unsuccessful'
        for r in scheduled:
            r['created_delay_seconds']=max(0,int((moment(r['created_at'])-expected).total_seconds()))
            r['start_delay_seconds']=max(0,int((moment(r['started_at'])-expected).total_seconds())) if r['started_at'] else None
            r['delayed_over_15_minutes']=(r['start_delay_seconds'] if r['start_delay_seconds'] is not None else r['created_delay_seconds'])>900
        days.append({'date':day.isoformat(),'expected_at':iso(expected),'state':state,'scheduled_runs':scheduled})
    manual=[r for r in records if r['event']=='workflow_dispatch']
    successful=sorted((r for r in records if r['status']=='completed' and r['conclusion']=='success'),
                      key=lambda r:(r['started_at'] or r['created_at'],r['run_id'],r['attempt']))
    return {'schema':'un.scheduled-observation.v1','repository':REPOSITORY,'observed_at':iso(now),
            'window':{'start':start.isoformat(),'end':end.isoformat(),'expected_dates':len(days)},
            'run_inventory_complete':inventory_complete,'days':days,'manual_runs':manual,
            'scheduled_dates_successful':sum(d['state']=='successful' for d in days),
            'latest_successful_workflow':successful[-1] if successful else None,
            'operational_acceptance':False,
            'limitations':['Scheduled dates are associated by GitHub run creation date in UTC; GitHub does not expose an original scheduled-for timestamp.',
                           'Missing means no scheduled run was returned after a two-hour reporting grace period; delays over fifteen minutes are flagged separately.',
                           'Earlier attempts of rerun IDs are flagged but not inferred from the latest run record.',
                           'Workflow success alone does not establish snapshot freshness, source completeness, model accuracy or operational acceptance.']}


def public_freshness(manifest, as_of):
    if manifest.get('schema')!='un.archive.v1' or not re.fullmatch(r'\d{8}T\d{6}Z-[a-f0-9]{12}',manifest.get('snapshot_id','')):
        raise ValueError('Invalid public snapshot identity')
    generated=moment(manifest['generated_at']);age=(moment(as_of)-generated).total_seconds()
    if age < -300:
        raise ValueError('Public snapshot publication time is in the future')
    coverage=manifest['coverage']
    counts={k:coverage[k] for k in ('meetings','stored_meetings','segments')}
    if any(type(v) is not int or v<0 for v in counts.values()) or counts['stored_meetings']>counts['meetings']:
        raise ValueError('Invalid public coverage counts')
    if manifest.get('status') not in ('partial','complete'):
        raise ValueError('Invalid public coverage status')
    return {'snapshot_id':manifest['snapshot_id'],'generated_at':iso(generated),
            'age_seconds':max(0,int(age)),'older_than_48_hours':age>48*3600,
            'coverage_status':manifest['status'],'coverage':counts,
            'model_accepted':manifest.get('model_status') in ('accepted','evaluated_accepted')}
