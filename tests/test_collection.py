"""Source-free production collector tests. No requests to actual UN transcripts."""
import copy
import hashlib
import json
import unittest
from datetime import date
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from un_transcript.collection import (
    Collector, DEFAULTS, RESERVED_MEETINGS, RESERVED_MEETING_DATES, safe_url,
    validate_config, parse_transcript,
)


def encode(value):
    return json.dumps(value, ensure_ascii=False).encode()


def meeting(mid="ga/81/99", day="2026-11-04", **kwargs):
    return dict(slug=mid, date=day, title="Synthetic meeting", pageUrl="/en/" + mid,
                jsonUrl="/en/" + mid + ".json", hasTranscript=True, **kwargs)


def source(row, language="en", text="We support the proposed synthetic measure.", speaker=None):
    return encode({"video": {"slug": row["slug"], "date": row["date"]}, "transcript": {
        "language": language, "data": [{"speaker": speaker or {"affiliation": "USA"},
        "paragraphs": [{"sentences": [{"text": text}]}]}]}})


class Transport:
    def __init__(self, rows=None, sources=None):
        self.rows = rows or []
        self.sources = sources or {r["slug"]: source(r) for r in self.rows}
        self.calls = []
        self.fail_dates = set()

    def __call__(self, url):
        self.calls.append(url)
        if "/meetings.json?" in url:
            query = parse_qs(urlsplit(url).query)
            day = query["date"][0]
            if day in self.fail_dates:
                raise OSError("synthetic outage")
            rows = [r for r in self.rows if r["date"] == day]
            return encode({"page": int(query["page"][0]), "meetings": rows, "total": len(rows), "hasMore": False})
        mid = urlsplit(url).path[4:-5]
        value = self.sources[mid]
        if isinstance(value, Exception):
            raise value
        return {"raw": value, "headers": {"ETag": "synthetic"}, "retrieved_at": "2026-11-05T12:00:00Z"}


def config(**overrides):
    return {**DEFAULTS, "start_date": "2026-11-04", "end_date": "2026-11-04", **overrides}


