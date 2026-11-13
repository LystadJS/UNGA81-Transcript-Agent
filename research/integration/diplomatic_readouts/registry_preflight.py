"""Metadata-only synthetic registry preflight; never an authorization issuer.

Inputs are fictional metadata. This module cannot inspect original sources,
verify a custodian's identity, approve reviewer labels, or release results.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
import re

from private_source_contract import (REQUIRED_GATES, assert_design_only, AuthorizationWithheld)

SNAPSHOT_SCHEMA = "un.private-source-registry.metadata.v0"
POLICY_SCHEMA = "un.private-source-registry.custody-intent.v0"
RECEIPT_SCHEMA = "un.private-source-registry.preflight-receipt.v0"
HEX = re.compile(r"[a-f0-9]{64}\Z")
IDENT = re.compile(r"synthetic:[A-Za-z0-9][A-Za-z0-9._:-]{0,100}\Z")
SNAPSHOT_KEYS = frozenset((
    "schema", "fixture_kind", "registry_id", "registry_revision", "previous_registry_sha256",
    "recorded_at", "source_schema", "source_hash_basis", "source_sha256",
    "selection_sha256", "records", "population", "holdout_lock"))
RECORD_KEYS = frozenset((
    "id", "parent_id", "source_family_id", "meeting_id", "event_date",
    "source_status", "exclusion_code", "missing_reason", "raw_sha256",
    "text_sha256", "representation_id", "offset_basis", "classification"))
POP_KEYS = frozenset((
    "total_in_frame", "observations_total", "eligible", "excluded", "unavailable", "unobserved"))
POLICY_KEYS = frozenset((
    "schema", "fixture_kind", "registry_id", "registry_sha256", "custodian_ref",
    "reviewer_ref", "issuer_ref", "purpose", "issued_at", "expires_at",
    "revocation_sequence", "attestation", "requested_scopes", "permissions"))
PERM_KEYS = frozenset((
    "read_source_bytes", "read_reserved", "write_registry", "issue_reviewer_decision",
    "approve_statistics", "publish", "send_mail"))
EVENT_KEYS = frozenset((
    "index", "event_id", "kind", "actor_ref", "occurred_at", "registry_sha256",
    "previous_sha256", "event_sha256"))
RECEIPT_KEYS = frozenset((
    "schema", "mode", "metadata_status", "reason_codes", "registry_sha256",
    "population", "gate_status", "holdout_lock", "authority", "authorized",
    "can_read_source", "can_issue_review", "statistical_eligible", "publication_eligible",
    "delivery_eligible", "source_text_included", "source_rows_exported"))
LOCK = {"reserved_meetings": 37, "transcripts_opened": 0,
        "access_granted": False, "d1_o1_o5": "frozen"}
ZERO = "0" * 64


class PreflightWithheld(ValueError):
    """Fixed, non-sensitive rejection code."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise PreflightWithheld(code)


def _exact(value: object, keys: frozenset, code: str) -> None:
    _require(type(value) is dict and set(value) == keys, code)


def _ident(value: object) -> bool:
    return type(value) is str and IDENT.fullmatch(value) is not None


def _hash(value: object) -> bool:
    return type(value) is str and HEX.fullmatch(value) is not None


def _count(value: object) -> bool:
    return type(value) is int and value >= 0


def _utc(value: object) -> datetime:
    _require(type(value) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value),
             "timestamp_not_utc")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise PreflightWithheld("timestamp_invalid") from None


def _digest(domain: bytes, value: object) -> str:
    try:
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise PreflightWithheld("malformed_metadata") from None
    return sha256(domain + payload).hexdigest()


def registry_digest(snapshot: dict) -> str:
    """Consistency digest, NOT a custodian signature."""
    return _digest(b"un.private-source-registry.metadata.v0\n", snapshot)


def event_digest(event_without_hash: dict) -> str:
    return _digest(b"un.private-source-registry.event.v0\n", event_without_hash)


