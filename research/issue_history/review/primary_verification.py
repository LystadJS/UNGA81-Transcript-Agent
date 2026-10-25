"""Pinned primary-source review overlay, separate from original ASR and owner choices."""
import copy
import hashlib
from pathlib import Path
from urllib.parse import urlsplit
from . import corrections as C
from . import private_packet as P

VERSION = 'private-primary-verification-1'
SCHEMA = 'un.private-primary-verification.v1'
FIELDS = {'row_id','original_row_sha256','source_sha256','status','context_summary','note','unresolved_reasons','proofs'}
PROOF_FIELDS = {'role','url','title','displayed_date','locator','summary','exact_short_quote','capture_sha256','capture_hash_scope','audio_verified'}
ROLES = {'official_government_written_statement','un_recording_metadata','un_primary_record_metadata','verification_attempt'}
GOVERNMENT_HOSTS = frozenset({'www.un.emb-japan.go.jp','un.emb-japan.go.jp','finlandabroad.fi','www.finlandabroad.fi','www.mzv.sk','mzv.sk'})


def _method():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _text(value, maximum, empty=False):
    if not isinstance(value,str) or len(value)>maximum or (not empty and not value.strip()):
        raise ValueError('Bounded primary review text required')


def _proof(proof):
    if not isinstance(proof,dict) or set(proof)!=PROOF_FIELDS or proof['role'] not in ROLES:
        raise ValueError('Exact separated primary proof required')
    for key in ('title','locator','summary','capture_hash_scope'):_text(proof[key],4000)
    _text(proof['exact_short_quote'],200,True)
    _text(proof['displayed_date'],100,True)
    url=urlsplit(proof['url'])
    if url.scheme!='https' or not url.hostname or url.username or url.password or url.fragment or url.port not in (None,443):
        raise ValueError('Primary proof requires strict HTTPS URL')
    # These are endpoint families, not claims of authenticity or permission.
    host=url.hostname.lower()
    if proof['role'].startswith('un_') and not (host=='un.org' or host.endswith('.un.org')):
        raise ValueError('UN proof requires UN host')
    if proof['role']=='official_government_written_statement' and host not in GOVERNMENT_HOSTS:
        raise ValueError('Government proof requires an explicitly supported official endpoint')
    if not isinstance(proof['capture_sha256'],str) or len(proof['capture_sha256'])!=64 or any(c not in '0123456789abcdef' for c in proof['capture_sha256']):
        raise ValueError('Explicit capture digest required')
    if proof['capture_hash_scope'] not in ('review_receipt_not_primary_bytes','captured_rendered_text_not_raw_html'):
        raise ValueError('Capture scope must not imply original primary bytes')
    if proof['audio_verified'] is not False:
        raise ValueError('This overlay cannot authenticate audio')


def build_packet(*,correction_inputs,reviews,expected_reviews_sha256,expected_row_ids):
    method=_method();original=C.build_packet(**correction_inputs)
    C.validate_packet_identity(original)
    if not isinstance(reviews,list) or P.digest(reviews)!=expected_reviews_sha256:
        raise ValueError('Externally pinned primary reviews required')
    if not isinstance(expected_row_ids,list) or len(set(expected_row_ids))!=len(expected_row_ids) or len(reviews)!=len(expected_row_ids) or {r.get('row_id') for r in reviews}!=set(expected_row_ids):
        raise ValueError('Exact pinned review membership required')
    packet=copy.deepcopy(original);packet.pop('packet_id');rows={r['id']:r for r in packet['rows']};seen=set()
    for review in reviews:
        if not isinstance(review,dict) or set(review)!=FIELDS or review['row_id'] not in rows or review['row_id'] in seen:
            raise ValueError('Exact unique primary review required')
        seen.add(review['row_id']);row=rows[review['row_id']]
        if row.get('correction',{}).get('status')!='unresolved' or P.digest(row)!=review['original_row_sha256'] or row['source']['sha256']!=review['source_sha256']:
            raise ValueError('Review must bind an unchanged unresolved corrected row')
        if review['status'] not in ('written_statement_supported','unresolved'):raise ValueError('Unknown primary review status')
        _text(review['context_summary'],2000);_text(review['note'],4000)
        reasons=review['unresolved_reasons']
        if not isinstance(reasons,list) or len(reasons)>10 or (review['status']=='unresolved')!=bool(reasons):raise ValueError('Explicit unresolved reasons required')
        for reason in reasons:_text(reason,1000)
        proofs=review['proofs']
        if not isinstance(proofs,list) or not 1<=len(proofs)<=12:raise ValueError('Bounded primary proofs required')
        for proof in proofs:_proof(proof)
        if review['status']=='written_statement_supported' and not any(p['role']=='official_government_written_statement' and p['exact_short_quote'] and p['displayed_date'] for p in proofs):
            raise ValueError('Resolution requires dated government written statement proof')
        row['pre_primary_verification_proposal']=copy.deepcopy(row)
        row['primary_verification']={k:copy.deepcopy(review[k]) for k in ('status','context_summary','note','unresolved_reasons','proofs')}
        row['primary_verification'].update(review_state='assistant_provisional',audio_verified=False,owner_confirmed=False)
        if review['status']=='written_statement_supported':
            row['correction']['status']='corrected';row['correction']['unresolved_reasons']=[]
            row['assistant_proposal'].update(context_state='anchored',context_relation='full_statement_review',context_reason=None)
            row['correction']['interpretation']['context_summary']=review['context_summary']
        else:row['correction']['unresolved_reasons']=copy.deepcopy(reasons)
        row['correction']['note']=review['note']
    # A remaining warning is scoped to its unresolved origin, not erased by a resolved sibling.
    warnings=[]
    for warning in original.get('source_warnings',[]):
        origins=[rid for rid in warning['origin_row_ids'] if rows[rid]['correction']['status']=='unresolved']
        if origins:
            updated=copy.deepcopy(warning);updated['origin_row_ids']=origins
            updated['unresolved_reasons']=sorted({reason for rid in origins for reason in rows[rid]['correction']['unresolved_reasons']})
            warnings.append(updated)
    packet.update(schema=SCHEMA,version=VERSION,source_warnings=warnings)
    packet['input_fingerprints'].update(corrected_packet_id=original['packet_id'],primary_reviews_sha256=expected_reviews_sha256,primary_row_ids_sha256=P.digest(expected_row_ids),primary_method_sha256=method)
    packet['limitations'].append('Primary written-statement review is assistant-provisional, separate from unchanged ASR and unauthenticated recording audio. Capture receipt hashes do not authenticate primary bytes.')
    if C.build_packet(**correction_inputs)!=original or _method()!=method:raise ValueError('Primary review dependencies changed during build')
    packet['packet_id']=P.digest(packet);return packet