class CollectionTests(unittest.TestCase):
    def test_config_rejects_invalid_dates_unknown_keys_and_missing_backfill_capacity(self):
        for override in ({"start_date": "2026-02-30"}, {"request_attempts": True}, {"hostname": "other"},
                         {"max_inventory_days": 14}, {"selection_mode": "meetings"}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                validate_config(config(**override))

    def test_original_bytes_and_offsets_and_affiliation_capacity(self):
        row = meeting()
        raw = b"\xef\xbb\xbf" + source(row, text="  caf\u00e9  ")
        transport = Transport([row], {row["slug"]: raw})
        result = Collector(config(), transport).collect(date(2026, 11, 5))
        item = result["items"][0]
        self.assertEqual(item["raw"], raw)
        self.assertEqual(item["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(item["headers"]["ETag"], "synthetic")
        segment = item["segments"][0]
        self.assertEqual(segment["text"], "  caf\u00e9  ")
        self.assertEqual(segment["end"], len(segment["text"]))
        self.assertEqual(segment["country"], "USA")
        self.assertEqual(segment["capacity"], "unknown")
        self.assertEqual(segment["json_pointer"], "/transcript/data/0")
        self.assertEqual(result["inventory"][0]["raw"], transport(result["inventory"][0]["source_url"]))

    def test_collective_attribution_remains_collective(self):
        row = meeting()
        result = Collector(config(), Transport([row], {row["slug"]: source(row, speaker={"affiliation": "USA", "group": "Group of synthetic states"})})).collect("2026-11-04")
        self.assertEqual(result["items"][0]["segments"][0]["capacity"], "collective")

    def test_unsafe_or_mismatched_source_endpoint_never_downloaded(self):
        for endpoint in ("https://evil.test/a.json", "/en/sc/2.json", "/en/ga/81/99.json?token=bad"):
            row = meeting(); row["jsonUrl"] = endpoint
            transport = Transport([row])
            result = Collector(config(), transport).collect("2026-11-04")
            self.assertEqual(result["items"], [])
            self.assertTrue(all("meetings.json?" in u for u in transport.calls))
            self.assertEqual(result["coverage"][0]["status"], "inventory_failed")

    def test_url_validation_refuses_aliases_credentials_traversal_queries(self):
        for url in ("http://transcripts.un.org/en/ga/81/1.json", "https://x@transcripts.un.org/en/ga/81/1.json",
                    "https://transcripts.un.org:443/en/ga/81/1.json", "/en/%2e%2e/admin/x.json", "/en/ga/a/../81/1.json",
                    "/en/ga/81/1.json#fragment", "/en/ga/81/1.json?foo=bar"):
            with self.subTest(url=url), self.assertRaises(ValueError): safe_url(url)

    def test_all_reserved_dates_and_exact_ids_blocked_before_network(self):
        transport = Transport()
        result = Collector(config(start_date="2026-10-05", end_date="2026-10-06"), transport).collect("2026-10-06")
        self.assertEqual(transport.calls, [])
        self.assertEqual({x["meeting_id"] for x in result["coverage"] if not x["meeting_id"].startswith("inventory:")}, RESERVED_MEETINGS)
        self.assertEqual(len(RESERVED_MEETINGS), 37)
        # Mislabeled inventory dates cannot bypass a protected exact identity.
        reserved = next(iter(RESERVED_MEETINGS)); row = meeting(reserved)
        transport = Transport([row])
        result = Collector(config(), transport).collect("2026-11-04")
        self.assertEqual(result["items"], [])
        self.assertTrue(all("meetings.json?" in u for u in transport.calls))
        self.assertEqual(result["coverage"][-1]["status"], "excluded_reserved")

    def test_pagination_only_used_when_complete(self):
        one, two = meeting(), meeting("sc/99")
        calls = []
        def request(url):
            calls.append(url)
            if "meetings.json" not in url: return source(one)
            page = int(parse_qs(urlsplit(url).query)["page"][0])
            return encode({"page": page, "total": 2 if page == 1 else 3, "hasMore": page == 1, "meetings": [one if page == 1 else two]})
        result = Collector(config(), request).collect("2026-11-04")
        self.assertEqual(result["items"], [])
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(result["inventory"]), 2)
        self.assertIn("2026-11-04", result["state"]["pending_dates"])

    def test_duplicate_inventory_id_rejected(self):
        row = meeting(); result = Collector(config(), Transport([row, row])).collect("2026-11-04")
        self.assertEqual(result["items"], [])
        self.assertEqual(result["coverage"][0]["status"], "inventory_failed")

    def test_non_english_and_empty_pending_are_distinct_and_raw_retained(self):
        rows = [meeting("ga/81/1"), meeting("ga/81/2"), meeting("ga/81/3")]
        sources = {rows[0]["slug"]: source(rows[0], language="fr"), rows[1]["slug"]: source(rows[1], text=""),
                   rows[2]["slug"]: encode({"video": {"slug": rows[2]["slug"], "date": rows[2]["date"]}})}
        result = Collector(config(), Transport(rows, sources)).collect("2026-11-04")
        self.assertEqual(len(result["items"]), 3)
        self.assertEqual({x["status"] for x in result["coverage"] if not x["meeting_id"].startswith("inventory:")}, {"excluded_language", "empty_transcript", "pending"})

    def test_response_identity_must_match_inventory(self):
        row = meeting(); raw = source(meeting("sc/99"))
        result = Collector(config(), Transport([row], {row["slug"]: raw})).collect("2026-11-04")
        self.assertEqual(result["items"], [])
        self.assertEqual(result["coverage"][-1]["status"], "failed")

    def test_exact_selection_and_body_filters_precede_source_fetch(self):
        rows = [meeting(), meeting("sc/99"), meeting("ga/c3/81/99")]
        transport = Transport(rows)
        selected = [{"meeting_id": "sc/99", "date": "2026-11-04"}]
        result = Collector(config(selection_mode="meetings", meetings=selected), transport).collect("2026-11-04")
        self.assertEqual([x["meeting"]["meeting_id"] for x in result["items"]], ["sc/99"])
        result = Collector(config(bodies=["ga"]), Transport(rows)).collect("2026-11-04")
        self.assertEqual({x["meeting"]["meeting_id"] for x in result["items"]}, {"ga/81/99", "ga/c3/81/99"})

    def test_budget_resumes_other_meetings_and_retries_failure(self):
        rows = [meeting("ga/81/1"), meeting("ga/81/2")]
        transport = Transport(rows)
        first = Collector(config(max_meetings_per_run=1), transport).collect("2026-11-04")
        self.assertEqual(len(first["items"]), 1)
        second = Collector(config(max_meetings_per_run=1), transport).collect("2026-11-04", first["state"])
        self.assertNotEqual(first["items"][0]["meeting"]["meeting_id"], second["items"][0]["meeting"]["meeting_id"])
        self.assertIn("deferred", {row["status"] for row in first["coverage"]})
        transport.sources[rows[0]["slug"]] = OSError("synthetic outage")
        failed = Collector(config(), transport).collect("2026-11-04")
        self.assertIn("failed", {row["status"] for row in failed["coverage"]})
        transport.sources[rows[0]["slug"]] = source(rows[0])
        retry = Collector(config(), transport).collect("2026-11-05", failed["state"])
        self.assertEqual(len(retry["items"]), 2)

    def test_daily_backfill_and_failed_date_do_not_starve_later_dates(self):
        conf = config(start_date="2026-10-01", end_date="2026-11-04", refresh_days=1, max_inventory_days=3)
        transport = Transport(); transport.fail_dates = {"2026-10-01", "2026-10-02"}
        first = Collector(conf, transport).collect("2026-11-04")
        second = Collector(conf, transport).collect("2026-11-04", first["state"])
        self.assertIn("2026-10-03", second["state"]["completed_dates"])
        self.assertIn("2026-10-04", second["state"]["completed_dates"])
        self.assertIn("2026-10-01", second["state"]["pending_dates"])

    def test_weekly_reconciliation_rechecks_old_completed_dates(self):
        conf = config(start_date="2026-10-20", end_date="2026-10-20", refresh_days=1, max_inventory_days=2)
        transport = Transport()
        first = Collector(conf, transport).collect("2026-11-03")
        self.assertEqual(first["state"]["pending_dates"], [])
        transport.calls.clear()
        Collector(conf, transport).collect("2026-11-04", first["state"])
        self.assertEqual(transport.calls, [])
        Collector(conf, transport).collect("2026-11-08", first["state"])
        self.assertEqual(len(transport.calls), 1)

    def test_invalid_utf8_and_over_budget_responses_fail_without_items(self):
        row = meeting()
        for raw in (b'{"bad":"\xff"}', b" " * 1025):
            result = Collector(config(max_response_bytes=1024, max_bytes_per_run=4096), Transport([row], {row["slug"]: raw})).collect("2026-11-04")
            self.assertEqual(result["items"], [])
            self.assertEqual(result["coverage"][-1]["status"], "failed")

    def test_revision_retains_bytes_and_new_source_bound_segment_id(self):
        row = meeting(); transport = Transport([row])
        first = Collector(config(), transport).collect("2026-11-04")
        transport.sources[row["slug"]] = source(row, text="A revised synthetic statement.")
        second = Collector(config(), transport).collect("2026-11-04", first["state"])
        self.assertNotEqual(first["items"][0]["sha256"], second["items"][0]["sha256"])
        self.assertNotEqual(first["items"][0]["segments"][0]["segment_id"], second["items"][0]["segments"][0]["segment_id"])
        self.assertEqual(first["items"][0]["segments"][0]["text"], "We support the proposed synthetic measure.")

    def test_missing_exact_selection_is_not_substituted(self):
        conf = config(selection_mode="meetings", meetings=[{"meeting_id": "sc/99", "date": "2026-11-04"}])
        result = Collector(conf, Transport([meeting()])).collect("2026-11-04")
        self.assertEqual(result["items"], [])
        self.assertIn("not_in_inventory", {r["status"] for r in result["coverage"]})

    def test_new_configuration_resets_checkpoint_without_editing_input_state(self):
        first = Collector(config(), Transport()).collect("2026-11-04")
        previous = copy.deepcopy(first["state"])
        result = Collector(config(bodies=["sc"]), Transport()).collect("2026-11-04", previous)
        self.assertTrue(result["selection_reset"])
        self.assertEqual(previous, first["state"])


if __name__ == "__main__":
    unittest.main()
