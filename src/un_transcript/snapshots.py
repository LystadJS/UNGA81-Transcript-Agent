"""Verified immutable checkpoints and optimistic, two-phase remote publication.

Repository usedStorage includes repository history, not other repositories owned
by the account. Defaults reserve 80 GB private + 10 GB public; maintainers must
check other account usage separately. No paid capacity is requested here.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import os
import re
import shutil
import sqlite3
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_FILES = 100_000
DISK_RESERVE_BYTES = 1024 ** 3
HEX = re.compile(r'[a-f0-9]{64}')
IDENTITY = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}')
PUBLIC_MEETING_FIELDS = {'meeting_id','date','title','body','source_url','status','segments','positions','issues'}
PUBLIC_POSITION_FIELDS = {'country','capacity','issue_id','issue_label','proposition','label','stance','status','confidence','model_version','source_url','issue_version','source_revision_ids','source_segment_ids','evidence_ids'}
PUBLIC_REFERENCE_FIELDS = {'source_revision_ids','source_segment_ids','evidence_ids'}
PUBLIC_ISSUE_FIELDS = {'id','label','kind'}
PUBLIC_CSV_COLUMNS = ['meeting_id','date','title','body','source_url','status','segments']
PUBLIC_MANIFEST_FIELDS = {'schema','snapshot_id','generated_at','status','model_status','csv_text_safety','coverage','partitions','downloads'}
PUBLIC_COVERAGE_FIELDS = {'meetings','stored_meetings','segments','statuses','latest_run_status'}


class RemoteEntryMissing(FileNotFoundError):
    """A successful remote path metadata query established that no entry exists."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def _size(value):
    return value.stat().st_size if isinstance(value, Path) else len(value)


def _hash(value):
    return file_sha(value) if isinstance(value, Path) else sha(value)


