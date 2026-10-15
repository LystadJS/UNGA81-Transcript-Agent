"""Synthetic-only US-relative sidecar; no loaders, fitting, networking or release.

The external synthetic receipt binds an already supplied panel; it establishes
consistency, never independent authentication. W4 core is imported read-only by
adapt_w4. Missingness and source identities survive aggregation and replay.
"""
from __future__ import annotations

import copy
import hashlib
import math
import re
import struct
from collections import Counter, defaultdict
from datetime import date

INPUT_SCHEMA = 'un.us-relative-source-panel.v1'
SCHEMA = 'un.us-relative-trajectories.v1'
VERSION = '0.1.0'
HASH_BASIS = 'sha256/usref-wire-v1'
WEIGHT_POLICY = 'w4_equal_meeting_within_genre_equal_genre_v1'
TOLERANCE = 1e-10  # Engineering arithmetic tolerance, NOT a scientific gate.
PERMISSIONS = {'evaluation_role': 'engineering_only', 'publication_eligible': False,
               'real_data_eligible': False, 'holdout_access': False, 'approval_receipts': []}
TOKEN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,159}$')
HASH = re.compile(r'^[0-9a-f]{64}$')
ISO3 = re.compile(r'^[A-Z]{3}$')
STATUSES = {'available', 'unavailable', 'unverified', 'failed', 'empty_transcript',
            'inventory_failed', 'excluded_language'}
OBS_KEYS = ('id period date country_iso3 actor_id speaker_id speech_id capacity '
            'attribution_status review_receipt genre language source_type topic_id '
            'source_status missing_reason meeting_id source_family_id source_sha256 '
            'text_sha256 source_hash_basis parent_id parent_text_sha256 start end '
            'source_pointer representation_fingerprint vector').split()


class ContractError(ValueError):
    """Rejected input; callers must discard any previous read model."""


def require(condition, message):
    if not condition:
        raise ContractError(message)


def exact(obj, fields, label):
    require(type(obj) is dict and set(obj) == set(fields), f'{label}: unexpected or missing fields')


def token(value, label, nullable=False):
    require((nullable and value is None) or (type(value) is str and TOKEN.fullmatch(value)),
            f'{label}: expected a bounded identifier, not source prose')


def sha(value, label, nullable=False):
    require((nullable and value is None) or (type(value) is str and HASH.fullmatch(value)),
            f'{label}: invalid SHA-256')


def finite_vector(value, dimension, label):
    require(type(value) is list and len(value) == dimension and all(
        type(x) in (int, float) and math.isfinite(x) and abs(x) <= 1e100 for x in value),
        f'{label}: invalid, nonfinite or unsafe vector')


def iso_date(value, label):
    require(type(value) is str and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value), f'{label}: ISO date required')
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ContractError(f'{label}: invalid date') from exc


def wire(value):
    """Language-neutral typed bytes; numbers are normalized IEEE-754 binary64.

    Null=n, booleans=t/f, number=d+16 hex bytes, UTF-8=s<byte-length>:<bytes>,
    list=[items], dict={sorted-key/value pairs}. -0 is canonicalized to +0.
    Never confuse a self-computed digest with a source-authentication receipt.
    """
    if value is None:
        return b'n'
    if type(value) is bool:
        return b't' if value else b'f'
    if type(value) in (int, float):
        require(math.isfinite(value), 'Nonfinite number cannot be hashed')
        require(type(value) is not int or abs(value) <= 2**53 - 1, 'Unsafe integer')
        return b'd' + struct.pack('>d', float(value) if value else 0.0).hex().encode('ascii')
    if type(value) is str:
        raw = value.encode('utf-8')
        return b's' + str(len(raw)).encode('ascii') + b':' + raw
    if type(value) is list:
        return b'[' + b''.join(map(wire, value)) + b']'
    if type(value) is dict:
        require(all(type(k) is str and k.isascii() for k in value), 'Hash keys must be ASCII')
        return b'{' + b''.join(wire(k) + wire(value[k]) for k in sorted(value)) + b'}'
    raise ContractError('Unsupported hash value')


