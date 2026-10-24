"""Versioned chair-role guard over the unchanged provisional review validator."""
import hashlib
import json
from pathlib import Path
import re
from . import transcript_review as legacy
from .transcripts_un_batch import get_current_batch

VERSION='transcript-review-overlay-2'
CHAIR_ROLES={'chair','cochair','chairperson','cochairperson'}


def build_review_overlay(store,raw,receipt,frame_entry,reviews):
    """Validate source linkage first; role exclusion is not semantic acceptance."""
    result=legacy.build_review_overlay(store,raw,receipt,frame_entry,reviews)
    source=json.loads(raw)
    records={r['statement_number']:r for r in source['transcript']['data']}
    for row in reviews:
        function=records[row['statement_number']]['speaker'].get('function') or ''
        role=re.sub(r'[^a-z]','',function.casefold())
        if row['capacity']=='national_candidate' and role in CHAIR_ROLES:
            raise ValueError('Chair or co-chair function cannot supply national capacity')
    batch=get_current_batch(store,result['meeting_id'],receipt['source_url'])
    if not batch or legacy._digest(batch)!=result['input_fingerprints']['batch_sha256']:
        raise ValueError('Current batch changed during chair-role validation')
    result['version']=VERSION
    result['input_fingerprints']['method_sha256']['transcript_review_v2.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['capacity_guard']='Existing PGA/vice-president guard plus normalized Chair, Co-Chair, Chairperson and Co-Chairperson exclusions; no national-capacity inference.'
    result['owner_confirmed']=False
    return result
