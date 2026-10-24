"""Conservative, source-preserving SC action selection; no political scores."""
import copy
import re
from collections import Counter, defaultdict
from urllib.parse import urlparse
from .sc_crosswalk import build_crosswalk, normalize_resolution, _date

VERSION = 'sc-event-selection-1'


def select_events(collection, ddl_votes, crosswalk):
    """Select one source representative per verified action, retaining alternatives."""
    expected = build_crosswalk(collection, ddl_votes)
    for key in ('schema', 'version', 'input_fingerprints', 'links', 'summary', 'unmatched_dppa', 'unmatched_ddl', 'conflicts'):
        if crosswalk.get(key) != expected[key]:
            raise ValueError('Stale or modified crosswalk: ' + key)
    from .sc_drafts import registry
    countries = registry()[0]
    groups = defaultdict(list)
    events = collection['events']
    ids = Counter(e.get('id') for e in events)
    row_ids = Counter(r.get('id') for r in ddl_votes)
    revisions = defaultdict(set)
    for r in ddl_votes:
        revisions[r.get('source_id')].add(r.get('source_revision'))
        groups[(normalize_resolution(r.get('resolution')), r.get('date'))].append(r)
    selected, withheld = [], []
    consumed_dppa, consumed_ddl = set(), set()

    def hold(reason, ds=(), rs=()):
        withheld.append({'reason': reason, 'dppa_events': copy.deepcopy(list(ds)), 'ddl_rows': copy.deepcopy(list(rs))})
        consumed_dppa.update(id(e) for e in ds)
        consumed_ddl.update(id(r) for r in rs)

    def valid_group(rs):
        # Reuse the crosswalk's full roster/provenance validator with a synthetic
        # unknown alternative. This record is validation-only and never emitted.
        if not rs or len(rs) != 15: return False
        resolution = normalize_resolution(rs[0].get('resolution')); date = rs[0].get('date')
        if not resolution or not _date(date): return False
        if any(row_ids[r.get('id')] != 1 or len(revisions[r.get('source_id')]) != 1 for r in rs): return False
        probe = {'id': '_validation', 'resolution': resolution, 'date': date,
                 'stage': 'draft_resolution', 'source_family': 'un_dppa_sc_draft_vote',
                 'source_sha256': collection['source_sha256'], 'outcome': 'Adopted unanimously',
                 'modality': 'unanimous_ballot_unverified',
                 'votes': [{'country_code': r.get('country_code'), 'country': r.get('country'), 'vote': 'unknown', 'eligible': None} for r in rs]}
        check = build_crosswalk({**collection, 'events': [probe]}, rs)
        return len(check['links']) == 1 and not check['links'][0]['roster_gaps']

    def valid_dppa(e):
        if ids[e.get('id')] != 1 or not e.get('id') or e.get('stage') != 'draft_resolution' or e.get('source_family') != 'un_dppa_sc_draft_vote' or e.get('source_sha256') != collection['source_sha256']: return False
        date = e.get('date')
        if not _date(date) or not collection['window']['start'] <= date <= collection['window']['end']: return False
        adopted = e.get('outcome') in ('Adopted unanimously','Adopted by majority')
        if adopted != bool(e.get('resolution')): return False
        if not isinstance(e.get('draft'),str) or not re.fullmatch(r'S/(?:\d{4}/)?\d+(?:/Rev\.\d+)?',e['draft']): return False
        meeting=e.get('meeting_record')
        if not isinstance(meeting,str) or (meeting!='S/PV.' and not re.fullmatch(r'S/(?:PV\.\d+(?: \(Resumption \d+\))?|\d{4}/\d+)',meeting)): return False
        url=urlparse(e.get('source_url',''))
        if e.get('source_url')!=collection.get('source_url') or url.scheme!='https' or not (url.hostname=='un.org' or (url.hostname or '').endswith('.un.org')) or url.username or url.password: return False
        votes, notes = e.get('votes'), e.get('nonparticipation', [])
        if not isinstance(votes, list) or not isinstance(notes, list) or len(votes)+len(notes) != 15: return False
        codes = [r.get('country_code') for r in votes+notes]
        if len(set(codes)) != 15 or any(countries.get(r.get('country_code')) != r.get('country') for r in votes+notes): return False
        # A paired validation probe also enforces nonparticipation receipt and
        # unknown-ballot contracts for source-only or unsuccessful draft events.
        resolution = normalize_resolution(e.get('resolution')) or 'S/RES/1('+date[:4]+')'
        probe = {**e, 'resolution': resolution, 'outcome': 'Adopted by majority'}
        if e.get('outcome') == 'Adopted unanimously': probe['outcome'] = e['outcome']
        rs = [{'id': '_probe_'+str(i), 'source_id': '_probe_'+str(i), 'source_revision': 'a'*64,
               'country_code': r.get('country_code'), 'country': r.get('country'),
               'date': date, 'resolution': resolution, 'stage': 'adopted_resolution',
               'vote': 'unknown', 'eligible': None, 'modality': 'Without Vote'} for i,r in enumerate(votes+notes)]
        check = build_crosswalk({**collection, 'events': [probe]}, rs)
        return len(check['links']) == 1 and not check['links'][0]['roster_gaps']

    def emit(status, representative, ds=(), rs=(), link=None):
        d = ds[0] if ds else None; r = rs[0] if rs else None
        resolution = normalize_resolution((r or d).get('resolution'))
        failed = status == 'failed_draft'
        selected.append({'action_id': 'sc:dppa:'+str(d['id']) if failed else 'sc:adopted:'+resolution,
                         'date': (r or d)['date'], 'resolution': resolution, 'status': status,
                         'representative_source': representative,
                         'representative_ballots': copy.deepcopy(list(rs) if representative == 'ddl' else d['votes']),
                         'representative_event': copy.deepcopy(d) if representative == 'dppa' else None,
                         'alternatives': [{'source_family': 'un_dppa_sc_draft_vote', 'event': copy.deepcopy(d)}] if representative == 'ddl' and d else [],
                         'nonparticipation': copy.deepcopy(d.get('nonparticipation', [])) if d else [],
                         'comparison_evidence': copy.deepcopy(link), 'coverage_gap': status in ('ddl_only_adopted','dppa_only_adopted'),
                         'issue_binding': 'unbound', 'comparisons_eligible': False})
        consumed_dppa.update(id(e) for e in ds); consumed_ddl.update(id(row) for row in rs)

    by_id = {e.get('id'): e for e in events if ids[e.get('id')] == 1}
    # Any source disagreement on the date of the same resolution blocks both
    # representatives, even when another exact-date candidate also exists.
    resolutions = defaultdict(lambda: {'dppa': [], 'ddl': []})
    for e in events:
        n = normalize_resolution(e.get('resolution'))
        if n and e.get('outcome') in ('Adopted unanimously','Adopted by majority'): resolutions[n]['dppa'].append(e)
    for (n,date),rs in groups.items():
        if n: resolutions[n]['ddl'].extend(rs)
    for n,sides in sorted(resolutions.items()):
        ds,rs = sides['dppa'],sides['ddl']
        if len({e.get('date') for e in ds}|{r.get('date') for r in rs}) > 1:
            hold('possible_same_action_date_conflict',ds,rs)
    for conflict in expected['conflicts']:
        key = conflict['ddl_event_key']; n,date = key.split('|')
        ds = [e for e in events if normalize_resolution(e.get('resolution')) == n and e.get('date') == date]
        rs = groups.get((n,date),[])
        if not any(id(e) in consumed_dppa for e in ds): hold('crosswalk_conflict',ds,rs)
    for link in expected['links']:
        e = by_id.get(link['dppa_event_id']); rs = groups[(link['resolution'],link['date'])]
        if not e or id(e) in consumed_dppa or any(id(r) in consumed_ddl for r in rs): continue
        if not link['deduplication_eligible'] or not valid_dppa(e) or not valid_group(rs): hold('invalid_or_conflicting_action',[e],rs)
        else: emit('matched_adopted','ddl',[e],rs,link)
    for e in events:
        if id(e) in consumed_dppa: continue
        adopted = e.get('outcome') in ('Adopted unanimously','Adopted by majority')
        n = normalize_resolution(e.get('resolution')); date = e.get('date')
        if not valid_dppa(e) or (adopted and (not n or n[-5:-1] != date[:4])): hold('invalid_or_malformed_dppa_action',[e]); continue
        if not adopted and e.get('outcome') not in ('Not adopted - veto','Not adopted - failed to receive required number of votes'):
            hold('unsupported_outcome',[e]); continue
        emit('dppa_only_adopted' if adopted else 'failed_draft','dppa',[e])
    for (n,date),rs in sorted(groups.items(),key=lambda x:str(x[0])):
        remaining = [r for r in rs if id(r) not in consumed_ddl]
        if not remaining: continue
        if not valid_group(remaining): hold('invalid_or_malformed_ddl_action',rs=remaining)
        else: emit('ddl_only_adopted','ddl',rs=remaining)
    selected.sort(key=lambda e:(e['date'],e['action_id']))
    withheld.sort(key=lambda e:(e['reason'],str(e['dppa_events']),str(e['ddl_rows'])))
    return {'schema':'un.sc-event-selection.v1','version':VERSION,'events':selected,'withheld':withheld,
            'summary':{'selected_actions':len(selected),'statuses':dict(sorted(Counter(e['status'] for e in selected).items())),
                       'withheld_groups':len(withheld),'political_scores_computed':False},
            'input_provenance':copy.deepcopy(crosswalk.get('input_provenance',{})),
            'input_fingerprints':copy.deepcopy(crosswalk['input_fingerprints']),
            'limitations':['Source representative selection does not merge or overwrite ballots.','Unverified unanimity remains unknown in its original source.','No policy agreement or aggregate political score is inferred.']}
