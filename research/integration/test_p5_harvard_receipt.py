"""Aggregate-only checks of privately replayed P5 Harvard-v14 verification.

These tests never mount or download private Harvard speeches, UN-PV original
PDFs, country/person rows or fitted models. A passing test proves the public
receipt is internally coherent; it does NOT independently rehash raw inputs.
"""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
PATH=ROOT/"docs/parallel-work/P5_ORIGINAL_HARVARD_REPLAY_AGGREGATE_2026-10-08.json"
P2=ROOT/"docs/parallel-work/W4_P2_REPLAYED_ORIGINAL_BYTES_AGGREGATE_2026-10-08.json"
EXPANDED=ROOT/"docs/parallel-work/P2_W1_EXPANDED_ORIGINAL_SOURCE_2026-10-08.json"
SHA="55077dccf7242cdf544aa95c4797c68e443b0c37344c9c112a2e2392ddfcf8e5"
SELECTION="3ebec834635e4d493e8035aeede3321efb951aa22f2f61d81f6ac7a0f65a4c89"

def require(ok, message):
    if not ok:
        raise ValueError(message)

def validate(d):
    require(d["schema"]=="un.w4.p5.full_original_harvard.v14_source_validation.public_aggregate.v1",
            "Receipt schema unrecognized")
    a=d["harvard_archive"]
    require(a["exact_harvard_v14_archive_sha256"]==SHA and
            a["exact_harvard_v14_archive_md5"]=="81bdd06086d9e7c4e67026acb7325df3" and
            a["original_archive_bytes"]==71280312,
            "Original Harvard v14 archive identity changed")
    require(list(map(int,a["country_speech_files_by_year_2016_2025"].keys()))==
            list(range(2016,2026)) and
            sum(a["country_speech_files_by_year_2016_2025"].values())==
            a["country_speech_files_2016_2025"]==1926,
            "Archive authentic-year membership counts irreconcilable")
    s=d["P2_full_speech_comparison"]
    require(s["original_PV_pdf_sha256_rechecked"]==
            s["original_PV_full_text_sha256_rechecked"]==63,
            "Original PDF/text source hash count changed")
    st=s["recomputed_source_status_counts"]
    require(sum(st.values())==s["independently_recomputed_original_Harvard_to_PV_pairs"]==985,
            "Original Harvey/PV replay source denominators altered")
    require(st["strong_full_speech_content_correspondence"]==
            s["recomputed_strong_count"]==840 and
            sum(s["recomputed_strong_by_year"].values())==840 and
            st["partial_or_variant_transcription"]==94 and
            st["insufficient_full_speech_text_overlap"]==50 and
            st["no_corpus_text_for_comparison"]==
            s["source_verification_ledger_missing_Harvard_speeches"]==1,
            "Whole-speech 7-gram/source modality classification changed")
    require(not any([s["original_Harvard_raw_country_speech_SHA256_discrepancies"],
            s["full_speech_7gram_coverage_and_decile_discrepancies"],
            s["full_speech_status_discrepancies"]]),"Raw source replay discrepancies in accepted receipt")
    ctl=d["wrong_meeting_negative_controls"]
    require(ctl["wrong_original_same_year_controls"]==
            ctl["prior_correct_score_and_wrong_score_exact_replays"]==96 and
            ctl["correspondence_score_replay_discrepancies"]==
            ctl["wrong_original_strong_false_matches"]==0 and
            0<=ctl["maximum_wrong_original_overlap"]<.90,
            "Wrong-meeting controls or specificity gate changed")
    c=d["restricted_W1_historical_source_preframe"]
    require(c["complete_country_year_slots_retained"]==792 and
            c["source_corroborated_cells"]==523 and
            c["unverified_cells_not_imputed_zero"]==269 and
            c["verified_original_PV_meeting_source_groups"]==55 and
            c["index_date_authority"]==520 and
            c["original_PV_frontpage_meeting_date_authority"]==3 and
            c["original_Harvard_523_member_SHA256_checked"]==
            c["original_Harvard_PV_full_speech_7gram_match_recomputed"]==523 and
            c["source_only_inventories"]["private_original_523_member_PV_proof_rows"]==523,
            "Full original 99x8 observed/missing/date source evidence changed")
    require(d["P2_selection_sha256_recomputed"]==SELECTION,
            "Original P2 source selection digest changed")
    e=d["expanded_W1_repository_scope"]
    require(e["original_PVs_reported_on_current_main"]==105 and
            e["source_corroborated_cells_reported_on_current_main"]==790 and
            e["additional_50_original_PV_PDFs_private_bytes_available_in_this_run"] is False and
            e["expanded_105_source_adapter_independently_replayed_this_run"] is False,
            "Unverified expanded 105-PV model falsely promoted")
    require(d["heldout_37_reserved_meetings_opened"]==0 and
            d["publication_eligible"] is False and
            d["national_alignment_or_causal_inference_authorized"] is False and
            d["privacy"]["private_rows_committed_to_GitHub"] is False,
            "Frozen source/publication/privacy gates changed")
    require(d["deterministic_replay"]["two_full_985_pair_replays_match"] is True and
            d["deterministic_replay"]["six_private_provenance_files_byte_identical"] is True,
            "Independent second source replay not declared")
    return True


