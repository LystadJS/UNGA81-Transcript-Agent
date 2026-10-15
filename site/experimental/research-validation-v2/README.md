# Research browser validation v2

Standalone, synthetic-only, engineering-only browser prototype. It does not import private transcript content, refit numerical models, or authorize publication. The renderer preserves supplied family numerators/denominators without replacing the accepted W6 co-assignment formula. Missing/failed groups remain in the source ledger and frame coverage; eligibility is not silently imputed. Table-first display supports keyboard navigation, mobile horizontal scrolling, and JSON export/replay.

Run `node --test site/experimental/research-validation-v2/tests.cjs`. Serve the repository root with `python -m http.server 8000` and open `/site/experimental/research-validation-v2/`. File:// fetch may be blocked by browser security.

## Coordinator-only integration proposal

After exact-head PR acceptance and source contract verification, add a navigation link from `site/research.html` (or approved shared entry point) to this isolated prototype. For accepted W1/W2/W4 outputs, coordinator must implement a **separate read-only source-bound adapter** mapping source IDs/hashes, selection/representation identities, family-balanced pair ledgers, country-theme weighting, temporal comparability, attempted/failed fits, and review statuses to a versioned validated envelope. Do not map empirical results into this synthetic-only schema or remove its synthetic gate. Keep PR #56 unmerged until separately accepted. No edits to shared entry points are included here.

## Limitations and pending acceptance

The current implementation is an accessible table-first baseline, not a complete graphical heatmap or plotted movement interface. It does not yet implement an accepted v1 interchange adapter, hash lineage verification against upstream originals, source URL inspection, graphical exports, browser automation or saved-run persistence. Node tests are deterministic; browser QA must be run separately. Co-assignment is not policy agreement, thematic profile is not stance, stability is not significance, and observed movement is not causal influence.
