"""Synthetic adapter checks; no original voting records are published here."""
import csv
import tempfile
import unittest
from pathlib import Path
from .un_sc_csv import HEADERS, SourceError, adapt, select_batch, validate_headers


def row(code="Y", **extra):
    value = dict.fromkeys(HEADERS, "")
    value.update(undl_id="123", ms_code="AAA", ms_name="SYNTHETIC STATE A", permanent_member="False", ms_vote=code, date="2020-01-01", resolution="S/RES/9000(2020)", meeting="S/PV.9000", total_yes="1", total_no="0", total_abstentions="0", total_non_voting="0", total_ms="1", modality="Vote", undl_link="https://digitallibrary.un.org/record/123")
    value.update(extra)
    return value


class SCAdapterTests(unittest.TestCase):
    def test_categories_and_modality(self):
        for code, vote in (("Y", "yes"), ("N", "no"), ("A", "abstain"), ("X", "unknown")):
            normalized = adapt(row(code))
            self.assertEqual(normalized["vote"], vote)
            self.assertEqual(normalized["eligible"], None if code == "X" else True)
            self.assertNotIn("policy", normalized)
            self.assertNotIn("context", normalized)
        without = adapt(row("Y", modality="Without Vote"))
        self.assertEqual(without["vote"], "unknown")
        self.assertIsNone(without["eligible"])
        self.assertEqual(without["raw_vote_code"], "Y")
        self.assertFalse(without["individual_vote_recorded"])

    def test_identity_and_fail_closed(self):
        self.assertEqual(adapt(row(resolution="S/RES/9000 (2020)"))["resolution_id"], "S/RES/9000(2020)")
        for extra in ({"resolution": "S/2020/123"}, {"modality": "Consensus"}, {"ms_vote": ""}, {"ms_vote": "Z"}, {"undl_link": "https://example.org/123"}, {"date": "2020-02-30"}, {"permanent_member": "maybe"}):
            with self.assertRaises(ValueError):
                adapt(row(**extra))
        with self.assertRaises(SourceError):
            validate_headers(HEADERS[:-1])

    def test_bounded_complete_groups_and_reconciliation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.csv"
            def write(rows):
                with path.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=HEADERS)
                    writer.writeheader()
                    writer.writerows(rows)
            recent = [row("Y", total_yes="1", total_no="1", total_ms="2"), row("N", ms_code="BBB", ms_name="SYNTHETIC STATE B", total_yes="1", total_no="1", total_ms="2")]
            older = row(date="2019-01-01", resolution="S/RES/8999(2019)", undl_id="122", undl_link="https://digitallibrary.un.org/record/122")
            write([older, *recent])
            selected, receipt = select_batch(path, start="2019-01-01", end="2020-12-31", limit=2)
            self.assertEqual(len(selected), 2)
            self.assertEqual(receipt["next_cursor"], 1)
            self.assertFalse(receipt["complete"])
            self.assertEqual(receipt["window_rows"], 3)
            next_rows, next_receipt = select_batch(path, start="2019-01-01", end="2020-12-31", limit=2, cursor=1)
            self.assertEqual(len(next_rows), 1)
            self.assertTrue(next_receipt["complete"])
            with self.assertRaises(SourceError):
                select_batch(path, start="2019-01-01", end="2020-12-31", limit=1)
            for bad in ([recent[0]], [recent[0], recent[0]], [recent[0], {**recent[1], "total_no": "0"}]):
                write(bad)
                with self.assertRaises(SourceError):
                    select_batch(path, start="2019-01-01", end="2020-12-31", limit=2)


if __name__ == "__main__":
    unittest.main()
