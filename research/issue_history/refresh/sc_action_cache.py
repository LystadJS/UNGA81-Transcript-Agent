"""Private, content-pinned cache of source-preserving SC action selections."""
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import tempfile
import uuid
from ..ingest.sc_crosswalk import crosswalk_files, _source_hash
from ..ingest.sc_primary_review import load_review

VERSION = 'sc-action-cache-1'
MARKER = 'un.sc-action-cache-root.v1'
MAX_ENTRY_BYTES = 256_000_000


class _UnsafeCachePath(ValueError):
    pass


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def _hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda:stream.read(1024*1024),b''): h.update(part)
    return h.hexdigest()


def _dependency_paths():
    folder=Path(__file__).resolve().parents[1]/'ingest'
    result={name:folder/name for name in ('sc_crosswalk.py','sc_primary_review.py','sc_event_selection.py','sc_drafts.py','un_sc_csv.py','adapters.py','countries.py')}
    result['country_registry']=folder.parents[2]/'un/config/countries.csv'
    result['sc_action_cache.py']=Path(__file__).resolve()
    return result


def _quiescent(database):
    for suffix in ('-wal','-journal','-shm'):
        if Path(str(database)+suffix).exists():
            raise ValueError('SQLite sidecar exists; close writers and checkpoint before caching')


def _validate_report(report,identity):
    provenance=report.get('input_provenance',{})
    selection=report.get('event_selection',{})
    deps=identity['dependencies']
    expected={'collection_sha256':identity['inputs']['collection']['sha256'],
              'ddl_database_sha256':identity['inputs']['ddl_database']['sha256'],
              'ddl_original_source_sha256':identity['expected_ddl_source_sha256'],
              'raw_reference_enrichment':True,'algorithm_sha256':deps['sc_crosswalk.py']['sha256']}
    if any(provenance.get(k)!=v for k,v in expected.items()): raise ValueError('Cached report input provenance mismatch')
    required={'sc_drafts.py','adapters.py','countries.py','un_sc_csv.py','country_registry','sc_event_selection.py'}
    if identity['proofs']: required.add('sc_primary_review.py')
    if any(provenance.get('dependency_sha256',{}).get(name)!=deps[name]['sha256'] for name in required): raise ValueError('Cached report dependency mismatch')
    if provenance.get('review_input_sha256',{})!=identity['proofs']: raise ValueError('Cached report proof identity mismatch')
    if report.get('schema')!='un.sc-event-crosswalk.v1' or report.get('version')!=identity['versions']['crosswalk'] or selection.get('schema')!='un.sc-event-selection.v1' or selection.get('version')!=identity['versions']['selection']: raise ValueError('Cached report version mismatch')
    fingerprints=report.get('input_fingerprints',{})
    if set(fingerprints)!={'collection_sha256','ddl_votes_sha256'} or any(not isinstance(v,str) or not re.fullmatch('[a-f0-9]{64}',v) for v in fingerprints.values()) or selection.get('input_fingerprints')!=fingerprints or selection.get('input_provenance')!=provenance: raise ValueError('Cached selection input fingerprints mismatch')


