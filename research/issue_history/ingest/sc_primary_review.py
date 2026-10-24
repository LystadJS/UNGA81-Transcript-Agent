"""Source-linked private correction views; original ledgers are never modified."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse

VERSION='sc-primary-review-2'
SUPPORTED_VERSIONS=('sc-primary-review-1',VERSION)

def _official(url):
    try:
        u=urlparse(url)
        return u.scheme=='https' and (u.hostname=='un.org' or (u.hostname or '').endswith('.un.org')) and not u.username and not u.password
    except (ValueError,TypeError):return False

def _sha(value):return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value)

def _valid(field,value):
    if not isinstance(value,str):return False
    if field=='resolution':return bool(re.fullmatch(r'[1-9]\d* \(\d{4}\)',value))
    if field=='draft':return bool(re.fullmatch(r'S/(?:\d{4}/)?\d+(?:/Rev\.\d+)?',value))
    if field=='meeting_record':return bool(re.fullmatch(r'S/(?:PV\.\d+(?: \(Resumption \d+\))?|\d{4}/\d+)',value))
    if field=='date':
        try:return dt.date.fromisoformat(value).isoformat()==value
        except ValueError:return False
    return False

def load_review(path,provenance):
    path=Path(path).resolve();root=path.parent
    if path.stat().st_size>2_000_000:raise ValueError('Review envelope exceeds bound')
    payload=path.read_bytes();review=json.loads(payload)
    if review.get('schema')!='un.sc-primary-review.v1' or review.get('version') not in SUPPORTED_VERSIONS or not isinstance(review.get('corrections'),list) or len(review['corrections'])>100:raise ValueError('Invalid primary review envelope')
    pins=review.get('input_pins',{})
    for key in ('collection_sha256','ddl_database_sha256','ddl_original_source_sha256'):
        if not _sha(pins.get(key)) or pins[key]!=provenance.get(key):raise ValueError('Primary review input identity mismatch')
    hashes={str(path):hashlib.sha256(payload).hexdigest()}
    def identity_key(item):
        e=item.get('event',{})
        return (item.get('target'),e.get('resolution'),e.get('date'),e.get('dppa_event_id') if item.get('target')=='dppa' else '')
    reviewed_dates={identity_key(item):item.get('after') for item in review['corrections'] if item.get('field')=='date'}
    for correction in review['corrections']:
        source=correction.get('source',{});relative=source.get('evidence_file')
        if not isinstance(relative,str) or Path(relative).is_absolute():raise ValueError('Review evidence must be relative')
        evidence=(root/relative).resolve()
        if not evidence.is_relative_to(root) or evidence.stat().st_size>1_000_000:raise ValueError('Review evidence path or size exceeds bounds')
        raw=evidence.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        if not _sha(source.get('sha256')) or sha!=source['sha256']:raise ValueError('Primary evidence receipt changed')
        receipt=json.loads(raw)
        if receipt.get('schema')!='un.sc-primary-facts.v1' or source.get('hash_scope')!='tool_extracted_primary_metadata' or receipt.get('hash_scope')!=source['hash_scope'] or not _official(source.get('url')) or receipt.get('source_url')!=source['url'] or not isinstance(source.get('anchor'),str) or not source['anchor'].strip() or not isinstance(receipt.get('anchor'),str) or not receipt['anchor'].strip() or source['anchor']!=receipt['anchor']:raise ValueError('Incomplete official primary metadata receipt')
        facts=receipt.get('facts',{});event=correction.get('event',{});field=correction.get('field')
        from .sc_crosswalk import normalize_resolution
        if field=='resolution' and review['version']!=VERSION:raise ValueError('Malformed-symbol repairs require review version 2')
        supported_value=normalize_resolution(correction.get('after')) if field=='resolution' else correction.get('after')
        expected_date=correction.get('after') if field=='date' else reviewed_dates.get(identity_key(correction),event.get('date'))
        if not _valid('date',facts.get('date')) or facts['date']!=expected_date or facts.get('resolution')!=event.get('resolution') or facts.get(field)!=supported_value:raise ValueError('Correction is not supported by its dated primary facts')
        if field=='resolution' and (facts.get('draft')!=event.get('draft') or facts.get('meeting_record')!=event.get('meeting_record')):raise ValueError('Resolution repair lacks matching primary draft/meeting facts')
        hashes[str(evidence)]=sha
    return review,hashes

def _apply_review(collection,ddl_votes,review):
    """Apply an exact-before-value view to copies only; no persistence side effects."""
    from .sc_crosswalk import normalize_resolution
    if review.get('schema')!='un.sc-primary-review.v1' or review.get('version') not in SUPPORTED_VERSIONS:raise ValueError('Unsupported primary review')
    corrections=review.get('corrections')
    if not isinstance(corrections,list) or len(corrections)>100:raise ValueError('Invalid correction count')
    c=copy.deepcopy(collection);rows=copy.deepcopy(ddl_votes);operations=[];seen=set()
    for correction in corrections:
        identity=correction.get('event',{});field=correction.get('field');after=correction.get('after');target=correction.get('target');date=identity.get('date');resolution=identity.get('resolution')
        if correction.get('review_state')!='assistant_provisional' or target not in ('dppa','ddl') or not _valid(field,after) or not _valid('date',date) or normalize_resolution(resolution)!=resolution or correction.get('before')==after:raise ValueError('Invalid primary correction contract')
        if field=='date' and (after[:4]!=resolution[-5:-1] or not collection['window']['start']<=after<=collection['window']['end']):raise ValueError('Reviewed date is outside the source window/year')
        key=(target,resolution,date,identity.get('dppa_event_id') if target=='dppa' else '',field)
        if key in seen:raise ValueError('Duplicate primary correction target')
        seen.add(key)
        if field=='resolution':
            if review['version']!=VERSION:raise ValueError('Malformed-symbol repairs require review version 2')
            if target!='dppa' or normalize_resolution(correction.get('before')) is not None or normalize_resolution(after)!=resolution or after[-5:-1]!=date[:4] or not _valid('draft',identity.get('draft')) or not _valid('meeting_record',identity.get('meeting_record')):raise ValueError('Malformed-resolution review requires exact draft/meeting identity')
        if target=='dppa':
            matches=[i for i,e in enumerate(collection['events']) if e.get('id')==identity.get('dppa_event_id') and e.get('date')==date and ((e.get('resolution')==correction.get('before') and e.get('draft')==identity.get('draft') and e.get('meeting_record')==identity.get('meeting_record')) if field=='resolution' else normalize_resolution(e.get('resolution'))==resolution)]
            if len(matches)!=1:raise ValueError('Primary correction DPPA identity mismatch')
            targets=[c['events'][matches[0]]]
        else:
            indexes=[i for i,r in enumerate(ddl_votes) if r.get('date')==date and normalize_resolution(r.get('resolution'))==resolution and r.get('stage')=='adopted_resolution']
            if len(indexes)!=15:raise ValueError('Primary correction DDL event is not a complete original group')
            targets=[rows[i] for i in indexes]
        if any(t.get(field)!=correction.get('before') for t in targets):raise ValueError('Primary correction before-value mismatch')
        operations.append((targets,field,after,copy.deepcopy(correction)))
    for targets,field,after,correction in operations:
        for target in targets:
            original=target[field];target[field]=after
            target.setdefault('primary_review_notes',[]).append({'field':field,'original':original,'reviewed':after,'review_state':'assistant_provisional','source':correction.get('source',{}),'qualification':correction.get('qualification','')})
    return c,rows,{'version':VERSION,'applied_corrections':len(operations),'targets':dict((target,sum(x.get('target')==target for x in corrections)) for target in ('dppa','ddl')),'review_state':'assistant_provisional','original_records_modified':False}
