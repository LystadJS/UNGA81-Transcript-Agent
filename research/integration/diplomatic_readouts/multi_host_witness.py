"""Synthetic four-witness, two-observer audit consistency *simulation*.

No capability to grant source access, sign as a real custodian, query a real
registry, or change scientific/publication gates. The adversary may supply all
arguments: security claims hold only conditional on independently pinned honest
witness keys, at least two distinct honest observers, and their persistent state.
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

from private_source_contract import REQUIRED_GATES
from registry_preflight import LOCK
from synthetic_signatures import (
    SyntheticTrustAnchors, REVOCATION_SCHEMA, content_digest,
    verify_synthetic_signatures,
)

LOG_SCHEMA = "un.synthetic-witness-log.v0"
CHECKPOINT_SCHEMA = "un.synthetic-witness-checkpoint.v0"
ATTESTATION_SCHEMA = "un.synthetic-witness-attestation.v0"
RECEIPT_SCHEMA = "un.synthetic-multi-host-witness-review.v0"
AUDIENCE = "synthetic:unga81-multi-host-revocation"
DOMAIN_EVENT = b"UNGA81/SYNTHETIC/WITNESS/EVENT/V0\x00"
DOMAIN_LOG = b"UNGA81/SYNTHETIC/WITNESS/LOG/V0\x00"
DOMAIN_CHECKPOINT = b"UNGA81/SYNTHETIC/WITNESS/CHECKPOINT/V0\x00"
DOMAIN_ATTEST = b"UNGA81/SYNTHETIC/WITNESS/ATTEST/V0\x00"
DOMAIN_ANCHOR = b"UNGA81/SYNTHETIC/WITNESS/OBSERVER-ANCHOR/V0\x00"
ZERO = "0" * 64
HEX = re.compile(r"[0-9a-f]{64}\Z")
IDENT = re.compile(r"synthetic:[A-Za-z0-9][A-Za-z0-9._:-]{0,100}\Z")
CLOCK = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
EVENT_FIELDS = frozenset(("schema", "index", "event_id", "kind", "registry_sha256",
                          "revocation_sha256", "occurred_at", "previous_sha256", "event_sha256"))
CP_FIELDS = frozenset(("schema", "fixture_kind", "registry_id", "registry_sha256",
                       "audit_tip_sha256", "revocation_sha256", "revocation_sequence",
                       "epoch", "log_length", "log_sha256", "log_tip_sha256",
                       "previous_checkpoint_sha256", "audience", "signed_at", "expires_at",
                       "permission"))
SIGN_FIELDS = frozenset(("schema", "key_id", "payload", "signature_b64"))
RECEIPT_FIELDS = frozenset(("schema", "status", "reason_codes", "fixture_kind",
                            "authority", "authorized", "can_read_source", "can_issue_review",
                            "statistical_eligible", "publication_eligible", "delivery_eligible",
                            "gate_status", "holdout_lock", "source_text_included",
                            "source_rows_exported", "epoch", "log_length", "quorum_size",
                            "checkpoint_sha256"))

class WitnessWithheld(ValueError):
    """Non-sensitive rejection reason; never returns untrusted original fields."""


def _require(value: bool, code: str) -> None:
    if not value:
        raise WitnessWithheld(code)


def _closed(value: object, names: frozenset, code: str) -> dict:
    _require(type(value) is dict and set(value) == names, code)
    return value


def _hex(value: object) -> bool:
    return type(value) is str and HEX.fullmatch(value) is not None


def _ident(value: object) -> bool:
    return type(value) is str and IDENT.fullmatch(value) is not None


def _uint(value: object, floor: int = 0) -> bool:
    return type(value) is int and value >= floor


def _utc(value: object) -> datetime:
    _require(type(value) is str and CLOCK.fullmatch(value) is not None,
             "witness_timestamp_invalid")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise WitnessWithheld("witness_timestamp_invalid") from None


def _canonical(value: object) -> bytes:
    try:
        data = json.dumps(value, sort_keys=True, separators=(",", ":"),
                          allow_nan=False, ensure_ascii=True).encode("ascii")
    except (TypeError, ValueError, UnicodeError, OverflowError, RecursionError):
        raise WitnessWithheld("witness_canonical_encoding_invalid") from None
    _require(len(data) <= 32768, "witness_payload_too_large")
    return data


def _digest(domain: bytes, value: object) -> str:
    return sha256(domain + _canonical(value)).hexdigest()


def event_digest(entry: dict) -> str:
    return _digest(DOMAIN_EVENT, {k: v for k, v in entry.items() if k != "event_sha256"})


def log_digest(log: list) -> str:
    return _digest(DOMAIN_LOG, log)


def checkpoint_digest(cp: dict) -> str:
    return _digest(DOMAIN_CHECKPOINT, cp)


def anchor_digest(anchor: "WitnessObserverPin") -> str:
    return _digest(DOMAIN_ANCHOR, {
        "epoch": anchor.epoch, "log_length": anchor.log_length,
        "log_sha256": anchor.log_sha256, "log_tip_sha256": anchor.log_tip_sha256,
        "checkpoint_sha256": anchor.checkpoint_sha256,
        "revocation_sequence": anchor.revocation_sequence,
        "revocation_sha256": anchor.revocation_sha256,
        "registry_sha256": anchor.registry_sha256,
    })


@dataclass(frozen=True)
class WitnessObserverPin:
    """Separate observer's *asserted* external state; not authenticated here."""
    observer_id: str
    epoch: int
    log_length: int
    log_sha256: str
    log_tip_sha256: str
    checkpoint_sha256: str
    revocation_sequence: int
    revocation_sha256: str
    registry_sha256: str


