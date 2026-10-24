"""Private DPPA draft-event ledger; isolated from completed adopted-vote data."""
import argparse
import csv
import json
import hashlib
import shutil
from pathlib import Path
from ..ingest.sc_drafts import HEADERS,VERSION,adapt,registry,validate_headers,SOURCE_URL
from ..ingest.adapters import SourceError,digest
from ..store import IssueStore,canonical_bytes,stable_id
from .vote_cli import file_hash


def load_overlays(path):
    if path is None:return []
    path=Path(path)
    if path.stat().st_size>100_000:raise SourceError("Overlay metadata exceeds bound")
    data=json.loads(path.read_bytes())
    if data.get('schema')!='un.sc-draft-nonparticipation.v1' or not isinstance(data.get('overlays'),list) or len(data['overlays'])>100:raise SourceError("Unsupported overlay metadata")
    for entry in data['overlays']:
        source=Path(entry.get('source_evidence_file') or entry['local_source_file'])
        if not source.is_absolute():source=path.parent/source
        if not 100<=source.stat().st_size<=2_000_000 or file_hash(source)!=entry['note']['source_sha256']:raise SourceError("Primary nonparticipation bytes/hash mismatch")
        raw=source.read_bytes()
        if b'/_fs-ch-' in raw or (source.suffix.lower()=='.pdf' and not raw.startswith(b'%PDF-')):raise SourceError("Primary source is a challenge or malformed PDF")
        scope=entry['note'].get('hash_scope','original_document_bytes')
        if scope=='browser_rendered_primary_text':
            if len(raw.decode('utf-8').strip())<100:raise SourceError("Rendered primary text is incomplete")
        elif scope=='tool_extracted_primary_metadata':
            primary=json.loads(raw)
            if primary.get('schema')!='un.primary-metadata-extract.v1' or primary.get('hash_scope')!=scope or primary.get('source_url')!=entry['note']['source_url'] or primary.get('review_state')!='assistant_provisional':raise SourceError("Primary extraction provenance mismatch")
            facts=primary.get('event',{})
            if any(facts.get(key)!=entry['event'][key] for key in ('date','meeting_record')) or any(facts.get(key)!=entry['recorded_counts'][key] for key in ('yes','no','abstain')):raise SourceError("Primary extraction event/count mismatch")
            if facts.get('resolution')!=entry.get('recorded_adopted_resolution') or primary.get('source_pages')!=entry['note'].get('source_pages'):raise SourceError("Primary extraction resolution/page mismatch")
            footnote=primary.get('primary_footnote','')
            if entry['note']['country'] not in footnote or 'did not participate' not in footnote:raise SourceError("Primary extraction does not support named nonparticipation")
        elif scope!='original_document_bytes':raise SourceError("Unsupported primary hash scope")
    return data['overlays']


def collect(source_file,source_sha256,start,end,overlays=()):
    if Path(source_file).stat().st_size>5_000_000 or file_hash(source_file)!=source_sha256:
        raise SourceError("DPPA source bound or exact digest mismatch")
    countries=registry();events=[];quarantined=[];raw_rows={};ids=set();actions=set();scanned=0
    with open(source_file,encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream);validate_headers(reader.fieldnames)
        for row in reader:
            scanned+=1
            if row["id"] in ids:raise SourceError("Duplicate native DPPA event ID")
            ids.add(row["id"])
            if not start<=row["date"]<=end:continue
            try:event=adapt(row,source_sha256=source_sha256,countries=countries,overlays=overlays)
            except SourceError as error:
                if str(error).startswith("Incomplete source roster:"):
                    quarantined.append({"id":row["id"],"draft":row["draft"].strip(),"date":row["date"],"reason":"incomplete_recorded_roster","recorded_count":sum(len(r.split(',')) for r in (row['yes'],row['no'],row['abstain']) if r)})
                    continue
                raise
            action=(event["date"],event["draft"],event["meeting_record"])
            if action in actions:raise SourceError("Duplicate DPPA voting-action identity")
            actions.add(action);events.append(event);raw_rows[event["id"]]=row
    collection={"schema":"un.sc-draft-collection.v1","dataset_id":"DPPA-SCVOTES","source_url":SOURCE_URL,
        "source_sha256":source_sha256,"window":{"start":start,"end":end},"events":events,"quarantined":quarantined,
        "scanned":scanned,"limitations":["Votes on a draft are separate from adopted-resolution records; cross-source duplicates must not add weight.","Published unanimous outcomes may include no formal ballot; individual ballots remain unknown.","Catalog topics are source metadata, not extracted national policy positions."]}
    return collection,raw_rows


