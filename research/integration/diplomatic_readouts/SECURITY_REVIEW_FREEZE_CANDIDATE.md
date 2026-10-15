# Prospective security-review freeze candidate — synthetic signature protocol

**Decision: CANDIDATE, NOT APPROVED.** This freezes exact synthetic-method source bytes and the proposed adversarial acceptance matrix for independent security review; it **does not** freeze or weaken any pre-existing source, evaluation, human-review, or publication gate. No private original source is read, no reserved transcript opened, and no access is granted. Full machine-readable candidate: [security_review_freeze_candidate.v0.json](security_review_freeze_candidate.v0.json).

## Threat model and discovered vulnerabilities

Four tests were run *before* remediation on the original synthetic implementation (GitHub Actions push run [38791494790](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38791494790), commit `cde4021cfe5e5e63edd186f0cf7e82f1477b3dac`). All four failed as expected, confirming the initial verifier erroneously returned `synthetic_signatures_verified_no_authority` when the tampered key/audit input should have been withheld.

1. **Key-ID alias, custody role:** a revoked key was relabeled under a second trusted ID using identical public bytes and unchanged Ed25519 signature; the synthetic status erroneously passed.
2. **Key-ID alias, revocation role:** the same technique evaded a revoked revocation-signing key ID.
3. **Compromised custody signer:** an attacker with custody signing key, but *not* the revocation root or independently pinned audit state, rewrote the unsigned audit tip and issued a new valid custody signature.
4. **Signer-role collision:** duplicate key IDs across the custody and revocation keyrings were accepted.

The remediation: signatures bind their `key_id` as part of the signed canonical message; key IDs cannot overlap between the signer roles, and public-key bytes cannot be duplicated within either role. The independent trust context must pin both custody-policy and audit-tip digests. The independently signed revocation checkpoint now binds the precise registry, policy, and audit-tip hashes, in addition to sequence, revocations, signer, audience, and expiry. Previously created synthetic v0 signatures using the old payload-only message form are **intentionally incompatible**, not grandfathered.

The new attack suite additionally checks compromise of only the revocation signer against the independent persisted checkpoint pin, malicious policy alteration, checkpoint-policy/registry/audit mismatch, bad key rotation, mistaken audience, permission escalation and revocation high-water rollback. All manipulated versions must be **WITHHELD**. The benign rotated, externally pinned key may be **verified_no_authority**, never authorized.

## Frozen code inputs (exact Git blob identities)

The machine-readable candidate pins Git blob SHA-1 (Git repository object identities, **not** an independent custodian certificate) for: `synthetic_signatures.py`, `signed_metadata.v0.schema.json`, `synthetic_signatures.v0.schema.json`, `registry_preflight.py`, `private_source_contract.py`, `tests/test_synthetic_signatures.py`, `tests/test_signature_redteam.py`, `examples_signatures.py`, and `benchmark_signatures.py`. The adjacent `tests/test_security_freeze.py` independently recalculates Git blob hashes, validates the closed prospective attack matrix, and ensures all protected flags remain disabled. Any subsequent change to a pinned file invalidates this candidate and requires a new separately reviewed candidate; do not silently alter its digests.

**Execution:** Python 3.13, Node 22, pinned `cryptography==46.0.4` and `jsonschema==4.26.0`. Tests and example generation are synthetic-only. No seeded random search, real transcript inputs or new production model fitting. Use the read-only coordinator workflow `.github/workflows/coord-evidence-readout-adapter.yml` for the official source/interchange/corpus/latent regressions, the independent pinned PR #70 renderer tests, native W1 24-eligible synthetic input, all negative controls, deterministic replays, and a bounded latency microbenchmark. Run after every candidate change; refuse acceptance on non-green exact-head CI, code hash drift or any weakened withhold.

## Security-review criteria and gate ledger

| Boundary | Proposed acceptance | Currently authorized? |
| --- | --- | --- |
| Cryptographic integrity | Domain-separated Ed25519 over exact key identity and canonical signed fields; complete protocol/schema consistency | Synthetic testing only |
| Revocation | Exact independently pinned, separately signed checkpoint; sequence/high-water/expiry checks; revoked key denial | Synthetic testing only |
| Audit continuity | Externally pinned audit tip and signed revocation binding; complete local hash sequence | Synthetic testing only |
| Trust-anchor compromise | Distinct signers and pinned identities; document unavoidable compromise of both roots, pins and high-water state | **No real trust root** |
| Source provenance and custodian | Independently governed enrollment, controlled keys/KMS, authenticated original source and inventory | **NOT RUN** |
| Operational safety | 13 source, review, privacy, statistical, holdout and D1 gates remain `NOT_RUN`; `authorized=false` and no access/delivery | **WITHHELD** |

**Residual limitations (review blockers):** a compromised anchor distribution can replace all pinned keys and hashes; colluding/signature-compromised custody and revocation authorities can forge a consistent history unless independent append-only ledger anchoring exists. The synthetic checkpoint does not prove global completeness or real-world freshness. No secure monotonic persisted counter, independent clock, transparency witness, HSM/KMS isolation, certificate enrollment/revocation, private-host audit isolation, source-byte provenance, reviewer choice or statistical identification is implemented. A green synthetic study does **not** license real-source intake or declaration of diplomatic findings.

## Prospective independent review and freeze decision

The candidate is **NOT approved for merge or real-source authorization**. Independent coordinator/security reviewer must: (i) independently reproduce each originally failing attack and the amended rejection, (ii) review pinned source/schema bytes and exact-head CI, (iii) verify cryptographic key-rotation/revocation logic and cross-role separation, (iv) establish requirements for authenticated external trust anchors, revocation completeness, rollback-resilient persisted state, audit witnesses and compromise response, and (v) explicitly record approved/rejected status in a *separate* coordinator decision. Until then, this file is only a prospective test-method freeze, not production certification.

**Hard exclusions:** all 37 reserved Oct 5–6 meeting transcripts unopened, all original source hashes and 24 reviewer decisions unchanged, all D1 O1–O5 authority frozen, no Outlook drafts/emails, no Shiny/browser entry points, no release manifest/Pages/mirror, no merge or publication.