def _validate_snapshot(snapshot: object) -> str:
    _exact(snapshot, SNAPSHOT_KEYS, "snapshot_not_closed")
    s = snapshot
    _require(s["schema"] == SNAPSHOT_SCHEMA and s["fixture_kind"] == "synthetic",
             "real_registry_forbidden")
    _require(_ident(s["registry_id"]) and _count(s["registry_revision"])
             and s["registry_revision"] >= 1, "registry_identity_invalid")
    _require((s["registry_revision"] == 1 and s["previous_registry_sha256"] is None)
             or (s["registry_revision"] > 1 and _hash(s["previous_registry_sha256"])),
             "registry_revision_chain_invalid")
    _utc(s["recorded_at"])
    _require(s["source_schema"] in ("synthetic.v1", "un.browser.corpus.v1",
              "un.passage-corpus.v1", "un.review.v1") and
             s["source_hash_basis"] == "synthetic" and
             _hash(s["source_sha256"]) and _hash(s["selection_sha256"]),
             "source_or_selection_lineage_invalid")
    _require(_sealed(s["holdout_lock"]), "reserved_holdout_lock_violation")
    _exact(s["population"], POP_KEYS, "population_shape_invalid")
    counts = s["population"]
    _require(all(_count(v) for v in counts.values()), "population_count_invalid")
    _require(type(s["records"]) is list and len(s["records"]) <= 128,
             "registry_records_invalid")
    _require(counts["observations_total"] == len(s["records"])
             and counts["total_in_frame"] == counts["observations_total"] + counts["unobserved"]
             and counts["observations_total"] == counts["eligible"] + counts["excluded"] + counts["unavailable"],
             "population_accounting_invalid")
    ids = set()
    tally = {"eligible": 0, "excluded": 0, "unavailable": 0}
    for r in s["records"]:
        _exact(r, RECORD_KEYS, "source_record_not_closed")
        _require(_ident(r["id"]) and r["id"] not in ids, "source_id_duplicate_or_invalid")
        ids.add(r["id"])
        _require(all(x is None or _ident(x) for x in (
            r["parent_id"], r["source_family_id"], r["meeting_id"])),
            "source_linkage_invalid")
        day = r["event_date"]
        _require(type(day) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}", day),
                 "source_date_invalid")
        try:
            datetime.strptime(day, "%Y-%m-%d")
        except ValueError:
            raise PreflightWithheld("source_date_invalid") from None
        _require(day not in ("2026-10-05", "2026-10-06"), "reserved_dates_forbidden")
        _require(r["classification"] == "synthetic_only", "non_synthetic_material_forbidden")
        status = r["source_status"]
        if status == "available":
            _require(_hash(r["raw_sha256"]) and _hash(r["text_sha256"])
                     and _ident(r["representation_id"]) and
                     r["offset_basis"] == "unicode_codepoints"
                     and r["missing_reason"] is None,
                     "available_source_metadata_invalid")
            if r["exclusion_code"] is None:
                tally["eligible"] += 1
            else:
                _require(_ident(r["exclusion_code"]), "exclusion_code_invalid")
                tally["excluded"] += 1
        else:
            _require(status in ("unavailable", "failed", "inventory_failed")
                     and _ident(r["missing_reason"]) and r["exclusion_code"] is None
                     and r["raw_sha256"] is None and r["text_sha256"] is None
                     and r["representation_id"] is None and r["offset_basis"] is None,
                     "unavailable_source_metadata_invalid")
            tally["unavailable"] += 1
    _require(all(tally[k] == counts[k] for k in tally), "record_population_mismatch")
    return registry_digest(s)


