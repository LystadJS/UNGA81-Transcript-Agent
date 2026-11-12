"""Read one canonical workflow attempt and its explicitly allowlisted artifact."""
import io
import hashlib
import re
import json
import subprocess
import zipfile
from .monitoring import validate_operational_receipt
from .observation import REPOSITORY, STATUSES, CONCLUSIONS, moment, iso


def api_bytes(endpoint, limit=8*1024*1024):
    result=subprocess.run(['gh','api',endpoint],capture_output=True,timeout=45)
    if result.returncode or len(result.stdout)>limit:
        raise RuntimeError('GitHub operational evidence unavailable or oversized')
    return result.stdout


def api_json(endpoint):
    return json.loads(api_bytes(endpoint))


def receipt_from_zip(data, *, run_id, attempt, event):
    if len(data)>262144:raise ValueError('Monitoring archive exceeds size bound')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members=archive.infolist()
        if len(members)!=1 or members[0].filename!='operational-receipt.json' or members[0].file_size>65536:
            raise ValueError('Unexpected monitoring archive members')
        with archive.open(members[0]) as stream:
            raw=stream.read(65537)
        if len(raw)>65536:raise ValueError('Monitoring receipt exceeds size bound')
        value=json.loads(raw)
    return validate_operational_receipt(value,run_id=run_id,attempt=attempt,event=event)


def inspect_run(run_id, attempt=None, *, api=api_json, binary=api_bytes, receipt_zip=None):
    if type(run_id) is not int or run_id<=0 or (attempt is not None and (type(attempt) is not int or attempt<=0)):
        raise ValueError('Invalid workflow attempt identity')
    prefix=f'repos/{REPOSITORY}/actions/runs/{run_id}'
    run=api(prefix)
    current=run['run_attempt']
    attempt=current if attempt is None else attempt
    if type(attempt) is not int or not 1<=attempt<=current:
        raise ValueError('Unavailable workflow attempt')
    if attempt!=current:run=api(prefix+f'/attempts/{attempt}')
    if run.get('id')!=run_id or run.get('run_attempt')!=attempt or run.get('path')!='.github/workflows/operational-pipeline.yml' or run.get('event') not in ('schedule','workflow_dispatch'):
        raise ValueError('Run is outside the canonical operational workflow')
    if run['status'] not in STATUSES or run.get('conclusion') not in CONCLUSIONS:
        raise ValueError('Unknown workflow outcome')
    result={'schema':'un.operational-run-inspection.v1','run_id':run_id,'attempt':attempt,
            'event':run['event'],'status':run['status'],'conclusion':run.get('conclusion'),
            'url':f'https://github.com/{REPOSITORY}/actions/runs/{run_id}',
            'created_at':iso(moment(run['created_at'])),
            'run_started_at':iso(moment(run['run_started_at'])) if run.get('run_started_at') else None,
            'last_job_completed_at':None,'job_timing_available':False,
            'receipt_state':'missing','receipt':None,'receipt_artifact':None,'operational_acceptance':False}
    jobs=api(prefix+f'/attempts/{attempt}/jobs?per_page=100')
    if not isinstance(jobs.get('jobs'),list) or jobs.get('total_count')!=len(jobs['jobs']) or len(jobs['jobs'])>100:
        raise ValueError('Incomplete job timing inventory')
    if jobs['jobs'] and all(j.get('status')=='completed' and j.get('completed_at') for j in jobs['jobs']):
        result['last_job_completed_at']=iso(max(moment(j['completed_at']) for j in jobs['jobs']))
        result['job_timing_available']=True
    artifacts=api(prefix+'/artifacts?per_page=100')
    if not isinstance(artifacts.get('artifacts'),list) or artifacts.get('total_count')!=len(artifacts['artifacts']) or len(artifacts['artifacts'])>100:
        raise ValueError('Incomplete artifact inventory')
    matches=[a for a in artifacts['artifacts'] if a.get('name')==f'operational-receipt-{attempt}']
    if len(matches)>1:raise ValueError('Ambiguous operational receipt artifacts')
    if matches:
        item=matches[0]
        if item.get('expired') is True:
            result['receipt_state']='expired'
        else:
            size=item.get('size_in_bytes')
            if type(size) is not int or not 0<=size<=262144:raise ValueError('Monitoring artifact exceeds size bound')
            identifier=item['id']
            if type(identifier) is not int or identifier<=0:raise ValueError('Invalid artifact identity')
            digest=item.get('digest')
            if digest is not None and (not isinstance(digest,str) or not re.fullmatch('sha256:[a-f0-9]{64}',digest)):
                raise ValueError('Invalid provider artifact digest')
            result['receipt_artifact']={'id':identifier,'bytes':size,'sha256':digest[7:] if digest else None}
            try:
                if receipt_zip is not None:
                    if digest is None:raise ValueError('Offline receipt requires a provider digest')
                    data=receipt_zip
                else:
                    data=binary(f'repos/{REPOSITORY}/actions/artifacts/{identifier}/zip',limit=262144)
            except (RuntimeError,OSError,subprocess.SubprocessError):
                result['receipt_state']='unavailable'
                return result
            try:
                if digest is not None and hashlib.sha256(data).hexdigest()!=digest[7:]:
                    raise ValueError('Artifact digest mismatch')
                validated=receipt_from_zip(data,run_id=run_id,attempt=attempt,event=run['event'])
            except (ValueError,zipfile.BadZipFile,KeyError,TypeError,RuntimeError,EOFError):
                result['receipt_state']='invalid'
                return result
            result['receipt']=validated
            result['receipt_state']='verified'
    return result