def encode(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n').encode()


def safe_path(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value or any(ord(c) < 32 for c in value):
        raise ValueError('Unsafe artifact path')
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ('', '.', '..') for p in value.split('/')):
        raise ValueError('Unsafe artifact path')
    return value


def _identity(value):
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        raise ValueError('Invalid snapshot ID')
    return value


def _integer(value, maximum=MAX_FILE_BYTES):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError('Invalid artifact byte/count bound')
    return value


def _descriptor(item):
    if not isinstance(item, dict) or set(item) - {'path','sha256','bytes','rows','name'}:
        raise ValueError('Invalid artifact descriptor')
    safe_path(item.get('path'))
    _integer(item.get('bytes'))
    if not isinstance(item.get('sha256'), str) or not HEX.fullmatch(item['sha256']):
        raise ValueError('Invalid artifact checksum')
    if 'rows' in item:
        _integer(item['rows'], 100_000_000)
    if 'name' in item and item['name'] != PurePosixPath(item['path']).name:
        raise ValueError('Unexpected artifact display name')


def _manifest(value):
    if not isinstance(value, dict) or value.get('schema') != 'un.snapshot.v1':
        raise ValueError('Unsupported snapshot schema')
    _identity(value.get('snapshot_id'))
    files = value.get('files')
    if not isinstance(files, list) or not 2 <= len(files) <= MAX_FILES:
        raise ValueError('Invalid snapshot file count')
    seen = set()
    for item in files:
        _descriptor(item)
        if item['path'] in seen or item['path'] == 'snapshot.json':
            raise ValueError('Duplicate or reserved snapshot artifact')
        seen.add(item['path'])
    if not {'warehouse.sqlite3','state.json'} <= seen:
        raise ValueError('Snapshot has no database or cursor')
    return value


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        f.write(encode(value)); f.flush(); os.fsync(f.fileno()); temporary = f.name
    try:
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _originals(db):
    return db.execute('SELECT raw_sha256,byte_count FROM source_revisions UNION SELECT raw_sha256,byte_count FROM inventory_receipts')


def verify_snapshot(directory):
    directory = Path(directory)
    manifest_path = directory / 'snapshot.json'
    if manifest_path.is_symlink() or manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError('Unsafe or oversized snapshot manifest')
    manifest = _manifest(json.loads(manifest_path.read_bytes()))
    seen = set()
    for item in manifest['files']:
        name = item['path']; seen.add(name)
        file = directory / name
        if file.is_symlink() or not file.resolve().is_relative_to(directory.resolve()):
            raise ValueError('Unsafe snapshot artifact')
        if file.stat().st_size != item['bytes'] or file_sha(file) != item['sha256']:
            raise ValueError('Snapshot integrity failed: ' + name)
    with sqlite3.connect((directory / 'warehouse.sqlite3').resolve().as_uri() + '?mode=ro', uri=True) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or db.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('Snapshot database integrity failed')
        schema = db.execute("SELECT value FROM warehouse_meta WHERE key='schema'").fetchone()
        if not schema or schema[0] != 'un.transcript-warehouse.v1':
            raise ValueError('Unexpected database schema')
        for raw_hash, byte_count in _originals(db):
            if not isinstance(raw_hash, str) or not HEX.fullmatch(raw_hash):
                raise ValueError('Invalid original source identity')
            name = 'raw/' + raw_hash + '.json'; file = directory / name
            if name not in seen or file.stat().st_size != byte_count or file_sha(file) != raw_hash:
                raise ValueError('Missing or altered original source/inventory')
    return manifest


def seal_snapshot(warehouse, directory, state, snapshot_id, generated_at):
    """Back up SQLite and hardlink immutable CAS blobs; originals are never edited."""
    _identity(snapshot_id)
    directory = Path(directory)
    if (directory / 'snapshot.json').exists():
        raise FileExistsError('Snapshot is already sealed')
    with sqlite3.connect(directory / 'warehouse.sqlite3') as backup:
        warehouse.db.backup(backup)
    atomic_json(directory / 'state.json', state)
    raw_dir = directory / 'raw'
    if raw_dir.is_symlink():
        raise ValueError('Unsafe raw artifact directory')
    raw_dir.mkdir(exist_ok=True)
    for raw_hash, byte_count in _originals(warehouse.db):
        if not isinstance(raw_hash, str) or not HEX.fullmatch(raw_hash):
            raise ValueError('Invalid original source identity')
        original = warehouse.raw_directory / (raw_hash + '.json')
        if original.is_symlink() or original.stat().st_size != byte_count or file_sha(original) != raw_hash:
            raise ValueError('Original artifact integrity failed')
        target = raw_dir / original.name
        if not target.exists():
            # Same filesystem is the ordinary case. A portable cross-filesystem
            # fallback copies one file at a time, never materializing all bytes.
            try:
                os.link(original, target)
            except OSError:
                shutil.copyfile(original, target)
    files = []
    for file in sorted(directory.rglob('*')):
        if file.is_symlink():
            raise ValueError('Symlink in snapshot')
        if file.is_file():
            _integer(file.stat().st_size)
            files.append({'path': file.relative_to(directory).as_posix(), 'sha256': file_sha(file), 'bytes':file.stat().st_size})
    manifest = _manifest({'schema':'un.snapshot.v1','snapshot_id':snapshot_id,'generated_at':generated_at,'files':files})
    if len(encode(manifest)) > MAX_MANIFEST_BYTES:
        raise ValueError('Snapshot manifest exceeds size limit')
    atomic_json(directory / 'snapshot.json', manifest)
    verify_snapshot(directory)
    return manifest


def _keys(value, allowed):
    if not isinstance(value, dict) or set(value) - allowed:
        raise ValueError('Public artifact contains fields outside the publication allowlist')


def _scalar(value, *, nullable=True, limit=8192):
    if (value is None and nullable) or (isinstance(value,str) and len(value) <= limit):
        return
    raise ValueError('Invalid public scalar value')


def _source_url(value):
    if value is None:
        return
    if not isinstance(value,str):
        raise ValueError('Invalid public source URL')
    parts = urlsplit(value)
    if parts.scheme != 'https' or parts.netloc != 'transcripts.un.org' or parts.query or parts.fragment or not parts.path.startswith('/en/'):
        raise ValueError('Invalid public source URL')


def _public_payload(file, path):
    """Independently enforce the exporter field contract before remote publication."""
    if re.fullmatch(r'partitions/meetings-\d{5}.json', path):
        payload = json.loads(file.read_bytes()); _keys(payload, {'meetings'})
        if not isinstance(payload.get('meetings'),list) or len(payload['meetings']) > 500:
            raise ValueError('Invalid public partition')
        for meeting in payload['meetings']:
            _keys(meeting, PUBLIC_MEETING_FIELDS)
            if set(meeting) != PUBLIC_MEETING_FIELDS:
                raise ValueError('Missing public meeting fields')
            for key in PUBLIC_MEETING_FIELDS - {'segments','positions','issues'}:
                _scalar(meeting[key])
            _integer(meeting['segments'],100_000_000)
            _source_url(meeting.get('source_url'))
            if not isinstance(meeting.get('positions'),list) or not isinstance(meeting.get('issues'),list):
                raise ValueError('Invalid public evidence lists')
            for position in meeting['positions']:
                _keys(position, PUBLIC_POSITION_FIELDS)
                if set(position) != PUBLIC_POSITION_FIELDS:
                    raise ValueError('Missing public position fields')
                for key in PUBLIC_POSITION_FIELDS - {'confidence'} - PUBLIC_REFERENCE_FIELDS:
                    _scalar(position[key])
                for key in PUBLIC_REFERENCE_FIELDS:
                    references = position[key]
                    if not isinstance(references,list) or len(references) > 10000 or any(not isinstance(ref,str) or not re.fullmatch(r'[A-Za-z0-9._:/#-]{1,256}',ref) for ref in references):
                        raise ValueError('Invalid public source reference IDs')
                confidence = position['confidence']
                if confidence is not None and (type(confidence) not in (int,float) or not math.isfinite(confidence) or not 0 <= confidence <= 1):
                    raise ValueError('Invalid public confidence')
                _source_url(position.get('source_url'))
            for issue in meeting['issues']:
                _keys(issue, PUBLIC_ISSUE_FIELDS)
                if set(issue) != PUBLIC_ISSUE_FIELDS:
                    raise ValueError('Missing public issue fields')
                for value in issue.values():
                    _scalar(value,nullable=False)
    elif path == 'meetings.csv':
        with file.open(encoding='utf-8', newline='') as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != PUBLIC_CSV_COLUMNS:
                raise ValueError('Public CSV contains columns outside the publication allowlist')
            for row in reader:
                if None in row or any(v is None for v in row.values()):
                    raise ValueError('Invalid public CSV row')
                _source_url(row['source_url'] or None)
    else:
        raise ValueError('Public artifact is outside the publication allowlist')


class HFStorage:
    """Per-repository storage budgets; account-wide remaining quota is external."""
    def __init__(self, repo_id, *, token=None, private=True, budget_bytes=None, api=None, downloader=None):
        if not re.fullmatch(r'[\w.-]+/[\w.-]+', repo_id or ''):
            raise ValueError('Expected an owner/dataset repository ID')
        budget_bytes = budget_bytes if budget_bytes is not None else (80_000_000_000 if private else 10_000_000_000)
        if type(budget_bytes) is not int or budget_bytes <= 0:
            raise ValueError('Invalid repository storage budget')
        self.repo_id, self.private, self.budget_bytes = repo_id, private, budget_bytes
        if api is None:
            from huggingface_hub import HfApi, hf_hub_download
            token = token or os.environ.get('HF_TOKEN')
            if not token:
                raise ValueError('HF_TOKEN must be set in the environment, never in source configuration')
            api = HfApi(token=token)
            def downloader(path, revision):
                # Return a file, not all its bytes. The metadata bound is checked
                # before the hub download and the local file is rechecked after.
                return Path(hf_hub_download(repo_id=repo_id, filename=path, repo_type='dataset', revision=revision, token=token))
        self.api, self.downloader = api, downloader

    def info(self):
        info = self.api.repo_info(self.repo_id, repo_type='dataset', expand=['private','sha','usedStorage'])
        if getattr(info, 'private', None) is not self.private:
            raise ValueError('Dataset visibility does not match its configured role')
        revision = getattr(info, 'sha', None)
        if not isinstance(revision, str) or not re.fullmatch(r'[0-9a-fA-F]{40}', revision):
            raise ValueError(
                'Dataset has no valid immutable commit SHA; initialize a new dataset with a '
                'README or .gitattributes commit, then retry. If it is already initialized, '
                'verify repository access and metadata availability. Refusing unpinned reads '
                'or a write without optimistic concurrency protection.'
            )
        used = getattr(info, 'used_storage', getattr(info, 'usedStorage', None))
        if type(used) is not int or used < 0:
            raise ValueError('Repository history storage usage unavailable; refusing an unbudgeted write')
        return info, used

    def _entries(self, paths, revision):
        return self.api.get_paths_info(self.repo_id, paths, repo_type='dataset', revision=revision)

    def _download(self, path, revision, limit=MAX_FILE_BYTES):
        path = safe_path(path)
        entries = self._entries([path], revision)
        if not entries:
            raise RemoteEntryMissing(path)
        if len(entries) != 1 or type(getattr(entries[0], 'size', None)) is not int or not 0 <= entries[0].size <= limit:
            raise ValueError('Remote artifact exceeds download size bound')
        value = self.downloader(path, revision)
        if not isinstance(value, (bytes, Path)) or _size(value) != entries[0].size or _size(value) > limit:
            raise ValueError('Downloaded artifact size differs from remote metadata')
        return value

    def read(self, path, revision, limit=MAX_FILE_BYTES):
        value = self._download(path, revision, limit)
        return value.read_bytes() if isinstance(value, Path) else value

    def _commit(self, files, parent, message):
        from huggingface_hub import CommitOperationAdd
        operations = [CommitOperationAdd(path_in_repo=safe_path(path), path_or_fileobj=data) for path, data in files.items()]
        result = self.api.create_commit(self.repo_id, repo_type='dataset', operations=operations, parent_commit=parent, commit_message=message)
        return result.oid

    def _immutable_prefix(self, prefix, revision):
        # Any existing prefix, even a failed staging attempt, is immutable. A new
        # run gets a fresh identity instead of overwriting partial publication.
        if self._entries([prefix.rstrip('/')], revision):
            raise FileExistsError('Snapshot prefix already exists; use a new snapshot ID')

    def _verify_remote(self, files, revision):
        for path, value in files.items():
            actual = self._download(path, revision)
            if _size(actual) != _size(value) or _hash(actual) != _hash(value):
                raise ValueError('Remote verification failed; latest pointer unchanged')

    def publish(self, directory):
        if not self.private:
            raise ValueError('Canonical snapshots require private storage')
        directory = Path(directory)
        manifest = verify_snapshot(directory)
        info, used = self.info()
        snapshot_id = manifest['snapshot_id']; prefix = 'snapshots/' + snapshot_id + '/'
        self._immutable_prefix(prefix, info.sha)
        files = {}
        for item in manifest['files']:
            remote = item['path'] if item['path'].startswith('raw/') else prefix + item['path']
            if remote.startswith('raw/') and self._entries([remote], info.sha):
                existing = self._download(remote, info.sha)
                if _size(existing) != item['bytes'] or _hash(existing) != item['sha256']:
                    raise ValueError('Existing remote raw artifact is corrupt')
                continue
            # SDK streams from local files. Existing raw blobs were checked
            # before this point, so the archive is never loaded into a byte dict.
            files[remote] = directory / item['path']
        manifest_file = directory / 'snapshot.json'
        files[prefix + 'snapshot.json'] = manifest_file
        if used + sum(_size(value) for value in files.values()) + 1_000_000 > self.budget_bytes:
            raise ValueError('Free storage budget would be exceeded; previous snapshot retained')
        staged = self._commit(files, info.sha, 'Stage immutable transcript snapshot ' + snapshot_id)
        self._verify_remote(files, staged)
        pointer = {'schema':'un.snapshot-pointer.v1','snapshot_id':snapshot_id,'manifest_path':prefix+'snapshot.json','manifest_sha256':file_sha(manifest_file),'revision':staged}
        self._commit({'latest.json':encode(pointer)}, staged, 'Activate verified transcript snapshot ' + snapshot_id)
        return pointer

    def restore(self, workspace):
        """Install one verified data/ subtree atomically; never overwrite local work."""
        if not self.private:
            raise ValueError('Only private snapshots may restore a warehouse')
        workspace = Path(workspace)
        if (workspace / 'data').exists() or (workspace / 'data').is_symlink():
            raise FileExistsError('Restore requires an absent data directory; preserve existing local data first')
        info, _ = self.info()
        try:
            raw_pointer = self.read('latest.json', info.sha, 1024 * 1024)
        except RemoteEntryMissing:
            return None
        pointer = json.loads(raw_pointer)
        if not isinstance(pointer, dict) or pointer.get('schema') != 'un.snapshot-pointer.v1':
            raise ValueError('Invalid remote pointer')
        snapshot_id = _identity(pointer.get('snapshot_id'))
        prefix = 'snapshots/' + snapshot_id + '/'
        if pointer.get('manifest_path') != prefix + 'snapshot.json' or not isinstance(pointer.get('revision'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',pointer['revision']) or not isinstance(pointer.get('manifest_sha256'),str) or not HEX.fullmatch(pointer['manifest_sha256']):
            raise ValueError('Invalid remote pointer identity/path')
        revision = pointer['revision']
        raw_manifest = self.read(pointer['manifest_path'], revision, MAX_MANIFEST_BYTES)
        if sha(raw_manifest) != pointer['manifest_sha256']:
            raise ValueError('Remote manifest hash mismatch')
        manifest = _manifest(json.loads(raw_manifest))
        if manifest['snapshot_id'] != snapshot_id:
            raise ValueError('Snapshot identity mismatch')
        total = sum(item['bytes'] for item in manifest['files'])
        if total > self.budget_bytes:
            raise ValueError('Remote snapshot exceeds restore budget')
        workspace.mkdir(parents=True, exist_ok=True)
        # Account for both hub download cache and restored files on one volume.
        if shutil.disk_usage(workspace).free < 2 * total + DISK_RESERVE_BYTES:
            raise ValueError('Insufficient disk reserve for verified restoration')
        with tempfile.TemporaryDirectory(prefix='.restore-', dir=workspace) as temporary:
            target = Path(temporary) / 'data'; target.mkdir()
            for item in manifest['files']:
                path = item['path']; remote = path if path.startswith('raw/') else prefix + path
                data = self._download(remote, revision, item['bytes'])
                if _size(data) != item['bytes'] or _hash(data) != item['sha256']:
                    raise ValueError('Remote artifact hash mismatch')
                file = target / path; file.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(data, Path):
                    shutil.copyfile(data, file)
                else:
                    file.write_bytes(data)
            # Empty archives still have a raw/ directory for the warehouse.
            (target / 'raw').mkdir(exist_ok=True)
            (target / 'snapshot.json').write_bytes(raw_manifest)
            verify_snapshot(target)
            atomic_json(target / 'restored.json', pointer)
            if (workspace / 'data').exists() or (workspace / 'data').is_symlink():
                raise FileExistsError('Local data appeared during restoration; refusing overwrite')
            os.replace(target, workspace / 'data')
        return pointer

    def publish_public(self, public_directory):
        if self.private:
            raise ValueError('Public reports require a separate public dataset')
        directory = Path(public_directory)
        manifest_file = directory / 'manifest.json'
        if manifest_file.is_symlink() or manifest_file.stat().st_size > MAX_MANIFEST_BYTES:
            raise ValueError('Unsafe public manifest')
        manifest = json.loads(manifest_file.read_bytes())
        _keys(manifest, PUBLIC_MANIFEST_FIELDS)
        if manifest.get('schema') != 'un.archive.v1':
            raise ValueError('Unsupported public archive')
        snapshot_id = _identity(manifest.get('snapshot_id')); prefix = 'snapshots/' + snapshot_id + '/'
        for key in PUBLIC_MANIFEST_FIELDS - {'coverage','partitions','downloads'}:
            _scalar(manifest.get(key))
        _keys(manifest.get('coverage'), PUBLIC_COVERAGE_FIELDS)
        for key in ('meetings','stored_meetings','segments'):
            _integer(manifest['coverage'].get(key),100_000_000)
        _scalar(manifest['coverage'].get('latest_run_status'))
        statuses = manifest['coverage'].get('statuses')
        if not isinstance(statuses,dict) or any(not isinstance(k,str) or type(v) is not int or v < 0 for k,v in statuses.items()):
            raise ValueError('Invalid public coverage counts')
        files, seen = {}, set()
        for group in ('partitions','downloads'):
            if not isinstance(manifest.get(group),list) or len(manifest[group]) > MAX_FILES:
                raise ValueError('Invalid public artifact list')
            for item in manifest[group]:
                _descriptor(item); path = item['path']
                if path in seen:
                    raise ValueError('Duplicate public artifact path')
                seen.add(path)
                file = directory / path
                if file.is_symlink() or not file.resolve().is_relative_to(directory.resolve()):
                    raise ValueError('Unsafe public artifact')
                if file.stat().st_size != item['bytes'] or file_sha(file) != item['sha256']:
                    raise ValueError('Public artifact integrity failed')
                _public_payload(file, path)
                files[prefix + path] = file
        # The immutable manifest keeps relative paths so it can be reopened at
        # snapshots/<id>/manifest.json. Only root latest.json needs prefixes.
        files[prefix + 'manifest.json'] = manifest_file
        latest = copy.deepcopy(manifest)
        for group in ('partitions','downloads'):
            for item in latest[group]:
                item['path'] = prefix + item['path']
        info, used = self.info()
        self._immutable_prefix(prefix, info.sha)
        if used + sum(_size(value) for value in files.values()) + len(encode(latest)) + 1_000_000 > self.budget_bytes:
            raise ValueError('Public free storage budget would be exceeded')
        staged = self._commit(files, info.sha, 'Stage public transcript report ' + snapshot_id)
        self._verify_remote(files, staged)
        self._commit({'latest.json':encode(latest)}, staged, 'Activate public transcript report ' + snapshot_id)
        return latest