def digest(value):
    return hashlib.sha256(wire(value)).hexdigest()


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b))


def point_metrics(country, us):
    require(type(country) is list and 2 <= len(country) <= 1024, 'Invalid metric dimension')
    finite_vector(country, len(country), 'country')
    finite_vector(us, len(country), 'US')
    relative = sub(country, us)
    return {'relative_vector': relative, 'distance': math.hypot(*relative)}


def transition_metrics(c0, c1, u0, u1):
    a, b = point_metrics(c0, u0), point_metrics(c1, u1)
    require(len(c0) == len(c1), 'Transition dimension mismatch')
    dc, du = sub(c1, c0), sub(u1, u0)
    dr = sub(dc, du)
    total = [x + y for x, y in zip(a['relative_vector'], b['relative_vector'])]
    qc, qu = dot(total, dc), -dot(total, du)
    denom = a['distance'] + b['distance']
    # Normalize before the dot product so tiny nonzero gaps do not underflow.
    direction = [x / denom for x in total] if denom > 0 else None
    gc, gu = (dot(direction, dc), -dot(direction, du)) if denom > 0 else (None, None)
    return {'gap_change': b['distance'] - a['distance'], 'country_change': dc,
            'us_change': du, 'relative_change': dr,
            'country_displacement': math.hypot(*dc), 'us_displacement': math.hypot(*du),
            'relative_displacement': math.hypot(*dr),
            'squared_gap_country_contribution': qc, 'squared_gap_us_contribution': qu,
            'gap_country_contribution': gc, 'gap_us_contribution': gu,
            'decomposition_status': 'ready' if denom > 0 else 'undefined_zero_gaps',
            'reconciliation_residual': (gc + gu - (b['distance'] - a['distance'])) if denom > 0 else None,
            'interpretation': 'algebraic_not_causal'}


def validate_display(display, metric):
    """A display-only failure withholds xy, never an otherwise valid metric."""
    if display is None:
        return {'state': 'withheld', 'reason': 'display_transform_missing'}
    try:
        exact(display, ['method', 'basis', 'center', 'metric_fingerprint', 'fit_id'], 'display')
        require(display['method'] == 'fixed_orthonormal_linear', 'Nonlinear display is not a metric')
        require(display['metric_fingerprint'] == metric['fingerprint'], 'Display basis mismatch')
        token(display['fit_id'], 'display fit')
        d = metric['dimension']
        finite_vector(display['center'], d, 'display center')
        require(type(display['basis']) is list and len(display['basis']) == d, 'Display row count')
        for row in display['basis']:
            finite_vector(row, 2, 'display basis')
        cols = list(map(list, zip(*display['basis'])))
        require(all(abs(dot(cols[i], cols[j]) - int(i == j)) <= TOLERANCE
                    for i in range(2) for j in range(2)), 'Nonorthonormal display')
        return {'state': 'ready', 'reason': None, **copy.deepcopy(display), 'sha256': digest(display)}
    except ContractError:
        # Do not propagate unvalidated strings, vectors, coefficients or pointers.
        return {'state': 'withheld', 'reason': 'display_transform_invalid'}


