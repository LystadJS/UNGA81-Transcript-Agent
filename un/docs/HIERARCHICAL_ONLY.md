# Hierarchical clustering only — M07 implementation

Release: **2.4.0-d1-hc-only**. Parent: the complete 2.3.0-d1-i2 release. The incomplete earlier 2.4/PAM attempts are not its implementation baseline.

## Scope and publication

M07 is the only newly implemented D1 adapter. M01, M02, M05 and M06 remain; M09/PAM is not registered or executed. All 42 methods and 133 original prerequisites are still accounted for. The original D1 method registry remains unchanged.

The email still contains exactly O1–O5 plus region-grouped country summaries. M07 cannot generate a ready packet, a new section, cluster outlines on PCA, movement, network changes or a political-bloc claim. The new dendrogram and diagnostics are **audit-only**, even if the engineering screens pass. Independent empirical validation and a separately implemented source-bound publication contract are still required for release. Editing a Boolean is not a release mechanism.

## Input and geometry

The adapter consumes the verified `audit/analytics/artifacts/M02.rds` object. Every retained TF-IDF term is used; it does not cluster PCA, PCoA or UMAP coordinates. Tokenization, vocabulary, IDF and equal-statement country pooling remain the exact I2 implementation. Reference identity, current snapshot, source/version metadata and event/availability cutoffs are retained in M07.

For nonzero L2-normalized country vectors, distance is

```
d(i,j) = sqrt(||x_i||² + ||x_j||² - 2 x_i' x_j)
       = sqrt(2 * (1 - cosine(i,j)))
```

Distances are constructed from the full sparse-vector Gram matrix. Tiny floating-point negative squared distances are clipped to zero within tolerance; material violations are rejected. Country identifiers are sorted before fitting, making ties deterministic for a fixed runtime. Zero vectors are excluded with a recorded reason, never treated as neutral, absent, zero-distance neighbors, or assigned to a cluster. Missing contributing statements and cross-country duplicate text/vector observations fail separate quality screens. Completely coincident data and too few usable observations produce explicit non-delivery.

There is no daily refitting of vocabulary/IDF. The hierarchy itself is a **cross-sectional fit to the current available roster**. New countries can change its tree and labels. Cluster numbers are local labels, not persistent states. No out-of-sample hierarchical classifier or historical cluster correspondence is claimed.

## Candidate set and selection

`stats::hclust` fits average linkage as the predeclared primary hierarchy. Complete linkage and `ward.D2` are hierarchical sensitivity alternatives. Ward.D2 receives ordinary Euclidean distances, not pre-squared distances; R applies its own squared-distance update.

All valid k in **2–6**, with k < n, are retained. Each cut receives country assignments, cluster sizes, individual and average silhouette widths from `cluster::silhouette`, and a descriptive cophenetic correlation. The primary audit cut maximizes mean silhouette among average-linkage cuts with minimum cluster size 3 and maximum cluster share 0.85. Exact score ties select smaller k. When none meets the size screen, the highest-silhouette average cut remains an explicitly unqualified audit cut; a challenger is not silently promoted.

This is within-sample descriptive selection, not an estimate of the true number of diplomatic coalitions. Linkage sensitivity is reported at the same selected k using adjusted Rand agreement. Agreement between related algorithms is not independent corroboration.

## Conditional stability design

Production policy: **100 subsets**, each containing `floor(0.8*n)` countries sampled **without replacement**, with seed 20260925 and fixed R RNG kinds. The original caller's RNG state is restored. The same subset plan is used for every linkage and k. A single-country sample is never interpreted as independent textual replication.

Vocabulary and IDF stay frozen. Each original candidate is compared with a freshly fitted hierarchy/cut on each subset at that candidate's fixed k. Selection of k is not repeated inside the subset: this assesses the selected partition conditional on the declared cut, not unconditional model-selection uncertainty.

- **Partition agreement:** adjusted Rand index (ARI) between the full-data assignment restricted to sampled countries and the subset assignment. This is invariant to cluster labels. Degenerate identical pair partitions return 1; fewer than two comparable observations return undefined.
- **Clusterwise overlap:** for each original cluster, restrict its membership to the sampled countries and find the maximum Jaccard overlap with a subset cluster. Fewer than two retained original members is **not evaluable**, not zero or perfect stability.
- **Dissolution/recovery:** count evaluable replicates with Jaccard <=0.50 / >=0.75. Exact denominator and excluded/failed opportunities are retained.
- **Pair coassignment:** conditional fraction of successful selected-primary subsets in which two sampled countries share a cluster. Pair-inclusion and coassignment counts are exported. Never-observed pairs are NA, not zero. This is not a posterior membership probability.

