# PR #89 coordinator security acceptance decision — persistent revocation stress

**Decision timestamp:** 15 October 2026, synthetic-engineering review.
**Disposition:** **PASS** for the isolated synthetic persistence/dual-authority stress-test implementation and preservation of all existing holds. **HOLD** for approving the prospective security freeze as a real private-host security protocol or authorization mechanism. **NO MERGE, NO SOURCE ACCESS, NO PUBLICATION.**

This is a coordinator engineering assessment based solely on invented synthetic inputs and hosted tests, **not** an independent owner/custodian sign-off, security certification, trusted-root enrollment or statistical/release decision.

## Verified references and scope

- [PR #89](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/89) remained **draft and unmerged** during this review.
- Pinned upstream [PR #70](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/70) readout dependency: `028e3d26f707401cbff498593ab27f64e2cc072a`, not vendored, merged or modified.
- Initial current-main and frozen PR head: `da4ab9ed11dba3693d11aa12f5333963b1b85478` / `3d248a79e354eacc98ba6df4625b8fe80a93134d`. The earlier prospective freeze remained `PROPOSED_NOT_APPROVED`; no frozen signature code or schema bytes were altered for these stress tests.
- Candidate extension changes only `research/integration/diplomatic_readouts/**` and the existing coordinator-owned, read-only synthetic CI workflow. No D1 O1–O5, R/Shiny, Outlook, browser loader, source retrieval, original checksums, 24 owner review decisions, site release or Pages/mirror change.

## Independent threat-model review

**External witness as explicit precondition.** The frozen v0 signature verifier checks independently *supplied* checkpoint digests and minimum sequences, but provides no durable counter or external witness. The supplemental `persistent_revocation_review.py` is a strictly synthetic simulation: a JSON checkpoint with explicit 0-authority flags, SHA-256 domain-separated state digest, monotonically increasing sequence and predecessor linkage, local atomic-write/fsync rehearsal, and a separately supplied `ExternalObserverPin` containing a minimum sequence and exact registry/checkpoint/state digests. A file cannot serve as its own external pin. Deleted, corrupted, symlink, old/replayed or forked files fail closed. These local writes and fixture-supplied pins are **not** evidence of actual external custody or rollback resilience.

**Dual-authority compromise boundary.** The synthetic attacker can use both publicly reconstructed Ed25519 role keys to issue a forged custody assertion and a replacement signed revocation checkpoint. An unchanged independently retained pin rejects it. The test deliberately shows the **counterexample** when the same attacker can also replace the external pin and persisted file: the forged fictional checkpoint obtains `synthetic_checkpoint_consistent_no_authority`. That is an **unresolved system-level security risk**, not a pass against total compromise. The result still has `authorized=false`, `can_read_source=false`, 13 `NOT_RUN` gates and an unchanged reserved holdout lock.

| Threat/control | Synthetic result | Operational interpretation |
| --- | --- | --- |
| New process reads exact persisted checkpoint with out-of-band pin | PASS | Demonstrates parser/process replay only, not trust in pin source |
| Proper rotated key and sequence-3 revocation state | No-authority success | No actual authorization issued |
| Restore old disk volume while keeping new external pin | WITHHELD | Demonstrates conditional rollback detection |
| Missing pin, missing/corrupt file, forged same-sequence fork | WITHHELD | Fail-closed local behavior |
| Dual custody+revocation signers compromised, witness unchanged | WITHHELD | Conditional resilience to signer-only compromise |
| Dual signers **and** observer/pin compromised | Forged synthetic metadata verifies, still no authority | **Residual security blocker; do not claim production resilience** |
| Attempt to use revoked old custody key without proper rotation | WITHHELD | Missing/failed original provenance remains withheld |

## Exact-head test evidence

The first workflow at `51ebb1acf5c2f8ba874f7da63e3e162b987bd45d` failed **one new test harness case** because Python Ed25519 private-key objects cannot be deep-copied. Rebuilding a fresh deterministic fictional fixture fixed the test without modifying the signature verifier, frozen schemas or scientific gates; the test-only correction was committed at `d7ad88da27a11e7c8f5123636148ea6b33521b8c`.

- [Hosted push #38806175794](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38806175794), job `116667501277`: **SUCCESS** at `d7ad88da...`.
- [Hosted PR #38806184543](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38806184543), job `116667533978`: **SUCCESS** at `d7ad88da...`.
- **179/179 coordinator tests** (162 prior frozen/synthetic tests plus 17 new restart/compromise tests), **46/46 pinned PR #70 renderer tests**.
- Native W1/parallel interchange/source-aware/passage-corpus/latent regressions: **PASS**; W1 synthetic input 24 eligible. No original UN rows or reserved transcripts opened.
- **Eight** invented restart and dual-compromise demonstrations rendered twice into separate directories with byte-identical results. SHA-256 of synthetic manifest:
  `6a25b09ad44f35ebcc44834726c8098870f416638a87adfefed9821934e4e9a4`.
- Previously frozen synthetic signature, registry and source-to-readout manifests remained identical; original code-blob freeze check continued to pass.

All 13 original gates (`source_registry`, original bytes/offsets, selection/dependence, attribution/stance, actual owner review, privacy, statistical identification, reserved holdout, D1 publication) remain **`NOT_RUN`**. The original 37-meeting holdout has `transcripts_opened=0` in every checked output. No access or release-capable token is emitted.

## Acceptance matrix and residual blockers

| Requirement | Decision |
| --- | --- |
| Synthetic restart/rollback and dual-signer compromise tests | **PASS** at the reviewed implementation head |
| Preservation of prospective freeze source blobs, original contract and all gates | **PASS**, unchanged frozen signatures |
| Authenticated *external* witness distribution, monotonic persisted counter | **NOT RUN / BLOCKER** |
| Tamper-resistant key storage, trust-anchor enrollment, secure clock | **NOT RUN / BLOCKER** |
| Append-only witnessed audit completeness, multi-host fork/restart handling | **NOT RUN / BLOCKER** |
| Compromise of both signers and the external observer | **UNRESOLVED BY DESIGN** |
| Real/private original-source authentication, rights, source/text offset replay | **NOT RUN / WITHHELD** |
| Actual human source/reviewer decision, statistical identification, D1 O1–O5 | **NOT RUN / WITHHELD** |
| Merge, email, Shiny/browser integration, website/Pages publication | **NOT AUTHORIZED / NOT DONE** |

**Final disposition:** **ACCEPT synthetic security-test evidence only; do not approve the v0 candidate as a real authentication or private-source release mechanism.** The freeze candidate is **PROPOSED_NOT_APPROVED**, not silently changed to approved. Before any real private-host proposal: obtain an independently administered witness with durable monotonic state and auditable revocation freshness, exercise multi-host restarts/competing witness heads and dual-authority compromise under a formal security threat model, arrange human custodian/security review, and separately satisfy source, statistical and publication gates. PR #89 stays draft/unmerged.
