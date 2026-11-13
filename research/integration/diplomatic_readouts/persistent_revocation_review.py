"""Synthetic-only persisted-revocation rehearsal; not a trust store or authorizer.

The independent observer pin MUST be maintained outside the possibly rolled-back
file and signing authorities. This module deliberately cannot create credentials,
fetch sources, issue approvals, alter upstream gates, or certify a real custodian.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import secrets
from typing import Mapping

from private_source_contract import REQUIRED_GATES
from registry_preflight import LOCK
from synthetic_signatures import (
    SyntheticTrustAnchors, REVOCATION_SCHEMA, content_digest,
    verify_synthetic_signatures,
)

SCHEMA = "un.synthetic-revocation-persistence-review.v0"
RECEIPT_SCHEMA = "un.synthetic-revocation-restart-assessment.v0"
HEX = re.compile(r"^[0-9a-f]{64}$")
IDENT = re.compile(r"^synthetic:[A-Za-z0-9][A-Za-z0-9._:-]{0,100}$")
FIELDS = frozenset((
    "schema", "registry_id", "registry_sha256", "proposal_sha256",
    "policy_sha256", "audit_tip_sha256", "checkpoint_sha256",
    "sequence", "revoked_key_ids", "previous_state_sha256", "checked_at",
    "authority", "authorized", "can_read_source", "publication_eligible",
))

class SyntheticRestartWithheld(ValueError):
    """Fixed, non-sensitive diagnostic only."""


def _require(ok: bool, code: str) -> None:
    if not ok:
        raise SyntheticRestartWithheld(code)


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                          separators=(",", ":")).encode("ascii")
    except (TypeError, ValueError, OverflowError, UnicodeError, RecursionError):
        raise SyntheticRestartWithheld("persistence_state_invalid") from None


def state_digest(value: object) -> str:
    validate_state(value)
    return sha256(b"UNGA81/SYNTHETIC/PERSISTENCE/STATE/V0\0" +
                  _canonical(value)).hexdigest()


def validate_state(value: object) -> None:
    _require(type(value) is dict and set(value) == FIELDS,
             "persistence_state_invalid")
    x = value
    _require(x["schema"] == SCHEMA and x["authority"] == "none" and
             all(x[k] is False for k in ("authorized", "can_read_source",
                                       "publication_eligible")),
             "persistence_cannot_grant_authority")
    _require(type(x["registry_id"]) is str and IDENT.fullmatch(x["registry_id"])
             and all(type(x[k]) is str and HEX.fullmatch(x[k]) for k in (
                 "registry_sha256", "proposal_sha256", "policy_sha256",
                 "audit_tip_sha256", "checkpoint_sha256"))
             and type(x["sequence"]) is int and x["sequence"] >= 2
             and (x["previous_state_sha256"] is None or
                  type(x["previous_state_sha256"]) is str and
                  HEX.fullmatch(x["previous_state_sha256"]))
             and type(x["checked_at"]) is str and
             re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", x["checked_at"]),
             "persistence_state_invalid")
    ids = x["revoked_key_ids"]
    _require(type(ids) is list and len(ids) <= 32 and
             all(type(k) is str and IDENT.fullmatch(k) for k in ids) and
             ids == sorted(set(ids)), "persistence_revocation_list_invalid")


@dataclass(frozen=True)
class ExternalObserverPin:
    """A separately delivered synthetic witness pin, NOT derived from the file.

    Authentic issuance, monotonic storage and availability are outside scope.
    Caller must never use a value loaded from the file as this pin.
    """
    registry_id: str
    sequence_floor: int
    state_sha256: str
    registry_sha256: str
    checkpoint_sha256: str
    observer_ref: str = "synthetic:offline-independent-observer"


def _pin_ok(pin: object) -> bool:
    return (isinstance(pin, ExternalObserverPin)
            and type(pin.observer_ref) is str and IDENT.fullmatch(pin.observer_ref)
            and type(pin.registry_id) is str and IDENT.fullmatch(pin.registry_id)
            and type(pin.sequence_floor) is int and pin.sequence_floor >= 2
            and all(type(v) is str and HEX.fullmatch(v) for v in (
                pin.state_sha256, pin.registry_sha256, pin.checkpoint_sha256)))


def proposed_pin_from_state(state: dict) -> ExternalObserverPin:
    """Return a proposed pin for independent *simulation*; not a trusted grant."""
    validate_state(state)
    return ExternalObserverPin(
        state["registry_id"], state["sequence"], state_digest(state),
        state["registry_sha256"], state["checkpoint_sha256"],
    )


def make_verified_state(snapshot: object, policy: object, events: object,
                        proposal: object, custody: object, revocation: object,
                        *, checked_at: str, trust: SyntheticTrustAnchors,
                        previous: ExternalObserverPin | None = None) -> dict:
    """Only a valid synthetic signature result may become a state *proposal*."""
    result = verify_synthetic_signatures(
        snapshot, policy, events, proposal, custody, revocation,
        checked_at=checked_at, trust=trust)
    _require(result["status"] == "synthetic_signatures_verified_no_authority",
             "persistence_requires_verified_synthetic_checkpoint")
    signed = revocation["payload"]
    _require(signed["schema"] == REVOCATION_SCHEMA and
             content_digest(REVOCATION_SCHEMA, signed) ==
             trust.expected_checkpoint_sha256,
             "persistence_checkpoint_invalid")
    state = {
        "schema": SCHEMA, "registry_id": trust.expected_registry_id,
        "registry_sha256": trust.expected_registry_sha256,
        "proposal_sha256": trust.expected_proposal_sha256,
        "policy_sha256": trust.expected_policy_sha256,
        "audit_tip_sha256": trust.expected_audit_tip_sha256,
        "checkpoint_sha256": trust.expected_checkpoint_sha256,
        "sequence": signed["sequence"],
        "revoked_key_ids": list(signed["revoked_key_ids"]),
        "previous_state_sha256": None if previous is None else previous.state_sha256,
        "checked_at": checked_at,
        "authority": "none", "authorized": False,
        "can_read_source": False, "publication_eligible": False,
    }
    validate_state(state)
    if previous is not None:
        _require(_pin_ok(previous), "independent_observer_pin_missing")
        _require(state["sequence"] > previous.sequence_floor,
                 "persistence_checkpoint_not_advancing")
        _require(state["registry_id"] == previous.registry_id and
                 state["registry_sha256"] == previous.registry_sha256,
                 "persistence_registry_switch_denied")
    return state


def _safe_directory(path: Path) -> None:
    # This is merely a synthetic atomic write rehearsal. Parent filesystem ACL,
    # symlink races, remote durability and true rollback resistance are NOT proven.
    _require(path.parent.is_dir() and not path.parent.is_symlink(),
             "persistence_directory_untrusted")
    _require(not path.is_symlink(), "persistence_symlink_forbidden")
    _require(path.name.endswith(".synthetic.json"), "persistence_path_invalid")


def read_checked_state(path: str | Path, pin: ExternalObserverPin) -> dict:
    """Fail closed on missing/corrupt/rolled-back local state and any absent pin."""
    _require(_pin_ok(pin), "independent_observer_pin_missing")
    target = Path(path)
    _safe_directory(target)
    _require(target.is_file(), "persistence_state_missing")
    try:
        _require(target.stat().st_size <= 4096, "persistence_state_oversized")
        state = json.loads(target.read_text(encoding="utf-8"))
        validate_state(state)
        _require(state_digest(state) == pin.state_sha256 and
                 state["sequence"] >= pin.sequence_floor and
                 state["registry_id"] == pin.registry_id and
                 state["registry_sha256"] == pin.registry_sha256 and
                 state["checkpoint_sha256"] == pin.checkpoint_sha256,
                 "persisted_checkpoint_rollback_or_fork")
        return state
    except SyntheticRestartWithheld:
        raise
    except (OSError, UnicodeError, ValueError, OverflowError, RecursionError):
        raise SyntheticRestartWithheld("persistence_state_unreadable") from None


def write_state_rehearsal(path: str | Path, state: dict, *,
                          previous_pin: ExternalObserverPin | None = None) -> ExternalObserverPin:
    """Atomic local simulation, NEVER issuance of an independent trust anchor.

    Writes synthetic metadata only. The returned pin MUST be independently
    retained on a different trust plane before future restart verification.
    """
    validate_state(state)
    target = Path(path)
    _safe_directory(target)
    exists = target.exists()
    if previous_pin is None:
        _require(not exists and state["previous_state_sha256"] is None,
                 "persistence_initial_state_exists_or_invalid")
    else:
        prior = read_checked_state(target, previous_pin)
        _require(state["previous_state_sha256"] == previous_pin.state_sha256
                 and state["sequence"] > prior["sequence"]
                 and state["registry_id"] == prior["registry_id"]
                 and state["registry_sha256"] == prior["registry_sha256"],
                 "persistence_nonmonotonic_or_unlinked")
    data = _canonical(state) + b"\n"
    _require(len(data) <= 4096, "persistence_state_oversized")
    temp = target.parent / ("." + target.name + "." + secrets.token_hex(8) + ".tmp")
    try:
        descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                             0o600)
        try:
            with os.fdopen(descriptor, "wb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temp, target)
            # Best-effort crash durability. This is not proof against malicious
            # filesystem actors or rolling back a whole volume snapshot.
            if hasattr(os, "O_DIRECTORY"):
                directory = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
        except BaseException:
            try: os.unlink(temp)
            except OSError: pass
            raise
    except OSError:
        raise SyntheticRestartWithheld("persistence_store_write_failed") from None
    return proposed_pin_from_state(state)


def _receipt(status: str, reason: str | None) -> dict:
    result = {
        "schema": RECEIPT_SCHEMA,
        "status": status,
        "reason_codes": [] if reason is None else [reason],
        "gate_status": {g: "NOT_RUN" for g in REQUIRED_GATES},
        "holdout_lock": dict(LOCK),
        "authority": "none", "authorized": False,
        "can_read_source": False, "can_issue_review": False,
        "statistical_eligible": False, "publication_eligible": False,
        "delivery_eligible": False, "source_text_included": False,
        "source_rows_exported": False,
    }
    return result


def assert_no_authority(result: object) -> None:
    _require(type(result) is dict and set(result) == {
        "schema", "status", "reason_codes", "gate_status", "holdout_lock",
        "authority", "authorized", "can_read_source", "can_issue_review",
        "statistical_eligible", "publication_eligible", "delivery_eligible",
        "source_text_included", "source_rows_exported",
    }, "persistence_receipt_invalid")
    _require(result["schema"] == RECEIPT_SCHEMA
             and result["status"] in ("withheld", "synthetic_checkpoint_consistent_no_authority")
             and result["authority"] == "none"
             and all(result[k] is False for k in (
                "authorized", "can_read_source", "can_issue_review", "statistical_eligible",
                "publication_eligible", "delivery_eligible", "source_text_included",
                "source_rows_exported"))
             and result["holdout_lock"] == LOCK
             and result["gate_status"] == {g: "NOT_RUN" for g in REQUIRED_GATES},
             "persistence_receipt_authority_invalid")
    code = result["reason_codes"]
    _require(type(code) is list and
             all(type(r) is str and re.fullmatch(r"[a-z_]{3,80}", r) for r in code) and
             ((result["status"] == "withheld" and len(code) == 1) or
              (result["status"] == "synthetic_checkpoint_consistent_no_authority"
               and not code)),
             "persistence_receipt_reasons_invalid")


def guarded_restart_verify(path: str | Path, pin: ExternalObserverPin | None,
                           snapshot: object, policy: object, events: object,
                           proposal: object, custody: object, revocation: object,
                           *, checked_at: str, trust: SyntheticTrustAnchors | None) -> dict:
    """Verifier must not trust a stale/rolled-back persisted checkpoint after restart."""
    try:
        state = read_checked_state(path, pin)
        _require(isinstance(trust, SyntheticTrustAnchors),
                 "persistence_verifier_trust_missing")
        _require(trust.expected_registry_id == state["registry_id"] and
                 trust.expected_registry_sha256 == state["registry_sha256"] and
                 trust.expected_proposal_sha256 == state["proposal_sha256"] and
                 trust.expected_policy_sha256 == state["policy_sha256"] and
                 trust.expected_audit_tip_sha256 == state["audit_tip_sha256"] and
                 trust.expected_checkpoint_sha256 == state["checkpoint_sha256"] and
                 trust.minimum_checkpoint_sequence >= state["sequence"],
                 "persistence_verifier_pin_mismatch")
        _require(type(revocation) is dict and type(revocation.get("payload")) is dict and
                 revocation["payload"].get("sequence") == state["sequence"] and
                 revocation["payload"].get("revoked_key_ids") == state["revoked_key_ids"],
                 "persistence_checkpoint_substitution")
        checked = verify_synthetic_signatures(
            snapshot, policy, events, proposal, custody, revocation,
            checked_at=checked_at, trust=trust)
        _require(checked["status"] == "synthetic_signatures_verified_no_authority",
                 "persistence_signed_checkpoint_withheld")
        answer = _receipt("synthetic_checkpoint_consistent_no_authority", None)
    except SyntheticRestartWithheld as error:
        answer = _receipt("withheld", str(error))
    except (OSError, TypeError, KeyError, ValueError, AttributeError, IndexError,
            UnicodeError, OverflowError, RecursionError):
        answer = _receipt("withheld", "persistence_malformed_or_untrusted_input")
    assert_no_authority(answer)
    return answer
