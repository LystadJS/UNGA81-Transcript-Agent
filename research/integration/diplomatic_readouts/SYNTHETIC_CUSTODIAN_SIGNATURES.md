# Synthetic Ed25519 custody and revocation preflight — engineering only

**Status: offline synthetic protocol; NO source authorization.** This design checks whether invented, signed custody metadata and a separately signed revocation checkpoint are internally consistent with an independently pinned synthetic trust context and the existing `registry_preflight.py` + `private_source_contract.py`. It does **not** establish real custodian identity, prove original UN bytes, access a private registry, authorize a reviewer, open protected holdouts or enable delivery.

## Separation of trust

| Object | Supplied by | What it binds | What it does **not** prove |
| --- | --- | --- | --- |
| Registry snapshot + custody-intent + audit | Existing synthetic registry preflight | Inventory totals, original/raw and selection SHA strings, dates, custody policy and audit event hashes | Genuine original source, complete external inventory or permission |
| Custody Ed25519 envelope | Fictional custodian signing key | Registry digest, custody-policy digest, unapproved proposal digest, last audit-event digest, custodian reference, purpose, audience, issue/expiry times, **no-access** scope | Real custodian organization or its authority to grant access |
| Revocation Ed25519 envelope | **Different** fictional revocation signing key | Registry ID, strictly typed revocation sequence, ordered revoked key IDs, issuer, audience, purpose and bounded observed/expiry window | Completeness/freshness of an outside revocation service |
| `SyntheticTrustAnchors` | Independent caller, **never the signed envelopes** | Expected registry/custodian identities, exact source/proposal/checkpoint digests, public keys and custodian-key subject mapping, revocation high-water sequence, audience | Authenticity of that caller or real-world trust bootstrap |
| Verification receipt | `verify_synthetic_signatures` | Only the result of these synthetic checks; fixed reason codes on refusal | **No** source read, review, statistical, delivery or D1 authority |

`cryptography` Ed25519 signatures are verified over canonical JSON with **different domain prefixes** (`UNGA81/SYNTHETIC/CUSTODY/ED25519/V0\0` and `UNGA81/SYNTHETIC/REVOCATION/ED25519/V0\0`). The two signing roles cannot share an identical public key. Signature payloads and receipt use closed allowlists, explicit schema versions and a fixed synthetic audience. Never parse these packets as future real authorization tokens. The fixture private keys are publicly reconstructible **test keys only**; their signing labels must never be adopted as secrets.

## Preflight order

1. First independently run **all** existing metadata-only registry checks with the previous unapproved proposal. Real/`private_development` sources, unavailable-source coercion, 5–6 October protected dates, extra private fields, permission escalation, stale custody or tampered event chains must fail.
2. Check the caller's independent trust anchors: both role-specific public-key sets, expected custodian reference, key-to-subject assignments, exact externally pinned registry/proposal/revocation digest, fixed audience and minimum checkpoint sequence. Their provenance is **unverified** in this synthetic project.
3. Verify revocation root Ed25519 signature and checkpoint constraints. Require the signed checkpoint digest to equal the independent pinned digest, sequence ≥ supplied high-water AND policy sequence, sorted unique revocations, valid and at-most-7-day observation/expiry interval, observation after the synthetic audit tip, and no revocation of the root key.
4. Verify custodian Ed25519 signature with a distinct pinned key. Require exact registry/policy/proposal/audit/custodian identity binding and a validity window inside the original metadata custody policy. Deny revoked or untrusted keys. Key-rotation works only when the new key and its custodian subject were already independently pinned and the old key is listed as revoked in a sufficiently fresh checkpoint.
5. Return **only** an allowlisted aggregate receipt. Successful crypto checks have status `synthetic_signatures_verified_no_authority`, never `authorized`. On any verification failure withhold source hashes, counts, titles and reviewer prose. Do not serialize signatures, public or private keys, row-level registry entries or source text.

Every receipt, including success, enforces **all 13 existing gates = `NOT_RUN`**, `authority=none`, `can_read_source=false`, `authorized=false`, `can_issue_review=false`, `statistical_eligible=false`, `publication_eligible=false`, `delivery_eligible=false`, and the unchanged 37-reserved-meeting/D1 lock.

## Reproduce on synthetic fixtures only

```bash
python3 -m pip install -r research/integration/diplomatic_readouts/requirements-dev.txt
PYTHONPATH=research/integration/diplomatic_readouts \
  python3 -m unittest discover -s research/integration/diplomatic_readouts/tests -p 'test_synthetic_signatures.py' -v
python3 research/integration/diplomatic_readouts/examples_signatures.py --output /tmp/new-synthetic-signature-examples
python3 research/integration/diplomatic_readouts/benchmark_signatures.py --iterations 1000 --warmup 50
```

The examples produce **10 scenarios**: 2 cryptographically valid **but unauthorized** cases (ordinary and key-rotation), and 8 explicit withholds (tampering, revocation, high-water rollback, checkpoint replacement, cross-audience replay, expired custody, real-source attempt and permission escalation). Use separate empty directories to prove byte-identical SHA-256 output. All public files contain no real UN text, source URLs, personally identifying information, credentials or signature/private-key material.

### Benchmark methodology and interpretation

`benchmark_signatures.py` compares existing **metadata-only** `preflight` with the full metadata + two Ed25519 verifications + externally pinned signed revocation. It alternates execution order, uses `perf_counter_ns`, reports median/p95/mean/min/max and a median overhead ratio. Warmup, iteration count, Python version, platform and `cryptography` version are recorded. The benchmark contains **only invented metadata** and *does not apply a performance gate*. Results vary by runner, CPU, VM load and Python/OpenSSL build; do not interpret as measured production throughput, security efficacy or evidence of diplomatic findings.

Example local engineering measurements (Linux / CPython 3.13.5 / cryptography 46.0.4, 1,000 measurements per mode, 50 warmups): metadata-only **0.105 ms median** (p95 0.211 ms); signed+revocation **0.473 ms median** (p95 0.744 ms), approximately **4.51×** median runtime. CI records its own fresh performance sample and must not assert these exact values.

## Security and methodological limitations

- SHA-256 binds bytes *relative to the supplied synthetic record*; it does not authenticate original custody or its legal/ethical scope. Real signed identities require an independently governed PKI/KMS, audited key issuance, physical/organizational credential validation, secure clock, authenticated revocation service, monotonic persisted checkpoint state, freshness proofs, key-compromise response and secure audit retention. This module implements **none** of those real services.
- Independent checkpoint pins/high-water prevent rollback **only when** the caller obtains and persists them from a source independent of the attacker. The mock `SyntheticTrustAnchors` dataclass and publicly reproducible keys are **not** such a source; their correctness is an explicit future prerequisite.
- The signed revocation list is synthetic and bounded; no completeness/availability guarantee follows from the signatures or sequence. A key signed before its revocation is still withheld at the checkpoint pinned by the caller. A cryptographic signature is not review, statistical identification, or authorization of a proposition-specific stance.
- Do not use the 37 reserved 5–6 October texts, original source rows, private annotations, corrected transcripts, real Outlook drafts, D1 producers or publication manifests. The frozen O1–O5 policy and owner review decisions remain unchanged. A future private-host validator, if approved separately, must be an entirely new security and governance phase.

**Coordinator disposition:** synthetic engineering candidate only; PR remains DRAFT and UNMERGED. Do not deploy, publish, send, grant source access, or claim real diplomatic evidence.