def _identity(collection_file,ddl_database,*,ddl_raw_csv,expected_ddl_source_sha256,review_file=None):
    from ..ingest import sc_crosswalk,sc_event_selection,sc_primary_review,sc_drafts
    paths={'collection':Path(collection_file).resolve(),'ddl_database':Path(ddl_database).resolve(),'ddl_raw_csv':Path(ddl_raw_csv).resolve()}
    _quiescent(paths['ddl_database'])
    if paths['collection'].stat().st_size>60_000_000: raise ValueError('Collection exceeds cache bound')
    hashes={name:_hash(path) for name,path in paths.items()}
    decompressed=_source_hash(paths['ddl_raw_csv'])
    if decompressed!=expected_ddl_source_sha256: raise ValueError('Raw DDL source identity mismatch')
    collection=json.loads(paths['collection'].read_bytes())
    proof={}
    if review_file is not None:
        provenance={'collection_sha256':hashes['collection'],'ddl_database_sha256':hashes['ddl_database'],'ddl_original_source_sha256':expected_ddl_source_sha256}
        _,proof=load_review(review_file,provenance)
    dependencies={name:{'path':str(Path(path).resolve()),'sha256':_hash(path)} for name,path in sorted(_dependency_paths().items())}
    return {'schema':'un.sc-action-cache-identity.v1','version':VERSION,
            'inputs':{name:{'path':str(path),'sha256':hashes[name]} for name,path in sorted(paths.items())},
            'proofs':dict(sorted(proof.items())),'dependencies':dependencies,
            'ddl_original_source_sha256':decompressed,'expected_ddl_source_sha256':expected_ddl_source_sha256,
            'window':collection.get('window'),'collection_schema':collection.get('schema'),
            'flags':{'select_events':True,'raw_reference_enrichment':True},
            'versions':{'crosswalk':sc_crosswalk.VERSION,'selection':sc_event_selection.VERSION,
                        'primary_review':sc_primary_review.VERSION,'sc_drafts':sc_drafts.VERSION,'cache':VERSION}}


def _safe_root(cache_dir,identity):
    raw=Path(cache_dir).absolute()
    for p in (raw,*raw.parents):
        if p.is_symlink() or getattr(p,'is_junction',lambda:False)(): raise ValueError('Cache path must not traverse symlinks or junctions')
    root=raw.resolve()
    for p in (root,*root.parents):
        if (p/'.git').exists(): raise ValueError('Private cache must be outside repository trees')
    inputs=[Path(v['path']).resolve() for v in identity['inputs'].values()]+[Path(p).resolve() for p in identity['proofs']]+[Path(v['path']).resolve() for v in identity['dependencies'].values()]
    if any(p==root or p.is_relative_to(root) for p in inputs): raise ValueError('Cache must not contain any input or evidence file')
    marker=root/'cache-root.json'
    if root.exists():
        if not root.is_dir(): raise ValueError('Cache root must be a directory')
        contents=list(root.iterdir())
        if contents:
            if marker.is_symlink() or not marker.is_file() or marker.stat().st_nlink!=1 or marker.stat().st_size>1024: raise ValueError('Nonempty directory is not an owned cache')
            try: valid=json.loads(marker.read_bytes())=={'schema':MARKER,'version':VERSION}
            except (ValueError,UnicodeError): valid=False
            if not valid: raise ValueError('Cache ownership marker mismatch')
    return root,inputs


def _safe_file(path,inputs):
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.stat().st_nlink!=1: raise _UnsafeCachePath('Cache file alias is unsafe')
        if any(p.exists() and path.samefile(p) for p in inputs): raise _UnsafeCachePath('Cache file aliases an input')


def _space(root,needed,reserve,margin):
    ancestor=root
    while not ancestor.exists(): ancestor=ancestor.parent
    if shutil.disk_usage(ancestor).free < reserve+margin+needed: raise OSError('Insufficient free space for cache reserve and atomic write')


