# HDBSCAN with explicit unassigned passages

Browser **1.7.0** adds HDBSCAN to the same PCA/LSA representations and grouped
stability checks. It selects dense groups without forcing every passage into a
group. **Unassigned passages remain visible, source-linked and exported.** The
frozen R daily pipeline and its publication gates are unchanged.

## Use

1. Open the [workspace](https://lystadjs.github.io/un/transcript-agent/#analyze)
   and select the topic, dates, region and meeting scope, or import a saved collection.
2. Select **Text clusters and stability**, then **HDBSCAN** as the clustering method.
3. Choose PCA, LSA or their comparison. Start with 20 components, minimum group
   size **15**, density-neighbor count **5**, and **EOM** selection. These are
   starting settings, not empirically approved thresholds.
4. Enable stability to refit on whole meeting or affiliation samples. Generate
   the report and inspect assigned/unassigned coverage, group sizes and sources.
5. Compare minimum sizes and density-neighbor counts; compare leaf selection
   when finer groups are useful. Keep the same corpus and representation settings.
6. Download HTML, JSON, cluster CSV and consensus CSV. Changing settings disables
   exports until a new run. Cancel terminates the worker without a partial report.

The cluster-count and clustering-seed controls are disabled for HDBSCAN. The UMAP
seed remains active for the independent display. Gray crosses identify unassigned
passages on individual maps; the PCA/LSA overview uses PCA reference colors and
symbols in both panels so the same passages can be tracked. Open each individual
result for its own assignments. The unassigned section includes every affected
source passage and its original link.

## Method and limits

HDBSCAN uses unwhitened Euclidean retained PCA or LSA scores, never UMAP coordinates.
It computes exact core distances, an exact mutual-reachability minimum spanning
tree, the single-linkage hierarchy, a condensed tree and EOM or leaf selection.
There is no approximate neighbor search, forced group count or fallback partition.
Changing only density settings leaves the representation and UMAP unchanged.

| Setting | Meaning |
| --- | --- |
| Minimum group size | Smallest branch eligible to persist as a cluster; 2–600. |
| Density neighbors | Core-distance neighbor count, **including the observation itself**, as in scikit-learn; 2–600. A count exceeding usable passages withholds the fit with a reason. |
| EOM | Selects branches by excess of mass in the condensed hierarchy. |
| Leaf | Selects eligible terminal branches, often producing finer groups and more unassigned passages. |
| Fixed settings | Euclidean metric, alpha 1, selection epsilon 0, root/single-cluster selection disabled. |

The browser retains its maximum of 600 selected passages and minimum of four
usable passages. Requested components are capped at numerical rank. Zero-term
passages are explicitly excluded before representation and reported separately;
they are not HDBSCAN noise. An all-unassigned fit is a valid outcome, including
when minimum group size exceeds the collection. It displays zero groups and
withholds silhouette/ARI instead of reporting perfect agreement or forcing a group.

Membership strength is the point's departure density divided by the selected
cluster's maximum departure density, capped at one; unassigned strength is zero.
It is a geometric measure, not a calibrated probability, relevance score or human
review decision. HDBSCAN tree-selection stability is distinct from the grouped
resampling stability described below. Silhouette uses assigned passages only,
requires at least two groups and is accompanied by its passage count.

Exact distance ties use source row order in Prim's algorithm and stable MST
insertion order when sorting equal edges. Different libraries can resolve equal
hierarchy heights differently, changing labels or strengths. The exported tree
and tie rule make this inspectable. Exact zero distances are preserved; infinite
lambda/stability values are serialized as the string `Infinity`, not a finite
epsilon approximation or JSON null. Other algorithm diagnostics remain finite.

## Stability that accounts for unassigned passages

The [existing protocol](CLUSTER_STABILITY.md) remains: 30 samples by default,
80% of whole groups, seed 31415, at least one group omitted. Each sample refits
TF-IDF, representation and HDBSCAN using the fixed requested density settings.
UMAP is excluded. With this six-meeting collection the rounding retains five
meetings, and many repetitions reuse the same six omissions.

- **ARI:** compare only passages assigned in both the reference and sample;
  require at least two represented clusters in each fit on that shared subset.
  Otherwise record an unassessed reason. Record shared-assigned counts and all
  four assigned/unassigned transitions separately. PCA/LSA agreement uses the
  same rule and separately reports assignment-status agreement.
- **Cluster Jaccard:** compare each regular reference group with the best regular
  sampled group on included passages. A reference member becoming unassigned
  remains in the denominator. A group with at least two sampled members receives
  zero overlap if the entire sample is unassigned. Noise is never a matching group.
- **Consensus:** every successfully fitted, jointly sampled pair increments
  `co_observed`. Only the same non-noise cluster increments `co_clustered`.
  `co_assigned` separately counts occasions when both have any non-noise assignment.
  The heatmap uses `co_clustered / co_observed`. The pair CSV also supplies
  `co_clustered / co_assigned`, blank when that denominator is zero.
- **Per passage:** preserve included, assigned and unassigned sample counts and
  assignment rate. Reference-unassigned passages have no within-cluster score or
  cluster margin; they are not collected into a synthetic noise cluster.
- **All-unassigned samples:** successful fits contribute pair exposure and zero
  co-clustering. Failed fits do not contribute. Successful-fit count and assessable
  ARI count are separate; paired PCA/LSA means require assessable ARI in both fits.

These measures describe refitting sensitivity, not independent replication,
confidence intervals, future accuracy or shared national positions. High ARI may
coexist with low assignment coverage or procedural clusters.

## Export contract

The additive `un.text-clusters.v1` schema uses `algorithm: "hdbscan"`, common
`clustering` metadata and an `hdbscan` diagnostic block. The latter retains core
distances, MST edges, full single-linkage and condensed trees, selected nodes,
selection stability, parameters, counts and `unassigned_ids`.

At the public point/CSV level, **cluster 0 means unassigned**; regular groups
are 1-based. Points include `assignment_status` and `membership_strength`.
Kernel labels and resample logs use **-1 for unassigned** and 0-based regular
labels, explicitly distinguished in diagnostics. Tree leaves are 0-based point
indexes. Zero-term exclusions retain separate source IDs. The complete matched
source collection remains in analysis JSON, including unassigned passages.

Cluster CSV adds assignment status, strength and, when assessed, passage assignment
counts/rates. Consensus CSV adds endpoint status, `co_assigned` and the conditional
rate with its denominator. Existing k-means, PAM and hierarchical exports retain
their columns and numerical behavior. HDBSCAN's full trees are in JSON; the
**Hierarchy CSV** download remains specific to Ward/average.

## Validation and source findings

See the [source/settings comparison](CLUSTER_SENSITIVITY.md) and
[validation record](browser-hdbscan-validation.json). All six browser Node suites
pass. Independent SciPy checks reproduce every single-linkage connection level,
MST weight and edge distance across 22 fixtures. Scikit-learn 1.7.2 reproduces
condensation, selected membership, noise masks and strengths on the identical
tree for all 22. Entire independent fits agree on 18/22 fixtures; four tied cases
show cross-library differences recorded explicitly. This is not a claim of
universal label identity across implementations.

Both default 458-passage PCA/LSA EOM fits agree exactly with the independent
scikit-learn results, including noise and membership strengths. Browser acceptance
covers EOM, leaf and all-unassigned results, both representations, retained sources,
exports, cancellation, stale settings and desktop/mobile layouts. Independent
reconstruction checks all 104,653 pairs in each of six fits, across 140 sampled
fits; ARI/Jaccard errors are at most floating-point rounding. Existing k-means,
PAM, Ward and average scores, UMAP, partitions, diagnostics, sample logs and
consensus match their saved acceptance outputs exactly. Both GitHub deployments
succeeded, and the same three browser cases passed on the published website;
all exported clustering results exactly matched the local acceptance runs.

```sh
node tools/test_browser_hdbscan.cjs
python tools/check_hdbscan_reference.py --node /path/to/node
node tools/test_browser_hdbscan_ui.cjs http://127.0.0.1:8787/ saved-corpus.json qa-output
python tools/check_hdbscan_reference.py --analysis qa-output/eom/analysis.json
python tools/check_stability_reference.py qa-output/eom/analysis.json pca
```

Reference checks require NumPy, SciPy and scikit-learn 1.7.2; the staged comparison
uses that version's internal tree adapter. Website visitors need none of these.
The adapted condensation/selection code retains the
[scikit-learn BSD license](../site/HDBSCAN_LICENSE.txt).

Primary references: [scikit-learn HDBSCAN](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html),
[algorithm explanation](https://hdbscan.readthedocs.io/en/latest/how_hdbscan_works.html),
and [parameter selection](https://hdbscan.readthedocs.io/en/latest/parameter_selection.html).

The [reviewed passage comparison](PASSAGE_TYPES.md) now includes all 460 confirmed
source types and repeated full/subset fits with originals preserved. [NMF](NMF.md)
is implemented next in the sequence; neither HDBSCAN nor NMF supplies reviewed
thematic labels. [Regularized Gaussian mixtures](GMM.md) now add a separate
soft-membership comparison on the same reviewed inputs.
