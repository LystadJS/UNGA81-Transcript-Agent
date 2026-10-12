#!/usr/bin/env python3
"""Standard-library, synthetic-only tests for the private annotation adapter."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("private_review_adapter", ROOT / "prepare_review.py")
assert SPEC and SPEC.loader
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)

SOURCE_HEADERS = adapter.FIELDS["sources"].split()
PASSAGE_HEADERS = adapter.FIELDS["passages"].split()


def save_csv(path: Path, headers: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


class ReviewPacketTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="un-country-positions-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.workspace = self.root / "review"
        self.workspace.mkdir()
        (self.workspace / "texts").mkdir()
        (self.workspace / "bundle.json").write_text(
            json.dumps({"schema": "un.review.v1", "dataset_kind": "unreviewed"}),
            encoding="utf-8")
        raw = "Élan 🌐 — fictional policy language only.\nA second invented passage."
        (self.workspace / "texts" / "s1.txt").write_text(raw, encoding="utf-8")
        self.raw = raw
        self.source = {
            "source_id": "syn1", "iso3": "ALP", "event_date": "2026-09-25",
            "available_at": "2026-09-25T20:00:00Z",
            "genre": "general_debate", "language": "en",
            "source_url": "https://example.org/fictional-record",
            "text_path": "texts/s1.txt",
            "text_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            "duplicate_group": "family-1",
        }
        self.passages = [
            {"passage_id": "p1", "source_id": "syn1",
             "start": "0", "end": str(raw.index("\n")), "quote": raw.split("\n")[0]},
            {"passage_id": "p2", "source_id": "syn1",
             "start": str(raw.index("\n")+1), "end": str(len(raw)),
             "quote": raw.split("\n")[1]},
        ]
        self.save()
        self.packet = self.root / "private-packet.json"

    def save(self) -> None:
        save_csv(self.workspace / "sources.csv", SOURCE_HEADERS, [self.source])
        save_csv(self.workspace / "passages.csv", PASSAGE_HEADERS, self.passages)

    def prepare(self, **overrides) -> dict:
        args = {
            "workspace": self.workspace,
            "codebook": ROOT / "propositions.v1.json",
            "output": self.packet,
            "count": 2,
            "seed": 20261008,
        }
        args.update(overrides)
        return adapter.prepare(SimpleNamespace(**args))

    def test_produces_unlabeled_source_bound_packet(self) -> None:
        result = self.prepare()
        packet = json.loads(self.packet.read_text(encoding="utf-8"))
        self.assertEqual(result["selected"], 2)
        self.assertEqual(packet["schema"], adapter.SCHEMA)
        self.assertFalse(packet["publication_eligible"])
        self.assertFalse(packet["model_predictions_included"])
        self.assertEqual(len(packet["items"]), 2)
        self.assertEqual(packet["sampling"]["source_rows"], 1)
        self.assertEqual(packet["items"][0]["actor_capacity"], "recorded_affiliation_only")
        self.assertNotIn("label", packet["items"][0])
        self.assertNotIn("stance", packet["items"][0])
        self.assertEqual(
            packet["packet_sha256"], adapter.sha256(
                adapter.encoded({k: v for k, v in packet.items() if k != "packet_sha256"})))
        for item in packet["items"]:
            self.assertEqual(
                self.raw[item["start"]:item["end"]], item["quote"])

    def test_changed_original_sha_or_quote_aborts(self) -> None:
        self.source["text_sha256"] = "0"*64
        self.save()
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            self.prepare()
        self.source["text_sha256"] = hashlib.sha256(self.raw.encode()).hexdigest()
        self.passages[0]["quote"] = "wrong quote"
        self.save()
        with self.assertRaisesRegex(ValueError, "quote/offset"):
            self.prepare()

    def test_reserved_meeting_is_refused_before_source_read(self) -> None:
        self.source["event_date"] = "2026-10-05"
        self.save()
        with self.assertRaisesRegex(ValueError, "Reserved"):
            self.prepare()

    def test_private_export_does_not_create_gold_labels(self) -> None:
        self.prepare()
        packet = json.loads(self.packet.read_text(encoding="utf-8"))
        draft = {
            "schema": adapter.DRAFT,
            "packet_sha256": packet["packet_sha256"],
            "reviewer_id": "human-reviewer-test",
            "decisions": [
                {"item_id": packet["items"][0]["item_id"],
                 "issue_label": "relevant", "stance_label": "support",
                 "rationale": "Fictional statement directly supports the proposition.",
                 "reviewed_at": "2026-10-08T19:00:00Z"}
            ]
        }
        draft_path = self.root / "draft.json"
        draft_path.write_text(json.dumps(draft), encoding="utf-8")
        annotations = self.root / "candidate-annotations.csv"
        result = adapter.export(SimpleNamespace(
            packet=self.packet, draft=draft_path, output=annotations))
        self.assertEqual(result["rows"], 2)
        self.assertIn("UNFINALIZED", result["status"])
        self.assertFalse((self.root / "adjudications.csv").exists())
        with annotations.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual({row["task"] for row in rows}, {"issue", "stance"})
        self.assertEqual({row["reviewer_id"] for row in rows}, {"human-reviewer-test"})

    def test_invalid_nonrelevant_support_refused(self) -> None:
        self.prepare()
        packet = json.loads(self.packet.read_text(encoding="utf-8"))
        draft = {
            "schema": adapter.DRAFT,
            "packet_sha256": packet["packet_sha256"],
            "reviewer_id": "reviewer-test",
            "decisions": [{
                "item_id": packet["items"][0]["item_id"],
                "issue_label": "not_relevant", "stance_label": "support",
                "rationale": "This example deliberately contradicts its issue label.",
                "reviewed_at": "2026-10-08T19:00:00Z",
            }]
        }
        draft_path = self.root / "bad-draft.json"
        draft_path.write_text(json.dumps(draft), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "cannot be coded"):
            adapter.export(SimpleNamespace(
                packet=self.packet, draft=draft_path, output=self.root / "invalid.csv"))

    def test_overwrite_and_public_output_refused(self) -> None:
        self.prepare()
        with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
            self.prepare()
        with self.assertRaisesRegex(ValueError, "must not be written"):
            self.prepare(output=ROOT / "forbidden-private-packet.json")


# Native CI already invokes this legacy entry point. Include the independently
# defined grouped/split pilot tests without editing coordinator-owned CI.
from test_pilot_pipeline import SourceSeparatedPilotTests  # noqa: E402

if __name__ == "__main__":
    unittest.main(verbosity=2)
