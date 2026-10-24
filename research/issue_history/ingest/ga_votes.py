"""Actual GA voting CSV v6 adapter, inspected 23 October 2026.

UN Dag Hammarskjold Library, United Nations General Assembly Voting Data,
15 October 2026. Non-commercial use with attribution. Original CSV stays private.
"""
import re
from .adapters import SourceError,vote_record
from .countries import map_country

HEADERS=("undl_id","ms_code","ms_name","ms_vote","date","session","resolution","draft","committee_report","meeting","title","agenda_title","subjects","vote_note","total_yes","total_no","total_abstentions","total_non_voting","total_ms","undl_link")
DATASET_URL="https://digitallibrary.un.org/record/4060887/files/2026_10_15_votes_ga.csv"
METADATA_URL="https://digitallibrary.un.org/record/4060887/files/2026_10_15_votes_ga_1.md"

def validate_headers(headers):
    if tuple(headers or ())!=HEADERS:raise SourceError("GA v6 header schema mismatch; review a new adapter version")

def adapt(row):
    if set(row)!=set(HEADERS):raise SourceError("GA v6 row/header mismatch")
    if not re.fullmatch(r"[A-Z]{3}",row["ms_code"] or ""):raise SourceError("Invalid recorded Member State code")
    if not row["ms_name"].strip():raise SourceError("Missing recorded historical Member State name")
    if not re.fullmatch(r"A/(?:RES|DEC)/[A-Za-z0-9()./-]+(?:\[[A-Z]\]| [A-Z])?",row["resolution"] or ""):raise SourceError("Invalid adopted GA resolution or decision symbol")
    stage="adopted_decision" if row["resolution"].startswith("A/DEC/") else "adopted_resolution"
    if not re.fullmatch(r"\d+",row["undl_id"] or "") or row["undl_link"]!="https://digitallibrary.un.org/record/"+row["undl_id"]:raise SourceError("UN Digital Library voting record identity mismatch")
    code=row["ms_vote"]
    if code not in ("Y","N","A","X"):raise SourceError("Unknown GA vote code; blank is not abstention or absence")
    # X means non-voting in this dictionary; it does not establish absence or non-eligibility.
    identity=map_country(row["ms_code"],row["ms_name"])
    normalized={**identity,"resolution_id":row["resolution"],"resolution_version":"as_adopted","stage":stage,"date":row["date"],"source_url":row["undl_link"],"vote":{"Y":"yes","N":"no","A":"abstain","X":"unknown"}[code],"eligible":None if code=="X" else True,"raw_vote_code":code,"non_voting_reported":code=="X","vote_note_present":bool(row["vote_note"].strip()),"dataset_version":"6","adapter_version":"ga-v6-csv-3","body":"GA"}
    return vote_record(normalized)


def iter_batches(path,start,end,batch_size=500):
    """Scan the verified file once, yielding bounded date-filtered batches.

    Caller pins source-file SHA before use. Cursor is the CSV record ordinal,
    not a claim that rows are chronological. No topic binding is inferred.
    """
    import csv
    from datetime import date
    if date.fromisoformat(start).isoformat()!=start or date.fromisoformat(end).isoformat()!=end or start>end:raise SourceError("Invalid source shard dates")
    if type(batch_size) is not int or not 1<=batch_size<=500:raise SourceError("Source batch must be 1..500")
    rows=[];scanned=0;selected=0
    with open(path,encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream);validate_headers(reader.fieldnames)
        for scanned,row in enumerate(reader,1):
            day=row["date"]
            if not start<=day<=end:continue
            rows.append(adapt(row));selected+=1
            if len(rows)==batch_size:
                yield {"rows":rows,"source_row_cursor":scanned,"selected_so_far":selected,"complete":False,"start":start,"end":end}
                rows=[]
        # An empty final marker is intentional when the last batch was full.
        yield {"rows":rows,"source_row_cursor":scanned,"selected_so_far":selected,"complete":True,"start":start,"end":end}


