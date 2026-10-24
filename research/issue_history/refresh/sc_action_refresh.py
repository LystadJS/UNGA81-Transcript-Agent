"""Private accepted-state refresh lane. Never ingests or exports public bundles."""
import json
import hashlib
import os
from pathlib import Path
import re
import uuid
import datetime as dt
from . import sc_action_cache as cache
from .sc_action_cache import cached_crosswalk, _atomic

VERSION='sc-action-refresh-1'
MARKER={'schema':'un.sc-action-refresh-root.v1','version':VERSION}


def _configuration_identity(collection_file,ddl_database,ddl_raw_csv,review_file):
    """Resolve path safety before operational hash/proof validation."""
    result={'inputs':{str(i):{'path':str(Path(p).resolve())} for i,p in enumerate((collection_file,ddl_database,ddl_raw_csv))},
            'dependencies':{name:{'path':str(Path(p).resolve())} for name,p in cache._dependency_paths().items()},'proofs':{}}
    if review_file is not None:
        review=Path(review_file).resolve();result['proofs'][str(review)]=''
        if review.exists():
            if review.stat().st_size>2_000_000: raise ValueError('Review envelope exceeds bound')
            try: payload=json.loads(review.read_bytes())
            except (ValueError,UnicodeError): payload={}
            for c in payload.get('corrections',[]):
                relative=c.get('source',{}).get('evidence_file')
                if not isinstance(relative,str) or Path(relative).is_absolute(): raise ValueError('Unsafe review evidence configuration')
                evidence=(review.parent/relative).resolve()
                if not evidence.is_relative_to(review.parent): raise ValueError('Unsafe review evidence configuration')
                result['proofs'][str(evidence)]=''
    return result


def _safe_state(state_dir,cache_dir,identity):
    raw=Path(state_dir).absolute();root=raw.resolve();cache_root=Path(cache_dir).resolve()
    for p in (raw,*raw.parents):
        if p.is_symlink() or getattr(p,'is_junction',lambda:False)(): raise ValueError('Refresh state path traverses an alias')
    if root==cache_root or root.is_relative_to(cache_root) or cache_root.is_relative_to(root): raise ValueError('State and cache directories must be independent')
    for p in (root,*root.parents):
        if (p/'.git').exists(): raise ValueError('Private refresh state must be outside repository trees')
    inputs=[Path(v['path']).resolve() for v in identity['inputs'].values()]+[Path(p).resolve() for p in identity['proofs']]+[Path(v['path']).resolve() for v in identity['dependencies'].values()]+[Path(__file__).resolve()]
    if any(p==root or p.is_relative_to(root) for p in inputs): raise ValueError('Refresh state contains an input')
    marker=root/'refresh-root.json'
    if root.exists():
        if not root.is_dir(): raise ValueError('Refresh state must be a directory')
        if any(root.iterdir()):
            cache._safe_file(marker,inputs)
            if not marker.is_file() or marker.stat().st_size>1024: raise ValueError('Nonempty state directory is not owned')
            try: valid=json.loads(marker.read_bytes())==MARKER
            except (ValueError,UnicodeError): valid=False
            if not valid: raise ValueError('Refresh ownership marker mismatch')
    for name in ('checkpoint.json','health.json'): cache._safe_file(root/name,inputs)
    return root,inputs


