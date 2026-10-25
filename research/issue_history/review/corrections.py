"""Source-bound assistant corrections; never owner acceptance or policy resolution."""
import copy
import hashlib
import json
from pathlib import Path
import re
from . import private_packet as P

VERSION = 'private-country-corrections-1'
FIELDS = {'row_id','original_row_sha256','source_sha256','status','replacement','evidence','note','unresolved_reasons','interpretation'}
PROPOSAL_FIELDS = {'stance','discourse_labels','context_state','context_relation','context_reason'}
INTERPRETATION_FIELDS = {'temporal_scope','claim_qualification','attribution_note','context_summary','policy_object_note'}


def _text(value, limit, empty=True):
    if not isinstance(value,str) or len(value)>limit or (not empty and not value.strip()):
        raise ValueError('Bounded correction text required')


def _method():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def build_packet(store,bundles,frame,expected_inputs,corrections,expected_corrections_sha256,expected_flagged_row_ids):
    method=_method()
    original=P.build_packet(store,bundles,frame,expected_inputs)
    if not isinstance(corrections,list) or len(corrections)>len(original['rows']) or P.digest(corrections)!=expected_corrections_sha256:
        raise ValueError('Pinned bounded correction reviews required')
    if not isinstance(expected_flagged_row_ids,list) or len(set(expected_flagged_row_ids))!=len(expected_flagged_row_ids) or {x.get('row_id') for x in corrections}!=set(expected_flagged_row_ids):
        raise ValueError('Corrections must match externally pinned flagged membership')
    sources={b['frame_entry']['meeting_id']:json.loads(b['raw']) for b in bundles}
    rows={r['id']:copy.deepcopy(r) for r in original['rows']};seen=set()
    for item in corrections:
        if not isinstance(item,dict) or set(item)!=FIELDS or item['row_id'] not in rows or item['row_id'] in seen:
            raise ValueError('Exact unique correction membership required')
        seen.add(item['row_id']);row=rows[item['row_id']]
        if item['original_row_sha256']!=P.digest(row) or item['source_sha256']!=row['source']['sha256']:
            raise ValueError('Correction original/source pin changed')
        if item['status'] not in ('corrected','unresolved'):raise ValueError('Assistant correction status required')
        _text(item['note'],2000,False)
        reasons=item['unresolved_reasons']
        if not isinstance(reasons,list) or len(reasons)>10 or (item['status']=='unresolved' and not reasons) or (item['status']=='corrected' and reasons):
            raise ValueError('Unresolved corrections require explicit reasons')
        for reason in reasons:_text(reason,500,False)
        interpretation=item['interpretation']
        if not isinstance(interpretation,dict) or set(interpretation)!=INTERPRETATION_FIELDS:raise ValueError('Exact interpretation qualifications required')
        for value in interpretation.values():_text(value,1000)
        replacement=item['replacement']
        if not isinstance(replacement,dict) or set(replacement)!={'country','group','capacity','assistant_proposal'}:raise ValueError('Exact replacement proposal required')
        capacity=replacement['capacity'];country=replacement['country'];group=replacement['group']
        if capacity not in ('national_candidate','collective','procedural','unclear','institutional','youth_testimony'):raise ValueError('Unknown provisional capacity')
        for entity in (country,group):
            if entity is not None:_text(entity,200,False)
        if capacity!='national_candidate' and country is not None:raise ValueError('Non-national correction cannot attribute country')
        if capacity=='national_candidate' and (not country or group is not None):raise ValueError('National candidate requires country only')
        proposal=replacement['assistant_proposal']
        if not isinstance(proposal,dict) or set(proposal)!=PROPOSAL_FIELDS:raise ValueError('Exact assistant proposal fields required')
        labels=proposal['discourse_labels']
        if not isinstance(labels,list) or len(set(labels))!=len(labels) or any(x not in ('requested_action','reported_condition','claimed_implementation') for x in labels):raise ValueError('Unknown discourse labels')
        if proposal['stance'] not in (None,'support','oppose','qualified') or (proposal['stance'] is not None and 'requested_action' not in labels):raise ValueError('Explicit requested action required for stance')
        if proposal['context_state'] not in ('anchored','unresolved'):raise ValueError('Unknown context state')
        if proposal['context_relation'] not in (None,'same_sentence','adjacent_sentence_review','full_statement_review'):raise ValueError('Unknown provisional correction relation')
        if proposal['context_state']=='anchored' and (proposal['context_relation'] is None or proposal['context_reason'] is not None):raise ValueError('Anchored correction requires relation and null reason')
        if proposal['context_state']=='unresolved' and (proposal['context_relation'] is not None or not proposal['context_reason']):raise ValueError('Unresolved context requires null relation and reason')
        for key in ('context_relation','context_reason'):
            if proposal[key] is not None:_text(proposal[key],1000,False)
        evidence=item['evidence']
        if not isinstance(evidence,list) or not 0<len(evidence)<=30:raise ValueError('Bounded correction evidence required')
        # The original statement number is a literal source-array position, not a speaker identity.
        original_pointer=row['evidence'][0]['pointer'].split('/paragraphs/')[0]
        pattern=re.escape(original_pointer)+r'/paragraphs/(0|[1-9]\d*)/sentences/(0|[1-9]\d*)/text'
        proofs=[];unique=set()
        for proof in evidence:
            if not isinstance(proof,dict) or set(proof)!={'pointer','quote'}:raise ValueError('Exact evidence pointer/quote required')
            pointer=proof['pointer'];quote=proof['quote'];_text(quote,4000,False)
            if not isinstance(pointer,str) or not re.fullmatch(pattern,pointer):raise ValueError('Evidence must remain inside original statement')
            try:
                value=sources[row['meeting_id']]
                for token in pointer.strip('/').split('/'):value=value[int(token)] if isinstance(value,list) else value[token]
            except (KeyError,IndexError,TypeError,ValueError):raise ValueError('Unresolvable correction evidence')
            if not isinstance(value,str) or quote not in value:raise ValueError('Correction evidence must be exact source substring')
            key=(pointer,quote)
            if key in unique:raise ValueError('Duplicate correction evidence')
            unique.add(key);proofs.append({'kind':'correction','pointer':pointer,'quote':quote,'quote_sha256':hashlib.sha256(quote.encode()).hexdigest()})
        row['original_proposal']=copy.deepcopy(row)
        row.update(copy.deepcopy(replacement));row['evidence']=proofs
        row['correction']={k:copy.deepcopy(item[k]) for k in ('status','note','unresolved_reasons','interpretation')}
        row['correction']['review_state']='assistant_provisional'
    packet=copy.deepcopy(original);packet.pop('packet_id')
    packet.update(schema='un.private-country-corrections.v1',version=VERSION,rows=list(rows.values()))
    packet['country_groups']=[{'country':c,'row_ids':[r['id'] for r in packet['rows'] if r['country']==c]} for c in sorted({r['country'] for r in packet['rows'] if r['country'] is not None})]
    warnings={}
    for row in packet['rows']:
        if row.get('correction',{}).get('status')!='unresolved':continue
        source=row['source'];key=(source['sha256'],source['statement_number'])
        warning=warnings.setdefault(key,{'source_sha256':source['sha256'],'statement_number':source['statement_number'],'source_url':source['url'],'origin_row_ids':[],'affected_row_ids':[],'unresolved_reasons':[]})
        warning['origin_row_ids'].append(row['id'])
        warning['unresolved_reasons']=sorted(set(warning['unresolved_reasons']+row['correction']['unresolved_reasons']))
    for key,warning in warnings.items():
        warning['affected_row_ids']=sorted(r['id'] for r in packet['rows'] if (r['source']['sha256'],r['source']['statement_number'])==key)
        warning['origin_row_ids'].sort()
    packet['source_warnings']=sorted(warnings.values(),key=lambda w:(w['source_sha256'],w['statement_number']))
    packet['non_national_row_ids']=[r['id'] for r in packet['rows'] if r['country'] is None]
    packet['input_fingerprints'].update(original_packet_id=original['packet_id'],corrections_sha256=expected_corrections_sha256,correction_method_sha256=method,flagged_row_ids_sha256=P.digest(expected_flagged_row_ids))
    packet['limitations'].append('Corrections remain assistant-provisional; literal source checks do not authenticate semantic interpretation or owner decisions.')
    if P.build_packet(store,bundles,frame,expected_inputs)!=original:raise ValueError('Original dependencies changed during correction build')
    if _method()!=method:raise ValueError('Correction method changed during build')
    packet['packet_id']=P.digest(packet)
    return packet


