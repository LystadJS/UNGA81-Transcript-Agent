"""Source-free official-record metadata verification; no legal or intake grants."""
import copy
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote, parse_qs
from ..store.repository import canonical_bytes
from . import historical_register_bridge as bridge
from . import historical_source_register as register

VERSION = 'official-record-verification-1'
SCOPES = {'private_analysis', 'automated_retrieval', 'public_redistribution'}
STATUSES = {'unknown', 'conditional', 'approval_required', 'denied'}


def _digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _methods():
    return {'official_record_verification.py': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            **bridge._methods()}


def _fields(value, fields):
    if not isinstance(value, dict) or set(value) != set(fields.split()):
        raise ValueError('Exact metadata-only fields required')


def _official_url(value):
    parsed = register._url(value)
    if parsed.hostname not in ('docs.un.org', 'documents.un.org', 'undocs.org',
                                'digitallibrary.un.org', 'transcripts.un.org', 'www.un.org', 'uncitral.un.org', 'journal.un.org'):
        raise ValueError('Primary UN metadata URL required')
    return parsed


def _symbol(value):
    if not isinstance(value, str) or not re.fullmatch(r'(?:A/[1-9]\d*/PV\.[1-9]\d*|A/C\.[1-6]/[1-9]\d*/SR\.[1-9]\d*|S/PV\.[1-9]\d*)', value):
        raise ValueError('Exact GA or SC meeting-record symbol required')
    return value


def _symbol_url(value, symbol):
    parsed = _official_url(value)
    if parsed.hostname not in ('docs.un.org', 'documents.un.org', 'undocs.org'):
        raise ValueError('Official document symbol URL required')
    path = unquote(parsed.path).strip('/')
    if path[:3].lower() == 'en/':
        path = path[3:]
    query = parse_qs(parsed.query, keep_blank_values=True)
    if any(key.lower() in ('s', 'symbol') and key not in ('s', 'symbol') for key in query):
        raise ValueError('Noncanonical document selector key')
    selectors = query.get('s', []) + query.get('symbol', [])
    if re.match(r'^(?:A/|S/PV)', path, re.I) and path != symbol:
        raise ValueError('Document path conflicts with symbol')
    if selectors:
        if len(selectors) != 1 or selectors[0] != symbol:
            raise ValueError('Ambiguous or mismatched document selector')
    elif path != symbol:
        raise ValueError('Document URL must explicitly identify symbol')


def _provenance(value, as_of):
    _fields(value, 'url retrieved_on content_sha256 hash_scope retrieval_mode')
    _official_url(value['url'])
    if value['hash_scope'] not in ('review_note', 'retrieved_primary_metadata_bytes') or value['retrieval_mode'] not in ('review_note', 'direct_primary', 'search_index'):
        raise ValueError('Explicit provenance hash and retrieval scope required')
    if value['hash_scope'] == 'retrieved_primary_metadata_bytes' and value['retrieval_mode'] != 'direct_primary':
        raise ValueError('Primary byte hash requires direct primary retrieval')
    if register._day(value['retrieved_on']) > register._day(as_of) or not register._sha(value['content_sha256']):
        raise ValueError('Dated primary metadata hash required')