def _read_checkpoint(root,cache_root,inputs):
    pointer=root/'checkpoint.json'
    if not pointer.exists(): return None
    if pointer.stat().st_size>4096: raise ValueError('Checkpoint pointer exceeds bound')
    p=json.loads(pointer.read_bytes());leaf=p.get('record','')
    if p.get('schema')!='un.sc-action-refresh-pointer.v1' or not isinstance(leaf,str) or not re.fullmatch(r'[1-9]\d*\.[a-f0-9]{32}\.json',leaf): raise ValueError('Invalid accepted pointer')
    file=root/leaf;cache._safe_file(file,inputs)
    if file.stat().st_size>2_000_000 or cache._hash(file)!=p.get('record_sha256'): raise ValueError('Accepted record changed')
    record=json.loads(file.read_bytes())
    if record.get('schema')!='un.sc-action-refresh-checkpoint.v1' or record.get('version')!=VERSION or not isinstance(record.get('generation'),int) or record['generation']<1 or not leaf.startswith(str(record['generation'])+'.'): raise ValueError('Invalid accepted record')
    artifact=Path(record.get('artifact_path','')).resolve();key=record.get('cache_key','')
    if artifact.parent!=cache_root or not re.fullmatch(re.escape(key)+r'\.[a-f0-9]{32}\.json',artifact.name): raise ValueError('Accepted artifact path mismatch')
    cache._safe_file(artifact,inputs)
    if artifact.stat().st_size>cache.MAX_ENTRY_BYTES or cache._hash(artifact)!=record.get('artifact_sha256'): raise ValueError('Accepted artifact changed')
    envelope=json.loads(artifact.read_bytes())
    if envelope.get('schema')!='un.sc-action-cache-entry.v1' or envelope.get('version')!=cache.VERSION or envelope.get('cache_key')!=key or key!=hashlib.sha256(cache._bytes(record.get('cache_identity'))).hexdigest() or envelope.get('identity')!=record.get('cache_identity') or envelope.get('report_sha256')!=record.get('report_sha256') or envelope.get('report_sha256')!=hashlib.sha256(cache._bytes(envelope.get('report'))).hexdigest(): raise ValueError('Accepted artifact proof mismatch')
    cache._validate_report(envelope['report'],record['cache_identity'])
    return record


def _validate_result(result,identity,cache_root,inputs):
    key=hashlib.sha256(cache._bytes(identity)).hexdigest()
    if result.get('cache_key')!=key: raise ValueError('Cache callback identity mismatch')
    artifact=Path(result.get('artifact_path','')).resolve()
    if artifact.parent!=cache_root or not re.fullmatch(re.escape(key)+r'\.[a-f0-9]{32}\.json',artifact.name): raise ValueError('Cache callback artifact path mismatch')
    cache._safe_file(artifact,inputs)
    if artifact.stat().st_size>cache.MAX_ENTRY_BYTES: raise ValueError('Cache callback artifact exceeds bound')
    raw=artifact.read_bytes();envelope=json.loads(raw);report=result.get('report')
    report_sha=hashlib.sha256(cache._bytes(report)).hexdigest()
    if envelope.get('schema')!='un.sc-action-cache-entry.v1' or envelope.get('version')!=cache.VERSION or envelope.get('cache_key')!=key or envelope.get('identity')!=identity or envelope.get('report')!=report or envelope.get('report_sha256')!=report_sha: raise ValueError('Cache callback artifact proof mismatch')
    cache._validate_report(report,identity)
    return envelope,hashlib.sha256(raw).hexdigest()


def _health(root,inputs,value,reserve,margin):
    """Health is advisory; an accepted pointer remains authoritative."""
    value={**value,'health_persisted':True}
    try:
        for p in (root,*root.parents):
            if p.is_symlink() or getattr(p,'is_junction',lambda:False)(): raise ValueError('Refresh health path traverses an alias')
        cache._safe_file(root/'refresh-root.json',inputs)
        if json.loads((root/'refresh-root.json').read_bytes())!=MARKER: raise ValueError('Refresh health ownership changed')
        cache._safe_file(root/'health.json',inputs)
        persisted=dict(value)
        if persisted.get('checkpoint'):
            persisted['checkpoint']={k:persisted['checkpoint'][k] for k in ('generation','cache_key','artifact_sha256')}
        data=cache._bytes(persisted);cache._space(root,len(data),reserve,margin)
        _atomic(root/'health.json',data)
    except (OSError,ValueError): value['health_persisted']=False
    return value


