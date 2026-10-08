"""Source-dependent longitudinal deletion diagnostics, not confidence intervals.

Every source meeting is omitted whole; a calendar-year omission removes all its
meetings. Repeated affiliation IDs cross meetings and years, so resamples are
not independent even when source-level omission is reproducible.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import math
from framework import validate_panel, actor_distances, require, ContractError


def _graph_size(rows):
    neighbors = defaultdict(set)
    for r in rows:
        if r['source_status'] != 'available' or r.get('actor_id') is None:
            continue
        a, m = 'a:' + r['actor_id'], 'm:' + r['meeting_id']
        neighbors[a].add(m)
        neighbors[m].add(a)
    remaining = set(neighbors)
    sizes = []
    while remaining:
        todo = [remaining.pop()]
        total = 0
        while todo:
            node = todo.pop()
            total += 1
            for other in neighbors[node] & remaining:
                remaining.remove(other)
                todo.append(other)
        sizes.append(total)
    return sorted(sizes, reverse=True)


def _point(rows, before, after, original_actors):
    values = actor_distances(rows, before, after)
    actors = {r['actor_id'] for r in values['rows']}
    retained = len(actors & original_actors)
    comparable = actors == original_actors and values['mean_within_actor_distance'] is not None
    return {'status': 'descriptive_same_actors' if comparable else 'withheld_population_change',
            'matched_actor_count': values['matched_actor_count'],
            'original_actor_count': len(original_actors),
            'retained_original_actor_count': retained,
            'mean_within_actor_distance': (
                values['mean_within_actor_distance'] if comparable else None),
            'common_actor_centroid_distance': (
                values['common_actor_centroid_distance'] if comparable else None)}


def _summarize(trials, original):
    successful = [t for t in trials if t['status'] == 'descriptive_same_actors']
    summary = {'attempted': len(trials), 'successful': len(successful),
               'withheld_population_changes': len(trials) - len(successful),
               'matched_actors_min': min([t['matched_actor_count'] for t in trials], default=None),
               'matched_actors_max': max([t['matched_actor_count'] for t in trials], default=None)}
    for key in ('mean_within_actor_distance','common_actor_centroid_distance'):
        nums = [t[key] for t in successful]
        summary[key] = (
            {'point': original[key], 'range_min': min(nums), 'range_max': max(nums),
             'maximum_absolute_deletion_difference': max(abs(v-original[key]) for v in nums),
             'type': 'conditional_deletion_sensitivity_not_confidence_interval'}
            if nums else {'point': original[key], 'range_min': None, 'range_max': None,
                          'maximum_absolute_deletion_difference': None,
                          'type': 'withheld_no_identical_population_trials'})
    return summary


def audit_meeting_year_dependence(panel, before, after):
    """Audit conditional changes using the *identical already pinned* features.

    This is not design-based uncertainty: source selection, meeting-within-year,
    actor trajectories, missing sources and training-fit dependence preclude an
    iid row, meeting, actor or year bootstrap.
    """
    meta = validate_panel(panel)
    require(panel['feature_space']['fit_policy'] == 'transformed_reference',
            'Only saved reference transforms accepted; no automatic refitting')
    require(before != after and before in meta['periods'] and after in meta['periods'],
            'Two valid different periods are required')
    by_period = {r['period']: r for r in panel['periods']}
    require(by_period[before]['start'] < by_period[after]['start'],
            'Periods must be in forward chronological order')
    rows = [r for r in panel['observations'] if r['period'] in (before, after)]
    original = actor_distances(rows, before, after)
    actors = {r['actor_id'] for r in original['rows']}
    require(bool(actors), 'No supported matched actors')
    baseline = _point(rows, before, after, actors)

    meetings = {}
    years = {before: set(), after: set()}
    for r in rows:
        if r['source_status'] != 'available':
            continue
        year = int(r['date'][:4])
        p = r['period']
        years[p].add(year)
        identity = (year, r['source_sha256'])
        existing = meetings.setdefault(r['meeting_id'], identity)
        require(existing == identity,
                'Meeting has conflicting original year or source hashes')
    meeting_trials = []
    for mid in sorted(meetings):
        trial = _point([r for r in rows if r.get('meeting_id') != mid],
                       before, after, actors)
        meeting_trials.append(trial)

    year_trials = []
    for y in sorted(set.union(*years.values())):
        year_trials.append(_point([r for r in rows if r['source_status'] != 'available'
                                  or int(r['date'][:4]) != y],
                                 before, after, actors))
    paired_trials = []
    if min(len(years[before]), len(years[after])) >= 2:
        for year_before in sorted(years[before]):
            for year_after in sorted(years[after]):
                paired_trials.append(_point([r for r in rows if r['source_status'] != 'available'
                                            or int(r['date'][:4]) not in (year_before, year_after)],
                                           before, after, actors))

    source_families = {
        p: {r['source_family_id'] for r in rows
            if r['period'] == p and r['source_status'] == 'available'}
        for p in (before,after)}
    components = _graph_size(rows)
    status_by_period = {
        p: dict(Counter(r['source_status'] for r in rows if r['period'] == p))
        for p in (before,after)}
    return {'schema':'un.longitudinal-dependence-descriptive.v1',
            'evaluation_role':'engineering_only','publication_eligible':False,
            'representation': {'id':panel['feature_space']['id'],
                 'fingerprint':panel['feature_space']['fingerprint'],
                 'fit_policy':'transformed_reference',
                 'reference_refit_during_deletions':False},
            'population':{'matched_original_actors':len(actors),
                 'observations_available':sum(r['source_status']=='available' for r in rows),
                 'observations_other':sum(r['source_status']!='available' for r in rows),
                 'meeting_groups':len(meetings),'year_blocks':len(set.union(*years.values())),
                 'years_per_period':{k:len(v) for k,v in years.items()},
                 'source_status_by_period':status_by_period,
                 'paired_source_families':len(source_families[before]&source_families[after]),
                 'actor_meeting_connected_components':len(components),
                 'largest_actor_meeting_component_nodes':max(components,default=0)},
            'baseline':baseline,
            'meeting_delete_one':_summarize(meeting_trials,baseline),
            'year_delete_one':_summarize(year_trials,baseline),
            'one_year_per_period_delete':_summarize(paired_trials,baseline),
            'inference':{'year_cluster_se':None,'meeting_cluster_se':None,
                 'bootstrap_interval':None,'p_value':None,
                 'reason':'Meetings nested in years and crossed by repeated actors; '
                 'years per period small, source selection nonrandom, and population inference unjustified.',
                 'deletion_ranges_are_confidence_intervals':False,
                 'stance_or_political_movement':False},
            'limitations':[
                 'Finite conditional deletion sensitivity only; no sampling uncertainty.',
                 'Year/meeting deletion changes the number of speeches in each actor mean.',
                 'Reference feature weights were not refitted in perturbations.',
                 'Missing observations are never converted to zero vectors.']}