@dataclass(frozen=True)
class WitnessTrust:
    """Independently pinned *synthetic* public keys; hostile parameters are not trust."""
    public_keys: Mapping[str, bytes]
    expected_host_ids: frozenset[str]
    observer_ids: frozenset[str]
    quorum: int = 3
    fixture_kind: str = "synthetic"
    audience: str = AUDIENCE


def _trust(trust: object, source_trust: SyntheticTrustAnchors) -> None:
    _require(isinstance(trust, WitnessTrust) and trust.fixture_kind == "synthetic"
             and trust.audience == AUDIENCE and trust.quorum == 3
             and type(trust.expected_host_ids) is frozenset
             and type(trust.observer_ids) is frozenset
             and len(trust.expected_host_ids) == 4 and len(trust.observer_ids) == 2
             and trust.observer_ids.isdisjoint(trust.expected_host_ids)
             and all(_ident(x) for x in trust.expected_host_ids | trust.observer_ids)
             and isinstance(trust.public_keys, Mapping)
             and set(trust.public_keys) == trust.expected_host_ids
             and all(type(k) is bytes and len(k) == 32 for k in trust.public_keys.values())
             and len(set(trust.public_keys.values())) == 4
             and isinstance(source_trust, SyntheticTrustAnchors),
             "independent_witness_trust_missing")
    source_keys = set(source_trust.custodian_keys.values()) | set(source_trust.revocation_keys.values())
    _require(set(trust.public_keys.values()).isdisjoint(source_keys),
             "witness_role_key_collision")


def _observer_pins(pins: object, trust: WitnessTrust) -> WitnessObserverPin:
    _require(type(pins) in (list, tuple) and len(pins) == 2
             and all(isinstance(p, WitnessObserverPin) for p in pins),
             "observer_pins_missing")
    ids = {p.observer_id for p in pins}
    _require(ids == trust.observer_ids, "observer_identity_mismatch")
    for p in pins:
        _require(_uint(p.epoch, 0) and _uint(p.log_length, 2)
                 and _uint(p.revocation_sequence, 2)
                 and all(_hex(value) for value in (
                     p.log_sha256, p.log_tip_sha256, p.checkpoint_sha256,
                     p.revocation_sha256, p.registry_sha256)),
                 "observer_pin_invalid")
    fields = ("epoch", "log_length", "log_sha256", "log_tip_sha256",
              "checkpoint_sha256", "revocation_sequence", "revocation_sha256",
              "registry_sha256")
    _require(all(getattr(pins[0], k) == getattr(pins[1], k) for k in fields),
             "observer_checkpoint_fork_detected")
    return pins[0]