def validate_packet_identity(packet):
    if not isinstance(packet,dict) or packet.get('schema')!=SCHEMA or packet.get('version')!=VERSION or packet.get('packet_id')!=P.digest({k:v for k,v in packet.items() if k!='packet_id'}):raise ValueError('Primary packet identity mismatch')
    proxy=copy.deepcopy(packet);proxy.update(schema='un.private-country-corrections.v1',version=C.VERSION);proxy.pop('packet_id');proxy['packet_id']=P.digest(proxy);C.validate_packet_identity(proxy)


def correction_proxy(packet):
    validate_packet_identity(packet);proxy=copy.deepcopy(packet)
    proxy.update(schema='un.private-country-corrections.v1',version=C.VERSION);proxy.pop('packet_id');proxy['packet_id']=P.digest(proxy)
    return proxy


def build_decisions(packet,choices,filters,previous=None):
    if any(c.get('label') is not None or c.get('note')!='' for c in choices):raise ValueError('Primary verification must leave owner choices blank')
    result=C.build_decisions(correction_proxy(packet),choices,filters)
    result.update(schema='un.private-primary-verification-decisions.v1',packet_id=packet['packet_id'],primary_reviews_sha256=packet['input_fingerprints']['primary_reviews_sha256'])
    if previous is not None:
        _validate_decisions(previous,packet);result.update(revision=previous['revision']+1,parent_revision_sha256=previous['revision_sha256'])
    result.pop('revision_sha256');result['revision_sha256']=P.digest(result);return result


def _validate_decisions(value,packet):
    validate_packet_identity(packet)
    if not isinstance(value,dict) or value.get('schema')!='un.private-primary-verification-decisions.v1' or value.get('packet_id')!=packet['packet_id'] or value.get('primary_reviews_sha256')!=packet['input_fingerprints']['primary_reviews_sha256'] or value.get('revision_sha256')!=P.digest({k:v for k,v in value.items() if k!='revision_sha256'}):raise ValueError('Primary decisions identity mismatch')
    converted=copy.deepcopy(value);converted.pop('primary_reviews_sha256');converted.update(schema='un.private-country-decisions-corrections.v1',packet_id=correction_proxy(packet)['packet_id']);converted.pop('revision_sha256');converted['revision_sha256']=P.digest(converted)
    C._validate_decisions(converted,correction_proxy(packet))
    if any(c.get('label') is not None or c.get('note')!='' for c in value['choices']):raise ValueError('Owner choices must remain blank')


def save_packet(path,packet,**kwargs):
    if packet!=build_packet(**kwargs):raise ValueError('Primary packet differs from authoritative inputs')
    return P._save(path,packet)


def load_packet(path,**kwargs):
    value=P._read(path)
    if value!=build_packet(**kwargs):raise ValueError('Saved primary review differs from authoritative inputs')
    return value


def save_decisions(path,decisions,*,packet,previous=None):
    _validate_decisions(decisions,packet)
    if decisions!=build_decisions(packet,decisions['choices'],decisions['filters'],previous):raise ValueError('Primary decision history differs')
    return P._save(path,decisions)


def load_decisions(path,*,packet,previous=None):
    value=P._read(path);_validate_decisions(value,packet)
    if value!=build_decisions(packet,value['choices'],value['filters'],previous):raise ValueError('Primary decision history differs')
    return value
