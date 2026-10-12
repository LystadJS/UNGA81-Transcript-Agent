# W1 → W2 source-group assignment uncertainty (coordinator)

**Release state:** engineering-only / synthetic-only / no active browser changes. This follows the accepted baseline adapter in coordinator PR #46 without changing its original source-read model.

## Method

The W1 native runner has an explicit retained-child option. Source-bound records are exported under **un.source-aware.group-refits.v1** and verified against the original W1 interchange envelope and actual native per-run labels. The producer stores every original observation ID/text SHA and a complete selected-source-group ledger; the adapter fills omitted eligible rows as not_fitted and retains source-unavailable/excluded inventory rows separately.

The coordinator grouped bridge derives sample-specific W2 hard-assignment models with immutable model/representation/seed replay identities. It keeps the original five baseline fits and includes every successful, skipped or failed child model as a **planned** fit record; zero hard labels are noise, not a genuine common cluster. The W1 family mapping is unchanged: k-means/PAM partition, Ward hierarchical, GMM mixture, HDBSCAN density. Each family retains equal planned weight, and repeated numerical seeds cannot buy another family vote.

W1 resampling is **without replacement**. One omitted meeting is leave_group_out; multiple omissions are group_subsample; no with-replacement bootstrap is estimated. Identical selected group sets across seeds share the same W2 resample ID. This gives a truthful denominator of *distinct sample selections*, while retaining numerical seed-specific fit records. Refit prevalence/sensitivity and cross-method weighted association remain separate from W1 ARI/AMI.

For each source-observation pair, W2 retains:

- coassigned_count and coassigned_weight (both have a common assigned cluster);
- assigned_both_count and assigned_both_weight (both assigned, regardless of their clusters);
- planned_count and planned_weight (all models scheduled, even skipped/failed);
- noise_pair_count, missing_pair_count, failed_fit_count and distinct contributing families.

The conditional co-assignment rate is numerator divided by **assigned-both weight**; assignment coverage divides assigned-both weight by **planned weight**. A pair with no assigned-both denominator is **null, not zero**.

For each distinct grouped source selection, W2 reconstructs an aggregate family-balanced conditional association. When at least three distinct, assessable leave-one-group-out selections exist, it reports empirical 5th–95th percentiles as **descriptive spread**. Group subsampling requires at least five distinct assessable selections. Every pair also reports total and assessable source-selection denominators; otherwise all percentiles are null and status is withheld. These are **not bootstrap confidence intervals**, significance tests, independent replication or policy-position estimates.

## Tested synthetic cohorts

- **Six source meetings:** 25 inventoried fictional records, 24 eligible, one explicitly unavailable; five original methods; 18 whole-meeting group samples per method, **90 actual child numerical fits** (all successful in the reference fixture), six distinct omitted-group designs, 276 off-diagonal uncertainty records, and 300 full pair records including diagonals. The W2 family weights are 0.25 each.
- **Ten source meetings:** a second synthetic cohort with grouped samples that exclude three meetings. The adapter labels them **group_subsample**, never leave_group_out or bootstrap, and applies the five-distinct-selection reporting minimum.
- **Two source meetings:** W1 correctly withholds resampling as insufficient; no child-fit labels, interval or implied certainty are fabricated.
- **Negative controls:** invalid source/text hashes, parent/meeting discrepancies, duplicate IDs, changed hard labels, altered seeds and source selection, invalid noise/abstention, private/holdout masquerading, forced failed child-fit denominator, and numerical-fit summary-only refusal.

## Reproduction and privacy

From repository root (Node 22):

~~~bash
node --test research/validation_framework/tests/test_group_refits.cjs
node --test research/integration/w1_w2/test-grouped-refits.cjs
node research/consensus/test_consensus.cjs
node research/integration/w1_w2/make_grouped_synthetic.cjs /tmp/new-w1-w2-grouped-synthetic
~~~

The synthetic exporter refuses in-repository output and existing directories. Its optional results are checksummed with SHA256.json and preserve full text-free source/model/pair ledgers; no original transcript text or source vectors are exported. The W1 runner retains child assignments only under a nonenumerable, opt-in memory property. The original W1 v1 interchange and W1 default exports remain unchanged.

**Limits:** W1 originally supports up to 600 eligible rows; this dense W2 consensus accepts at most 256. Retained child-fit opportunity cap: 120,000. No silent subsetting or unverified country-attribution inference. The 37 reserved October 5–6 transcripts and frozen O1–O5 protocol are not opened or changed. A source-dependence/null-calibration plan and authorized private development validation remain prerequisites for any empirical release.

## Outstanding integration boundaries

1. Original UN source-byte development verification and source-group exchangeability must be established before interpreting group stability substantively. Source-family/affiliation closure and between-meeting dependence require independent assessment.
2. Lexical/group representation transforms are refitted per source sample; this sidecar records a deterministic replay key, **not an authenticated saved transformation matrix**. A separate persisted-matrix audit may be required for more stringent replay claims.
3. W6 currently displays a different simple family-average metric. The W2/W4 weighted native panel work in other coordinator PRs is separate; do not silently render these W2 output fractions using an incompatible W6 formula.
4. No browser or D1 publication integration occurs in this PR; it is a research read-model capability for later reviewed consumer wiring.
