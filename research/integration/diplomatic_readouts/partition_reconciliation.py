"""Offline *synthetic* partition reconciliation and per-witness non-equivocation.

The signing keys in this simulation are PUBLICLY RECONSTRUCTIBLE TEST KEYS.
Neither a witnessed quorum nor an equivocation proof grants source, review,
statistical, holdout, delivery, or publication authority. No network operations.

Trust boundaries: callers must authenticate separately the two observer pins,
per-witness durable state pins, public-key enrollment and secure clock. The
module checks that those *supplied* values are consistent; it cannot establish
their real provenance or protect against compromise of all external anchors.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Mapping
import base64
import binascii
import json
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

STATE_SCHEMA = "un.synthetic-witness-signer-state.v0"
VOTE_SCHEMA = "un.synthetic-witness-partition-vote.v0"
GOSSIP_SCHEMA = "un.synthetic-witness-gossip-state.v0"
RECEIPT_SCHEMA = "un.synthetic-partition-reconciliation.v0"
CHECKPOINT_SCHEMA = "un.synthetic-witness-checkpoint.v0"
EVENT_SCHEMA = "un.synthetic-witness-log.v0"
AUDIENCE = "synthetic:unga81-multi-host-revocation"
NO_PERMISSION = "no_source_access_or_release"
DOMAIN_CHECKPOINT = b"UNGA81/SYNTHETIC/WITNESS/CHECKPOINT/V0\x00"
DOMAIN_LOG = b"UNGA81/SYNTHETIC/WITNESS/LOG/V0\x00"
DOMAIN_EVENT = b"UNGA81/SYNTHETIC/WITNESS/EVENT/V0\x00"
DOMAIN_VOTE = b"UNGA81/SYNTHETIC/WITNESS/NON-EQUIVOCATION/V0\x00"
DOMAIN_STATE = b"UNGA81/SYNTHETIC/WITNESS/SIGNER-STATE/V0\x00"
DOMAIN_GOSSIP = b"UNGA81/SYNTHETIC/WITNESS/GOSSIP-STATE/V0\x00"
DOMAIN_PROOF = b"UNGA81/SYNTHETIC/WITNESS/EQUIVOCATION-PROOF/V0\x00"
ZERO = "0" * 64
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
IDENT = re.compile(r"synthetic:[a-zA-Z0-9][a-zA-Z0-9.:-]{0,100}\Z")
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
# Exactly 13 gates from the frozen source-authority contract. Do not change.
GATES = (
    "source_registry", "original_bytes", "text_transform", "original_offsets",
    "selection_and_duplicates", "source_dependence", "country_attribution",
    "proposition_stance", "owner_review", "privacy", "statistical_identification",
    "reserved_holdout", "d1_publication",
)
LOCK = {"reserved_meetings": 37, "transcripts_opened": 0,
        "access_granted": False, "d1_o1_o5": "frozen"}
CP_FIELDS = frozenset((
    "schema", "fixture_kind", "registry_id", "registry_sha256", "audit_tip_sha256",
    "revocation_sha256", "revocation_sequence", "epoch", "log_length", "log_sha256",
    "log_tip_sha256", "previous_checkpoint_sha256", "audience", "signed_at",
    "expires_at", "permission",
))
EVENT_FIELDS = frozenset((
    "schema", "index", "event_id", "kind", "registry_sha256",
    "revocation_sha256", "occurred_at", "previous_sha256", "event_sha256",
))
VOTE_FIELDS = frozenset(("schema", "key_id", "payload", "signature_b64"))
PAYLOAD_FIELDS = frozenset((
    "schema", "fixture_kind", "witness_id", "epoch", "checkpoint_sha256",
    "previous_checkpoint_sha256", "registry_sha256", "revocation_sha256",
    "revocation_sequence", "log_sha256", "log_length", "audience", "permission",
))
STATE_FIELDS = frozenset((
    "schema", "witness_id", "epoch", "checkpoint_sha256", "registry_sha256",
    "revocation_sha256", "revocation_sequence", "log_sha256", "log_tip_sha256",
    "log_length", "signed_vote_sha256",
))
GOSSIP_FIELDS = frozenset((
    "schema", "parent_epoch", "parent_checkpoint_sha256", "votes", "equivocations",
))
RECEIPT_FIELDS = frozenset((
    "schema", "status", "reason_codes", "epoch", "signed_hosts", "quorum",
    "fork_evidence_sha256", "authority", "authorized", "can_read_source",
    "can_issue_review", "statistical_eligible", "publication_eligible",
    "delivery_eligible", "holdout_lock", "gate_status", "source_text_included",
    "source_rows_exported",
))

class SyntheticRefusal(ValueError):
    """Fixed non-sensitive reason code; no private source input is supported."""


def _need(ok: bool, reason: str) -> None:
    if not ok:
        raise SyntheticRefusal(reason)


def _shape(x, keys, reason):
    _need(type(x) is dict and set(x) == keys, reason)
    return x


def _hash(x):
    return type(x) is str and HEX64.fullmatch(x) is not None


def _ident(x):
    return type(x) is str and IDENT.fullmatch(x) is not None


def _integer(x, minimum=0):
    return type(x) is int and x >= minimum


def _utc(x):
    _need(type(x) is str and TIMESTAMP.fullmatch(x) is not None, "timestamp_invalid")
    try:
        return datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise SyntheticRefusal("timestamp_invalid") from None


def _canon(value):
    try:
        raw = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False).encode("ascii")
    except (TypeError, ValueError, RecursionError, OverflowError, UnicodeError):
        raise SyntheticRefusal("canonical_json_invalid") from None
    _need(len(raw) <= 65536, "metadata_size_limit")
    return raw


def _digest(domain, value):
    return sha256(domain + _canon(value)).hexdigest()


def checkpoint_digest(cp):
    return _digest(DOMAIN_CHECKPOINT, cp)


def _log_digest(entries):
    return _digest(DOMAIN_LOG, entries)


def _event_digest(e):
    return _digest(DOMAIN_EVENT, {k: v for k, v in e.items() if k != "event_sha256"})


def _validate_log(entries, cp):
    _need(type(entries) is list and 3 <= len(entries) <= 32, "log_length_invalid")
    previous, prior_time, ids = ZERO, None, set()
    for n, e in enumerate(entries, 1):
        _shape(e, EVENT_FIELDS, "log_event_not_closed")
        _need(e["schema"] == EVENT_SCHEMA and e["index"] == n and _integer(e["index"], 1)
              and _ident(e["event_id"]) and e["event_id"] not in ids
              and e["kind"] in ("registry_checked", "revocation_checkpoint", "key_rotation", "audit_observed")
              and e["registry_sha256"] == cp["registry_sha256"]
              and _hash(e["revocation_sha256"]) and e["previous_sha256"] == previous
              and e["event_sha256"] == _event_digest(e), "log_integrity_invalid")
        when = _utc(e["occurred_at"])
        _need(prior_time is None or when >= prior_time, "log_time_rollback")
        previous, prior_time = e["event_sha256"], when
        ids.add(e["event_id"])
    _need(cp["log_length"] == len(entries) and cp["log_sha256"] == _log_digest(entries)
          and cp["log_tip_sha256"] == entries[-1]["event_sha256"]
          and entries[-1]["revocation_sha256"] == cp["revocation_sha256"],
          "log_checkpoint_mismatch")


def _validate_cp(cp):
    _shape(cp, CP_FIELDS, "checkpoint_not_closed")
    _need(cp["schema"] == CHECKPOINT_SCHEMA and cp["fixture_kind"] == "synthetic"
          and cp["audience"] == AUDIENCE and cp["permission"] == NO_PERMISSION,
          "checkpoint_non_synthetic_or_permission")
    _need(_ident(cp["registry_id"]) and all(_hash(cp[k]) for k in (
        "registry_sha256", "audit_tip_sha256", "revocation_sha256", "log_sha256",
        "log_tip_sha256", "previous_checkpoint_sha256"))
          and _integer(cp["epoch"]) and _integer(cp["revocation_sequence"], 2)
          and _integer(cp["log_length"], 2), "checkpoint_identity_invalid")
    _need(_utc(cp["signed_at"]) < _utc(cp["expires_at"]), "checkpoint_clock_invalid")
    return cp


@dataclass(frozen=True)
class ObserverPin:
    """Externally supplied trusted context; no authenticity implied by class type."""
    observer_id: str
    snapshot_sha256: str
    epoch: int
    checkpoint_sha256: str


@dataclass(frozen=True)
class GossipPin:
    """Externally retained gossip high-water; not issued by this module."""
    observer_id: str
    snapshot_sha256: str
    parent_epoch: int
    parent_checkpoint_sha256: str


@dataclass(frozen=True)
class Keyring:
    keys: Mapping[str, bytes]
    expected_ids: frozenset[str]
    observers: frozenset[str]
    quorum: int = 3


def _keyring(trust):
    _need(isinstance(trust, Keyring) and trust.quorum == 3
          and type(trust.expected_ids) is frozenset and len(trust.expected_ids) == 4
          and type(trust.observers) is frozenset and len(trust.observers) == 2
          and trust.expected_ids.isdisjoint(trust.observers)
          and all(_ident(x) for x in trust.expected_ids | trust.observers)
          and isinstance(trust.keys, Mapping)
          and set(trust.keys) == trust.expected_ids
          and all(type(x) is bytes and len(x) == 32 for x in trust.keys.values())
          and len(set(trust.keys.values())) == 4, "witness_trust_invalid")


def new_signer_state(host_id: str, cp0: dict):
    _validate_cp(cp0)
    _need(_ident(host_id) and cp0["epoch"] == 0, "signer_genesis_invalid")
    return {"schema": STATE_SCHEMA, "witness_id": host_id,
            "epoch": 0, "checkpoint_sha256": checkpoint_digest(cp0),
            "registry_sha256": cp0["registry_sha256"],
            "revocation_sha256": cp0["revocation_sha256"],
            "revocation_sequence": cp0["revocation_sequence"],
            "log_sha256": cp0["log_sha256"], "log_tip_sha256": cp0["log_tip_sha256"],
            "log_length": cp0["log_length"], "signed_vote_sha256": None}


def _signer_state(state):
    _shape(state, STATE_FIELDS, "signer_state_not_closed")
    _need(state["schema"] == STATE_SCHEMA and _ident(state["witness_id"])
          and _integer(state["epoch"]) and _integer(state["revocation_sequence"], 2)
          and _integer(state["log_length"], 2)
          and all(_hash(state[k]) for k in (
              "checkpoint_sha256", "registry_sha256", "revocation_sha256",
              "log_sha256", "log_tip_sha256"))
          and (state["signed_vote_sha256"] is None or _hash(state["signed_vote_sha256"])),
          "signer_state_invalid")
    return state


def signer_state_digest(state):
    _signer_state(state)
    return _digest(DOMAIN_STATE, state)


def propose_signer_pins(state, observer_ids):
    """Only creates UNTRUSTED synthetic proposals; callers must pin externally."""
    _signer_state(state)
    _need(type(observer_ids) in (tuple, list) and len(observer_ids) == 2
          and len(set(observer_ids)) == 2 and all(_ident(x) for x in observer_ids),
          "observer_identity_invalid")
    return tuple(ObserverPin(x, signer_state_digest(state), state["epoch"],
                             state["checkpoint_sha256"]) for x in observer_ids)


def _check_signer_pins(state, pins, trust):
    _need(type(pins) in (tuple, list) and len(pins) == 2
          and all(isinstance(p, ObserverPin) for p in pins)
          and {p.observer_id for p in pins} == trust.observers,
          "signer_observer_pins_missing")
    d = signer_state_digest(state)
    _need(all(p.snapshot_sha256 == d and p.epoch == state["epoch"]
              and p.checkpoint_sha256 == state["checkpoint_sha256"] for p in pins),
          "signer_rollback_or_fork_detected")


def _vote_payload(cp, witness_id):
    return {"schema": VOTE_SCHEMA, "fixture_kind": "synthetic",
            "witness_id": witness_id, "epoch": cp["epoch"],
            "checkpoint_sha256": checkpoint_digest(cp),
            "previous_checkpoint_sha256": cp["previous_checkpoint_sha256"],
            "registry_sha256": cp["registry_sha256"],
            "revocation_sha256": cp["revocation_sha256"],
            "revocation_sequence": cp["revocation_sequence"],
            "log_sha256": cp["log_sha256"], "log_length": cp["log_length"],
            "audience": AUDIENCE, "permission": NO_PERMISSION}


def signer_vote(state, pins, cp, entries, key, trust):
    """Simulate one honest synthetic witness signing a strictly advanced epoch.

    The returned state is a NEW value, not persistent storage. A host must first
    bind it to *independent* durable observer pins before accepting any next vote.
    """
    _keyring(trust)
    _signer_state(state)
    _check_signer_pins(state, pins, trust)
    _validate_cp(cp)
    host_id = state["witness_id"]
    _need(host_id in trust.expected_ids, "untrusted_witness")
    _need(isinstance(key, Ed25519PrivateKey), "test_signer_key_invalid")
    public_bytes = key.public_key().public_bytes(serialization.Encoding.Raw,
                                                  serialization.PublicFormat.Raw)
    _need(public_bytes == trust.keys[host_id], "test_signer_key_untrusted")
    _need(cp["registry_sha256"] == state["registry_sha256"]
          and cp["epoch"] == state["epoch"] + 1
          and cp["previous_checkpoint_sha256"] == state["checkpoint_sha256"]
          and cp["revocation_sequence"] >= state["revocation_sequence"]
          and (cp["revocation_sequence"] != state["revocation_sequence"]
               or cp["revocation_sha256"] == state["revocation_sha256"]),
          "signer_non_equivocation_or_revocation_rollback")
    _validate_log(entries, cp)
    _need(state["log_length"] < len(entries)
          and _log_digest(entries[:state["log_length"]]) == state["log_sha256"]
          and entries[state["log_length"] - 1]["event_sha256"] == state["log_tip_sha256"],
          "signer_log_prefix_fork_or_rollback")
    payload = _vote_payload(cp, host_id)
    signature = key.sign(DOMAIN_VOTE + _canon({"key_id": host_id, "payload": payload}))
    vote = {"schema": VOTE_SCHEMA, "key_id": host_id, "payload": payload,
            "signature_b64": base64.b64encode(signature).decode("ascii")}
    state2 = dict(state, epoch=cp["epoch"], checkpoint_sha256=checkpoint_digest(cp),
                  revocation_sha256=cp["revocation_sha256"],
                  revocation_sequence=cp["revocation_sequence"],
                  log_sha256=cp["log_sha256"], log_tip_sha256=cp["log_tip_sha256"],
                  log_length=cp["log_length"], signed_vote_sha256=vote_digest(vote))
    return vote, state2


def _validated_vote(vote, trust):
    _shape(vote, VOTE_FIELDS, "gossip_vote_not_closed")
    _need(vote["schema"] == VOTE_SCHEMA and _ident(vote["key_id"])
          and vote["key_id"] in trust.expected_ids, "gossip_witness_not_trusted")
    payload = _shape(vote["payload"], PAYLOAD_FIELDS, "gossip_vote_payload_not_closed")
    _need(payload["schema"] == VOTE_SCHEMA and payload["fixture_kind"] == "synthetic"
          and payload["witness_id"] == vote["key_id"]
          and payload["audience"] == AUDIENCE and payload["permission"] == NO_PERMISSION
          and all(_hash(payload[k]) for k in (
              "checkpoint_sha256", "previous_checkpoint_sha256", "registry_sha256",
              "revocation_sha256", "log_sha256"))
          and _integer(payload["epoch"], 1)
          and _integer(payload["revocation_sequence"], 2)
          and _integer(payload["log_length"], 3),
          "gossip_vote_scope_invalid")
    text = vote["signature_b64"]
    _need(type(text) is str and len(text) == 88, "gossip_signature_encoding_invalid")
    try:
        binary = base64.b64decode(text.encode("ascii"), validate=True)
        _need(len(binary) == 64 and base64.b64encode(binary).decode("ascii") == text,
              "gossip_signature_encoding_invalid")
        Ed25519PublicKey.from_public_bytes(trust.keys[vote["key_id"]]).verify(
            binary, DOMAIN_VOTE + _canon({"key_id": vote["key_id"], "payload": payload}))
    except (binascii.Error, UnicodeError, InvalidSignature, TypeError, ValueError):
        raise SyntheticRefusal("gossip_signature_invalid") from None
    return payload


def vote_digest(vote):
    _shape(vote, VOTE_FIELDS, "gossip_vote_not_closed")
    return _digest(DOMAIN_VOTE, vote)


def new_gossip_state(parent_epoch, parent_checkpoint_sha256):
    _need(_integer(parent_epoch) and _hash(parent_checkpoint_sha256), "gossip_parent_invalid")
    return {"schema": GOSSIP_SCHEMA, "parent_epoch": parent_epoch,
            "parent_checkpoint_sha256": parent_checkpoint_sha256,
            "votes": [], "equivocations": []}


def _validate_gossip_state(state, trust):
    _shape(state, GOSSIP_FIELDS, "gossip_state_not_closed")
    _need(state["schema"] == GOSSIP_SCHEMA and _integer(state["parent_epoch"])
          and _hash(state["parent_checkpoint_sha256"])
          and type(state["votes"]) is list and len(state["votes"]) <= 32
          and type(state["equivocations"]) is list and len(state["equivocations"]) <= 16
          and all(_hash(d) for d in state["equivocations"]), "gossip_state_invalid")
    ids = set()
    for vote in state["votes"]:
        payload = _validated_vote(vote, trust)
        _need(payload["epoch"] == state["parent_epoch"] + 1
              and payload["previous_checkpoint_sha256"] == state["parent_checkpoint_sha256"],
              "gossip_parent_mismatch")
        h = vote_digest(vote)
        _need(h not in ids, "gossip_duplicate_state_vote")
        ids.add(h)
    # Equivocation proofs must be recoverable from the retained, verified
    # signed messages, not merely from a self-asserted list of hash strings.
    groups = {}
    for vote in state["votes"]:
        groups.setdefault((vote["key_id"], vote["payload"]["epoch"]), []).append(vote)
    expected = set()
    for messages in groups.values():
        for i, a in enumerate(messages):
            for b in messages[i+1:]:
                if a["payload"]["checkpoint_sha256"] != b["payload"]["checkpoint_sha256"]:
                    expected.add(_proof(a, b))
    _need(state["equivocations"] == sorted(expected),
          "gossip_fork_evidence_incomplete_or_fabricated")
    return state


def gossip_state_digest(state, trust):
    _keyring(trust)
    _validate_gossip_state(state, trust)
    return _digest(DOMAIN_GOSSIP, state)


def propose_gossip_pins(state, trust):
    """Creates only UNTRUSTED proposals for two independently durable observers."""
    _validate_gossip_state(state, trust)
    return tuple(GossipPin(o, gossip_state_digest(state, trust),
                           state["parent_epoch"], state["parent_checkpoint_sha256"])
                 for o in sorted(trust.observers))


def _receipt(status, reason_codes=(), *, epoch=None, hosts=0, proof_hash=None):
    receipt = {"schema": RECEIPT_SCHEMA, "status": status,
               "reason_codes": list(reason_codes), "epoch": epoch,
               "signed_hosts": hosts, "quorum": 3, "fork_evidence_sha256": proof_hash,
               "authority": "none", "authorized": False, "can_read_source": False,
               "can_issue_review": False, "statistical_eligible": False,
               "publication_eligible": False, "delivery_eligible": False,
               "holdout_lock": dict(LOCK), "gate_status": {g: "NOT_RUN" for g in GATES},
               "source_text_included": False, "source_rows_exported": False}
    return receipt


def assert_no_authority(receipt):
    _shape(receipt, RECEIPT_FIELDS, "gossip_receipt_not_closed")
    _need(receipt["schema"] == RECEIPT_SCHEMA and receipt["status"] in (
        "withheld", "pending_gossip", "quorum_observed_no_authority")
          and receipt["authority"] == "none"
          and all(receipt[k] is False for k in (
              "authorized", "can_read_source", "can_issue_review", "statistical_eligible",
              "publication_eligible", "delivery_eligible", "source_text_included",
              "source_rows_exported")) and receipt["holdout_lock"] == LOCK
          and receipt["gate_status"] == {g: "NOT_RUN" for g in GATES}
          and receipt["quorum"] == 3
          and type(receipt["reason_codes"]) is list
          and all(type(x) is str and re.fullmatch(r"[a-z0-9_]{3,80}", x) for x in receipt["reason_codes"]),
          "gossip_receipt_authority_violation")
    if receipt["status"] == "withheld":
        _need(receipt["reason_codes"] and receipt["signed_hosts"] == 0
              and receipt["epoch"] is None, "gossip_withheld_leaks")
    else:
        _need(receipt["reason_codes"] == [] and _integer(receipt["signed_hosts"])
              and _integer(receipt["epoch"], 1), "gossip_receipt_invalid")
    if receipt["fork_evidence_sha256"] is not None:
        _need(_hash(receipt["fork_evidence_sha256"]), "gossip_fork_digest_invalid")
    return None


def _proof(v1, v2):
    a, b = sorted((vote_digest(v1), vote_digest(v2)))
    return _digest(DOMAIN_PROOF, {"signed_votes": [a, b]})


def reconcile_gossip(state, pins, delivered_votes, trust):
    """Reconcile a single synthetic epoch. Never treat quorum as authorization.

    If any authenticated witness signs conflicting checkpoints for the same
    epoch, permanently retain an evidence hash in the returned synthetic state.
    Honest restarts must verify two independently held state pins; constructing
    pins from attacker-restored state destroys this guarantee.
    """
    try:
        _keyring(trust)
        _validate_gossip_state(state, trust)
        _need(type(pins) in (tuple, list) and len(pins) == 2
              and all(isinstance(p, GossipPin) for p in pins)
              and {p.observer_id for p in pins} == trust.observers,
              "gossip_observer_pins_missing")
        current = gossip_state_digest(state, trust)
        _need(all(p.snapshot_sha256 == current
                  and p.parent_epoch == state["parent_epoch"]
                  and p.parent_checkpoint_sha256 == state["parent_checkpoint_sha256"]
                  for p in pins), "gossip_state_rollback_or_fork")
        _need(type(delivered_votes) is list and len(delivered_votes) <= 32,
              "gossip_delivery_invalid")
        merged = {vote_digest(v): v for v in state["votes"]}
        for v in delivered_votes:
            payload = _validated_vote(v, trust)
            _need(payload["epoch"] == state["parent_epoch"] + 1
                  and payload["previous_checkpoint_sha256"] == state["parent_checkpoint_sha256"],
                  "gossip_wrong_parent_or_epoch")
            merged[vote_digest(v)] = v
        _need(len(merged) <= 32, "gossip_delivery_limit")
        ordered = [merged[k] for k in sorted(merged)]
        pair_by_host = {}
        groups = {}
        proofs = set(state["equivocations"])
        for v in ordered:
            p = v["payload"]
            key = p["witness_id"]
            pair_by_host.setdefault(key, []).append(v)
            groups.setdefault(p["checkpoint_sha256"], set()).add(key)
        for messages in pair_by_host.values():
            for i, a in enumerate(messages):
                for b in messages[i + 1:]:
                    if a["payload"]["checkpoint_sha256"] != b["payload"]["checkpoint_sha256"]:
                        proofs.add(_proof(a, b))
        out = {"schema": GOSSIP_SCHEMA, "parent_epoch": state["parent_epoch"],
               "parent_checkpoint_sha256": state["parent_checkpoint_sha256"],
               "votes": ordered, "equivocations": sorted(proofs)}
        epoch = state["parent_epoch"] + 1
        if proofs:
            receipt = _receipt("withheld", ["witness_equivocation_evidence"],
                               proof_hash=_digest(DOMAIN_PROOF, sorted(proofs)))
        elif len([ids for ids in groups.values() if len(ids) >= 3]) > 1:
            receipt = _receipt("withheld", ["witness_conflicting_quorum"])
        elif any(len(ids) >= 3 for ids in groups.values()):
            receipt = _receipt("quorum_observed_no_authority", epoch=epoch,
                               hosts=max(len(ids) for ids in groups.values()))
        else:
            receipt = _receipt("pending_gossip", epoch=epoch,
                               hosts=max((len(ids) for ids in groups.values()), default=0))
        assert_no_authority(receipt)
        return out, receipt
    except SyntheticRefusal as exc:
        result = _receipt("withheld", [str(exc)])
        assert_no_authority(result)
        return None, result
    except (TypeError, AttributeError, ValueError, KeyError, IndexError,
            UnicodeError, OverflowError, RecursionError):
        result = _receipt("withheld", ["malformed_synthetic_gossip"])
        assert_no_authority(result)
        return None, result
