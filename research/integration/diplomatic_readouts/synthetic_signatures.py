"""Offline synthetic Ed25519 custody and revocation verification -- NEVER access authorization.

This module accepts invented registry metadata only. External trust anchors and
revocation high-water marks are required. Even correctly signed inputs confer no
permission to access sources, open protected meetings, review claims or publish.
This is an engineering simulation, not a PKI, authenticated private registry, or
real-world custodian identity certification.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
import base64
import binascii
import json
import re
from typing import Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from private_source_contract import REQUIRED_GATES, proposal_digest
from registry_preflight import (
    LOCK, PreflightWithheld, assert_no_authority, preflight, registry_digest,
)

CUSTODY_SCHEMA = "un.synthetic-custody-attestation.v0"
REVOCATION_SCHEMA = "un.synthetic-revocation-checkpoint.v0"
SIGNED_SCHEMA = "un.synthetic-ed25519-envelope.v0"
RESULT_SCHEMA = "un.synthetic-custodian-signature-preflight.v0"
AUDIENCE = "synthetic:unga81-metadata-preflight"
DOMAINS = {
    CUSTODY_SCHEMA: b"UNGA81/SYNTHETIC/CUSTODY/ED25519/V0\x00",
    REVOCATION_SCHEMA: b"UNGA81/SYNTHETIC/REVOCATION/ED25519/V0\x00",
}
CUSTODY_FIELDS = frozenset((
    "schema", "fixture_kind", "registry_id", "registry_sha256",
    "policy_sha256", "proposal_sha256", "audit_tip_sha256",
    "purpose", "audience", "custodian_ref", "issued_at", "expires_at", "permission",
))
REVOCATION_FIELDS = frozenset((
    "schema", "fixture_kind", "registry_id", "sequence", "observed_at",
    "expires_at", "revoked_key_ids", "audience", "purpose", "issuer_ref", "permission",
))
ENVELOPE_FIELDS = frozenset(("schema", "algorithm", "key_id", "payload", "signature_b64"))
RESULT_FIELDS = frozenset((
    "schema", "fixture_kind", "status", "reason_codes", "registry_sha256",
    "checkpoint_sequence", "signature_verified", "revocation_verified", "gate_status",
    "holdout_lock", "authority", "authorized", "can_read_source",
    "can_issue_review", "statistical_eligible", "publication_eligible",
    "delivery_eligible", "source_text_included", "source_rows_exported",
))
HEX = re.compile(r"[a-f0-9]{64}\Z")
SYNID = re.compile(r"synthetic:[A-Za-z0-9][A-Za-z0-9._:-]{0,100}\Z")
UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
ZERO_PERMISSIONS = "no_source_access_or_release"


class SignatureWithheld(ValueError):
    """Safe reason code; no private keys, registry row data or original bytes."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise SignatureWithheld(code)


def _closed(obj: object, fields: frozenset, code: str) -> dict:
    _require(type(obj) is dict and set(obj) == fields, code)
    return obj


def _hex(x: object) -> bool:
    return type(x) is str and HEX.fullmatch(x) is not None


def _ident(x: object) -> bool:
    return type(x) is str and SYNID.fullmatch(x) is not None


def _time(x: object) -> datetime:
    _require(type(x) is str and UTC.fullmatch(x) is not None, "signed_timestamp_invalid")
    try:
        return datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise SignatureWithheld("signed_timestamp_invalid") from None


def _canon(obj: object) -> bytes:
    try:
        result = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                            ensure_ascii=True, allow_nan=False).encode("ascii")
    except (TypeError, ValueError, OverflowError, UnicodeError, RecursionError):
        raise SignatureWithheld("signed_payload_not_canonical") from None
    _require(len(result) <= 8192, "signed_payload_too_large")
    return result


def content_digest(schema: str, payload: dict) -> str:
    _require(schema in DOMAINS and type(payload) is dict, "signed_payload_type_invalid")
    return sha256(DOMAINS[schema] + _canon(payload)).hexdigest()


def policy_digest(policy: dict) -> str:
    return sha256(b"UNGA81/SYNTHETIC/CUSTODY-POLICY/V0\x00" + _canon(policy)).hexdigest()


@dataclass(frozen=True)
class SyntheticTrustAnchors:
    """External trust configuration. Supplying this does not prove real-world authority.

    Public keys, current expected source digest, signed revocation checkpoint
    digest and high-water counter MUST be pinned independently of untrusted
    signed envelopes. In tests these pins are created from invented fixtures.
    """

    custodian_keys: Mapping[str, bytes]
    revocation_keys: Mapping[str, bytes]
    custodian_subjects: Mapping[str, str]
    expected_custodian_ref: str
    expected_revocation_issuer_ref: str
    expected_registry_id: str
    expected_registry_sha256: str
    expected_proposal_sha256: str
    expected_checkpoint_sha256: str
    minimum_checkpoint_sequence: int
    expected_audience: str = AUDIENCE
    fixture_kind: str = "synthetic"


