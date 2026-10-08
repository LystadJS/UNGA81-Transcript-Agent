"""Deterministic fictional panels; never downloads or references UN source text."""
import hashlib
import math

import numpy as np


def sha(value):
    return hashlib.sha256(('fictional-w4:' + value).encode()).hexdigest()


def make_panel(*, motion=False, roster=True, fit_policy='full_refit', unavailable_family=None):
    """Six unchanged stable anchors, three repeat targets, eight paired source groups.

    Optional true target movement, roster-only shift, fixed or refitted display,
    or one missing meeting. Every high-dimensional representation is frozen.
    """
    if fit_policy not in ('full_refit', 'transformed_reference'):
        raise ValueError('Unsupported fixture policy')
    anchors = {f'A{i}': np.array([2 * math.cos(i * math.pi / 3),
                                    2 * math.sin(i * math.pi / 3), i * .12, (i % 2) * .15])
               for i in range(6)}
    targets = {'T0': np.array([.5, .3, .4, 0.]), 'T1': np.array([1., .8, .2, .3]),
               'T2': np.array([-.5, -.4, 0., .6])}
    prior = {**anchors, **targets}
    after = {**anchors, **targets}
    if roster:
        prior.update({'D0': np.array([-8., -7., 0., 0.]),
                      'D1': np.array([-9., -8., 0., 0.])})
        after.update({'N0': np.array([9., 8., 0., 0.]),
                      'N1': np.array([8., 7., 0., 0.])})
    rotation = np.array([[0., -1.], [1., 0.]])
    rows = []
    for period, actors, day in [('p0', prior, '2026-01-15'), ('p1', after, '2026-02-15')]:
        for family in range(8):
            for actor, base in sorted(actors.items()):
                vec = base.copy()
                if motion and period == 'p1' and actor == 'T0':
                    vec += np.array([.8, .2, 0., 0.])
                xy = vec[:2]
                display = xy @ rotation + np.array([3., -2.]) if period == 'p1' and fit_policy == 'full_refit' else xy
                ident = f'fictional-{period}-f{family}-{actor}'
                missing = unavailable_family is not None and (period, family) == unavailable_family
                cluster = (1 if actor in ('A0', 'A1', 'A2', 'T0', 'T1', 'D0', 'D1') else 2) if period == 'p0' else (
                    9 if actor in ('T0', 'T1') and motion else 7 if actor in ('A0', 'A1', 'A2', 'A3', 'A4', 'T0', 'T1') else 8 if actor in ('A5', 'T2') else 10)
                rows.append({'id': ident, 'period': period, 'date': day, 'actor_id': actor,
                    'actor_kind': 'synthetic', 'speaker_id': None, 'speech_id': None,
                    'review_status': 'unreviewed', 'unit': 'source_segment', 'country': None,
                    'genre': 'fictional_intervention', 'meeting_id': f'fictional-meeting-{period}-{family}',
                    'source_family_id': f'fictional-series-{family}', 'parent_id': None,
                    'parent_text_sha256': None, 'start': None, 'end': None, 'source_url': None,
                    'json_pointer': None, 'source_sha256': sha(f'{period}-{family}'),
                    'text_sha256': sha(ident), 'source_hash_basis': 'synthetic',
                    'representation_id': 'fictional-frozen-embeddings',
                    'representation_version': '1', 'representation_fingerprint': sha('unchanged-4d-basis'),
                    'source_status': 'unavailable' if missing else 'available',
                    'missing_reason': 'fictional_missing_meeting' if missing else None,
                    'vector': None if missing else vec.tolist(), 'map': None if missing else display.tolist(),
                    'map_fit_id': None if missing else ('fictional-refit-' + period if fit_policy == 'full_refit'
                        else 'fictional-frozen-map'), 'cluster': None if missing else cluster,
                    'cluster_fit_id': None if missing else 'fictional-imported-partition-' + period,
                    'cluster_parameters_sha256': None if missing else sha('partition-parameters-' + period),
                    'cluster_training_selection_sha256': None if missing else sha('partition-training-selection-' + period)})
    return {'schema': 'un.longitudinal-panel.v1', 'split': 'synthetic',
            'periods': [{'id': 'p0', 'start': '2026-01-01', 'end': '2026-01-31'},
                        {'id': 'p1', 'start': '2026-02-01', 'end': '2026-02-28'}],
            'feature_space': {'id': 'fictional-frozen-embeddings', 'version': '1',
                              'fingerprint': sha('unchanged-4d-basis'),
                              'dimension': 4, 'fit_policy': fit_policy},
            'map_space': {'method': 'fictional-linear-2d', 'dimension': 2},
            'observations': rows}


if __name__ == '__main__':
    from .framework import compare
    print(compare(make_panel(), 'p0', 'p1', anchor_ids=[f'A{i}' for i in range(6)])['high_dimensional'])
