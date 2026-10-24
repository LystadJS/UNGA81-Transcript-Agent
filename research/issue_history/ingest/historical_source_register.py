"""Private metadata registration, separate from source authentication and intake."""
import calendar
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit, unquote
from ..store.repository import canonical_bytes

VERSION='historical-source-register-1'
FRAME_PIN='9a814f3f7986896f553072d5a610f6874b57a16adc4c15696da4998ce9b133e0'
FIELDS={'source_id','family','source_kind','native_id','date','language','body','source_url','original_sha256','declared_role','provenance_sha256','receipt'}
ROLES={'product_development','source_quality_audit','evaluation','restricted_research','unknown'}
KINDS={'statement':{'transcripts_un_asr','official_un_meeting_record','unknown'},'vote':{'official_un_vote','unknown'},'official_document':{'official_document','unknown'}}
BODY={'GA':'General Assembly','SC':'Security Council',**{'GA_C'+str(i):name+' Committee' for i,name in enumerate(['First','Second','Third','Fourth','Fifth','Sixth'],1)}}

def _digest(value): return hashlib.sha256(canonical_bytes(value)).hexdigest()
def _sha(value): return isinstance(value,str) and bool(re.fullmatch('[a-f0-9]{64}',value))
def _day(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value): raise ValueError('ISO calendar date required')
    try:return dt.date.fromisoformat(value)
    except ValueError:raise ValueError('Invalid calendar date')
def _method():return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def _url(value):
    if not isinstance(value,str) or len(value)>2048: raise ValueError('Bounded HTTPS source URL required')
    u=urlsplit(value)
    if u.scheme!='https' or not u.hostname or u.username or u.password or u.fragment: raise ValueError('Credential-free HTTPS source URL required')
    return u

def _native_url(value):
    u=_url(value)
    if u.hostname.lower() not in ('transcripts.un.org','www.transcripts.un.org'):return None
    path=unquote(u.path).strip('/').lower()
    if path.startswith('en/'):path=path[3:]
    if path.endswith('.json'):path=path[:-5]
    return path

def _body(native):
    if re.fullmatch(r'ga/\d+/\d+',native):return 'GA'
    m=re.fullmatch(r'ga/c([1-6])/\d+/\d+',native)
    if m:return 'GA_C'+m[1]
    if re.fullmatch(r'sc/\d+',native):return 'SC'
    return None

