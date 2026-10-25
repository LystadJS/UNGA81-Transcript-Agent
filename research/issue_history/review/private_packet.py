"""Bounded private country-first proposals; saved choices never accept opinions."""
import hashlib
import json
from pathlib import Path
from ..store.repository import canonical_bytes
from ..ingest.transcript_context import build_context_overlay
from ..ingest import transcript_context
from ..ingest.transcripts_un_batch import get_current_batch
from ..ingest.historical_source_register import _publish

VERSION = 'private-country-review-1'
FRAME_SHA256 = '9a814f3f7986896f553072d5a610f6874b57a16adc4c15696da4998ce9b133e0'
BUNDLE_FIELDS = {'raw','receipt','frame_entry','reviews','context_reviews'}
PIN_FIELDS = {'raw_sha256','receipt_sha256','frame_entry_sha256','reviews_sha256','context_reviews_sha256'}


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _method():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def build_packet(store, bundles, frame, expected_inputs):
    """Recompute proposals against a pinned development frame and current batches.

    expected_inputs are separately retained acceptance pins, not permission grants.
    Only metadata from the full frame is used; reserved source bodies are forbidden.
    """
    method = _method(); context_methods=transcript_context._methods()
    if not isinstance(frame,dict) or frame.get('sha256') != FRAME_SHA256 or digest({k:v for k,v in frame.items() if k!='sha256'}) != FRAME_SHA256:
        raise ValueError('Authoritative complete development frame required')
    eligible = {}
    for row in frame.get('meetings',[]):
        if row.get('split')=='development' and row.get('has_transcript') is True and row.get('date') in ('2026-10-01','2026-10-02','2026-10-03','2026-10-04'):
            mid=row['meeting_id']
            if mid in eligible: raise ValueError('Duplicate frame identity')
            eligible[mid]={**row,'frame_sha256':FRAME_SHA256}
    if not isinstance(bundles,list) or not 0<len(bundles)<=8 or not isinstance(expected_inputs,dict):
        raise ValueError('Bounded permitted development inputs required')
    rows=[]; provenance={}; seen=set()
    for bundle in bundles:
        if not isinstance(bundle,dict) or set(bundle)!=BUNDLE_FIELDS: raise ValueError('Exact source bundle fields required')
        entry=bundle['frame_entry'];mid=entry.get('meeting_id') if isinstance(entry,dict) else None
        if mid not in eligible or mid in seen or entry!=eligible[mid]: raise ValueError('Source outside pinned permitted development membership')
        seen.add(mid)
        raw=bundle['raw']
        if not isinstance(raw,bytes): raise ValueError('Exact artifact bytes required')
        pins={'raw_sha256':hashlib.sha256(raw).hexdigest(),**{k+'_sha256':digest(bundle[k]) for k in ('receipt','frame_entry','reviews','context_reviews')}}
        if not isinstance(expected_inputs.get(mid),dict) or set(expected_inputs[mid])!=PIN_FIELDS or expected_inputs[mid]!=pins:
            raise ValueError('Accepted input pins changed')
        overlay=build_context_overlay(store,raw,bundle['receipt'],entry,bundle['reviews'],bundle['context_reviews'])
        provenance[mid]={'inputs':pins,'context_overlay_sha256':digest(overlay),'context_batch_sha256':overlay['input_fingerprints']['batch_sha256'],'context_method_sha256':overlay['input_fingerprints']['method_sha256']}
        originals={r['statement_number']:r for r in bundle['reviews']}
        contexts={r['candidate_id']:r for r in bundle['context_reviews']}
        # The inherited overlay recomputes candidate IDs and exact quote proofs.
        matches={}
        from ..ingest.transcript_review_v3 import build_review_overlay
        review=build_review_overlay(store,raw,bundle['receipt'],entry,bundle['reviews'])
        for r in review['reviews']:
            for match,original in zip(r['policy_matches'],originals[r['statement_number']]['policy_matches']): matches[match['candidate_id']]=original
        for candidate in overlay['contexts']:
            cid=candidate['candidate_id']; evidence=[]
            for kind,items in (('policy',matches[cid]['evidence']),('object',contexts[cid]['object_evidence']),('context',contexts[cid]['context_evidence'])):
                if len(items)>30: raise ValueError('Evidence count exceeds private packet bound')
                for item in items:
                    quote=item['quote']
                    if not isinstance(quote,str) or not 0<len(quote)<=1000: raise ValueError('Evidence quote exceeds private packet bound')
                    evidence.append({'kind':kind,'pointer':item['pointer'],'quote':quote,'quote_sha256':hashlib.sha256(quote.encode()).hexdigest()})
            rows.append({'id':digest([mid,cid]),'meeting_id':mid,'candidate_id':cid,'country':candidate['country_entity'],'group':candidate['group_entity'],'capacity':candidate['capacity_proposal'],'policy_id':candidate['policy_id'],
                         'assistant_proposal':{'stance':candidate['proposed_stance'],'discourse_labels':candidate['discourse_labels'],'context_state':candidate['state'],'context_relation':candidate['relation'],'context_reason':candidate['reason']},
                         'source':{'url':entry['source_url'],'sha256':overlay['source_sha256'],'modality':overlay['source_modality'],**{k:candidate[k] for k in ('statement_number','locator_id','text_sha256')}},
                         'evidence':evidence,'owner_decision':None})
    if set(expected_inputs)!=seen: raise ValueError('Input authority membership differs')
    rows.sort(key=lambda r:(r['country'] or '',r['meeting_id'],r['id']))
    if len(rows)>2000 or len({r['id'] for r in rows})!=len(rows): raise ValueError('Invalid bounded proposal membership')
    for bundle in bundles:
        mid=bundle['frame_entry']['meeting_id']
        batch=get_current_batch(store,mid,bundle['receipt']['source_url'])
        if batch is None or digest(batch)!=provenance[mid]['context_batch_sha256']:
            raise ValueError('Current batch changed during packet build')
    if _method()!=method or transcript_context._methods()!=context_methods: raise ValueError('Packet method changed during build')
    packet={'schema':'un.private-country-review.v1','version':VERSION,'rows':rows,
            'country_groups':[{'country':country,'row_ids':[r['id'] for r in rows if r['country']==country]} for country in sorted({r['country'] for r in rows if r['country'] is not None})],
            'non_national_row_ids':[r['id'] for r in rows if r['country'] is None],
            'input_fingerprints':{'frame_sha256':FRAME_SHA256,'expected_inputs_sha256':digest(expected_inputs),'meetings':provenance,'packet_method_sha256':method},
            'private_only':True,'owner_identity_verified':False,'accepted_positions':False,'comparisons_eligible':False,
            'limitations':['Assistant proposals are not owner labels or verified government positions.','Source excerpts are ASR, not official UN records.','Repeated evidence is not independent country opinion weight.','Saved choices are self-asserted review data and do not authenticate a reviewer or promote models.']}
    packet['packet_id']=digest(packet)
    return packet