class P5PublicReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=json.loads(PATH.read_text(encoding="utf8"))
    def test_replayed_original_source_aggregate(self):
        self.assertTrue(validate(self.receipt))
    def test_existing_p2_and_expanded_105_are_distinct(self):
        p2=json.loads(P2.read_text(encoding="utf8"))
        expanded=json.loads(EXPANDED.read_text(encoding="utf8"))
        self.assertEqual(p2["official_originals"]["meetings"],63)
        self.assertEqual(expanded["original_sources"]["original_UN_PV_meetings_total"],105)
        self.assertEqual(expanded["restricted_99_country_panel"]["expanded_strong_source_verification"],790)
        self.assertFalse(self.receipt["expanded_W1_repository_scope"][
            "expanded_105_source_adapter_independently_replayed_this_run"])
    def test_source_count_mutation_refused(self):
        d=deepcopy(self.receipt)
        d["P2_full_speech_comparison"]["recomputed_strong_count"]=839
        with self.assertRaisesRegex(ValueError,"classification"):
            validate(d)
    def test_missing_source_cell_mutation_refused(self):
        d=deepcopy(self.receipt)
        d["restricted_W1_historical_source_preframe"]["unverified_cells_not_imputed_zero"]=0
        with self.assertRaisesRegex(ValueError,"source evidence"):
            validate(d)
    def test_harvard_archive_digest_mutation_refused(self):
        d=deepcopy(self.receipt)
        d["harvard_archive"]["exact_harvard_v14_archive_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"identity"):
            validate(d)
    def test_no_false_expanded_source_claim(self):
        d=deepcopy(self.receipt)
        d["expanded_W1_repository_scope"]["expanded_105_source_adapter_independently_replayed_this_run"]=True
        with self.assertRaisesRegex(ValueError,"falsely promoted"):
            validate(d)
    def test_reserved_heldout_lock_mutation_refused(self):
        d=deepcopy(self.receipt)
        d["heldout_37_reserved_meetings_opened"]=1
        with self.assertRaisesRegex(ValueError,"Frozen"):
            validate(d)
    def test_public_receipt_contains_no_private_row_keys(self):
        # Aggregate SHA and published panel counts are safe; actual country and
        # speaker/source row-level identifiers belong only in the private ZIP.
        raw=PATH.read_text(encoding="utf8")
        for forbidden in ('"iso3":','"speech_text":','"meeting_id":','"speaker_name":',
                          '"person_id":','"country":','"transcript_text":'):
            self.assertNotIn(forbidden,raw)

if __name__=="__main__":
    unittest.main()
