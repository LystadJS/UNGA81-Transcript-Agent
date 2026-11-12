"""Read-only, bounded GitHub/public-manifest monitor; no HF secret or sources."""
import argparse
from datetime import datetime, timezone, date
import json
from pathlib import Path
import re
import subprocess
from urllib.error import HTTPError
from urllib.request import urlopen

from un_transcript.observation import REPOSITORY, observe, public_freshness, moment
from un_transcript.snapshots import atomic_json

PUBLIC_URL = 'https://huggingface.co/datasets/LystadJS/UN-Transcript-Agent-Public/resolve/main/latest.json'


class ObservationAccessError(RuntimeError):
    def __init__(self, reason, http_status=None):
        self.reason = reason
        self.http_status = http_status
        super().__init__('GitHub workflow inventory unavailable')


def api_json(endpoint):
    try:
        result=subprocess.run(['gh','api',endpoint],capture_output=True,timeout=45)
    except subprocess.TimeoutExpired:
        raise ObservationAccessError('timeout') from None
    except OSError:
        raise ObservationAccessError('client_unavailable') from None
    if result.returncode:
        match=re.search(rb'\(HTTP ([1-5][0-9]{2})\)', result.stderr[:16384])
        raise ObservationAccessError('request_failed', int(match[1]) if match else None)
    if len(result.stdout)>8*1024*1024:
        raise ObservationAccessError('response_oversized')
    try:
        return json.loads(result.stdout)
    except (ValueError, UnicodeError):
        raise ObservationAccessError('invalid_json') from None


def fetch_runs(start, api=api_json):
    rows=[]
    for page in range(1,21):
        value=api(f'repos/{REPOSITORY}/actions/workflows/operational-pipeline.yml/runs?branch=main&per_page=100&page={page}')
        batch=value.get('workflow_runs')
        if not isinstance(batch,list):
            raise ValueError('Invalid workflow inventory response')
        rows.extend(batch)
        if len(batch)<100 or (batch and min(moment(r['created_at']).date() for r in batch)<start):
            # API pagination is newest-first. Preserve duplicates as an error,
            # rather than silently losing a run during concurrent pagination.
            return rows
    raise RuntimeError('Workflow inventory pagination bound reached; completeness is unknown')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start',type=date.fromisoformat,default=date(2026,11,12))
    parser.add_argument('--end',type=date.fromisoformat,default=date(2026,11,25))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    now=datetime.now(timezone.utc)
    try:
        report=observe(fetch_runs(args.start),args.start,args.end,now)
    except Exception as error:
        # Never overwrite the prior successful observation or echo provider
        # messages, credentials, URLs or response contents into the failure.
        failure={'schema':'un.scheduled-observation-error.v1','status':'unavailable',
                 'observed_at':now.isoformat().replace('+00:00','Z'),
                 'window':{'start':args.start.isoformat(),'end':args.end.isoformat()},
                 'operation':'github_workflow_inventory','error_type':type(error).__name__,
                 'reason':error.reason if isinstance(error,ObservationAccessError) else 'invalid_or_incomplete_inventory',
                 'http_status':error.http_status if isinstance(error,ObservationAccessError) else None,
                 'previous_report_preserved':args.output.is_file(),'operational_acceptance':False}
        sidecar=args.output.with_name(args.output.name+'.error.json')
        atomic_json(sidecar, failure)
        print(json.dumps(failure))
        return 1
    try:
        with urlopen(PUBLIC_URL,timeout=30) as response:
            data=response.read(1024*1024+1)
        if len(data)>1024*1024:raise ValueError('Public manifest exceeds monitor bound')
        report['latest_public_snapshot']=public_freshness(json.loads(data),now)
        report['public_manifest_available']=True
    except Exception as error:
        # A failed freshness probe must not erase actual workflow evidence.
        report['latest_public_snapshot']=None
        report['public_manifest_available']=False
        report['public_manifest_error']={'operation':'public_manifest','error_type':type(error).__name__,
                                         'http_status':error.code if isinstance(error,HTTPError) else None}
    atomic_json(args.output, report)
    print(json.dumps({'schema':report['schema'],'output':str(args.output),
                      'scheduled_dates_successful':report['scheduled_dates_successful'],
                      'public_manifest_available':report['public_manifest_available'],
                      'operational_acceptance':False}))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
