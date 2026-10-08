# Evidence visualization suite (W6)

**Status:** Synthetic-only, engineering-only, unmerged integration candidate.
This directory is independent of the production browser, numerical kernels,
source selection, held-out evaluation, and public release gates.

## Demo and design

Open [index.html](index.html) locally. All scripts and styles are local.
The four charts are rendered from invented source IDs and synthetic numerical
outputs, not actual UN records. Nothing is fitted, collected, transmitted, or
interpreted as a government position.

1. **Consensus and stability** — unordered observation-pair SVG and keyboard
   table. The plotted value is the mean co-assignment rate across *eligible
   method families*, not a pooled successes/opportunities ratio. Each cell
   exposes the family-specific numerators, denominators, failed attempts, and
   supplied instability flags. Missing pair record, zero-opportunity pair,
   observed zero, and excluded diagonal are different.
2. **Country × latent theme** — normalized NMF component-share numerator over
   the declared eligible country weight; observed source count and source IDs
   are preserved. Unknown attribution remains unassigned rather than
   redistributed. Missing/withheld is not plotted as a zero. These values
   describe linguistic component usage, **not political support or stance**.
3. **Discourse network** — an explicit cosine metric, fixed-representation
   threshold and pair-eligibility denominator determine an undirected edge.
   Duplicate/agenda sensitivity and connected-component sizes are visible.
   Node positions are **deterministic illustration**, not fitted space or
   inter-actor geographic distance; similarity does not imply alliance.
4. **Longitudinal latent movement** — already aligned actor-period coordinates
   and descriptive uncertainty radii. A period failing anchor-count, rank,
   degeneracy or selection-comparability checks is withheld from the common
   axes, **even when period-specific coordinates exist**. Lines are drawn
   only between adjacent comparable periods with matched, observed actors.
   Arrivals, departures, incomplete rosters and missing periods are explicit.

SVG exports embed descriptive titles and text labels. HTML heatmap cells and
tables expose numerators, denominators and source-linked metadata through
native buttons, keyboard focus and an accessible live inspector. The source
ledger lists original IDs, hashes in the envelope, source status, JSON
pointers and reviewed status. **Synthetic links are intentionally disabled**:
source URLs are null and local synthetic JSON pointers are displayed. Static
HTML exports omit executable scripts, retain the ledger, and label
interactivity as unavailable.

## API: additive, no model changes

The standalone UMD module exports these functions:

    const bundle = UNEvidenceFixture.fixture();
    const views = UNEvidenceViz.mount(container, bundle.envelope, bundle.panels);
    const one = UNEvidenceViz.renderPanel(bundle.envelope, bundle.panels[0]);
    const svg = one.svg;
    const staticHtml = UNEvidenceViz.htmlDocument(one);

The authority for the observation population and model records is the v1
interchange in [docs/parallel-work/INTERCHANGE_V1.md](../../../docs/parallel-work/INTERCHANGE_V1.md)
and its machine-readable schema. The prototype accepts only the exact v1
schema version family, publication_eligible false, evaluation_role
engineering_only, and a synthetic producer/split. No public browser adapter
for private development evidence is implemented; that requires separate
approved statistical and privacy gates.

Every view panel requires:

| Property | Contract |
| --- | --- |
| kind, status, reason | One of the four types; ready, empty, failed or withheld; reason required unless ready |
| measure | Full measurement definition |
| identity | Exact upstream source schema, source hash basis/hash, selection hash, unit, weighting, representation ID/version |
| identity.observation_refs | Exact ID plus text SHA-256 for all reference observations |
| coverage | Frame, eligible, included, excluded, and missing counts (not assumed disjoint) |
| warnings | Explicit list, including limitations and unavailable diagnostics |

The panel-specific additions are as follows:

| View | Validated fields |
| --- | --- |
| consensus | observation_ids; pairs with a, b, families (family, together, eligible, failed), missing_reason, unstable |
| country-theme | countries; components (id, label); unattributed_count; cells (country, component, status, weighted_sum, weight_total, evidence_count, observation_ids, missing_reason) |
| network | graph (threshold, metric, selection_rule); nodes (id, label, observation_ids, affiliation_status); edges (from, to, strength, eligible_pairs, duplicate_sensitivity, agenda_sensitivity, observation_ids) |
| longitudinal | periods; alignments (from, to, anchors, reference_basis, selection_comparability, status, rank_ok, degeneracy_ok, uncertainty_status); actors and positions (period, status, xy, radius, n, observation_ids, reason) |