def validate_source(panel, receipt):
    from .schema_contract import validate as validate_schema, SchemaError
    try:
        validate_schema(panel, source=True)
    except SchemaError as exc:
        raise ContractError('Invalid synthetic input schema') from exc
    exact(panel, ['schema', 'split', 'identity', 'metric_space', 'display_space', 'scope',
                  'periods', 'observations'], 'source panel')
    require(panel['schema'] == INPUT_SCHEMA and panel['split'] == 'synthetic',
            'Phase 1 accepts synthetic panels only; development and holdout are forbidden')
    exact(receipt, ['kind', 'hash_basis', 'panel_sha256'], 'external synthetic receipt')
    require(receipt['kind'] == 'synthetic_consistency_only' and receipt['hash_basis'] == HASH_BASIS,
            'Synthetic consistency receipt required; not authentication')
    sha(receipt['panel_sha256'], 'receipt')
    require(digest(panel) == receipt['panel_sha256'], 'source_authentication_failed: panel/receipt mismatch')
    identity = panel['identity']
    exact(identity, ['producer_schema', 'producer_version', 'producer_panel_sha256',
                     'selection_sha256', 'runtime_id'], 'identity')
    for key in ('producer_schema', 'producer_version', 'runtime_id'):
        token(identity[key], key)
    for key in ('producer_panel_sha256', 'selection_sha256'):
        sha(identity[key], key)
    metric = panel['metric_space']
    exact(metric, ['id', 'version', 'fingerprint', 'dimension', 'feature_order', 'space_kind',
                   'preprocessing_id', 'normalization', 'fit_selection_sha256', 'training_cutoff', 'upstream_fingerprint'], 'metric')
    for key in ('id', 'version', 'preprocessing_id', 'normalization'):
        token(metric[key], key)
    require(type(metric['dimension']) is int and 2 <= metric['dimension'] <= 1024, 'Dimension must be 2..1024')
    require(metric['space_kind'] in ('full_feature_space', 'retained_score_space'), 'Metric space kind')
    features = metric['feature_order']
    require(type(features) is list and len(features) == metric['dimension'] and
            all(type(f) is str for f in features) and len(set(features)) == len(features), 'Feature order must be complete and unique')
    for feature in features:
        token(feature, 'feature')
    sha(metric['fit_selection_sha256'], 'fitting selection')
    sha(metric['upstream_fingerprint'], 'upstream representation')
    iso_date(metric['training_cutoff'], 'training cutoff')
    sha(metric['fingerprint'], 'metric fingerprint')
    require(metric['fingerprint'] == digest({k: v for k, v in metric.items() if k != 'fingerprint'}),
            'representation_mismatch: descriptor/fingerprint mismatch')
    scope = panel['scope']
    exact(scope, ['countries', 'genres', 'language', 'source_type', 'topic_id', 'support_mode',
                  'weight_policy', 'source_unit_policy', 'baseline_iso3', 'baseline_mode'], 'scope')
    require(scope['support_mode'] == 'common' and scope['baseline_mode'] == 'contemporaneous',
            'Phase 1 requires common support and contemporaneous reference; no silent substitution')
    require(scope['baseline_iso3'] == 'USA', 'Canonical baseline must be USA')
    require(scope['weight_policy'] == WEIGHT_POLICY, 'Weight policy is not the inherited W4 policy')
    require(scope['source_unit_policy'] == 'one_vector_per_original_parent', 'Unsupported source partition')
    countries, genres = scope['countries'], scope['genres']
    require(type(countries) is list and 1 <= len(countries) <= 256 and
            all(type(c) is str and ISO3.fullmatch(c) for c in countries) and
            len(set(countries)) == len(countries) and 'USA' in countries, 'Invalid declared country frame')
    require(type(genres) is list and 1 <= len(genres) <= 32 and all(type(g) is str for g in genres) and len(set(genres)) == len(genres), 'Invalid genres')
    for value in [*genres, scope['language'], scope['source_type'], scope['topic_id']]:
        token(value, 'scope identifier')
    periods = panel['periods']
    require(type(periods) is list and 2 <= len(periods) <= 256 and
            len(periods) * len(countries) <= 20000, 'Invalid period/cell resource bound')
    pmap, previous = {}, None
    for p in periods:
        exact(p, ['id', 'start', 'end'], 'period')
        token(p['id'], 'period id')
        require(p['id'] not in pmap, 'Duplicate period')
        start, end = iso_date(p['start'], 'start'), iso_date(p['end'], 'end')
        require(start <= end and (previous is None or previous < start), 'Periods must be ordered and nonoverlapping')
        pmap[p['id']] = (start, end)
        previous = end
    if panel['display_space'] is not None:
        exact(panel['display_space'], ['method', 'basis', 'center', 'metric_fingerprint', 'fit_id'], 'display input')
        token(panel['display_space']['method'], 'display method')
        token(panel['display_space']['fit_id'], 'display fit')
    rows = panel['observations']
    require(type(rows) is list and len(rows) <= 20000, 'Source-row resource bound')
    ids, units, parents, meetings, used_parents = set(), {}, {}, {}, set()
    for row in rows:
        exact(row, OBS_KEYS, 'observation')
        token(row['id'], 'observation id')
        require(row['id'].startswith(('syn-', 'fictional-')) and row['id'] not in ids, 'Synthetic unique IDs required')
        ids.add(row['id'])
        require(row['period'] in pmap, 'Unknown observation period')
        require(row['country_iso3'] is None or row['country_iso3'] in countries, 'Country outside declared frame')
        require(row['source_hash_basis'] == 'synthetic', 'Non-synthetic source basis forbidden')
        require(row['source_status'] in STATUSES, 'Unknown source state')
        require(row['capacity'] in ('national', 'collective', 'un_staff', 'unknown'), 'Unknown capacity')
        require(row['attribution_status'] in ('synthetic_verified', 'unverified'), 'Unknown attribution state')
        for key in ('genre', 'language', 'source_type', 'topic_id'):
            token(row[key], key)
        for key in ('actor_id', 'speaker_id', 'speech_id', 'review_receipt', 'meeting_id',
                    'source_family_id', 'parent_id', 'missing_reason'):
            token(row[key], key, nullable=True)
        for key in ('source_sha256', 'text_sha256', 'parent_text_sha256', 'representation_fingerprint'):
            sha(row[key], key, nullable=True)
        if row['date'] is not None:
            when = iso_date(row['date'], 'observation date')
            require(pmap[row['period']][0] <= when <= pmap[row['period']][1], 'Observation outside period')
            require(row['date'] not in ('2026-10-05', '2026-10-06'), 'Reserved dates are not admissible')
        a, b = row['start'], row['end']
        require((a is None and b is None) or (type(a) is int and type(b) is int and 0 <= a < b <= 2**53-1),
                'Original code-point offsets are inconsistent')
        pointer = row['source_pointer']
        require(pointer is None or (type(pointer) is str and
                re.fullmatch(r'/synthetic/[A-Za-z0-9_/-]{1,200}', pointer)), 'Unsafe source pointer')
        if row['parent_id'] is not None:
            require(row['parent_text_sha256'] is not None, 'Parent hash required')
            parent = (row['source_sha256'], row['parent_id'])
            require(parents.setdefault(parent, row['parent_text_sha256']) == row['parent_text_sha256'],
                    'Conflicting parent identity')
        if row['meeting_id'] is not None and row['source_sha256'] is not None:
            meeting = (row['period'], row['date'], row['source_family_id'], row['source_sha256'])
            require(meetings.setdefault(row['meeting_id'], meeting) == meeting, 'Conflicting meeting identity')
        if row['source_status'] == 'available':
            require(row['date'] is not None and row['missing_reason'] is None, 'Observed source needs an actual date')
            require(all(row[k] is not None for k in ('meeting_id', 'source_family_id', 'source_sha256',
                        'text_sha256', 'parent_id', 'parent_text_sha256', 'source_pointer', 'start', 'end')),
                    'Observed lineage incomplete')
            require(row['representation_fingerprint'] == metric['fingerprint'], 'representation_mismatch')
            finite_vector(row['vector'], metric['dimension'], 'source vector')
            if row['attribution_status'] == 'synthetic_verified':
                require(row['actor_id'] is not None and row['review_receipt'] is not None,
                        'Attributed evidence needs original actor and review record')
            parent_key = (row['source_sha256'], row['parent_id'])
            require(parent_key not in used_parents, 'Repeated original parent requires a separately reviewed partition policy')
            used_parents.add(parent_key)
            # Exact lineage duplicates are rejected even under a new observation ID.
            unit = (row['source_sha256'], row['parent_id'], a, b)
            require(unit not in units, 'Duplicate source span')
            # Overlapping spans cannot acquire extra weight by fragmentation.
            for lo, hi in units.get((row['source_sha256'], row['parent_id']), []):
                require(b <= lo or a >= hi, 'Overlapping source spans')
            units[unit] = True
            units.setdefault((row['source_sha256'], row['parent_id']), []).append((a, b))
        else:
            require(row['vector'] is None and row['missing_reason'] is not None, 'Missing source cannot contain a vector')
    return validate_display(panel['display_space'], metric)