def _anchors(trust: object) -> None:
    _require(isinstance(trust, SyntheticTrustAnchors)
             and trust.fixture_kind == "synthetic"
             and _ident(trust.expected_registry_id)
             and _ident(trust.expected_custodian_ref)
             and _ident(trust.expected_revocation_issuer_ref)
             and all(_hex(x) for x in (
                 trust.expected_registry_sha256, trust.expected_proposal_sha256,
                 trust.expected_checkpoint_sha256))
             and type(trust.minimum_checkpoint_sequence) is int
             and trust.minimum_checkpoint_sequence >= 2
             and trust.expected_audience == AUDIENCE,
             "independent_trust_anchor_missing_or_invalid")
    for mapping in (trust.custodian_keys, trust.revocation_keys):
        _require(isinstance(mapping, Mapping) and 1 <= len(mapping) <= 16,
                 "independent_trust_anchor_missing_or_invalid")
        for kid, data in mapping.items():
            _require(_ident(kid) and type(data) is bytes and len(data) == 32,
                     "independent_trust_anchor_missing_or_invalid")
    _require(isinstance(trust.custodian_subjects, Mapping) and
             set(trust.custodian_subjects) == set(trust.custodian_keys) and
             all(subject == trust.expected_custodian_ref
                 for subject in trust.custodian_subjects.values()),
             "independent_custodian_identity_binding_missing")
    # Never let the custodian and revocation authority use the identical key material.
    _require(set(trust.custodian_keys.values()).isdisjoint(
        set(trust.revocation_keys.values())), "independent_revocation_signer_required")


def _verify_signed(envelope: object, schema: str, keys: Mapping[str, bytes]) -> tuple[dict, str]:
    e = _closed(envelope, ENVELOPE_FIELDS, "signed_envelope_not_closed")
    _require(e["schema"] == SIGNED_SCHEMA and e["algorithm"] == "Ed25519" and
             _ident(e["key_id"]), "unsupported_signature_algorithm_or_identity")
    _require(e["key_id"] in keys, "untrusted_signature_key")
    fields = CUSTODY_FIELDS if schema == CUSTODY_SCHEMA else REVOCATION_FIELDS
    payload = _closed(e["payload"], fields, "signed_payload_not_closed")
    _require(payload["schema"] == schema and payload["fixture_kind"] == "synthetic" and
             payload["audience"] == AUDIENCE and
             payload["permission"] == ZERO_PERMISSIONS,
             "signed_payload_scope_invalid")
    sig = e["signature_b64"]
    _require(type(sig) is str and 0 < len(sig) <= 100,
             "invalid_signature_encoding")
    try:
        binary = base64.b64decode(sig.encode("ascii"), validate=True)
        _require(len(binary) == 64 and base64.b64encode(binary).decode("ascii") == sig,
                 "invalid_signature_encoding")
    except (UnicodeError, binascii.Error):
        raise SignatureWithheld("invalid_signature_encoding") from None
    try:
        Ed25519PublicKey.from_public_bytes(keys[e["key_id"]]).verify(
            binary, DOMAINS[schema] + _canon(payload))
    except (InvalidSignature, ValueError, TypeError):
        raise SignatureWithheld("invalid_ed25519_signature") from None
    return payload, e["key_id"]


def _empty_result() -> dict:
    return {
        "schema": RESULT_SCHEMA, "fixture_kind": "synthetic",
        "status": "withheld", "reason_codes": [], "registry_sha256": None,
        "checkpoint_sequence": None, "signature_verified": False,
        "revocation_verified": False, "gate_status": {g: "NOT_RUN" for g in REQUIRED_GATES},
        "holdout_lock": dict(LOCK), "authority": "none", "authorized": False,
        "can_read_source": False, "can_issue_review": False,
        "statistical_eligible": False, "publication_eligible": False,
        "delivery_eligible": False, "source_text_included": False,
        "source_rows_exported": False,
    }


