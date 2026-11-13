# Metadata-only private-source registry preflight — prospective v0

**Status: synthetic-only, non-authorizing engineering preflight.** This implementation neither reads real/private/original UN source bytes nor confirms an actual custodian identity. It issues no grants, reviewer decisions, scientific approvals, or D1 O1–O5 release approvals. All 37 reserved October 5–6 meetings remain sealed. **`metadata_consistent` means only internal consistency of invented metadata, never permission to retrieve, use, publish, or release source text.**

## Private-host architecture (future, not implemented)

```text
Private acquisition registry + independently established custody issuer
                 |
                 v
Original provenance/rights verification (not in this code)
                 |
                 v
Metadata snapshot -- immutable digest -- prospective custody intent
                 |                    |                 |
                 +--- chained audit ---+--- revocation check --- expiry check
                                      |
                     synthetic-only consistency preflight
                                      |
                          NON-AUTHORIZING receipt
                            all 13 gates NOT_RUN
                                      |
                    separately authorized future private-host
                 source, reviewer, privacy and statistical checks
                                      |
                      D1 publication remains a separate authority
```

No issuer key, identity provider, source endpoint, real inventory, credential, original byte content, private annotation, transcript URL, source file path, or row-level output is included here. Each input is a **synthetic** metadata object. The `custodian_ref`, `reviewer_ref`, and `issuer_ref` are fictional labels and may denote the same operator, consistent with the owner's declared single-reviewer pilot; they do not establish human identity or sign-off.

### Snapshot contract (`un.private-source-registry.metadata.v0`)

`registry_preflight.py` requires exactly these fields: `schema`, `fixture_kind=synthetic`, synthetic registry ID and integer revision, nullable previous registry digest, UTC recorded timestamp, existing supported upstream source-schema label, `source_hash_basis=synthetic`, source/selection SHA-256 digest strings, `records`, `population`, and a **locked** holdout status. No URL, text, quote, raw bytes, path, credentials, private document, country or stance field is accepted. All observation identities must begin `synthetic:`.

Each synthetic record contains ID, optional parent/source-family/meeting IDs, event date, availability status, one exclusion or missing-reason code, optional **digest labels** only for available synthetic sources, representation ID and Unicode code-point basis for available records, and `classification=synthetic_only`. Duplicate IDs, invented hashes for unavailable records, malformed dates, and 5–6 October reserved dates are rejected.

Population counts are mandatory and mutually exclusive:

- `observations_total = eligible + excluded + unavailable`;
- `total_in_frame = observations_total + unobserved`;
- `eligible`, `excluded`, and `unavailable` must equal the independently enumerated synthetic record statuses.

An unavailable or unobserved item means **unknown**, not absence of a diplomatic position or issue. Original hash strings here are not checked against original bytes; real verification remains prohibited and `NOT_RUN`.

### Custody intent, expiry, and revocation

The separate synthetic custody intent binds the exact **snapshot digest** and registry ID, fictional custodian/reviewer/issuer references, requested purpose `synthetic_metadata_preflight`, issuance/expiry dates in UTC, a revocation ledger sequence, and `attestation=unverified_metadata_consistency_only`. All requested permissions—source-byte read, reserved read, registry write, review issuance, statistical release, publication and email—must be literally `false`. Unknown fields fail closed.

Audit events have contiguous positive indices, unique synthetic event IDs, explicit actors, UTC timestamps, exact snapshot identity, the previous event digest, and an event digest of canonical JSON. The first event is custodian `registered`, the second is reviewer `metadata_checked`; subsequent events are sequential, and any `revoked` event withholds. The events must match the custody revocation sequence. A gap, altered payload, future timestamp, duplicate event ID, wrong actor, expired intent, or apparent permission escalation is rejected. Digest chaining is **not a tamper-proof, signed or externally authenticated audit log**; rollback of the entire self-attested packet is not detectable. An actual independent revocation feed, signed custody record, monotonic trusted ledger, and issuer verification are prerequisites for any future real authorization.

### Public receipt and authority separation

`preflight(snapshot, policy, events, checked_at=UTC_ISO_STRING, proposal=unapproved_v0_proposal)` accepts only synthetic metadata and returns a **closed**, aggregate-only receipt `un.private-source-registry.preflight-receipt.v0`. Failures return fixed non-sensitive codes and no registry, record, or custodian identifier. The response never contains row-level source details, text, paths, signatures, or credentials. Even a valid consistency result contains no source list, and its `registry_sha256` is a **self-consistency checksum**, not proof of custodian identity.

The receipt permanently sets `authority=none`, `authorized=false`, `can_read_source=false`, `can_issue_review=false`, `statistical_eligible=false`, `publication_eligible=false`, `delivery_eligible=false`, `source_text_included=false`, `source_rows_exported=false`, `reserved_meetings=37`, `transcripts_opened=0`, `access_granted=false`, `d1_o1_o5=frozen`. **All 13** existing private/reviewer/statistical/holdout/D1 statuses are `NOT_RUN`. `assert_no_authority()` separately rechecks closed output invariants and refuses attempted privilege escalation. An **existing** `un.private-source-authorization.proposal.v0` must be provided separately. Its closed `assert_design_only` contract is revalidated; source schema/hash basis, source/selection digests and all population counts must match this snapshot. The existing v0 `excluded` count includes unavailable records, while this registry contract discloses `excluded` and `unavailable` separately, so the bridge requires `v0.excluded = registry.excluded + registry.unavailable`. A self-certified proposal or an altered gate is rejected. This prevents silent denominator reinterpretation, but **both packets remain unverified and carry zero authority**. No API here produces `SourceReceipt`, `UpstreamValidation`, `ReviewDecision`, a signed receipt, or a private access token.

### Reproducibility (synthetic, standard-library runtime)

In a full checkout with the existing `private_source_contract.py` in this namespace:

```sh
python3 -m unittest discover -s research/integration/diplomatic_readouts/tests -v
python3 research/integration/diplomatic_readouts/examples_registry.py --output /tmp/private-registry-a
python3 research/integration/diplomatic_readouts/examples_registry.py --output /tmp/private-registry-b
diff -rq /tmp/private-registry-a /tmp/private-registry-b
```

Portable receipt and input JSON Schemas are `registry_preflight.v0.schema.json` and `registry_preflight_input.v0.schema.json`. The built-in validator enforces relational invariants without using optional `jsonschema` at runtime; hosted CI installs the already-pinned development-only `jsonschema` package. Negative tests cover tampered hashes, stale/revoked or expired custody, wrong actors, audit-chain gaps, duplicate IDs, absent/misclassified records, false population counts, private-field injection, reserved date/holdout changes, boolean/integer confusion, and attempted reviewer/statistical/publication escalation. Example outputs are aggregate synthetic metadata only and must never be committed as real review evidence.

## Remaining authoritative prerequisites (all NOT RUN)

A later independently authorized private-host implementation must obtain actual custodian authorization and a protected registry; authenticate original bytes *against a trusted external original*, represent both raw and canonical text hash bases, verify source/selection lineage and Unicode parent/passage spans, enforce real rights/retention/privacy classification, and consult a trusted revocation feed. It must record actual human decisions with proposition-specific evidence separately from assistant-provisional labels, and verify applicable null/dependence, temporal comparability, and method gates before any exploratory interpretation. A dedicated D1 O1–O5/Outlook/Shiny/browser change-control review is still required for operational integration. The current preflight does **none** of those things and is not an instruction to open the reserved material.
