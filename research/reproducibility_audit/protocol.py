"""Independent, offline validation of the coordinator-owned interchange contract.

No held-out source access, external services, empirical fitting or publication side
 effects. Fail closed if the authoritative schema is missing or unrecognized.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

CONTRACT_RELATIVE = Path('docs/parallel-work/interchange-v1.schema.json')
SCHEMA_SHA_GIT_BLOB = '3786a08eb6c4a7de7db2845138ffe4ae51f4b2c3'
RESERVED = {'2026-10-05', '2026-10-06'}
STATUSES = ('PASS', 'FAIL', 'NOT RUN', 'NOT APPLICABLE')
SHA256_RE = re.compile(r'^[a-f0-9]{64}$')
KNOWN_SCHEMA_KEYWORDS = {'type', 'properties', 'required', 'items', 'additionalProperties',
                         'enum', 'const', 'minimum', 'maximum', 'minItems', 'minLength',
                         'pattern', 'format', 'description', 'title', '$schema', '$id'}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def canonical_json(data: Any) -> bytes:
    return (json.dumps(data, sort_keys=True, ensure_ascii=False,
                       separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def _value_type(t: str, value: Any) -> bool:
    return {'null': lambda: value is None,
            'string': lambda: isinstance(value, str),
            'integer': lambda: type(value) is int,
            'number': lambda: type(value) in (int, float) and math.isfinite(value),
            'boolean': lambda: type(value) is bool,
            'array': lambda: isinstance(value, list),
            'object': lambda: isinstance(value, dict)}[t]()


def structural(schema: dict, value: Any, location: str = '$') -> list[str]:
    """Enforce every keyword used by the pinned coordinator JSON schema, stdlib only.

    Refuse unsupported keywords rather than silently treating an expanded schema
    as though it had been completely validated.
    """
    problems: list[str] = []
    unknown = set(schema).difference(KNOWN_SCHEMA_KEYWORDS)
    if unknown:
        return [f'{location}: unsupported schema keywords {sorted(unknown)}']
    types = schema.get('type')
    if types is not None and not any(_value_type(t, value) for t in
                                     ([types] if isinstance(types, str) else types)):
        return [f'{location}: type']
    if 'const' in schema and value != schema['const']:
        problems.append(f'{location}: const')
    if 'enum' in schema and value not in schema['enum']:
        problems.append(f'{location}: enum')
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0):
            problems.append(f'{location}: minLength')
        if 'pattern' in schema and not re.search(schema['pattern'], value):
            problems.append(f'{location}: pattern')
        if schema.get('format') == 'date-time':
            try:
                assert re.search(r'(Z|[+-]\d{2}:\d{2})$', value)
                datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (AssertionError, ValueError):
                problems.append(f'{location}: date-time')
        elif schema.get('format') not in (None, 'date-time'):
            problems.append(f'{location}: unsupported format')
    if type(value) in (int, float):
        if value < schema.get('minimum', float('-inf')):
            problems.append(f'{location}: minimum')
        if value > schema.get('maximum', float('inf')):
            problems.append(f'{location}: maximum')
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            problems.append(f'{location}: minItems')
        for idx, item in enumerate(value):
            if 'items' in schema:
                problems.extend(structural(schema['items'], item, f'{location}[{idx}]'))
    if isinstance(value, dict):
        for key in schema.get('required', []):
            if key not in value:
                problems.append(f'{location}: missing {key}')
        props = schema.get('properties', {})
        for key, item in value.items():
            if key in props:
                problems.extend(structural(props[key], item, f'{location}.{key}'))
            elif schema.get('additionalProperties') is False:
                problems.append(f'{location}: unknown {key}')
    return problems


def load_contract(repo_root: Path, *, expected_git_blob: str = SCHEMA_SHA_GIT_BLOB) -> tuple[dict | None, list[str]]:
    """Reject missing schema, altered schema, or unsupported schema vocabulary."""
    path = Path(repo_root) / CONTRACT_RELATIVE
    try:
        data = path.read_bytes()
    except OSError as e:
        return None, [f'contract NOT RUN: schema unavailable ({e.__class__.__name__})']
    if git_blob_sha(data) != expected_git_blob:
        return None, ['contract FAIL: upstream schema SHA differs from pinned base; explicit audit required']
    try:
        schema = json.loads(data)
    except (ValueError, UnicodeError):
        return None, ['contract FAIL: schema not valid JSON']
    def inspect(definition: Any) -> list[str]:
        if not isinstance(definition, dict):
            return ['invalid schema node']
        result = [f'unsupported keywords: {sorted(set(definition) - KNOWN_SCHEMA_KEYWORDS)}'] if set(definition)-KNOWN_SCHEMA_KEYWORDS else []
        if isinstance(definition.get('items'), dict):
            result.extend(inspect(definition['items']))
        for child in definition.get('properties', {}).values():
            result.extend(inspect(child))
        return result
    issues = inspect(schema)
    return (None, issues) if issues else (schema, [])


def _nonnull_string(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip())


def validate_envelope(doc: Any, schema: dict | None) -> list[str]:
    """Structural + relational rules, using only synthetic or authorized metadata.

    Never accept schema-less calls as successful validation. No text inspection.
    """
    if schema is None:
        return ['contract NOT RUN: authoritative schema unavailable']
    errs = structural(schema, doc)
    if errs:
        return sorted(set(errs))  # do not trust malformed input for relational logic
    cohort, upstream, producer = doc['cohort'], doc['upstream'], doc['producer']
    observations, models, results, coverage = (doc[k] for k in ('observations', 'models', 'results', 'coverage'))
    if cohort['split'] == 'development' and producer['fixture_kind'] != 'private_development':
        errs.append('split/fixture_kind mismatch')
    if any(o['date'] in RESERVED for o in observations):
        errs.append('reserved October 5-6 source identity')
    for key in ('source_sha256', 'selection_sha256'):
        if upstream[key] is None and not _nonnull_string(upstream['missing_reason']):
            errs.append(f'missing {key} without reason')
    ids = [o['id'] for o in observations]
    mids = [m['model_id'] for m in models]
    if len(ids) != len(set(ids)) or any(not _nonnull_string(x) for x in ids):
        errs.append('duplicate/missing observation ID')
    if len(mids) != len(set(mids)) or any(not _nonnull_string(x) for x in mids):
        errs.append('duplicate/missing model ID')
    if any(o['unit'] != cohort['unit'] for o in observations):
        errs.append('unit population mismatch')
    if any(m['fit_split'] != cohort['split'] for m in models):
        errs.append('fit/evaluation split mismatch')
    eligible = {o['id'] for o in observations if o['source_status'] == 'available' and not o['exclusion_reasons']}
    excluded = len(observations) - len(eligible)
    if len(eligible) != cohort['eligible'] or coverage['eligible'] != len(eligible):
        errs.append('eligible denominator mismatch')
    if coverage['excluded'] != excluded or coverage['observations_total'] != len(observations):
        errs.append('frame denominator mismatch')
    # Inventory meetings, source groups and passage observations are different
    # units. Never compare their raw counts, except that a nonempty observed
    # frame cannot have an explicitly empty inventory.
    if observations and cohort['total_in_frame'] == 0:
        errs.append('empty declared frame with observed records')
    ob_by_id = {o['id']: o for o in observations}
    for o in observations:
        if o['parent_id'] is not None and not o['parent_text_sha256']:
            errs.append('parent hash missing')
        if (o['start'] is None) != (o['end'] is None) or (o['start'] is not None and o['end'] <= o['start']):
            errs.append('invalid code-point offsets')
        if o['source_status'] != 'available' and not _nonnull_string(o['missing_reason']):
            errs.append('unavailable source reason missing')
        if o['speech_id'] is not None and o['review_status'] != 'confirmed':
            errs.append('unverified speech attribution')
        if cohort['split'] == 'development' and o['source_status'] == 'available' and o['date'] and not o['meeting_id']:
            errs.append('unverified development meeting')
    mc = coverage['models']
    cids = [c['model_id'] for c in mc]
    if len(cids) != len(set(cids)) or set(cids) != set(mids):
        errs.append('coverage model identity mismatch')
    rows_by_model = {m: [] for m in mids}
    for r in results:
        if r['model_id'] not in rows_by_model or r['observation_id'] not in ob_by_id:
            errs.append('orphan result')
        else:
            rows_by_model[r['model_id']].append(r)
    for model in models:
        m = model['model_id']
        seen: set[str] = set()
        for r in rows_by_model[m]:
            oid = r['observation_id']
            if oid in seen:
                errs.append('duplicate result identity')
            seen.add(oid)
            status, cluster = r['status'], r['cluster']
            if r['representation_basis_id'] != model['representation_id']:
                errs.append('representation basis mismatch')
            if status == 'assigned' and (type(cluster) is not int or cluster < 1):
                errs.append('invalid assigned label')
            if status == 'unassigned' and cluster != 0:
                errs.append('invalid unassigned label')
            if status in ('excluded', 'not_fitted') and (cluster is not None or not _nonnull_string(r['reason'])):
                errs.append('invalid excluded/not-fitted label')
            weights = r['memberships']
            if r['membership_kind'] in ('gmm_responsibility', 'nmf_share'):
                if not weights or any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in weights) or abs(math.fsum(weights) - 1) >= 1e-6:
                    errs.append('membership denominator/normalization')
            elif weights is not None:
                errs.append('unexpected membership array')
            if r['membership_kind'] == 'hdbscan_strength' and r['membership_strength'] is None:
                errs.append('missing density strength')
            if r['membership_kind'] != 'hdbscan_strength' and r['membership_strength'] is not None:
                errs.append('untyped membership strength')
            if oid in eligible and status == 'excluded':
                errs.append('eligible observation mislabeled excluded')
            if oid not in eligible and status != 'excluded':
                errs.append('excluded observation mislabeled eligible')
        if len(eligible) > 0 and any(o not in seen for o in eligible):
            errs.append('missing eligible model result')
        if len(eligible) == 0 and rows_by_model[m] and any(r['status'] != 'excluded' for r in rows_by_model[m]):
            errs.append('non-excluded result in empty eligible cohort')
        c = next((c for c in mc if c['model_id'] == m), None)
        if c is None:
            continue
        observed = Counter(r['status'] for r in rows_by_model[m])
        if c['eligible'] != len(eligible) or c['excluded'] != excluded:
            errs.append('per-model eligible/excluded denominator mismatch')
        for key in ('assigned', 'unassigned', 'not_fitted', 'excluded'):
            if c[key] != observed[key]:
                errs.append('per-model outcome denominator mismatch')
        if c['assigned'] + c['unassigned'] + c['not_fitted'] != c['eligible']:
            errs.append('selected outcome denominator mismatch')
        if c['attempted_fits'] != c['successful_fits'] + c['failed_fits']:
            errs.append('fit attempt denominator mismatch')
    for entry in coverage['failure_ledger']:
        if entry['model_id'] not in mids:
            errs.append('orphan failed-fit model')
        if not _nonnull_string(entry['reason']):
            errs.append('unexplained failed-fit')
    for c in mc:
        failures = [f for f in coverage['failure_ledger'] if f['model_id'] == c['model_id'] and f['status'] in ('failed', 'timed_out', 'nonconverged')]
        if c['failed_fits'] and len(failures) < c['failed_fits']:
            errs.append('missing failed-fit ledger')
    for evidence in doc['evidence']:
        if evidence['observation_id'] not in ob_by_id:
            errs.append('orphan evidence')
        if (evidence['start'] is None) != (evidence['end'] is None) or (evidence['start'] is not None and evidence['end'] <= evidence['start']):
            errs.append('invalid evidence offset')
    for diagnostic in doc['diagnostics']:
        if diagnostic['model_id'] is not None and diagnostic['model_id'] not in mids:
            errs.append('orphan diagnostic')
        if diagnostic['status'] == 'validated' and (diagnostic['denominator'] is None or diagnostic['denominator'] == 0):
            errs.append('validated zero/unknown diagnostic denominator')
        if diagnostic['status'] in ('withheld', 'failed') and not _nonnull_string(diagnostic['reason']):
            errs.append('unexplained diagnostic withholding')
    return sorted(set(errs))


def check_populations(a: dict, b: dict, alignment_protocol: dict | None = None) -> list[str]:
    """No implicit comparisons between different sources, selected rows or bases."""
    keys = ('source_schema', 'source_hash_basis', 'source_sha256', 'selection_sha256')
    errors = [f'{key} mismatch' for key in keys if a.get('upstream', {}).get(key) != b.get('upstream', {}).get(key)]
    for key in keys:
        if not a.get('upstream', {}).get(key) or not b.get('upstream', {}).get(key):
            errors.append(f'{key} missing comparison identity')
    for key in ('population', 'unit', 'source_group_unit', 'weighting', 'selection_policy'):
        if a.get('cohort', {}).get(key) != b.get('cohort', {}).get(key):
            errors.append(f'{key} mismatch')
    left = {(o.get('id'), o.get('text_sha256')) for o in a.get('observations', [])}
    right = {(o.get('id'), o.get('text_sha256')) for o in b.get('observations', [])}
    if left != right:
        errors.append('observation population/hash mismatch')
    left_rep = {(m.get('representation_id'), m.get('representation_version')) for m in a.get('models', [])}
    right_rep = {(m.get('representation_id'), m.get('representation_version')) for m in b.get('models', [])}
    if left_rep != right_rep:
        errors.append('representation lineage mismatch')
    if errors and alignment_protocol:
        errors.append('alignment proposal supplied; independent source authorization still required')
    return sorted(set(errors))


def check_isolation(training: list[dict], evaluation: list[dict]) -> list[str]:
    if not training or not evaluation:
        return ['training/evaluation identity unavailable']
    failures=[]
    for key in ('id', 'source_family_id', 'parent_id', 'speech_id', 'meeting_id', 'text_sha256', 'parent_text_sha256'):
        tr = {r.get(key) for r in training if r.get(key) is not None}
        ev = {r.get(key) for r in evaluation if r.get(key) is not None}
        if tr.intersection(ev):
            failures.append(f'evaluation leakage: {key}')
    if any(not r.get('id') or not r.get('text_sha256') or not r.get('source_family_id') for r in training + evaluation):
        failures.append('missing isolation identity')
    return failures


def changed_path_violations(paths: list[str], allowed_prefix: str = 'research/reproducibility_audit/') -> list[str]:
    violations=[]
    for raw in paths:
        path=Path(raw)
        if (not isinstance(raw, str) or not raw.startswith(allowed_prefix) or
            path.is_absolute() or any(p in ('.', '..') for p in raw.split('/')) or
            '\\' in raw or '\x00' in raw):
            violations.append(str(raw))
    return violations


def result_record(name: str, status: str, evidence: str) -> dict:
    if status not in STATUSES or not _nonnull_string(evidence):
        raise ValueError('Each QA status requires supported evidence')
    return {'name': name, 'status': status, 'evidence': evidence}


def qa_summary(checks: list[dict]) -> dict:
    if len({c['name'] for c in checks}) != len(checks):
        raise ValueError('duplicate QA check names')
    for c in checks:
        result_record(c['name'], c['status'], c['evidence'])
    return {'schema': 'un.reproducibility-audit.v2', 'checks': checks,
            'engineering_acceptance': 'PASS' if checks and all(c['status'] in ('PASS', 'NOT APPLICABLE') for c in checks) else 'WITHHELD',
            'publication_authorized': False}
