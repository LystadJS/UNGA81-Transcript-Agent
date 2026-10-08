# W3 — source-aware graph-based learning

**Development-only research, not a D1 adapter or public analytical release.**
Python implementation adds exact source-linked k-nearest-neighbor affinity,
spectral clustering, diffusion maps, baseline comparisons, whole-meeting
sensitivity, coefficient/numerical diagnostics, and synthetic SVG benchmark plots.

## Reproduce (Python 3.13)

~~~sh
python -m pip install -r research/graph_methods/requirements.txt
python -m unittest discover -s research/graph_methods/tests -v
python -m research.graph_methods.reproduce --fixture blobs --seed 81 --output /tmp/graph-benchmark
~~~

The fixture creates 96 invented points, fictional observation/parent/meeting
IDs and hashes; **no transcript text, country label, private vector or held-out
meeting is read**. The output directory must be empty. Local output includes
receipt.json, interchange-v1.json, source-linked-edges.json, source-concentration.json,
fit-geometry.json, source-group-sensitivity.json, graph-policy-sensitivity.json,
diffusion-policy-sensitivity.json, SHA256.json, and
synthetic affinity.svg, diffusion.svg, baselines.svg and sensitivity.svg.

For an **already authorized** local development corpus, substitute
--input-manifest PATH --vectors PATH; the NPZ must have precisely the numeric X
array, no pickled content. The metadata-only manifest schema
un.graph-input.v1 carries split, upstream source/selection hashes and their
hash basis, a pinned matrix and representation identity, declared population
denominators and ordered observation ID/text-hash/parent/meeting/source linkage.
All rows must be development, never 5–6 October 2026. If the frame contains
excluded observations, list them under excluded_observations with explicit
exclusion reasons and define frame_join_sha256 for the joined eligible/excluded
ordered ID/hash sequence; total_in_frame must count both. Unavailable meeting
inventory remains separately counted. No original speech text
belongs in a manifest or public PR.

The SHA of the ordered [id,text_sha256] JSON pairs is
observation_join_sha256 (sorted-key compact JSON). Matrix SHA covers compact
shape JSON then little-endian contiguous float64 bytes. These checks verify
identity with the declared upstream manifest, **not the upstream transcript
bytes themselves**; upstream validation of original bytes remains required.
Optional --compare-manifest/--compare-vectors pairs two development
representations only with exact common observation IDs/hashes, upstream source
and selection identity, parent/meeting associations and identical distance
geometry. Pinned MiniLM needs a model revision fingerprint. Cross-basis ARI
and neighborhood overlap are descriptive; they do not align latent coordinates.
Merged W1's native source-frame, grouping and assignment-metric APIs are invoked
by an acceptance-gated Python↔Node adapter only for exactly matched, pinned
and authorized populations. W1 is an engineering source dependency, not a
scientific certification of graph discoveries.

## Numerical and scientific contracts

| Component | Supported options | Explicit diagnostics/refusals |
| --- | --- | --- |
| Graph | Euclidean or cosine; deterministic exact kNN; union/mutual edges; global Gaussian or local adaptive bandwidth; no self loops | Connected components, isolates, weighted degree/hub concentration, duplicate/tied points, neighbor count, edge identities; maximum 600 rows |
| Spectral | Symmetric, random-walk or unnormalized Laplacian; bottom-k eigenvectors; seeded 20-start k-means | Require k < n, nonzero degree and k >= component count; disconnected graph needs explicit opt-in; eigengap, residual, K-means convergence and row-normalization failures retained |
| Diffusion | Coifman–Lafon density alpha 0–1, time as integer 1–1000, selected nonstationary positive eigenmodes | Connected non-isolated graph, eigenvalues/gaps, stationary eigenvalue, residuals and sign/rotation sensitivity; no validated out-of-sample extension |
| Comparison | PAM and k-means in same full source/feature geometry; spectral ARI/AMI | Never use two-dimensional UMAP/display distances or compare mismatched cohorts |
| Quality | Neighbor retention, trustworthiness, continuity, source-group leave-one-out, kernel bandwidth and kNN sensitivity | Planned/successful/failed resamples explicit. Not independent replication, a null test, calibrated significance or confidence interval |
| Output | un.parallel-analysis.v1 metadata envelope, source-linked edges and local fit coordinates | Diffusion has no hard clusters: all fitted rows are explicitly unassigned cluster 0; failed fits are not_fitted with ledger entries. No policy stance inferred |

M34 in un/R/21_research_methods.R remains unchanged: its frozen D1
country-roster cosine threshold and M02 TF-IDF input are **not** equivalent
to this new passage/representation kNN graph. Daily publication flags, O1–O5
gates and all 37 reserved meetings remain untouched.

