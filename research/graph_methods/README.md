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
W1's independent source-validation APIs must be integrated after acceptance,
not claimed to exist here.

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
workflow because the owner's explicit later request specified them. **The
coordinator must approve or reconcile that namespace exception before merge.**
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


## W1 integration readiness (not activated)

W1 source-aware validation resides in draft PR #19 at
research/validation_framework/** and is not merged or coordinator-accepted.
The isolated Python W3 bridge (w1_bridge.py) has a strict acceptance gate:
without actual installed W1 Node validators, coordinator-pinned merged code
SHA, and matching versioned W1 interchange, it refuses the request. It never
imports unmerged W1 code, quietly computes a replacement ARI/AMI, or changes
a failed graph partition. The accepted bridge will call W1's native Node
evaluateAssignments and validateRelational APIs after checking exact source,
selection, meeting/parent/offset, missingness and pinned representation identity.

The private CLI adds --w1-envelope /private/w1-evidence.json,
--w1-approval /private/w1-approval.json, and --w1-model-id ID.
All three are required together, only on authorized development inputs;
private results are stored outside the Git checkout in an owner-only directory.
Synthetic CI exercises the **withholding/identity checks** and explicitly logs
W1's full integration as NOT_RUN until accepted and installed.

For the precise approval-record schema, coordinator decision matrix,
remaining scientific limitations, and merge checklist, see
COORDINATOR_REVIEW.md. No current CI result constitutes W1 integration
acceptance or a policy/diplomatic finding.
