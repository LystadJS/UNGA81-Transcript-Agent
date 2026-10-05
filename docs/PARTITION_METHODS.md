# PAM and hierarchical clustering

Browser 1.6 adds PAM first, then agglomerative hierarchical clustering to the
existing PCA/LSA workflow. All three clustering methods use the same retained,
unwhitened scores and Euclidean geometry. Changing only the clustering method
leaves the representation, neighborhood diagnostics and UMAP coordinates unchanged.
The frozen country-level R adapters and daily publication gates remain separate.

## Use

1. Open the [workspace](https://lystadjs.github.io/un/transcript-agent/#analyze).
2. Choose topic, inclusive dates, meeting scope and region, or import a saved collection.
3. Select **Text clusters and stability**. Choose PCA, LSA or **Compare PCA and LSA**.
4. Choose **PAM — representative passages** or **Hierarchical — nested groups**.
   For hierarchical clustering, choose Ward or average linkage.
5. Set retained components and `k` under **Clustering settings**. Enable
   **Assess cluster stability** for the same whole-group sensitivity checks.
6. Generate the report. Inspect cluster sizes, source passages, silhouette,
   stability and coverage. Hierarchical results also include an overview and
   full passage dendrogram; both preserve source links.
7. Download the HTML, JSON, cluster CSV, consensus CSV, and, for hierarchical
   results, **Hierarchy CSV**. A changed setting disables exports until rerun.

The browser bound remains 600 selected passages, with no silent sampling.
Zero-term passages are explicitly excluded. Each fit requires at least four
usable passages and `2 ≤ k < usable count`; requested components are capped at
the numerical rank. All fitting runs in a cancellable worker. Comparison means
PCA versus LSA under the **same selected algorithm**, not automatic model selection.

## PAM

PAM selects actual observations as medoids. BUILD greedily reduces total Euclidean
distance to the selected medoids. SWAP evaluates every possible single medoid
replacement and applies the greatest improving change. Shared nearest/second-nearest
distance calculations accelerate evaluation without restricting the swap search.
The exported objective is the **sum of unsquared Euclidean distances**, with the
mean also recorded. It must not be compared numerically with k-means inertia.

Stopping requires no improving swap larger than `1e-12 × max(1, current total)`.
At most 300 swaps are allowed; exhausting the bound with an available improvement
withholds the partition. Insufficient distinct score locations also withhold PAM
with a reason. No fallback to k-means occurs. A fitted result is a local single-swap
optimum, not a guarantee of the globally best set of medoids.

The initialization is deterministic. Exact candidate ties use source row order,
then current medoid row order for swaps; medoids and cluster IDs are ordered by
source row index. The cluster card shows the actual medoid and its source.
JSON retains initial/final medoid indexes, final source IDs, objective history,
swap count and tolerance. No clustering seed is consumed.

## Hierarchical clustering

Each passage starts as one group. The closest active pair merges at every step;
the complete `n-1` merge record is retained. Pair ties use ascending node indexes.

| Linkage | Merge criterion | Exported height |
| --- | --- | --- |
| Ward | Smallest increase in within-group sum of squares | Square root of twice that increase |
| Average | Mean Euclidean distance across the two groups | That mean distance |

Ward's updates use squared Euclidean distances internally, following the Ward.D2 /
SciPy Ward convention. The input is Euclidean retained scores, never cosine
dissimilarity or UMAP coordinates. Average linkage weights the two child groups
by their actual sizes. Neither method uses random initialization.

The selected partition is the exact `k` groups present after `n-k` merges.
Cluster numbers follow the earliest source row in each group. Tied boundary
heights receive a visible warning: a scalar height threshold may not recover
exactly this cut. Duplicate coordinates can produce zero-height merges.
The report's source example is the included passage nearest that group's centroid;
it is an illustrative exemplar, not a PAM medoid or a reviewed label.

The overview collapses each selected cluster to one branch endpoint at its last
merge height. The full tree retains every source-linked leaf and scrolls within
the report. Vertical leaf order is a reading order, not another score. JSON and
Hierarchy CSV preserve all leaves, child indexes, heights and group sizes.

## Shared stability and audit

The [grouped stability protocol](CLUSTER_STABILITY.md) is unchanged: default 30
repetitions, 80% of meeting groups, seed 31415; at least one group is omitted.
Each sample refits vocabulary, IDF and PCA/LSA before refitting the selected
clustering method with the original `k` and linkage. Source order is preserved.
PAM records sample medoids, objective and swap count; hierarchical runs record
linkage, cut height, next merge height and tie status. Deterministic methods have
no spurious random-start agreement or k-means seed fields.

ARI and cluster-wise Jaccard compare only shared observations. Failed fits do
not enter agreement or consensus denominators. The consensus view, exact pair
counts and passage review leads are identical in definition across algorithms.
PCA/LSA comparison uses exactly the same group schedule and retains failures.
No UMAP is fitted inside the resampling loop.

`methods.clusters` retains schema `un.text-clusters.v1` with additive
`algorithm` and common `clustering` metadata. Method-specific diagnostics are
under `kmeans`, `pam` or `hierarchical` only. Existing default k-means CSV columns
remain supported. New-method cluster/consensus CSVs explicitly include
representation, algorithm and linkage; cluster CSV also marks representatives.
Hierarchy indexes are zero-based: leaves `0..n-1` match `points` / `leaf_ids`;
internal nodes `n..2n-2` identify successive merges. `cut_nodes` correspond to
one-based cluster labels. Every leaf row in Hierarchy CSV retains its source URL.

## Validation

Run the existing browser suites plus:

```sh
node tools/test_browser_partitions.cjs
node tools/test_browser_partitions_ui.cjs http://127.0.0.1:8786/ corpus.json qa-output
python tools/check_partition_reference.py qa-output/pam/analysis.json /path/to/Rscript
python tools/check_partition_reference.py qa-output/ward/analysis.json
python tools/check_partition_reference.py qa-output/average/analysis.json
python tools/check_stability_reference.py qa-output/pam/analysis.json pca
```

The Node suite checks PAM against an independent exhaustive BUILD/SWAP reference
on 40 generated datasets, decreasing objectives and local optimality. It checks
hand-calculated Ward/average heights, Ward's SSE relation, nested cuts, ties,
invalid inputs, cancellation, medoid/source mapping, full sample refits, identical
group schedules, unchanged coordinates and report rendering under both representations.
The optional reference script compares exported scores with R `cluster::pam`
and SciPy hierarchical linkage, independently recomputes silhouette, and checks
every possible medoid swap and hierarchical cut membership. Tied data can yield
alternative optima/trees across implementations; discrepancies require inspection.

Browser acceptance imports a saved public corpus locally, runs PAM, Ward and
average under both representations with 30 samples each, checks all exports,
source links, stale settings, cancellation and desktop/mobile layout. Numerical
and interface validation records accompany this guide when executed. These are
engineering checks, not evidence of substantive or predictive validity.

The [fresh validation record](browser-partitions-validation.json) uses the saved
September 22–28 General Debate corpus: 460 source segments, 458 nonzero vectors,
20 retained components, `k=4`, six meeting groups and 30 samples per fit.
All **180 sampled fits** completed across PAM, Ward and average under PCA/LSA.
R and browser PAM objectives/partitions agreed; SciPy Ward/average partitions
agreed exactly and merge heights differed by at most `1.78e-15`. Independent
reconstruction matched all **104,653 pair counts per fit**, across six fits.
Existing k-means scores, UMAP coordinates, labels, diagnostics, sample logs and
consensus exactly matched the saved 1.5 acceptance run. All five Node suites,
browser exports, cancellation and desktop/mobile checks passed.

| Method | PCA mean stability ARI | LSA mean stability ARI | PCA largest group | LSA largest group |
| --- | ---: | ---: | ---: | ---: |
| PAM | 0.834 | 0.836 | 266/458 | 266/458 |
| Ward | 0.963 | 0.902 | 196/458 | 196/458 |
| Average | 0.937 | 0.546 | 445/458 | 435/458 |

Average linkage illustrates why agreement alone is insufficient: a high PCA
stability score accompanies a group containing 97.2% of passages. The report
flags fits with at least 90% in one group as a descriptive review prompt, not a
validated rejection threshold. PAM examples also expose procedural introductions
in several clusters. Source review is necessary before assigning substantive labels.

## Interpretation and next step

Stable text groups can reflect procedural language, source segmentation, repeated
speakers or common transcription patterns. Medoids are representative of geometry,
not representative national positions. Silhouette and stability do not certify
political categories, causal effects or coordination. With few meeting groups,
many resamples repeat the same omissions. Inspect source passages and compare
`k` and retained dimensions before interpreting differences between methods.

**Implemented in 1.7:** [HDBSCAN](HDBSCAN.md) with explicit unassigned passages,
density-setting sensitivity and stability accounting that never treats shared
noise labels as co-clustering. The [source/settings audit](CLUSTER_SENSITIVITY.md)
compares 96 fixed-count settings and 36 density settings. Review source-type
inclusion before assigning themes. NMF and regularized Gaussian mixtures follow.

Algorithm references: [R cluster PAM](https://stat.ethz.ch/R-manual/R-devel/library/cluster/html/pam.html)
and [SciPy hierarchical linkage](https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.linkage.html).
