# PCA and LSA comparison

Browser 1.5 adds uncentered truncated SVD / latent semantic analysis (LSA) to
the existing PCA → k-means → UMAP workflow. The comparison uses identical
filtered, deduplicated source passages and preserves the current default PCA
fit. It does not change frozen D1 outputs or reviewed-data publication gates.

## Use

1. Open the [workspace](https://lystadjs.github.io/un/transcript-agent/#analyze).
2. Set the topic (or leave blank for all passages), dates, region and meeting scope.
3. Select **Text clusters**, then choose **LSA** or **Compare PCA and LSA** under
   **Text representation**. PCA remains the default.
4. Use the same retained dimension count and `k` for both representations. Enable
   **Assess cluster stability** to evaluate identical group samples under each.
5. Inspect the comparison table, source-linked maps, membership correspondence,
   changed nearest neighbors and each representation's full result.
6. Download the HTML, analysis JSON, cluster CSV or consensus pair CSV. Files stay
   local. A comparison takes longer because it fits both representations and,
   when selected, both sets of resamples. Cancel terminates the worker.

## Representation and fitting

Both methods use the same sparse TF-IDF vectors: fixed token/stop-word filtering,
sublinear term frequency, smoothed IDF and L2 normalization. Zero vectors are
excluded with their source IDs. All date, region, language, meeting scope,
topic and deduplication rules run before this analysis. Limits remain 600
included passages, 2–50 requested components and 2–12 clusters, with `k` smaller
than the usable passage count. No silent sampling or vocabulary truncation occurs.

**PCA** centers features and retains leading components of the centered matrix.
Its numerical solver, centering, component scaling and clustering results remain
unchanged. **LSA** retains leading singular triplets of the uncentered TF-IDF
matrix `X`. Scores are `U_k S_k = X V_k`; they are not subsequently normalized
or whitened. In both cases, Euclidean k-means uses all retained scores, ten
seeded k-means++ starts and the lowest-inertia converged non-empty fit. UMAP
uses those same scores, never supplies labels to its fit, and never determines
cluster membership.

Within the browser bound, LSA computes the symmetric eigendecomposition of
`X Xᵀ`, then retains the requested leading positive eigenpairs. This is an exact
Gram-based truncated SVD up to floating-point accuracy, not randomized SVD or a
large-corpus streaming implementation. It avoids a dense document-term matrix
but stores a dense passage-by-passage matrix; the 600-passage limit still matters.
`ml-matrix` 6.15.0 remains the numerical dependency. No package or server was added.

Numerical rank uses `max(1e-12, largest_eigenvalue * 1e-10)`; eigenvalues below
that positive tolerance are omitted. Material negative eigenvalues fail the
numerical check. Component counts are capped separately at each method's rank.
Signs orient the largest absolute document score positively. Equal singular
values can admit different bases; subspace geometry is the invariant object.

LSA exports singular values and three separate quantities:

- **Uncentered energy retained:** `sum(singular_values²) / ||X||²_F`. This includes
  the corpus mean profile and is not the PCA explained-variance percentage.
- **Centered variance retained:** the sum of centered score variances divided
  by total centered TF-IDF variance. This uses the same denominator concept as
  PCA and appears in the comparison table. If the input has no centered
  variation, the quantity is null, not a perfect score.
- **Relative reconstruction error:** `||X - X_k||_F / ||X||_F`, calculated from
  the omitted singular-value energy.

Component vocabulary lists the largest positive and negative loadings from
`V_k = Xᵀ (U_k S_k) / S_k²`, with weights. These describe numerical axes. Sign
orientation carries no stance interpretation, and components are not reviewed
topic labels. Cluster vocabulary remains mean TF-IDF and nearest-centroid examples.

## Comparison and visual checks

PCA and LSA use the same requested dimensions, `k`, ten-start protocol and seeds.
Requested dimensions may exceed one method's available rank; actual dimensions
are displayed. Cluster correspondence counts passages shared by each pair of
groups. Between-representation ARI compares partitions without equating their
numeric labels. No automatic preferred method or substantive validity threshold
is selected. Silhouette measures separation within each representation; values
from different geometries are descriptive and do not prove a better model.

Both overview UMAP maps use **PCA reference colors**, so a passage keeps its
color while its display changes. The LSA overview is therefore not colored by
LSA assignments. Individual result sections show each fit's own assignments.
Layouts have separate axes/orientations and equal unit scales within each map;
islands and gaps do not establish diplomatic separation or coordination.

Neighborhood diagnostics use `q = min(10, floor((n-1)/2))`, so `1 <= q < n/2`:

- **Neighbor overlap:** fraction of each passage's original `q` neighbors retained,
  averaged over passages.
- **Trustworthiness:** penalizes introduced neighbors according to their ranks
  in the original geometry.
- **Continuity:** applies the same rank penalty to neighbors lost by reduction.

For each passage, rank other passages by squared Euclidean distance rounded to
12 decimal places, breaking ties by input row order. TF-IDF is L2-normalized, so
its Euclidean neighbor order is equivalent to cosine order apart from numerical
ties. The rank penalty normalization is `2 / (n*q*(2*n-3*q-1))`.

The report distinguishes **TF-IDF → retained representation** from **retained
representation → UMAP**. Values range from 0 to 1, with higher values preserving
more local geometry. They are not semantic accuracy, reviewed relevance or
confidence scores. The comparison separately reports PCA/LSA neighbor overlap
and up to ten passages with the lowest overlap, linked to both neighbor sets.
Every passage's neighbor IDs remain in JSON. Choices of `q`, retained dimensions,
tokenization and source composition remain consequential assumptions.

## Paired stability

The [grouped subsampling protocol](CLUSTER_STABILITY.md) refits TF-IDF and the
chosen representation in every sample. PCA and LSA use identical group subsets,
passage ordering and k-means seeds. Rank and convergence can still differ; each
fit retains its own failure record and denominators. The paired table includes
only samples that fitted successfully under both methods, alongside the eligible
sample counts for each method. Each resample ARI compares against that method's
own full-data reference; their difference does not estimate superiority or
provide a confidence interval. UMAP remains excluded from resampling.

## Data contracts

The additive `un.text-clusters.v1` contract retains the previous PCA fields:

- `representation` identifies `pca` or `lsa`; metadata and point scores use the
  matching `pca` or `lsa` key. LSA is never exported under a misleading PCA key.
- `fidelity.representation` and `fidelity.display` store metric definitions,
  neighbor counts, summary measures and per-passage neighbor IDs/overlap.
- Comparison mode retains PCA at `methods.clusters` and adds
  `comparison.alternative` for the complete LSA fit, plus membership counts,
  between-fit ARI, neighbor comparisons and paired stability results. The
  comparison schema is `un.representation-comparison.v1`; `requested_parameters`
  preserves the comparison request while each fit has its own method parameter.
- Stability adds `representation`; attempts record `pca_components`/`pca_rank`
  or `lsa_components`/`lsa_rank`. LSA attempts also retain uncentered energy.
- PCA-only CSV retains its existing headers. LSA-only coordinate columns use
  `LS1`, `LS2`, etc. Comparison cluster CSV has one row per representation and
  passage, a `representation` column, and generic `D1`, `D2`, etc. Shorter-rank
  score arrays are padded with blanks, never invented zeros.
- LSA and comparison consensus CSVs include a `representation` column so pairs
  cannot be mixed silently. The PCA-only consensus CSV retains its old headers.
- Fewer than four usable passages, no usable variation, insufficient groups or
  failed clustering/stability yield explicit reasons. A comparison can retain a
  valid individual result while withholding comparison metrics if the other fails.

The standalone HTML includes the plots, comparisons, source links and collapsible
details without scripts. Changing controls disables exports until another run.

## Validation and observed limits

Run the normal browser-analysis, clustering and stability suites, then:

```sh
node tools/test_browser_lsa.cjs
python tools/check_lsa_reference.py saved-corpus.json
node tools/test_browser_lsa_ui.cjs http://127.0.0.1:8785/ saved-corpus.json qa-output
python tools/check_stability_reference.py qa-output/analysis.json pca
python tools/check_stability_reference.py qa-output/analysis.json lsa
```

Serve `site/` locally for UI acceptance. The browser test accepts existing
Playwright/Edge through `PLAYWRIGHT_MODULE` and `BROWSER_PATH`. Independent
references use NumPy and scikit-learn; none is required by website visitors.

Hand calculations distinguish mean energy from centered variance and check
rank, full-space geometry, loadings, ARI and neighborhood penalties. A separate
NumPy full-SVD reference on 72 public passages (6,894 terms) agreed with LSA
retained-space squared distances to below 8.6e-14 and with signed loadings to
below 8.8e-14. Trustworthiness and continuity agree with scikit-learn on an
untied test geometry. Paired resampling, unchanged PCA fitting, determinism,
zero vectors, low-rank/small samples, UMAP independence and cancellation are tested.

Full browser acceptance used 458 usable September 22–28 General Debate passages,
with 20 components, four clusters and 30 matched meeting resamples per method:

| Measure | PCA | LSA |
|---|---:|---:|
| Centered TF-IDF variance retained | 24.4% | 24.1% |
| Original ten-neighbor overlap | 38.5% | 38.1% |
| Silhouette in the fitted representation | 0.412 | 0.405 |
| Mean resampling ARI | 0.959 | 0.961 |

Between-fit cluster ARI was 0.975; PCA/LSA neighbor overlap was 93.8%. These
results show similar fitted partitions on this collection, not external
validity. The much lower overlap with original TF-IDF neighborhoods warrants
source inspection and dimension sensitivity checks before decision use. LSA's
uncentered energy was 30.3%, reported separately from its 24.1% centered variance.

Python independently reproduced all 104,653 consensus pair counts for each
method and all resample ARI/Jaccard scores to numerical precision. Browser
acceptance also checked standalone LSA against comparison LSA, shared reference
colors, source links, HTML/JSON/CSV exports, stale controls, second-fit cancellation,
and desktop/mobile layouts. See [the validation record](browser-lsa-validation.json).

**Next implementation:** PAM and hierarchical clustering under the same corpus,
representation and evidence contracts. Keep representation choices explicit
when comparing those clustering methods.

Primary references: [Truncated SVD / LSA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.TruncatedSVD.html)
and [trustworthiness](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.trustworthiness.html).