For the 39-country reference, 15 candidates × 100 subsets produce **1,500 planned candidate–replicate records**. Every fit failure or insufficient-support case retains a row and reason. A mean over available scores is accompanied by successful and evaluable fractions over **all planned repeats**; failure cannot disappear through `na.rm=TRUE`.

This tests sensitivity to deletion of countries from the observed roster. It is not a confidence interval, a p-value, independent-country sampling validation, robustness to transcript errors, or proof of semantic/geopolitical validity. The singleton diagnostic is deliberately unevaluable under the minimum-two-members rule.

## Frozen engineering screens

The policy was written and hashed before the source fit. It is stored in both `config/hierarchical_policy.json` and `design/D1-HC/hierarchical_policy.json`. A mismatch is rejected. No threshold was lowered to make the source example pass.

| Screen | Requirement |
|---|---|
| Coverage | Every contributing country/statement vector is nonzero |
| Duplicates | No cross-country exact text or feature duplicates |
| Provenance | Reference/current inputs are observed, not replay/engineering |
| Metadata | One declared English-language genre |
| Source quality | No retained source flags/collection errors |
| OOV | Maximum statement unknown-token fraction <=0.35 |
| Text support | At least 30 eligible tokens per statement |
| Cluster sizes | Minimum 3; maximum share 0.85 |
| Separation | Mean silhouette >=0.15 |
| Replicate delivery | 100% of selected-primary planned replicates yield finite ARI |
| Partition stability | Mean subset ARI >=0.75 |
| Cluster stability | Every cluster mean Jaccard >=0.75 |
| Evaluability | Every cluster evaluable in at least 80% of planned subsets |

These are engineering defaults, not calibrated semantic thresholds. They are recorded under M07's `cluster_stability` prerequisite with source/numerical evidence. A successful fit that fails the screens ends as `withheld_quality`, with the full artifact retained. A pass ends as `executed` but still `audit_only`. A dependency, data, resource or integrity failure is separately recorded; it is not a fitted result.

## Files and execution

- `R/11_hierarchical.R`: full-space distances, hierarchy, cut selection, silhouette, resampling, validation and exports.
- `R/19_hierarchical_accounting.R`: registered M07 execution, source-bound gate proofs and audit integration.
- `R/Figure_6_Hierarchical_Audit.R`: standalone deterministic dendrogram and diagnostic figure.
- `hierarchical_only.R`: execute just M07 against a hash-verified archived M02 object; never refits upstream models or calls an external service.
- `tests/run_hierarchical_tests.R`: numerical, failure-accounting, integrity and publication tests.

The daily entry point runs M07 after M02, regardless of whether the PCA/PCoA display gates pass. All source and feature bindings are independently revalidated. The artifact stores a content identity, the input hash, policy, source index, full trees/cuts, replicate plans/memberships/results, quality checks and runtime versions.

Outputs under `audit/hierarchical/` include `country_assignments.csv`, `candidates.csv`, `partitions.csv`, `cluster_stability.csv`, `resample_plan.csv`, `resample_ledger.csv`, `resample_memberships.csv`, `cluster_resample_jaccard.csv`, `linkage_sensitivity.csv`, `distance.csv`, `coassignment.csv`, pair counts, `quality_checks.csv` and `summary.json`. The full R object is `audit/analytics/artifacts/M07.rds`.

Whole-run `rebuild.R` reuses the saved M07 artifact, verifies it through recomputation, and rerenders the figure. It does not update history, refit upstream references, or reclassify a source using live AI. The legacy five audit figures remain separate and are not inserted into the email.

## Runtime and safety

Actual new dependencies: R `stats`, `cluster` and `Matrix`; graphics use R `graphics` and `grDevices`. No Python runtime is required. Source-backed hierarchy computation ran in R 4.6.1 with Matrix 1.7-5 and cluster 2.1-8.2. Package versions are recorded rather than guessed.

The pairwise bound is 250 countries / 62,500 matrix cells before dense construction. There is no all-passage distance matrix. Large-corpus or peak-memory performance is not certified. All RDS inputs must be trusted; hashes detect changes relative to a trusted manifest, not malicious replacement of both source and manifest. The model and its audit figure never send mail.

## Primary numerical references

R hclust: https://stat.ethz.ch/R-manual/R-devel/library/stats/html/hclust.html

R cluster silhouette: https://stat.ethz.ch/R-manual/R-devel/library/cluster/html/silhouette.html

Hennig's clusterwise-resampling documentation: https://search.r-project.org/CRAN/refmans/fpc/html/clusterboot.html

This is an explicit R-native subset-stability implementation, not a claim that `fpc::clusterboot` or PAM was executed. The exact source code, policy and tests define the implementation.
