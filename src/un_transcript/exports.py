"""Consistent, atomic research CSV snapshots and conservative public metadata.

The public artifact is intentionally source-free. Model predictions remain in
the private research tables until a separate validated publication path exists.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from .warehouse import canonical, _timestamp
from .attribution import infer_capacity, METHOD_VERSION


TABLES = {
    "warehouse_meta": "Warehouse format identity and active evaluated model pointer.",
    "meetings": "Current revision pointer; one row per inventoried stored meeting.",
    "source_revisions": "Immutable raw response and normalization identity; one row per revision.",
    "actors": "Recorded actor metadata, not independently verified national representation.",
    "segments": "Source-revision-local ASR segment; not necessarily a complete speech. Offsets are source-defined when present.",
    "issues": "Versioned policy question definitions; empty until configured.",
    "predictions": "Private model outputs; status is not a claim of human review. Join current meetings to exclude superseded revisions.",
    "evidence": "Exact source substring per prediction; Python Unicode code-point offsets, end exclusive.",
    "collection_runs": "One row per collection run, retaining configuration, completion state and timestamps.",
    "coverage": "One row per run and requested meeting; noncollection is never neutral stance.",
    "inventory_receipts": "Original paginated inventory response receipt; run coverage records whether the whole inventory validated.",
    "source_evidence": "Version-bound lexical evidence spans; a topic mention is not a stance.",
    "issue_candidates": "Source-bound retrieval or uncatalogued discovery candidates; never automatically policy positions.",
    "analytical_results": "Versioned private method output with its own measurement units and run identity.",
    "model_releases": "Artifact-bound accepted model release receipts; distinct from individual prediction status.",
}


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(value) + "\n", encoding="utf-8")


def _receipt(path, root, *, rows=None):
    raw = path.read_bytes()
    item = {"name":path.name, "path":path.relative_to(root).as_posix(),
            "sha256":hashlib.sha256(raw).hexdigest(), "bytes":len(raw)}
    if rows is not None:
        item["rows"] = rows
    return item


def _csv(path, columns, rows, *, spreadsheet_safe=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    # RFC4180, UTF-8, CRLF. Preserve source bytes semantically rather than
    # spreadsheet formula rewriting; consumers should import text columns.
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\r\n")
        writer.writerow(columns)
        def cell(value):
            if spreadsheet_safe and isinstance(value,str) and value.lstrip(" \t\r\n").startswith(("=","+","-","@")):
                return "'"+value
            return value
        writer.writerows([[cell(row.get(k)) for k in columns] for row in rows])


PANEL_COLUMNS = ["meeting_id","date","body","country","recorded_countries","issue_id","issue_version",
                 "model_version","capacity","status","stance","eligible_for_comparison",
                 "source_revision_ids","source_segment_ids","evidence_ids","prediction_ids",
                 "attribution_method_version","attribution_registry_sha256","source_url"]


def _country_issue_panel(data):
    """One current-source country/issue/meeting/model opportunity, no passage weights.

    Opportunities come from explicit retrieval candidates or predictions. This
    is not the universe of all countries and issues; no retrieved opportunity
    must never be interpreted as a neutral or absent position.
    """
    current={r["current_revision"]:r["meeting_id"] for r in data["meetings"]}
    revisions={r["revision_id"]:r for r in data["source_revisions"]}
    actors={r["actor_id"]:r for r in data["actors"]}
    segments={(r["revision_id"],r["segment_id"]):r for r in data["segments"]}
    active=next((r["value"] for r in data["warehouse_meta"] if r["key"]=="active_model"),"")
    release=next((json.loads(r["receipt_json"]) for r in data["model_releases"] if r["model_version"]==active),{})
    issues={(r["issue_id"],r["version"]) for r in data["issues"]}
    attributed={}
    for key,segment in segments.items():
        actor=actors[segment["actor_id"]]
        derived=infer_capacity({**segment,**actor})
        # Recompute rules rather than trusting a private prediction's claimed
        # country. Promotion of unknown capacity requires the evaluated method.
        effective=actor["capacity"]
        if derived["attribution_kind"]=="collective":
            effective="collective"
        elif effective=="unknown" and derived["attribution_kind"]=="national" and release.get("attribution_method_version")==METHOD_VERSION and release.get("attribution_registry_sha256")==derived["attribution_registry_sha256"]:
            effective="national"
        attributed[key]=(derived["canonical_country"] or "",effective,actor["country"],derived)
    groups={}
    def ensure(revision,segment_id,issue_id,issue_version,model):
        key=(revision,segment_id)
        if revision not in current or (issue_id,issue_version) not in issues or key not in attributed:
            return None
        country,capacity,recorded,derived=attributed[key]
        group_key=(current[revision],country,issue_id,issue_version,model)
        if group_key not in groups:
            source=revisions[revision]
            groups[group_key]={"meeting_id":current[revision],"date":source["date"],"body":source["body"],
                "country":country,"issue_id":issue_id,"issue_version":issue_version,"model_version":model,
                "source_url":source["source_url"],"recorded_countries":set(),"capacities":set(),
                "source_revision_ids":set(),"source_segment_ids":set(),"evidence_ids":set(),"prediction_ids":set(),
                "predictions":[],"segment_predictions":set(),"attribution_method_version":METHOD_VERSION,
                "attribution_registry_sha256":derived["attribution_registry_sha256"]}
        row=groups[group_key]
        row["capacities"].add(capacity);row["recorded_countries"].add(recorded)
        row["source_revision_ids"].add(revision);row["source_segment_ids"].add(segment_id)
        return row
    for candidate in data["issue_candidates"]:
        payload=json.loads(candidate["payload_json"])
        if payload.get("status")!="retrieval_candidate_not_stance":continue
        row=ensure(candidate["revision_id"],candidate["segment_id"],payload.get("issue_id"),payload.get("catalog_version"),active)
        if row is not None and payload.get("evidence_id"):row["evidence_ids"].add(payload["evidence_id"])
    for prediction in data["predictions"]:
        if prediction["model_version"]!=active:continue
        row=ensure(prediction["revision_id"],prediction["segment_id"],prediction["issue_id"],prediction["issue_version"],active)
        if row is None:continue
        row["predictions"].append(prediction);row["prediction_ids"].add(prediction["prediction_id"])
        row["segment_predictions"].add(prediction["segment_id"])
        payload=json.loads(prediction["payload_json"])
        if payload.get("evidence_id"):row["evidence_ids"].add(payload["evidence_id"])
    result=[]
    for _,row in sorted(groups.items()):
        predictions=row.pop("predictions");predicted_segments=row.pop("segment_predictions")
        capacities=row.pop("capacities")
        capacity="national" if capacities=={"national"} and row["country"] else "collective" if capacities=={"collective"} else "unknown"
        labels={p["stance"] for p in predictions if p["status"]=="validated" and p["stance"]}
        states={p["interpretability_status"] for p in predictions}
        stance=None
        if capacity!="national":status="unresolved_attribution"
        elif not release:status="not_evaluated"
        elif "mixed" in states or "conflicting" in states or len(labels)>1:status="mixed"
        elif "conditional" in states:status="conditional"
        elif any(p["status"] not in ("validated","abstained") for p in predictions):status="withheld"
        elif states.intersection({"unclear","unresolved_attribution"}):status="unclear"
        elif not predictions or row["source_segment_ids"]-predicted_segments:status="insufficient_evidence"
        elif labels:
            # Nonexpressed passages do not add weight or neutral votes.
            stance=next(iter(labels));status="clear"
        else:status=next(iter(states)) if len(states)==1 else "insufficient_evidence"
        row.update(capacity=capacity,status=status,stance=stance,eligible_for_comparison=status=="clear")
        for field in ("recorded_countries","source_revision_ids","source_segment_ids","evidence_ids","prediction_ids"):
            row[field]=sorted(row[field])
        result.append(row)
    return result


def export_snapshot(warehouse, output: Path, snapshot_id, generated_at):
    """Publish a new immutable directory containing private/ and public/ trees.

    The returned un.archive.v1 manifest has paths relative to public/. A
    separate private manifest identifies all research CSVs. Consumers change
    their latest pointer only after this call succeeds.
    """
    if not isinstance(snapshot_id,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", snapshot_id):
        raise ValueError("Snapshot ID must be a bounded safe identifier")
    _timestamp(generated_at)
    output = Path(output)
    if output.exists():
        raise FileExistsError("Snapshots are immutable; choose a new output directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".snapshot-", dir=output.parent))
    try:
        # Capture every table under one SQLite read snapshot. No exporter
        # writes to the live warehouse or clears historical records.
        warehouse.db.execute("BEGIN")
        try:
            schema_version = warehouse.db.execute('PRAGMA user_version').fetchone()[0]
            if schema_version not in (1, 2):
                raise ValueError('Unsupported warehouse export version')
            tables = dict(TABLES)
            if schema_version == 2:
                tables['inventory_meetings'] = ('Selected meeting metadata from complete inventories; '
                    'receipt_id joins inventory_receipts, which binds raw hash, date, page and run. '
                    'Last known metadata is not current availability; has_transcript is a source claim. '
                    'meeting_id need not occur in meetings until a transcript is stored.')
            data = {}
            schemas = {}
            for table in tables:
                columns = [dict(r) for r in warehouse.db.execute("PRAGMA table_info(" + table + ")")]
                schemas[table] = [{"name":c["name"],"sqlite_type":c["type"],"nullable":not bool(c["notnull"]),"primary_key_order":c["pk"]} for c in columns]
                order = ",".join('"' + c["name"] + '"' for c in columns if c["pk"]) or "rowid"
                data[table] = [dict(r) for r in warehouse.db.execute("SELECT * FROM " + table + " ORDER BY " + order)]
            if warehouse.db.execute("PRAGMA foreign_key_check").fetchone():
                raise ValueError("Warehouse foreign-key integrity failed")
        finally:
            warehouse.db.rollback()
        private = temporary / "private"
        public = temporary / "public"
        private.mkdir(); public.mkdir()
        downloads = []
        for table, rows in data.items():
            file = private / (table + ".csv")
            _csv(file,[c["name"] for c in schemas[table]],rows)
            downloads.append(_receipt(file,private,rows=len(rows)))
        dictionary = {"schema":"un.csv-dictionary.v1", "encoding":"UTF-8", "delimiter":",",
            "line_ending":"CRLF", "null_encoding":"empty field", "timestamps":"ISO-8601 with timezone",
            "source_text":"Original normalized text; import text columns explicitly in spreadsheet software.",
            "missingness":"Missing, failed, unknown, collective and abstained are not neutral stances.",
            "current_predictions":"Join predictions.revision_id to meetings.current_revision; old predictions remain historical only.",
            "joins":["meetings.current_revision = source_revisions.revision_id", "segments.revision_id = source_revisions.revision_id", "segments.actor_id = actors.actor_id", "predictions.(revision_id,segment_id) = segments.(revision_id,segment_id)", "predictions.(issue_id,issue_version) = issues.(issue_id,version)", "evidence.prediction_id = predictions.prediction_id", "coverage.run_id = collection_runs.run_id", "coverage.meeting_id beginning inventory: identifies a date-level inventory check, not a meeting"],
            "tables":{t:{"description":tables[t],"columns":schemas[t]} for t in tables}}
        if schema_version == 2:
            dictionary['joins'].append('inventory_meetings.receipt_id = inventory_receipts.receipt_id; inventory_meetings.meeting_id = coverage.meeting_id (many historical observations)')
        _write_json(private / "dictionary.json",dictionary)
        private_manifest = {"schema":"un.research-csv-snapshot.v1","snapshot_id":snapshot_id,
            "generated_at":generated_at,"warehouse_schema":schema_version,"tables":downloads,
            "dictionary":_receipt(private / "dictionary.json",private),"status":"engineering_snapshot_not_empirical_acceptance"}
        _write_json(private / "manifest.json",private_manifest)

        revision_by_id = {r["revision_id"]:r for r in data["source_revisions"]}
        counts = {}
        for row in data["segments"]:
            counts[row["revision_id"]] = counts.get(row["revision_id"],0)+1
        run_by_id = {r["run_id"]:r for r in data["collection_runs"]}
        last_inventory = {}
        if schema_version == 2:
            receipts = {r['receipt_id']:r for r in data['inventory_receipts']}
            def inventory_order(row):
                receipt = receipts[row['receipt_id']]
                return (run_by_id[receipt['run_id']]['started_at'], receipt['run_id'], receipt['page'])
            for row in sorted(data['inventory_meetings'], key=inventory_order):
                last_inventory[row['meeting_id']] = row
        latest_coverage = {}
        for row in sorted(data["coverage"],key=lambda r:(run_by_id[r["run_id"]]["started_at"],r["run_id"],r["meeting_id"])):
            latest_coverage[row["meeting_id"]] = row
        # Inventory checks are date-level collection outcomes, not meetings.
        # Preserve all originals in private coverage.csv while separating grain.
        inventory_coverage = {mid:row for mid,row in latest_coverage.items() if mid.startswith("inventory:")}
        latest_coverage = {mid:row for mid,row in latest_coverage.items() if not mid.startswith("inventory:")}
        inventory_statuses = {}
        for row in inventory_coverage.values():
            inventory_statuses[row["status"]] = inventory_statuses.get(row["status"],0)+1
        public_meetings = []
        for row in data["meetings"]:
            revision = revision_by_id.get(row["current_revision"])
            if not revision:
                continue
            mid = row["meeting_id"]
            public_meetings.append({k:revision[k] for k in ("meeting_id","date","title","body","source_url")})
            public_meetings[-1].update(status=latest_coverage.get(mid,{}).get("status","stored"),
                segments=counts.get(revision["revision_id"],0),positions=[],issues=[])
        # Coverage rows for selected but unavailable meetings remain visible;
        # unknown metadata is explicit rather than fabricated from identifiers.
        stored_ids = {r["meeting_id"] for r in public_meetings}
        for mid,row in latest_coverage.items():
            if mid not in stored_ids:
                metadata = last_inventory.get(mid, {})
                public_meetings.append(dict(meeting_id=mid,date=metadata.get('date'),
                    title=metadata.get('title', mid),body=metadata.get('body'),
                    source_url=metadata.get('source_url'),status=row["status"],segments=0,positions=[],issues=[]))
        public_meetings.sort(key=lambda r:(r["date"] or "",r["meeting_id"]))
        # Only accepted model releases can expose source-linked prediction
        # metadata. No quotes, speaker names or unvalidated estimates are copied.
        active_model = next((r["value"] for r in data["warehouse_meta"] if r["key"]=="active_model"),None)
        approved_models = {r["model_version"] for r in data["model_releases"] if r["model_version"]==active_model}
        current_revision = {r["current_revision"]:r["meeting_id"] for r in data["meetings"]}
        actors = {r["actor_id"]:r for r in data["actors"]}
        segment_actors = {(r["revision_id"],r["segment_id"]):actors[r["actor_id"]] for r in data["segments"]}
        issues = {(r["issue_id"],r["version"]):r for r in data["issues"]}
        meeting_index = {r["meeting_id"]:r for r in public_meetings}
        pilot_segments=[]
        for segment in data["segments"]:
            if segment["revision_id"] not in current_revision:continue
            source=revision_by_id[segment["revision_id"]]
            actor=segment_actors[(segment["revision_id"],segment["segment_id"])]
            pilot_segments.append({**segment,**{k:source[k] for k in ("meeting_id","date","title","body","source_url","raw_sha256")},
                **{k:actor[k] for k in ("speaker","country","capacity","group_name")},
                "source_hash":source["raw_sha256"],"source_id":segment["revision_id"]})
        pilot_file=private/"current_segments.json"
        _write_json(pilot_file,{"schema":"un.private-current-segments.v1","snapshot_id":snapshot_id,"segments":pilot_segments})
        private_manifest["companion_files"]=[_receipt(pilot_file,private,rows=len(pilot_segments))]
        for candidate in data["issue_candidates"]:
            if candidate["revision_id"] not in current_revision:
                continue
            payload = json.loads(candidate["payload_json"])
            key = (payload.get("issue_id"),payload.get("catalog_version"))
            if payload.get("status") != "retrieval_candidate_not_stance" or key not in issues:
                continue
            issue = issues[key]
            row = meeting_index[current_revision[candidate["revision_id"]]]
            if not any(i["id"] == issue["issue_id"] for i in row["issues"]):
                row["issues"].append({"id":issue["issue_id"],"label":issue["label"],"kind":"retrieval_candidate_not_stance"})
        panel=_country_issue_panel(data)
        panel_file=private/"country_issue_observations.csv"
        _csv(panel_file,PANEL_COLUMNS,[{k:canonical(v) if isinstance(v,list) else v for k,v in r.items()} for r in panel])
        private_manifest["tables"].append(_receipt(panel_file,private,rows=len(panel)))
        dictionary["tables"]["country_issue_observations"]={"description":"One current-source recorded country/issue-version/meeting/active-model opportunity from retrieval candidates or predictions. Missing opportunities are not absence. Repeated segments have no additional weight; divergent labels or conditions remain explicit. No numeric stance mean.","columns":[{"name":c,"encoding":"JSON array" if c.endswith("_ids") or c=="recorded_countries" else "scalar"} for c in PANEL_COLUMNS]}
        _write_json(private/"dictionary.json",dictionary)
        private_manifest["dictionary"]=_receipt(private/"dictionary.json",private)
        _write_json(private/"manifest.json",private_manifest)
        for observation in panel:
            if observation["model_version"] not in approved_models or observation["capacity"]!="national":continue
            row=meeting_index[observation["meeting_id"]]
            issue=issues[(observation["issue_id"],observation["issue_version"])]
            row["positions"].append({"country":observation["country"],"capacity":"national",
                "issue_id":observation["issue_id"],"issue_version":observation["issue_version"],
                "issue_label":issue["label"],"proposition":issue["definition"],"label":observation["stance"],"stance":observation["stance"],
                "status":observation["status"],"confidence":None,"model_version":observation["model_version"],"source_url":row["source_url"],
                **{k:observation[k] for k in ("source_revision_ids","source_segment_ids","evidence_ids")}})
            if not any(i["id"]==observation["issue_id"] for i in row["issues"]):
                row["issues"].append({"id":observation["issue_id"],"label":issue["label"],"kind":"evaluated_stance"})
        partitions = []
        for offset in range(0,len(public_meetings),500):
            file = public / "partitions" / ("meetings-%05d.json" % (offset//500))
            _write_json(file,{"meetings":public_meetings[offset:offset+500]})
            receipt = _receipt(file,public)
            partitions.append({k:receipt[k] for k in ("path","sha256","bytes")})
        public_csv = public / "meetings.csv"
        _csv(public_csv,["meeting_id","date","title","body","source_url","status","segments"],public_meetings,spreadsheet_safe=True)
        statuses = {}
        for row in public_meetings:
            statuses[row["status"]] = statuses.get(row["status"],0)+1
        latest_run = max(data["collection_runs"],key=lambda r:(r["started_at"],r["run_id"]),default=None)
        status = "empty" if not public_meetings else "complete"
        if latest_run and latest_run["status"] not in ("complete","completed","success"):
            status = "partial"
        manifest = {"schema":"un.archive.v1","snapshot_id":snapshot_id,"generated_at":generated_at,
            "status":status,"model_status":"accepted" if approved_models else "not_validated",
            "csv_text_safety":"Potential spreadsheet formulas are prefixed with an apostrophe in public CSV; JSON metadata preserves original values.",
            "coverage":{"meetings":len(public_meetings),"stored_meetings":len(stored_ids),
                        "segments":sum(r["segments"] for r in public_meetings),"statuses":statuses,
                        "latest_run_status":latest_run["status"] if latest_run else None,
                        "inventory_dates":len(inventory_coverage),"inventory_statuses":inventory_statuses},
            "partitions":partitions,"downloads":[_receipt(public_csv,public,rows=len(public_meetings))]}
        _write_json(public / "manifest.json",manifest)
        # Rename the complete directory only; a failed export cannot expose a
        # new manifest with missing tables or replace the previous snapshot.
        os.rename(temporary,output)
        return manifest
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
