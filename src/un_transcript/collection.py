"""Bounded official UN collection. Only metadata is used to select sources.

The transport is injectable for offline tests. Runtime state is a JSON checkpoint;
callers persist it only with the successfully committed warehouse snapshot.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import time
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ORIGIN = "https://transcripts.un.org"
SCHEMA = "un.collection.v1"
STATE_SCHEMA = "un.collection-state.v1"
RESERVED_DATES = frozenset({"2026-10-05", "2026-10-06"})
# Exact metadata from the existing sealed passage frame; never transcript text.
RESERVED_MEETINGS = frozenset({
    "asset/k18/k1830eoxgo", "asset/k1n/k1ncqarxvr", "briefing/sg/2026-10-05",
    "cedaw/3008", "cedaw/3009", "ga/c1/81/1", "ga/c2/81/2", "ga/c2/81/3",
    "ga/c3/81/5", "ga/c3/81/6/2", "ga/c4/81/3", "ga/c5/81/1", "ga/c6/81/1/2",
    "ga/c6/81/2", "hrc/63/39", "hrc/63/40", "asset/k17/k17uzy6agr",
    "asset/k1c/k1csby03jk", "asset/k1o/k1oj2b9eg1", "asset/k1p/k1pmq8xyp0",
    "asset/k1r/k1rqyj5xan", "briefing/geneva/2026-10-06", "briefing/sg/2026-10-06",
    "cedaw/3010", "cedaw/3011", "ga/c1/81/2", "ga/c2/81/4", "ga/c2/81/5",
    "ga/c3/81/7/2", "ga/c3/81/8/3", "ga/c4/81/4", "ga/c5/81/2",
    "ga/c6/81/3", "ga/c6/81/4/2", "hrc/63/41", "hrc/63/42", "sc/10233",
})
RESERVED_MEETING_DATES = {'asset/k18/k1830eoxgo': '2026-10-05', 'asset/k1n/k1ncqarxvr': '2026-10-05', 'briefing/sg/2026-10-05': '2026-10-05', 'cedaw/3008': '2026-10-05', 'cedaw/3009': '2026-10-05', 'ga/c1/81/1': '2026-10-05', 'ga/c2/81/2': '2026-10-05', 'ga/c2/81/3': '2026-10-05', 'ga/c3/81/5': '2026-10-05', 'ga/c3/81/6/2': '2026-10-05', 'ga/c4/81/3': '2026-10-05', 'ga/c5/81/1': '2026-10-05', 'ga/c6/81/1/2': '2026-10-05', 'ga/c6/81/2': '2026-10-05', 'hrc/63/39': '2026-10-05', 'hrc/63/40': '2026-10-05', 'asset/k17/k17uzy6agr': '2026-10-06', 'asset/k1c/k1csby03jk': '2026-10-06', 'asset/k1o/k1oj2b9eg1': '2026-10-06', 'asset/k1p/k1pmq8xyp0': '2026-10-06', 'asset/k1r/k1rqyj5xan': '2026-10-06', 'briefing/geneva/2026-10-06': '2026-10-06', 'briefing/sg/2026-10-06': '2026-10-06', 'cedaw/3010': '2026-10-06', 'cedaw/3011': '2026-10-06', 'ga/c1/81/2': '2026-10-06', 'ga/c2/81/4': '2026-10-06', 'ga/c2/81/5': '2026-10-06', 'ga/c3/81/7/2': '2026-10-06', 'ga/c3/81/8/3': '2026-10-06', 'ga/c4/81/4': '2026-10-06', 'ga/c5/81/2': '2026-10-06', 'ga/c6/81/3': '2026-10-06', 'ga/c6/81/4/2': '2026-10-06', 'hrc/63/41': '2026-10-06', 'hrc/63/42': '2026-10-06', 'sc/10233': '2026-10-06'}
SLUG = re.compile(r"^[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+){1,5}$")
DEFAULTS = {
    "schema": SCHEMA, "start_date": "2026-09-08", "end_date": None,
    "selection_mode": "subscription", "meetings": [], "bodies": [],
    "refresh_days": 14, "reconcile_weekday": 6, "max_inventory_days": 21,
    "max_meetings_per_run": 100, "max_bytes_per_run": 100_000_000,
    "max_response_bytes": 25_000_000, "max_inventory_pages": 50,
    "timeout_seconds": 45, "request_attempts": 3,
}


def _date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Expected an ISO calendar date")
    return date.fromisoformat(value)


def _now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_config(value):
    if not isinstance(value, dict):
        raise ValueError("Collection configuration must be an object")
    unknown = set(value) - set(DEFAULTS)
    if unknown:
        raise ValueError("Unknown collection configuration keys: " + ", ".join(sorted(unknown)))
    config = {**DEFAULTS, **copy.deepcopy(value)}
    if config["schema"] != SCHEMA:
        raise ValueError("Unsupported collection schema")
    start = _date(config["start_date"])
    if config["end_date"] is not None and _date(config["end_date"]) < start:
        raise ValueError("End date precedes start date")
    if config["selection_mode"] not in {"subscription", "meetings", "union"}:
        raise ValueError("Invalid selection mode")
    if not isinstance(config["meetings"], list) or not isinstance(config["bodies"], list):
        raise ValueError("Meetings and bodies must be lists")
    identities = {}
    for meeting in config["meetings"]:
        if not isinstance(meeting, dict) or set(meeting) != {"meeting_id", "date"}:
            raise ValueError("Exact meetings require meeting_id and date")
        if not isinstance(meeting["meeting_id"], str) or not SLUG.fullmatch(meeting["meeting_id"]):
            raise ValueError("Invalid exact meeting identifier")
        _date(meeting["date"])
        if meeting["meeting_id"] in identities and identities[meeting["meeting_id"]] != meeting["date"]:
            raise ValueError("Conflicting exact meeting dates")
        identities[meeting["meeting_id"]] = meeting["date"]
    if config["selection_mode"] == "meetings" and not identities:
        raise ValueError("Exact-meeting selection cannot be empty")
    if config["selection_mode"] == "subscription" and identities:
        raise ValueError("Use selection_mode=union to combine subscriptions and exact meetings")
    if any(not isinstance(body, str) or not body.strip() or len(body) > 120 for body in config["bodies"]):
        raise ValueError("Invalid body filter")
    limits = {
        "refresh_days": (1, 90), "reconcile_weekday": (0, 6),
        "max_inventory_days": (2, 365), "max_meetings_per_run": (1, 1000),
        "max_bytes_per_run": (1024, 1_000_000_000),
        "max_response_bytes": (1024, 50_000_000), "max_inventory_pages": (1, 100),
        "timeout_seconds": (1, 120), "request_attempts": (1, 5),
    }
    for key, (minimum, maximum) in limits.items():
        if type(config[key]) is not int or not minimum <= config[key] <= maximum:
            raise ValueError("Invalid bound: " + key)
    if config["max_inventory_days"] <= config["refresh_days"]:
        raise ValueError("Inventory budget must leave room for historical backfill")
    if config["max_bytes_per_run"] < config["max_response_bytes"]:
        raise ValueError("Run budget must cover a complete response")
    return config


def config_digest(config):
    return _sha(json.dumps(config, sort_keys=True, separators=(",", ":")).encode())


def selection_digest(config):
    return config_digest({key: config[key] for key in
                         ("schema", "start_date", "end_date", "selection_mode", "meetings", "bodies")})


def load_config(path):
    return validate_config(json.loads(Path(path).read_text(encoding="utf-8")))


def safe_url(value, *, inventory=False, meeting_id=None):
    """Reject redirects, credentials, query surprises, traversal and host aliases."""
    if not isinstance(value, str) or "\\" in value or "%" in value:
        raise ValueError("Invalid source URL")
    if any(part in {".", ".."} for part in urlsplit(value).path.split("/")):
        raise ValueError("Source path traversal refused")
    url = urljoin(ORIGIN + "/", value)
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc != "transcripts.un.org" or parts.fragment:
        raise ValueError("Unexpected transcript host or URL fragment")
    if inventory:
        if parts.path != "/en/meetings.json":
            raise ValueError("Unexpected inventory path")
        query = parse_qs(parts.query, strict_parsing=True)
        if set(query) != {"date", "xlang", "page"} or any(len(v) != 1 for v in query.values()):
            raise ValueError("Invalid inventory query")
        _date(query["date"][0])
        if query["xlang"] != ["1"] or not query["page"][0].isdigit() or int(query["page"][0]) < 1:
            raise ValueError("Invalid inventory query")
    else:
        if parts.query or not parts.path.startswith("/en/"):
            raise ValueError("Unexpected transcript path/query")
        slug = parts.path[4:].removesuffix(".json")
        if not SLUG.fullmatch(slug) or (meeting_id is not None and slug != meeting_id):
            raise ValueError("Transcript path does not match meeting identity")
    return url


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Source redirect refused; reverify the official endpoint")


class HTTPTransport:
    def __init__(self, config):
        self.config = config
        self.opener = build_opener(_NoRedirect())

    def __call__(self, url):
        # Transport itself also refuses noncanonical URLs, even if used directly.
        safe_url(url, inventory=urlsplit(url).path == "/en/meetings.json")
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "UN-Transcript-Agent/2 collection"})
        for attempt in range(self.config["request_attempts"]):
            try:
                with self.opener.open(request, timeout=self.config["timeout_seconds"]) as response:
                    raw = response.read(self.config["max_response_bytes"] + 1)
                    if len(raw) > self.config["max_response_bytes"]:
                        raise ValueError("Source response exceeds configured byte limit")
                    return {"raw": raw, "headers": {key: response.headers.get(key) for key in ("ETag", "Last-Modified", "Content-Type")}, "retrieved_at": _now()}
            except HTTPError as error:
                if error.code not in {429, 500, 502, 503, 504} or attempt + 1 == self.config["request_attempts"]:
                    raise
                retry_after = error.headers.get("Retry-After", "")
                # Long deferrals resume on the next scheduled run; never hammer.
                if retry_after.isdigit() and int(retry_after) > 30:
                    raise
                delay = int(retry_after) if retry_after.isdigit() else min(2 ** attempt, 8)
                if retry_after and not retry_after.isdigit():
                    try:
                        delay = max(0, (parsedate_to_datetime(retry_after) - datetime.now(timezone.utc)).total_seconds())
                    except (ValueError, TypeError):
                        pass
                    if delay > 30:
                        raise
            except (URLError, TimeoutError):
                if attempt + 1 == self.config["request_attempts"]:
                    raise
                delay = min(2 ** attempt, 8)
            time.sleep(delay)


def _meeting(row, expected_date):
    if not isinstance(row, dict):
        raise ValueError("Invalid inventory meeting")
    slug = row.get("slug")
    if not isinstance(slug, str) or not SLUG.fullmatch(slug):
        raise ValueError("Invalid inventory meeting identifier")
    if not isinstance(row.get("date"), str) or row["date"][:10] != expected_date:
        raise ValueError("Inventory meeting date mismatch")
    page = safe_url(row.get("pageUrl", "/en/" + slug), meeting_id=slug)
    endpoint = safe_url(row.get("jsonUrl", "/en/" + slug + ".json"), meeting_id=slug)
    if not endpoint.endswith(".json") or page.endswith(".json"):
        raise ValueError("Invalid transcript endpoint shape")
    body = row.get("body")
    if not isinstance(body, str) or not body.strip():
        # Canonical paths are usable metadata; generic asset paths are not a body.
        components = slug.split("/")
        body = "/".join(components[:2]) if components[0] == "ga" and re.fullmatch(r"c[1-6]", components[1]) else (components[0] if components[0] != "asset" else "unknown")
    return {"meeting_id": slug, "date": expected_date, "title": str(row.get("title", slug)),
            "body": body, "source_url": page, "json_url": endpoint,
            "has_transcript": row.get("hasTranscript") is True,
            "source_status": str(row.get("transcriptStatus", row.get("transcript_status", "")))}


def parse_transcript(meeting, raw):
    """Normalize exact sentence strings; raw JSON remains the original evidence."""
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data, dict) or not isinstance(data.get("video"), dict):
        raise ValueError("Unexpected transcript format")
    video = data["video"]
    if video.get("slug") != meeting["meeting_id"] or str(video.get("date", ""))[:10] != meeting["date"]:
        raise ValueError("Transcript identity or date mismatch")
    transcript = data.get("transcript")
    if not isinstance(transcript, dict) or not isinstance(transcript.get("data"), list):
        return [], "pending"
    if transcript.get("language") != "en":
        return [], "excluded_language"
    result = []
    raw_sha = _sha(raw)
    for index, segment in enumerate(transcript["data"]):
        if not isinstance(segment, dict) or not isinstance(segment.get("paragraphs", []), list):
            raise ValueError("Invalid transcript segment")
        sentences = []
        for paragraph in segment.get("paragraphs", []):
            if not isinstance(paragraph, dict) or not isinstance(paragraph.get("sentences", []), list):
                raise ValueError("Invalid transcript paragraph")
            for sentence in paragraph.get("sentences", []):
                if not isinstance(sentence, dict) or not isinstance(sentence.get("text"), str):
                    raise ValueError("Invalid transcript sentence")
                sentences.append(sentence["text"])
        text = " ".join(sentences)
        if not text.strip():
            continue
        speaker = segment.get("speaker") or {}
        if not isinstance(speaker, dict):
            raise ValueError("Invalid speaker metadata")
        clean = lambda value: value if isinstance(value, str) else ""
        group = clean(speaker.get("group"))
        affiliation = clean(speaker.get("affiliation")) or clean(speaker.get("affiliation_full"))
        result.append({
            "segment_id": _sha((meeting["meeting_id"] + "|" + raw_sha + "|" + str(index)).encode()),
            "text": text, "language": "en", "speaker": clean(speaker.get("name")),
            "country": affiliation, "capacity": "collective" if group.strip() else "unknown",
            "group_name": group, "speaker_metadata": {k: clean(speaker.get(k)) for k in ("name", "id", "affiliation", "affiliation_full", "function", "group")},
            "json_pointer": "/transcript/data/" + str(index), "start": 0, "end": len(text),
            "source_url": meeting["source_url"], "text_sha256": _sha(text.encode()),
            "timestamps_flagged": bool(transcript.get("timestamps_flagged")),
        })
    return result, "collected" if result else "empty_transcript"


def ordered_candidates(candidates, checked, stored_meeting_ids=None, *, missing_first=True):
    """Alternate missing-source retries and refreshes under unchanged run caps."""
    ordered = sorted(candidates.items(), key=lambda item: (checked.get(item[0], ""), item[1]["date"], item[0]))
    if stored_meeting_ids is None:
        return ordered  # Compatibility for callers without a verified warehouse.
    stored = frozenset(stored_meeting_ids)
    missing, refresh, unavailable = [], [], []
    for item in ordered:
        mid, meeting = item
        if not meeting['has_transcript'] or mid in RESERVED_MEETINGS or meeting['date'] in RESERVED_DATES:
            unavailable.append(item)
        elif mid in stored:
            refresh.append(item)
        else:
            missing.append(item)
    result = []
    queues = (missing, refresh) if missing_first else (refresh, missing)
    for index in range(max(len(missing), len(refresh))):
        for queue in queues:
            if index < len(queue): result.append(queue[index])
    return result + unavailable


class Collector:
    def __init__(self, config, transport=None):
        self.config = validate_config(config)
        self.transport = transport or HTTPTransport(self.config)
        self._bytes = 0

    def _request(self, url):
        if self._bytes + self.config["max_response_bytes"] > self.config["max_bytes_per_run"]:
            raise ValueError("Insufficient byte budget for a bounded response")
        response = self.transport(url)
        if isinstance(response, bytes):
            response = {"raw": response}
        if not isinstance(response, dict) or not isinstance(response.get("raw"), bytes):
            raise ValueError("Transport must return original response bytes")
        raw = response["raw"]
        if len(raw) > self.config["max_response_bytes"] or self._bytes + len(raw) > self.config["max_bytes_per_run"]:
            raise ValueError("Collection byte budget exceeded")
        self._bytes += len(raw)
        return {"raw": raw, "headers": response.get("headers", {}), "retrieved_at": response.get("retrieved_at", _now()), "sha256": _sha(raw)}

    def collect(self, as_of: date, state=None, *, prior_config=None, stored_meeting_ids=None):
        if isinstance(as_of, str):
            as_of = _date(as_of)
        if not isinstance(as_of, date):
            raise ValueError("as_of must be a calendar date")
        config = self.config
        previous = copy.deepcopy(state or {})
        if previous and previous.get("schema") != STATE_SCHEMA:
            raise ValueError("Unsupported collection checkpoint")
        digest = config_digest(config)
        selection = selection_digest(config)
        prior_selection = previous.get("selection_sha256")
        # Legacy checkpoints may inherit a selection only from the exact config
        # recorded for their verified snapshot, bound by the original digest.
        if prior_selection is None and prior_config is not None:
            prior_config = validate_config(prior_config)
            if config_digest(prior_config) == previous.get("config_sha256"):
                prior_selection = selection_digest(prior_config)
        reset = bool(previous and previous.get("config_sha256") != digest and prior_selection != selection)
        if reset:
            previous = {}
        start = _date(config["start_date"])
        end = min(as_of, _date(config["end_date"])) if config["end_date"] else as_of
        exact = {row["meeting_id"]: row["date"] for row in config["meetings"] if _date(row["date"]) <= as_of}
        allowed_dates = set()
        if config["selection_mode"] != "meetings":
            allowed_dates = {(start + timedelta(days=n)).isoformat() for n in range(max(0, (end-start).days + 1))}
        allowed_dates.update(exact.values())
        recent = sorted((day for day in allowed_dates if _date(day) >= as_of - timedelta(days=config["refresh_days"] - 1)), reverse=True)
        completed = set(previous.get("completed_dates", [])) & allowed_dates
        pending = (set(previous.get("pending_dates", [])) & allowed_dates) | (allowed_dates - completed)
        week = (as_of - timedelta(days=(as_of.weekday() - config["reconcile_weekday"]) % 7)).isoformat()
        inventory_pending = (set(previous.get("inventory_pending_dates", allowed_dates)) & allowed_dates) | (allowed_dates - completed)
        if previous.get("reconciliation_week") != week:
            pending |= allowed_dates
            inventory_pending |= allowed_dates
        pending |= inventory_pending
        date_checks = previous.get("checked_dates", {})
        pending_order = sorted(pending - set(recent), key=lambda day: (date_checks.get(day, ""), day))
        selected_dates = (recent + pending_order)[:config["max_inventory_days"]]
        items, coverage, inventory = [], [], []
        candidates = {}
        checked = previous.get("checked_meetings", {})
        seen = previous.get("known_meetings", {})
        self._bytes = 0
        for day in selected_dates:
            if day in RESERVED_DATES:
                for mid in sorted(RESERVED_MEETINGS):
                    if RESERVED_MEETING_DATES[mid] == day and (config["selection_mode"] != "meetings" or exact.get(mid) == day):
                        coverage.append({"meeting_id": mid, "date": day, "status": "excluded_reserved", "detail": "Sealed evaluation meeting; no source request"})
                coverage.append({"meeting_id": "inventory:" + day, "date": day, "status": "excluded_reserved", "detail": "Reserved date excluded before network access, including possible alias routes"})
                completed.add(day); pending.discard(day); inventory_pending.discard(day)
                continue
            if self._bytes + config["max_response_bytes"] > config["max_bytes_per_run"]:
                pending.add(day)
                coverage.append({"meeting_id": "inventory:" + day, "date": day, "status": "deferred", "detail": "Collection byte budget reserved for a complete response"})
                continue
            date_checks[day] = _now()
            found, pages = [], []
            try:
                total = None
                for page in range(1, config["max_inventory_pages"] + 1):
                    url = safe_url(ORIGIN + "/en/meetings.json?" + urlencode({"date": day, "xlang": 1, "page": page}), inventory=True)
                    response = self._request(url)
                    pages.append({"date": day, "page": page, "source_url": url, **response})
                    data = json.loads(response["raw"].decode("utf-8-sig"))
                    if not isinstance(data, dict) or not isinstance(data.get("meetings"), list) or type(data.get("page")) is not int or data["page"] != page or type(data.get("total")) is not int or data["total"] < 0 or type(data.get("hasMore")) is not bool:
                        raise ValueError("Unexpected inventory format")
                    if total is not None and total != data["total"]:
                        raise ValueError("Inventory total changed during pagination")
                    total = data["total"]
                    rows = [_meeting(row, day) for row in data["meetings"]]
                    found.extend(rows)
                    if not data["hasMore"]:
                        break
                else:
                    raise ValueError("Inventory page limit reached before completion")
                if len(found) != total or len({row["meeting_id"] for row in found}) != total:
                    raise ValueError("Inventory count or duplicate identity mismatch")
                inventory.extend(pages)
                completed.add(day); pending.discard(day); inventory_pending.discard(day)
                eligible = []
                for row in found:
                    is_exact = exact.get(row["meeting_id"]) == day
                    body_match = not config["bodies"] or row["body"].casefold() in {b.casefold() for b in config["bodies"]} or ("ga" in {b.casefold() for b in config["bodies"]} and row["body"].casefold().startswith("ga/"))
                    subscription = config["selection_mode"] != "meetings" and start <= _date(day) <= end and body_match
                    if is_exact or subscription:
                        eligible.append(row)
                        candidates[row["meeting_id"]] = row
                        seen[row["meeting_id"]] = row
                coverage.append({"meeting_id": "inventory:" + day, "date": day, "status": "inventory_complete", "detail": json.dumps({"meetings": total, "selected": len(eligible)})})
                for mid, when in exact.items():
                    if when == day and mid not in {r["meeting_id"] for r in found}:
                        coverage.append({"meeting_id": mid, "date": day, "status": "not_in_inventory", "detail": "Exact selection is absent from the complete inventory"})
                        pending.add(day)
                for mid, row in seen.items():
                    if row["date"] == day and mid not in {r["meeting_id"] for r in found}:
                        coverage.append({"meeting_id": mid, "date": day, "status": "no_longer_listed", "detail": "Previously selected meeting absent from latest complete inventory"})
            except (ValueError, UnicodeError, HTTPError, URLError, TimeoutError, OSError) as error:
                # Keep partial inventory responses as private evidence, never use
                # their rows as a complete selection or advance the watermark.
                inventory.extend(pages)
                pending.add(day)
                coverage.append({"meeting_id": "inventory:" + day, "date": day, "status": "inventory_failed", "detail": type(error).__name__ + ": " + str(error)[:300]})
        # Deferred and failed dates are inventoried again before retrying sources.
        attempted = 0
        stored = None if stored_meeting_ids is None else frozenset(stored_meeting_ids)
        next_queue = previous.get('next_source_queue', 'missing')
        for mid, meeting in ordered_candidates(candidates, checked, stored, missing_first=next_queue != 'refresh'):
            row = {"meeting_id": mid, "date": meeting["date"], "status": "unavailable", "detail": ""}
            if mid in RESERVED_MEETINGS or meeting["date"] in RESERVED_DATES:
                row.update(status="excluded_reserved", detail="Sealed evaluation meeting; no source request")
            elif not meeting["has_transcript"]:
                row["status"] = "pending" if meeting["source_status"].lower() in {"pending", "queued", "processing", "preparing"} else "unavailable"
                pending.add(meeting["date"])
            elif attempted >= config["max_meetings_per_run"] or self._bytes + config["max_response_bytes"] > config["max_bytes_per_run"]:
                row.update(status="deferred", detail="Run budget reached; retry from verified inventory")
                pending.add(meeting["date"])
            else:
                attempted += 1
                if stored is not None:
                    next_queue = 'missing' if mid in stored else 'refresh'
                checked[mid] = _now()
                try:
                    response = self._request(safe_url(meeting["json_url"], meeting_id=mid))
                    segments, status = parse_transcript(meeting, response["raw"])
                    items.append({"meeting": meeting, "segments": segments, **response})
                    row.update(status=status, detail="", sha256=response["sha256"], segments=len(segments))
                    if status in {"pending", "empty_transcript"}:
                        pending.add(meeting["date"])
                except (ValueError, UnicodeError, HTTPError, URLError, TimeoutError, OSError) as error:
                    row.update(status="failed", detail=type(error).__name__ + ": " + str(error)[:300])
                    pending.add(meeting["date"])
            coverage.append(row)
        next_state = {"schema": STATE_SCHEMA, "config_sha256": digest, "selection_sha256": selection, "completed_dates": sorted(completed),
                      "pending_dates": sorted(pending), "checked_meetings": checked, "known_meetings": seen,
                      "reconciliation_week": week, "reconciliation_pending": bool(pending),
                      "inventory_pending_dates": sorted(inventory_pending), "as_of": as_of.isoformat(), "checked_dates": date_checks}
        if stored is not None:
            next_state['next_source_queue'] = next_queue
        historical = len(allowed_dates - set(recent))
        historical_slots = config["max_inventory_days"] - len(recent)
        progress = {"week_start": week, "selected_dates": len(allowed_dates),
                    "pending_dates": len(inventory_pending), "recent_dates": len(recent), "complete": not inventory_pending,
                    "max_dates_per_run": config["max_inventory_days"],
                    "nominal_weekly_capacity_sufficient": historical <= 7 * historical_slots}
        return {"items": items, "coverage": coverage, "state": next_state, "inventory": inventory,
                "inventory_progress": progress,
                "bytes_downloaded": self._bytes, "selection_reset": reset}
