# Coordinator multi-host witness security review — 2026-10-15

**Disposition: PASS for isolated synthetic engineering, HOLD independent production security certification, private-source authorization, scientific release, merge and deployment.** This is a prospective technical coordinator review, not an independently authenticated second-human signoff. The PR remains DRAFT/UNMERGED and all 13 private-source, owner-review, statistical, reserved holdout and D1 O1–O5 gates remain `NOT_RUN`.

## Exact reviewed source and ownership

- Repository: `LystadJS/UNGA81-Transcript-Agent`.
- Latest reviewed `main`: `da4ab9ed11dba3693d11aa12f5333963b1b85478`.
- Initial reviewed worker head: `83915afba02d74d660a22e50b6b5058883be7859`, draft PR [#89](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/89).
- Corrected tested implementation head before this decision note: `520c1857b9fa9266ac759ca9afb9e333cc9397c4`.
- All PR changes are scoped to `research/integration/diplomatic_readouts/**` and the pre-existing, coordinator-owned synthetic read-only workflow `.github/workflows/coord-evidence-readout-adapter.yml`. No shared source kernel, original bytes, source manifests, D1 producer, Shiny/Outlook/browser entry point or published website file changed.
- Pinned and separately unmerged dependency PR #70 remains `028e3d26f707401cbff498593ab27f64e2cc072a`. Previous prospective security freeze candidate remains **`PROPOSED_NOT_APPROVED`** and all nine of its pinned Git blob identities were independently compared against this branch without drift.

## New synthetic witness protocol

The new `multi_host_witness.py`, `tests/test_multi_host_witness.py`, `stress_multi_host.py`, `multi_host_witness_receipt.v0.schema.json` and `MULTI_HOST_WITNESS_REVIEW_2026-10-15.md` implement a bounded metadata-only consistency rehearsal with:

1. Four distinct, externally pinned **fictional** Ed25519 witness public keys, three of four unique signatures for a checkpoint, and no key reuse across custody/revocation/witness roles.
2. Two independently provided synthetic observer pins that must agree on the exact previous epoch, registry, revocation checkpoint, full log prefix digest, last event and checkpoint digest.
3. Domain-separated, chained source-free audit event digests; unique dense event indices, identities and ordered UTC times; an exact append-only prefix extension, not an RFC 6962 Merkle proof.
4. Signed checkpoint fields covering registry identity, previous checkpoint hash, revocation hash and sequence, epoch, complete new log hash/tip, audience, short expiry and `no_source_access_or_release`.
5. Optional independently signed gossip evidence to reject conflicting authenticated checkpoint views at the same epoch. Without gossip delivery, a partition can hide its fork; no global completeness claim is possible.
6. Exact binding of unchanged revocation sequence to its **same previously pinned revocation hash**. A different revocation hash requires a genuine sequence advance.
7. Only allowlisted `withheld` or `synthetic_quorum_consistent_no_authority` receipts; all 13 legacy gates remain `NOT_RUN`, with `authority=none`, `authorized=false`, `can_read_source=false`, `can_issue_review=false`, `statistical_eligible=false`, `publication_eligible=false`, `delivery_eligible=false`, and unchanged `transcripts_opened=0` for the 37 protected meetings.

**Proof boundary:** Four nodes with 3-of-4 quorum have pairwise intersection of at least two. At most one Byzantine witness *and* honest non-equivocating durable signer state means the intersection contains an honest signer. This reasoning is conditional; the module does not implement independently durable witness signing state, a real host enrollment protocol, authenticated observer checkpoint custody, trust-anchor bootstrap, a secure clock, real audit completeness or network reconciliation. No signature or metadata consistency verdict grants source permission.

## Independent adversarial findings and remediation

| Attempt | Before fix | Final disposition |
| --- | --- | --- |
| Corrupt or duplicate host signature; two of four signatures | Rejected in tested prototype | **WITHHELD**, zero authority |
| Two observer hosts hold different exact previous tips or checkpoint hashes | Rejected in tested prototype | **WITHHELD**, zero authority |
| Forked prior log prefix rehashed and signed by three compromised witnesses | Rejected against independently pinned previous prefix | **WITHHELD** |
| Conflicting authenticated signed gossip for same epoch | Rejected when conflict evidence is supplied | **WITHHELD** |
| Restore/replay old epoch after observer-pin advancement | Rejected | **WITHHELD** |
| Corrupt source/checkpoint hashes, wrong audience or expired epoch | Rejected | **WITHHELD** |
| Compromised upstream custody and revocation signers; honest external observer pins | Rejected when their revocation/log lineage conflicts | **WITHHELD** |
| **Change revocation checkpoint digest while retaining same sequence**, re-sign source and witness assertions | **FAIL reproduced** in [hosted run #38810450927](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38810450927): previous logic returned synthetic consistency | Fixed: exact prior-pinned revocation hash must match when sequence is unchanged. Retained regression and positive genuine-sequence-advance case. |
| Compromise both upstream signers, a quorum of witness keys, **and both independent observer pins** | All externally trusted boundaries replaced by attacker | **FORGED SYNTHETIC CONSISTENCY CAN PASS**. This is the explicit known failure mode, *not* a proven defense. No source permission or publication eligibility becomes true. |

A first hosted run also surfaced a purely test-harness privacy assertion matching the legitimate mandatory gate name `original_bytes`, not private bytes. It was corrected without removing the required gate.

## New hosted acceptance evidence

- Final implementation push [Actions #38810873051](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38810873051), job `116683460019`: **PASS**.
- Final implementation PR-triggered [Actions #38810880054](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38810880054), job `116683484532`: **PASS**.
- **221/221** synthetic coordinator Python tests, **46/46** pinned PR #70 renderer tests, official native W1/source/interchange, passage-corpus and latent regressions **PASS**, W1 synthetic source frame **24 eligible**.
- Independent seeded witness stress: **15 kinds × 20 iterations = 300 trials**, zero unexpected states; two separate runs produced byte-identical outputs with manifest SHA-256 `ad068d300155e9548937876680a350e23050d579d348cc1ae0e87b5988e2f877`. Positive statuses *including complete synthetic trust compromise* are intentionally non-authorizing.
- Previous synthetic signatures, single-host registry, restart and readout manifests remained unchanged. No original rows, signer secrets or user data were uploaded as CI artifacts. Workflow has `contents: read` and no site build, deployment or mail step.

## Security review and operational HOLD

**Engineering PASS does not certify real security.** The following remain **NOT RUN / NOT PROVIDED**: authenticated witness enrollment and key rotation, durable non-equivocation state for honest witnesses, independently persisted and authenticated observer pins across hosts/process restarts, reliable signed gossip distribution and evidence retention, secure monotonic clock and high-water counter, independent append-only audit transparency/consistency proof, source completeness witness, real key compromise incident response, custody authority and permissions, real original source/text/offset authentication, verified reviewer decisions, null/selection/dependence identification, protected heldout access approval, and all D1 O1–O5 release requirements.

**Explicit coordinator decision:** accept the isolated experimental witness **as synthetic engineering-only** for continued adversarial work. **HOLD all merge, publication, source access, reviewer authorization, inferential findings, and delivery**. PR #89 and PR #70 remain draft and unmerged until separate human and coordinator authorization. The existing frozen security-review candidate stays unapproved and unchanged; this is supplemental review evidence, not a change to its hash pins.

**Next executable task:** independently model true per-witness non-equivocation and externally witnessed signed gossip under partial network partitions, including quorum intersection and provable equivocation evidence, using invented data only. Do not treat any acceptance as real custodian enrollment, source rights, or scientific release.
