# Research browser validation v2

Standalone, synthetic-only, engineering-only browser prototype. It does not import private transcript content, refit numerical models, or authorize publication. The renderer preserves supplied family numerators/denominators without replacing the accepted W6 co-assignment formula. Missing/failed groups remain in the source ledger and frame coverage; eligibility is not silently imputed. Table-first display supports keyboard navigation, mobile horizontal scrolling, and JSON export/replay.

Run `node --test site/experimental/research-validation-v2/tests.cjs`. Serve the repository root with `python -m http.server 8000` and open `/site/experimental/research-validation-v2/`. File:// fetch may be blocked by browser security.

## Coordinator-only integration proposal

After exact-head PR acceptance and source contract verification, add a navigation link from `site/research.html` (or approved shared entry point) to this isolated prototype. For accepted W1/W2/W4 outputs, coordinator must implement a **separate read-only source-bound adapter** mapping source IDs/hashes, selection/representation identities, family-balanced pair ledgers, country-theme weighting, temporal comparability, attempted/failed fits, and review statuses to a versioned validated envelope. Do not map empirical results into this synthetic-only schema or remove its synthetic gate. Keep PR #56 unmerged until separately accepted. No edits to shared entry points are included here.

## Limitations and pending acceptance

The current implementation is an accessible table-first baseline, a basic keyboard-accessible pair-eligibility heatmap, not a complete matrix or plotted movement interface. It does not yet implement an accepted v1 interchange adapter, hash lineage verification against upstream originals, source URL inspection, graphical exports, browser automation or saved-run persistence. Node tests are deterministic; browser QA must be run separately. Co-assignment is not policy agreement, thematic profile is not stance, stability is not significance, and observed movement is not causal influence.

## Continuation audit — 15 October 2026

- Verified main from commit search: `25ba1a7948c33188f21986af3cffbe73bbcafdba`.
- Added keyboard-focusable consensus pair tiles showing **supplied** family numerator/eligible counts; zero opportunities are hatched, unstable assignments marked separately. No family aggregation or W6 numerical formula is recalculated.
- Added checks for mandatory identity disclosures, malformed family ledgers, negative theme weights and inconsistent attempted/successful/failed fits; added four negative tests.
- **NOT RUN:** Node test suite, actual Chromium/mobile/keyboard QA, CI for latest head, accepted interchange relational adapter, independent replay verification. The execution container could not resolve github.com to clone the repository; GitHub connector reads/writes succeeded. No pass claim is made from authored tests.
- **Still required:** actual pairwise matrix heatmap, country/theme graphical profile, uncertainty-aware longitudinal chart, method comparison chart, source-hash bound v1 adapter, real browser screenshot/accessibility checks and source-population compatibility tests. Do not merge or deploy before independent coordinator acceptance.
