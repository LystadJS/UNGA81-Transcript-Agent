"""Synthetic-only replay and adversarial checks for the offline readout surface."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "examples"))
from readout import (  # noqa: E402
    export, normalize, pointer_digest, render, validate,
)

TEXT = "café 🌐 fictional synthetic passage, with twenty-seven extra characters."
from fixtures import fixture, sha, TEXT, ORIGINAL, refresh


class SurfaceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag in ("script", "iframe", "img", "a"):
            self.scripts.append(tag)


class SchemaAndProvenance(unittest.TestCase):
    def test_complete_synthetic_and_three_formats(self):
        report, proofs, decision = fixture()
        self.assertEqual(validate(report, proofs, decision), [])
        for fmt in ("json", "markdown", "html"):
            out = render(report, fmt, proofs=proofs, decision=decision)
            self.assertIn("Synthetic exploratory grouping", out)
            self.assertIn("synthetic_demo", out)
        view = normalize(report, proofs, decision)
        self.assertFalse(view["publication_eligible"])
        self.assertEqual(view["findings"][0]["status"], "exploratory")
        self.assertNotIn('"original_bytes":', json.dumps(view))
        self.assertNotIn(TEXT, json.dumps(view))

    def test_descriptive_without_statistics(self):
        report, proofs, decision = fixture("descriptive")
        decision = replace(decision, statistical_gate="fail")
        view = normalize(report, proofs, decision)
        self.assertEqual(view["release_state"], "descriptive_only")
        self.assertIn("A synthetic source", json.dumps(view))
        self.assertIsNone(view["findings"][0]["reviewer_interpretation"])

    def test_partial_exploratory_withheld(self):
        report, proofs, decision = fixture()
        decision = replace(decision, statistical_gate="fail")
        view = normalize(report, proofs, decision)
        self.assertEqual(view["release_state"], "withheld")
        self.assertNotIn("Synthetic exploratory grouping", json.dumps(view))
        self.assertEqual(view["findings"][0]["status"], "withheld")
        self.assertIn("statistical_gate_not_passed", view["findings"][0]["reason_codes"])

    def test_abstain_without_source_receipt(self):
        report, proofs, decision = fixture()
        view = normalize(report, {}, decision)
        self.assertEqual(view["release_state"], "withheld")
        self.assertNotIn("Synthetic exploratory grouping", json.dumps(view))

    def test_tampered_content_digest(self):
        report, proofs, decision = fixture()
        report["findings"][0]["pattern"] += " UNSUPPORTED"
        view = normalize(report, proofs, decision)
        self.assertEqual(view["release_state"], "withheld")
        self.assertNotIn("UNSUPPORTED", json.dumps(view))

    def test_input_cannot_self_authorize(self):
        report, proofs, decision = fixture()
        report["gates"] = {"source": True, "review": True, "statistical": True}
        view = normalize(report, proofs, refresh(report, decision))
        self.assertEqual(view["release_state"], "withheld")
        self.assertIsNone(view["coverage"])

    def test_no_decision_defaults_to_withheld(self):
        report, proofs, _ = fixture()
        view = normalize(report, proofs, None)
        self.assertIsNone(view["coverage"])
        self.assertEqual(view["release_state"], "withheld")

    def test_original_bytes_hash_mismatch(self):
        report, proofs, decision = fixture()
        report["sources"][0]["raw_sha256"] = "f" * 64
        view = normalize(report, proofs, refresh(report, decision))
        self.assertEqual(view["release_state"], "withheld")
        self.assertIn("source_authentication_failed", view["validation_errors"])

    def test_unicode_codepoint_length_and_utf8_hash(self):
        report, proofs, decision = fixture()
        self.assertNotEqual(len(TEXT), len(TEXT.encode("utf-8")))
        report["sources"][0]["text_length"] = len(TEXT.encode("utf-8"))
        self.assertEqual(normalize(report, proofs, refresh(report, decision))["release_state"], "withheld")
        report["sources"][0]["text_length"] = len(TEXT)
        report["sources"][0]["text_sha256"] = sha(b"wrong")
        self.assertEqual(normalize(report, proofs, refresh(report, decision))["release_state"], "withheld")

    def test_offset_beyond_actual_text(self):
        report, proofs, decision = fixture()
        report["findings"][0]["supporting"][0]["end"] = len(TEXT) + 1
        view = normalize(report, proofs, refresh(report, decision))
        self.assertEqual(view["release_state"], "withheld")
        self.assertIn("evidence_pointer_unverified", view["validation_errors"])

    def test_invalid_span_zero_and_bool(self):
        report, proofs, decision = fixture()
        report["findings"][0]["supporting"][0]["end"] = 0
        self.assertIn("schema_pointer_invalid", validate(report, proofs, refresh(report, decision)))
        report["findings"][0]["supporting"][0]["end"] = True
        self.assertIn("schema_pointer_invalid", validate(report, proofs, refresh(report, decision)))

    def test_json_pointer_must_resolve_to_text(self):
        report, proofs, decision = fixture()
        report["sources"][0]["json_pointer"] = "/records/99/text"
        report["findings"][0]["supporting"][0]["json_pointer"] = "/records/99/text"
        proofs["synthetic:A"] = replace(proofs["synthetic:A"], json_pointer="/records/99/text")
        self.assertEqual(normalize(report, proofs, refresh(report, decision))["release_state"], "withheld")

    def test_original_and_offset_text_cannot_be_decoupled(self):
        report, proofs, decision = fixture()
        replacement = replace(proofs["synthetic:A"], text="Completely fabricated text, independent of the original")
        proofs["synthetic:A"] = replacement
        report["sources"][0]["text_length"] = len(replacement.text)
        report["sources"][0]["text_sha256"] = sha(replacement.text.encode("utf-8"))
        report["findings"][0]["supporting"][0]["text_sha256"] = sha(replacement.text.encode("utf-8"))
        self.assertEqual(normalize(report, proofs, refresh(report, decision))["release_state"], "withheld")

    def test_representation_mismatch(self):
        report, proofs, decision = fixture()
        report["findings"][0]["supporting"][0]["representation_id"] = "different_basis"
        self.assertEqual(normalize(report, proofs, refresh(report, decision))["release_state"], "withheld")

    def test_parent_lineage_mismatch(self):
        report, proofs, decision = fixture()
        report["sources"][0]["parent_id"] = "different_parent"
        self.assertEqual(normalize(report, proofs, refresh(report, decision))["release_state"], "withheld")

    def test_source_family_mismatch(self):
        report, proofs, decision = fixture()
        report["sources"][0]["source_family_id"] = "different_family"
        self.assertEqual(normalize(report, proofs, refresh(report, decision))["release_state"], "withheld")

    def test_unaccepted_source(self):
        report, proofs, decision = fixture()
        proofs["synthetic:A"] = replace(proofs["synthetic:A"], accepted=False)
        self.assertEqual(normalize(report, proofs, decision)["release_state"], "withheld")

    def test_nonpublic_source(self):
        report, proofs, decision = fixture()
        proofs["synthetic:A"] = replace(proofs["synthetic:A"], public=False)
        self.assertEqual(normalize(report, proofs, decision)["release_state"], "withheld")

    def test_missing_evidence(self):
        report, proofs, decision = fixture()
        report["findings"][0]["supporting"] = []
        self.assertEqual(normalize(report, proofs, refresh(report, decision))["release_state"], "withheld")

    def test_contrary_search_is_not_absence(self):
        report, proofs, decision = fixture()
        view = normalize(report, proofs, decision)
        self.assertEqual(view["findings"][0]["contrary_search"], "not_assessed")
        self.assertIn("Contrary-passage search: not assessed", render(report, "markdown", proofs=proofs, decision=decision))

    def test_wrong_contrary_accounting(self):
        report, proofs, decision = fixture()
        report["findings"][0]["contrary_search"] = "identified"
        self.assertIn("schema_contrary_accounting_mismatch", validate(report, proofs, refresh(report, decision)))

    def test_duplicate_source_ids(self):
        report, proofs, decision = fixture()
        report["sources"].append(deepcopy(report["sources"][0]))
        self.assertIn("schema_source_duplicate_id_or_malformed", validate(report, proofs, refresh(report, decision)))

    def test_duplicate_finding_ids(self):
        report, proofs, decision = fixture()
        report["findings"].append(deepcopy(report["findings"][0]))
        self.assertIn("schema_finding_duplicate_id_or_malformed", validate(report, proofs, refresh(report, decision)))

    def test_population_denominator_mismatch(self):
        report, proofs, decision = fixture()
        report["coverage"]["missing"] = 1
        self.assertIn("schema_population_accounting_mismatch", validate(report, proofs, refresh(report, decision)))
        self.assertIn("schema_reason_accounting_mismatch", validate(report, proofs, refresh(report, decision)))

    def test_fit_accounting(self):
        report, proofs, decision = fixture()
        report["coverage"]["failed_fits"] = 1
        self.assertIn("schema_fit_attempt_mismatch", validate(report, proofs, refresh(report, decision)))

    def test_unknown_private_key_injection(self):
        report, proofs, decision = fixture()
        report["sources"][0]["PRIVATE_EXCERPT"] = "ABSOLUTELY_PRIVATE_PASSAGE"
        view = normalize(report, proofs, refresh(report, decision))
        self.assertEqual(view["release_state"], "withheld")
        self.assertNotIn("ABSOLUTELY_PRIVATE_PASSAGE", json.dumps(view))

    def test_nested_reference_secret_injection(self):
        report, proofs, decision = fixture()
        report["findings"][0]["supporting"][0]["secret"] = "ABSOLUTELY_PRIVATE_PASSAGE"
        self.assertNotIn("ABSOLUTELY_PRIVATE_PASSAGE", render(report, "json", proofs=proofs, decision=refresh(report, decision)))

    def test_exact_source_excerpt_blocked(self):
        report, proofs, decision = fixture()
        report["reviewer_note"] = TEXT[:40]
        view = normalize(report, proofs, refresh(report, decision))
        self.assertEqual(view["release_state"], "withheld")
        self.assertNotIn(TEXT[:40], json.dumps(view))

    def test_html_injection_escaped(self):
        report, proofs, decision = fixture()
        report["findings"][0]["label"] = '<script>alert("x")</script>'
        doc = render(report, "html", proofs=proofs, decision=refresh(report, decision))
        parser = SurfaceParser(); parser.feed(doc)
        self.assertEqual(parser.scripts, [])
        self.assertIn("&amp;lt;script&amp;gt;", doc)
        self.assertIn("Content-Security-Policy", doc)

    def test_malformed_unicode_in_urls_and_json_pointers_is_withheld(self):
        report, proofs, decision = fixture()
        report["sources"][0]["source_url"] = "https://example.invalid/\ud800"
        self.assertIn("schema_source_identity_invalid", validate(report, proofs, decision))
        self.assertEqual(normalize(report, proofs, decision)["release_state"], "withheld")
        report, proofs, decision = fixture()
        report["sources"][0]["json_pointer"] = "/records/\ud800"
        self.assertIn("schema_source_identity_invalid", validate(report, proofs, decision))
        self.assertEqual(normalize(report, proofs, decision)["release_state"], "withheld")

    def test_bad_url_rejected(self):
        report, proofs, decision = fixture()
        report["sources"][0]["source_url"] = "javascript:alert(1)"
        self.assertIn("schema_source_identity_invalid", validate(report, proofs, refresh(report, decision)))

    def test_country_unverified(self):
        report, proofs, decision = fixture()
        ref = report["findings"][0]["supporting"][0]
        report["findings"][0]["country_attribution"] = {
            "iso3": "ZZZ", "mode": "individual", "supporting_pointer_sha256": pointer_digest(ref),
        }
        self.assertEqual(normalize(report, proofs, refresh(report, decision))["release_state"], "withheld")

    def test_country_collective_not_individual(self):
        report, proofs, decision = fixture()
        ref = report["findings"][0]["supporting"][0]
        report["findings"][0]["country_attribution"] = {
            "iso3": "ZZZ", "mode": "individual", "supporting_pointer_sha256": pointer_digest(ref),
        }
        decision = replace(refresh(report, decision), attributed_countries={
            "fictional:f1": ("ZZZ", "individual", pointer_digest(ref))})
        proofs["synthetic:A"] = replace(proofs["synthetic:A"], collective=True)
        self.assertEqual(normalize(report, proofs, decision)["release_state"], "withheld")

    def test_stance_requires_proposition_adjudication(self):
        report, proofs, decision = fixture()
        ref = report["findings"][0]["supporting"][0]
        report["findings"][0]["stance"] = {
            "proposition_id": "synthetic:proposal1", "proposition": "Fictional narrow proposal",
            "position": "support", "evidence_pointer_sha256": pointer_digest(ref),
        }
        self.assertEqual(normalize(report, proofs, refresh(report, decision))["release_state"], "withheld")

    def test_stance_proposition_text_change_invalidates_receipt(self):
        report, proofs, decision = fixture()
        ref = report["findings"][0]["supporting"][0]
        s = {"proposition_id": "synthetic:proposal1", "proposition": "Narrow fictional proposal",
             "position": "support", "evidence_pointer_sha256": pointer_digest(ref)}
        report["findings"][0]["stance"] = s
        decision = replace(refresh(report, decision), adjudicated_stances={"fictional:f1": (
            s["proposition_id"], sha(s["proposition"].encode()), s["position"], pointer_digest(ref))})
        self.assertEqual(normalize(report, proofs, decision)["release_state"], "synthetic_demo")
        s["proposition"] = "Different policy object"
        self.assertEqual(normalize(report, proofs, refresh(report, decision))["release_state"], "withheld")

    def test_no_reviewer_interpretation_without_explicit_release(self):
        report, proofs, decision = fixture()
        decision = replace(decision, interpreted_findings=frozenset())
        view = normalize(report, proofs, decision)
        self.assertEqual(view["release_state"], "synthetic_demo")
        self.assertIsNone(view["findings"][0]["reviewer_interpretation"])

    def test_no_embedded_passage_or_credential_fields(self):
        report, proofs, decision = fixture()
        for key in ("passage", "raw_source", "token"):
            modified = deepcopy(report)
            modified["findings"][0][key] = "PERSONAL_ACCESS_SECRET"
            out = render(modified, "json", proofs=proofs, decision=refresh(modified, decision))
            self.assertNotIn("PERSONAL_ACCESS_SECRET", out)
            self.assertEqual(json.loads(out)["release_state"], "withheld")

    def test_export_is_deterministic_and_non_overwriting(self):
        report, proofs, decision = fixture()
        with tempfile.TemporaryDirectory() as temp:
            d1 = Path(temp) / "one"
            d2 = Path(temp) / "two"
            a = export(report, d1, proofs=proofs, decision=decision)
            b = export(report, d2, proofs=proofs, decision=decision)
            self.assertEqual(a, b)
            for suffix in ("json", "md", "html"):
                self.assertEqual((d1 / ("readout." + suffix)).read_bytes(),
                                 (d2 / ("readout." + suffix)).read_bytes())
            with self.assertRaises(FileExistsError):
                export(report, d1, proofs=proofs, decision=decision)

    def test_malformed_nested_types_fail_closed(self):
        report, proofs, decision = fixture()
        for section, key in (("sources", "id"), ("findings", "id"),
                             ("sources", "text_length"), ("findings", "category")):
            for bad in ([], {}, None, False, 123):
                mutated = deepcopy(report)
                mutated[section][0][key] = bad
                view = normalize(mutated, proofs, refresh(mutated, decision))
                self.assertEqual(view["release_state"], "withheld")

    def test_surrogate_unicode_rejected_not_serialized(self):
        report, proofs, decision = fixture()
        report["title"] = "Bad\ud800unicode"
        self.assertIn("schema_required_prose_missing_or_invalid", validate(report, proofs, decision))

    def test_failed_source_suppresses_all_authored_report_level_claims(self):
        report, proofs, decision = fixture()
        report["reviewer_note"] = "UNSUPPORTED CLAIM OF DIPLOMATIC REALIGNMENT"
        proofs["synthetic:A"] = replace(proofs["synthetic:A"], accepted=False)
        view = normalize(report, proofs, refresh(report, decision))
        self.assertEqual(view["release_state"], "withheld")
        self.assertEqual(view["reviewer_note"], "Withheld")
        self.assertEqual(view["sources"], [])
        self.assertEqual(view["findings"], [])
        self.assertNotIn("UNSUPPORTED", json.dumps(view))

    def test_missing_support_suppresses_unqualified_reviewer_note(self):
        report, proofs, decision = fixture()
        report["findings"][0]["supporting"] = []
        report["reviewer_note"] = "UNSUPPORTED DISCOURSE COMMUNITY ASSERTION"
        view = normalize(report, proofs, refresh(report, decision))
        self.assertEqual(view["release_state"], "withheld")
        self.assertEqual(view["reviewer_note"], "Withheld")
        self.assertNotIn("UNSUPPORTED", render(report, "json", proofs=proofs, decision=refresh(report, decision)))

    def test_fail_closed_malformed_top_level(self):
        self.assertEqual(normalize({"credentials": "DO_NOT_LEAK"})["release_state"], "withheld")
        self.assertNotIn("DO_NOT_LEAK", render({"credentials": "DO_NOT_LEAK"}, "json"))

    def test_published_json_schema_matches_authoring_contract(self):
        from readout import ROOT_FIELDS, COVERAGE_FIELDS, FINDING_FIELDS, SOURCE_FIELDS
        schema = json.loads((HERE / "schema.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), ROOT_FIELDS)
        self.assertEqual(set(schema["properties"]["coverage"]["required"]), COVERAGE_FIELDS)
        self.assertEqual(set(schema["properties"]["sources"]["items"]["required"]), SOURCE_FIELDS)
        self.assertEqual(set(schema["properties"]["findings"]["items"]["required"]), FINDING_FIELDS)
        self.assertFalse(schema["additionalProperties"])
        try:
            import jsonschema
        except ImportError:
            return  # JSON Schema validator is optional; runtime validation is stdlib-only.
        report, _, _ = fixture()
        jsonschema.Draft202012Validator(schema).validate(report)
        report["unexpected_private_copy"] = "secret"
        self.assertTrue(list(jsonschema.Draft202012Validator(schema).iter_errors(report)))

    def test_all_five_template_identifiers(self):
        from readout import TEMPLATES
        for template in TEMPLATES:
            report, proofs, decision = fixture()
            report["template"] = template
            view = normalize(report, proofs, refresh(report, decision))
            self.assertEqual(view["release_state"], "synthetic_demo")
            self.assertIn("question", view["template_guidance"])
            self.assertIn("Template-specific qualification", render(
                report, "markdown", proofs=proofs, decision=refresh(report, decision)))

    def test_human_reports_preserve_authenticated_original_source_urls(self):
        report, proofs, decision = fixture()
        output = render(report, "markdown", proofs=proofs, decision=decision)
        self.assertIn("https://documents.un.org/synthetic", output)
        self.assertIn("text SHA-256", output)


if __name__ == "__main__":
    unittest.main()