**Geometric diffusion describes a random walk on a constructed similarity
graph; it is neither political influence nor policy transmission.** Affiliation
is recorded metadata, not independently verified speech attribution. A stable
partition is not evidence of politically meaningful or nonrandom clusters.

## Coordinator handoff and ownership exception

The shared 8 October OWNERSHIP.md reserves
research/parallel/w03-spectral-diffusion/** and coordinator-only
.github/workflows/**. This PR uses research/graph_methods/** and a distinct
workflow because the owner's explicit later request specified them. **The owner-approved exception was recorded and merged through
[coordinator PR #23](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/23)
at commit `74bc2c70d0f7a79b8cf319d50b4d8d18f0978875`.**
No files under un/, site/, research/reference_tests/, research/corpus/,
shared release records or the original contract are modified.

Review the output row identifiers, graph components and degree concentration,
parameter and source-group sensitivity, failure ledger, residual/eigengap,
geometry distortion, and source provenance. Preserve all private
development-level output locally; only synthetic outputs belong in CI.
The coordinator alone may subsequently wire accepted work to the browser.
Scientific acceptance requires independent source-group testing and
nuisance-preserving negative controls beyond engineering fixtures.

References: von Luxburg (2007), *A Tutorial on Spectral Clustering*;
Coifman and Lafon (2006), *Diffusion Maps*; scipy.linalg.eigh;
scikit-learn KMeans/trustworthiness; docs/parallel-work/INTERCHANGE_V1.md.


## W1 interoperability — merged source, synthetic bridge validated

Source-aware W1 PR #19 merged into main at
`87dedd6ee7b30fb7cd1e26e8ef26e30ee8e52329` on 8 October 2026.
The W3 bridge, `w1_bridge.py`, now invokes W1's **actual installed Node**
`validateFrame`, `schedule` (whole-meeting), `auditSources`,
`validateRelational` and `evaluateAssignments` APIs when the code is
present and the caller has an approved merge-commit/code-SHA provenance pin.
The local bridge also independently checks exact source identity, original
ID/text hashes, selection, parent/meeting/offset, missing reasons,
affiliations, review status and representation training-selection version.
It rejects unmerged/W1-unavailable checkout states, incompatible frame
schemas, coverage mismatch, impossible soft/hard assignments and unapproved
code. No W1 metrics are reimplemented by Python as fallback.

**Executed synthetic interoperability:** the CI pull-request merged-tree
checkout contains W1 from main and W3 from this PR. The W1 native synthetic
fixture produces 24 eligible observations plus one unavailable/missing source;
W3 uses the *same* ordered text/SHA identities and invented raw vector basis.
The tests exercise real W1↔W3 ARI/AMI, independent scikit-learn references,
whole-meeting group scheduling, exclusion/noise denominators, altered source
and model hashes, false approval and incomplete assignments. A text-free
aggregate `w1-w3-interoperability.json` receipt is archived with SHA256
alongside graph benchmark artifacts on PR-triggered CI runs. Push-only W3
branch checkouts may not contain W1 files and therefore skip these tests;
PR merged-tree CI requires them explicitly.

For private development validation, the CLI supports
`--w1-envelope /private/w1-evidence.json`,
`--w1-approval /private/w1-approval.json` and
`--w1-model-id ID`; supply all three. Outputs must be created outside the
public GitHub checkout in an owner-only directory. A local approval record is
not cryptographic authentication or verification of the original transcript
bytes. Identical *underlying* representation ID/version does not guarantee
identical fitted distances: W1 can refit PCA, and W3 may operate on its
pinned original high-dimensional vectors. The comparison is descriptive,
not an aligned latent coordinate comparison.

For the merge-review gates, required local approval shape, W1 source-schema
limitations and scientific caveats, see `COORDINATOR_REVIEW.md`. Real
development-source interoperability and independent/null-calibrated
diplomatic conclusions remain **NOT RUN**. The W3 file-ownership exception is now documented and approved. PR #16
still requires exact-head CI and coordinator acceptance before engineering-only merge.

## Accepted W1 interoperability and merge path

The accepted W1 source implementation has been merged into main; the W3
interoperability bridge exercises W1's native source-frame validator, whole-
meeting sampling schedule, source audit, versioned relational validator and
assignment metrics on the PR merged tree. Independent scikit-learn references
verify the synthetic ARI/AMI; generated W3 v1 envelopes are also checked with
the accepted W1 relational API, including negative model/source-ledger cases.
The uniquely named CI now runs after relevant changes to main, so post-merge
regressions can be verified without opening private sources. No result is
eligible for publication or inference from synthetic engineering evidence alone.

The owner authorized coordinator merge of PR #16 after validation. The
remaining operations are verifying the latest full file list, per-head
passing checks, merge commit on main and post-merge CI. No active
browser, D1 email or website deployment is part of PR #16.
