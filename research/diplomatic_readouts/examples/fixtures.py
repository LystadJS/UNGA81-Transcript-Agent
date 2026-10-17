"""Synthetic fixture factory; no diplomatic source, external service, or private text."""
from dataclasses import replace
from hashlib import sha256
import json

from readout import SCHEMA, ReviewDecision, SourceReceipt, report_digest

TEXT = "café 🌐 fictional synthetic passage, with twenty-seven extra characters."
ORIGINAL = json.dumps({"records": [{"text": TEXT}]}, ensure_ascii=False, sort_keys=True).encode("utf-8")


def sha(value: bytes) -> str:
    return sha256(value).hexdigest()


def fixture(category="exploratory"):
    proof = SourceReceipt(
        source_id="synthetic:A", original_bytes=ORIGINAL, text=TEXT,
        representation_id="synthetic_unicode_v1", parent_id="synthetic:parent",
        accepted=True, public=True, source_url="https://documents.un.org/synthetic",
        json_pointer="/records/0/text", meeting_id="synthetic:meeting",
        speech_id=None, source_family_id="synthetic:family",
    )
    source = {
        "id": proof.source_id, "raw_sha256": sha(proof.original_bytes),
        "text_sha256": sha(proof.text.encode("utf-8")), "hash_basis": "original_bytes",
        "representation_id": proof.representation_id, "parent_id": proof.parent_id,
        "text_length": len(proof.text), "source_url": proof.source_url,
        "meeting_id": proof.meeting_id, "speech_id": proof.speech_id,
        "source_family_id": proof.source_family_id, "json_pointer": proof.json_pointer,
    }
    pointer = {
        "source_id": source["id"], "text_sha256": source["text_sha256"],
        "representation_id": source["representation_id"], "start": 0,
        "end": 6, "json_pointer": source["json_pointer"],
    }
    report = {
        "schema": SCHEMA, "title": "SYNTHETIC evidence example",
        "template": "emerging_themes",
        "coverage": {
            "population": "Two synthetic entries, one eligible", "period": "Fictional period A",
            "unit": "synthetic_passage", "weighting": "equal_source",
            "source_group_unit": "synthetic_meeting", "total_in_frame": 2,
            "eligible": 1, "excluded": 1, "missing": 0,
            "exclusion_reasons": [{"code": "synthetic_duplicate", "count": 1}],
            "missing_reasons": [], "planned_fits": 1, "attempted_fits": 1,
            "converged_fits": 1, "failed_fits": 0, "skipped_fits": 0,
            "unassigned": 0,
        },
        "sources": [source],
        "findings": [{
            "id": "fictional:f1", "category": category,
            "label": "FICTIONAL lexical repetition",
            "observation": "A synthetic source contains repeated text" if category == "descriptive" else None,
            "pattern": "Synthetic exploratory grouping; no diplomatic inference" if category == "exploratory" else None,
            "reviewer_interpretation": "Fictional reviewer qualification, not an empirical result",
            "supporting": [pointer], "contrary": [], "contrary_search": "not_assessed",
            "uncertainty": "Uncertainty uncalibrated", "sensitivity": "Alternate segmentation not fitted",
            "alternative_explanations": "Repeated source structure may dominate",
            "country_attribution": None, "stance": None,
        }],
        "uncertainty": "Synthetic-only; no external validity", "sensitivity": "No empirical sensitivity estimates",
        "alternative_explanations": "Fictional source-group composition",
        "reviewer_note": "This is generated fictional data, not UN evidence",
    }
    decision = ReviewDecision(
        report_sha256=report_digest(report), source_gate="pass", reviewer_gate="pass",
        privacy_gate="pass", statistical_gate="pass", evaluation_role="synthetic_fixture",
        interpreted_findings=frozenset({"fictional:f1"}),
    )
    return report, {proof.source_id: proof}, decision


def refresh(report, decision):
    return replace(decision, report_sha256=report_digest(report))

