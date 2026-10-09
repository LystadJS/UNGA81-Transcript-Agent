#!/usr/bin/env python3
"""Synthetic unit tests for frozen, source-separated diplomatic stance pilot."""
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
SPEC = importlib.util.spec_from_file_location("supervised_pilot_pipeline",
                                              ROOT / "pilot_pipeline.py")
assert SPEC and SPEC.loader
PILOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PILOT)

def write_rows(path: Path, headers: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


class SourceSeparatedPilotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="synthetic-source-split-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ws = self.root / "private-synthetic"
        self.ws.mkdir()
        (self.ws / "texts").mkdir()
        (self.ws / "bundle.json").write_text(json.dumps({
            "schema": "un.review.v1", "dataset_kind": "unreviewed"
        }), encoding="utf-8")
        self.source_rows = []
        self.quality_rows = []
        self.passage_rows = []
        self.codebook = ROOT / "propositions.v1.json"
        self.add_corpus(15)
        self.flush()

    def add_corpus(self, actors: int) -> None:
        for actor in range(actors):
            iso = chr(65 + (actor // 26)) + chr(65 + actor % 26) + "Z"
            for yr in (2018, 2020, 2022):
                sid = f"fictional-{iso}-{yr}"
                text = (
                    f"The imaginary delegation {iso} discusses Cuba and the embargo.\n"
                    f"The invented delegation {iso} refers to Ukraine's territorial integrity.\n"
                    f"These fictional proceedings concern the conference schedule.\n"
                )
                raw = text.encode("utf-8")
                text_name = f"texts/{sid}.txt"
                (self.ws / text_name).write_bytes(raw)
                self.source_rows.append({
                    "source_id": sid, "iso3": iso,
                    "event_date": f"{yr}-09-24",
                    "available_at": "", "genre": "general_debate",
                    "language": "en",
                    "source_url": "https://documents.un.org/synthetic-fixture-no-record",
                    "text_path": text_name,
                    "text_sha256": hashlib.sha256(raw).hexdigest(),
                    "duplicate_group": sid,
                })
                self.quality_rows.append({
                    "source_id": sid,
                    "official_document_symbol": f"A/{yr - 1945}/PV.5",
                    "original_pdf_sha256": hashlib.sha256(
                        (sid + "fictional PDF digest placeholder").encode()).hexdigest(),
                    "match_status": "strong", "source_method": "official_pv",
                    "country_capacity": "individual", "source_family_id": sid,
                    "verification_basis": "original_pv_full_speech",
                })
                offset = 0
                for i, paragraph in enumerate(text.splitlines(True), start=1):
                    quote = paragraph.rstrip("\n")
                    self.passage_rows.append({
                        "passage_id": f"{sid}-p{i:02d}", "source_id": sid,
                        "start": str(offset), "end": str(offset + len(quote)),
                        "quote": quote,
                    })
                    offset += len(paragraph)

    def flush(self) -> None:
        write_rows(self.ws / "sources.csv", PILOT.review.FIELDS["sources"].split(),
                   self.source_rows)
        write_rows(self.ws / "source_quality.csv", PILOT.QUALITY_HEADERS,
                   self.quality_rows)
        write_rows(self.ws / "passages.csv", PILOT.review.FIELDS["passages"].split(),
                   self.passage_rows)

    def plan(self) -> dict:
        result, kept = PILOT.make_plan(self.ws, self.codebook, 20261009)
        self.assertEqual(result["human_stance_labels"], 0)
        self.assertEqual(result["gold_stance_labels"], 0)
        return result

    def packet(self, plan: dict, split: str = "train",
               count: int = 4, authorized: bool = False) -> dict:
        location = self.root / "plan_for_packet.json"
        location.write_text(json.dumps(plan), encoding="utf-8")
        return PILOT.make_packet(self.ws, location, self.codebook,
                                 split, count, 20261009, authorized)

    def test_frozen_country_and_year_separated_plan(self) -> None:
        plan = self.plan()
        PILOT.verified_plan(plan)
        assignments = [r for r in plan["assignment"] if r["split"] in PILOT.SPLITS]
        self.assertGreater(len(assignments), 0)
        for split in PILOT.SPLITS:
            self.assertGreaterEqual(
                plan["population"]["countries_by_split"][split], 2)
            self.assertGreaterEqual(
                plan["population"]["sources_by_split"][split], 2)
        years = {split: set() for split in PILOT.SPLITS}
        actors = {split: set() for split in PILOT.SPLITS}
        hashes = {split: set() for split in PILOT.SPLITS}
        for row in assignments:
            years[row["split"]].add(int(row["event_date"][:4]))
            actors[row["split"]].add(row["iso3"])
            hashes[row["split"]].add(row["text_sha256"])
        self.assertEqual(years["train"], {2018})
        self.assertEqual(years["calibration"], {2020})
        self.assertEqual(years["test"], {2022})
        for one in PILOT.SPLITS:
            for other in PILOT.SPLITS:
                if one != other:
                    self.assertFalse(actors[one] & actors[other])
                    self.assertFalse(hashes[one] & hashes[other])
        self.assertEqual(plan["source_schema"], "un.review.v1")
        self.assertFalse(plan["publication_eligible"])

    def test_determinism_and_private_csv_exports(self) -> None:
        plan = self.plan()
        again, _ = PILOT.make_plan(self.ws, self.codebook, 20261009)
        self.assertEqual(plan["plan_sha256"], again["plan_sha256"])
        output = self.root / "private-output"
        data = PILOT.write_plan(self.ws, self.codebook, output, 20261009)
        self.assertEqual(data["plan_sha256"], plan["plan_sha256"])
        with (output / "splits.csv").open(encoding="utf-8", newline="") as handle:
            splits = list(csv.DictReader(handle))
        self.assertEqual(set(splits[0]), {"source_id", "split"})
        self.assertTrue(all(r["split"] in PILOT.SPLITS for r in splits))
        with self.assertRaisesRegex(ValueError, "overwrite"):
            PILOT.write_plan(self.ws, self.codebook, output, 20261009)

    def test_corrupted_source_bytes_rejected(self) -> None:
        path = self.ws / self.source_rows[0]["text_path"]
        path.write_text("Changed after source SHA freeze!", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            self.plan()

    def test_unverified_original_qc_withheld(self) -> None:
        self.quality_rows[0]["match_status"] = "partial"
        self.flush()
        plan = self.plan()
        row = next(r for r in plan["assignment"]
                   if r["source_id"] == self.quality_rows[0]["source_id"])
        self.assertEqual(row["split"], "withheld")
        self.assertEqual(row["reason"], "original_source_or_attribution_not_eligible")

    def test_reserved_source_metadata_only_never_opened(self) -> None:
        src = dict(self.source_rows[0])
        src["source_id"] = "sealed-metadata-only"
        src["event_date"] = "2026-10-05"
        src["text_path"] = "texts/never-open-this-file.txt"
        src["text_sha256"] = "0"*64
        self.source_rows.append(src)
        self.flush()
        plan = self.plan()
        sealed = next(r for r in plan["assignment"]
                      if r["source_id"] == "sealed-metadata-only")
        self.assertEqual(sealed["split"], "withheld")
        self.assertEqual(sealed["reason"], "reserved_meeting_metadata_only")
        with self.assertRaisesRegex(ValueError, "reserved"):
            self.packet(plan)

    def test_cross_country_duplicate_withheld(self) -> None:
        first = self.source_rows[0]
        second = self.source_rows[3]
        second["text_sha256"] = first["text_sha256"]
        # Give both sources genuinely identical bytes so integrity holds:
        (self.ws / second["text_path"]).write_bytes(
            (self.ws / first["text_path"]).read_bytes()
        )
        self.flush()
        plan = self.plan()
        for sid in [first["source_id"], second["source_id"]]:
            record = next(r for r in plan["assignment"] if r["source_id"] == sid)
            self.assertEqual(record["split"], "withheld")
            self.assertEqual(record["reason"], "cross_actor_duplicate_or_family")

    def test_plan_manifest_tampering_rejected(self) -> None:
        p = self.plan()
        p["assignment"][0]["split"] = "test"
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            PILOT.verified_plan(p)

    def test_manifest_or_codebook_drift_rejected(self) -> None:
        p = self.plan()
        self.packet(p)
        self.source_rows[0]["available_at"] = "2018-10-01T00:00:00Z"
        self.flush()
        with self.assertRaisesRegex(ValueError, "CSV drift"):
            self.packet(p)

    def test_blind_prop_sampling_with_nonhits_and_context(self) -> None:
        p = self.plan()
        packet = self.packet(p, count=4)
        self.assertEqual(packet["source_split"], "train")
        self.assertEqual(packet["human_stance_labels"], 0)
        self.assertEqual(packet["gold_stance_labels"], 0)
        self.assertFalse(packet["model_predictions_included"])
        self.assertGreater(len(packet["items"]), 0)
        self.assertEqual(len(set(x["item_id"] for x in packet["items"])),
                         len(packet["items"]))
        self.assertEqual(set(x["proposition_id"] for x in packet["items"]),
                         set(PILOT.PLAN_PROP_IDS))
        self.assertTrue(all("stance_label" not in x for x in packet["items"]))
        self.assertTrue(any(x["selection_route"] == "unfiltered_control"
                            for x in packet["items"]))
        self.assertTrue(any(x["selection_route"] == "lexical_screen"
                            for x in packet["items"]))
        self.assertTrue(all("context_before" in x and "context_after" in x
                            for x in packet["items"]))
        self.assertEqual(
            packet["packet_sha256"],
            PILOT.digest(PILOT.stable(
                {k: v for k, v in packet.items() if k != "packet_sha256"})))

    def test_frozen_test_review_requires_authorization(self) -> None:
        p = self.plan()
        with self.assertRaisesRegex(ValueError, "authorize-test-review"):
            self.packet(p, split="test")
        t = self.packet(p, split="test", authorized=True)
        self.assertEqual(t["source_split"], "test")
        self.assertFalse(t["publication_eligible"])

    def test_owner_review_attestation_not_independent_gold(self) -> None:
        p = self.plan()
        packet = self.packet(p)
        item = packet["items"][0]
        draft = {
            "schema": PILOT.review.DRAFT,
            "packet_sha256": packet["packet_sha256"],
            "reviewer_id": "synthetic-reviewer",
            "human_confirmation": False,
            "finalized": False, "human_gold": False,
            "decisions": [{
                "item_id": item["item_id"],
                "issue_label": "relevant",
                "stance_label": "support",
                "rationale": "Invented test person explicitly claims support.",
                "reviewed_at": "2026-10-09T15:00:00Z",
            }]
        }
        with self.assertRaisesRegex(ValueError, "attestation"):
            PILOT.inspect_draft(packet, draft)
        draft["human_confirmation"] = True
        audit = PILOT.inspect_draft(packet, draft)
        self.assertTrue(audit["owner_review_attested"])
        self.assertFalse(audit["independent_gold"])
        self.assertFalse(audit["model_training_eligible"])
        self.assertEqual(audit["reviewed_items"], 1)
        self.assertEqual(audit["counts"]["stance_support"], 1)

    def test_no_genuine_owner_stance_labels_is_reported_as_zero(self) -> None:
        plan = self.plan()
        location = self.root / "plan_for_packet.json"
        location.write_text(json.dumps(plan), encoding="utf-8")
        result = PILOT.reviewed_label_status(self.ws, location, self.codebook)
        self.assertEqual(result["reviewed_stance_labels"], 0)
        self.assertEqual(result["reviewed_issue_labels"], 0)
        self.assertFalse(result["human_review_attested"])
        self.assertFalse(result["model_training_eligible"])

    def attested_synthetic_review(self) -> tuple[dict, Path]:
        plan = self.plan()
        location = self.root / "plan_for_packet.json"
        location.write_text(json.dumps(plan), encoding="utf-8")
        packet = self.packet(plan)
        item = packet["items"][0]
        expected = [{"source_id": r["source_id"], "split": r["split"]}
                    for r in plan["assignment"] if r["split"] in PILOT.SPLITS]
        write_rows(self.ws / "splits.csv",
                   PILOT.REVIEW_TABLE_HEADERS["splits"], expected)
        (self.ws / "bundle.json").write_text(json.dumps({
            "schema": "un.review.v1",
            "dataset_kind": "real",
            "review_mode": "single_reviewer_pilot",
            "validation_scheme": "time_and_country",
            "human_review_complete": True,
            "cutoff": "2026-10-09T22:00:00Z"
        }), encoding="utf-8")
        when = "2026-10-09T20:00:00Z"
        final = "2026-10-09T21:00:00Z"
        rows = []
        resolved = []
        for task, label in [("issue", "relevant"), ("stance", "support")]:
            rows.append({
                "annotation_id": "synthetic-" + task,
                "passage_id": item["passage_id"], "task": task,
                "proposition_id": item["proposition_id"],
                "label": label,
                "reviewer_id": "synthetic-owner-fixture",
                "reviewed_at": when,
                "rationale": "Invented owner decision solely for the synthetic test.",
            })
            resolved.append({
                "passage_id": item["passage_id"], "task": task,
                "proposition_id": item["proposition_id"],
                "final_label": label,
                "adjudicator_id": "synthetic-owner-fixture",
                "adjudicated_at": final,
                "rationale": "Invented self-finalization solely for CI.",
            })
        write_rows(self.ws / "annotations.csv",
                   PILOT.REVIEW_TABLE_HEADERS["annotations"], rows)
        write_rows(self.ws / "adjudications.csv",
                   PILOT.REVIEW_TABLE_HEADERS["adjudications"], resolved)
        return plan, location

    def test_synthetic_owner_finalized_status_not_independent_gold(self) -> None:
        _, location = self.attested_synthetic_review()
        audited = PILOT.reviewed_label_status(self.ws, location, self.codebook)
        self.assertTrue(audited["human_review_attested"])
        self.assertFalse(audited["independent_gold"])
        self.assertFalse(audited["model_training_eligible"])
        self.assertEqual(audited["stance_by_split"]["train"], 1)
        self.assertEqual(audited["reviewed_stance_labels"], 1)
        self.assertEqual(audited["reviewed_issue_labels"], 1)

    def test_mismatched_source_split_in_owner_review_is_withheld(self) -> None:
        _, location = self.attested_synthetic_review()
        rows = list(csv.DictReader((self.ws / "splits.csv").open(
            encoding="utf-8", newline="")))
        rows[0]["split"] = ("test" if rows[0]["split"] != "test" else "train")
        write_rows(self.ws / "splits.csv",
                   PILOT.REVIEW_TABLE_HEADERS["splits"], rows)
        with self.assertRaisesRegex(ValueError, "does not match frozen source plan"):
            PILOT.reviewed_label_status(self.ws, location, self.codebook)

    def test_too_few_groups_fail_without_allocations(self) -> None:
        self.source_rows = [s for s in self.source_rows if s["iso3"] in {"AAZ", "ABZ"}]
        ids = {s["source_id"] for s in self.source_rows}
        self.quality_rows = [q for q in self.quality_rows if q["source_id"] in ids]
        self.passage_rows = [p for p in self.passage_rows if p["source_id"] in ids]
        self.flush()
        with self.assertRaisesRegex(ValueError, "six distinct"):
            self.plan()


if __name__ == "__main__":
    unittest.main(verbosity=2)
