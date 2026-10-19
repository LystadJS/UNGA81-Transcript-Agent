# Independent persistent-revocation / dual-authority security assessment

**Status:** coordinator **synthetic engineering evidence only**. **NO REAL-SOURCE SECURITY ACCEPTANCE.** Original prospective freeze candidate remains `PROPOSED_NOT_APPROVED`. This change adds an isolated, offline replay rehearsal under `research/integration/diplomatic_readouts/**`; it does **not** modify the pinned signature verifier, its schemas, upstream D1 O1–O5, release manifests, Shiny, browser interfaces, Outlook, private source registry, or any original UN data.

## 1. Threat model and tested propositions

| ID | Synthetic attack or control | Expected observation |
| --- | --- | --- |
| P01 | Signed checkpoint and separately pinned observer state, fresh process | `synthetic_checkpoint_consistent_no_authority` |
| P02 | Independently pinned rotated key + higher revocation sequence | Verification only, never a source grant |
| P03 | Replay signed earlier revocation checkpoint after advancing observer high-water | `withheld` |
| P04 | Restore older on-disk state after restart, retaining later independent observer pin | `withheld` |
| P05 | Delete, corrupt, symlink, or mutate stored checkpoint | `withheld` |
| P06 | Present valid signatures without an independent observer pin | `withheld` |
| P07 | Create a competing same-sequence on-disk fork | `withheld` |
| P08 | Compromise **both custody and revocation Ed25519 signers**, keep independent observer pin | `withheld` for forged checkpoint |
| P09 | Compromise **both signers and the external observer-pin distributor** | Forged metadata can appear cryptographically consistent. **Expected limitation**, never permission |
| P10 | Revoke old key but fail to rotate active custody signature | `withheld` |
| P11 | Attempt approval, publication, or source access in any receipt | Must remain disabled |

These exercises use publicly reconstructible fictional test signing keys. The phrase "compromise" models attacker capabilities only, not an actual breach. The verifier's signature/baseline security properties are pinned by the previous prospective candidate. New code is a **separate test-only witness simulation**, not a replacement verifier or deployed trust anchor.

## 2. Restart-state protocol, simulated only

`persistent_revocation_review.py` has no network calls or source reads. It stores only the registry ID/hash, proposal/policy/audit-tip hashes, signed checkpoint hash, monotonically increasing sequence, synthetic revoked key IDs, previous state digest, check time, and explicit no-authority flags. It refuses additional keys, unpinned state, missing/corrupt/symlink files, a non-increasing update, changed registry identity, and a restored state whose digest does not match an **independently supplied** observer pin.

`ExternalObserverPin` models an external *trusted* witness: minimum revocation sequence and exact state, registry and checkpoint digests. Constructing that dataclass or calling `proposed_pin_from_state` **does not create authenticity**. The pin must be durably maintained by a separately administered principal outside the rollback domain in any future actual architecture. The local rehearsal performs atomic writes with best-effort fsync, but provides **no secure monotonic counter, HSM, multi-writer concurrency control, append-only proof, or anti-rollback protection if an attacker controls both the file and the external pin**. Its directory checks are not a filesystem-hardening audit. Missing or untrusted witness => withheld.

`guarded_restart_verify` performs state/pin consistency and then reruns the existing synthetic custody and revocation signatures; its output contains exactly 13 `NOT_RUN` gates, `authority: none`, `authorized: false`, `can_read_source: false`, `can_issue_review: false`, `statistical_eligible: false`, `publication_eligible: false`, `delivery_eligible: false`, and the 37-meeting seal with `transcripts_opened: 0`. No prior synthetic readout or custody approval is promoted into scientific authority.

**Attack inference:** Compromising both signers is insufficient *under the assumption that* the observer state is independently controlled and up to date. Compromising the observer distribution too defeats checkpoint authenticity, even if a verifier correctly checks both signatures and the local file. This third case is intentionally demonstrated as a residual, not incorrectly called a passing security gate. An offline recovered older pin can similarly defeat monotonicity; authenticated delivery and independent high-water persistence remain future prerequisites.

## 3. Exact reproducibility commands

From a full repository checkout, with development-only pinned dependencies installed:

```bash
python3 -m pip install -r research/integration/diplomatic_readouts/requirements-dev.txt
python3 -m unittest discover -s research/integration/diplomatic_readouts/tests -v
python3 research/integration/diplomatic_readouts/stress_persistence.py --output /tmp/unga-restart-a
python3 research/integration/diplomatic_readouts/stress_persistence.py --output /tmp/unga-restart-b
diff -rq /tmp/unga-restart-a /tmp/unga-restart-b
```

All examples are synthetic, source-free and explicitly no-authority. The coordinator CI workflow additionally runs native `un.parallel-analysis.v1` relational tests, W1 source framework, passage-corpus/latent regressions, the pinned PR #70 renderer, original metadata and signature scenarios, and a bounded performance microbenchmark. The `tests/test_security_freeze.py` suite guards original code Git blob identities and unchanged frozen status. **Do not update the previous freeze candidate merely to make new tests pass.**

## 4. Coordinator security decision and remaining blockers

**Decision prepared:** **PASS** for the *isolated synthetic stress-test evidence* only, subject to exact-head hosted CI and byte-identical replays; **HOLD** for approving the original prospective freeze as an operational security protocol. This assessment is an engineering opinion based on synthetic tests, not a human custodian sign-off or independent source authorization.

Real-host blockers: authenticated external observer enrollment, rollback-resistant persisted high-water state, authenticated freshness independent of the source operator, append-only/witnessed audit history, split-brain reconciliation across nodes, securely stored/rotated keys, credential recovery, trust-anchor compromise response, real legal/ethical source rights, actual owner review, accepted statistical identification, and a separate explicit D1 O1–O5 release decision. No source bytes or reserved transcripts may be supplied to this study. **No merge, deployment, source-access grant or publication follows.**
