# Synthetic witness partition reconciliation and per-witness non-equivocation

**Status: isolated engineering candidate, not independently security-certified or authorized for source access.** This module is a deterministic, no-network, synthetic-only simulation. It is not a new producer, a private-source service, a real witness deployment, a statistical validator or a publication gate. Keep PR #89 draft and unmerged, pinned PR #70 separate, all 37 October 5–6 reserved meetings unopened, and D1 O1–O5 unchanged.

## Input and trust boundaries

- `partition_reconciliation.py` uses *only invented* checkpoint and source-free log metadata conforming to the existing `multi_host_witness.py` v0 hash domains. It does not alter that file, the nine pinned freeze candidate source blobs or existing verifier behavior. Native hash parity is checked in the full-checkout test.
- Exactly four fictional Ed25519 witness public keys are pinned in a `Keyring`, with unique IDs and raw public-key bytes. There are two different synthetic observer IDs. Test private keys are **deterministically reconstructible** and entirely unsuitable for deployment.
- An honest synthetic witness signs a checkpoint exactly once per epoch. Before signing, the harness verifies **two separately supplied observer pins** for the complete previous signer-state digest, epoch and checkpoint ID. It requires strictly advancing epoch, the expected previous checkpoint, exact append-only log prefix, bounded log integrity, and monotonic revocation sequence. A changed revocation hash without increasing sequence is refused. The signature binds the witness ID and canonical checkpoint identity under a new domain separator.
- This does **not** implement durable storage of observer pins, real per-host HSM signing discipline, a securely distributed trust bundle, a trusted time service, audit witness gossip delivery, or transactional signing. Constructing both pins from an attacker-restored snapshot destroys rollback resistance. The code creates *pin proposals*, never asserts their independent authenticity.
- Gossip accepts only Ed25519-verifiable synthetic votes for **one exact parent checkpoint and next epoch**, and checks two independent prior gossip-state pins. Votes are sorted canonically, duplicates never inflate the quorum, malformed signatures/unknown senders refuse, and per-host conflicting signed checkpoints produce deterministic equivocation-evidence hashes backed by the retained original signed messages. A returned gossip snapshot contains **signed fictional metadata** and is private to this harness; the allowlisted public receipt contains no signature, source rows, original bytes or signer keys.
- If a cryptographically verified conflicting vote arrives after the first quorum, the next reconciliation reports **WITHHELD** and retains evidence across simulated restart. Quorum alone returns `quorum_observed_no_authority` and cannot prove all gossip has arrived, audit-log completeness, consensus, real provenance, or absence of forks. This is deliberately a weaker status than the existing full signed-checkpoint/source-validator result.

## Quorum/partition stress model

For four signers and a **3-of-4 quorum**, any two different 3-host quorums intersect in two IDs. If at most one signer is Byzantine and each honest signer durably signs at most one checkpoint in an epoch, conflicting quorums are impossible. If *two* members equivocate or a signer loses its externally pinned state, conflicting signed quorums can be constructed and the conflict is detected only when both views are gossiped. A 2–2 partition cannot independently claim a quorum. A 3–1 partition can observe a synthetic quorum but **cannot infer that the isolated host has no conflicting evidence**. Later verified gossip may revoke the observed experimental status, but cannot undo any already-delivered real action, which is why this simulator grants none.

### Synthetic scenarios and negative controls

The local unit suite includes 46 tests at authoring time: honest single-sign constraints, valid one-epoch progression, stale state recovery, log-prefix rewrite, missing/split observer pins, duplicate delivery, 2–2/3–1 partitions, delayed reconciliation, valid key-bound signatures, invalid signatures and audiences, role/identity aliasing, malicious double-signs, overlapping conflicting quorums, proof reconstruction and persistence across restart, deliberate proof deletion, gossip order independence and a closed JSON Schema. One parity test checks the *actual* existing `multi_host_witness` checkpoint and log digests and runs in the full checkout; it is not counted as executed locally when the dependency is unavailable.

`stress_partition.py` replays **18 classes over 360 trials** using fixed integer seed `81081` (sample ordering varies by deterministic PRNG). It includes the known **witness-quorum compromise** case: an attacker controlling three witness signing keys can generate a signed quorum over an otherwise unvalidated checkpoint hash while retaining the honest observers’ **previous parent pin**. Gossip observes the cryptographic votes but does not authenticate the supplied checkpoint/log or independently establish source provenance. The simulated output is **only a no-authority receipt**, never a source-validation or security authorization. Complete compromise of the independent pins is an additional, more powerful failure mode. It emits a small JSON manifest with counts and test statuses, no private keys, raw signatures, source URLs, transcript text or actual source-bearing rows. Run twice and compare bytes.

```sh
python3 -m unittest discover -s research/integration/diplomatic_readouts/tests -v
python3 research/integration/diplomatic_readouts/stress_partition.py --iterations 360 --seed 81081 --output /tmp/partition-one
python3 research/integration/diplomatic_readouts/stress_partition.py --iterations 360 --seed 81081 --output /tmp/partition-two
diff -rq /tmp/partition-one /tmp/partition-two
```

Use the existing read-only GitHub Actions workflow `.github/workflows/coord-evidence-readout-adapter.yml` to run native v1 source and interchange regressions, frozen synthetic renderer tests, and the new stress suite in a complete checkout. Do not attach uploads containing signed vote packets or any operational certificate.

## No-authority contract

Every `reconcile_gossip` receipt has `authority: none`, `authorized: false`, `can_read_source: false`, `can_issue_review: false`, `statistical_eligible: false`, `publication_eligible: false`, `delivery_eligible: false`, `source_text_included: false`, `source_rows_exported: false`; all **13** existing source/privacy/reviewer/statistical/holdout/D1 gates remain `NOT_RUN`, `transcripts_opened: 0`, `reserved_meetings: 37`, `d1_o1_o5: frozen`. The JSON Schema requires these values. `pending_gossip` and `quorum_observed_no_authority` are engineering states, **not** access grants or evidence of real-world security.

## Remaining fundamental blockers

Authentic private-host witness enrollment, independent pin persistence, non-equivocating hardware-backed signer state, authenticated gossip channel, durable conflict archives, secure monotonic timestamp/checkpoint ordering, independently witnessed append-only log completeness, independent custodian/owner approvals and compromise recovery are **not implemented or demonstrated**. Compromise of all witness signers and both observer state custodians is not detectable in this synthetic system. Source and reviewer authority, null calibration/statistical identification, heldout access and every D1 publication gate remain withheld; the previously proposed freeze remains unapproved and its pinned code unchanged.

**Disposition:** synthetic engineering review candidate only. Do not merge PR #89 or PR #70, deploy, open protected sources, send Outlook/email, or publish any findings.
