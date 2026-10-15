"""Synthetic-only estimated AR(1) year-shock nuisance model; engineering audit.

Independent of the generating coefficients. The design is restricted to
multiple meetings per consecutive year and one synthetic count representation.
"""
import math
import random
from collections import defaultdict


def estimate_ar1(rows, minimum_years=16, minimum_kish=12):
    """Estimate stationary year variance, lag correlation and meeting variance.

    Use unweighted meeting prevalence to avoid large meetings dominating. Subtract
    estimated within-year meeting noise from year-mean variance. This is a
    moment estimator, not an efficient likelihood estimator or confidence bound.
    """
    if not rows or len({r.get('id') for r in rows}) != len(rows):
        return {'ready': False, 'reason': 'empty_or_duplicate_ids'}
    by_meeting = defaultdict(list)
    years = defaultdict(set)
    family = defaultdict(set)
    try:
        for r in rows:
            if (r['representation'] != 'synthetic-count-v1' or r['selected'] is not True
                    or not isinstance(r['year'], int) or not isinstance(r['length'], int)
                    or not isinstance(r['count'], int) or not 0 <= r['count'] <= r['length']
                    or r['length'] < 1):
                return {'ready': False, 'reason': 'source_or_selection_invalid'}
            by_meeting[r['meeting']].append(r)
            years[r['year']].add(r['meeting'])
            family[r['family']].add(r['meeting'])
    except (KeyError, TypeError):
        return {'ready': False, 'reason': 'source_or_selection_invalid'}
    if any(len(x) > 1 for x in family.values()):
        return {'ready': False, 'reason': 'cross_meeting_family'}
    calendar = sorted(years)
    if len(calendar) < minimum_years or calendar != list(range(calendar[0], calendar[-1] + 1)):
        return {'ready': False, 'reason': 'insufficient_or_gapped_years'}
    if any(len(meetings) < 2 for meetings in years.values()):
        return {'ready': False, 'reason': 'one_meeting_per_year'}
    sizes = [len(v) for v in by_meeting.values()]
    kish = sum(sizes)**2 / sum(n*n for n in sizes)
    if kish < minimum_kish:
        return {'ready': False, 'reason': 'low_effective_group_count', 'kish': kish}
    meeting_p = {m: sum(r['count'] for r in group) / sum(r['length'] for r in group)
                 for m, group in by_meeting.items()}
    year_p = [sum(meeting_p[m] for m in sorted(years[y])) / len(years[y]) for y in calendar]
    global_p = sum(year_p) / len(year_p)
    if not .03 < global_p < .97:
        return {'ready': False, 'reason': 'prevalence_boundary'}
    within = [sum((meeting_p[m]-mean)**2 for m in years[y])/(len(years[y])-1)
              for y, mean in zip(calendar, year_p)]
    meeting_observed_var = sum(within)/len(within)
    sampling_noise = sum(v/len(years[y]) for v, y in zip(within, calendar))/len(calendar)
    centered = [p-global_p for p in year_p]
    observed_year_var = sum(v*v for v in centered)/len(centered)
    year_variance = observed_year_var-sampling_noise
    if year_variance <= 1e-5:
        return {'ready': False, 'reason': 'year_variance_not_identified',
                'observed_year_variance': observed_year_var, 'noise_variance': sampling_noise}
    lag_cov = sum(a*b for a,b in zip(centered[:-1],centered[1:]))/(len(centered)-1)
    rho = lag_cov/year_variance
    if not math.isfinite(rho) or abs(rho) >= .9:
        return {'ready': False, 'reason': 'rho_near_or_beyond_boundary', 'raw_rho': rho}
    meeting_sd = math.sqrt(max(0., meeting_observed_var - global_p*(1-global_p) /
                               (sum(r['length'] for r in rows)/len(rows) *
                                (sum(sizes)/len(sizes)))))
    return {'ready': True, 'rho': rho, 'year_sd': math.sqrt(year_variance),
            'meeting_sd': meeting_sd, 'prevalence': global_p, 'years': len(calendar),
            'meetings': len(by_meeting), 'kish': kish, 'estimator': 'year_meeting_moments_v1',
            'parameter_interval_available': False, 'publication_eligible': False}


def resample_ar1(rows, fit, seed):
    """Resimulate nested source design with independently ESTIMATED rho."""
    if not fit.get('ready') or fit.get('estimator') != 'year_meeting_moments_v1':
        raise ValueError('nuisance fit not accepted')
    rng = random.Random(seed)
    years = sorted({r['year'] for r in rows})
    rho = fit['rho']
    sd = fit['year_sd']
    current = rng.gauss(0, sd)
    shocks = {}
    for j, year in enumerate(years):
        if j:
            current = rho*current + rng.gauss(0, sd*math.sqrt(1-rho*rho))
        shocks[year] = current
    meeting_noise = {m:rng.gauss(0, fit['meeting_sd']) for m in sorted({r['meeting'] for r in rows})}
    output = []
    for row in rows:
        p = max(.001, min(.999, fit['prevalence'] + shocks[row['year']] + meeting_noise[row['meeting']]))
        output.append(dict(row, count=sum(rng.random() < p for _ in range(row['length']))))
    return output
