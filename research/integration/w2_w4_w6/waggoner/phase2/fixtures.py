"""Fresh fictional panels. No path, URL, transcript or user-data argument exists."""
from copy import deepcopy
from .. import us_reference as u

COUNTRIES = ['USA', 'BRA', 'CAN', 'FRA', 'IND', 'GBR']
YEARS = [2000, 2001, 2003, 2004, 2006]  # Unequal elapsed intervals are intentional.


def source_panel():
    metric = dict(id='syn-phase2-3d', version='1', dimension=3,
                  feature_order=['syn-x', 'syn-y', 'syn-z'],
                  space_kind='full_feature_space', preprocessing_id='syn-fixed',
                  normalization='none', fit_selection_sha256=u.digest('syn-phase2-fit'),
                  training_cutoff='1999-12-31', upstream_fingerprint=u.digest('syn-phase2-upstream'))
    metric['fingerprint'] = u.digest(metric)
    p = dict(schema=u.INPUT_SCHEMA, split='synthetic',
             identity=dict(producer_schema='un.us-relative-source-panel.v1', producer_version='1',
                           producer_panel_sha256=u.digest('syn-phase2-panel'),
                           selection_sha256=u.digest('syn-phase2-selection'), runtime_id='synthetic-phase2'),
             metric_space=metric,
             display_space=dict(method='fixed_orthonormal_linear', basis=[[1, 0], [0, 1], [0, 0]],
                                center=[0, 0, 0], metric_fingerprint=metric['fingerprint'], fit_id='syn-phase2-plane'),
             scope=dict(countries=COUNTRIES[:], genres=['debate', 'committee'], language='en',
                        source_type='synthetic', topic_id='syn-topic', support_mode='common',
                        weight_policy=u.WEIGHT_POLICY, source_unit_policy='one_vector_per_original_parent',
                        baseline_iso3='USA', baseline_mode='contemporaneous'),
             periods=[dict(id=f'p{i}', start=f'{year}-01-01', end=f'{year}-12-31') for i, year in enumerate(YEARS)],
             observations=[])
    for country in COUNTRIES:
        if country == 'GBR':  # Retained empty inventory row, not a zero-valued country.
            continue
        for i, period in enumerate(p['periods']):
            v = {'USA': [0.6*i, 0.2*i, 0.2*i], 'CAN': [3-0.1*i, 0.5+0.2*i, 1],
                 'FRA': [-2+0.2*i, 2-0.3*i, -0.4*i], 'IND': [0.4*i, -1+0.1*i, 0.3],
                 'BRA': [-1+0.4*i, -2+0.4*i, 0.6]}[country]
            for genre in p['scope']['genres']:
                key = f'syn-{country}-p{i}-{genre}'
                row = dict.fromkeys(u.OBS_KEYS)
                row.update(id=key, period=period['id'], date=period['start'], country_iso3=country,
                           actor_id=f'syn-person-{country}-{i}', speaker_id=f'syn-speaker-{country}-{i}',
                           speech_id=key+'-speech', capacity='national', attribution_status='synthetic_verified',
                           review_receipt=key+'-review', genre=genre, language='en', source_type='synthetic',
                           topic_id='syn-topic', source_status='available', meeting_id=key+'-meeting',
                           source_family_id=f'syn-family-{country}-{genre}', source_sha256=u.digest(key+'-source'),
                           text_sha256=u.digest(key+'-text'), source_hash_basis='synthetic', parent_id=key+'-parent',
                           parent_text_sha256=u.digest(key+'-parent'), start=0, end=10,
                           source_pointer='/synthetic/'+key, representation_fingerprint=metric['fingerprint'], vector=v[:])
                p['observations'].append(row)
    return p


def scenarios():
    base = source_panel()
    rows = []
    def add(key, title, note, panel):
        # A substantive scenario change has its own selection and source identity.
        panel['identity']['selection_sha256'] = u.digest({'scenario': key, 'observations': panel['observations']})
        panel['identity']['producer_panel_sha256'] = u.digest({'scenario': key, 'split': 'synthetic'})
        rows.append(dict(id=key, title=title, note=note, source=panel))
    add('moving', 'Moving US reference', 'Both reference and comparator move. All numbers and source records are fictional.', deepcopy(base))
    p = deepcopy(base)
    for r in p['observations']:
        if r['country_iso3'] == 'USA' and r['period'] == 'p2':
            r.update(source_status='unavailable', missing_reason='syn-missing', date=None, vector=None)
    add('missing-us', 'Missing middle US period', 'The 2003 US profile is unavailable. No zero fill, carry-forward or connector across that period.', p)
    p = deepcopy(base)
    p['observations'] = [r for r in p['observations'] if not (r['country_iso3']=='CAN' and r['period']=='p2' and r['genre']=='committee')]
    add('support-gap', 'Incomplete comparator support', 'CAN has no committee observation in 2003. The required common genre scope is not renormalized.', p)
    p = deepcopy(base)
    for r in p['observations']:
        if r['country_iso3']=='USA': r['vector'] = [0, 0, 0]
        elif r['country_iso3']=='CAN': r['vector'] = [0, 0, int(r['period'][1:])]
    add('hidden-dimension', 'Movement outside the plane', 'CAN moves only in the third feature. The 2D position stays fixed while the high-dimensional gap increases.', p)
    p = deepcopy(base)
    for r in p['observations']:
        if r['country_iso3']=='CAN':
            i=int(r['period'][1:]); r['vector'] = [0.6*i, 0.2*i, 0.2*i]
    add('zero-gap', 'Equal observed profiles', 'CAN and USA share the same fictional profile. Zero distance is observed; zero-gap contribution ratios remain undefined.', p)
    p = deepcopy(base); p['display_space']['basis'][0][0] = 2
    add('display-withheld', 'Invalid display transform', 'The display is withheld. Valid high-dimensional gaps and source provenance remain available.', p)
    p = deepcopy(base); p['observations'] = []
    add('empty', 'Empty source inventory', 'The country-period frame remains visible with no invented coordinates or distances.', p)
    p = deepcopy(base)
    for r in p['observations']:
        if r['country_iso3']=='CAN': r.update(source_status='failed', missing_reason='syn-failed', date=None, vector=None)
    add('failed-source', 'Failed comparator sources', 'Failed observations retain their identity and state; none is treated as a measured zero.', p)
    return rows
