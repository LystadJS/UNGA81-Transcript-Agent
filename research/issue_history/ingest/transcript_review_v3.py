"""Versioned committee-role exclusions over immutable review validators."""
import hashlib
import json
from pathlib import Path
import re
from ..store.repository import canonical_bytes
from . import transcript_review_v2 as legacy
from .transcripts_un_batch import get_current_batch

VERSION='transcript-review-overlay-3'
COMMITTEE_ROLES={'vicechair','vicechairperson','rapporteur'}


def build_review_overlay(store,raw,receipt,frame_entry,reviews):
    """Role uncertainty blocks national proposals, not supported group mandates."""
    method_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result=legacy.build_review_overlay(store,raw,receipt,frame_entry,reviews)
    records={r['statement_number']:r for r in json.loads(raw)['transcript']['data']}
    for row in reviews:
        role=re.sub(r'[^a-z]','',(records[row['statement_number']]['speaker'].get('function') or '').casefold())
        if row['capacity']=='national_candidate' and role in COMMITTEE_ROLES:
            raise ValueError('Vice-chair or rapporteur role cannot establish national capacity')
    batch=get_current_batch(store,result['meeting_id'],receipt['source_url'])
    if not batch or hashlib.sha256(canonical_bytes(batch)).hexdigest()!=result['input_fingerprints']['batch_sha256']:
        raise ValueError('Current batch changed during committee-role validation')
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=method_sha: raise ValueError('Committee-role method changed during validation')
    result['version']=VERSION
    result['input_fingerprints']['method_sha256']['transcript_review_v3.py']=method_sha
    result['capacity_guard']+=' Normalized Vice-Chair, Vice-Chairperson and Rapporteur roles also exclude national-capacity proposals; non-national mandates remain source-reviewed.'
    result['owner_confirmed']=False
    return result