Unrecognized ID/hash pairs, mismatched source hash basis or selection hash,
incompatible populations, invalid denominators, duplicate pairs and
nonconforming alignment ledgers **fail closed**. The rendering layer never
recalculates PCA, LSA, NMF, co-assignment, a graph embedding, or an alignment.

Missing and excluded indicators may overlap: a source listed as unavailable
is excluded from the eligible analysis and also counts toward the missing
source inventory. Do not treat the five coverage labels as a disjoint
five-way partition. Preserve the original full inventory separately from the
selected analytic population.

## Tests and reproducible screenshot generation

    node --test site/experimental/evidence-viz/tests.cjs

For desktop and mobile Chromium checks:

    python -m pip install playwright
    python -m playwright install chromium
    python site/experimental/evidence-viz/browser_smoke.py

The browser test verifies 1440 × 900 desktop and 390 × 844 mobile,
keyboard Tab/Enter inspection, accessibility of evidence details,
script-free HTML/SVG download and XML parsing, zero-eligible populations,
failed/withheld render states, viewport overflow and uncaught browser errors.
It saves two full screenshots and eight per-chart PNGs to
previews/browser/ by default. Source fixtures and offline exports are
deterministic and do not use a random seed.

Checked-in [previews](previews/) include four directly rendered SVG charts
and two synthesized desktop/mobile composite SVG layouts. These are
**illustrative vectors, not Chromium screenshots or browser-validated views**.
Actual responsive PNG screenshots are not yet captured. Report browser tests
as passed **only** when the Chromium script runs and its output is inspected.

## Upstream and integration dependencies

| Owner | Required published input or decision |
| --- | --- |
| W1 | Source eligibility and provenance, source-group dependence, duplicate/agenda sensitivity and non-delivery ledger |
| W2 | Family-balanced consensus pair counts, missing pairs, failures and assignment uncertainty |
| W3 | Valid graph metrics/affinities, explicit thresholds and sensitivity diagnostics |
| W4 | Frozen common representation, anchor and rank checks, actor roster and alignment uncertainty |
| W5 | Browser result acceptance, version replay, resource and cancellation contract |
| W7 | Diplomacy-facing labels, accessible inspection patterns, caution language |
| Coordinator | Approve interfaces, bind actual validated inputs, modify shared entry points, run final tests/deployment and website mirroring |

**Ownership exception:** the user explicitly requested
site/experimental/evidence-viz/ instead of the reserved W6 path
site/parallel/w06-visualization/. The coordinator should approve the
exception or relocate this subtree in a coordinator-owned integration PR
before merging. No existing site asset, global style, page entry point,
release checksum, shared contract or reserved input was edited.

**Scientific limitations:** Fixture tests demonstrate implementation
guardrails only. No evidence of valid themes, statistical significance,
geopolitical alignment, government policy, clustering calibration or
change over time is asserted. Real-source adapters remain blocked pending
upstream source, model, privacy and uncertainty validation.

## Source-complete excluded/missing-frame repair (W3/W5 compatibility)

The synthetic inventory contains 11 source identities: 10 eligible and one unavailable.
Each model now has 11 result rows, including a distinct 'excluded' result
for the unavailable source, with cluster null and explicit missing reason.
The text SHA of an unavailable source remains null. Each model has
assigned + unassigned + not_fitted = 10 and excluded = 1.
Missing/unavailable is a subset of excluded, not a disjoint third category.

New negative tests reject dropped, duplicated, falsely assigned and
miscounted results and panel coverage. The authoritative W1/W3/W5
un.parallel-analysis.v1 frame and status contract remains unchanged.

For Chromium using an already installed browser binary:

    python site/experimental/evidence-viz/browser_smoke.py --browser-path /usr/bin/google-chrome --outdir /tmp/w6-browser-qa

Only invented synthetic sources may enter this public research prototype;
browser screenshots are engineering QA, not diplomatic findings.
