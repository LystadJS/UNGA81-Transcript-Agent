"""Deterministic, offline, evidence-gated diplomatic research readouts.

This is a presentation validator, not a source-authority or D1 publisher.
The caller must supply independently established source receipts and review
approvals.  User-authored report data cannot assert its own gate status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
from typing import Mapping
from urllib.parse import urlsplit

SCHEMA = "un.diplomatic-readout.v1"
TEMPLATES = (
    "emerging_themes", "discourse_communities", "changing_actor_profiles",
    "boundary_cases", "source_backed_anomalies",
)
CATEGORIES = ("descriptive", "exploratory")
TEMPLATE_GUIDANCE = {
    "emerging_themes": {
        "question": "Which language patterns emerge in the declared comparable observation population?",
        "limit": "A newly observed pattern is not proof a policy issue is new; selection, coverage and wording may explain it.",
    },
    "discourse_communities": {
        "question": "Which independently sourced observations use relatively similar language?",
        "limit": "A language community is not a diplomatic coalition, shared policy or coordination.",
    },
    "changing_actor_profiles": {
        "question": "How do source-comparable actor-language profiles differ across reported periods?",
        "limit": "Composition, attribution, translation or representation can mimic movement; do not infer realignment.",
    },
    "boundary_cases": {
        "question": "Which accepted observations have ambiguous or method-sensitive memberships?",
        "limit": "Instability and display proximity cannot establish a diplomatic bridge or agreement.",
    },
    "source_backed_anomalies": {
        "question": "Which source-grounded observations depart from a declared comparison profile?",
        "limit": "An unusual passage does not establish novelty, wrongdoing, causal influence or statistical significance.",
    },
}
GATE_STATES = ("pass", "fail", "not_run")
RESTRICTIONS = (
    "Language similarity is not policy agreement.",
    "Clustering is not coordination.",
    "Temporal movement is not necessarily diplomatic realignment.",
    "Co-assignment stability is not statistical significance or independent replication.",
    "Missing transcription is not evidence of issue absence.",
    "Embedding or display distances are not evidence of influence.",
)
ROOT_FIELDS = frozenset((
    "schema", "title", "template", "coverage", "sources", "findings",
    "uncertainty", "sensitivity", "alternative_explanations", "reviewer_note",
))
COVERAGE_FIELDS = frozenset((
    "population", "period", "unit", "weighting", "source_group_unit",
    "total_in_frame", "eligible", "excluded", "missing", "exclusion_reasons",
    "missing_reasons", "planned_fits", "attempted_fits", "converged_fits",
    "failed_fits", "skipped_fits", "unassigned",
))
SOURCE_FIELDS = frozenset((
    "id", "raw_sha256", "text_sha256", "hash_basis", "representation_id",
    "parent_id", "text_length", "source_url", "meeting_id", "speech_id",
    "source_family_id", "json_pointer",
))
FINDING_FIELDS = frozenset((
    "id", "category", "label", "observation", "pattern", "reviewer_interpretation",
    "supporting", "contrary", "contrary_search", "uncertainty", "sensitivity",
    "alternative_explanations", "country_attribution", "stance",
))
POINTER_FIELDS = frozenset((
    "source_id", "text_sha256", "representation_id", "start", "end", "json_pointer",
))
ATTRIBUTION_FIELDS = frozenset(("iso3", "mode", "supporting_pointer_sha256"))
STANCE_FIELDS = frozenset(("proposition_id", "proposition", "position", "evidence_pointer_sha256"))
HEX64 = re.compile(r"^[a-f0-9]{64}$")
ISO3 = re.compile(r"^[A-Z]{3}$")
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


@dataclass(frozen=True)
class SourceReceipt:
    """Trusted, nonexported authentication evidence for a source text basis.

    ``original_bytes`` are the original representation bytes; ``text`` is the
    versioned Unicode offset basis. They may differ. Neither is exported.
    An upstream source validator, not this renderer, establishes ``accepted``.
    """

    source_id: str
    original_bytes: bytes
    text: str
    representation_id: str
    parent_id: str
    accepted: bool
    public: bool
    source_url: str | None = None
    json_pointer: str | None = None
    collective: bool = False
    meeting_id: str | None = None
    speech_id: str | None = None
    source_family_id: str | None = None


@dataclass(frozen=True)
class ReviewDecision:
    """Trusted review/fit verdict, maintained separately from draft report JSON.

    ``report_sha256`` binds the exact authored content. This is a consistency
    check, not a cryptographic signature or an independent reviewer certificate.
    """

    report_sha256: str
    source_gate: str = "not_run"
    reviewer_gate: str = "not_run"
    privacy_gate: str = "not_run"
    statistical_gate: str = "not_run"
    evaluation_role: str = "engineering_only"  # synthetic_fixture or experimental_review
    attributed_countries: Mapping[str, tuple[str, str, str]] = field(default_factory=dict)
    adjudicated_stances: Mapping[str, tuple[str, str, str, str]] = field(default_factory=dict)
    interpreted_findings: frozenset[str] = frozenset()


def _sha(data: bytes) -> str:
    return sha256(data).hexdigest()


def report_digest(report: object) -> str:
    """SHA-256 of canonical UTF-8 authoring JSON, domain-separated by schema."""
    raw = json.dumps(report, sort_keys=True, ensure_ascii=False,
                     allow_nan=False, separators=(",", ":")).encode("utf-8")
    return _sha(b"un.diplomatic-readout.v1\n" + raw)


def _is_count(value: object) -> bool:
    return type(value) is int and value >= 0


def _valid_text(value: object, limit: int = 1000) -> bool:
    return (isinstance(value, str) and 0 < len(value.strip()) <= limit
            and not any((ord(c) < 32 and c not in "\n\t")
                        or 0xD800 <= ord(c) <= 0xDFFF for c in value))


def _ident(value: object) -> bool:
    return isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None


def _hash(value: object) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def _safe_url(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, str) or len(value) > 512 or any(ord(c) < 33 or 0xD800 <= ord(c) <= 0xDFFF for c in value):
        return False
    try:
        parts = urlsplit(value)
        return (parts.scheme == "https" and bool(parts.hostname)
                and parts.username is None and parts.password is None
                and parts.port in (None, 443))
    except ValueError:
        return False


def _safe_pointer(value: object) -> bool:
    return (value is None or (isinstance(value, str) and len(value) <= 500
                              and (value == "" or value.startswith("/"))
                              and not any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in value)
                              and re.search(r"~(?![01])", value) is None))


def _closed(record: object, allowed: frozenset) -> bool:
    return isinstance(record, dict) and not (record.keys() - allowed)


def _reason_counts(value: object) -> int | None:
    if not isinstance(value, list):
        return None
    seen = set()
    total = 0
    for item in value:
        if (not isinstance(item, dict) or set(item) != {"code", "count"}
                or not _ident(item["code"]) or item["code"] in seen
                or not _is_count(item["count"])):
            return None
        seen.add(item["code"])
        total += item["count"]
    return total


def _structure(report: object) -> list[str]:
    """Closed input-schema validation; errors are safe fixed codes only."""
    if not _closed(report, ROOT_FIELDS):
        return ["schema_root_invalid_or_extra_fields"]
    errors: list[str] = []
    if report.get("schema") != SCHEMA or report.get("template") not in TEMPLATES:
        errors.append("schema_or_template_invalid")
    for key in ("title", "uncertainty", "sensitivity", "alternative_explanations", "reviewer_note"):
        if not _valid_text(report.get(key), 1200):
            errors.append("schema_required_prose_missing_or_invalid")
    cov = report.get("coverage")
    if not _closed(cov, COVERAGE_FIELDS) or set(cov) != COVERAGE_FIELDS:
        errors.append("schema_coverage_incomplete")
    else:
        for key in ("population", "period", "unit", "weighting", "source_group_unit"):
            if not _valid_text(cov.get(key), 350):
                errors.append("schema_coverage_description_invalid")
        keys = ("total_in_frame", "eligible", "excluded", "missing", "planned_fits",
                "attempted_fits", "converged_fits", "failed_fits", "skipped_fits", "unassigned")
        if not all(_is_count(cov.get(key)) for key in keys):
            errors.append("schema_coverage_count_invalid")
        else:
            if cov["total_in_frame"] != cov["eligible"] + cov["excluded"] + cov["missing"]:
                errors.append("schema_population_accounting_mismatch")
            if cov["planned_fits"] != cov["attempted_fits"] + cov["skipped_fits"]:
                errors.append("schema_fit_plan_mismatch")
            if cov["attempted_fits"] != cov["converged_fits"] + cov["failed_fits"]:
                errors.append("schema_fit_attempt_mismatch")
            if cov["unassigned"] > cov["eligible"]:
                errors.append("schema_unassigned_exceeds_eligible")
        if (_reason_counts(cov.get("exclusion_reasons")) != cov.get("excluded")
                or _reason_counts(cov.get("missing_reasons")) != cov.get("missing")):
            errors.append("schema_reason_accounting_mismatch")
    sources = report.get("sources")
    if not isinstance(sources, list):
        errors.append("schema_sources_not_array")
    else:
        ids = []
        for source in sources:
            if not _closed(source, SOURCE_FIELDS) or set(source) != SOURCE_FIELDS:
                errors.append("schema_source_invalid_or_extra_fields")
                continue
            ids.append(source["id"])
            if (not _ident(source["id"]) or not _ident(source["representation_id"])
                    or not _ident(source["parent_id"]) or not _hash(source["raw_sha256"])
                    or not _hash(source["text_sha256"]) or source["hash_basis"] != "original_bytes"
                    or not _is_count(source["text_length"]) or source["text_length"] == 0
                    or not _safe_url(source["source_url"])
                    or not _safe_pointer(source["json_pointer"])):
                errors.append("schema_source_identity_invalid")
            for key in ("meeting_id", "speech_id", "source_family_id"):
                if source[key] is not None and not _ident(source[key]):
                    errors.append("schema_source_linkage_invalid")
        if any(not _ident(x) for x in ids) or len(ids) != len(set(x for x in ids if _ident(x))):
            errors.append("schema_source_duplicate_id_or_malformed")
    findings = report.get("findings")
    if not isinstance(findings, list):
        errors.append("schema_findings_not_array")
    else:
        ids = []
        for f in findings:
            if not _closed(f, FINDING_FIELDS) or set(f) != FINDING_FIELDS:
                errors.append("schema_finding_invalid_or_extra_fields")
                continue
            ids.append(f["id"])
            if not _ident(f["id"]) or f["category"] not in CATEGORIES:
                errors.append("schema_finding_category_invalid")
            if not _valid_text(f["label"], 180):
                errors.append("schema_finding_label_invalid")
            category = f["category"]
            if (category == "descriptive" and (not _valid_text(f["observation"]) or f["pattern"] is not None)
                    or category == "exploratory" and (not _valid_text(f["pattern"]) or f["observation"] is not None)):
                errors.append("schema_finding_text_category_mismatch")
            for key in ("uncertainty", "sensitivity", "alternative_explanations"):
                if not _valid_text(f[key]):
                    errors.append("schema_finding_disclosure_missing")
            if f["reviewer_interpretation"] is not None and not _valid_text(f["reviewer_interpretation"]):
                errors.append("schema_reviewer_interpretation_invalid")
            if f["contrary_search"] not in ("not_assessed", "assessed_none", "identified"):
                errors.append("schema_contrary_search_invalid")
            if not isinstance(f["supporting"], list) or not isinstance(f["contrary"], list):
                errors.append("schema_evidence_not_arrays")
            else:
                if (f["contrary_search"] == "identified") != bool(f["contrary"]):
                    errors.append("schema_contrary_accounting_mismatch")
                for ref in f["supporting"] + f["contrary"]:
                    if not _closed(ref, POINTER_FIELDS) or set(ref) != POINTER_FIELDS:
                        errors.append("schema_pointer_invalid_or_extra_fields")
                        continue
                    if (not _ident(ref["source_id"]) or not _ident(ref["representation_id"])
                            or not _hash(ref["text_sha256"]) or not _is_count(ref["start"])
                            or not _is_count(ref["end"]) or ref["start"] >= ref["end"]
                            or not _safe_pointer(ref["json_pointer"])):
                        errors.append("schema_pointer_invalid")
            if f["country_attribution"] is not None:
                a = f["country_attribution"]
                if (not _closed(a, ATTRIBUTION_FIELDS) or set(a) != ATTRIBUTION_FIELDS
                        or not isinstance(a["iso3"], str) or not ISO3.fullmatch(a["iso3"])
                        or a["mode"] not in ("individual", "collective")
                        or not _hash(a["supporting_pointer_sha256"])):
                    errors.append("schema_country_attribution_invalid")
            if f["stance"] is not None:
                s = f["stance"]
                if (not _closed(s, STANCE_FIELDS) or set(s) != STANCE_FIELDS
                        or not _ident(s["proposition_id"]) or not _valid_text(s["proposition"])
                        or s["position"] not in ("support", "oppose", "qualified", "unclear")
                        or not _hash(s["evidence_pointer_sha256"])):
                    errors.append("schema_stance_invalid")
        if any(not _ident(x) for x in ids) or len(ids) != len(set(x for x in ids if _ident(x))):
            errors.append("schema_finding_duplicate_id_or_malformed")
    return sorted(set(errors))


def _extract_from_original(receipt: SourceReceipt) -> str | None:
    """Reconstruct the exact Unicode offset basis from authenticated input bytes.

    A non-JSON representation uses decoded UTF-8 bytes directly. A JSON pointer
    follows RFC 6901 and must resolve to a string in the original JSON document.
    No normalization, regex extraction, or silent text correction is performed.
    """
    try:
        raw = receipt.original_bytes.decode("utf-8")
        if receipt.json_pointer is None:
            return raw
        node = json.loads(raw)
        for component in receipt.json_pointer.split("/")[1:]:
            key = component.replace("~1", "/").replace("~0", "~")
            if isinstance(node, dict):
                node = node[key]
            elif isinstance(node, list) and re.fullmatch(r"0|[1-9][0-9]*", key):
                node = node[int(key)]
            else:
                return None
        return node if isinstance(node, str) else None
    except (UnicodeError, ValueError, KeyError, IndexError, TypeError, OverflowError):
        return None


def _source_authenticated(source: dict, receipt: SourceReceipt | None) -> bool:
    if not isinstance(receipt, SourceReceipt):
        return False
    if not (receipt.accepted is True and receipt.public is True
            and isinstance(receipt.original_bytes, bytes) and isinstance(receipt.text, str)):
        return False
    try:
        text_bytes = receipt.text.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return (
        source["id"] == receipt.source_id
        and source["representation_id"] == receipt.representation_id
        and source["parent_id"] == receipt.parent_id
        and source["raw_sha256"] == _sha(receipt.original_bytes)
        and source["text_sha256"] == _sha(text_bytes)
        and source["text_length"] == len(receipt.text)  # Unicode code points, not UTF-8 bytes
        and source["source_url"] == receipt.source_url
        and source["json_pointer"] == receipt.json_pointer
        and source["meeting_id"] == receipt.meeting_id
        and source["speech_id"] == receipt.speech_id
        and source["source_family_id"] == receipt.source_family_id
        and _extract_from_original(receipt) == receipt.text
    )


def pointer_digest(pointer: dict) -> str:
    """Fingerprint exact code-point span, text and representation (not only source ID)."""
    return report_digest(pointer)


def _pointer_authenticated(pointer: dict, sources: dict, proofs: Mapping[str, SourceReceipt]) -> bool:
    source = sources.get(pointer["source_id"])
    receipt = proofs.get(pointer["source_id"])
    return bool(
        source and receipt and _source_authenticated(source, receipt)
        and pointer["text_sha256"] == source["text_sha256"]
        and pointer["representation_id"] == source["representation_id"]
        and pointer["json_pointer"] == source["json_pointer"]
        and pointer["end"] <= len(receipt.text)
    )


def _verbatim_leak(report: dict, proofs: Mapping[str, SourceReceipt]) -> bool:
    """Conservative check for 32-code-point verbatim source excerpts in prose.

    This supplements, but cannot replace, external privacy clearance.
    """
    fields = [report["title"], report["reviewer_note"], report["uncertainty"],
              report["sensitivity"], report["alternative_explanations"]]
    for finding in report["findings"]:
        fields.extend(finding[k] for k in (
            "label", "observation", "pattern", "reviewer_interpretation",
            "uncertainty", "sensitivity", "alternative_explanations") if finding[k])
        if finding["stance"] is not None:
            fields.append(finding["stance"]["proposition"])
    for receipt in proofs.values():
        if not isinstance(receipt, SourceReceipt) or not isinstance(receipt.text, str):
            continue
        txt = receipt.text
        if len(txt) < 32:
            continue
        for field in fields:
            # Exhaustive substring scan, including source spans that cross fixed-size blocks.
            if any(txt[i:i + 32] in field for i in range(len(txt) - 31)):
                return True
    return False


def validate(report: object, proofs: Mapping[str, SourceReceipt] | None = None,
             decision: ReviewDecision | None = None) -> list[str]:
    """Check schema, authenticated source pointers, approval integrity and privacy."""
    errors = _structure(report)
    if errors:
        return errors
    proofs = proofs or {}
    if not isinstance(decision, ReviewDecision) or decision.report_sha256 != report_digest(report):
        errors.append("authorization_missing_or_digest_mismatch")
    else:
        if any(getattr(decision, key) not in GATE_STATES for key in (
            "source_gate", "reviewer_gate", "privacy_gate", "statistical_gate")):
            errors.append("authorization_gate_status_invalid")
        if decision.evaluation_role not in ("synthetic_fixture", "experimental_review", "engineering_only"):
            errors.append("authorization_evaluation_role_invalid")
        if decision.privacy_gate != "pass" or decision.reviewer_gate != "pass":
            errors.append("authorization_privacy_or_review_withheld")
        if decision.source_gate != "pass":
            errors.append("authorization_source_withheld")
    sources = {s["id"]: s for s in report["sources"]}
    for source in sources.values():
        if not _source_authenticated(source, proofs.get(source["id"])):
            errors.append("source_authentication_failed")
    for f in report["findings"]:
        if not f["supporting"]:
            errors.append("evidence_supporting_missing")
        if not all(_pointer_authenticated(ref, sources, proofs) for ref in f["supporting"] + f["contrary"]):
            errors.append("evidence_pointer_unverified")
        a = f["country_attribution"]
        if a is not None:
            match = decision.attributed_countries.get(f["id"]) if isinstance(decision, ReviewDecision) else None
            if (match != (a["iso3"], a["mode"], a["supporting_pointer_sha256"])
                    or a["supporting_pointer_sha256"] not in {pointer_digest(r) for r in f["supporting"]}
                    or (a["mode"] == "individual" and any(
                        proofs[r["source_id"]].collective for r in f["supporting"]
                        if r["source_id"] in proofs and isinstance(proofs[r["source_id"]], SourceReceipt)))):
                errors.append("country_attribution_unverified")
        s = f["stance"]
        if s is not None:
            match = decision.adjudicated_stances.get(f["id"]) if isinstance(decision, ReviewDecision) else None
            if (match != (s["proposition_id"], _sha(s["proposition"].encode("utf-8")), s["position"], s["evidence_pointer_sha256"])
                    or s["evidence_pointer_sha256"] not in {pointer_digest(r) for r in f["supporting"]}):
                errors.append("stance_specific_evidence_unverified")
        if f["category"] == "exploratory" and isinstance(decision, ReviewDecision):
            if (decision.statistical_gate != "pass" or report["coverage"]["converged_fits"] < 1):
                errors.append("statistical_result_withheld")
    if (isinstance(decision, ReviewDecision) and decision.privacy_gate == "pass"
            and _verbatim_leak(report, proofs)):
        errors.append("privacy_verbatim_source_excerpt")
    return sorted(set(errors))


def normalize(report: object, proofs: Mapping[str, SourceReceipt] | None = None,
              decision: ReviewDecision | None = None) -> dict:
    """Produce a strictly allowlisted public view; never serialize source payloads."""
    errors = validate(report, proofs, decision)
    result: dict = {
        "schema": SCHEMA, "release_state": "withheld", "publication_eligible": False,
        "validation_errors": errors, "restrictions": list(RESTRICTIONS),
        "title": "Research readout — withheld", "template": None, "template_guidance": None,
        "coverage": None, "sources": [], "findings": [],
        "uncertainty": "Not established", "sensitivity": "Not established",
        "alternative_explanations": "Not established", "reviewer_note": "Withheld",
    }
    # Any invalid source, pointer, attribution or missing evidence also blocks
    # ALL authored prose, including report-level reviewer notes and titles.
    # Only a failed statistical gate may retain separately approved descriptive
    # evidence, with the unrestricted reviewer note itself withheld.
    blocking = any(e != "statistical_result_withheld" for e in errors)
    if blocking:
        return result
    assert isinstance(report, dict) and isinstance(decision, ReviewDecision)
    # Authored material was approved by digest and review/privacy decisions.
    result.update({key: report[key] for key in (
        "title", "template", "coverage", "uncertainty", "sensitivity",
        "alternative_explanations", "reviewer_note")})
    if "statistical_result_withheld" in errors:
        result["reviewer_note"] = "Withheld pending statistical validation"
    result["template_guidance"] = TEMPLATE_GUIDANCE[report["template"]]
    proofs = proofs or {}
    sources = {s["id"]: s for s in report["sources"]}
    result["sources"] = [
        {k: s[k] for k in SOURCE_FIELDS}
        for s in report["sources"] if _source_authenticated(s, proofs.get(s["id"]))
    ]
    statuses = []
    for finding in report["findings"]:
        reasons = []
        refs = finding["supporting"] + finding["contrary"]
        if not finding["supporting"]:
            reasons.append("missing_supporting_evidence")
        if not all(_pointer_authenticated(ref, sources, proofs) for ref in refs):
            reasons.append("unverified_pointer_or_source")
        a = finding["country_attribution"]
        if a is not None:
            match = decision.attributed_countries.get(finding["id"])
            if (match != (a["iso3"], a["mode"], a["supporting_pointer_sha256"])
                    or a["supporting_pointer_sha256"] not in {pointer_digest(r) for r in finding["supporting"]}
                    or (a["mode"] == "individual" and any(
                        proofs[r["source_id"]].collective for r in finding["supporting"]
                        if r["source_id"] in proofs and isinstance(proofs[r["source_id"]], SourceReceipt)))):
                reasons.append("unverified_country_attribution")
        s = finding["stance"]
        if s is not None and (decision.adjudicated_stances.get(finding["id"]) != (
                s["proposition_id"], _sha(s["proposition"].encode("utf-8")), s["position"], s["evidence_pointer_sha256"])
                or s["evidence_pointer_sha256"] not in {pointer_digest(r) for r in finding["supporting"]}):
            reasons.append("unverified_stance")
        if finding["category"] == "exploratory" and (decision.statistical_gate != "pass"
                                                        or report["coverage"]["converged_fits"] < 1):
            reasons.append("statistical_gate_not_passed")
        if reasons:
            result["findings"].append({"status": "withheld", "reason_codes": sorted(set(reasons))})
            statuses.append("withheld")
            continue
        item = {k: finding[k] for k in (
            "id", "category", "label", "observation", "pattern", "supporting", "contrary",
            "contrary_search", "uncertainty", "sensitivity", "alternative_explanations",
            "country_attribution", "stance")}
        item["reviewer_interpretation"] = (
            finding["reviewer_interpretation"] if finding["id"] in decision.interpreted_findings
            and decision.statistical_gate == "pass" else None
        )
        item["status"] = "descriptive" if finding["category"] == "descriptive" else "exploratory"
        item["reason_codes"] = []
        result["findings"].append(item)
        statuses.append(item["status"])
    if "exploratory" in statuses:
        result["release_state"] = (
            "synthetic_demo" if decision.evaluation_role == "synthetic_fixture"
            else "qualified_experimental"
        )
    elif "descriptive" in statuses:
        result["release_state"] = "descriptive_only"
    return result


def _md(value: object) -> str:
    """Literal Markdown text, not arbitrary markup or unsafe HTML."""
    return escape(str(value), quote=False).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def render(report: object, format: str = "json", *,
           proofs: Mapping[str, SourceReceipt] | None = None,
           decision: ReviewDecision | None = None) -> str:
    if format not in ("json", "markdown", "html"):
        raise ValueError("unsupported format")
    view = normalize(report, proofs, decision)
    if format == "json":
        return json.dumps(view, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    lines = ["# " + _md(view["title"]), "", "Status: " + view["release_state"],
             "Publication eligible: no", ""]
    if view["template_guidance"] is not None:
        lines.extend(["## Evidence question", "", _md(view["template_guidance"]["question"]), "",
                      "## Template-specific qualification", "", _md(view["template_guidance"]["limit"]), ""])
    if view["coverage"] is not None:
        cov = view["coverage"]
        lines.extend(["## Declared scope", ""])
        for key in ("population", "period", "unit", "weighting", "source_group_unit",
                    "total_in_frame", "eligible", "excluded", "missing", "unassigned",
                    "planned_fits", "attempted_fits", "converged_fits", "failed_fits", "skipped_fits"):
            lines.append("- " + key.replace("_", " ").title() + ": " + _md(cov[key]))
        for key in ("exclusion_reasons", "missing_reasons"):
            lines.append("- " + key.replace("_", " ").title() + ": " + _md(
                json.dumps(cov[key], sort_keys=True, ensure_ascii=False)))
        lines.append("")
    lines.extend(["## Evidence", ""])
    if not view["findings"]:
        lines.append("No authorized findings to display.")
    source_index = {s["id"]: s for s in view["sources"]}
    for f in view["findings"]:
        if f["status"] == "withheld":
            lines.append("- WITHHELD: " + ", ".join(f["reason_codes"]))
            continue
        lines.append("### " + _md(f["label"]) + " — " + f["status"])
        lines.append("")
        lines.append(_md(f["observation"] or f["pattern"]))
        for role in ("supporting", "contrary"):
            if f[role]:
                for p in f[role]:
                    location = source_index.get(p["source_id"], {}).get("source_url")
                    lines.append("- " + role + ": " + _md(p["source_id"]) +
                                 " (" + _md(p["representation_id"]) + ", " +
                                 str(p["start"]) + ":" + str(p["end"]) + ", text SHA-256 " +
                                 p["text_sha256"] + ")" +
                                 (" — original: " + _md(location) if location else ""))
            elif role == "contrary":
                lines.append("- Contrary-passage search: " + f["contrary_search"].replace("_", " "))
        if f["country_attribution"] is not None:
            a = f["country_attribution"]
            lines.append("- Country attribution: " + _md(a["iso3"]) + " (" + _md(a["mode"]) + ")")
        if f["stance"] is not None:
            s = f["stance"]
            lines.append("- Expressed stance on specific proposition " + _md(s["proposition_id"]) +
                         ": " + _md(s["position"]) + "; not a vote or government-wide position")
        for key in ("uncertainty", "sensitivity", "alternative_explanations"):
            lines.append("- " + key.replace("_", " ").title() + ": " + _md(f[key]))
        lines.append("- Reviewer interpretation: " + _md(f["reviewer_interpretation"] or "WITHHELD"))
        lines.append("")
    for key in ("uncertainty", "sensitivity", "alternative_explanations", "reviewer_note"):
        lines.extend(["## " + key.replace("_", " ").title(), "", _md(view[key]), ""])
    lines.extend(["## Limitations", ""])
    lines.extend("- " + _md(x) for x in RESTRICTIONS)
    if view["validation_errors"]:
        lines.extend(["", "## Validation status", ""])
        lines.extend("- " + _md(x) for x in view["validation_errors"])
    md = "\n".join(lines) + "\n"
    if format == "markdown":
        return md
    return ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; "
            "style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">"
            "<title>Research readout</title>"
            "<style>body{font:16px/1.6 system-ui,sans-serif;max-width:74ch;"
            "margin:2rem auto;padding:0 1rem;color:#18212d;background:#fff}"
            "pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}</style>"
            "</head><body><main aria-label=\"Research readout\"><pre>" + escape(md) +
            "</pre></main></body></html>\n")


def export(report: object, directory: str | Path, *,
           proofs: Mapping[str, SourceReceipt] | None = None,
           decision: ReviewDecision | None = None) -> dict[str, str]:
    """Write deterministic offline formats; refuse overwrite/symlinks."""
    dest = Path(directory)
    if dest.is_symlink():
        raise ValueError("output directory cannot be symlink")
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise FileExistsError("output directory must be empty; no overwrite")
    data = {ext: render(report, fmt, proofs=proofs, decision=decision).encode("utf-8")
            for fmt, ext in (("json", "json"), ("markdown", "md"), ("html", "html"))}
    dest.mkdir(parents=True, exist_ok=True)
    for ext, content in data.items():
        (dest / ("readout." + ext)).write_bytes(content)
    return {ext: _sha(content) for ext, content in data.items()}
