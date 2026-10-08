# Historical UN original-source validation — metadata checkpoint

**Date:** 8 October 2026.  **Status:** original-PV metadata independently reconciled; W1 source-bound observation execution, W4 empirical modeling, inference, and publication remain **WITHHELD**.

## Independent source-reconciliation result

I rechecked the *indexed extraction* of the user's P2 original-source review workbook against the already published P2 aggregate.  This is a new examination of real-source **metadata**, not a replay of privately retained original PDF bytes or Harvard speech text.  The full workbook bytes, original UN-PV PDFs, and private full-speech exports are **not available as materializable inputs in this chat**, so they cannot be represented as freshly verified source text or byte integrity.  The public, row-free [audit receipt](W4_P2_INDEXED_SOURCE_AUDIT_2026-10-08.json) records 24 completed consistency checks.

| Verified worksheet property | New independent metadata result | Interpretive restriction |
| --- | ---: | --- |
| Original UN-PV manifest | 63 distinct official A/session/PV symbols, 63 distinct shaped SHA-256 digests, 63 `documents.un.org` HTTPS links | These are the **declared local** PDF digests, not publisher-signed hashes; files not re-opened |
| Total recorded original pages and bytes | 3,370 pages, 53,218,960 bytes | Worksheet totals; original PDF bytes not independently replayed |
| 2016–2023 strong full-speech/original-PV matches | 840 | Previously established sampled full-speech comparisons; not a new text audit |
| 2024 source mismatch | 94 partial/variant, 50 insufficient, **0 strong** | **Do not pool** 2024/2025 text methods into a frozen 2016–2023 representation |
| Historical source inventory gaps | 752 original-PV candidate rows not yet independently reviewed | Gaps are **missing**, not speeches that did not happen |
| W4 matched-country candidate | 99 unique recorded affiliations, 523 source-corroborated slots of 792 | Nonrandom selection, recorded affiliation ≠ authenticated speaker or policy |
| Eligible epoch cells | 252 in 2016–2019; 271 in 2020–2023 | These cells are candidates for review; they are not validated fitted feature vectors |
| Remaining country×year cells | 269, all complement each 2016–2023 year exactly | Do not impute zero, invent text, or delete these cells |
| Priority source flags | 14 workbook source-label corroborations, 3 index omissions, 1 Harvard corpus omission, 6 outstanding | Provisional source corroboration is **not** owner/human identity adjudication |
| Negative original-PV control | 96 wrong-meeting comparisons; maximum 7-token overlap 2.793%, 0 above 90% strong threshold | Source-document specificity check, **not** null-calibrated cluster significance |
| W4 worksheet model-eligibility labels | **0/99 eligible** | Correct until W1 dependence, frozen representation, source linkage and speaker-role gates pass |

The independent check found **no arithmetic, uniqueness, source-domain, year-slot or status-count discrepancy** in the indexed metadata.  This does not imply the official transcripts are complete or that the selected sample is representative.

## Reusable private-only verifier

`research/integration/p2_source_readiness.py` checks the published aggregate locally without fetching new material.  To rerun the meaningful **private source** checks, export the six named workbook sheets as CSV to a private directory outside this public checkout:

- `Annual Verification.csv`
- `Original PDF Manifest.csv`
- `Stratified 120.csv`
- `W4 Candidate 99.csv`
- `Wrong PV Controls.csv`
- `Priority 24.csv`

Then run:

```sh
python -m research.integration.p2_source_readiness --private-csv-dir /private/P2/worksheets --private-output /private/P2/metadata-audit.json
```

This checks full country×year slot partitioning, source counts and status ledgers, original PV session/year symbols, uniqueness and locally recorded PDF SHA shapes/official links.  Only aggregate counters are emitted; source- and person-linked original rows are never written to public GitHub.  Passing this step **still does not reauthenticate the source document bytes**.

If the independently held original PDFs are available, create a **private** mapping JSON from each official `A/session/PV.number` symbol to the corresponding absolute, externally stored PDF path; add `--private-pdf-map /private/P2/paths.json`.  The verifier reads each PDF **only** for full-file SHA-256 and byte length; no PDF text is extracted, published, downloaded or used in a model.  It requires the same 63 official PVs and rejects other years, duplicate entries, wrong hostnames, broken source hashes and symlinked/public-checkout paths.

## W1 → W4 empirical release gates (still closed)

1. Retain the entire **99 × 8 = 792** expected country-year inventory, with 523 source-corroborated cells and 269 explicitly unavailable/unreviewed cells.  Only validated observations enter eligible feature fitting; unavailable sources retain null text and separate exclusion reasons.
2. Construct an actual W1 `un.source-validation.frame.v1` from private *per-observation* text SHA-256, source SHA/hash basis, original PV meeting/source-family, representative country and separately reviewed speaker/role, original source span and exact observation ID.  A country-year workbook key alone is **not** a verified speech boundary or W1 input.
3. Pin and independently validate the full lexical vocabulary/IDF or MiniLM encoder/embedding cache and W4 high-dimensional representation **before** comparing epochs.  Audit dependence by the 55 original 2016–2023 source PV meetings; do not treat 523 country-year entries as 523 independent source trials.
4. Audit missingness, year/source format and speaker roster changes; exclude 2024–2025 by policy until genuine mixed-modality measurement invariance is separately demonstrated.
5. Fix W4's null-source inventory adapter and independently test exact SHA/selection/representation matches; run paired-source-family controls and only then pilot a *descriptive* real-source fit.  A future inferential calibration must be independently designed and accepted; no blanket cluster, national stance or geopolitical influence interpretation follows.

**Preserved:** `research/reference_tests/evaluation-lock.json`, original source/corpus hashes, 24 owner review decisions, O1–O5 gates, `site/**`, `un/**`, current website mirror, and **all 37 unopened October 5–6 2026 reserved meeting transcripts**.  No W4 worker code or P2 private data is added by this coordinator checkpoint.

**Result:** 24/24 independent worksheet **metadata** checks passed; direct original-PDF byte replay **NOT RUN this turn**; original speaker identity/frozen W1 representation **NOT RUN**; W4 empirical modeling **WITHHELD**.