def validate_packet_identity(packet):
    if not isinstance(packet,dict) or packet.get('schema')!='un.private-country-corrections.v1' or packet.get('version')!=VERSION or packet.get('packet_id')!=P.digest({k:v for k,v in packet.items() if k!='packet_id'}):raise ValueError('Corrected packet identity mismatch')
    if packet.get('private_only') is not True or any(packet.get(k) is not False for k in ('owner_identity_verified','accepted_positions','comparisons_eligible')) or any(r.get('owner_decision') is not None for r in packet['rows']):raise ValueError('Corrections cannot grant owner acceptance')


def _legacy(packet):
    validate_packet_identity(packet)
    proxy=copy.deepcopy(packet);proxy.update(schema='un.private-country-review.v1',version=P.VERSION);proxy.pop('packet_id');proxy['packet_id']=P.digest(proxy)
    return proxy


def build_decisions(packet,choices,filters,previous=None):
    proxy=_legacy(packet)
    if not isinstance(filters,dict) or set(filters)!={'country','capacity','policy','correction_status','status'} or filters['capacity'] not in ('all','national_candidate','collective','procedural','unclear','institutional','youth_testimony') or filters['correction_status'] not in ('all','corrected','unresolved','unchanged'):
        raise ValueError('Exact corrected review filters required')
    basic={k:filters[k] for k in ('country','policy','status')}
    base=P.build_decisions(proxy,choices,basic)
    revision=1;parent=None
    if previous is not None:
        _validate_decisions(previous,packet);revision=previous['revision']+1;parent=previous['revision_sha256']
    base.update(schema='un.private-country-decisions-corrections.v1',packet_id=packet['packet_id'],original_packet_id=packet['input_fingerprints']['original_packet_id'],corrections_sha256=packet['input_fingerprints']['corrections_sha256'],revision=revision,parent_revision_sha256=parent,filters=copy.deepcopy(filters))
    base.pop('revision_sha256');base['revision_sha256']=P.digest(base)
    return base


