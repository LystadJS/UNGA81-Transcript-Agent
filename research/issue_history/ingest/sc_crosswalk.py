"""Read-only, literal SC voting-action crosswalk; no opinion inference."""
import csv
import datetime as dt
import gzip
import hashlib
import json
from collections import Counter,defaultdict
from pathlib import Path
import re
import sqlite3
import os
import tempfile
from urllib.parse import urlparse

VERSION='sc-event-crosswalk-1'


def normalize_resolution(value):
    if not isinstance(value,str):return None
    match=re.fullmatch(r'(?:S/RES/)?([1-9]\d*)[ \u00a0]*\((\d{4})\)',value.strip())
    return 'S/RES/'+match[1]+'('+match[2]+')' if match else None


def _date(value):
    try:return isinstance(value,str) and dt.date.fromisoformat(value).isoformat()==value
    except ValueError:return False


def _code(row):
    code=row.get('country_code')
    return code if isinstance(code,str) and re.fullmatch('[A-Z]{3}',code) else None


def build_crosswalk(collection,ddl_votes):
    window=collection.get('window',{})
    if collection.get('schema')!='un.sc-draft-collection.v1' or collection.get('dataset_id')!='DPPA-SCVOTES' or not re.fullmatch('[a-f0-9]{64}',collection.get('source_sha256','')) or not _date(window.get('start')) or not _date(window.get('end')) or window['start']>window['end'] or not isinstance(collection.get('events'),list) or len(collection['events'])>10000 or not isinstance(ddl_votes,list) or len(ddl_votes)>100000:
        raise ValueError('Unsupported or oversized crosswalk input')
    from .sc_drafts import registry
    canonical_countries=registry()[0]
    events=collection['events'];dppa=defaultdict(list);ddl=defaultdict(list);unmatched_dppa=[];unmatched_ddl=[];conflicts=[];links=[]
    ids=Counter(e.get('id') for e in events)
    row_ids=Counter(r.get('id') for r in ddl_votes)
    source_revisions=defaultdict(set)
    for row in ddl_votes:
        if row.get('source_id'):source_revisions[row['source_id']].add(row.get('source_revision'))
    for event in events:
        eid=event.get('id');resolution=normalize_resolution(event.get('resolution'));date=event.get('date')
        reason='source_provenance_mismatch' if event.get('stage')!='draft_resolution' or event.get('source_family')!='un_dppa_sc_draft_vote' or event.get('source_sha256')!=collection['source_sha256'] else 'not_adopted' if event.get('outcome') not in ('Adopted unanimously','Adopted by majority') else 'invalid_date' if not _date(date) or not window['start']<=date<=window['end'] else 'malformed_resolution' if resolution is None else 'resolution_year_date_mismatch' if resolution[-5:-1]!=date[:4] else 'duplicate_native_id' if not eid or ids[eid]!=1 else None
        if reason:unmatched_dppa.append({'dppa_event_id':eid,'reason':reason});continue
        dppa[(resolution,date)].append(event)
    for row in ddl_votes:
        resolution=normalize_resolution(row.get('resolution'));date=row.get('date')
        reason='not_adopted_resolution' if row.get('stage')!='adopted_resolution' else 'invalid_date' if not _date(date) or not window['start']<=date<=window['end'] else 'malformed_resolution' if resolution is None else 'resolution_year_date_mismatch' if resolution[-5:-1]!=date[:4] else None
        if reason:unmatched_ddl.append({'ddl_row_id':row.get('id'),'reason':reason});continue
        ddl[(resolution,date)].append(row)
    for key in sorted(set(dppa)|set(ddl)):
        ds=dppa.get(key,[]);rs=ddl.get(key,[]);event_key='|'.join(key)
        if len(ds)>1:
            conflicts.append({'ddl_event_key':event_key,'reason':'multiple_drafts_for_adopted_event','dppa_event_ids':sorted(e['id'] for e in ds)})
            continue
        if not ds:
            unmatched_ddl.append({'ddl_event_key':event_key,'reason':'no_exact_dppa_resolution_date'});continue
        if not rs:
            unmatched_dppa.append({'dppa_event_id':ds[0]['id'],'reason':'no_exact_ddl_resolution_date'});continue
        event=ds[0];votes=event.get('votes',[]);notes=event.get('nonparticipation',[])
        if not isinstance(votes,list) or len(votes)>15 or not isinstance(notes,list) or len(notes)>15:raise ValueError('Invalid DPPA event roster bound')
        left=defaultdict(list);right=defaultdict(list);roster_gaps=[]
        if event.get('modality')not in ('recorded_vote','unanimous_ballot_unverified'):roster_gaps.append('invalid_dppa_modality')
        for vote in votes:
            code=_code(vote)
            if code:left[code].append(vote)
            else:roster_gaps.append('unmapped_dppa_country')
            if not code or canonical_countries.get(code)!=vote.get('country'):roster_gaps.append('dppa_country_registry_mismatch')
            if vote.get('vote')not in ('yes','no','abstain','unknown') or (vote.get('vote')=='unknown' and vote.get('eligible')is not None) or (vote.get('vote')in ('yes','no','abstain') and vote.get('eligible')is not True):roster_gaps.append('invalid_dppa_ballot_contract')
            if event.get('modality')=='unanimous_ballot_unverified' and (vote.get('vote')!='unknown' or vote.get('eligible')is not None):roster_gaps.append('unverified_unanimous_ballot_claim')
        note_codes=[]
        for note in notes:
            code=_code(note)
            url=urlparse(note.get('source_url',''));scope=note.get('hash_scope','original_document_bytes')
            valid=code and canonical_countries.get(code)==note.get('country') and note.get('kind')=='confirmed_nonparticipation' and isinstance(note.get('anchor'),str) and note['anchor'].strip() and re.fullmatch('[a-f0-9]{64}',note.get('source_sha256','')) and note.get('review_state')=='assistant_provisional' and scope in ('original_document_bytes','browser_rendered_primary_text','tool_extracted_primary_metadata') and url.scheme=='https' and (url.hostname=='un.org' or (url.hostname or '').endswith('.un.org')) and not url.username and not url.password
            if valid:note_codes.append(code)
            else:roster_gaps.append('unsupported_nonparticipation_note')
        for row in rs:
            code=_code(row)
            if code:right[code].append(row)
            else:roster_gaps.append('unmapped_ddl_country')
            if not code or canonical_countries.get(code)!=row.get('country'):roster_gaps.append('ddl_country_registry_mismatch')
            if row.get('modality')not in ('Vote','Without Vote') or row.get('vote')not in ('yes','no','abstain','unknown','absent','not_eligible') or (row.get('vote')in ('yes','no','abstain','absent') and row.get('eligible')is not True) or (row.get('vote')=='not_eligible' and row.get('eligible')is not False) or (row.get('vote')=='unknown' and row.get('eligible')is not None):roster_gaps.append('invalid_ddl_ballot_contract')
            if row.get('modality')=='Without Vote' and (row.get('vote')!='unknown' or row.get('eligible')is not None):roster_gaps.append('unverified_without_vote_ballot_claim')
            if not row.get('id') or row_ids[row.get('id')]!=1:roster_gaps.append('duplicate_or_missing_ddl_row_identity')
            if not isinstance(row.get('source_id'),str) or not row['source_id'] or not isinstance(row.get('source_revision'),str) or not re.fullmatch('[a-f0-9]{64}',row['source_revision']):roster_gaps.append('invalid_ddl_source_provenance')
            if len(source_revisions.get(row.get('source_id'),set()))>1:roster_gaps.append('conflicting_ddl_source_revisions')
        left_codes=set(left)|set(note_codes);right_codes=set(right)
        if len(votes)+len(notes)!=15 or len(rs)!=15:roster_gaps.append('incomplete_or_duplicate_roster_size')
        if any(len(v)>1 for v in left.values()) or any(len(v)>1 for v in right.values()) or len(set(note_codes))!=len(note_codes) or set(left)&set(note_codes):roster_gaps.append('duplicate_country_identity')
        if left_codes!=right_codes:roster_gaps.extend(['dppa_only:'+c for c in sorted(left_codes-right_codes)]+['ddl_only:'+c for c in sorted(right_codes-left_codes)])
        agreements=0;unknown=[];different=[];participation_conflicts=[]
        for code in sorted(left_codes|right_codes):
            a=left.get(code,[]);b=right.get(code,[])
            if code in note_codes and len(b)==1 and b[0].get('modality')=='Vote' and b[0].get('eligible')is True and b[0].get('vote')in ('yes','no','abstain'):
                different.append(code);participation_conflicts.append(code);continue
            known=len(a)==len(b)==1 and event.get('modality')=='recorded_vote' and event.get('outcome')!='Adopted unanimously' and b[0].get('modality')=='Vote' and a[0].get('eligible')is True and b[0].get('eligible')is True and a[0].get('vote')in ('yes','no','abstain') and b[0].get('vote')in ('yes','no','abstain')
            if not known:unknown.append(code)
            elif a[0]['vote']==b[0]['vote']:agreements+=1
            else:different.append(code)
        reference_gaps=[];reference_conflicts=[];references={'dppa':{},'ddl':{}}
        for field,left_value in (('draft',event.get('draft')),('meeting_record',event.get('meeting_record'))):
            values={r.get(field) for r in rs if r.get(field)}
            references['dppa'][field]=left_value;references['ddl'][field]=sorted(values)
            if not values:reference_gaps.append('ddl_'+field+'_not_retained')
            elif len(values)!=1 or left_value not in values:reference_conflicts.append(field+'_mismatch')
        if reference_conflicts:conflicts.append({'ddl_event_key':event_key,'dppa_event_id':event['id'],'reason':'reference_conflict','fields':reference_conflicts})
        status='roster_conflict' if roster_gaps else 'ballot_conflict' if different else 'unknown_or_modality_gap' if unknown else 'exact_recorded_match'
        if roster_gaps:conflicts.append({'ddl_event_key':event_key,'dppa_event_id':event['id'],'reason':'roster_conflict','fields':sorted(set(roster_gaps))})
        if different:conflicts.append({'ddl_event_key':event_key,'dppa_event_id':event['id'],'reason':'ballot_conflict','countries':different})
        links.append({'dppa_event_id':event['id'],'ddl_event_key':event_key,'resolution':key[0],'date':key[1],
            'identity_status':'exact_resolution_date_one_to_one','identity_basis':['resolution','date'],
            'ballot_status':status,'known_agreements':agreements,'unknown_countries':unknown,'conflicting_countries':different,
            'roster_gaps':sorted(set(roster_gaps)),'reference_gaps':reference_gaps,'reference_conflicts':reference_conflicts,
            'references':references,
            'participation_conflicts':participation_conflicts,
            'ballot_agreement_verified':status=='exact_recorded_match','deduplication_eligible':not roster_gaps and not different and not reference_conflicts,
            'deduplication_scope':'event_identity_only' if status!='exact_recorded_match' else 'recorded_ballots'})
    links.sort(key=lambda r:(r['ddl_event_key'],r['dppa_event_id']))
    summary={'dppa_events':len(events),'ddl_event_groups':len(ddl),'identity_links':len(links),'ballot_statuses':dict(sorted(Counter(r['ballot_status'] for r in links).items())),
        'deduplication_eligible':sum(r['deduplication_eligible'] for r in links),'unmatched_dppa':len(unmatched_dppa),'unmatched_ddl':len(unmatched_ddl),'conflicts':len(conflicts)}
    return {'schema':'un.sc-event-crosswalk.v1','version':VERSION,'summary':summary,'links':links,
        'unmatched_dppa':sorted(unmatched_dppa,key=lambda r:(str(r.get('dppa_event_id')),r['reason'])),
        'unmatched_ddl':sorted(unmatched_ddl,key=lambda r:(str(r.get('ddl_event_key',r.get('ddl_row_id'))),r['reason'])),
        'conflicts':sorted(conflicts,key=lambda r:(r['ddl_event_key'],r['reason'])),
        'limitations':['Exact adopted-resolution/date identity is separate from ballot agreement.','Unknown or unverified unanimous ballots never become affirmative agreement.','No policy positions or clause agreement are inferred.','Source duplicates remain distinct until an explicit consumer applies a validated event deduplication policy.']}


