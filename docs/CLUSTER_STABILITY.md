# Cluster stability and consensus

Browser 1.4 adds the first method in the dimension-reduction and unsupervised
learning sequence: grouped subsampling with full representation refitting.
Browser 1.5 extends this protocol to LSA and paired PCA/LSA comparison; the
[comparison guide](LSA_COMPARISON.md) documents representation-specific fields.
It is an exploratory sensitivity assessment. Frozen D1 representations,
reviewed-model gates and daily publication behavior remain unchanged.

## Use

1. Open the [workspace](https://lystadjs.github.io/un/transcript-agent/#analyze).
2. Select dates, meeting scope and region. Leave Topic blank for all passages,
   or enter a topic to assess only its matching passages.
3. Select **Text clusters**, choose PCA, LSA or their comparison, then
   **Assess cluster stability**.
4. Choose **Meeting** (default) or **Recorded speaker affiliation**. The choice
   describes which passages must be omitted together, not a verified claim of
   independence. The latter also includes organizational/procedural affiliations.
5. Generate the report. Inspect Jaccard ranges, agreement and pair coverage,
   the consensus heatmap and the source-linked passages with low margins.
6. Download the HTML report, analysis JSON, cluster CSV or consensus pair CSV.
   Changing settings disables exports until another report is generated.

## Fixed protocol

- The original TF-IDF → PCA → k-means → UMAP fit remains the reference. Enabling
  stability does not change its coordinates, assignments, seeds or cluster terms.
- Default: 30 repetitions, 80% of groups retained, seed 31415. Repetitions may be
  10–100 and retained share 50–90%. The existing 600-passage bound applies. No
  additional passage sampling or vocabulary truncation occurs.
- Select groups uniformly **without replacement within each repetition**. The
  same group subset may recur across repetitions. Retain `ceil(fraction * G)`
  groups, capped at `G - 1`, and report the effective share. Require at least
  three groups. Within selected groups, retain every eligible unique passage
  and its original passage-level weight. This is subsampling, not a bootstrap
  with replacement and not equal weighting of groups.
- Meeting grouping uses a canonical `transcripts.un.org/.../asset/...` identifier,
  ignoring timestamp query parameters. Imported sources without that identifier
  use date + scope + normalized meeting title, with an explicit warning. Missing
  required meeting metadata withholds stability while retaining the base fit.
- Affiliation grouping uses the normalized recorded field. Unknown affiliations
  form one explicitly reported group. It does not infer speaker identity.
- Refit the vocabulary, smoothed IDF, sublinear TF and L2-normalized vectors on
  the selected records, including selected zero-term records in the IDF document
  count. Exclude zero vectors before reduction. Refit centered, unwhitened PCA
  or uncentered LSA using the requested component count capped at that sample's
  numerical rank. Comparison mode repeats the exact group schedule and k-means
  seeds under both representations, retaining both success/failure logs.
- Refit k-means using the reference `k`, ten seeded k-means++ starts, 300 iterations
  per start, and the lowest-inertia converged non-empty fit. Each repetition uses
  a recorded deterministic seed independent of UMAP. Insufficient rows, zero rank
  and unsuccessful fitting produce explicit skipped attempts. They never enter
  agreement or pair denominators. Worker termination cancels the entire operation.
- No UMAP is fitted during resampling. This assesses sensitivity to omitted
  groups and refitting, including optimization variation. It does not isolate
  each source of variation or automatically tune `k` or PCA dimensionality.

## Measures and interpretation

**Adjusted Rand index (ARI)** compares reference and resample assignments on
the passages actually retained. Cluster numbers need not match. ARI can be
negative; 1 denotes identical partitions up to label permutation.

**Cluster-wise Jaccard** compares a reference cluster, restricted to the sample,
with each fitted sample cluster and retains the largest intersection/union ratio.
Matches may be many-to-one. Samples retaining fewer than two members of a
reference cluster are unevaluable for that cluster. Export evaluable counts,
means, medians and observed minima/maxima. Ranges are not confidence intervals.

**Consensus** divides the number of successful joint samples assigning a pair
to the same cluster by the number of successful samples containing both passages.
Pairs never jointly observed have no rate, not rate zero. These co-assignment
values summarize the fitted samples; they are not probabilities of policy
agreement and do not create a new consensus partition.

The heatmap groups passage IDs into contiguous bins within reference clusters,
using all pairs. It pools numerator/denominator counts, rather than averaging
pair ratios. Gray cells have no observed pairs; single-passage diagonal cells
are also gray. The bin table identifies all constituent passages. Download the
pair CSV for unaggregated values. At mobile widths the entire heatmap fits the
viewport; the longer diagnostic tables can scroll within their containers.

The passage review list ranks up to ten passages by within-reference-cluster
co-assignment minus co-assignment with their strongest other reference cluster.
Both rates pool observed pair counts and omit the passage's self-comparison.
Inclusion and observed-peer counts accompany the ranking. Singleton or otherwise
unassessed passages retain null values and are explicitly counted as unranked.
Low margins are review leads, not verified errors or calibrated uncertainty.

**Limitations:** stability does not establish substantive validity, population
representativeness, independence, future performance, stance or coordination.
Source errors, procedural language, passage length and shared transcription
patterns can produce stable groups. Whole-group omission mitigates one source
of dependence; it cannot certify independent observations. With few groups,
additional repetitions mostly revisit existing omission patterns. Compare source
content and settings before interpreting the result. There is no automatic
pass/fail threshold or production-release decision.

## Export contract

`methods.clusters.stability` uses `un.cluster-stability.v1` and contains:

- Requested/effective parameters, reference IDs and labels, grouping keys with
  passage membership, warnings, attempted/successful counts and distinct subsets.
- Per-attempt retained group indexes, reference-point indexes, excluded IDs,
  vocabulary size, PCA rank/components/retained variance, k-means seed and
  diagnostics, ARI/Jaccard or a skipped reason. Resample `labels` are zero-based;
  reference cluster IDs and Jaccard matched-cluster IDs are one-based.
- Consensus counts in strict-lower-triangle order: for `i > j`, the packed index
  is `i*(i-1)/2+j`. Reference IDs define row order; per-point inclusion counts
  provide the diagonal separately. Counts remain integers. Ratios are derived.
- Per-passage within/alternative rates and margins. Missing comparisons remain
  null in JSON and blank in CSV. Fewer than two successful attempts withholds
  aggregate agreement summaries; attempt logs and pair counts remain inspectable.

The pair CSV includes every distinct unordered pair, both reference cluster IDs,
joint sample count, co-clustered count and derived rate. Existing cluster CSV
adds inclusion, peer coverage and consensus columns only for an assessed run.
The standalone HTML preserves visualizations and source links without scripts.

## Validation

```sh
node tools/test_browser_analysis.cjs
node tools/test_browser_clusters.cjs
node tools/test_browser_stability.cjs
```

The new tests cover independent contingency-table ARI and Jaccard examples,
exact pair denominators including never-observed pairs, intact group selection,
sample-specific vocabulary/PCA refits, reproducibility, unchanged reference
fits, UMAP independence, failed-fit accounting, grouping fallbacks, option bounds,
missing metadata, cancellation and the filtered analysis entry point.

Optional browser acceptance accepts an existing public saved corpus:

```sh
node tools/test_browser_stability_ui.cjs http://127.0.0.1:8784/ corpus.json qa-output
python tools/check_stability_reference.py qa-output/analysis.json
```

Serve `site/` locally first. The browser test uses Playwright (or an existing
runtime through `PLAYWRIGHT_MODULE` and `BROWSER_PATH`); the independent reference
check uses NumPy and scikit-learn. These are developer tools, not visitor
requirements. They neither collect new transcripts nor upload imported text.

The recorded acceptance used 458 nonzero vectors from the saved September 22–28
General Debate collection, grouped into six meeting assets. All 30 samples fitted;
rounding retained five meetings (83.3%), with six distinct omission patterns.
All 104,653 pairs were observed in 17–29 successful samples. Python reconstruction
matched every pair count; ARI/Jaccard differed by at most 1.12e-16. Browser checks
covered HTML/JSON/both CSV exports, source links, stale controls, cancellation
during resampling and desktop/mobile layout. See
[the validation record](browser-stability-validation.json). These are engineering
checks, not external validation of diplomatic categories.

## Implementation sequence

1. **Complete:** grouped resampling, Jaccard/ARI stability and consensus views.
2. **Complete:** truncated SVD / LSA comparison using the same corpus, source
   IDs, k-means settings and resampling protocol, plus neighborhood diagnostics.
3. **Next:** connect PAM and hierarchical clustering to the common comparison workflow.
4. Integrate and validate HDBSCAN, including unassigned passages and sensitivity.
5. Add NMF theme mixtures with source-linked components.
6. Add regularized Gaussian mixture models with model-based membership diagnostics.

Neighborhood overlap, trustworthiness and continuity now accompany representation
comparisons. Further display sensitivity checks, metric MDS, spectral
clustering, diffusion maps and historical change remain later work requiring
their own validation and, for historical inference, comparable source data.

Method references: [Hennig, cluster-wise stability](https://www.homepages.ucl.ac.uk/~ucakche/papers/clusta.pdf)
and [scikit-learn, adjusted Rand index](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.adjusted_rand_score.html).
