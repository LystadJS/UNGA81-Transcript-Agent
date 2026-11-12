"""Source-free operational receipts, deliberately separate from private run files."""
from datetime import datetime, timezone
import re

COLLECTION_STATUSES = {'collected', 'deferred', 'excluded_language', 'excluded_reserved',
                       'unavailable', 'failed', 'pending', 'empty_transcript'}
OPERATIONS = {'repository_metadata', 'path_metadata', 'artifact_download', 'stage_snapshot', 'activate_pointer'}


def integer(value):
    if type(value) is not int or value < 0:
        raise ValueError('Invalid operational count')
    return value


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z', value):
        raise ValueError('Invalid operational timestamp')
    datetime.fromisoformat(value.replace('Z', '+00:00'))
    return value


def storage_measurement(value):
    """Repository retained bytes include history; they are not account quota."""
    if value is None:
        return None
    return {'retained_bytes': integer(value['retained_storage_bytes']),
            'budget_bytes': integer(value['storage_budget_bytes'])}


def operational_receipt(result, *, run_id, attempt, event, processing_status,
                        before=None, after_private=None, after_public=None, recorded_at=None):
    if not re.fullmatch(r'[1-9][0-9]*', str(run_id)) or not re.fullmatch(r'[1-9][0-9]*', str(attempt)):
        raise ValueError('Invalid workflow identity')
    if event not in ('schedule', 'workflow_dispatch'):
        raise ValueError('Unexpected workflow event')
    if processing_status not in ('success', 'failure', 'cancelled', 'skipped'):
        raise ValueError('Invalid processing status')
    receipt = {'schema': 'un.operational-receipt.v1', 'workflow_run_id': int(run_id),
               'workflow_attempt': int(attempt), 'event': event,
               'processing_status': processing_status,
               'recorded_at': timestamp(recorded_at or datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')),
               'completed_pipeline_receipt': result is not None, 'snapshot': None,
               'storage': {'scope': 'repository_retained_including_history', 'account_quota_verified': False,
                           'private_before': storage_measurement(before),
                           'private_after': storage_measurement(after_private),
                           'public_after': storage_measurement(after_public)},
               'contains_source_text': False, 'contains_annotations': False}
    if result is None:
        return receipt
    if result.get('schema') != 'un.pipeline-run.v1' or not re.fullmatch(r'\d{8}T\d{6}Z-[a-f0-9]{12}', result.get('run_id', '')):
        raise ValueError('Invalid pipeline receipt identity')
    if result.get('status') not in ('partial', 'complete'):
        raise ValueError('Invalid pipeline coverage status')
    if result.get('private_publication') != 'published' or result.get('public_publication') not in ('published', 'failed', 'not_configured'):
        raise ValueError('Invalid durable publication status')
    coverage = result['coverage']
    counts = {key: integer(coverage[key]) for key in ('meetings', 'stored_meetings', 'segments', 'inventory_dates')}
    statuses = coverage['statuses']
    if not isinstance(statuses, dict) or set(statuses) - COLLECTION_STATUSES:
        raise ValueError('Unknown collection status')
    statuses = {key: integer(value) for key, value in statuses.items()}
    if sum(statuses.values()) != counts['meetings'] or counts['stored_meetings'] > counts['meetings']:
        raise ValueError('Operational coverage counts do not reconcile')
    model_accepted = result['model_status']['accepted']
    if type(model_accepted) is not bool:
        raise ValueError('Invalid model acceptance indicator')
    snapshot = {'snapshot_id': result['run_id'], 'generated_at': timestamp(result['generated_at']),
                'coverage_status': result['status'], 'coverage': {**counts, 'statuses': statuses},
                'meetings_downloaded': integer(result['meetings_downloaded']),
                'bytes_downloaded': integer(result['bytes_downloaded']),
                'private_publication': result['private_publication'],
                'public_publication': result['public_publication'], 'model_accepted': model_accepted}
    if result.get('public_storage_operation') in OPERATIONS:
        snapshot['public_storage_operation'] = result['public_storage_operation']
    code = result.get('public_http_status')
    if type(code) is int and 400 <= code <= 599:
        snapshot['public_http_status'] = code
    receipt['snapshot'] = snapshot
    return receipt
