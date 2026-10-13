# Coordinator W2/W4 → W6 source-evidence adapters

**Engineering-only / synthetic-only.** This is a post-merge continuation of
PR #20, PR #17 and PR #18, not publication of real UN evidence.

## Purpose

W3 graph evidence is already connected through the coordinator research hub.
This independent change adds strict read-only compatibility from:

- **W2's original un.consensus.v1 weighted pair report**, together with its
  authoritative *complete* un.parallel-analysis.v1 interchange envelope;
- **W4's original un.longitudinal-comparison.v1**, complete interchange and
  original synthetic longitudinal input panel (genre/meeting provenance is
  needed to retain W4's prescribed grouping weights).

The bridge does **not** accept private development outputs or open sources.
The W2, W4 and released W6 method kernels, contract identifiers, model
provenance, frozen D1 gates and reserved evaluation remain unchanged.

**Public release boundary:** The accepted W6 runtime is already included in
the site's Pages allowlist, so editing its existing site/experimental asset
would trigger public deployment and website-mirror divergence. This PR instead
keeps a clearly labeled **coordinator-only derived W6 renderer** in
evidence_renderer.cjs under this nonpublished research/integration subtree.
It preserves the original W6 demos while adding W2/W4 read-model modes.
No existing site/** file, Pages allowlist, live release manifest or portfolio
mirror is changed. A future separately approved public C5 integration must
reconcile the changes with the accepted W6 runtime and rerun deployment QA.

## Statistical identity and non-interchangeability

**W2:** The integrated view now also exposes original W2 per-family
planned weights, configurations, model/failure counts, and original fit ledger.
These are displayed without redistributing failed or absent opportunities.

**W4:** The coordinator independently replays saved transform coefficients
against the original frozen source maps and external anchors; it rejects
coordinate tampering, nonorthogonal rotations, drift in imported cluster-fit
IDs/labels, and manufactured W4 refit attempts. The W4 unavailable source
ledger counts *unique source-family series*, distinct from unavailable
observation rows; the synthetic regression explicitly tests 11 missing
observation rows belonging to one unavailable family.

**W2:** Original W6 synthetic example computes an average of separate
method-family co-assignment rates. W2 instead computes a **preplanned,
hierarchically weighted co-assigned numerator / assigned-both weight**.
These statistics are *not generally equal*. New W6 panel type
pair_mode = w2_weighted_conditional displays W2's **original** ratio and
checks its exact numerator, assigned-both denominator, planned-fit
denominator, raw coassignment/noise/missing counts and failed fits.
A numerical display never renormalizes successful fits or reconstructs
family weights from displayed labels. Method family contribution names
come from W2, and its original family weight audit is retained in the
typed panel object. Grouped refit quantiles remain descriptive sensitivity,
**not confidence intervals**.

**W2 inventory:** The W2 fixture's total_in_frame = 6 counts **meetings**,
while eligible = 12 counts synthetic source observations. These different
units are now explicitly identified. An impossible mismatch is still
rejected. Do not silently invent six extra meetings or change W2's
immutable source cohort.

**W4:** Already aligned per-source display scores are grouped using
W4's original **equal-meeting-within-genre, equal-genre-per-actor** rule.
Matched actors only use shared genres; arrivals/departures are isolated.
The original W4 comparison identifies rigid anchor-based full-refit
alignment or a *reused pinned transform*, which needs **zero** newly fitted
anchors. Those are separate guarded display conditions. Each W6 actor
point contains every contributing source ID; no actor-level confidence
radii are fabricated. Period dates are declared ISO ranges, not guessed
from labels. Plotted 2D coordinates use equal x/y axis scaling and do
not clip valid high-magnitude synthetic positions. Display alignment is
not high-dimensional language change or a political trajectory.

Without an explicitly checked **synthetic source-series selection**, W4
returns a full withheld read model with no coordinates. Real source
comparability and independent anchor stationarity remain unverified.

## Local reproducible QA

From the repository root:

    node --test research/integration/w2_w4_w6/test_w2_bridge.cjs
    node --test research/integration/w2_w4_w6/test_evidence_renderer.cjs
    python -m unittest research.integration.w2_w4_w6.test_w4_bridge -v
    node --test site/experimental/evidence-viz/tests.cjs

Install numeric dependencies from research/longitudinal/requirements.txt
first. To generate source-safe producer outputs:

    node research/integration/w2_w4_w6/run_synthetic.cjs /tmp/w2-fixture
    python -m research.integration.w2_w4_w6.run_synthetic --output /tmp/w4-fixture

Combine only generated W2 and W4 envelope/panel JSON in one local
directory; build_preview.cjs constructs a disposable source-verified browser
QA page there. This source tree is *not* registered in tools/build_pages.py
and is not included in the public site's asset allowlist.

The coordinator workflow .github/workflows/coord-w2-w4-evidence.yml
regenerates the native outputs, reruns upstream source/method/W6 tests,
builds a disposable local HTML page and launches real Chromium at
1440×900 and 390×844. It tests keyboard source inspection, safe SVG
and script-free HTML exports, page overflow, JavaScript errors, blocked
remote requests, and genuine synthetic screenshot captures.

The workflow uploads **only** synthetic screenshots and aggregate receipts.
Screenshots are not proof of substantive UN source evidence.

## Deferred coordinator gates

1. Review exact PR head, all changed paths, final native/Chromium CI and
   upstream statistical-result schema semantics.
2. Do **not** add new W2/W4 import controls to active research.html or
   change the Pages allowlist, release manifest, mirrored website or any
   private empirical source until a separate approved browser-publication
   integration change.
3. Before any real W2/W4 material, verify original bytes, source-group and
   country attribution, representation basis, selection/roster/anchor
   comparability, genre weighting, inference calibration and source
   licensing; keep all private row-level material outside public GitHub.
4. Continue withholding the 37 reserved transcripts and empirical
   geopolitical claims. No stability/affinity plot alone implies stance,
   alliance, influence or genuine historical movement.

**Status:** Engineering integration candidate only, no real-data release.
