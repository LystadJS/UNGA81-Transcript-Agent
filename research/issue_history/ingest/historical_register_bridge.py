"""Private register/exclusion composition; metadata restrictions never grant intake."""
import copy
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, unquote, urlsplit
from ..store.repository import canonical_bytes
from . import historical_source_register as register
from . import historical_exclusion_manifest as exclusions

VERSION = 'historical-register-bridge-1'


def _digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _methods():
    return {name: hashlib.sha256(Path(path).read_bytes()).hexdigest() for name, path in (
        ('historical_register_bridge.py', __file__),
        ('historical_source_register.py', register.__file__),
        ('historical_exclusion_manifest.py', exclusions.__file__))}


def _ga_candidate(value):
    value = re.sub(r'\s+', '', unquote(value)).strip('/')
    if value.lower().startswith('en/'):
        value = value[3:]
    return bool(re.match(r'^A/[^/]+/PV', value, re.I))


def _symbol(row):
    """Literal aliases only: transcript catalog keys are deliberately not translated."""
    native = row['native_id']
    symbols = []
    if _ga_candidate(native):
        symbols.append(exclusions.resolve_symbol(symbol=native))
    url = row['source_url']
    parsed = urlsplit(url)
    if parsed.hostname in ('documents.un.org', 'docs.un.org', 'undocs.org'):
        path = unquote(parsed.path).strip('/')
        if path.lower().startswith('en/'):
            path = path[3:]
        query = parse_qs(parsed.query, keep_blank_values=True)
        selectors = query.get('symbol', []) + query.get('s', [])
        # A malformed/ambiguous GA claim is an error, never an unknown bypass.
        if _ga_candidate(path) or any(_ga_candidate(unquote(v)) for v in selectors):
            symbols.append(exclusions.resolve_symbol(source_url=url))
    if len(set(symbols)) > 1:
        raise ValueError('Conflicting literal General Assembly source aliases')
    if not symbols:
        return None
    if row['family'] != 'statement' or row['source_kind'] != 'official_un_meeting_record':
        raise ValueError('General Assembly PV alias requires separate official meeting-record statement metadata')
    return symbols[0]


def build_bridge(*, register_kwargs, exclusion_kwargs):
    """Recompute both pinned inputs and overlay only restrictive exact roster matches."""
    if not isinstance(register_kwargs, dict) or not isinstance(exclusion_kwargs, dict):
        raise ValueError('Explicit register and exclusion builder inputs required')
    methods = _methods()
    base = register.build_register(**register_kwargs)
    manifest = exclusions.build_exclusion_manifest(**exclusion_kwargs)
    for field in ('as_of', 'start', 'end'):
        if base['window'][field] != manifest['window'][field]:
            raise ValueError('Register and exclusion windows must match exactly')
    roster = {row['symbol']: row for row in manifest['entries']}
    rows = []
    seen_symbols = set()
    for source in base['entries']:
        row = copy.deepcopy(source)
        symbol = _symbol(row)
        if symbol is not None:
            if symbol in seen_symbols:
                raise ValueError('Duplicate General Assembly symbol aliases require separate review')
            seen_symbols.add(symbol)
        role = roster.get(symbol)
        row['base_effective_role'] = row['effective_role']
        row['base_intake_eligible'] = row['intake_eligible']
        row['historical_exclusion'] = {
            'symbol': symbol, 'role_metadata': copy.deepcopy(role),
            'exclusion_coverage': 'known_exact_roster' if role else 'unknown'}
        if role:
            # Existing evaluation and audit restrictions outrank research status.
            priority = {'evaluation': 3, 'source_quality_audit': 2, 'restricted_research': 1}
            historical_role = role['effective_role']
            if priority.get(historical_role, 0) > priority.get(row['effective_role'], 0):
                row['effective_role'] = historical_role
            row['intake_eligible'] = False
            row['metadata_eligible_for_source_validation'] = False
            row['eligibility_reason'] = 'exact_historical_research_exclusion'
            row['exclusion_coverage'] = 'known_exact_historical_roster'
        rows.append(row)
    if _methods() != methods:
        raise ValueError('Bridge dependencies changed during validation')
    result = {
        'schema': 'un.historical-register-bridge.v1', 'version': VERSION,
        'window': copy.deepcopy(base['window']), 'base_register': base,
        'exclusion_manifest': manifest, 'entries': rows,
        'summary': {'registered_metadata': len(rows),
                    'matched_historical_exclusions': sum(r['historical_exclusion']['role_metadata'] is not None for r in rows),
                    'intake_eligible': sum(r['intake_eligible'] for r in rows),
                    'production_intake_accepted': 0, 'public_export_approved': 0},
        'historical_exclusion_coverage': 'known_exact_roster_only_off_roster_unknown',
        'archive_coverage': 'unknown', 'private_only': True,
        'production_intake_accepted': False, 'public_export_approved': False,
        'input_fingerprints': {'base_register_content_sha256': base['content_sha256'],
                               'exclusion_manifest_content_sha256': manifest['content_sha256'],
                               'method_sha256': methods},
        'limitations': ['Roster grouping years do not create exact-dated source records.',
                        'Exact roster restrictions never grant product permission or establish archive coverage.',
                        'Unknown transcript catalog keys and non-GA sources are not translated into General Assembly symbols.',
                        'Receipt metadata linkage does not authenticate original source bodies.']}
    result['content_sha256'] = _digest(result)
    return result


def _expected(value, kwargs):
    expected = build_bridge(**kwargs)
    if value != expected:
        raise ValueError('Bridge differs from recomputed pinned inputs')
    return canonical_bytes(expected)


def save_bridge(path, bridge, **kwargs):
    """Publish a canonical immutable snapshot after complete input revalidation."""
    data = _expected(bridge, kwargs)
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Bridge aliases forbidden')
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('Existing immutable bridge differs or is corrupt')
    else:
        try:
            register._publish(path, data)
        except FileExistsError:
            if path.is_symlink() or path.read_bytes() != data:
                raise ValueError('Concurrent bridge differs')
    return str(path.resolve())


def load_bridge(path, **kwargs):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('Bounded regular bridge snapshot required')
    data = path.read_bytes()
    try:
        value = json.loads(data)
    except (ValueError, UnicodeError):
        raise ValueError('Corrupt bridge snapshot')
    if data != _expected(value, kwargs):
        raise ValueError('Noncanonical or changed immutable bridge')
    return value
