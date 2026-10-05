# Live transcript report builder

Open https://lystadjs.github.io/un/transcript-agent/#analyze.

Current browser version: **1.7.0**. Text clustering offers k-means, PAM,
hierarchical Ward/average linkage and HDBSCAN on either PCA or LSA, including
paired representation comparison and grouped stability. HDBSCAN preserves explicit
unassigned passages and reports assignment coverage. See the
[partition guide](PARTITION_METHODS.md), [HDBSCAN guide](HDBSCAN.md) and
[source/settings comparison](CLUSTER_SENSITIVITY.md).

1. Enter a topic and optional comma-separated alternative phrases. A source
   segment matches any phrase; optional exclusion phrases remove the entire
   segment. Matching is case-insensitive over Unicode word tokens. It does not
   infer relevance, sentiment or stance. Abbreviations need human checking.
2. Select inclusive start/end dates, speaker region and meeting scope.
3. Choose descriptive methods and select **Collect transcripts & generate report**.
4. Inspect collection coverage, denominators and source evidence before sharing.
5. Download the standalone visual HTML report, analysis JSON, collected transcript
   JSON or matched-segment CSV. Use Print / save PDF for a printable copy.

## Collection

The browser requests the official `transcripts.un.org/en/meetings.json` inventory
for each date, checks pagination counts and dates, then retrieves the selected
meetings' transcript JSON. Both inventory and transcript endpoints returned
`Access-Control-Allow-Origin: *` in the October 2, 2026 acceptance check; a live
browser test confirmed collection without a proxy or separately hosted service.
If that policy changes, or a managed network blocks the service, live collection
will show failures. Exported collections can still be imported locally.

Only dates and source paths are sent to UN endpoints. Topic and regional filtering,
analysis and export run on the user's device. This is on-demand collection, not
a scheduled crawler, a complete search of all UN websites, or an authenticated
shared workspace. No secrets, account or paid backend is required.

Each observation is an original source segment from the transcript service,
not automatically a complete national address. Procedural interventions remain.
Only English transcript tracks are used; these may be interpretation or automatic
transcription. Non-English, unavailable and failed sources are recorded. Unmapped
affiliations are retained under All regions / Unmapped, rather than guessed from
text. Speaker region is the existing analytical geography in
`un/config/countries.csv`, not official UN group membership or topic geography.

Limits: 31 inclusive days, 300 selected meetings, 15,000 segments, 20 million text
characters, 25 MB per source response, 45-second request timeout. A failed daily
inventory or failed meeting is explicit in coverage. Data collected within limits
may still produce a partial report, with a coverage warning. No missing source is
treated as a non-match. Cancel releases no partial report. Transcript publication
can lag proceedings; an empty inventory is not evidence that no meeting occurred.

## Methods and denominators

Date, scope, English language and region filters precede deduplication and matching.
NFKC-normalized text with whitespace collapsed is deduplicated within that eligible
corpus, preserving a duplicate-to-retained-ID mapping. Case is preserved for this
exact-text operation. Near duplicates are not detected or removed. All matching
uses NFKC, lowercase Unicode letter/number tokens and contiguous phrase boundaries.

| Selectable method | Calculation |
| --- | --- |
| Regional frequency | Matched unique segments / eligible unique segments, by speaker region |
| Daily frequency | The same denominator by date; dates with no eligible collected segments are omitted |
| Length distribution | Unicode token counts in matched segments, in four displayed bins |
| TF-IDF | Lowercase unigrams longer than two characters, fixed English stop list; TF = 1 + ln(count), IDF = 1 + ln((1 + N)/(1 + df)); L2-normalized vectors; top 20 mean weights across matched segments |
| Cosine similarity | All pairs of matched TF-IDF vectors, top 10 reported; skipped with an explanation above 300 matched segments |

These are descriptive summaries of an observed corpus with dependent segments.
No population confidence intervals, significance, causality, diffusion, coordination,
or inferred stance is claimed. BERT and frozen D1 methods are not ported or run here.
The browser engine (`browser-descriptive-1.0.0`) does not change their gates,
full-corpus representations, source artifacts, or reviewed-model evaluations.

## Reuse, provenance and privacy

Collection export schema is `un.browser.corpus.v1`. Required record fields are
`id`, `date` (YYYY-MM-DD), `country`, `region`, `language`, `scope`, `meeting`,
`text`, `source_url` (HTTPS), and `text_sha256` (SHA-256 of UTF-8 text).
The top-level `records` and `coverage` arrays are required. Live exports also
include source response hashes, JSON pointers, timestamps and collection scope.
Imported hashes are recomputed before analysis; metadata and identity are still
user-supplied, not authenticated. An imported collection cannot supply dates or
scope it never collected; a mismatch is prominently reported.

Analysis JSON retains exact parameters, method outputs, coverage, duplicates and
all matched evidence. HTML previews the first 100 matched segments with expandable
full text. JSON and CSV include all matches. Keep collected transcript files on
your own device or approved storage; they are not automatically published or
submitted. The public repository contains only code and country metadata.

The content security policy permits same-origin assets and the UN transcript
origin. No third-party chart library, tracking service, arbitrary URL proxy or
central review submission is introduced. Existing review-packet functions remain.

## Validation

Run `node tools/test_browser_analysis.cjs` for deterministic calculations and
collector failure/cancellation tests. Browser acceptance checked a real September
22, 2026 General Debate collection, all five methods, downloadable HTML/JSON,
region filtering on reimport, hash-tamper rejection, cancellation, stale-result
export disabling, existing practice review and 1440/390-pixel layouts. Test
queries are engineering checks, not human-reviewed substantive findings.