def _log_validate(entries: object, expected_registry: str, current_revocation: str,
                  now: datetime) -> list:
    _require(type(entries) is list and 2 <= len(entries) <= 32,
             "witness_log_length_invalid")
    prev = ZERO
    ids = set()
    last_time = None
    for i, e in enumerate(entries, 1):
        _closed(e, EVENT_FIELDS, "witness_log_event_shape_invalid")
        _require(e["schema"] == LOG_SCHEMA and _uint(e["index"], 1)
                 and e["index"] == i and _ident(e["event_id"])
                 and e["event_id"] not in ids and
                 e["kind"] in ("registry_checked", "revocation_checkpoint",
                               "key_rotation", "audit_observed")
                 and e["registry_sha256"] == expected_registry
                 and _hex(e["revocation_sha256"])
                 and e["previous_sha256"] == prev and _hex(e["event_sha256"])
                 and e["event_sha256"] == event_digest(e),
                 "witness_log_integrity_invalid")
        event_time = _utc(e["occurred_at"])
        _require(event_time <= now and (last_time is None or last_time <= event_time),
                 "witness_log_timestamp_invalid")
        ids.add(e["event_id"])
        prev, last_time = e["event_sha256"], event_time
    _require(entries[-1]["revocation_sha256"] == current_revocation,
             "witness_revocation_log_tip_mismatch")
    return entries


def _attestation(sig: object, trust: WitnessTrust) -> tuple[dict, str]:
    v = _closed(sig, SIGN_FIELDS, "witness_attestation_not_closed")
    _require(v["schema"] == ATTESTATION_SCHEMA and _ident(v["key_id"])
             and v["key_id"] in trust.public_keys,
             "witness_untrusted_host")
    payload = _closed(v["payload"], CP_FIELDS, "witness_checkpoint_not_closed")
    _require(payload["schema"] == CHECKPOINT_SCHEMA
             and payload["fixture_kind"] == "synthetic"
             and payload["audience"] == AUDIENCE
             and payload["permission"] == "no_source_access_or_release",
             "witness_checkpoint_scope_invalid")
    signature = v["signature_b64"]
    _require(type(signature) is str and len(signature) == 88,
             "witness_signature_encoding_invalid")
    try:
        raw = base64.b64decode(signature.encode("ascii"), validate=True)
        _require(len(raw) == 64 and base64.b64encode(raw).decode("ascii") == signature,
                 "witness_signature_encoding_invalid")
        data = DOMAIN_ATTEST + _canonical({"key_id": v["key_id"], "payload": payload})
        Ed25519PublicKey.from_public_bytes(trust.public_keys[v["key_id"]]).verify(raw, data)
    except (ValueError, TypeError, InvalidSignature, UnicodeError, binascii.Error):
        raise WitnessWithheld("witness_signature_invalid") from None
    return payload, v["key_id"]


def _withheld(code: str) -> dict:
    return {
        "schema": RECEIPT_SCHEMA, "fixture_kind": "synthetic", "status": "withheld",
        "reason_codes": [code], "epoch": None, "log_length": None,
        "quorum_size": 0, "checkpoint_sha256": None, "authority": "none",
        "authorized": False, "can_read_source": False, "can_issue_review": False,
        "statistical_eligible": False, "publication_eligible": False,
        "delivery_eligible": False, "source_text_included": False,
        "source_rows_exported": False,
        "gate_status": {k: "NOT_RUN" for k in REQUIRED_GATES},
        "holdout_lock": dict(LOCK),
    }


def _success(cp: dict, count: int) -> dict:
    x = _withheld("synthetic_witness_only")
    x.update(status="synthetic_quorum_consistent_no_authority", reason_codes=[],
             epoch=cp["epoch"], log_length=cp["log_length"],
             quorum_size=count, checkpoint_sha256=checkpoint_digest(cp))
    return x


