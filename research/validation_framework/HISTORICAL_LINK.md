# W1 historical source-inventory linkage candidate (post-PR #19)

**Engineering candidate; coordinator approval required.** This implementation does not modify or define an authoritative v2 analytical interchange. It refuses legacy `un.parallel-analysis.v1` promotion and reads the already accepted standalone `un.parallel-source-inventory.v1` companion in memory.

## Problem and scope

The private P2 2016–2023 source inventory has 792 country–session cells: 790 independently original-PV-corroborated Harvard speech observations and two genuinely unverified cells. Canonical W1 supports at most 600 observations per source-selected fit; earlier private source-authenticated 523- and 600-observation W1 computations are recorded in the coordinator's existing acceptance reports. A W1 selected cohort is **not** the whole historical sampling frame. Neither extra verified-but-not-selected observations nor unverified cells may be counted as model nonconvergence, an unassigned density point, diplomatic speech absence or a zero issue mention.

The new `historical_link.cjs` produces an aggregate-only, explicitly non-authoritative `un.w1-historical-inventory-link.candidate.v0` object from (a) an already executed W1 in-memory result and (b) a separately validated source-inventory v1 sidecar. It does not read an original PDF, speech, vector cache, or repository-held private evidence. The upstream P2 authentication must happen **before** linking using the coordinator's original-byte/hash and full-speech attestation procedures. The new validator does not claim to independently reproduce those original-byte checks.

## Exact evidence join

1. First invoke the authoritative source-inventory v1 validator, including inventory hash, source status, coverage, year and period membership, source-group consistency, and refusal of unapproved legacy bindings. Require `legacy_v1_binding.mode=withheld`.
2. Require exact original source schema, engine, byte-vs-text hash basis and SHA-256 equality with W1. For P2, require the unchanged `un.p2.original-pv-reconciled.v1` schema, 2016–2023 historical source rules, and a privately verified recorded-country-year inventory. Do **not** relabel P2 as a supported legacy-v1 source.
3. Match every W1 input row by immutable source observation ID, original text SHA-256, actual event date, official meeting and source-family IDs, source status, review status, and available original PDF SHA-256. Reject any promotion of recorded affiliations to authenticated humans. Missing records retain their original reasons.
4. Recompute the W1 selected ordered ID/text-hash SHA-256 and source/population hash. Require **every** fitted model to retain the exact original selected population, representation identity and full-fit/assignment denominator. Verify grouped refit attempt counts and source-subset denominators.
5. Keep two different SHA-256 quantities: the **inventory selection fingerprint** for its original source-state universe, and the **W1 selected-fit fingerprint** for only its eligible observations. Do not substitute one for the other.

## Denominator rules

| Quantity | Meaning |
| --- | --- |
| Full inventoried cells | Full source-state universe, regardless of W1 eligibility |
| Verified available | Source-authenticated observations in the inventory |
| W1 selected eligible | Explicitly source-selected observations actually offered to each numerical fit |
| Verified not selected | Original verified sources outside the W1 selection, **not** non-converged fits or speech absence |
| W1 excluded | Records present in the W1 frame but excluded for documented source/selection reasons |
| Unverified and other missing | Entirely separate source-inventory statuses; retain null dates where unknown |
| Unassigned/noise | Only *eligible fitted* observations with method-specific cluster 0 |
| Skipped/failed fits | Actual declared W1 attempts/ledger; never convert to a zero effect |

**No confidence intervals, p-values or political alignment conclusions** follow from linked source counts or grouped-omission ARI. Source meetings and repeated country affiliations can form one dependent connected component, making affiliation bootstrap invalid. The current historical design has only four calendar years per era, and earlier simulations showed undercoverage.

## Synthetic checks and reproducibility

From the repository root (Node 22, no new dependencies):

    node research/validation_framework/tests/test_historical_link.cjs
    node research/validation_framework/tests/test_framework.cjs
    node docs/parallel-work/test-source-inventory-v1.cjs

The first command builds an entirely invented 28-cell inventory (25 available, two unverified, one unavailable), links it against exactly 24 source-selected W1 fictitious passages and two fitted methods, and verifies that one additional available cell remains **verified-but-not-selected**. Adversarial tests change hashes, schema, source basis, meetings, source families, dates, source text, fit identities, denominators, missingness and legacy claims. A strict candidate JSON Schema rejects unexpected source rows and publication eligibility. Existing W1 CI runs this new test through its existing `test_framework.cjs` entrypoint; no new workflow, shared roadmaps, browser code or frozen contracts change.

Only the source-free aggregate *candidate structure*, code, tests and invented fixture are published. Real P2 source correspondence is **not rerun** here: the necessary authenticated original PDF/Harvard files and private selected W1 result are not present in this conversation.

## Coordinator decision required

The coordinator should review the candidate **as a research-local metadata read model**, not merge it into the shared v1 schema or turn on a browser view. Accepting a new formal historical analytical v2 output will require a separate coordinator-owned versioned contract and independently private original-source replay, including population/selection policy, original PDF verification, source year/meeting dependence, all failures and missingness. The 37 reserved October 5–6 2026 transcripts, original source digests, 24 completed human decisions and D1 O1–O5 publication gates remain frozen.