def verify_synthetic_signatures(snapshot: object, policy: object, events: object,
                                proposal: object, custody_envelope: object,
                                revocation_envelope: object, *, checked_at: str,
                                trust: SyntheticTrustAnchors | None) -> dict:
    """Verify signed *synthetic* metadata and return a ZERO-authority receipt.

    This verifies two Ed25519 signatures, not the custodian's real identity,
    original source, or rights. A positive result MUST NEVER authorize access.
    """
    result = _empty_result()
    try:
        _anchors(trust)
        now = _time(checked_at)
        prior = preflight(snapshot, policy, events, checked_at=checked_at, proposal=proposal)
        assert_no_authority(prior)
        _require(prior["metadata_status"] == "metadata_consistent",
                 "underlying_registry_preflight_withheld")
        _require(prior["registry_sha256"] == trust.expected_registry_sha256
                 and snapshot["registry_id"] == trust.expected_registry_id
                 and proposal_digest(proposal) == trust.expected_proposal_sha256,
                 "externally_pinned_source_or_proposal_mismatch")
        revoke, signer = _verify_signed(revocation_envelope, REVOCATION_SCHEMA,
                                         trust.revocation_keys)
        _require(revoke["registry_id"] == trust.expected_registry_id
                 and revoke["purpose"] == "synthetic_revocation_verification" and
                 revoke["issuer_ref"] == trust.expected_revocation_issuer_ref and
                 type(revoke["sequence"]) is int and
                 revoke["sequence"] >= trust.minimum_checkpoint_sequence and
                 revoke["sequence"] >= policy["revocation_sequence"] and
                 type(revoke["revoked_key_ids"]) is list and
                 len(revoke["revoked_key_ids"]) <= 32 and
                 all(_ident(x) for x in revoke["revoked_key_ids"]) and
                 revoke["revoked_key_ids"] == sorted(set(revoke["revoked_key_ids"])),
                 "revocation_checkpoint_invalid_or_rollback")
        _require(content_digest(REVOCATION_SCHEMA, revoke) ==
                 trust.expected_checkpoint_sha256,
                 "revocation_checkpoint_not_externally_pinned")
        observed = _time(revoke["observed_at"])
        expired = _time(revoke["expires_at"])
        _require(observed <= now < expired and
                 timedelta(0) < expired - observed <= timedelta(days=7),
                 "revocation_checkpoint_expired_or_future")
        _require(observed >= _time(events[-1]["occurred_at"]),
                 "revocation_checkpoint_predates_audit_tip")
        _require(signer not in revoke["revoked_key_ids"], "revocation_signer_revoked")
        custody, key = _verify_signed(custody_envelope, CUSTODY_SCHEMA,
                                       trust.custodian_keys)
        _require(custody["registry_id"] == trust.expected_registry_id and
                 custody["registry_sha256"] == trust.expected_registry_sha256 and
                 custody["proposal_sha256"] == trust.expected_proposal_sha256 and
                 custody["policy_sha256"] == policy_digest(policy) and
                 custody["audit_tip_sha256"] == events[-1]["event_sha256"] and
                 custody["custodian_ref"] == trust.expected_custodian_ref and
                 custody["custodian_ref"] == policy["custodian_ref"] and
                 custody["purpose"] == "synthetic_metadata_preflight",
                 "custody_signature_binding_mismatch")
        _require(_time(policy["issued_at"]) <= _time(custody["issued_at"]) <= now
                 and now < _time(custody["expires_at"]) <= _time(policy["expires_at"]),
                 "custody_signature_expired_or_future")
        _require(key not in revoke["revoked_key_ids"], "custodian_key_revoked")
        result["status"] = "synthetic_signatures_verified_no_authority"
        result["registry_sha256"] = trust.expected_registry_sha256
        result["checkpoint_sequence"] = revoke["sequence"]
        result["signature_verified"] = True
        result["revocation_verified"] = True
    except SignatureWithheld as exc:
        result["reason_codes"] = [str(exc)]
    except (PreflightWithheld, TypeError, KeyError, ValueError, AttributeError,
            OverflowError, RecursionError, UnicodeError, IndexError, AssertionError):
        result["reason_codes"] = ["malformed_or_untrusted_metadata"]
    return result


def assert_zero_authority(result: object) -> None:
    r = _closed(result, RESULT_FIELDS, "signature_receipt_not_closed")
    _require(r["schema"] == RESULT_SCHEMA and r["fixture_kind"] == "synthetic"
             and r["status"] in ("withheld", "synthetic_signatures_verified_no_authority")
             and r["authority"] == "none" and all(r[k] is False for k in (
                 "authorized", "can_read_source", "can_issue_review", "statistical_eligible",
                 "publication_eligible", "delivery_eligible", "source_text_included",
                 "source_rows_exported")) and r["holdout_lock"] == LOCK and
             r["gate_status"] == {g: "NOT_RUN" for g in REQUIRED_GATES},
             "signature_receipt_authority_escalation")
    _require(type(r["reason_codes"]) is list and
             all(type(v) is str and re.fullmatch(r"[a-z0-9_]{3,80}", v) for v in r["reason_codes"]),
             "signature_receipt_reasons_invalid")
    if r["status"] == "withheld":
        _require(r["reason_codes"] != [] and r["registry_sha256"] is None and
                 r["checkpoint_sequence"] is None and
                 r["signature_verified"] is False and r["revocation_verified"] is False,
                 "signature_receipt_failed_exposure")
    else:
        _require(r["reason_codes"] == [] and _hex(r["registry_sha256"]) and
                 type(r["checkpoint_sequence"]) is int and r["checkpoint_sequence"] >= 2
                 and r["signature_verified"] is True and r["revocation_verified"] is True,
                 "signature_receipt_success_invalid")


def receipt_sha256(result: dict) -> str:
    assert_zero_authority(result)
    return sha256(b"UNGA81/SYNTHETIC/SIGNATURE-RECEIPT/V0\x00" + _canon(result)).hexdigest()