def _validate_decisions(value,packet):
    fields={'schema','packet_id','original_packet_id','corrections_sha256','revision','parent_revision_sha256','choices','filters','owner_identity_verified','accepted_positions','comparisons_eligible','revision_sha256'}
    validate_packet_identity(packet)
    if not isinstance(value,dict) or set(value)!=fields or value.get('schema')!='un.private-country-decisions-corrections.v1' or value.get('packet_id')!=packet['packet_id'] or value.get('original_packet_id')!=packet['input_fingerprints']['original_packet_id'] or value.get('corrections_sha256')!=packet['input_fingerprints']['corrections_sha256'] or value.get('revision_sha256')!=P.digest({k:v for k,v in value.items() if k!='revision_sha256'}):raise ValueError('Corrected decision identity mismatch')
    proxy=_legacy(packet);converted=copy.deepcopy(value)
    for key in ('original_packet_id','corrections_sha256'):converted.pop(key)
    converted.update(schema='un.private-country-decisions.v1',packet_id=proxy['packet_id'],filters={k:value['filters'][k] for k in ('country','status','policy')})
    converted.pop('revision_sha256');converted['revision_sha256']=P.digest(converted)
    P._validate_decisions(converted,proxy)
    build_decisions(packet,value['choices'],value['filters'])


def save_packet(path,packet,**kwargs):
    if packet!=build_packet(**kwargs):raise ValueError('Corrected packet differs from authoritative inputs')
    return P._save(path,packet)


def load_packet(path,**kwargs):
    value=P._read(path)
    if value!=build_packet(**kwargs):raise ValueError('Saved corrections differ from authoritative inputs')
    return value


def save_decisions(path,decisions,*,packet,previous=None):
    _validate_decisions(decisions,packet)
    if decisions!=build_decisions(packet,decisions['choices'],decisions['filters'],previous):raise ValueError('Corrected decision history differs')
    return P._save(path,decisions)


def load_decisions(path,*,packet,previous=None):
    value=P._read(path);_validate_decisions(value,packet)
    if value!=build_decisions(packet,value['choices'],value['filters'],previous):raise ValueError('Corrected decision history differs')
    return value