def reconcile_groups(rows,start,end,max_groups=5000,max_countries=500):
    """Read-only compact reconciliation; accepts noncontiguous source groups.

    Never equates source totals with independently verified national eligibility.
    No original row or speech text is returned.
    """
    from collections import Counter
    from datetime import date
    if date.fromisoformat(start).isoformat()!=start or date.fromisoformat(end).isoformat()!=end or start>end:raise SourceError("Invalid reconciliation dates")
    groups={};source_identities={};symbols={};scanned=0;selected=0;previous=None;closed=set();reopened=set();years={};bad_dates=0
    total_fields=("total_yes","total_no","total_abstentions","total_non_voting","total_ms")
    for scanned,row in enumerate(rows,1):
        day=row.get("date","")
        try:valid=date.fromisoformat(day).isoformat()==day
        except (ValueError,TypeError):valid=False
        if not valid:bad_dates+=1;continue
        if not start<=day<=end:continue
        selected+=1;key=(row["undl_id"],row["resolution"],day)
        if previous is not None and key!=previous:closed.add(previous)
        if key!=previous and key in closed:reopened.add(key)
        previous=key
        source_identities.setdefault(row["undl_id"],set()).add((row["resolution"],day))
        symbols.setdefault(row["resolution"],set()).add((row["undl_id"],day))
        if key not in groups:
            if len(groups)>=max_groups:raise SourceError("Reconciliation group bound exceeded")
            groups[key]={"counts":Counter(),"countries":set(),"duplicates":0,"published":set(),"rows":0}
        g=groups[key];g["rows"]+=1;g["counts"][row.get("ms_vote","")]+=1
        country=row.get("ms_code","")
        if country in g["countries"]:g["duplicates"]+=1
        g["countries"].add(country)
        if len(g["countries"])>max_countries:raise SourceError("Reconciliation country bound exceeded")
        g["published"].add(tuple(row.get(k,"") for k in total_fields))
        if len(g["published"])>max_countries:raise SourceError("Published-total variants exceed reconciliation bound")
    status=Counter();mismatch_fields=Counter();total_codes=Counter()
    for (source,symbol,day),g in groups.items():
        yr=years.setdefault(day[:4],{"rows":0,"groups":0,"mismatched_groups":0,"blank_totals_groups":0,"duplicate_country_groups":0})
        yr["rows"]+=g["rows"];yr["groups"]+=1;total_codes.update(g["counts"])
        mismatch=False
        if g["duplicates"]:status["duplicate_country_groups"]+=1;status["duplicate_country_rows"]+=g["duplicates"];yr["duplicate_country_groups"]+=1;mismatch=True
        if len(g["published"])!=1:status["inconsistent_published_totals_groups"]+=1;mismatch=True
        for published in g["published"]:
            if any(not str(v).strip() for v in published):status["blank_totals_groups"]+=1;yr["blank_totals_groups"]+=1;mismatch=True;break
        else:
            for published in g["published"]:
                try:
                    if any(not re.fullmatch(r"\d+(?:\.0+)?",str(v)) for v in published):raise ValueError()
                    expected=[int(str(v).split(".")[0]) for v in published]
                except ValueError:status["invalid_totals_groups"]+=1;mismatch=True;continue
                actual=[g["counts"][k] for k in ("Y","N","A","X")]+[g["rows"]]
                for field,a,b in zip(total_fields,actual,expected):
                    if a!=b:mismatch_fields[field]+=1;mismatch=True
                if sum(expected[:4])!=expected[4]:status["published_sum_mismatch_groups"]+=1;mismatch=True
        if set(g["counts"])-{"Y","N","A","X"}:status["unknown_vote_code_groups"]+=1;mismatch=True
        if mismatch:status["mismatched_groups"]+=1;yr["mismatched_groups"]+=1
    return {"schema":"un.ga-group-reconciliation.v1","start":start,"end":end,"source_rows_scanned":scanned,"selected_rows":selected,"groups":len(groups),"years":dict(sorted(years.items())),"raw_vote_counts":dict(total_codes),"issues":dict(status),"mismatch_fields":dict(mismatch_fields),"invalid_date_rows_entire_file":bad_dates,"source_id_identity_conflicts":sum(len(v)>1 for v in source_identities.values()),"resolution_identity_conflicts":sum(len(v)>1 for v in symbols.values()),"noncontiguous_groups":len(reopened),"database_completeness_assessed":False,"policy_bindings_created":0,"limitations":["Reconciles supplied file rows against repeated publisher totals, not independent national eligibility or policy meaning.","A partial database's final source group must be checked separately; complete source-file reconciliation does not establish complete database ingestion.","Non-voting X remains unknown, not absent or not eligible; blank totals do not establish consensus or individual yes votes."]}