def assert_no_authority(value: object) -> None:
    _closed(value, RECEIPT_FIELDS, "witness_receipt_not_closed")
    _require(value["schema"] == RECEIPT_SCHEMA and value["fixture_kind"] == "synthetic"
             and value["status"] in ("withheld", "synthetic_quorum_consistent_no_authority")
             and value["authority"] == "none"
             and all(value[k] is False for k in (
                 "authorized", "can_read_source", "can_issue_review", "statistical_eligible",
                 "publication_eligible", "delivery_eligible", "source_text_included",
                 "source_rows_exported"))
             and value["gate_status"] == {k: "NOT_RUN" for k in REQUIRED_GATES}
             and value["holdout_lock"] == LOCK,
             "witness_receipt_authority_violation")
    if value["status"] == "withheld":
        _require(len(value["reason_codes"]) == 1 and value["epoch"] is None
                 and value["log_length"] is None and value["quorum_size"] == 0
                 and value["checkpoint_sha256"] is None,
                 "witness_receipt_withheld_leak")
    else:
        _require(value["reason_codes"] == [] and _uint(value["epoch"], 1)
                 and _uint(value["log_length"], 3)
                 and value["quorum_size"] in (3, 4)
                 and _hex(value["checkpoint_sha256"]),
                 "witness_receipt_success_invalid")


def verify_multi_host(snapshot: object, policy: object, events: object,
                      proposal: object, custody: object, revocation: object,
                      *, checked_at: str, source_trust: SyntheticTrustAnchors,
                      witness_trust: WitnessTrust, observer_pins: object,
                      log_entries: object, checkpoint: object,
                      attestations: object, gossip: object = None) -> dict:
    """Validate synthetic witness quorum + anchored log extension, grant nothing.

    Exactly four independently pinned Ed25519 witness keys, quorum three, two
    independent observer pins agreeing on an old prefix. No reading/saving of
    original sources or generation of real authorization tokens is possible.
    """
    try:
        _trust(witness_trust, source_trust)
        prev = _observer_pins(observer_pins, witness_trust)
        now = _utc(checked_at)
        signed = verify_synthetic_signatures(
            snapshot, policy, events, proposal, custody, revocation,
            checked_at=checked_at, trust=source_trust)
        _require(signed["status"] == "synthetic_signatures_verified_no_authority",
                 "source_revocation_signature_withheld")
        _require(prev.registry_sha256 == source_trust.expected_registry_sha256
                 and prev.revocation_sequence <= revocation["payload"]["sequence"],
                 "observer_source_or_revocation_regression")
        revhash = content_digest(REVOCATION_SCHEMA, revocation["payload"])
        # Never accept a different signed revocation hash at an unchanged
        # sequence even if both signers and a witness quorum are compromised.
        _require(revocation["payload"]["sequence"] != prev.revocation_sequence
                 or revhash == prev.revocation_sha256,
                 "revocation_same_sequence_rewrite")
        entries = _log_validate(log_entries, source_trust.expected_registry_sha256,
                                revhash, now)
        _require(prev.log_length < len(entries)
                 and log_digest(entries[:prev.log_length]) == prev.log_sha256
                 and entries[prev.log_length-1]["event_sha256"] == prev.log_tip_sha256,
                 "witness_log_prefix_fork_or_rollback")
        cp = _closed(checkpoint, CP_FIELDS, "witness_checkpoint_not_closed")
        _require(cp["schema"] == CHECKPOINT_SCHEMA and cp["fixture_kind"] == "synthetic"
                 and cp["permission"] == "no_source_access_or_release"
                 and cp["audience"] == AUDIENCE
                 and cp["registry_id"] == source_trust.expected_registry_id
                 and cp["registry_sha256"] == source_trust.expected_registry_sha256
                 and cp["audit_tip_sha256"] == source_trust.expected_audit_tip_sha256
                 and cp["revocation_sha256"] == revhash
                 and cp["revocation_sequence"] == revocation["payload"]["sequence"]
                 and _uint(cp["epoch"], 1) and cp["epoch"] == prev.epoch + 1
                 and _uint(cp["log_length"], 3) and cp["log_length"] == len(entries)
                 and cp["log_sha256"] == log_digest(entries)
                 and cp["log_tip_sha256"] == entries[-1]["event_sha256"]
                 and cp["previous_checkpoint_sha256"] == prev.checkpoint_sha256,
                 "witness_checkpoint_binding_mismatch")
        signed_at, expires_at = _utc(cp["signed_at"]), _utc(cp["expires_at"])
        _require(_utc(entries[-1]["occurred_at"]) <= signed_at <= now < expires_at
                 and timedelta(0) < expires_at - signed_at <= timedelta(days=1),
                 "witness_checkpoint_time_invalid")
        _require(type(attestations) is list and 3 <= len(attestations) <= 4,
                 "witness_insufficient_quorum")
        signed_ids = set()
        for att in attestations:
            payload, host = _attestation(att, witness_trust)
            _require(host not in signed_ids, "witness_duplicate_host")
            signed_ids.add(host)
            _require(payload == cp, "witness_checkpoint_split_view")
        _require(len(signed_ids) >= witness_trust.quorum,
                 "witness_insufficient_quorum")
        if gossip is not None:
            _require(type(gossip) is list and len(gossip) <= 8,
                     "witness_gossip_invalid")
            for att in gossip:
                payload, host = _attestation(att, witness_trust)
                if payload["registry_id"] == cp["registry_id"] and (
                    payload["epoch"] == cp["epoch"] or
                    payload["previous_checkpoint_sha256"] == cp["previous_checkpoint_sha256"]
                ):
                    _require(payload == cp, "witness_gossip_fork_detected")
        out = _success(cp, len(signed_ids))
    except WitnessWithheld as error:
        out = _withheld(str(error))
    except (TypeError, ValueError, KeyError, AttributeError, IndexError,
            OverflowError, UnicodeError, RecursionError):
        out = _withheld("witness_malformed_or_untrusted_input")
    assert_no_authority(out)
    return out