def _eligible(row, scope):
    if row['source_status'] != 'available':
        return row['source_status']
    if row['capacity'] != 'national':
        return 'non_national_capacity'
    if row['attribution_status'] != 'synthetic_verified' or row['country_iso3'] is None:
        return 'attribution_unverified'
    if row['genre'] not in scope['genres'] or any(row[k] != scope[k] for k in ('language', 'source_type', 'topic_id')):
        return 'scope_excluded'
    return None


def _profile(country, period, rows, panel):
    scope, metric = panel['scope'], panel['metric_space']
    candidates = [r for r in rows if r['country_iso3'] == country and r['period'] == period]
    selected = [r for r in candidates if _eligible(r, scope) is None]
    excluded = [{'observation_id': r['id'], 'reason': _eligible(r, scope)}
                for r in candidates if _eligible(r, scope) is not None]
    common = {'id': f'{country}/{period}', 'country_iso3': country, 'period': period,
              'scope_sha256': digest(scope), 'metric_fingerprint': metric['fingerprint'],
              'excluded': excluded, 'coverage': {'unit': 'source_observation',
              'inventory': len(candidates), 'included': len(selected), 'excluded': len(excluded)}}
    genres = {r['genre'] for r in selected}
    reason = None
    state = 'ready'
    if not candidates:
        state, reason = 'empty', 'country_missing'
    elif not selected:
        reasons = {r['reason'] for r in excluded}
        state = 'failed' if reasons & {'failed', 'inventory_failed'} else 'withheld'
        reason = ('attribution_unverified' if 'attribution_unverified' in reasons else
                  'source_unverified' if 'unverified' in reasons else
                  'source_failed' if state == 'failed' else 'no_eligible_country_sources')
    elif genres != set(scope['genres']):
        state, reason = 'withheld', 'scope_incompatible'
    vector, contributions = None, []
    if state == 'ready':
        grouped = defaultdict(lambda: defaultdict(list))
        for r in selected:
            grouped[r['genre']][r['meeting_id']].append(r)
        for genre in sorted(grouped):
            for meeting in sorted(grouped[genre]):
                group = sorted(grouped[genre][meeting], key=lambda r: r['id'])
                weight = 1.0 / len(scope['genres']) / len(grouped[genre]) / len(group)
                for row in group:
                    contributions.append({'observation_id': row['id'], 'weight': weight})
        rowmap = {r['id']: r for r in selected}
        vector = [math.fsum(c['weight'] * rowmap[c['observation_id']]['vector'][j]
                           for c in contributions) for j in range(metric['dimension'])]
    result = {**common, 'state': state, 'reason': reason, 'vector': vector,
              'contributions': contributions}
    result['sha256'] = digest(result)
    return result


