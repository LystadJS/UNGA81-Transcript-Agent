"""Pure supplied-catalog/receipt reconciliation, never archive-completeness proof."""
import datetime as dt
import hashlib
import json
import re

VERSION='statement-coverage-1'
BODIES={'GA','SC',*('GA_C'+str(i) for i in range(1,7))}
PAGE_FIELDS={'family','date','page','total','has_more','metadata_sha256','meetings','availability','transcript_text_fetched'}
MEETING_FIELDS={'meeting_id','date','body','recorded_body','category','transcript_advertised','pageUrl','jsonUrl','textUrl'}
RECEIPT_FIELDS={'schema','meeting_id','date','body','inventory_metadata_sha256','source_url','retrieved','hash_verified','extraction_complete','expected_sha256','source_sha256','normalized_sha256','extraction_method_version'}


def _date(value):
    try: return isinstance(value,str) and dt.date.fromisoformat(value).isoformat()==value
    except ValueError: return False


def _sha(value):
    return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def reconcile_coverage(*,start,end,bodies,pages,receipts):
    """GA means GA plenary exactly; committees require explicit GA_C1..6."""
    if not _date(start) or not _date(end) or start>end: raise ValueError('Invalid requested date range')
    first,last=dt.date.fromisoformat(start),dt.date.fromisoformat(end)
    try: anniversary=first.replace(year=first.year+10)
    except ValueError: anniversary=dt.date(first.year+10,2,28) if first.year<=9989 else dt.date.max
    if last>=anniversary or (last-first).days>3660: raise ValueError('Coverage request exceeds ten-year bound')
    if not isinstance(bodies,list) or not bodies or any(not isinstance(b,str) or b not in BODIES for b in bodies) or len(set(bodies))!=len(bodies): raise ValueError('Explicit distinct supported bodies required')
    if not isinstance(pages,list) or len(pages)>183000 or not isinstance(receipts,list) or len(receipts)>1000000: raise ValueError('Coverage metadata exceeds bounds')
    days={};meetings={};meeting_groups={};page_ids=set()
    for p in pages:
        if not isinstance(p,dict) or set(p)!=PAGE_FIELDS or p.get('family')!='un_transcript_inventory' or p.get('transcript_text_fetched') is not False or not _date(p.get('date')) or not start<=p['date']<=end or type(p.get('page')) is not int or not 1<=p['page']<=50 or type(p.get('total')) is not int or not 0<=p['total']<=25000 or type(p.get('has_more')) is not bool or not _sha(p.get('metadata_sha256')) or not isinstance(p.get('meetings'),list) or len(p['meetings'])>500: raise ValueError('Invalid inventory page contract')
        key=(p['date'],p['page'])
        if key in page_ids: raise ValueError('Duplicate inventory page identity')
        page_ids.add(key);days.setdefault(p['date'],[]).append(p)
        expected_availability='entries_returned_not_transcript_verified' if p['meetings'] else 'no_entries_returned_not_verified_absence'
        if p.get('availability')!=expected_availability: raise ValueError('Inventory availability mismatch')
        for m in p['meetings']:
            if not isinstance(m,dict) or set(m)!=MEETING_FIELDS: raise ValueError('Invalid inventory meeting fields')
            mid=m.get('meeting_id')
            if not isinstance(mid,str) or len(mid)>500 or not re.fullmatch(r'[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+){1,5}',mid) or mid in meetings or m.get('date')!=p['date'] or type(m.get('transcript_advertised')) is not bool: raise ValueError('Duplicate or inconsistent inventory meeting identity')
            body='SC' if mid.startswith('sc/') else 'GA_C'+mid.split('/')[1][1:] if re.match(r'ga/c[1-6]/',mid) else 'GA' if mid.startswith('ga/') else 'other'
            if m.get('body')!=body or any(m[k] is not None and (not isinstance(m[k],str) or len(m[k])>300) for k in ('recorded_body','category')): raise ValueError('Inventory body metadata mismatch')
            for field,suffix in (('pageUrl',''),('jsonUrl','.json'),('textUrl','.txt')):
                if m.get(field) is not None and m[field]!='https://transcripts.un.org/en/'+mid+suffix: raise ValueError('Inventory source link mismatch')
            meetings[mid]=(m,p['metadata_sha256'])
            meeting_groups.setdefault((m['date'],m['body']),[]).append(mid)
            if len(meetings)>1000000: raise ValueError('Meeting metadata exceeds bound')
    catalog={}
    for day,items in days.items():
        ordered=sorted(items,key=lambda p:p['page']);totals={p['total'] for p in items};terminal=[p['page'] for p in items if not p['has_more']]
        if len(totals)!=1 or len(terminal)>1 or terminal and terminal[0]!=ordered[-1]['page']: raise ValueError('Unstable catalog totals or contradictory terminal pages')
        count=sum(len(p['meetings']) for p in items);total=ordered[0]['total']
        if count>total: raise ValueError('Catalog meeting count exceeds advertised total')
        complete=bool(terminal) and [p['page'] for p in ordered]==list(range(1,terminal[0]+1))
        if complete and count!=total: raise ValueError('Terminal catalog total does not reconcile distinct meetings')
        catalog[day]=(complete,total)
    declared={};receipt_fingerprints=set()
    for r in receipts:
        if not isinstance(r,dict) or set(r)!=RECEIPT_FIELDS or r.get('schema')!='un.statement-artifact-receipt.v1' or any(type(r.get(k)) is not bool for k in ('retrieved','hash_verified','extraction_complete')): raise ValueError('Invalid retrieval receipt contract')
        mid=r.get('meeting_id')
        if mid not in meetings: raise ValueError('Receipt has no supplied inventory meeting')
        m,metadata_sha=meetings[mid]
        if r.get('date')!=m['date'] or r.get('body')!=m['body'] or r.get('inventory_metadata_sha256')!=metadata_sha or r.get('source_url') is None or r['source_url'] not in (m['jsonUrl'],m['textUrl']): raise ValueError('Receipt inventory/source linkage mismatch')
        if r['retrieved']:
            if not _sha(r.get('source_sha256')): raise ValueError('Retrieved artifact requires declared raw hash')
        elif r.get('source_sha256') is not None: raise ValueError('Unretrieved artifact cannot assert raw hash')
        if r.get('expected_sha256') is not None and not _sha(r['expected_sha256']): raise ValueError('Invalid expected artifact hash')
        if r['hash_verified'] and (not r['retrieved'] or not _sha(r.get('expected_sha256')) or r['expected_sha256']!=r['source_sha256']): raise ValueError('Hash-verification claim lacks matching retrieved hash')
        if r['extraction_complete']:
            if not r['hash_verified'] or not _sha(r.get('normalized_sha256')) or not isinstance(r.get('extraction_method_version'),str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}',r['extraction_method_version']): raise ValueError('Extraction claim lacks verified raw/normalized/method linkage')
        elif r.get('normalized_sha256') is not None or r.get('extraction_method_version') is not None: raise ValueError('Incomplete extraction cannot assert normalized output')
        fingerprint=_digest(r);key=(mid,r['source_url'])
        if key in declared and declared[key]!=r: raise ValueError('Contradictory receipts for one source artifact')
        declared[key]=r;receipt_fingerprints.add(fingerprint)
    by_meeting={}
    for (mid,url),r in declared.items(): by_meeting.setdefault(mid,[]).append(r)
    rows=[]
    for offset in range((last-first).days+1):
        day=(first+dt.timedelta(days=offset)).isoformat();complete,total=catalog.get(day,(False,None))
        status='reconciled_catalog' if complete and total else 'unknown' if total is None or complete else 'incomplete_pages'
        for body in sorted(bodies):
            selected=[]
            for mid in sorted(meeting_groups.get((day,body),[])):
                m,pin=meetings[mid];rr=by_meeting.get(mid,[])
                selected.append({**m,'inventory_metadata_sha256':pin,'receipt_present':bool(rr),
                                 'artifact_receipts':[dict(r) for r in sorted(rr,key=lambda r:r['source_url'])],
                                 'receipt_reported_retrieved':any(r['retrieved'] for r in rr),
                                 'receipt_reported_hash_verified':any(r['hash_verified'] for r in rr),
                                 'receipt_reported_extraction_complete':any(r['extraction_complete'] for r in rr)})
            rows.append({'date':day,'body':body,'catalog_status':status,'catalog_pages_reconciled':complete,
                         'advertised_meetings':len(selected),'transcript_advertised':sum(m['transcript_advertised'] for m in selected),
                         'not_advertised':sum(not m['transcript_advertised'] for m in selected),
                         'retrieved':sum(m['receipt_reported_retrieved'] for m in selected),
                         'receipt_reported_hash_verified':sum(m['receipt_reported_hash_verified'] for m in selected),
                         'extraction_complete':sum(m['receipt_reported_extraction_complete'] for m in selected),
                         'unknown_meetings':sum(not m['receipt_present'] for m in selected) if complete and total else None,'meetings':selected})
    summary={k:sum(r[k] for r in rows) for k in ('advertised_meetings','transcript_advertised','not_advertised','retrieved','receipt_reported_hash_verified','extraction_complete')}
    summary.update(unknown_meetings=None if any(r['unknown_meetings'] is None for r in rows) else sum(r['unknown_meetings'] for r in rows),unknown_day_body_rows=sum(r['catalog_status']!='reconciled_catalog' for r in rows))
    return {'schema':'un.statement-coverage.v1','version':VERSION,'requested_window':{'start':start,'end':end},'bodies':sorted(bodies),
            'body_selection_scope':'exact_codes_GA_does_not_include_committees','rows':rows,'summary':summary,'private_only':True,
            'archive_completeness':'unknown','verification_scope':'provided_receipts_not_recomputed_content',
            'input_fingerprints':{'pages_sha256':_digest(pages),'receipts_sha256':_digest(sorted(receipt_fingerprints)),'request_sha256':_digest({'start':start,'end':end,'bodies':sorted(bodies)})},
            'limitations':['Reconciled pages establish supplied catalog consistency only, not complete UN archive coverage.','Empty or missing catalog days remain unknown.','Receipt status declarations are not independently recomputed artifact hashes.','No transcript wording, speakers, country positions or political statistics are processed.']}