def validate_packet_identity(packet):
    if not isinstance(packet,dict) or packet.get('schema')!='un.private-country-review.v1' or packet.get('version')!=VERSION or packet.get('packet_id')!=digest({k:v for k,v in packet.items() if k!='packet_id'}):
        raise ValueError('Packet identity mismatch')
    # This integrity check is not source authentication; build/load do that separately.
    if any(packet.get(k) is not False for k in ('owner_identity_verified','accepted_positions','comparisons_eligible')) or packet.get('private_only') is not True:
        raise ValueError('Review data cannot grant acceptance')


def build_decisions(packet, choices, filters, previous=None):
    """Separate append-only self-asserted review choices; no owner authentication."""
    validate_packet_identity(packet)
    ids={r['id'] for r in packet['rows']}
    if not isinstance(choices,list) or len(choices)!=len(ids): raise ValueError('One explicit nullable choice per proposal required')
    seen=set();clean=[]
    for choice in choices:
        if not isinstance(choice,dict) or set(choice)!={'row_id','label','note'} or choice['row_id'] not in ids or choice['row_id'] in seen or choice['label'] not in (None,'confirm','reject','unclear') or not isinstance(choice['note'],str) or len(choice['note'])>2000:
            raise ValueError('Invalid review choice')
        seen.add(choice['row_id']);clean.append(dict(choice))
    countries={'all','Collective / unknown capacity',*[r['country'] for r in packet['rows'] if r['country'] is not None]};policies={'all',*[r['policy_id'] for r in packet['rows']]}
    if not isinstance(filters,dict) or set(filters)!={'country','status','policy'} or filters['country'] not in countries or filters['policy'] not in policies or filters['status'] not in ('all','unreviewed','confirm','reject','unclear'):
        raise ValueError('Invalid saved filters')
    revision=1;parent=None
    if previous is not None:
        _validate_decisions(previous,packet)
        revision=previous['revision']+1;parent=previous['revision_sha256']
    value={'schema':'un.private-country-decisions.v1','packet_id':packet['packet_id'],'revision':revision,'parent_revision_sha256':parent,'choices':sorted(clean,key=lambda r:r['row_id']),'filters':dict(filters),'owner_identity_verified':False,'accepted_positions':False,'comparisons_eligible':False}
    value['revision_sha256']=digest(value)
    return value