def _project(country, us, display, gap):
    if display['state'] != 'ready':
        return {'state': 'withheld', 'reason': display['reason'], 'country_xy': None,
                'us_xy': None, 'relative_xy': None, 'visible_squared_gap_fraction': None,
                'fraction_reason': display['reason']}
    cols = list(map(list, zip(*display['basis'])))
    cxy = [dot(sub(country, display['center']), col) for col in cols]
    uxy = [dot(sub(us, display['center']), col) for col in cols]
    # Project the high-dimensional difference directly, avoiding cancellation.
    xy = [dot(sub(country, us), col) for col in cols]
    fraction = (math.hypot(*xy) / gap)**2 if gap > 0 else None
    return {'state': 'ready', 'reason': None, 'country_xy': cxy, 'us_xy': uxy,
            'relative_xy': xy, 'visible_squared_gap_fraction': fraction,
            'fraction_reason': None if gap > 0 else 'undefined_zero_gap'}


def build_us_reference(panel, receipt):
    """Build common-support contemporaneous comparisons from supplied synthetic data.

    No display filter argument exists: reference membership cannot change when a
    caller highlights another country. Invalid imports raise and return nothing.
    """
    display = validate_source(panel, receipt)
    scope, periods = panel['scope'], panel['periods']
    rows = sorted(panel['observations'], key=lambda r: r['id'])
    groups = defaultdict(list)
    for row in rows:
        groups[(row['country_iso3'], row['period'])].append(row)
    profiles = [_profile(c, p['id'], groups[(c, p['id'])], panel)
                for c in scope['countries'] for p in periods]
    by_profile = {(p['country_iso3'], p['period']): p for p in profiles}
    comparisons = []
    for c in scope['countries']:
        for p in periods:
            cp, up = by_profile[(c, p['id'])], by_profile[('USA', p['id'])]
            ready = cp['state'] == up['state'] == 'ready'
            comparison = {'id': f'{c}/{p["id"]}', 'country_iso3': c, 'period': p['id'],
                          'country_profile_sha256': cp['sha256'], 'us_profile_sha256': up['sha256'],
                          'state': 'ready' if ready else 'withheld',
                          'reason': None if ready else ('baseline_missing' if up['state'] != 'ready' else cp['reason']),
                          'distance': None, 'relative_vector': None, 'display': None}
            if ready:
                comparison.update(point_metrics(cp['vector'], up['vector']))
                comparison['display'] = _project(cp['vector'], up['vector'], display, comparison['distance'])
            comparisons.append(comparison)
    by_comparison = {(c['country_iso3'], c['period']): c for c in comparisons}
    transitions = []
    for c in scope['countries']:
        for a, b in zip(periods, periods[1:]):
            before, after = by_comparison[(c, a['id'])], by_comparison[(c, b['id'])]
            ready = before['state'] == after['state'] == 'ready'
            t = {'country_iso3': c, 'before': a['id'], 'after': b['id'],
                 'before_comparison_id': before['id'], 'after_comparison_id': after['id'],
                 'state': 'ready' if ready else 'withheld', 'reason': None if ready else 'endpoint_unavailable',
                 'metrics': None}
            if ready:
                t['metrics'] = transition_metrics(by_profile[(c, a['id'])]['vector'],
                    by_profile[(c, b['id'])]['vector'], by_profile[('USA', a['id'])]['vector'],
                    by_profile[('USA', b['id'])]['vector'])
            transitions.append(t)
    evidence = [{k: copy.deepcopy(r[k]) for k in OBS_KEYS if k != 'vector'} for r in rows]
    selection = {r['id']: _eligible(r, scope) for r in rows}
    metric_input_sha256 = digest({k:v for k,v in panel.items() if k != 'display_space'})
    result = {'schema': SCHEMA, 'version': VERSION, 'split': 'synthetic', 'hash_basis': HASH_BASIS,
              'identity': {**copy.deepcopy(panel['identity']), 'source_panel_sha256': digest(panel),
                           'metric_input_sha256': metric_input_sha256,
                           'comparison_set_id': digest({'source': metric_input_sha256, 'scope': scope}),
                           'consistency_receipt': copy.deepcopy(receipt)},
              'metric_space': copy.deepcopy(panel['metric_space']), 'display_space': display,
              'baseline': {'iso3': 'USA', 'mode': 'contemporaneous', 'attribution_rule': 'verified_national_capacity',
                           'profile_hashes': {p['id']: by_profile[('USA', p['id'])]['sha256'] for p in periods}},
              'scope': copy.deepcopy(scope), 'periods': copy.deepcopy(periods),
              'profiles': profiles, 'comparisons': comparisons, 'transitions': transitions, 'evidence': evidence,
              'coverage': {'unit': 'source_observation', 'inventory': len(rows),
                           'included': sum(v is None for v in selection.values()),
                           'excluded': sum(v is not None for v in selection.values()),
                           'source_status_counts': dict(sorted(Counter(r['source_status'] for r in rows).items())),
                           'exclusion_reasons': dict(sorted(Counter(v for v in selection.values() if v is not None).items()))},
              'uncertainty': {'state': 'withheld', 'reason': 'uncertainty_unavailable', 'interval': None},
              'sensitivity': {'state': 'withheld', 'reason': 'not_executed', 'attempts': []},
              'permissions': copy.deepcopy(PERMISSIONS)}
    result['sha256'] = digest(result)
    from .schema_contract import validate as validate_schema
    validate_schema(result)
    return result