def _validate_policy(policy: object, snapshot: dict, snapshot_sha: str, checked_at: datetime) -> None:
    _exact(policy, POLICY_KEYS, "custody_intent_not_closed")
    p = policy
    _require(p["schema"] == POLICY_SCHEMA and p["fixture_kind"] == "synthetic"
             and p["registry_id"] == snapshot["registry_id"]
             and p["registry_sha256"] == snapshot_sha, "custody_binding_invalid")
    _require(all(_ident(p[k]) for k in ("custodian_ref", "reviewer_ref", "issuer_ref"))
             and p["purpose"] == "synthetic_metadata_preflight"
             and p["attestation"] == "unverified_metadata_consistency_only"
             and p["requested_scopes"] == ["synthetic_metadata_inventory"],
             "custody_scope_or_identity_invalid")
    _exact(p["permissions"], PERM_KEYS, "custody_permissions_not_closed")
    _require(all(p["permissions"][k] is False for k in PERM_KEYS),
             "custody_permission_escalation")
    _require(_count(p["revocation_sequence"]), "revocation_sequence_invalid")
    issued, expires = _utc(p["issued_at"]), _utc(p["expires_at"])
    _require(_utc(snapshot["recorded_at"]) <= issued <= checked_at < expires,
             "custody_expired_or_future")


def _validate_audit(events: object, snapshot_sha: str, policy: dict,
                    checked_at: datetime) -> None:
    _require(type(events) is list and 2 <= len(events) <= 128, "audit_chain_incomplete")
    _require(len(events) == policy["revocation_sequence"], "revocation_ledger_stale")
    last_hash, last_time, used = ZERO, None, set()
    for index, e in enumerate(events, 1):
        _exact(e, EVENT_KEYS, "audit_event_not_closed")
        _require(type(e["index"]) is int and e["index"] == index and _ident(e["event_id"])
                 and e["event_id"] not in used and _ident(e["actor_ref"])
                 and e["registry_sha256"] == snapshot_sha and
                 e["previous_sha256"] == last_hash,
                 "audit_sequence_or_registry_mismatch")
        used.add(e["event_id"])
        when = _utc(e["occurred_at"])
        _require(when <= checked_at and (last_time is None or last_time <= when),
                 "audit_time_order_invalid")
        kind = e["kind"]
        _require(kind in ("registered", "metadata_checked", "revoked")
                 and (index != 1 or kind == "registered")
                 and (index != 2 or kind == "metadata_checked")
                 and (index <= 2 or kind in ("metadata_checked", "revoked")),
                 "audit_action_invalid")
        _require(index != 1 or e["actor_ref"] == policy["custodian_ref"],
                 "audit_custodian_mismatch")
        _require(index != 2 or e["actor_ref"] == policy["reviewer_ref"],
                 "audit_reviewer_mismatch")
        expected = event_digest({k: v for k, v in e.items() if k != "event_sha256"})
        _require(e["event_sha256"] == expected, "audit_hash_chain_invalid")
        _require(kind != "revoked", "registry_or_custody_revoked")
        last_hash, last_time = e["event_sha256"], when


def _validate_existing_proposal(proposal: object, snapshot: dict) -> None:
    """Bind to the existing unapproved v0 handoff; NEVER convert it to access."""
    try:
        assert_design_only(proposal)
    except (AuthorizationWithheld, KeyError, TypeError, ValueError, AttributeError):
        raise PreflightWithheld("existing_private_proposal_invalid") from None
    p = proposal["population"]
    src = proposal["source_identity"]
    counts = snapshot["population"]
    _require(src["upstream_source_schema"] == snapshot["source_schema"]
             and src["source_hash_basis"] == snapshot["source_hash_basis"]
             and src["source_sha256"] == snapshot["source_sha256"]
             and src["selection_sha256"] == snapshot["selection_sha256"]
             and p["total_in_frame"] == counts["total_in_frame"]
             and p["observations_total"] == counts["observations_total"]
             and p["eligible"] == counts["eligible"]
             and p["excluded"] == counts["excluded"] + counts["unavailable"]
             and p["unavailable_sources"] == counts["unavailable"],
             "existing_private_proposal_population_or_lineage_mismatch")


