"""Synthetic tests for the explicitly lower-trust 1946–2022 GitHub mirror."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd
import pyreadr
from mirror_inventory import MirrorError, REPO_ROOT, inventory, run


class MirrorFallbackTests(unittest.TestCase):
    def example(self, folder: Path):
        source = folder / "fictional-mirror.rds"
        pyreadr.write_rds(str(source), pd.DataFrame({
            "ccode_iso": ["USA", "USA", "CAN", "NOR", "AUS", "BRA"],
            "year": [2016, 2016, 2017, 2022, 2017, 2023],
            "session": [71, 71, 72, 77, 71, 78],
            "text": ["synthetic phrase A", "synthetic phrase B", "synthetic phrase C",
                     "synthetic phrase D", "wrong year/session", "outside mirror scope"],
        }))
        return source

    def test_rds_derived_inventory_no_absence_or_public_text(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            path = self.example(folder)
            report = run(folder / "private_output", source=path)
            years = {row["year"]: row for row in report["coverage"]["per_year"]}
            self.assertEqual(years[2016]["mirror_rows"], 2)
            self.assertEqual(years[2016]["distinct_iso3"], 1)
            self.assertEqual(years[2016]["duplicate_country_session"], 1)
            self.assertEqual(years[2017]["mirror_rows"], 1)
            self.assertEqual(years[2022]["mirror_rows"], 1)
            self.assertEqual(years[2023]["mirror_rows"], 0)
            self.assertEqual(years[2025]["mirror_rows"], 0)
            self.assertEqual(years[2025]["mirror_scope"],
                             "outside_mirror_release_not_missing_speech")
            self.assertEqual(report["coverage"]["quality"]["session_year_mismatch"], 1)
            self.assertEqual(report["coverage"]["excluded_invalid_code_rows"], 0)
            self.assertTrue((folder / "private_output" / "private" /
                             "mirror_code_exceptions_private.csv").exists())
            self.assertEqual(report["coverage"]["selected_rows"], 4)
            self.assertEqual(report["coverage"]["quality"]["outside_documented_2022_release"], 1)
            public = folder / "private_output" / "public_aggregate"
            receipt = (public / "mirror_receipt.json").read_text()
            self.assertNotIn("synthetic phrase", receipt)
            self.assertNotIn("USA,", (public / "mirror_per_year_aggregate.csv").read_text())
            self.assertFalse(report["independent_un_source_crosswalk_complete"])
            self.assertFalse(report["publication_eligible"])

    def test_invalid_country_codes_have_private_exception_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            file = folder / "unresolved.rds"
            pyreadr.write_rds(str(file), pd.DataFrame({
                "ccode_iso": ["???", "USA"],
                "year": [2018, 2018], "session": [73, 73],
                "text": ["fictional invalid-code intervention", "fictional valid intervention"],
            }))
            report = run(folder / "audited", source=file)
            y = next(x for x in report["coverage"]["per_year"] if x["year"] == 2018)
            self.assertEqual(y["mirror_rows"], 1)
            self.assertEqual(y["invalid_country_code_rows"], 1)
            self.assertEqual(report["coverage"]["excluded_invalid_code_rows"], 1)
            private = folder / "audited" / "private" / "mirror_code_exceptions_private.csv"
            self.assertIn("???", private.read_text(encoding="utf-8"))
            public = folder / "audited" / "public_aggregate" / "mirror_receipt.json"
            self.assertNotIn("???", public.read_text(encoding="utf-8"))

    def test_bad_rds_format_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            file = folder / "wrong.rds"
            pyreadr.write_rds(str(file), pd.DataFrame({"random": ["x"]}))
            with self.assertRaisesRegex(MirrorError, "expected"):
                inventory(file, folder / "none")

    def test_no_public_repo_output(self):
        with self.assertRaisesRegex(MirrorError, "under public"):
            run(REPO_ROOT / "research" / "forbidden-fallback")


if __name__ == "__main__":
    unittest.main(verbosity=2)