def build_register(*,as_of,frame,entries,expected_frame_sha256=FRAME_PIN):
    """Register declared metadata, never source bodies or accepted source authority."""
    method=_method();end=_day(as_of)
    if end.year<=10:raise ValueError('Window date outside supported range')
    y=end.year-10;base=dt.date(y,end.month,min(end.day,calendar.monthrange(y,end.month)[1]));start=base+dt.timedelta(days=1)
    if not _sha(expected_frame_sha256) or not isinstance(frame,dict) or frame.get('schema')!='un.passage-frame.v1':raise ValueError('Externally pinned frame required')
    frame_hash=_digest({k:v for k,v in frame.items() if k!='sha256'})
    if frame.get('sha256')!=expected_frame_sha256 or frame_hash!=expected_frame_sha256:raise ValueError('Authoritative frame pin mismatch')
    meetings=frame.get('meetings')
    if not isinstance(meetings,list) or len(meetings)>10000:raise ValueError('Bounded frame roster required')
    roster={};protected=set()
    for m in meetings:
        if not isinstance(m,dict) or not isinstance(m.get('meeting_id'),str) or m['meeting_id'] in roster:raise ValueError('Unique frame identities required')
        _day(m.get('date'));roster[m['meeting_id']]=m
        if m.get('split')!='development':protected.add(m['meeting_id'].lower())
    if not isinstance(entries,list) or len(entries)>100000:raise ValueError('Bounded metadata entry list required')
    out=[];seen=set()
    for e in entries:
        if not isinstance(e,dict) or set(e)!=FIELDS:raise ValueError('Exact metadata-only entry fields required')
        sid=e['source_id'];native=e['native_id'];role=e['declared_role'];family=e['family'];kind=e['source_kind']
        if not isinstance(sid,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9:._/=-]{0,499}',sid) or sid in seen:raise ValueError('Unique bounded source identity required')
        seen.add(sid)
        if not isinstance(native,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9:._/-]{0,299}',native):raise ValueError('Native identity required')
        date=_day(e['date']);u=_url(e['source_url'])
        if family not in KINDS or kind not in KINDS[family] or role not in ROLES:raise ValueError('Unsupported family, source kind or declared role')
        if not isinstance(e['language'],str) or not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})?',e['language']):raise ValueError('Explicit language metadata required')
        if e['body'] is not None and (not isinstance(e['body'],str) or len(e['body'])>100):raise ValueError('Invalid body metadata')
        if not _sha(e['original_sha256']):raise ValueError('Declared original artifact hash required')
        hashes=e['provenance_sha256']
        if not isinstance(hashes,list) or len(hashes)>100 or any(not _sha(h) for h in hashes) or len(set(hashes))!=len(hashes):raise ValueError('Distinct provenance hashes required')
        receipt=e['receipt']
        if receipt is not None and not isinstance(receipt,dict):raise ValueError('Receipt metadata must be an object or null')
        m=roster.get(native);url_native=_native_url(e['source_url']);reserved=native.lower() in protected or url_native in protected
        channel=family=='statement' and kind in ('transcripts_un_asr','official_un_meeting_record')
        date_guard=channel and e['date'] in ('2026-10-05','2026-10-06')
        authoritative='evaluation' if reserved else 'unknown'
        eligible_frame=bool(m and m.get('split')=='development' and m.get('has_transcript') is True and _body(native) and '2026-10-01'<=m['date']<='2026-10-04')
        if m and m.get('split')=='development' and not reserved and not date_guard:authoritative='product_development'
        effective=role if role in ('source_quality_audit','evaluation','restricted_research') else authoritative
        reason='historical_provenance_and_exclusion_coverage_unknown';eligible=False
        receipt_pinned=False
        if reserved or date_guard:effective='evaluation';reason='reserved_source_blocked'
        elif not start<=date<=end:reason='outside_rolling_window'
        elif role in ('source_quality_audit','evaluation','restricted_research'):reason='restrictive_declared_role'
        elif authoritative=='product_development' and not (eligible_frame and family=='statement' and kind=='transcripts_un_asr'):reason='unsupported_development_source_scope'
        elif eligible_frame and family=='statement' and kind=='transcripts_un_asr':
            exact=(e['date']==m['date'] and e['source_url']==m.get('json_url') and e['body']==_body(native) and m.get('body')==BODY[_body(native)] and e['language']=='en')
            required={'schema':'un.fresh-development-source-receipt.v1','source_role':'product_development','meeting_id':native,'frame_date':m['date'],'frame_sha256':frame_hash,'source_url':m.get('json_url'),'final_url':m.get('json_url'),'sha256':e['original_sha256']}
            receipt_pinned=bool(exact and receipt is not None and all(receipt.get(k)==v for k,v in required.items()) and type(receipt.get('bytes')) is int and 0<receipt['bytes']<=5*1024*1024 and frame_hash in hashes and _digest(receipt) in hashes)
            eligible=receipt_pinned;reason='development_receipt_metadata_linked' if eligible else 'development_metadata_or_receipt_mismatch'
        out.append({'source_id':sid,'family':family,'source_kind':kind,'native_id':native,'date':e['date'],'language':e['language'],'body':e['body'],'source_url':e['source_url'],'original_sha256':e['original_sha256'],'declared_role':role,'authoritative_role':authoritative,'effective_role':effective,'role_authority':'sealed_frame' if authoritative!='unknown' else 'unverified','provenance_sha256':sorted(hashes),'receipt_sha256':_digest(receipt) if receipt is not None else None,'receipt_retrieved_at':receipt.get('retrieved_at') if receipt is not None and isinstance(receipt.get('retrieved_at'),str) else None,'receipt_metadata_pinned':receipt_pinned,'in_window':start<=date<=end,'reserved_blocked':reserved or date_guard,'intake_eligible':eligible,'metadata_eligible_for_source_validation':eligible,'raw_verification_required':True,'eligibility_reason':reason,'exclusion_coverage':'known_development_frame_only' if eligible_frame else 'unknown','production_intake_accepted':False,'public_export_approved':False})
    # Restrictions close over aliases, rather than allowing a fresh source_id to bypass them.
    identities={}
    for row in out:
        u=_url(row['source_url'])
        url_key=('transcripts_un',_native_url(row['source_url'])) if _native_url(row['source_url']) is not None else (u.hostname.lower(),unquote(u.path).rstrip('/').lower())
        keys=[('native',row['family'],row['native_id'].lower()),('url',*url_key),('hash',row['original_sha256'])]
        for key in keys:identities.setdefault(key,[]).append(row)
    for group in identities.values():
        if len(group)>1:raise ValueError('Duplicate logical source aliases require explicit separate review')
    out.sort(key=lambda r:r['source_id'])
    if _method()!=method:raise ValueError('Register method changed during validation')
    result={'schema':'un.historical-source-register.v1','version':VERSION,'window':{'start':start.isoformat(),'end':end.isoformat(),'as_of':as_of,'definition':'ten_calendar_years_inclusive_end; subtract_ten_years_clamp_february_then_add_one_day'},'entries':out,'summary':{'registered_metadata':len(out),'intake_eligible':sum(r['intake_eligible'] for r in out),'reserved_blocked':sum(r['reserved_blocked'] for r in out),'production_intake_accepted':0,'public_export_approved':0},'archive_coverage':'unknown','historical_exclusion_coverage':'unknown_no_authoritative_28_or_64_roster_available','eligibility_scope':'candidate_gate_only_not_body_or_model_authorization','frame_pin_scope':'explicit_trusted_input_configuration_not_independent_authority_authentication','verification_scope':'provided_receipt_metadata_hash_linkage_not_independent_raw_source_authentication','window_scope':'publication_date_window_not_historical_availability_vintage_or_backtest_cutoff','translation_authority':'unverified','private_only':True,'production_intake_accepted':False,'public_export_approved':False,'input_fingerprints':{'frame_sha256':frame_hash,'expected_frame_sha256':expected_frame_sha256,'entries_sha256':_digest(entries),'method_sha256':method}}
    result['annual_metadata']=[{'year':year,'start':max(start,dt.date(year,1,1)).isoformat(),'end':min(end,dt.date(year,12,31)).isoformat(),'registered_metadata':sum(r['in_window'] and int(r['date'][:4])==year for r in out),'metadata_eligible_for_source_validation':sum(r['metadata_eligible_for_source_validation'] and int(r['date'][:4])==year for r in out),'expected_source_count':None,'archive_coverage':'unknown'} for year in range(start.year,end.year+1)]
    result['content_sha256']=_digest(result)
    return result