def _atomic(path,data):
    fd,name=tempfile.mkstemp(prefix='.cache-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream: stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)


def cached_crosswalk(collection_file,ddl_database,cache_dir,*,ddl_raw_csv,expected_ddl_source_sha256,review_file=None,min_free_bytes=200*1024**2,write_margin_bytes=5*1024**2,force_refresh=False):
    if min_free_bytes<200*1024**2 or write_margin_bytes<0: raise ValueError('Cache reserve cannot be reduced below 200 MiB')
    args=dict(ddl_raw_csv=ddl_raw_csv,expected_ddl_source_sha256=expected_ddl_source_sha256,review_file=review_file)
    identity=_identity(collection_file,ddl_database,**args)
    key=hashlib.sha256(_bytes(identity)).hexdigest();root,inputs=_safe_root(cache_dir,identity)
    index=root/(key+'.index.json');_safe_file(index,inputs)
    corrupt=None;valid_existing=False
    if index.exists():
        if index.stat().st_size>1_000_000: raise ValueError('Cache index exceeds bound')
        corrupt=index.read_bytes()
        try:
            pointer=json.loads(corrupt);leaf=pointer.get('entry','')
            if pointer.get('schema')!='un.sc-action-cache-index.v1' or pointer.get('cache_key')!=key or not isinstance(leaf,str) or not re.fullmatch(re.escape(key)+r'\.[a-f0-9]{32}\.json',leaf): raise ValueError('Invalid cache index')
            entry=root/leaf;_safe_file(entry,inputs)
            if entry.stat().st_size>MAX_ENTRY_BYTES: raise ValueError('Cache entry exceeds bound')
            raw=entry.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=pointer.get('entry_sha256'): raise ValueError('Cache entry hash changed')
            envelope=json.loads(raw);report=envelope['report']
            if envelope.get('schema')!='un.sc-action-cache-entry.v1' or envelope.get('version')!=VERSION or envelope.get('cache_key')!=key or envelope.get('identity')!=identity or envelope.get('report_sha256')!=hashlib.sha256(_bytes(report)).hexdigest() or report.get('schema')!='un.sc-event-crosswalk.v1' or report.get('event_selection',{}).get('schema')!='un.sc-event-selection.v1': raise ValueError('Cache envelope or report mismatch')
            _validate_report(report,identity)
        except _UnsafeCachePath: raise
        except (ValueError,KeyError,TypeError,AttributeError,FileNotFoundError,UnicodeError): pass
        else:
            if _identity(collection_file,ddl_database,**args)!=identity: raise ValueError('Cache inputs changed during warm validation')
            _safe_root(root,identity)
            valid_existing=True;corrupt=None
            if not force_refresh:
                return {'cache_status':'hit','cache_key':key,'artifact_path':str(entry),'report':report,'refresh_reason':None}
    # The builder writes a temporary report before its exact size is known.
    # Reserve its full permitted bound as well as the permanent free-space floor.
    _space(root,MAX_ENTRY_BYTES,min_free_bytes,write_margin_bytes)
    root.mkdir(parents=True,exist_ok=True)
    marker=root/'cache-root.json'
    if not marker.exists(): _atomic(marker,_bytes({'schema':MARKER,'version':VERSION}))
    work=root/('.building-'+uuid.uuid4().hex+'.json')
    try: report=crosswalk_files(collection_file,ddl_database,work,**args,select_events=True)
    finally:
        if work.exists(): work.unlink()
    _validate_report(report,identity)
    if _identity(collection_file,ddl_database,**args)!=identity: raise ValueError('Cache inputs changed during refresh')
    envelope={'schema':'un.sc-action-cache-entry.v1','version':VERSION,'cache_key':key,'identity':identity,'report_sha256':hashlib.sha256(_bytes(report)).hexdigest(),'report':report}
    raw=_bytes(envelope)
    if len(raw)>MAX_ENTRY_BYTES: raise ValueError('Cache artifact exceeds bound')
    leaf=key+'.'+uuid.uuid4().hex+'.json';entry=root/leaf
    pointer=_bytes({'schema':'un.sc-action-cache-index.v1','cache_key':key,'entry':leaf,'entry_sha256':hashlib.sha256(raw).hexdigest()})
    _space(root,len(raw)+len(pointer)+len(corrupt or b''),min_free_bytes,write_margin_bytes)
    _safe_root(root,identity)
    _safe_file(index,inputs)
    if corrupt is not None: _atomic(root/(key+'.corrupt-index.'+uuid.uuid4().hex+'.json'),corrupt)
    _atomic(entry,raw)
    if _identity(collection_file,ddl_database,**args)!=identity: raise ValueError('Cache inputs changed before index publication')
    _safe_root(root,identity);_safe_file(index,inputs)
    _atomic(index,pointer)
    return {'cache_status':'rebuilt_corrupt' if corrupt is not None else 'refreshed' if valid_existing else 'built','cache_key':key,'artifact_path':str(entry),'report':report,'refresh_reason':'corrupt_cache' if corrupt is not None else 'forced_refresh' if valid_existing else 'new_identity'}
