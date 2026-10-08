"""Synthetic-first longitudinal source-aware latent-structure diagnostics (W4).

No corpus loader, trained model, political inference, network access or publication gate.
Requires numpy; optional scipy for globally optimal cluster label correspondence.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import pdist

SCHEMA = 'un.longitudinal-panel.v1'
SHA = set('0123456789abcdef')


class ContractError(ValueError):
    """Incomplete or incompatible source and representation lineage."""


class AlignmentError(ContractError):
    """Anchor selection or Procrustes fit does not identify a defensible alignment."""


def require(condition, message, error=ContractError):
    if not condition:
        raise error(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode('utf-8')).hexdigest()


def hash_ok(value):
    return isinstance(value, str) and len(value) == 64 and set(value) <= SHA


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate_panel(panel):
    """Refuse ambiguous representations, source lineage, dates and missingness.

    This is a strict input adapter; it does not assert provenance authenticity.
    A real-data producer must validate against its upstream source hash ledger.
    """
    require(isinstance(panel, dict) and panel.get('schema') == SCHEMA, 'Panel schema is not supported')
    require(panel.get('split') in ('synthetic', 'development'), 'Only synthetic/development splits allowed')
    periods = panel.get('periods')
    require(isinstance(periods, list) and len(periods) >= 2, 'At least two declared periods required')
    by_period = {}
    for p in periods:
        require(isinstance(p, dict) and nonempty(p.get('id')) and p['id'] not in by_period,
                'Period IDs must be unique and nonempty')
        try:
            start, end = date.fromisoformat(p['start']), date.fromisoformat(p['end'])
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError('Period bounds must be ISO dates') from exc
        require(start <= end, 'Reversed period')
        by_period[p['id']] = (start, end)
    ordered = sorted(by_period.items(), key=lambda item: item[1][0])
    require(all(ordered[i][1][1] < ordered[i + 1][1][0] for i in range(len(ordered) - 1)),
            'Overlapping periods are not comparable')
    feat = panel.get('feature_space', {})
    for key in ('id', 'version', 'fingerprint'):
        require(nonempty(feat.get(key)), f'Missing feature-space {key}')
    require(hash_ok(feat['fingerprint']), 'Feature fingerprint must be SHA-256')
    require(feat.get('fit_policy') in ('transformed_reference', 'full_refit'), 'Unknown fit policy')
    d = feat.get('dimension')
    require(type(d) is int and d >= 2 and d <= 1024, 'Invalid high-dimensional feature count')
    maps = panel.get('map_space', {})
    q = maps.get('dimension')
    require(type(q) is int and 2 <= q <= min(10, d), 'Invalid display map dimension')
    require(nonempty(maps.get('method')), 'Display method must be declared')
    rows = panel.get('observations')
    require(isinstance(rows, list) and 0 < len(rows) <= 20000, 'Invalid number of observations')
    seen = set()
    meetings, actors = {}, {}
    for r in rows:
        require(isinstance(r, dict) and nonempty(r.get('id')) and r['id'] not in seen,
                'Observation IDs must be unique')
        seen.add(r['id'])
        require(r.get('period') in by_period, f"{r['id']}: unknown period")
        try:
            when = date.fromisoformat(r['date'])
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError(f"{r['id']}: missing/invalid source date") from exc
        require(by_period[r['period']][0] <= when <= by_period[r['period']][1],
                f"{r['id']}: source date outside period")
        require(panel['split'] != 'development' or str(when) not in ('2026-10-05', '2026-10-06'),
                'Reserved holdout dates cannot enter the development adapter')
        require(nonempty(r.get('genre')) and nonempty(r.get('meeting_id')) and
                nonempty(r.get('source_family_id')), f"{r['id']}: meeting/genre/source lineage missing")
        require(hash_ok(r.get('text_sha256')) and hash_ok(r.get('source_sha256')),
                f"{r['id']}: invalid text/source hash")
        require(r.get('source_hash_basis') in ('synthetic', 'utf8_response_text',
                    'raw_response_bytes', 'canonical_source_text', 'source_text_file_bytes',
                    'utf8_corpus_export'), f"{r['id']}: source hash basis missing")
        require(r.get('representation_fingerprint') == feat['fingerprint'],
                f"{r['id']}: vocabulary, embedding or preprocessing basis changed")
        require(r.get('representation_id') == feat['id'] and
                r.get('representation_version') == feat['version'],
                f"{r['id']}: representation identity changed")
        require(r.get('actor_kind') in ('synthetic', 'verified_speaker', 'recorded_affiliation',
                'unknown'), f"{r['id']}: ambiguous actor evidence")
        require(r.get('actor_id') is None or nonempty(r.get('actor_id')),
                f"{r['id']}: invalid actor identity")
        require(r['actor_kind'] != 'verified_speaker' or nonempty(r.get('speaker_id')),
                f"{r['id']}: speaker identity lacks verification")
        require(r['actor_kind'] != 'unknown' or r.get('actor_id') is None,
                f"{r['id']}: unknown actor cannot be assigned a verified ID")
        if r.get('actor_id') is not None:
            identity = (r['actor_kind'], r.get('speaker_id') if r['actor_kind'] == 'verified_speaker' else None)
            require(actors.setdefault(r['actor_id'], identity) == identity,
                    f"{r['id']}: inconsistent actor identity across periods")
        meeting = (r['period'], r['source_family_id'], r['source_sha256'], r['source_hash_basis'])
        require(meetings.setdefault(r['meeting_id'], meeting) == meeting,
                f"{r['id']}: meeting reused for incompatible source or period")
        require(r.get('source_status') in ('available', 'unavailable', 'failed', 'empty_transcript',
                'inventory_failed', 'excluded_language'), f"{r['id']}: missing source status")
        require(r.get('parent_id') is None or hash_ok(r.get('parent_text_sha256')),
                f"{r['id']}: parent hash required")
        off1, off2 = r.get('start'), r.get('end')
        require((off1 is None and off2 is None) or
                (type(off1) is int and type(off2) is int and 0 <= off1 < off2),
                f"{r['id']}: inconsistent Unicode offsets")
        c = r.get('cluster')
        require(c is None or (type(c) is int and c >= 0), f"{r['id']}: bad cluster label")
        if c is not None:
            require(nonempty(r.get('cluster_fit_id')) and
                    hash_ok(r.get('cluster_parameters_sha256')) and
                    hash_ok(r.get('cluster_training_selection_sha256')),
                    f"{r['id']}: imported cluster label lacks original fit/parameter/selection identity")
        if panel['split'] == 'development':
            require(r.get('unit') in ('source_segment', 'passage', 'reviewed_speech', 'parent', 'country_period')
                    and r.get('review_status') in ('confirmed', 'pending', 'provisional', 'unreviewed'),
                    f"{r['id']}: development unit/review status not declared")
            require(r.get('speech_id') is None or
                    (r['review_status'] == 'confirmed' and nonempty(r['speech_id'])),
                    f"{r['id']}: unconfirmed speech identity")
        if r['source_status'] == 'available':
            require(not r.get('missing_reason'), f"{r['id']}: available source has missing reason")
            require(nonempty(r.get('map_fit_id')), f"{r['id']}: map fit provenance absent")
            for name, count in (('vector', d), ('map', q)):
                x = r.get(name)
                require(isinstance(x, list) and len(x) == count and
                        all(type(v) in (float, int) and math.isfinite(v) for v in x),
                        f"{r['id']}: missing/nonfinite {name} or changed dimension")
        else:
            require(nonempty(r.get('missing_reason')) and r.get('vector') is None and
                    r.get('map') is None and c is None,
                    f"{r['id']}: missing source must not have fabricated vectors/labels")
    available = [r for r in rows if r['source_status'] == 'available']
    ids_by_period = defaultdict(set)
    for r in available:
        ids_by_period[r['period']].add(r['map_fit_id'])
    require(all(len(ids_by_period[p]) == 1 for p in by_period),
            'Exactly one pinned map fit per nonempty period required')
    imported_fits = defaultdict(set)
    for r in available:
        if r['cluster'] is not None:
            imported_fits[r['period']].add((r['cluster_fit_id'],
                r['cluster_parameters_sha256'], r['cluster_training_selection_sha256']))
    require(all(len(fits) <= 1 for fits in imported_fits.values()),
            'Incompatible imported clustering fits within the same period')
    if feat['fit_policy'] == 'transformed_reference':
        require(len(set.union(*ids_by_period.values())) == 1,
                'Transformed-reference comparisons must use exactly the same saved map fit')
    require(all(r['source_hash_basis'] == 'synthetic' for r in rows) if panel['split'] == 'synthetic'
            else all(r['source_hash_basis'] != 'synthetic' for r in rows),
            'Synthetic and non-synthetic hash bases cannot be mixed')
    return {'periods': [p for p, _ in ordered], 'available': len(available), 'excluded': len(rows) - len(available),
            'representation_id': feat['id'], 'source_groups': len({r['source_family_id'] for r in available})}


def _aggregates(rows, key, genre_intersection=None):
    """Equal meeting weight within genre; equal genre weight for actor-period."""
    grouped = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r['source_status'] != 'available' or r.get('actor_id') is None:
            continue
        if genre_intersection is not None and r['genre'] not in genre_intersection.get(r[key], set()):
            continue
        grouped[r[key]][(r['genre'], r['meeting_id'])].append(np.asarray(r['vector'], dtype=float))
    result = {}
    for unit, meetings in grouped.items():
        genres = defaultdict(list)
        for (genre, _), vectors in meetings.items():
            genres[genre].append(np.mean(vectors, axis=0))
        result[unit] = np.mean([np.mean(v, axis=0) for v in genres.values()], axis=0)
    return result


def _actor_map(rows, period, vector_key='vector', allowed_genres=None, family=None):
    groups = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r['period'] != period or r['source_status'] != 'available' or r.get('actor_id') is None:
            continue
        if family is not None and r['source_family_id'] != family:
            continue
        if allowed_genres is not None and r['genre'] not in allowed_genres.get(r['actor_id'], set()):
            continue
        groups[r['actor_id']][(r['genre'], r['meeting_id'])].append(np.asarray(r[vector_key], dtype=float))
    out = {}
    for actor, meetings in groups.items():
        genres = defaultdict(list)
        for (genre, _), vectors in meetings.items():
            genres[genre].append(np.mean(vectors, axis=0))
        out[actor] = np.mean([np.mean(z, axis=0) for z in genres.values()], axis=0)
    return out


def matched_genres(rows, before, after):
    observed = defaultdict(set)
    for r in rows:
        if r['source_status'] == 'available' and r.get('actor_id') is not None:
            observed[(r['period'], r['actor_id'])].add(r['genre'])
    actors = sorted({a for p, a in observed if p == before} &
                    {a for p, a in observed if p == after})
    return {a: observed[(before, a)] & observed[(after, a)] for a in actors}


def actor_distances(rows, before, after):
    genres = matched_genres(rows, before, after)
    genres = {a: g for a, g in genres.items() if g}
    a = _actor_map(rows, before, allowed_genres=genres)
    b = _actor_map(rows, after, allowed_genres=genres)
    distances = []
    for actor in sorted(genres):
        x, y = a[actor], b[actor]
        norm_x, norm_y = np.linalg.norm(x), np.linalg.norm(y)
        cosine = None if min(norm_x, norm_y) < 1e-12 else float(np.clip(1 - np.dot(x, y) / (norm_x * norm_y), 0, 2))
        distances.append({'actor_id': actor, 'matched_genres': sorted(genres[actor]),
                          'euclidean': float(np.linalg.norm(y - x)), 'cosine': cosine,
                          'chord': None if cosine is None else float(math.sqrt(2 * cosine)),
                          'before_norm': float(norm_x), 'after_norm': float(norm_y)})
    before_all = _actor_map(rows, before)
    after_all = _actor_map(rows, after)
    def centroid(value):
        return np.mean(list(value.values()), axis=0) if value else None
    whole_a, whole_b = centroid(before_all), centroid(after_all)
    whole = None if whole_a is None or whole_b is None else float(np.linalg.norm(whole_b - whole_a))
    diff = [b[actor] - a[actor] for actor in sorted(genres)]
    matched = float(np.linalg.norm(np.mean(diff, axis=0))) if diff else None
    return {'rows': distances, 'matched_actor_count': len(genres),
            'genre_incompatible_actors': sorted(set(matched_genres(rows, before, after)) - set(genres)),
            'arrived_actors': sorted(set(after_all) - set(before_all)),
            'departed_actors': sorted(set(before_all) - set(after_all)),
            'all_actor_centroid_distance': whole, 'common_actor_centroid_distance': matched,
            'mean_within_actor_distance': float(np.mean([r['euclidean'] for r in distances])) if distances else None,
            'before_actor_count': len(before_all), 'after_actor_count': len(after_all)}


def common_source_distances(rows, before, after):
    families = sorted({r['source_family_id'] for r in rows if r['period'] == before and r['source_status'] == 'available'} &
                      {r['source_family_id'] for r in rows if r['period'] == after and r['source_status'] == 'available'})
    pairs = []
    for family in families:
        subset = [r for r in rows if r['source_family_id'] == family]
        d = actor_distances(subset, before, after)
        for r in d['rows']:
            pairs.append({'source_family_id': family, **r})
    return {'matched_source_families': families, 'actor_family_pairs': pairs,
            'pair_count': len(pairs),
            'mean_distance': float(np.mean([r['euclidean'] for r in pairs])) if pairs else None}


def procrustes(before, after, *, allow_reflection=False, max_condition=1e7,
               max_relative_rmse=0.15):
    """Rigid after-to-before map; independently predeclared full-rank anchors only."""
    a = np.asarray(before, dtype=float)
    b = np.asarray(after, dtype=float)
    require(a.ndim == b.ndim == 2 and a.shape == b.shape and np.isfinite(a).all()
            and np.isfinite(b).all(), 'Matched finite anchor matrices required', AlignmentError)
    n, dim = a.shape
    require(n >= dim + 2, 'Need at least dimension + 2 stable anchors', AlignmentError)
    ac, bc = a.mean(axis=0), b.mean(axis=0)
    aa, bb = a - ac, b - bc
    sa, sb = np.linalg.svd(aa, compute_uv=False), np.linalg.svd(bb, compute_uv=False)
    require(sa[-1] > 1e-8 * sa[0] and sb[-1] > 1e-8 * sb[0],
            'Degenerate or rank-deficient anchor geometry', AlignmentError)
    u, s, vt = np.linalg.svd(bb.T @ aa)
    require(s[-1] > 1e-12 * s[0] and s[0] / s[-1] <= max_condition,
            'Unstable cross-anchor rotation spectrum', AlignmentError)
    orient = np.eye(dim)
    if not allow_reflection and np.linalg.det(u @ vt) < 0:
        orient[-1, -1] = -1
    rot = u @ orient @ vt
    translation = ac - bc @ rot
    fitted = b @ rot + translation
    residual = np.linalg.norm(fitted - a, axis=1)
    radius = float(np.sqrt(np.mean(np.sum(aa ** 2, axis=1))))
    rel = float(np.sqrt(np.mean(residual ** 2)) / max(radius, 1e-12))
    require(rel <= max_relative_rmse, f'Anchor residual {rel:.4g} exceeds preregistered {max_relative_rmse}', AlignmentError)
    return {'rotation': rot, 'translation': translation, 'anchor_residuals': residual,
            'anchor_rmse': float(np.sqrt(np.mean(residual ** 2))),
            'anchor_relative_rmse': rel, 'singular_values': s.tolist(),
            'condition_number': float(s[0] / s[-1]),
            'scale_ratio': float(np.linalg.norm(bb) / np.linalg.norm(aa)),
            'reflection_applied': bool(np.linalg.det(rot) < 0),
            'scaling_applied': False, 'anchor_count': n}


def align_maps(rows, before, after, fit_policy, anchor_ids=(), max_anchor_relative_rmse=0.15):
    data = [r for r in rows if r['source_status'] == 'available']
    if fit_policy == 'transformed_reference':
        return {r['id']: np.asarray(r['map'], dtype=float) for r in data}, {
            'mode': 'identity_pinned_transform', 'anchor_count': 0,
            'anchor_relative_rmse': 0.0, 'scaling_applied': False,
            'limitation': 'Coordinates share exactly one pinned fitted transform; display only.'}
    require(len(anchor_ids) == len(set(anchor_ids)) and len(anchor_ids) > 0,
            'Explicit distinct, externally justified stable anchors required', AlignmentError)
    genres = matched_genres(data, before, after)
    require(all(a in genres and genres[a] for a in anchor_ids),
            'Anchor missing or has changed genre/source coverage', AlignmentError)
    x = _actor_map(data, before, vector_key='map', allowed_genres=genres)
    y = _actor_map(data, after, vector_key='map', allowed_genres=genres)
    fit = procrustes([x[a] for a in anchor_ids], [y[a] for a in anchor_ids],
                     max_relative_rmse=max_anchor_relative_rmse)
    aligned = {r['id']: np.asarray(r['map'], dtype=float) @ fit['rotation'] + fit['translation']
               if r['period'] == after else np.asarray(r['map'], dtype=float) for r in data}
    diag = {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in fit.items()}
    diag.update({'mode': 'rigid_full_refit', 'anchor_ids': list(anchor_ids),
                 'limitation': 'Stable anchors are an external assumption; rotation does not identify political movement.'})
    return aligned, diag


def display_stress(rows, period):
    selected = [r for r in rows if r['period'] == period and r['source_status'] == 'available']
    if len(selected) < 3:
        return {'stress': None, 'reason': 'fewer_than_three_rows'}
    # Bounded observed-row sample prevents O(n^2) use; repeated source families are retained.
    selected = selected[:min(len(selected), 250)]
    hi = pdist([r['vector'] for r in selected]); lo = pdist([r['map'] for r in selected])
    if np.dot(hi, hi) < 1e-20 or np.dot(lo, lo) < 1e-20:
        return {'stress': None, 'reason': 'degenerate_pairwise_distances'}
    scale = float(np.dot(hi, lo) / np.dot(lo, lo))
    return {'stress': float(np.linalg.norm(hi - scale * lo) / np.linalg.norm(hi)),
            'rescaling_for_diagnostic_only': scale, 'sampled_observations': len(selected),
            'reason': None}


def _actor_labels(rows, period):
    labels = defaultdict(list)
    for r in rows:
        if r['period'] == period and r['source_status'] == 'available' and r.get('actor_id'):
            labels[r['actor_id']].append(r['cluster'])
    out = {}
    for actor, membership in labels.items():
        counts = Counter(v for v in membership if v is not None and v > 0)
        # Ties, noise, missing cluster and mixed assignment -> explicitly abstain.
        if not counts:
            out[actor] = 0 if 0 in membership else None
        else:
            top = max(counts.values())
            winners = [k for k, n in counts.items() if n == top]
            out[actor] = (winners[0] if len(winners) == 1 and top > len(membership) / 2
                          else (0 if 0 in membership else None))
    return out


def cluster_correspondence(rows, before, after, min_overlap=2):
    a, b = _actor_labels(rows, before), _actor_labels(rows, after)
    shared = sorted(set(a) & set(b))
    ta, tb = sorted({v for v in a.values() if v is not None and v > 0}), sorted({v for v in b.values() if v is not None and v > 0})
    matrix = np.array([[sum(a[x] == i and b[x] == j for x in shared) for j in tb]
                       for i in ta], dtype=int)
    edges = [{'before': i, 'after': j, 'shared_overlap': int(matrix[ii, jj]),
              'share_of_prior_common': float(matrix[ii, jj] / max(1, sum(a[x] == i for x in shared))),
              'share_of_next_common': float(matrix[ii, jj] / max(1, sum(b[x] == j for x in shared)))}
             for ii, i in enumerate(ta) for jj, j in enumerate(tb) if matrix[ii, jj] > 0]
    matched = []
    if len(ta) and len(tb):
        # Labels are arbitrary, Hungarian assignment is descriptive only.
        rr, cc = linear_sum_assignment(-matrix)
        matched = [{'before': ta[i], 'after': tb[j], 'shared_overlap': int(matrix[i, j])}
                   for i, j in zip(rr, cc) if matrix[i, j] >= min_overlap]
    supported = [e for e in edges if e['shared_overlap'] >= min_overlap]
    return {'shared_actor_count': len(shared), 'before_clusters': ta, 'after_clusters': tb,
            'eligible_shared_assigned': sum(a[x] is not None and a[x] > 0 and b[x] is not None and b[x] > 0 for x in shared),
            'unassigned_before': sum(a[x] == 0 for x in shared),
            'unassigned_after': sum(b[x] == 0 for x in shared),
            'not_fitted_before': sum(a[x] is None for x in shared),
            'not_fitted_after': sum(b[x] is None for x in shared),
            'overlap_edges': edges, 'max_overlap_matching': matched,
            'persistent_candidates': matched,
            'splits': [v for v in ta if sum(e['before'] == v for e in supported) > 1],
            'merges': [v for v in tb if sum(e['after'] == v for e in supported) > 1],
            'without_supported_successor': [v for v in ta if not any(e['before'] == v for e in supported)],
            'without_supported_predecessor': [v for v in tb if not any(e['after'] == v for e in supported)],
            'arrived_actors': sorted(set(b) - set(a)), 'departed_actors': sorted(set(a) - set(b)),
            'minimum_overlap': min_overlap,
            'limitation': 'Descriptive memberships, including roster turnover; split/merge not political evidence.'}


def grouped_bootstrap(rows, before, after, *, repetitions=200, seed=30092026, minimum_groups=6):
    """Resample complete source families jointly across periods, never passages.

    Percentile spread is resampling sensitivity under an assumed independently
    sampled source-family design, NOT a calibrated confidence interval.
    """
    require(type(repetitions) is int and 50 <= repetitions <= 3000, 'Bootstrap repetitions must be 50..3000')
    require(type(seed) is int and 0 <= seed < 2**63, 'Invalid bootstrap seed')
    family = defaultdict(list)
    for r in rows:
        if r['period'] in (before, after) and r['source_status'] == 'available':
            family[r['source_family_id']].append(r)
    groups = sorted(family)
    spanning = [f for f in groups if {r['period'] for r in family[f]} == {before, after}]
    if len(spanning) < minimum_groups or len(spanning) != len(groups):
        return {'status': 'withheld', 'reason': 'insufficient_independent_paired_source_families',
                'attempted': 0, 'successful': 0, 'failed': 0, 'available_groups': len(groups),
                'paired_groups': len(spanning), 'percentile_interval': None}
    base = actor_distances(rows, before, after)
    if not base['matched_actor_count']:
        return {'status': 'withheld', 'reason': 'no_matched_actors', 'attempted': 0,
                'successful': 0, 'failed': 0, 'available_groups': len(groups), 'percentile_interval': None}
    rng = np.random.default_rng(seed)
    values, failures, compositions = [], Counter(), []
    for _ in range(repetitions):
        selection = rng.choice(groups, size=len(groups), replace=True)
        sample = [r for f in selection for r in family[f]]
        result = actor_distances(sample, before, after)
        if result['matched_actor_count'] < 2 or result['common_actor_centroid_distance'] is None:
            failures['insufficient_matched_actors'] += 1
            continue
        values.append(result['common_actor_centroid_distance'])
        compositions.append(result['matched_actor_count'])
    failure_rate = 1 - len(values) / repetitions
    if len(values) < 50 or failure_rate > 0.20:
        return {'status': 'withheld', 'reason': 'insufficient_successful_resamples',
                'attempted': repetitions, 'successful': len(values),
                'failed': repetitions - len(values), 'failure_reasons': dict(failures),
                'available_groups': len(groups), 'percentile_interval': None}
    return {'status': 'sensitivity_only', 'unit': 'paired_source_family', 'seed': seed,
            'attempted': repetitions, 'successful': len(values), 'failed': repetitions - len(values),
            'failure_reasons': dict(failures), 'available_groups': len(groups),
            'matched_actors_original': base['matched_actor_count'],
            'matched_actors_resampled_range': [min(compositions), max(compositions)],
            'point_estimate': base['common_actor_centroid_distance'],
            'std': float(np.std(values, ddof=1)),
            'percentile_interval': [float(v) for v in np.quantile(values, [0.025, 0.975])],
            'interpretation': 'Descriptive source-group resampling sensitivity, not a calibrated confidence region.'}


def compare(panel, before, after, *, anchor_ids=(), bootstrap_reps=200, bootstrap_seed=30092026,
            max_anchor_relative_rmse=0.15, min_cluster_overlap=2):
    metadata = validate_panel(panel)
    require(before != after and before in metadata['periods'] and after in metadata['periods'],
            'Comparison periods must be distinct and declared')
    indices = {p: i for i, p in enumerate(metadata['periods'])}
    require(indices[before] < indices[after], 'Comparison must move forward in time')
    rows = [r for r in panel['observations'] if r['period'] in (before, after)]
    high = actor_distances(rows, before, after)
    matched_source = common_source_distances(rows, before, after)
    aligned, transform = align_maps(rows, before, after, panel['feature_space']['fit_policy'],
                                    anchor_ids, max_anchor_relative_rmse)
    maps = [{**r, 'vector': aligned[r['id']].tolist()} for r in rows
            if r['source_status'] == 'available']
    mapped = actor_distances(maps, before, after)
    clusters = cluster_correspondence(rows, before, after, min_cluster_overlap)
    boot = grouped_bootstrap(rows, before, after, repetitions=bootstrap_reps, seed=bootstrap_seed)
    coords = [{'observation_id': r['id'], 'period': r['period'], 'actor_id': r.get('actor_id'),
               'source_family_id': r['source_family_id'], 'meeting_id': r['meeting_id'],
               'map_fit_id': r['map_fit_id'], 'coordinate_kind': 'aligned_display_only',
               'coordinates': aligned[r['id']].tolist()} for r in rows if r['id'] in aligned]
    return {'schema': 'un.longitudinal-comparison.v1', 'evaluation_role': 'engineering_only',
            'publication_eligible': False, 'split': panel['split'], 'before': before, 'after': after,
            'representation': {**panel['feature_space'], 'map_method': panel['map_space']['method']},
            'provenance': {'panel_sha256': digest(panel), 'included_observation_ids': [r['id'] for r in rows]},
            'coverage': {**metadata, 'compared_available': len(coords),
                         'unavailable_by_period': {p: sum(r['period'] == p and r['source_status'] != 'available'
                                                         for r in rows) for p in (before, after)}},
            'high_dimensional': high, 'common_source': matched_source,
            'alignment': transform, 'display': {'actor_distances': mapped['rows'],
                'common_actor_centroid_distance': mapped['common_actor_centroid_distance'],
                'stress': {p: display_stress(rows, p) for p in (before, after)},
                'movement_is_inferential': False},
            'cluster_correspondence': clusters, 'uncertainty': boot, 'aligned_coordinates': coords,
            'limitations': ['Period-specific roster and genre shift can change pooled centroids without individual drift.',
                'Source family independence is an assumption, not verified from UN transcripts.',
                'Anchor invariance and adequate geometry are required for full refits.',
                '2D display movement, cluster labels and resampling spread are not political change or significance.',
                'No historical change-point inference: M24 independent-Gaussian observation-index prerequisites not met.',
                'No M26/driftmapR calibration or inference is asserted.']}


def to_interchange_v1(panel, comparison, *, upstream=None):
    """W4 adapter to the coordinator's un.parallel-analysis.v1 (1.0.0).

    Caller must supply original source/selection hashes for real development data.
    Does not fit or reclassify any model and never exports original text.
    """
    from datetime import datetime, timezone
    validate_panel(panel)
    require(comparison['provenance']['panel_sha256'] == digest(panel), 'Comparison belongs to another panel')
    rows = [r for r in panel['observations'] if r['period'] in (comparison['before'], comparison['after'])]
    synthetic = panel['split'] == 'synthetic'
    if not synthetic:
        require(isinstance(upstream, dict) and upstream.get('source_schema') in
                ('un.browser.corpus.v1', 'un.passage-corpus.v1', 'un.latent-comparison.v1', 'un.review.v1'),
                'Development export requires verified original upstream metadata')
        require(hash_ok(upstream.get('source_sha256')) and hash_ok(upstream.get('selection_sha256')),
                'Development export must carry original source and selection hashes')
        require(nonempty(upstream.get('source_engine')) and
                all(r['source_hash_basis'] == upstream.get('source_hash_basis') for r in rows),
                'Upstream hash basis must exactly match original observation basis')
    else:
        upstream = {'source_schema': 'synthetic.v1', 'source_engine': 'W4 synthetic longitudinal fixture',
                    'source_hash_basis': 'synthetic',
                    'source_sha256': digest([[r['id'], r['source_sha256']] for r in rows]),
                    'selection_sha256': digest([r['id'] for r in rows]),
                    'frame_sha256': None, 'corpus_sha256': None, 'review_sha256': None,
                    'missing_reason': None}
    eligible = [r for r in rows if r['source_status'] == 'available']
    period_ids = (comparison['before'], comparison['after'])
    models, results, coverage = [], [], []
    for p in period_ids:
        ident = f'W4-imported-{p}'
        label_fit = next((r for r in eligible if r['period'] == p and r['cluster'] is not None), None)
        models.append({'model_id': ident, 'method_family': 'imported_partition',
                       'method': 'saved_source_linked_cluster_assignment',
                       'representation_id': panel['feature_space']['id'],
                       'representation_version': panel['feature_space']['version'],
                       'fit_version': label_fit['cluster_fit_id'] if label_fit else 'no_imported_fit',
                       'fit_split': panel['split'],
                       'parameters_sha256': label_fit['cluster_parameters_sha256'] if label_fit else
                                            digest({'period': p, 'kind': 'no_imported_fit'}),
                       'training_selection_sha256': label_fit['cluster_training_selection_sha256'] if label_fit
                                                    else upstream['selection_sha256'],
                       'diagnostic_basis': 'Imported partition fit identity; never the display map fit. '
                                           'Upstream attempt/failure validation required separately.'})
        counts = Counter()
        for r in rows:
            if r['source_status'] != 'available':
                status, cluster, reason = 'excluded', None, r['missing_reason']
            elif r['period'] != p or r['cluster'] is None:
                status, cluster, reason = 'not_fitted', None, ('outside_model_period' if r['period'] != p else 'no_imported_assignment')
            elif r['cluster'] == 0:
                status, cluster, reason = 'unassigned', 0, 'imported_noise_or_abstention'
            else:
                status, cluster, reason = 'assigned', r['cluster'], None
            counts[status] += 1
            results.append({'model_id': ident, 'observation_id': r['id'], 'status': status,
                            'cluster': cluster, 'membership_kind': 'none', 'memberships': None,
                            'membership_strength': None,
                            'representation_basis_id': panel['feature_space']['id'], 'reason': reason})
        coverage.append({'model_id': ident, 'eligible': len(eligible), 'assigned': counts['assigned'],
                         'unassigned': counts['unassigned'], 'not_fitted': counts['not_fitted'],
                         'excluded': counts['excluded'], 'attempted_fits': 0,
                         'successful_fits': 0, 'failed_fits': 0})
    from pathlib import Path
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    observations = []
    for r in rows:
        observations.append({'id': r['id'], 'text_sha256': r['text_sha256'],
            'parent_id': r.get('parent_id'), 'parent_text_sha256': r.get('parent_text_sha256'),
            'meeting_id': r['meeting_id'], 'speech_id': r.get('speech_id') if r.get('review_status') == 'confirmed' else None,
            'source_family_id': r['source_family_id'], 'date': r['date'], 'country': r.get('country'),
            'source_url': r.get('source_url'), 'json_pointer': r.get('json_pointer'),
            'start': r.get('start'), 'end': r.get('end'),
            'unit': 'synthetic' if synthetic else r.get('unit', 'source_segment'),
            'review_status': 'not_applicable' if synthetic else r.get('review_status', 'unreviewed'),
            'exclusion_reasons': [] if r['source_status'] == 'available' else [r['source_status']],
            'source_status': r['source_status'], 'missing_reason': r.get('missing_reason')})
    diagnostics = [{'model_id': None, 'name': 'matched_actors',
        'value': comparison['high_dimensional']['matched_actor_count'],
        'denominator': len({r['actor_id'] for r in eligible if r.get('actor_id')}),
        'unit': 'recorded_actor', 'status': 'descriptive', 'reason': None},
        {'model_id': None, 'name': 'bootstrap_status', 'value': comparison['uncertainty']['status'],
         'denominator': comparison['uncertainty']['attempted'], 'unit': 'resamples',
         'status': 'descriptive' if comparison['uncertainty']['status'] == 'sensitivity_only' else 'withheld',
         'reason': comparison['uncertainty'].get('reason')}]
    return {'schema': 'un.parallel-analysis.v1', 'contract_version': '1.0.0',
        'producer': {'workstream_id': 'W4', 'adapter_version': '0.1.0',
                     'code_sha256': code_hash, 'runtime': f'python-numpy-{np.__version__}',
                     'generated_at': datetime.now(timezone.utc).isoformat(),
                     'fixture_kind': 'synthetic' if synthetic else 'private_development'},
        'upstream': upstream,
        'cohort': {'split': panel['split'], 'population': 'longitudinal_' + comparison['before'] + '_' + comparison['after'],
                   'unit': 'synthetic' if synthetic else rows[0].get('unit', 'source_segment'),
                   'selection_policy': 'source-validated period pair; missing retained',
                   'weighting': 'equal_meeting', 'source_group_unit': 'source_family',
                   'duplicate_policy': 'retain_and_audit', 'total_in_frame': len(rows), 'eligible': len(eligible)},
        'observations': observations, 'models': models, 'results': results,
        'coverage': {'inventory_meetings': len({r['meeting_id'] for r in rows}),
                     'observations_total': len(rows), 'eligible': len(eligible),
                     'excluded': len(rows) - len(eligible),
                     'unavailable_sources': len({r['source_family_id'] for r in rows if r['source_status'] != 'available'}),
                     'models': coverage, 'failure_ledger': []},
        'evidence': [], 'diagnostics': diagnostics,
        'limitations': [{'code': 'descriptive_longitudinal_only', 'scope': 'all',
                         'description': 'Synthetic-first comparisons; no validated political or calibrated inferential movement.'},
                        {'code': 'resampling_assumption', 'scope': 'uncertainty',
                         'description': 'Independent paired-source-family sampling is unverified; percentile spread is sensitivity only.'}],
        'publication_eligible': False, 'evaluation_role': 'engineering_only'}


def write_exports(folder, comparison, envelope):
    """Create new output directory and export text-free coordinates/links/diagnostics."""
    target = Path(folder)
    target.mkdir(parents=True, exist_ok=False)
    files = {'analysis.json': comparison, 'interchange-v1.json': envelope}
    for name, data in files.items():
        (target / name).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    with (target / 'aligned-coordinates.csv').open('x', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['observation_id', 'period', 'actor_id', 'meeting_id', 'source_family_id',
                         'map_fit_id', 'kind'] + [f'display_{i+1}' for i in range(len(comparison['aligned_coordinates'][0]['coordinates']))])
        for r in comparison['aligned_coordinates']:
            writer.writerow([r['observation_id'], r['period'], r['actor_id'], r['meeting_id'],
                             r['source_family_id'], r['map_fit_id'], r['coordinate_kind'], *r['coordinates']])
    with (target / 'cluster-correspondence.csv').open('x', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['before', 'after', 'shared_overlap',
                                                     'share_of_prior_common', 'share_of_next_common'])
        writer.writeheader()
        writer.writerows(comparison['cluster_correspondence']['overlap_edges'])
    return sorted(p.name for p in target.iterdir())