def propose_observer_pins(checkpoint: dict, observer_ids: tuple[str, str]) -> tuple[WitnessObserverPin, ...]:
    """Generate *untrusted* synthetic pin proposals for independent observers.

    In real systems the observer state must be durably monotonic and authenticated
    independently, not reconstructed from the checkpoint received from the log.
    """
    _closed(checkpoint, CP_FIELDS, "witness_checkpoint_not_closed")
    _require(len(observer_ids) == 2 and len(set(observer_ids)) == 2 and
             all(_ident(x) for x in observer_ids), "observer_identity_invalid")
    return tuple(WitnessObserverPin(
        observer_id=host, epoch=checkpoint["epoch"],
        log_length=checkpoint["log_length"], log_sha256=checkpoint["log_sha256"],
        log_tip_sha256=checkpoint["log_tip_sha256"],
        checkpoint_sha256=checkpoint_digest(checkpoint),
        revocation_sequence=checkpoint["revocation_sequence"],
        revocation_sha256=checkpoint["revocation_sha256"],
        registry_sha256=checkpoint["registry_sha256"],
    ) for host in observer_ids)


def new_log_event(log: list, event_id: str, kind: str, registry_sha256: str,
                  revocation_sha256: str, occurred_at: str) -> dict:
    """Construct only invented test log events; not an operational writer."""
    _require(_ident(event_id) and _hex(registry_sha256) and _hex(revocation_sha256)
             and _utc(occurred_at) and kind in (
                 "registry_checked", "revocation_checkpoint", "key_rotation", "audit_observed"),
             "witness_event_invalid")
    entry = {"schema": LOG_SCHEMA, "index": len(log)+1, "event_id": event_id,
             "kind": kind, "registry_sha256": registry_sha256,
             "revocation_sha256": revocation_sha256,
             "occurred_at": occurred_at,
             "previous_sha256": log[-1]["event_sha256"] if log else ZERO}
    entry["event_sha256"] = event_digest(entry)
    return entry
