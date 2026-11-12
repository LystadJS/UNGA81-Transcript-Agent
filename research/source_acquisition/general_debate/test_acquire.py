"""Offline fictional source-acquisition contract regressions. No remote requests."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

from acquire import (
    AcquisitionError, REPO_ROOT, build_crosswalk, corpus_inventory,
    download, official_inventory, resolve_iso3, run
)

HERE = Path(__file__).resolve().parent
HEADER = ["Name", "Salutation", "Member State", "GA Session", "Meeting Date",
          "Meeting Symbol", "Agenda Items", "UNDL ID", "UNDL Link"]


def corpus(path: Path, entries: list[tuple[str, bytes]]) -> None:
    with tarfile.open(path, "w:gz") as tar:
        for name, body in entries:
            info = tarfile.TarInfo(name=name)
            info.size = len(body)
            tar.addfile(info, io.BytesIO(body))


def authority(path: Path, records: list[dict]) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, HEADER)
        writer.writeheader()
        writer.writerows(records)


def fixture(directory: Path, duplicate=False) -> tuple[Path, Path]:
    gz = directory / "fictional-history.tar.gz"
    rows = [
        ("member/USA_71_2016.txt", b"fictional-speech-2016"),
        ("member/CAN_72_2017.txt", b"fictional-speech-2017"),
    ]
    if duplicate:
        rows.append(("different/USA_71_2016.txt", b"fictional-revised"))
    corpus(gz, rows)
    idx = directory / "fictional-UN-index.csv"
    authority(idx, [
        {"Name": "Fictional Ambassador X", "Member State": "United States of America",
         "GA Session": "71", "Meeting Date": "2016-09-20",
         "Meeting Symbol": "A/71/PV.10", "UNDL ID": "fictional-1"},
        {"Name": "Fictional Ambassador Y", "Member State": "Norway",
         "GA Session": "72", "Meeting Date": "2017-09-20",
         "Meeting Symbol": "A/72/PV.12", "UNDL ID": "fictional-2"}
    ])
    return gz, idx


class GeneralDebateAcquisition(unittest.TestCase):
    def test_explicit_country_mapping_without_fuzzy_matching(self):
        self.assertEqual(resolve_iso3("United States of America")[0], "USA")
        self.assertEqual(resolve_iso3("Norway")[0], "NOR")
        self.assertEqual(resolve_iso3("Bolivia (Plurinational State of)")[0], "BOL")
        self.assertEqual(resolve_iso3("Definitely Fictional Not A Country")[0], None)

    def test_country_session_join_and_unknown_not_absence(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            tar, index = fixture(root)
            out = root / "private_run"
            receipt = run(tar, index, out, [2016, 2017], version_query=False)
            self.assertEqual(receipt["status"], "both_sources_indexed_not_originally_verified")
            per = receipt["crosswalk_aggregate"]["per_year"]
            self.assertEqual(per[0]["key_matches_not_text_verified"], 1)
            self.assertEqual(per[1]["corpus_only_no_official_key"], 1)
            self.assertEqual(per[1]["official_only_no_corpus_text"], 1)
            self.assertEqual(per[0]["candidate_union_countries"], 3)
            private = (out / "private" / "candidate_crosswalk_private.csv").read_text()
            self.assertIn("neither_observed_not_confirmed_absent", private)
            self.assertIn("A/71/PV.10", private)
            public = (out / "public_aggregate" / "acquisition_receipt.json").read_text()
            self.assertNotIn("Fictional Ambassador", public)
            self.assertNotIn("fictional-speech", public)
            self.assertNotIn("USA,", (out / "public_aggregate" / "per_year_aggregate.csv").read_text())
            self.assertFalse(receipt["independent_text_verification_complete"])
            self.assertFalse(receipt["publication_eligible"])
            self.assertFalse(receipt["holdout_access"])

    def test_duplicate_country_session_requires_adjudication(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            tar, idx = fixture(root, duplicate=True)
            speeches, qa = corpus_inventory(tar, {2016, 2017})
            self.assertEqual(qa["duplicate_country_session_keys"], 1)
            official, _ = official_inventory(idx, {2016, 2017})
            result = build_crosswalk(speeches, official, [2016, 2017],
                                     root / "private", root / "aggregate")
            self.assertEqual(result["per_year"][0]["duplicate_or_multiple"], 1)
            self.assertEqual(result["per_year"][0]["key_matches_not_text_verified"], 0)

    def test_official_mapping_does_not_invent_speaker_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _, index = fixture(root)
            rows, qa = official_inventory(index, {2016, 2017})
            self.assertEqual(qa["indexed_official_rows"], 2)
            self.assertTrue(all(x["personal_identity_verified"] is False for x in rows))
            self.assertEqual(rows[0]["meeting_symbol"], "A/71/PV.10")

    def test_year_scope_and_unmatched_tar_filenames(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive = root / "sample.tar.gz"
            corpus(archive, [
                ("text/USA_71_2016.txt", b"2016-fake"),
                ("text/CAN_80_2025.txt", b"2025-fake"),
                ("text/USA_81_2026.txt", b"excluded-not-2026"),
                ("text/USA_71_2020.txt", b"session-mismatch"),
                ("text/unknown-document.pdf", b"not-a-speech"),
            ])
            rows, qa = corpus_inventory(archive, {2016, 2025})
            self.assertEqual(len(rows), 2)
            self.assertEqual(qa["nonmatching_tar_members"], 1)
            self.assertEqual({x["year"] for x in rows}, {2016, 2025})
            script = subprocess.run([sys.executable, str(HERE / "acquire.py"),
                                     "--start-year", "2026", "--out", str(root / "blocked")],
                                    capture_output=True, text=True, timeout=10)
            self.assertNotEqual(script.returncode, 0)
            self.assertFalse((root / "blocked").exists())

    def test_year_2025_does_not_claim_official_index_support(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive = root / "s.tar.gz"
            corpus(archive, [("A/CAN_80_2025.txt", b"fictional-2025")])
            rows, _ = corpus_inventory(archive, {2025})
            report = build_crosswalk(rows, [], [2025], root / "private", root / "aggregate")
            self.assertEqual(report["per_year"][0]["corpus_with_uncovered_index"], 1)
            self.assertEqual(report["per_year"][0]["official_index_scope"],
                             "not_published_in_20260129_index")

    def test_no_repo_output_and_missing_input_not_imputed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive, _ = fixture(root)
            partial = run(archive, None, root / "out", [2016, 2017], version_query=False)
            self.assertEqual(partial["status"], "partial_only_no_independent_reconciliation")
            self.assertIn("undl_official", partial["failures"])
            self.assertFalse(partial["publication_eligible"])
            with self.assertRaises(AcquisitionError):
                run(None, None, REPO_ROOT / "research" / "forbidden", [2016])

    def test_downloads_fail_closed_for_unapproved_urls(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(AcquisitionError, "allowlist"):
                download("https://example.net/unapproved-source", Path(d) / "leak", 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
