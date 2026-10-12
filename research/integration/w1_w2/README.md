# Coordinator W1 → W2 consensus interoperability

**Status:** Synthetic-only engineering integration. No real transcript inputs, reserved holdout, direct browser wiring, published empirical output, or frozen analytical-gate modification.

## Scope and current verified inputs

This read-only integration connects **actual fitted W1 synthetic output** to merged W2, W5 and W6 modules, without modifying those sources:

- W1 — research/validation_framework: native runner, interchange adapter, source frame validation and synthetic fixture.
- W2 — research/consensus: versioned source-bound fit ingestion, pair denominators and balanced consensus.
- W5 — site/parallel/w05-browser: native interchange validator, side-by-side view and checksum-verified saved-run replay.
- W6 — site/experimental/evidence-viz: native synthetic-only consensus heatmap/inspector.

The W1 fixture has 25 inventoried fictional records, 24 eligible observations and one unavailable source. Five baseline methods fit the same 24 IDs under a deterministic source-group schedule. Exact W1 code SHA, source/text and selection digests, model parameters and seed, original group assignments, fitted representation, and v1 result rows must reconcile before W2 ingestion. Public artifacts contain synthetic metadata and no source text.

## Method-family projection

W1's v1 output classifies all five algorithms under the generic method-family label **unsupervised_partition**. That is not informative enough for W2's distinct family balancing. The bridge projects a new separately identified W2 envelope (preserving every original source and fit row):

| W1 algorithm | W2 declared family |
| --- | --- |
| kmeans / pam | partition |
| hierarchical | hierarchical |
| gmm | mixture |
| hdbscan | density |

The W2 configuration ID includes the pinned fit options, representation identity/version and method, omitting only display model ID and random seed. The W2 projection declares its own code SHA and producer identity rather than impersonating W1. The four family weights are 25% each in the original synthetic fixture. Similar lexical PCA/LSA evidence is **not independent source corroboration**.

## Statistical limits

W1 grouped refit summaries report optimizer attempts, failures, ARI/AMI, source-group omissions and pairwise consistency summaries, **but not the child observation/cluster assignments**. Those summaries cannot be counted as W2 grouped pair opportunities. W2 therefore consumes only original W1 baseline fitted assignments. Grouped W2 LOO/bootstrap uncertainty is **not_estimated**, not silently extrapolated from W1 stability metrics.

Distinct concepts remain separate: W1 numerical-fit stability, W2 cross-method coassignment, source-group dependence, and unperformed null-calibrated inference. Neither stable language clusters nor semantic similarity imply government positions, political coalitions, diplomatic agreement probability, or policy influence.

## W5 and W6 integration constraints

W5 accepts the original W1 and W2 standardized interchange separately, retaining every available, unavailable, noise and excluded source and verifying checksum archive/replay. No algorithm is refitted by W5.

W6's current heatmap computes a **simple mean of eligible method-family integer pair ratios**. W2 computes a **weighted coassigned numerator divided by weighted assigned-both denominator**, which may differ if seeds/configurations and noise change the effective family weights. The adapter reconstructs and verifies every original hard-assignment pair and permits W6 rendering only when both expressions are numerically equal on *every* pair. Any discrepancy returns an explicit withheld panel rather than a visually attractive but incorrect result. W6's 35-observation display limit is also enforced without silent sampling. A targeted unequal-weight fixture verifies refusal.

## Reproduction

Node.js 22, no extra npm dependencies:

~~~bash
node --test research/integration/w1_w2/test-integration.cjs
node research/validation_framework/tests/test_framework.cjs
node research/consensus/test_consensus.cjs
node --test site/experimental/evidence-viz/tests.cjs
node research/integration/w1_w2/make-synthetic.cjs /tmp/new-w1-w2-synthetic
~~~

The synthetic exporter refuses repository-local output paths, writes files with restricted permissions, and produces SHA256.json, receipt.json, W1/W2 interchange records, a W2 method-family audit and consensus report, and a script-free W6 HTML snapshot. W1's original generated-at timestamp varies across executions, so per-run file-byte digests may change even when the seeded assignments and source identities are reproducible.

The dedicated coordinator GitHub Actions workflow runs 16 native integration/refusal checks, W1 source-aware tests, 36 W2 consensus checks, the original v1 contract regression, W5 and W6 tests, latent/corpus regressions and a checksummed synthetic export. Results must be assessed against the **exact PR head**, not historical CI logs.

## Unresolved issues and next stage

1. W1 does not export observation-to-cluster assignments for grouped refits; W2 inferential/source-group uncertainty remains unestimated. A new explicitly versioned W1 child-fit record contract is needed before enabling that layer.
2. W2 supports at most 256 eligible observations; W1 allows up to 600, and W6's interactive pair heatmap allows 35. Never silently sample.
3. The prior W2 synthetic fixture records a **total_in_frame of 6** despite having **12** eligible invented observations. Its legacy validator does not reject this inconsistent denominator. This coordinator bridge requires full frame reconciliation. A separate W2-owned fix should correct its fixture and source contract validation.
4. W2-native W6 visualization of weighted pair numerator/denominator requires a future reviewed contract extension; the current adapter renders only exactly equivalent cases.
5. All source-dependent country/stance interpretation, null calibration, empirical publication, original-byte development data and the 37 reserved October 5–6 transcripts are out of this PR's scope. The D1 gates, shared roadmaps, browser entry points, site release manifest and portfolio mirror remain unchanged.

**Coordinator disposition:** integration-ready as a synthetic-only read model; not a production, empirical or website release approval.
