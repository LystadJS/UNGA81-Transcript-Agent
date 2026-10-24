import unittest
from .ga_votes import HEADERS,adapt,validate_headers,iter_batches,reconcile_groups
from .adapters import SourceError
class GAVoteTests(unittest.TestCase):
    def row(self,code="Y"):
        row={key:"" for key in HEADERS}
        row.update(undl_id="123456",ms_code="XXX",ms_name="Synthetic Country",ms_vote=code,date="2025-01-01",resolution="A/RES/79/999",meeting="A/79/PV.999",undl_link="https://digitallibrary.un.org/record/123456")
        return row
    def test_actual_header_contract(self):
        validate_headers(HEADERS)
        with self.assertRaises(SourceError):validate_headers(HEADERS[1:])
    def test_non_voting_is_unknown_not_absent(self):
        vote=adapt(self.row("X"));self.assertEqual(vote["vote"],"unknown");self.assertIsNone(vote["eligible"]);self.assertTrue(vote["non_voting_reported"])
        self.assertEqual(adapt(self.row("A"))["vote"],"abstain")
        for code in ("","Z"):
            with self.assertRaises(SourceError):adapt(self.row(code))
    def test_source_identity_and_notes(self):
        row=self.row();row["vote_note"]="Synthetic qualification"
        self.assertTrue(adapt(row)["vote_note_present"])
        row["undl_link"]="https://evil.invalid/123456"
        with self.assertRaises(SourceError):adapt(row)
    def test_canonical_identity_and_exact_subpart_symbols(self):
        row=self.row();row.update(ms_code="USA",ms_name="UNITED STATES")
        mapped=adapt(row)
        self.assertEqual(mapped["country_id"],"United States")
        self.assertEqual(mapped["recorded_country_name"],"UNITED STATES")
        self.assertEqual(mapped["country_mapping_status"],"registry_mapped")
        for symbol in ("A/RES/75/254[C]","A/RES/78/183 A","A/RES/80/293 B"):
            self.assertEqual(adapt({**row,"resolution":symbol})["resolution_id"],symbol)
        decision=adapt({**row,"resolution":"A/DEC/80/506"})
        self.assertEqual(decision["stage"],"adopted_decision")
        self.assertEqual(decision["resolution_id"],"A/DEC/80/506")
    def test_single_pass_bounded_batches(self):
        import csv,tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path=Path(directory)/"synthetic.csv"
            with path.open("w",encoding="utf-8",newline="") as stream:
                writer=csv.DictWriter(stream,fieldnames=HEADERS);writer.writeheader()
                for i in range(5):
                    row=self.row("X" if i==2 else "Y");row["date"]="2024-01-01" if i==0 else "2025-01-01";writer.writerow(row)
            batches=list(iter_batches(path,"2025-01-01","2025-12-31",batch_size=2))
            self.assertEqual([len(b["rows"]) for b in batches],[2,2,0])
            self.assertTrue(batches[-1]["complete"]);self.assertEqual(batches[-1]["source_row_cursor"],5)
            self.assertEqual(batches[-1]["selected_so_far"],4)
    def test_group_reconciliation_noncontiguous_and_blanks(self):
        def row(country,resolution="A/RES/79/999",vote="Y"):
            r=self.row(vote);r.update(ms_code=country,resolution=resolution,total_yes="1.0",total_no="0.0",total_abstentions="0.0",total_non_voting="1.0",total_ms="2.0")
            return r
        rows=[row("AAA"),row("CCC","A/RES/79/998"),row("BBB",vote="X"),row("DDD","A/RES/79/998",vote="X")]
        result=reconcile_groups(rows,"2025-01-01","2025-12-31")
        self.assertEqual(result["groups"],2);self.assertEqual(result["noncontiguous_groups"],2)
        self.assertEqual(result["issues"].get("mismatched_groups",0),0)
        self.assertEqual(result["source_id_identity_conflicts"],1)
        duplicate=reconcile_groups([row("AAA"),row("AAA",vote="X")],"2025-01-01","2025-12-31")
        self.assertEqual(duplicate["issues"]["duplicate_country_rows"],1)
        mismatch=row("AAA");mismatch["total_yes"]="2.0"
        checked=reconcile_groups([mismatch],"2025-01-01","2025-12-31")
        self.assertGreater(checked["mismatch_fields"]["total_yes"],0)
        fractional=row("AAA");fractional["total_yes"]="1.5"
        self.assertEqual(reconcile_groups([fractional],"2025-01-01","2025-12-31")["issues"]["invalid_totals_groups"],1)
        blank=row("AAA");blank["total_ms"]=""
        self.assertEqual(reconcile_groups([blank],"2025-01-01","2025-12-31")["issues"]["blank_totals_groups"],1)
if __name__=="__main__":unittest.main()
