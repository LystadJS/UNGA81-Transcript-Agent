"""Dependency-free provenance and benchmark contracts."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

LABELS = ('strongly_oppose', 'oppose', 'neutral', 'support', 'strongly_support')
STATUSES = ('clear', 'not_discussed', 'no_expressed_position', 'conditional',
            'mixed', 'unclear', 'unresolved_attribution')
RESERVED_DATES = {'2026-10-05', '2026-10-06'}


def digest(value):
    data = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, ensure_ascii=False,
                                                             separators=(',', ':')).encode()
    return hashlib.sha256(data).hexdigest()


def identity(kind, *parts):
    return kind + '_' + digest(parts)[:24]


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    path = Path(path)
    if path.exists():
        raise ValueError('Refusing to overwrite an existing model or review artifact: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def check_registration(registration):
    """Metadata only: never use test labels to choose a split."""
    if registration.get('schema') != 'un.stance-registration.v1':
        raise ValueError('A versioned, prospectively frozen registration is required')
    datetime.fromisoformat(registration['registered_at'].replace('Z', '+00:00'))
    rows = registration.get('sources', [])
    if not rows:
        raise ValueError('No registered source sample')
    dates = {s: set() for s in ('train', 'calibration', 'test')}
    seen = {}
    for row in rows:
        split = row['split']
        if split not in dates or row['date'] in RESERVED_DATES:
            raise ValueError('Invalid split or reserved source date')
        datetime.strptime(row['date'], '%Y-%m-%d')
        dates[split].add(row['date'])
        for key in ('source_id', 'source_hash', 'meeting_id'):
            value = row.get(key)
            if not value:
                raise ValueError('Source identity is incomplete: ' + key)
            group = (key, value)
            if group in seen and seen[group] != split:
                raise ValueError('Source, hash or meeting leaks across splits')
            seen[group] = split
    if any(not d for d in dates.values()):
        raise ValueError('Training, calibration and untouched test source sets are required')
    if not (max(dates['train']) < min(dates['calibration']) and
            max(dates['calibration']) < min(dates['test'])):
        raise ValueError('Splits must be strictly forward in event time')
    return rows


def check_labels(bundle, registration, split):
    registered = check_registration(registration)
    if bundle.get('registration_sha256') != digest(registration):
        raise ValueError('Labels are not bound to this frozen registration')
    if bundle.get('owner_confirmed') is not True or not bundle.get('reviewer_id'):
        raise ValueError('Actual owner-confirmed labels are required; drafts cannot train or accept a model')
    reviewed = datetime.fromisoformat(bundle['reviewed_at'].replace('Z', '+00:00'))
    frozen = datetime.fromisoformat(registration['registered_at'].replace('Z', '+00:00'))
    if reviewed <= frozen:
        raise ValueError('Registration must predate review')
    source_set = {(r['source_id'], r['source_hash'], r['meeting_id'], r['date'])
                  for r in registered if r['split'] == split}
    segment_pins = {r['segment_id']: r['text_sha256'] for r in registered
                    if r['split'] == split and r.get('segment_id') and r.get('text_sha256')}
    rows = bundle.get('rows', [])
    if not rows:
        raise ValueError('Missing owner-reviewed rows')
    ids = set()
    for row in rows:
        if row.get('owner_confirmed') is not True or row.get('split') != split:
            raise ValueError('Every row must have actual owner confirmation and the requested split')
        if row.get('pair_id') in ids or not row.get('pair_id'):
            raise ValueError('Missing or duplicated proposition-passage identity')
        ids.add(row['pair_id'])
        if tuple(row.get(k) for k in ('source_id', 'source_hash', 'meeting_id', 'date')) not in source_set:
            raise ValueError('Label source identity is not registered')
        if row.get('status') not in STATUSES:
            raise ValueError('Unreviewed or invalid interpretability label')
        if row['status'] == 'clear' and row.get('label') not in LABELS:
            raise ValueError('Five-class stance label required for clear statements')
        if row['status'] != 'clear' and row.get('label') is not None:
            raise ValueError('Nonordinal statuses must not be relabeled as neutral')
        text = row.get('text', '')
        if not text or row.get('text_sha256') != digest(text.encode()):
            raise ValueError('Context text digest mismatch')
        if segment_pins.get(row.get('segment_id')) != row['text_sha256']:
            raise ValueError('Context text is not pinned by the prospective source registration')
        if not row.get('proposition') or not row.get('issue_id'):
            raise ValueError('A precise versioned proposition is required')
        if registration.get('propositions',{}).get(row['issue_id']) != row['proposition']:
            raise ValueError('Reviewed proposition differs from the prospective catalog definition')
        start, end = row.get('start'), row.get('end')
        if type(start) is not int or type(end) is not int or not 0 <= start < end:
            raise ValueError('Original source span required')
        a,b=row.get('focal_start',0),row.get('focal_end',len(text))
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(text):
            raise ValueError('Focal span must lie within the original supplied context')
    return rows


def verify_artifacts(directory, manifest):
    root = Path(directory).resolve()
    members = manifest.get('artifacts', {})
    if manifest.get('schema')!='un.stance-model.v1' or manifest.get('labels')!=list(LABELS) or manifest.get('statuses')!=list(STATUSES):
        raise ValueError('Model schema or class ordering mismatch')
    required={'model.onnx','config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json'}
    required.update(name for name in ('vocab.txt','added_tokens.json') if (root/name).exists())
    if not required.issubset(members):
        raise ValueError('Every runtime model/tokenizer asset must be hash-bound')
    for name, expected in members.items():
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
            raise ValueError('Missing or unsafe model artifact: ' + name)
        if digest(path.read_bytes()) != expected:
            raise ValueError('Model artifact digest mismatch: ' + name)
    return manifest