def validate_result(result, panel, receipt):
    """Exact producer replay with independent input receipt; never self-authorizes."""
    expected = build_us_reference(panel, receipt)
    require(type(result) is dict and wire(result) == wire(expected), 'Read model differs from source-bound replay')
    return True


def select_comparisons(result, countries):
    """Pure display selection: returns copies, never changes profiles or reference."""
    require(type(countries) is list and len(set(countries)) == len(countries)
            and all(c in result['scope']['countries'] for c in countries), 'Invalid display country selection')
    return copy.deepcopy([row for row in result['comparisons'] if row['country_iso3'] in countries])


def adapt_w4(panel, annotations, plan, producer_receipt):
    """Read-only W4 boundary. Annotation/plan must carry an external synthetic receipt.

    W4 does not authenticate country representational capacity. Keep an explicit
    country annotation ledger rather than treating actor_id or speech text as ISO3.
    This adapter intentionally does not open files or accept development panels.
    """
    require(type(panel) is dict and panel.get('split') == 'synthetic', 'Only synthetic W4 input is allowed')
    # Importing the existing validator must succeed; no weak local fallback.
    from research.longitudinal import framework as w4
    w4.validate_panel(panel)
    exact(plan, ['identity', 'metric_space', 'display_space', 'scope'], 'adapter plan')
    exact(producer_receipt, ['kind', 'panel_sha256', 'annotations_sha256', 'plan_sha256'], 'W4 receipt')
    require(producer_receipt['kind'] == 'synthetic_consistency_only' and
            producer_receipt['panel_sha256'] == w4.digest(panel) and
            producer_receipt['annotations_sha256'] == digest(annotations) and
            producer_receipt['plan_sha256'] == digest(plan), 'W4 receipt mismatch')
    require(type(annotations) is dict and set(annotations) == {r['id'] for r in panel['observations']},
            'Complete country attribution ledger required')
    require(plan['identity']['producer_panel_sha256'] == w4.digest(panel), 'Original W4 identity lost')
    require(all(plan['metric_space'][k] == panel['feature_space'][k] for k in ('id', 'version', 'dimension')) and
            plan['metric_space']['upstream_fingerprint'] == panel['feature_space']['fingerprint'] and
            panel['feature_space']['fit_policy'] == 'transformed_reference', 'Frozen W4 representation required')
    observations = []
    for row in panel['observations']:
        annotation = annotations[row['id']]
        exact(annotation, ['country_iso3', 'capacity', 'attribution_status', 'review_receipt',
                           'language', 'source_type', 'topic_id', 'source_pointer'], 'country annotation')
        # Preserve original actor/person/speech and source identities; do not mutate panel.
        item = {k: copy.deepcopy(row.get(k)) for k in OBS_KEYS}
        item.update(copy.deepcopy(annotation))
        item['representation_fingerprint'] = plan['metric_space']['fingerprint'] if row['source_status'] == 'available' else None
        observations.append(item)
    source = {'schema': INPUT_SCHEMA, 'split': 'synthetic', **copy.deepcopy(plan),
              'periods': copy.deepcopy(panel['periods']), 'observations': observations}
    # The upstream W4 fingerprint is retained separately in the producer identity
    # through its exact full-panel hash; sidecar descriptor has its own fingerprint.
    receipt = {'kind': 'synthetic_consistency_only', 'hash_basis': HASH_BASIS, 'panel_sha256': digest(source)}
    validate_source(source, receipt)
    return source, receipt
