"""Private real-source preflight for 2008–2023, WITHOUT fitting a representation.

The 2008–2015 original-PV sample provides 64 authentic meeting groups with
known first-stage inclusion probabilities, but has no *randomized second-stage
audit* of missing/failed speech outcomes. The 2016–2023 original-PV cohort is
historically validated under a different sampling design. Stop real fitting
until both source and joint-selection calibration gates pass independently.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path

EXPECTED_INDEX_SHA='841ae22d6485a7e3c0bce84830f09c43d75421ce9b3a58408d20dfec3cbbaf43'
EXPECTED_SOURCE_YEARS=tuple(range(2008,2016))
EXPECTED_INDEXED=858
EXPECTED_ISO_RESOLVED=855
EXPECTED_STRONG=832
EXPECTED_UNAMBIGUOUS=828
EXPECTED_SAMPLE=64
EXPECTED_MEETINGS_IN_FRAME=118
UNKNOWN_AUDIT_FIELDS={'random_audit_probability','audit_assigned_before_outcome',
    'audited_nonresponse_text_sha256','audit_randomization_seed'}

def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def audit_source_inputs(early_rows,meeting_frame,un_index):
    if hashlib.sha256(un_index.read_bytes()).hexdigest()!=EXPECTED_INDEX_SHA:
        raise ValueError('Original UN speaker index source bytes changed')
    source=rows(early_rows);frame=rows(meeting_frame)
    if not source or not frame or len(source)!=EXPECTED_ISO_RESOLVED or len(frame)!=EXPECTED_MEETINGS_IN_FRAME:
        raise ValueError('P2 source linked row/frame counts changed')
    if any(k in source[0] for k in UNKNOWN_AUDIT_FIELDS):
        # A declared audit column alone does not verify independent randomization.
        raise ValueError('New audit fields require separate preregistered source-provenance validation')
    selected=[r for r in frame if r['selected']=='True']
    if len(selected)!=EXPECTED_SAMPLE:raise ValueError('Sampling selection population changed')
    byyear=defaultdict(list);byquartile=defaultdict(list)
    for r in frame:
        year=int(r['year']);quartile=int(r['stratum'])
        if year not in EXPECTED_SOURCE_YEARS or quartile not in (1,2,3,4):
            raise ValueError('Original source outside frozen year/quartile frame')
        byyear[year].append(r);byquartile[(year,quartile)].append(r)
    for (year,q),members in byquartile.items():
        if len([r for r in members if r['selected']=='True'])!=2:
            raise ValueError('Not exactly two original meeting sources per stratum')
        for r in members:
            if abs(float(r['meeting_inclusion_probability'])-2/len(members))>1e-12:
                raise ValueError('Invalid original meeting-stage inclusion weight')
    if any(sum(r['selected']=='True' for r in byyear[y])!=8 for y in EXPECTED_SOURCE_YEARS):
        raise ValueError('Per-year source meeting counts changed')
    present={r['meeting_symbol'] for r in selected}
    if not all(r['meeting_symbol'] in present for r in source):
        raise ValueError('A source-linked speech references an unselected original PDF')
    if any(not r['Harvard_SHA256'] or len(r['Harvard_SHA256'])!=64 or
            not r['official_PV_SHA256'] or len(r['official_PV_SHA256'])!=64
           for r in source):
        raise ValueError('Source attestation lacks original Harvard/PV byte hashes')
    passed=[r for r in source if r['strong_original_PV_match']=='True']
    if len(passed)!=EXPECTED_STRONG:raise ValueError('Strong original-PV source text count changed')
    groups=defaultdict(list)
    for r in passed:groups[(r['year'],r['iso3_candidate'])].append(r)
    unique=[v[0] for v in groups.values() if len(v)==1]
    if len(unique)!=EXPECTED_UNAMBIGUOUS:
        raise ValueError('Duplicate attribution/matching denominator changed')
    per=[]
    for y in EXPECTED_SOURCE_YEARS:
        members=[r for r in source if int(r['year'])==y]
        strong=[r for r in passed if int(r['year'])==y]
        acceptable=[r for r in unique if int(r['year'])==y]
        per.append({'year':y,'total_index_PV_meetings':len(byyear[y]),
            'selected_PV_meetings':8,'source_index_ISO3_rows':len(members),
            'full_PV_strong_matches':len(strong),
            'unambiguous_verified_country_years':len(acceptable),
            'independent_randomized_text_audit_completed':False})
    return {'schema':'un.W4.source-preflight.private-aggregate.v1',
      'original_index_sha256':EXPECTED_INDEX_SHA,
      'source_sample_years':'2008–2015','source_frame_meetings':len(frame),
      'original_meetings_sampled':len(selected),
      'original_source_rows_included_in_selected_meetings':EXPECTED_INDEXED,
      'rows_with_resolved_ISO3_country_labels':len(source),
      'strong_source_matches':len(passed),'unambiguous_country_year_texts':len(unique),
      'source_method':'first_stage_known_original_PV_meeting_probabilities',
      'probability_sample_of_country_speeches':False,
      'missing_text_response_probability_identified':False,
      'random_phase2_outcome_audit_provenance_available':False,
      'old_period_2016_2023_source_comparison':'PR58 prior original-source receipt only; row-level basis not jointly audited here',
      'common_2008_2023_frozen_training_selection_accepted':False,
      'source_sampling_generalizable_to_UN_member_census':False,
      'recorded_affiliation_is_authenticated_person':False,
      'annual':per,
      'real_new_2008_2023_representation_fitted':False,
      'real_new_2008_2023_representation_fit_gate':'BLOCKED_UNIDENTIFIED_TRANSCRIPT_NONRESPONSE_AND_DIFFERENT_YEAR_SOURCE_FRAME',
      'publication_eligible':False,'reserved_2026_meeting_reads':0}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--early-source-rows',required=True,type=Path)
    p.add_argument('--meeting-frame',required=True,type=Path)
    p.add_argument('--original-un-index',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError('Output already exists; do not overwrite')
    result=audit_source_inputs(a.early_source_rows,a.meeting_frame,a.original_un_index)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in (
      'source_frame_meetings','original_meetings_sampled','strong_source_matches',
      'unambiguous_country_year_texts','random_phase2_outcome_audit_provenance_available',
      'real_new_2008_2023_representation_fit_gate')},indent=2))

if __name__=='__main__':main()
