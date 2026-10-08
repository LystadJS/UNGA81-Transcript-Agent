"""Public invented fixtures for source-audit gates; no original UN text or names."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from research.integration import p2_source_readiness as S


def fake_tables() -> dict:
    years = list(range(2016, 2025))
    pv = [7, 9, 6, 7, 7, 7, 7, 5, 8]
    all_pdf = []
    n = 0
    for year, number in zip(years, pv):
        for j in range(number):
            symbol = f"A/{year-1945}/PV.{j+1}"
            all_pdf.append({
                "Year": str(year),
                "Official symbol": symbol,
                "Pages": str(3370 // 63 + (n < (3370 % 63))),
                "Raw bytes": str(53218960 // 63 + (n < (53218960 % 63))),
                "Original PDF SHA-256": hashlib.sha256(
                    f"fictional-pv-{n}".encode()).hexdigest(),
                "Original official URL": f"https://documents.un.org/mock-pv-{n}",
            })
            n += 1
    strong = [82, 92, 115, 120, 107, 105, 128, 91, 0]
    missing = [111, 103, 80, 74, 85, 88, 64, 100, 47]
    annual = [
        {"Year": str(year), "Strong full texts": str(strong[i]),
         "Variant partial": str(94 if year == 2024 else 0),
         "Insufficient text": str(50 if year == 2024 else 0),
         "PV not yet reviewed": str(missing[i]), "Original PV documents": str(pv[i])}
        for i, year in enumerate(years)
    ]
    candidates = []
    for i in range(99):
        iso = "X" + chr(65 + i//26) + chr(65 + i%26)
        past = [2016,2017]+([2018] if i < 54 else [])
        future = [2020,2021]+([2022] if i < 73 else [])
        verified = sorted(past + future)
        excluded = sorted(set(range(2016,2024)) - set(verified))
        candidates.append({
            "ISO3": iso, "Prior verified": str(len(past)),
            "Later verified": str(len(future)), "Total verified": str(len(verified)),
            "Verified years": ";".join(map(str,verified)),
            "Unreviewed years": ";".join(map(str,excluded)), "W4 eligible": "False"
        })
    flags = {
        "SOURCE_AUTHORITY_COUNTRY_AND_RECORDED_SPEAKER_CORROBORATED": 14,
        "CONFIRMED_UN_SPEAKER_INDEX_OMISSION_NOT_SPEECH_ABSENCE": 3,
        "CONFIRMED_HARVARD_CORPUS_TEXT_OMISSION_WITH_OFFICIAL_PV_PRESENT": 1,
        "UNRESOLVED_NEEDS_DOCUMENT_OR_MODALITY_REVIEW": 3,
        "GLOBAL_VALIDATION_GATE_STILL_OPEN": 3,
    }
    reviews = [dict(**{"Source adjudication":kind}) for kind,n in flags.items()
               for _ in range(n)]
    tally = {
        "strong_full_speech_content_correspondence":69,
        "no_official_source_download_for_sample_cell":38,
        "insufficient_full_speech_text_overlap":6,
        "no_corpus_text_for_comparison":1,
        "partial_or_variant_transcription":6
    }
    sample = [{"Official full-PV check": name} for name,n in tally.items()
              for _ in range(n)]
    controls = [{"Wrong 7gram overlap": str(.02793 if i == 95 else .001)}
                for i in range(96)]
    return {
        "Original PDF Manifest":all_pdf, "Annual Verification":annual,
        "W4 Candidate 99":candidates, "Stratified 120":sample,
        "Priority 24":reviews, "Wrong PV Controls":controls
    }


class P2SourceReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = S.read_public()

    def test_public_aggregate_gates_are_consistent_but_not_pdfs(self):
        r = S.aggregate_invariants(self.expected)
        self.assertEqual(r["original_pv_documents"],63)
        self.assertEqual(r["strong_speech_original_meeting_correspondences_2016_2023"],840)
        self.assertEqual(r["not_source_verified_candidate_cells"],269)
        self.assertFalse(r["real_pdf_bytes_replayed_in_this_run"])
        self.assertFalse(r["W4_descriptive_fit_eligible"])
        self.assertEqual(r["reserved_37_meetings_opened"],0)

    def test_invented_full_worksheet_passes_with_unverified_cells(self):
        data = fake_tables()
        out = S.audit_tables(data, self.expected)
        self.assertEqual(out["candidate_source_verified"],523)
        self.assertEqual(out["candidate_unreviewed"],269)
        self.assertEqual(out["prior_verified"],252)
        self.assertEqual(out["later_verified"],271)
        self.assertEqual(out["original_pdf_byte_digest_replay"],
                         "NOT_RUN_NO_PRIVATE_PDF_MAP")
        self.assertFalse(out["W1_source_frame_eligible"])
        self.assertFalse(out["publication_eligible"])

    def test_2026_reserved_pv_cannot_be_used_as_historical_source(self):
        t = fake_tables()
        t["Original PDF Manifest"][0]["Year"] = "2026"
        with self.assertRaisesRegex(S.SourceGateError,"symbol/session/year"):
            S.audit_tables(t,self.expected)

    def test_official_pv_duplicate_hash_or_wrong_url_is_rejected(self):
        t = fake_tables()
        t["Original PDF Manifest"][0]["Original PDF SHA-256"] = (
            t["Original PDF Manifest"][1]["Original PDF SHA-256"])
        with self.assertRaisesRegex(S.SourceGateError,"Duplicate source PDF"):
            S.audit_tables(t,self.expected)
        t = fake_tables()
        t["Original PDF Manifest"][0]["Original official URL"] = "https://nonun.example/fiction"
        with self.assertRaisesRegex(S.SourceGateError,"Nonofficial"):
            S.audit_tables(t,self.expected)

    def test_candidate_duplicate_and_modalities_refuse(self):
        t = fake_tables()
        t["W4 Candidate 99"][1]["ISO3"] = t["W4 Candidate 99"][0]["ISO3"]
        with self.assertRaisesRegex(S.SourceGateError,"Duplicate/invalid"):
            S.audit_tables(t,self.expected)
        t = fake_tables()
        t["W4 Candidate 99"][0]["Verified years"] = "2025;2017;2020;2021"
        with self.assertRaisesRegex(S.SourceGateError,"complement"):
            S.audit_tables(t,self.expected)

    def test_unverified_can_never_be_imputed_as_zero(self):
        t = fake_tables()
        t["W4 Candidate 99"][0]["Unreviewed years"] = ""
        with self.assertRaisesRegex(S.SourceGateError,"complement"):
            S.audit_tables(t,self.expected)
        t = fake_tables()
        t["W4 Candidate 99"][0]["W4 eligible"] = "True"
        with self.assertRaisesRegex(S.SourceGateError,"cannot be called model-eligible"):
            S.audit_tables(t,self.expected)

    def test_wrong_original_meeting_is_never_strong(self):
        t = fake_tables()
        t["Wrong PV Controls"][0]["Wrong 7gram overlap"]="0.91"
        with self.assertRaisesRegex(S.SourceGateError,"wrong-document"):
            S.audit_tables(t,self.expected)

    def test_pdf_byte_check_is_strict_and_local(self):
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp)
            pdf=home/"invented-source.pdf"
            pdf.write_bytes(b"%PDF-1.7\ninvented synthetic PDF\n")
            sha=hashlib.sha256(pdf.read_bytes()).hexdigest()
            data={"Original PDF Manifest":[{
                "Official symbol":"A/71/PV.1",
                "Raw bytes":str(pdf.stat().st_size),
                "Original PDF SHA-256":sha
            }]}
            pointer=home/"paths.json"
            pointer.write_text(json.dumps({"A/71/PV.1":str(pdf)}))
            self.assertEqual(S.check_original_pdf_bytes(home,pointer,data),1)
            pdf.write_bytes(pdf.read_bytes()+b"unexpected edit")
            with self.assertRaisesRegex(S.SourceGateError,"digest/length"):
                S.check_original_pdf_bytes(home,pointer,data)

    def test_no_private_input_inside_git_checkout(self):
        with self.assertRaisesRegex(S.SourceGateError,"outside the public repository"):
            S.private_path(S.PUBLIC,file=True)

    def test_aggregate_receipt_contains_no_row_level_keys_or_text(self):
        v=S.aggregate_invariants(self.expected)
        text=json.dumps(v)
        for forbidden in ("Official symbol","source_url","speaker_name","ISO3",
                          "Original official URL","text_sha256"):
            self.assertNotIn(forbidden,text)


if __name__ == "__main__":
    unittest.main()