def _validate_decisions(value,packet):
    fields={'schema','packet_id','revision','parent_revision_sha256','choices','filters','owner_identity_verified','accepted_positions','comparisons_eligible','revision_sha256'}
    if not isinstance(value,dict) or set(value)!=fields or value.get('schema')!='un.private-country-decisions.v1' or value.get('packet_id')!=packet['packet_id'] or type(value.get('revision')) is not int or value['revision']<1 or value.get('revision_sha256')!=digest({k:v for k,v in value.items() if k!='revision_sha256'}): raise ValueError('Decision revision identity mismatch')
    if any(value[k] is not False for k in ('owner_identity_verified','accepted_positions','comparisons_eligible')): raise ValueError('Decision cannot grant acceptance')
    parent=value['parent_revision_sha256']
    if (value['revision']==1 and parent is not None) or (value['revision']>1 and (not isinstance(parent,str) or len(parent)!=64 or any(c not in '0123456789abcdef' for c in parent))): raise ValueError('Invalid revision parent')
    # Validate all choices and filters through the initial-revision constructor.
    build_decisions(packet,value['choices'],value['filters'])


def _save(path,value):
    data=canonical_bytes(value);path=Path(path)
    if len(data)>32*1024*1024 or path.is_symlink(): raise ValueError('Bounded regular private snapshot required')
    if path.exists():
        if path.read_bytes()!=data: raise ValueError('Immutable snapshot already differs')
    else:
        try:_publish(path,data)
        except FileExistsError:
            if path.is_symlink() or path.read_bytes()!=data: raise ValueError('Concurrent snapshot differs')
    return str(path.resolve())


def _read(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>32*1024*1024: raise ValueError('Bounded regular private snapshot required')
    data=path.read_bytes()
    try:value=json.loads(data)
    except (ValueError,UnicodeError): raise ValueError('Malformed private snapshot')
    if data!=canonical_bytes(value): raise ValueError('Noncanonical private snapshot')
    return value


def save_packet(path,packet,**kwargs):
    if packet!=build_packet(**kwargs): raise ValueError('Packet differs from current authoritative inputs')
    return _save(path,packet)


def load_packet(path,**kwargs):
    packet=_read(path)
    if packet!=build_packet(**kwargs): raise ValueError('Saved packet differs from current authoritative inputs')
    return packet


def save_decisions(path,decisions,*,packet,previous=None):
    _validate_decisions(decisions,packet)
    if decisions!=build_decisions(packet,decisions['choices'],decisions['filters'],previous): raise ValueError('Decision history differs')
    return _save(path,decisions)


def load_decisions(path,*,packet,previous=None):
    value=_read(path)
    _validate_decisions(value,packet)
    if value!=build_decisions(packet,value['choices'],value['filters'],previous): raise ValueError('Decision history differs')
    return value