def refresh_selected_actions(collection_file,ddl_database,cache_dir,state_dir,*,ddl_raw_csv,expected_ddl_source_sha256,review_file=None,source_watermark=None,force_refresh=False,min_free_bytes=200*1024**2,write_margin_bytes=5*1024**2):
    if source_watermark is not None:
        try: valid=isinstance(source_watermark,str) and dt.date.fromisoformat(source_watermark).isoformat()==source_watermark
        except ValueError: valid=False
        if not valid: raise ValueError('Source watermark must be an ISO calendar date or null')
    if min_free_bytes<200*1024**2 or write_margin_bytes<0: raise ValueError('Private refresh reserve must remain at least 200 MiB')
    args=dict(ddl_raw_csv=ddl_raw_csv,expected_ddl_source_sha256=expected_ddl_source_sha256,review_file=review_file)
    # Unsafe paths/ownership/corrupt accepted state are configuration failures,
    # rejected before any advisory health or accepted-state write.
    configuration=_configuration_identity(collection_file,ddl_database,ddl_raw_csv,review_file)
    cache_root,_=cache._safe_root(cache_dir,configuration)
    root,inputs=_safe_state(state_dir,cache_root,configuration)
    old=_read_checkpoint(root,cache_root,inputs)
    workflow_sha=cache._hash(__file__)
    base={'schema':'un.sc-action-refresh-health.v1','version':VERSION,'checkpoint':old,'cache_status':None}
    try:
        cache._space(root,4096,min_free_bytes,write_margin_bytes)
        root.mkdir(parents=True,exist_ok=True)
        if not (root/'refresh-root.json').exists(): _atomic(root/'refresh-root.json',cache._bytes(MARKER))
        identity=cache._identity(collection_file,ddl_database,**args)
        result=cached_crosswalk(collection_file,ddl_database,cache_dir,**args,force_refresh=force_refresh,min_free_bytes=min_free_bytes,write_margin_bytes=write_margin_bytes)
        if cache._identity(collection_file,ddl_database,**args)!=identity or cache._hash(__file__)!=workflow_sha: raise ValueError('Private refresh inputs changed')
        envelope,artifact_sha=_validate_result(result,identity,cache_root,inputs)
        if old and old['cache_key']==result['cache_key'] and old.get('source_watermark')==source_watermark and old.get('workflow_sha256')==workflow_sha and not force_refresh:
            return _health(root,inputs,{**base,'status':'unchanged','cache_status':result['cache_status']},min_free_bytes,write_margin_bytes)
        dates=[e['date'] for e in result['report']['event_selection']['events']]
        record={'schema':'un.sc-action-refresh-checkpoint.v1','version':VERSION,'generation':old['generation']+1 if old else 1,
                'acceptance':'accepted_private_unbound','cache_key':result['cache_key'],'artifact_path':str(Path(result['artifact_path']).resolve()),
                'artifact_sha256':artifact_sha,'report_sha256':envelope['report_sha256'],'cache_identity':identity,
                'workflow_sha256':workflow_sha,'source_watermark':source_watermark,'source_watermark_scope':'caller_declared_snapshot_date_not_verified_freshness',
                'selection_summary':result['report']['event_selection']['summary'],'crosswalk_summary':result['report']['summary'],
                'requested_window':identity['window'],'observed_min':min(dates) if dates else None,'observed_max':max(dates) if dates else None,
                'observed_date_scope':'selected_voting_actions_only_not_archive_completeness'}
        data=cache._bytes(record);leaf=str(record['generation'])+'.'+uuid.uuid4().hex+'.json'
        pointer=cache._bytes({'schema':'un.sc-action-refresh-pointer.v1','record':leaf,'record_sha256':hashlib.sha256(data).hexdigest()})
        cache._space(root,len(data)+len(pointer),min_free_bytes,write_margin_bytes)
        _safe_state(root,cache_root,identity);_atomic(root/leaf,data)
        if cache._identity(collection_file,ddl_database,**args)!=identity or cache._hash(__file__)!=workflow_sha or cache._hash(result['artifact_path'])!=artifact_sha: raise ValueError('Private refresh inputs or artifact changed before acceptance')
        _safe_state(root,cache_root,identity);_atomic(root/'checkpoint.json',pointer)
    except (OSError,ValueError,KeyError,TypeError,RuntimeError) as error:
        code='insufficient_space' if isinstance(error,OSError) and 'space' in str(error).lower() else 'input_validation' if isinstance(error,(ValueError,KeyError,TypeError)) else 'cache_refresh_failed'
        # Do not persist exception messages, source paths, or voting records in
        # failure diagnostics. The prior immutable accepted record is retained.
        return _health(root,inputs,{**base,'status':'failed','failure_code':code},min_free_bytes,write_margin_bytes)
    return _health(root,inputs,{**base,'status':'accepted','checkpoint':record,'cache_status':result['cache_status']},min_free_bytes,write_margin_bytes)
