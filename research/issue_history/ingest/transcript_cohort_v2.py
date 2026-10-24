"""Version-two cohort coverage with guarded review roles; never historical coverage."""
import hashlib
from pathlib import Path
import re
import sqlite3
from ..store.repository import canonical_bytes
from .transcripts_un_audit import audit_source
from .transcripts_un_batch import get_current_batch
from .transcript_review_v3 import build_review_overlay

VERSION='transcript-cohort-2'
STAGES=('artifact_supplied','receipt_pinned','format_audit_verified','current_batch_validated','complete_provisional_review_linkage')
BODIES=('GA','SC',*('GA_C'+str(i) for i in range(1,7)))


def _digest(value): return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _body(mid):
    return 'SC' if mid.startswith('sc/') else 'GA_C'+mid.split('/')[1][1:] if re.match(r'ga/c[1-6]/',mid) else 'GA' if mid.startswith('ga/') else None


def build_cohort_coverage(store,frame,artifacts,review_inputs=None):
    """Every stage describes supplied cohort metadata, not a UN archive census."""
    if not isinstance(frame,dict) or frame.get('schema')!='un.passage-frame.v1' or not isinstance(frame.get('meetings'),list) or len(frame['meetings'])>1000: raise ValueError('Bounded sealed frame required')
    unsigned={k:v for k,v in frame.items() if k!='sha256'}
    if not isinstance(frame.get('sha256'),str) or not re.fullmatch('[a-f0-9]{64}',frame['sha256']) or _digest(unsigned)!=frame['sha256']: raise ValueError('Full frame seal mismatch')
    eligible={};seen=set()
    for e in frame['meetings']:
        if not isinstance(e,dict) or not isinstance(e.get('meeting_id'),str) or not re.fullmatch(r'[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+){1,5}',e['meeting_id']) or e['meeting_id'] in seen: raise ValueError('Invalid or duplicate frame meeting identity')
        mid=e['meeting_id'];seen.add(mid)
        if e.get('split')=='development' and e.get('has_transcript') is True and e.get('date') in ('2026-10-01','2026-10-02','2026-10-03','2026-10-04') and _body(mid):
            if e.get('source_url')!='https://transcripts.un.org/en/'+mid or e.get('json_url')!=e['source_url']+'.json' or not isinstance(e.get('body'),str): raise ValueError('Eligible frame source metadata mismatch')
            eligible[mid]={**e,'frame_sha256':frame['sha256']}
    review_inputs={} if review_inputs is None else review_inputs
    if not isinstance(artifacts,dict) or not isinstance(review_inputs,dict) or set(artifacts)-set(eligible) or set(review_inputs)-set(eligible): raise ValueError('Inputs outside the eligible development cohort are forbidden')
    all_review_inputs_sha=_digest(review_inputs)
    rows=[];countries={};groups={};input_hashes={};review_hashes={}
    for mid,e in sorted(eligible.items(),key=lambda item:(item[1]['date'],item[0])):
        stages={name:False for name in STAGES};gaps=[];audit=batch=overlay=None;raw=receipt=None
        def gap(stage,reason): gaps.append({'stage':stage,'reason':reason})
        if mid not in artifacts: gap('artifact_supplied','artifact_not_supplied')
        else:
            stages['artifact_supplied']=True;item=artifacts[mid]
            if not isinstance(item,dict) or set(item)!={'raw','receipt'}: gap('receipt_pinned','invalid_artifact_input')
            else:
                raw=item['raw'];receipt=item['receipt']
                if not isinstance(raw,bytes) or not 0<len(raw)<=5_000_000 or not isinstance(receipt,dict): gap('receipt_pinned','invalid_artifact_input')
                else:
                    sha=hashlib.sha256(raw).hexdigest();input_hashes[mid]={'raw_sha256':sha,'receipt_sha256':_digest(receipt)}
                    if receipt.get('schema')!='un.fresh-development-source-receipt.v1' or receipt.get('source_role')!='product_development' or receipt.get('meeting_id')!=mid or receipt.get('frame_date')!=e['date'] or receipt.get('frame_sha256')!=frame['sha256'] or receipt.get('source_url')!=e['json_url'] or receipt.get('final_url')!=e['json_url'] or type(receipt.get('bytes')) is not int or receipt['bytes']!=len(raw) or receipt.get('sha256')!=sha: gap('receipt_pinned','receipt_identity_or_hash_mismatch')
                    else:stages['receipt_pinned']=True
        if stages['receipt_pinned']:
            try:audit=audit_source(raw,receipt,e)
            except (ValueError,KeyError,TypeError,RecursionError):gap('format_audit_verified','unsupported_or_invalid_source_format')
            else:stages['format_audit_verified']=True
        if stages['format_audit_verified']:
            try:
                batch=get_current_batch(store,mid,e['json_url'])
                if not batch or batch.get('source_sha256')!=audit['source_sha256'] or batch.get('audit_sha256')!=_digest(audit) or batch.get('audit_input_fingerprints')!=audit['input_fingerprints']: raise ValueError('Missing or stale batch')
            except (ValueError,KeyError,TypeError,sqlite3.Error):gap('current_batch_validated','missing_stale_or_invalid_current_batch')
            else:stages['current_batch_validated']=True
        if stages['current_batch_validated'] and mid in review_inputs:
            review_hashes[mid]=_digest(review_inputs[mid])
            try:overlay=build_review_overlay(store,raw,receipt,e,review_inputs[mid])
            except (ValueError,KeyError,TypeError,sqlite3.Error):gap('complete_provisional_review_linkage','invalid_or_stale_provisional_review')
            else:stages['complete_provisional_review_linkage']=True
        elif stages['current_batch_validated']:gap('complete_provisional_review_linkage','provisional_review_not_supplied')
        for stage in STAGES:
            if not stages[stage] and not any(g['stage']==stage for g in gaps):gap(stage,'not_attempted_missing_prerequisite')
        row={'meeting_id':mid,'date':e['date'],'body':_body(mid),'recorded_body':e['body'],'stages':stages,'gaps':gaps,
             'source_sha256':audit['source_sha256'] if audit else input_hashes.get(mid,{}).get('raw_sha256'),
             'batch_artifact_id':batch['batch_artifact_id'] if stages['current_batch_validated'] else None,
             'review_overlay_sha256':_digest(overlay) if overlay else None,'accepted_positions':False,'comparisons_eligible':False}
        rows.append(row)
        if overlay:
            for c in overlay['countries']:
                target=countries.setdefault(c['country'],{'country':c['country'],'reviewed_meetings':set(),'requested_action_meetings':set(),'reported_condition_meetings':set(),'claimed_implementation_meetings':set(),'accepted_position':False,'comparison_eligible':False})
                target['reviewed_meetings'].add(mid)
                for field,out in (('requested_actions','requested_action_meetings'),('reported_conditions','reported_condition_meetings'),('claimed_implementation','claimed_implementation_meetings')):
                    if c[field]:target[out].add(mid)
            for i,g in enumerate(overlay['groups']):
                key=g['group'] if g['group'] is not None else mid+':unresolved:'+str(i)
                target=groups.setdefault(key,{'group':g['group'],'group_identity_status':g['group_identity_status'],'reviewed_meetings':set(),'accepted_position':False,'comparison_eligible':False})
                target['reviewed_meetings'].add(mid)
    def finished(values):
        return [{k:sorted(v) if isinstance(v,set) else v for k,v in values[name].items()} for name in sorted(values)]
    body_rows=[]
    for body in BODIES:
        subset=[r for r in rows if r['body']==body]
        body_rows.append({'body':body,'eligible_meetings':len(subset),'status':'declared_cohort' if subset else 'not_in_declared_cohort',**{stage:sum(r['stages'][stage] for r in subset) for stage in STAGES}})
    # A changed batch during reconciliation must not leave a current-stage claim.
    for row in rows:
        if row['stages']['current_batch_validated']:
            try:current=get_current_batch(store,row['meeting_id'],eligible[row['meeting_id']]['json_url'])
            except (ValueError,KeyError,TypeError,sqlite3.Error):current=None
            if not current or current['batch_artifact_id']!=row['batch_artifact_id']: raise ValueError('Current cohort batch changed during reconciliation')
    return {'schema':'un.transcript-cohort-coverage.v2','version':VERSION,'frame_sha256':frame['sha256'],'meetings':rows,'body_coverage':body_rows,
            'countries':finished(countries),'groups':finished(groups),
            'summary':{'eligible_meetings':len(rows),**{stage:sum(r['stages'][stage] for r in rows) for stage in STAGES},'national_candidate_countries':len(countries),'accepted_positions':0,'comparison_eligible':0},
            'source_scope':'declared_development_frame_2026_10_01_through_04_only','country_coverage_scope':'validated_provisional_review_source_coverage_not_country_opinion_or_archive_coverage',
            'archive_completeness':'unknown','accepted_positions':False,'comparisons_eligible':False,'private_only':True,
            'us_reference':{'status':'no_accepted_comparable_evidence','comparisons_eligible':False},
            'input_fingerprints':{'frame_sha256':frame['sha256'],'artifacts':input_hashes,'review_inputs':review_hashes,
                                  'all_review_inputs_sha256':all_review_inputs_sha,
                                  'method_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('transcript_cohort.py','transcripts_un_audit.py','transcripts_un_batch.py','transcript_review.py','transcript_review_v2.py','transcript_review_v3.py','transcript_cohort_v2.py','sc_drafts.py')}},
            'limitations':['All counts concern distinct meetings in the declared eligible cohort only.','No eligible SC entry means not represented in this cohort, never absence of UN meetings.',
                           'Missing sources or reviews remain stage gaps, not neutral or opposing positions.','Countries and groups are separate provisional review entities; no accepted positions or U.S. comparisons are produced.']}