def ingest(*,source_file,expected_sha256,database,checkpoint,collection_file,receipt_file,start,end,max_batches=100,min_free_bytes=209715200,overlays=None):
    import datetime as dt
    if dt.date.fromisoformat(start)>dt.date.fromisoformat(end) or type(max_batches)is not int or not 1<=max_batches<=1000:raise ValueError("Invalid date/batch bounds")
    overlay_rows=load_overlays(overlays)
    collection,raw_rows=collect(source_file,expected_sha256,start,end,overlay_rows)
    identity={"source_sha256":expected_sha256,"start":start,"end":end,"adapter_sha256":file_hash(Path(__file__).resolve().parents[1]/"ingest/sc_drafts.py"),"normalizer_sha256":file_hash(Path(__file__).resolve().parents[1]/"ingest/adapters.py"),"registry_sha256":registry()[2],"version":VERSION,"overlays_sha256":file_hash(overlays) if overlays else None}
    checkpoint=Path(checkpoint);prior=json.loads(checkpoint.read_bytes()) if checkpoint.exists() else {"identity":identity,"event_cursor":0,"accepted_events":0,"accepted_ballots":0,"complete":False}
    if prior["identity"]!=identity:raise ValueError("DPPA checkpoint identity changed")
    for path in (database,checkpoint,collection_file,receipt_file):Path(path).parent.mkdir(parents=True,exist_ok=True)
    store=IssueStore(database);storage_blocked=False
    try:
        for _ in range(max_batches):
            if prior["event_cursor"]>=len(collection["events"]):break
            if shutil.disk_usage(Path(database).parent).free<min_free_bytes+5_000_000:storage_blocked=True;break
            batch=collection["events"][prior["event_cursor"]:prior["event_cursor"]+33]
            with store.transaction():
                for event in batch:
                    source_id=stable_id("dppa-sc-draft-event-source",event["id"])
                    revision=store.upsert_source({"id":source_id,"published_date":event["date"],"body":"SC","family":"un_dppa_sc_draft_vote","url":SOURCE_URL,"content_hash":digest(event),"access":"private","countries":[v["country"] for v in event["votes"]],"download_sha256":expected_sha256,"raw_source_row":raw_rows[event["id"]],"nonparticipation_notes":event["nonparticipation"]})
                    for vote in event["votes"]:
                        store.put_vote({"id":stable_id("dppa-sc-draft-vote",event["id"],vote["country_code"] or vote["recorded_country"]),"source_id":source_id,"source_revision":revision,"country":vote["country"],"date":event["date"],"policy":"unbound","context":event["draft"],"resolution":event["draft"],"resolution_version":"recorded_draft","stage":"draft_resolution","vote":vote["vote"],"eligible":vote["eligible"],"recorded_choice":vote["recorded_choice"],"recorded_country_name":vote["recorded_country"],"country_code":vote["country_code"],"outcome":event["outcome"],"modality":event["modality"],"dppa_event_id":event["id"],"recorded_adopted_resolution":event["resolution"],"meeting_record":event["meeting_record"],"adapter_version":VERSION})
            prior["event_cursor"]+=len(batch);prior["accepted_events"]+=len(batch);prior["accepted_ballots"]+=sum(len(e["votes"]) for e in batch)
            prior["complete"]=prior["event_cursor"]==len(collection["events"])
            store._atomic_write(checkpoint,canonical_bytes(prior))
        if prior["complete"]:store._atomic_write(Path(collection_file),canonical_bytes(collection))
        receipt={"schema":"un.sc-draft-import-receipt.v1",**prior,"quarantined":collection["quarantined"],"scanned":collection["scanned"],"storage_reserve_reached":storage_blocked,"free_bytes":shutil.disk_usage(Path(database).parent).free,"publication":"private_only","policy_binding":"all_votes_unbound"}
        store._atomic_write(Path(receipt_file),canonical_bytes(receipt))
        return receipt
    finally:store.close()


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("source-file","expected-sha256","database","checkpoint","collection-file","receipt-file","start","end"):parser.add_argument('--'+name,required=True)
    parser.add_argument('--max-batches',type=int,default=100)
    parser.add_argument('--overlays')
    print(json.dumps(ingest(**vars(parser.parse_args())),indent=2))
