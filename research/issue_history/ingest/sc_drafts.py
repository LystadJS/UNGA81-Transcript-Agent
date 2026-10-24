"""DPPA-SCVOTES event adapter, inspected against the 24 October 2026 CSV.

Unanimous outcome labels may include no formal ballot: published yes lists are
retained as source claims, while individual ballots remain unknown.
"""
import csv
import datetime as dt
import hashlib
import re
from urllib.parse import urlparse
from pathlib import Path
from .adapters import SourceError

HEADERS = ("id","year","date","resolution","meeting_record","draft","agenda_item","topic","category","region","outcome","yes","no","abstain","last_update")
SOURCE_URL = "https://psdata.un.org/dataset/DPPA-SCVOTES"
OUTCOMES = ("Adopted unanimously","Adopted by majority","Not adopted - veto","Not adopted - failed to receive required number of votes")
VERSION = "dppa-sc-drafts-1"
EXPLICIT_ALIASES = {"Cape Verde":"CPV","Turkey":"TUR","Côte d’Ivoire":"CIV"}


def validate_headers(headers):
    if tuple(headers or ()) != HEADERS:
        raise SourceError("DPPA-SCVOTES header schema mismatch")


def registry(path=None):
    path = Path(path) if path else Path(__file__).resolve().parents[3]/"un/config/countries.csv"
    raw = path.read_bytes()
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    codes, aliases = {}, {}
    for row in rows:
        codes[row["iso3"]] = row["country"]
        for alias in [row["country"],*row["aliases"].split("|")]:
            aliases.setdefault(alias,set()).add(row["iso3"])
    for alias,code in EXPLICIT_ALIASES.items():
        if code not in codes:
            raise SourceError("Explicit country alias has no registry identity")
        aliases.setdefault(alias,set()).add(code)
    return codes,aliases,hashlib.sha256(raw).hexdigest()


def _date(value):
    if not isinstance(value,str) or dt.date.fromisoformat(value).isoformat()!=value:
        raise SourceError("Invalid source calendar date")


def adapt(row, *, source_sha256, countries=None, overlays=()):
    if set(row)!=set(HEADERS) or any(not isinstance(v,str) for v in row.values()):
        raise SourceError("DPPA row/header mismatch")
    if not re.fullmatch(r"[1-9]\d*",row["id"]):
        raise SourceError("Invalid native DPPA event ID")
    _date(row["date"]);_date(row["last_update"])
    if row["year"]!=row["date"][:4] or row["last_update"]<row["date"]:
        raise SourceError("Inconsistent source dates")
    draft=row["draft"].strip()
    if not re.fullmatch(r"S/(?:\d{4}/)?\d+(?:/Rev\.\d+)?",draft):
        raise SourceError("Unsupported draft reference")
    if row["meeting_record"]!="S/PV." and not re.fullmatch(r"S/(?:PV\.\d+|\d{4}/\d+)",row["meeting_record"]):
        raise SourceError("Unsupported meeting or written-procedure reference")
    if row["outcome"] not in OUTCOMES:
        raise SourceError("Unknown DPPA outcome")
    if not re.fullmatch(r"[a-f0-9]{64}",source_sha256):
        raise SourceError("Exact downloaded source hash required")
    if row["outcome"].startswith("Adopted") != bool(row["resolution"]):
        raise SourceError("Outcome and adopted reference conflict")
    codes,aliases,registry_hash=countries or registry()
    votes=[];identities=set()
    unanimous=row["outcome"]=="Adopted unanimously"
    for choice in ("yes","no","abstain"):
        names=row[choice].split(",") if row[choice] else []
        for recorded in names:
            literal=recorded.strip()
            if not literal:
                raise SourceError("Blank country inside recorded vote list")
            mapped=aliases.get(literal,set())
            if len(mapped)>1:
                raise SourceError("Ambiguous exact country alias")
            code=next(iter(mapped)) if mapped else None
            identity=code or literal
            if identity in identities:
                raise SourceError("Duplicate country across source vote lists")
            identities.add(identity)
            recorded_ballot=not unanimous and code is not None
            votes.append({"country":codes[code] if code else literal,"recorded_country":recorded,
                "country_code":code,"vote":choice if recorded_ballot else "unknown","recorded_choice":choice,
                "eligible":True if recorded_ballot else None,"mapping_status":"exact_registry_or_alias" if code else "unmapped_name"})
    notes=[]
    for overlay in overlays:
        target=overlay.get("event",{})
        if target.get("id")!=row["id"]:continue
        expected={"id":row["id"],"date":row["date"],"draft":draft,"meeting_record":row["meeting_record"],"outcome":row["outcome"],"source_sha256":source_sha256}
        if target!=expected or overlay.get("recorded_counts")!={key:sum(v["recorded_choice"]==key for v in votes) for key in ("yes","no","abstain")}:
            raise SourceError("Nonparticipation overlay event/count identity mismatch")
        note=overlay.get("note",{})
        required=("country","country_code","kind","source_url","source_sha256","review_state","anchor")
        if any(not isinstance(note.get(k),str) or not note[k] for k in required):raise SourceError("Incomplete nonparticipation provenance")
        parsed=urlparse(note["source_url"])
        if parsed.scheme!='https' or not (parsed.hostname=='un.org' or (parsed.hostname or '').endswith('.un.org')):raise SourceError("Nonparticipation source must be official HTTPS UN")
        if note['kind']!='confirmed_nonparticipation' or note['review_state']!='assistant_provisional' or not re.fullmatch('[a-f0-9]{64}',note['source_sha256']):raise SourceError("Unsupported nonparticipation review/provenance")
        code=note['country_code']
        if codes.get(code)!=note['country'] or code in identities or any(n['country_code']==code for n in notes):raise SourceError("Nonparticipation note conflicts with recorded roster")
        scope=note.get('hash_scope','original_document_bytes')
        if scope not in ('original_document_bytes','browser_rendered_primary_text','tool_extracted_primary_metadata'):raise SourceError("Unsupported primary hash scope")
        if 'source_pages' in note and (not isinstance(note['source_pages'],list) or not note['source_pages'] or any(type(p)is not int or not 1<=p<=10000 for p in note['source_pages'])):raise SourceError("Invalid primary source pages")
        notes.append({**{key:note[key] for key in required},'hash_scope':scope,**({'source_pages':note['source_pages']} if 'source_pages'in note else {})})
    if len(votes)+len(notes)!=15:
        raise SourceError("Incomplete source roster: expected 15 distinct listed members or source-bound nonparticipation notes")
    if unanimous and (row["no"] or row["abstain"]):
        raise SourceError("Unanimous outcome conflicts with source lists")
    return {"id":row["id"],"date":row["date"],"draft":draft,"recorded_draft":row["draft"],
        "meeting_record":row["meeting_record"],"resolution":row["resolution"],"outcome":row["outcome"],
        "modality":"unanimous_ballot_unverified" if unanimous else "recorded_vote","votes":votes,
        "source_url":SOURCE_URL,"source_sha256":source_sha256,"source_family":"un_dppa_sc_draft_vote",
        "stage":"draft_resolution","last_update":row["last_update"],"adapter_version":VERSION,
        "country_registry_sha256":registry_hash,"roster_complete":True,"nonparticipation":notes,
        "reference_valid":bool(re.fullmatch(r"\d+\s*\(\d{4}\)",row["resolution"])),
        **{key:row[key] for key in ("agenda_item","topic","category","region")},
        "meeting_reference_kind":"unavailable" if row["meeting_record"]=="S/PV." else "meeting_record" if row["meeting_record"].startswith("S/PV.") else "written_procedure_document"}
