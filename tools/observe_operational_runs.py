"""Read-only, bounded GitHub/public-manifest monitor; no HF secret or sources."""
import argparse
from datetime import datetime, timezone, date
import json
from pathlib import Path
import subprocess
from urllib.request import urlopen

from un_transcript.observation import REPOSITORY, observe, public_freshness, moment

PUBLIC_URL = 'https://huggingface.co/datasets/LystadJS/UN-Transcript-Agent-Public/resolve/main/latest.json'


def api_json(endpoint):
    result=subprocess.run(['gh','api',endpoint],capture_output=True,timeout=45)
    if result.returncode or len(result.stdout)>8*1024*1024:
        raise RuntimeError('GitHub workflow inventory unavailable or oversized')
    return json.loads(result.stdout)


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
    report=observe(fetch_runs(args.start),args.start,args.end,now)
    try:
        with urlopen(PUBLIC_URL,timeout=30) as response:
            data=response.read(1024*1024+1)
        if len(data)>1024*1024:raise ValueError('Public manifest exceeds monitor bound')
        report['latest_public_snapshot']=public_freshness(json.loads(data),now)
        report['public_manifest_available']=True
    except Exception:
        # A failed freshness probe must not erase actual workflow evidence.
        report['latest_public_snapshot']=None
        report['public_manifest_available']=False
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'schema':report['schema'],'output':str(args.output),
                      'scheduled_dates_successful':report['scheduled_dates_successful'],
                      'public_manifest_available':report['public_manifest_available'],
                      'operational_acceptance':False}))


if __name__=='__main__':
    main()