def _expected(register,kwargs):
    expected=build_register(**kwargs)
    if register!=expected:raise ValueError('Register differs from recomputed authoritative inputs')
    return canonical_bytes(expected)

def _commit(stage,path):
    # Windows rename rejects an existing destination; POSIX rename would replace it.
    if os.name=='nt':os.rename(stage,path)
    else:os.link(stage,path)

def _publish(path,data):
    stage=None
    try:
        fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',suffix='.stage',dir=str(path.parent))
        stage=Path(name)
        with os.fdopen(fd,'wb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        # Atomic no-clobber publication; never use replacing rename semantics.
        _commit(stage,path)
        try:
            directory=os.open(path.parent,os.O_RDONLY)
            try:os.fsync(directory)
            finally:os.close(directory)
        except OSError:pass  # Directory fsync is unavailable on some platforms.
    finally:
        if stage is not None:stage.unlink(missing_ok=True)

def save_register(path,register,**kwargs):
    """Immutable staged save: failures never expose partially written snapshots."""
    data=_expected(register,kwargs);path=Path(path)
    if path.is_symlink():raise ValueError('Register aliases are forbidden')
    if path.exists():
        if path.read_bytes()!=data:raise ValueError('Existing snapshot differs or is corrupt')
        return str(path.resolve())
    try:_publish(path,data)
    except FileExistsError:
        if path.is_symlink() or path.read_bytes()!=data:raise ValueError('Concurrent snapshot differs')
    return str(path.resolve())

def load_register(path,**kwargs):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>64*1024*1024:raise ValueError('Bounded regular register snapshot required')
    try:value=json.loads(path.read_bytes())
    except (ValueError,UnicodeError):raise ValueError('Corrupt register snapshot')
    data=_expected(value,kwargs)
    if path.read_bytes()!=data:raise ValueError('Noncanonical or changed register snapshot')
    return value