Recommended next step: run one narrow substantive query, inspect the full source
segments for false matches and missing affiliations, then decide whether additional
browser methods or an authenticated backend for D1 are warranted.


## PCA → k-means → UMAP (browser 1.3)

Browser 1.5 adds **LSA** and **Compare PCA and LSA**, with paired resampling,
source-linked membership/neighborhood comparisons and visualization fidelity
diagnostics. PCA remains the default. See [LSA methods and validation](LSA_COMPARISON.md).

Browser 1.4 additionally offers **Assess cluster stability**: grouped subsampling
with TF-IDF/PCA/k-means refits, Jaccard/ARI agreement, a consensus heatmap and
source-linked review candidates. See the [protocol, exports and validation](CLUSTER_STABILITY.md).
This optional assessment leaves the reference pipeline described below unchanged.

Select **Text clusters: PCA → k-means → UMAP** in the report controls. This uses
all included unique passages after the existing date, committee/scope, region,
language, deduplication and optional topic filters. Leaving Topic blank preserves
the all-passages mode. It does not change the frozen D1 representation or outputs.

1. **Representation:** build the existing sublinear, smoothed, L2-normalized
   TF-IDF vectors. Exclude zero vectors with retained IDs and reasons. Center
   features and compute PCA through the symmetric eigendecomposition of the
   centered document Gram matrix. No feature standardization or whitening is
   applied. Retain the requested leading components, capped at numerical rank.
2. **Clustering:** use Euclidean k-means on all retained PCA scores. Ten seeded
   k-means++ starts each allow 300 iterations. Empty clusters are repaired with
   farthest-point reassignment when possible. Only converged, non-empty fits are
   eligible; choose the lowest-inertia fit. Export centroids, inertia, mean
   silhouette in PCA space, restart inertias and adjusted Rand agreement with
   the selected fit. These are descriptive diagnostics, not external validation.
3. **Visualization:** fit unsupervised two-dimensional UMAP to the same PCA
   scores. Cluster labels are never supplied to UMAP; UMAP coordinates are never
   used by k-means. Use Euclidean distance, random initialization, spread 1 and
   300 epochs. The independent UMAP seed, neighborhood count and minimum distance
   affect only the display. Both scatterplots preserve equal axis unit scaling.

Defaults are 20 PCA components, four clusters, 15 UMAP neighbors, minimum distance
0.1, k-means seed 42 and UMAP seed 42. Controls permit 2–50 components, 2–12 clusters,
2–100 neighbors and minimum distance 0–0.99. Components are capped at rank;
neighbors at usable passage count minus one. Effective and requested settings
are retained. At least four nonzero vectors and fewer clusters than usable
passages are required. A zero-rank or unfit cluster configuration is explicitly
withheld. Above 600 included passages the method is skipped without sampling;
other selected report methods still run. Numerical work runs in a Web Worker
that is terminated on cancellation, including during synchronous PCA fitting.

The UMAP map links every point to its original source; labels give the country,
date, cluster and passage ID. A second plot shows the first two PCA components
with the identical assignments. Cluster descriptions use mean TF-IDF terms and
the passage nearest each centroid; these are examples, not reviewed topic or
political labels. A map's islands, distances or shapes do not establish shared
positions, coordination or diplomatic separation. Low retained PCA variance is
reported rather than hidden; comparing component counts, k and seeds remains
necessary before interpreting groups.

Analysis JSON contains the `un.text-clusters.v1` result, including every passage
ID/hash, retained PCA score, cluster assignment, UMAP coordinate, parameter and
diagnostic. Cluster CSV exports the same per-point coordinates and assignments.
The downloadable HTML retains both SVG plots and source links without scripts.
Numeric cluster IDs are nominal; comparisons across different fits should use
membership agreement rather than treating cluster numbers as stable categories.

### Rebuild and verify

The site serves its numerical bundle locally. No CDN, remote model call, package
installation or added backend is required for users. `ml-matrix` 6.15.0 and
`umap-js` 1.4.0 are pinned in `tools/browser-deps/package-lock.json`. Dependency
licenses are included in `site/NUMERICS_LICENSES.txt`; package integrity values
and the bundle SHA-256 are in `site/numerics-manifest.json`. The Pages builder
checks that hash before publishing. Build dependencies are separate from the
existing R/Python environments:

```sh
cd tools/browser-deps
npm ci --ignore-scripts --no-audit --no-fund
node build.cjs
cd ../..
node tools/test_browser_analysis.cjs
node tools/test_browser_clusters.cjs
```

Numerical tests cover hand-calculated PCA geometry, a known-cluster fixture,
reference silhouette, repeated-run determinism, UMAP-setting invariance of
k-means/PCA, zero vectors, rank/size bounds, cancellation and filter integration.
An independent NumPy SVD comparison on 71 public source passages agreed in
variance and retained-space pairwise squared distances (maximum absolute error
6.22e-14). The October 4 browser acceptance collected 460 General Debate passages
for September 22–28; 458 nonzero vectors entered the new pipeline. It verified
source links, HTML/JSON/CSV exports, worker cancellation, stale-export protection
and mobile overflow. These are engineering acceptance checks, not substantive
validation of the resulting diplomatic categories.

Primary implementation references: [ml-matrix](https://github.com/mljs/matrix),
[UMAP-JS](https://github.com/PAIR-code/umap-js), and the
[UMAP paper](https://arxiv.org/abs/1802.03426). The JavaScript implementation uses
random rather than spectral initialization; results are not asserted to match
Python UMAP coordinates.