def _sealed(value: object) -> bool:
    return (type(value) is dict and set(value) == set(LOCK)
            and type(value["reserved_meetings"]) is int
            and value["reserved_meetings"] == 37
            and type(value["transcripts_opened"]) is int
            and value["transcripts_opened"] == 0
            and value["access_granted"] is False
            and value["d1_o1_o5"] == "frozen")


def _withheld() -> dict:
    return {
        "schema": RECEIPT_SCHEMA, "mode": "synthetic_metadata_only",
        "metadata_status": "withheld", "reason_codes": [], "registry_sha256": None,
        "population": None, "gate_status": {k: "NOT_RUN" for k in REQUIRED_GATES},
        "holdout_lock": dict(LOCK), "authority": "none", "authorized": False,
        "can_read_source": False, "can_issue_review": False,
        "statistical_eligible": False, "publication_eligible": False,
        "delivery_eligible": False, "source_text_included": False,
        "source_rows_exported": False,
    }


def preflight(snapshot: object, policy: object, events: object, *, checked_at: str,
              proposal: object = None) -> dict:
    """Return only an aggregate synthetic consistency receipt, never grants.

    'metadata_consistent' is NOT proof of custodian identity, review, privacy,
    source authenticity, statistics or permission to read any source.
    """
    output = _withheld()
    try:
        now = _utc(checked_at)
        digest = _validate_snapshot(snapshot)
        _validate_policy(policy, snapshot, digest, now)
        _validate_audit(events, digest, policy, now)
        _validate_existing_proposal(proposal, snapshot)
        output["metadata_status"] = "metadata_consistent"
        output["registry_sha256"] = digest
        output["population"] = dict(snapshot["population"])
    except PreflightWithheld as exc:
        output["reason_codes"] = [str(exc)]
    except (TypeError, KeyError, ValueError, AttributeError, OverflowError, RecursionError, UnicodeError):
        output["reason_codes"] = ["malformed_metadata"]
    return output


def assert_no_authority(receipt: object) -> None:
    """Verify strictly closed exported receipt; refuse tampering/escalation."""
    _exact(receipt, RECEIPT_KEYS, "receipt_invalid_or_extra_fields")
    _require(receipt["schema"] == RECEIPT_SCHEMA and
             receipt["mode"] == "synthetic_metadata_only" and
             receipt["metadata_status"] in ("withheld", "metadata_consistent"),
             "receipt_invalid")
    _require(receipt["authority"] == "none" and
             all(receipt[k] is False for k in (
                 "authorized", "can_read_source", "can_issue_review", "statistical_eligible",
                 "publication_eligible", "delivery_eligible", "source_text_included",
                 "source_rows_exported")), "receipt_cannot_grant_authority")
    _require(_sealed(receipt["holdout_lock"]) and
             receipt["gate_status"] == {k: "NOT_RUN" for k in REQUIRED_GATES},
             "receipt_gate_or_holdout_violation")
    errors = receipt["reason_codes"]
    _require(type(errors) is list and all(type(v) is str and
             re.fullmatch(r"[a-z_]{3,80}", v) for v in errors), "receipt_error_codes_invalid")
    if receipt["metadata_status"] == "withheld":
        _require(len(errors) > 0 and receipt["population"] is None
                 and receipt["registry_sha256"] is None, "receipt_withheld_data_leak")
    else:
        _require(errors == [] and _hash(receipt["registry_sha256"]),
                 "receipt_valid_metadata_invalid")
        _exact(receipt["population"], POP_KEYS, "receipt_population_invalid")
        pop = receipt["population"]
        _require(all(_count(v) for v in pop.values())
                 and pop["total_in_frame"] == pop["observations_total"] + pop["unobserved"]
                 and pop["observations_total"] == pop["eligible"] + pop["excluded"] + pop["unavailable"],
                 "receipt_population_invalid")


def receipt_digest(receipt: dict) -> str:
    assert_no_authority(receipt)
    return _digest(b"un.private-source-registry.preflight-receipt.v0\n", receipt)