def build_verification(*, bridge_kwargs, evidence_receipts, expected_evidence_sha256):
    if not register._sha(expected_evidence_sha256) or _digest(evidence_receipts) != expected_evidence_sha256:
        raise ValueError('Externally configured evidence receipt digest required')
    methods = _methods()
    base = bridge.build_bridge(**bridge_kwargs)
    if not isinstance(evidence_receipts, list) or len(evidence_receipts) > 100000:
        raise ValueError('Bounded evidence receipts required')
    entries = {row['source_id']: row for row in base['entries']}
    receipts = {}
    for receipt in evidence_receipts:
        _fields(receipt, 'source_id primary_record primary_metadata crosswalk permissions')
        sid = receipt['source_id']
        if not isinstance(sid, str) or sid not in entries or sid in receipts:
            raise ValueError('Unique registered receipt source required')
        receipts[sid] = receipt
    out = []
    for sid, source in sorted(entries.items()):
        receipt = receipts.get(sid)
        identity = 'unverified_no_primary_metadata'
        conflicts = []
        symbol = None
        permissions = {scope: {'status': 'unknown', 'approved': False, 'evidence': None} for scope in sorted(SCOPES)}
        if receipt:
            primary, metadata, crosswalk = (receipt[k] for k in ('primary_record', 'primary_metadata', 'crosswalk'))
            if (primary is None) != (metadata is None):
                raise ValueError('Primary record and primary metadata must be supplied together')
            if primary is not None:
                _fields(primary, 'symbol body meeting_date official_url')
                symbol = _symbol(primary['symbol'])
                _symbol_url(primary['official_url'], symbol)
                _provenance(metadata, base['window']['as_of'])
                if metadata['hash_scope'] != 'retrieved_primary_metadata_bytes':
                    raise ValueError('Record identity requires primary metadata byte provenance')
                register._day(primary['meeting_date'])
                expected_body = ('GA_C' + symbol[4] if symbol.startswith('A/C.') else 'GA' if symbol.startswith('A/') else 'SC')
                if primary['body'] != expected_body:
                    raise ValueError('Symbol and primary body disagree')
                if primary['meeting_date'] > base['window']['as_of']:
                    raise ValueError('Future record metadata forbidden')
                if source['body'] != primary['body']: conflicts.append('body')
                if source['date'] != primary['meeting_date']: conflicts.append('meeting_date')
                if source['family'] != 'statement': conflicts.append('source_family')
                native = source['native_id']
                if re.match(r'^(?:A/|S/PV)', native) and native != symbol: conflicts.append('native_symbol')
                identity = 'conflicting_metadata' if conflicts else 'unlinked_primary_metadata'
            if crosswalk is not None:
                if primary is None:
                    raise ValueError('Crosswalk requires primary record metadata')
                _fields(crosswalk, 'source_native_id source_url official_symbol explicit_link metadata')
                _provenance(crosswalk['metadata'], base['window']['as_of'])
                if crosswalk['metadata']['hash_scope'] != 'retrieved_primary_metadata_bytes':
                    raise ValueError('Explicit crosswalk requires primary metadata byte provenance')
                if crosswalk['explicit_link'] is not True:
                    raise ValueError('Only explicit primary metadata crosswalks accepted')
                if crosswalk['source_native_id'] != source['native_id'] or crosswalk['source_url'] != source['source_url'] or crosswalk['official_symbol'] != symbol:
                    conflicts.append('crosswalk')
                # Distinct supplied artifact hashes do not establish independent authentication.
                if crosswalk['metadata']['content_sha256'] == metadata['content_sha256']:
                    raise ValueError('Distinct supplied crosswalk provenance hashes required')
                identity = 'conflicting_metadata' if conflicts else 'consistent_supplied_metadata_link'
            scopes_seen = set()
            if not isinstance(receipt['permissions'], list) or len(receipt['permissions']) > 3:
                raise ValueError('Bounded separate permission scopes required')
            for permission in receipt['permissions']:
                _fields(permission, 'scope status evidence')
                scope = permission['scope']
                if scope not in SCOPES or scope in scopes_seen or permission['status'] not in STATUSES:
                    raise ValueError('Distinct permission scope with non-grant status required')
                scopes_seen.add(scope)
                if permission['evidence'] is not None:
                    _provenance(permission['evidence'], base['window']['as_of'])
                elif permission['status'] != 'unknown':
                    raise ValueError('Permission qualification requires primary evidence')
                permissions[scope] = {'status': permission['status'], 'approved': False,
                                      'evidence': copy.deepcopy(permission['evidence'])}
        blocked = source['effective_role'] in ('evaluation', 'source_quality_audit', 'restricted_research') or source['reserved_blocked']
        out.append({'source_id': sid, 'effective_role': source['effective_role'],
                    'in_window': source['in_window'], 'role_blocked': blocked,
                    'identity_status': identity, 'official_symbol': symbol,
                    'metadata_conflicts': conflicts, 'permissions': permissions,
                    'receipt_sha256': _digest(receipt) if receipt else None,
                    'metadata_candidate_only': source['metadata_eligible_for_source_validation'],
                    'production_intake_accepted': False, 'public_export_approved': False})
    if methods != _methods():
        raise ValueError('Verification dependencies changed during validation')
    result = {'schema': 'un.official-record-verification.v1', 'version': VERSION,
              'window': copy.deepcopy(base['window']), 'bridge': base, 'entries': out,
              'summary': {'registered_metadata': len(out), 'consistent_supplied_metadata_links': sum(r['identity_status'] == 'consistent_supplied_metadata_link' for r in out),
                          'conflicting_metadata': sum(r['identity_status'] == 'conflicting_metadata' for r in out),
                          'production_intake_accepted': 0, 'public_export_approved': 0},
              'private_only': True, 'archive_coverage': 'unknown',
              'verification_scope': 'provided_metadata_consistency_only_not_independent_authentication',
              'authority_pin_scope': 'explicit_trusted_configuration_not_independent_authentication',
              'input_fingerprints': {'bridge_content_sha256': base['content_sha256'],
                                     'evidence_receipts_sha256': _digest(evidence_receipts), 'expected_evidence_sha256': expected_evidence_sha256, 'method_sha256': methods},
              'limitations': ['Supplied primary metadata and explicit crosswalk claims are checked for consistency, not independently authenticated.',
                              'Metadata hashes are supplied provenance, not raw source body verification.',
                              'Conditional copyright terms do not grant endpoint automation, private analysis or redistribution permission.',
                              'All legal permissions remain uncleared; role restrictions and holdouts remain effective.',
                              'No archive completeness, accepted opinion labels or model permission is established.']}
    result['content_sha256'] = _digest(result)
    return result


def _expected(value, kwargs):
    expected = build_verification(**kwargs)
    if value != expected:
        raise ValueError('Verification differs from recomputed pinned inputs')
    return canonical_bytes(expected)


def save_verification(path, verification, **kwargs):
    data = _expected(verification, kwargs)
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Verification aliases forbidden')
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('Existing immutable verification differs')
    else:
        try:
            register._publish(path, data)
        except FileExistsError:
            if path.is_symlink() or path.read_bytes() != data:
                raise ValueError('Concurrent verification differs')
    return str(path.resolve())


def load_verification(path, **kwargs):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('Bounded regular verification required')
    data = path.read_bytes()
    try:
        value = json.loads(data)
    except (ValueError, UnicodeError):
        raise ValueError('Corrupt verification snapshot')
    if data != _expected(value, kwargs):
        raise ValueError('Noncanonical verification snapshot')
    return value
