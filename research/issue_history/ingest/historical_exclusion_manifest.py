"""Pinned historical research exclusions, never permission for product intake."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit,unquote,parse_qs
from ..store.repository import canonical_bytes
from . import historical_source_register as register

VERSION='historical-exclusion-manifest-1'
DEFAULT_PINS={'split_records_sha256':'9f82613e7057a66f9ca7ccb550fade49797d4457fd67ada2443ef6a00edb9ef5','design_bytes_sha256':'265b4e00c254f75784cff8aa5937970dfbc0ce16182b557e38316afa9ba4b314','split_code_sha256':'82f6a3856707655f780dc39280d953e9d6cf2ad6f4b5baf15400535c755b5f3b','sampler_code_sha256':'a7b5e25c8c5ad5bf9e14bae83f1eda7555cb5d163f2075a99b2672cd0a44d7d6'}
PHASES={'development_acquisition','independent_source_auth_quality_audit'}

def _digest(value):return hashlib.sha256(canonical_bytes(value)).hexdigest()
def _methods():
    return {'historical_exclusion_manifest.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'historical_source_register.py':hashlib.sha256(Path(register.__file__).read_bytes()).hexdigest()}
def _canonical(value):
    if not isinstance(value,str) or not re.fullmatch(r'A/[1-9]\d*/PV\.[1-9]\d*',value):raise ValueError('Canonical General Assembly PV symbol required')
    return value

def resolve_symbol(symbol=None,source_url=None):
    """Resolve literal official symbol aliases only; never guess meeting identities."""
    values=[]
    def normalize(s):
        if not isinstance(s,str) or len(s)>200:raise ValueError('Bounded symbol required')
        return _canonical(re.sub(r'\s+','',s).upper())
    if symbol is not None:values.append(normalize(symbol))
    if source_url is not None:
        if not isinstance(source_url,str) or len(source_url)>2048:raise ValueError('Bounded official URL required')
        u=urlsplit(source_url)
        if u.scheme!='https' or u.hostname not in ('documents.un.org','docs.un.org','undocs.org') or u.username or u.password or u.fragment:raise ValueError('Official credential-free source URL required')
        q=parse_qs(u.query,keep_blank_values=True);candidates=q.get('symbol',[])+q.get('s',[])
        path=unquote(u.path).strip('/')
        if path.lower().startswith('en/'):path=path[3:]
        path_symbol=None
        try:path_symbol=normalize(path)
        except ValueError:pass  # Generic document/PDF paths carry their symbol in the selector.
        if not candidates:candidates=[path]
        if len(candidates)!=1:raise ValueError('Ambiguous source symbol URL')
        selected=normalize(unquote(candidates[0]))
        if path_symbol is not None and path_symbol!=selected:raise ValueError('Conflicting literal path and query symbols')
        values.append(selected)
    if not values or len(set(values))!=1:raise ValueError('Missing or conflicting source symbol aliases')
    return values[0]

def build_exclusion_manifest(*,as_of,split_records,design_bytes,authority_pins,expected_authority_pins=None):
    methods=_methods();expected=dict(DEFAULT_PINS if expected_authority_pins is None else expected_authority_pins)
    if set(expected)!=set(DEFAULT_PINS) or any(not register._sha(v) for v in expected.values()):raise ValueError('Explicit independently trusted authority pins required')
    if not isinstance(authority_pins,dict) or set(authority_pins)!={'split_code_sha256','sampler_code_sha256'} or any(authority_pins[k]!=expected[k] for k in authority_pins):raise ValueError('Authority code declarations differ from trusted configuration')
    end=register._day(as_of)
    if end.year<=10:raise ValueError('Invalid ten-year anchor')
    import calendar
    base=dt.date(end.year-10,end.month,min(end.day,calendar.monthrange(end.year-10,end.month)[1]));start=base+dt.timedelta(days=1)
    if not isinstance(split_records,list) or not split_records or len(split_records)>10000:raise ValueError('Bounded historical split metadata required')
    seen=set();records=[]
    for row in split_records:
        if not isinstance(row,dict) or set(row)!={'year','symbol','phase'} or type(row['year']) is not int or not 1900<=row['year']<=2100 or row['phase'] not in PHASES:raise ValueError('Exact historical role metadata required')
        symbol=_canonical(row['symbol'])
        if int(symbol.split('/')[1])+1945!=row['year']:raise ValueError('Symbol session and declared source year disagree')
        if symbol in seen:raise ValueError('Duplicate historical symbol or role conflict')
        seen.add(symbol);records.append(row)
    if _digest(split_records)!=expected['split_records_sha256']:raise ValueError('Pinned historical role roster mismatch')
    if not isinstance(design_bytes,bytes) or not 0<len(design_bytes)<=1000000 or hashlib.sha256(design_bytes.replace(b'\r\n',b'\n')).hexdigest()!=expected['design_bytes_sha256']:raise ValueError('Pinned public symbol-list bytes mismatch')
    try:lines=design_bytes.decode('utf-8').splitlines()
    except UnicodeError:raise ValueError('UTF-8 symbol metadata required')
    selected=[]
    for line in lines:
        if not line.strip() or line.lstrip().startswith('#'):continue
        selected.append(_canonical(line.strip()))
    if len(set(selected))!=len(selected) or not selected or set(selected)-seen:raise ValueError('Public design membership must be unique within role roster')
    output=[]
    for row in sorted(records,key=lambda r:(r['year'],r['symbol'])):
        year=row['year'];lo=dt.date(year,1,1);hi=dt.date(year,12,31);audit=row['phase']=='independent_source_auth_quality_audit'
        output.append({'symbol':row['symbol'],'year':year,'year_interval':{'start':lo.isoformat(),'end':hi.isoformat()},'date_precision':'recorded_session_start_grouping_year_only','window_relation':'outside' if hi<start or lo>end else 'overlaps_exact_date_unknown','upstream_phase':row['phase'],'upstream_role':'source_quality_audit' if audit else 'research_development','effective_role':'source_quality_audit' if audit else 'restricted_research','design_selected':row['symbol'] in selected,'product_intake_eligible':False,'public_export_approved':False,'role_scope':'research_only_not_product_development_permission'})
    if _methods()!=methods:raise ValueError('Exclusion adapter dependencies changed')
    result={'schema':'un.historical-exclusion-manifest.v1','version':VERSION,'window':{'as_of':as_of,'start':start.isoformat(),'end':end.isoformat(),'scope':'publication_date_window_not_historical_availability_vintage'},'entries':output,'public_design_symbols':selected,'summary':{'registered_symbols':len(output),'research_development':sum(r['upstream_role']=='research_development' for r in output),'source_quality_audit':sum(r['upstream_role']=='source_quality_audit' for r in output),'public_design_members':len(selected),'outside_window_year_intervals':sum(r['window_relation']=='outside' for r in output),'product_intake_eligible':0},'private_only':True,'product_intake_eligible':False,'public_export_approved':False,'full_design_digests_recomputed':False,'sampling_weights_inferred':False,'historical_exclusion_coverage':'known_exact_roster_only_off_roster_unknown','in_window_archive_coverage':'unknown','year_scope':'frozen_General_Debate_roster_session_start_grouping_year_not_general_UN_meeting_date_validation','register_bridge':'future_explicit_version_required_no_current_intake_enablement','input_fingerprints':{'split_records_sha256':_digest(split_records),'design_bytes_sha256':hashlib.sha256(design_bytes).hexdigest(),'design_lf_sha256':hashlib.sha256(design_bytes.replace(b'\r\n',b'\n')).hexdigest(),'design_authority_hash_scope':'CRLF_normalized_to_LF_in_memory_original_bytes_unchanged','authority_code_hash_scope':'declared_LF_normalized_code_bytes_not_recomputed_here','authority_code_declarations':dict(authority_pins),'expected_authority_pins':expected,'method_sha256':methods},'authority_scope':'exact_role_roster_and_public_symbol_membership; code_hashes_are_matched_declarations_not_recomputed_code_bytes','limitations':['The public 64-symbol list does not verify private-index rows, full design digest, probabilities or sampling weights.','Research acquisition status never authorizes product development or source publication.','Only source year is known; no exact source date, full historical availability or in-window completeness is inferred.','Historical source bodies are neither read nor authenticated.']}
    result['content_sha256']=_digest(result);return result

def lookup_exclusion(manifest,*,symbol=None,source_url=None,**kwargs):
    if not kwargs:raise ValueError('Lookup requires current independently pinned authority inputs')
    _expected(manifest,kwargs)
    canonical=resolve_symbol(symbol,source_url)
    matches=[r for r in manifest.get('entries',[]) if r.get('symbol')==canonical]
    if len(matches)>1:raise ValueError('Conflicting historical aliases')
    return {'symbol':canonical,'role_metadata':matches[0] if matches else None,'exclusion_coverage':'known_exact_roster' if matches else 'unknown','product_intake_eligible':False}

def _expected(value,kwargs):
    expected=build_exclusion_manifest(**kwargs)
    if value!=expected:raise ValueError('Manifest differs from recomputed authority inputs')
    return canonical_bytes(expected)

def save_manifest(path,manifest,**kwargs):
    data=_expected(manifest,kwargs);path=Path(path)
    if path.is_symlink():raise ValueError('Manifest aliases forbidden')
    if path.exists():
        if path.read_bytes()!=data:raise ValueError('Existing immutable manifest differs or is corrupt')
    else:
        try:register._publish(path,data)
        except FileExistsError:
            if path.is_symlink() or path.read_bytes()!=data:raise ValueError('Concurrent manifest differs')
    return str(path.resolve())

def load_manifest(path,**kwargs):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>64000000:raise ValueError('Bounded regular manifest required')
    try:value=json.loads(path.read_bytes())
    except (ValueError,UnicodeError):raise ValueError('Corrupt exclusion manifest')
    if path.read_bytes()!=_expected(value,kwargs):raise ValueError('Noncanonical or changed immutable manifest')
    return value