def _hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def _source_hash(path):
    h=hashlib.sha256();total=0;opener=gzip.open if str(path).endswith('.gz') else open
    with opener(path,'rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):
            total+=len(block)
            if total>50_000_000:raise ValueError('Raw DDL reference source exceeds 50 MB bound')
            h.update(block)
    return h.hexdigest()


def crosswalk_files(collection_file,ddl_database,output_file,*,ddl_raw_csv=None,expected_ddl_source_sha256=None):
    target=Path(output_file).resolve()
    for input_path in (collection_file,ddl_database,ddl_raw_csv):
        if input_path is not None:
            source=Path(input_path).resolve()
            if os.path.normcase(str(target))==os.path.normcase(str(source)) or target.exists() and source.exists() and target.samefile(source):raise ValueError('Crosswalk output must not overwrite an input')
    if target.suffix.lower()!='.json':raise ValueError('Crosswalk output must be a JSON artifact')
    if target.exists():
        try:old_output=json.loads(target.read_bytes())
        except (ValueError,UnicodeError):raise ValueError('Existing output is not a crosswalk artifact')
        if old_output.get('schema')!='un.sc-event-crosswalk.v1':raise ValueError('Existing output is not a crosswalk artifact')
    if Path(collection_file).stat().st_size>60_000_000:raise ValueError('Collection exceeds crosswalk bound')
    collection_bytes=Path(collection_file).read_bytes();collection=json.loads(collection_bytes)
    database_hash=_hash(ddl_database)
    connection=sqlite3.connect(Path(ddl_database).resolve().as_uri()+'?mode=ro',uri=True)
    try:
        fetched=connection.execute("SELECT e.payload,r.payload FROM evidence e JOIN sources s ON e.source_id=s.id AND e.source_revision=s.revision JOIN source_revisions r ON r.id=s.id AND r.revision=s.revision WHERE e.kind='vote' AND json_extract(r.payload,'$.body')='SC' AND json_extract(e.payload,'$.stage')='adopted_resolution' LIMIT 100001").fetchall()
        rows=[json.loads(r[0]) for r in fetched]
        if ddl_raw_csv is not None and any(json.loads(r[1]).get('download_sha256')!=expected_ddl_source_sha256 for r in fetched):raise ValueError('Ledger and raw reference source pins differ')
    finally:connection.close()
    dependency_paths={name:Path(__file__).with_name(name) for name in ('sc_drafts.py','adapters.py','countries.py')}
    if ddl_raw_csv is not None:dependency_paths['un_sc_csv.py']=Path(__file__).with_name('un_sc_csv.py')
    dependency_paths['country_registry']=Path(__file__).resolve().parents[3]/'un/config/countries.csv'
    dependencies={name:_hash(path) for name,path in dependency_paths.items()}
    provenance={'collection_sha256':hashlib.sha256(collection_bytes).hexdigest(),'ddl_database_sha256':database_hash,'raw_reference_enrichment':False,'algorithm_sha256':_hash(__file__),'dependency_sha256':dependencies}
    if ddl_raw_csv is not None:
        from .un_sc_csv import validate_headers
        if not expected_ddl_source_sha256 or _source_hash(ddl_raw_csv)!=expected_ddl_source_sha256:raise ValueError('Raw DDL source identity mismatch')
        metadata=defaultdict(set);opener=gzip.open if str(ddl_raw_csv).endswith('.gz') else open
        with opener(ddl_raw_csv,'rt',encoding='utf-8-sig',newline='') as stream:
            reader=csv.DictReader(stream);validate_headers(reader.fieldnames)
            for index,raw in enumerate(reader):
                if index>=250000:raise ValueError('Raw reference metadata exceeds bound')
                resolution=normalize_resolution(raw['resolution'])
                if resolution:metadata[(resolution,raw['date'],raw['ms_code'])].add((raw['draft'].strip(),raw['meeting'].strip()))
        for row in rows:
            values=metadata.get((normalize_resolution(row['resolution']),row['date'],row.get('country_code')),set())
            if len(values)==1:
                draft,meeting=next(iter(values));row.update(draft=draft,meeting_record=meeting)
            elif len(values)>1:row.update(draft='conflicting_raw_references',meeting_record='conflicting_raw_references')
        provenance.update(raw_reference_enrichment=True,ddl_original_source_sha256=expected_ddl_source_sha256)
    report=build_crosswalk(collection,rows);report['input_provenance']=provenance
    if _hash(collection_file)!=provenance['collection_sha256'] or _hash(ddl_database)!=database_hash:raise ValueError('Read-only crosswalk input changed during computation')
    if ddl_raw_csv is not None and _source_hash(ddl_raw_csv)!=expected_ddl_source_sha256:raise ValueError('Raw reference source changed during computation')
    if _hash(__file__)!=provenance['algorithm_sha256']:raise ValueError('Crosswalk algorithm changed during computation')
    if any(_hash(path)!=dependencies[name] for name,path in dependency_paths.items()):raise ValueError('Crosswalk dependency changed during computation')
    path=Path(output_file);path.parent.mkdir(parents=True,exist_ok=True)
    fd,temporary=tempfile.mkstemp(prefix='.crosswalk-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)
    return report


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('collection-file','ddl-database','output-file'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--ddl-raw-csv');parser.add_argument('--expected-ddl-source-sha256')
    result=crosswalk_files(**vars(parser.parse_args()))
    print(json.dumps(result['summary'],indent=2))
