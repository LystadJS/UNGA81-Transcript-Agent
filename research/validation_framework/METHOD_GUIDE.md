# Source-aware unsupervised learning validation (W1)

**Release status: engineering-only.** This adapter evaluates computational sensitivity, not statistical significance or diplomatic alignment.

## Reproduction and dependencies

Node 22; no npm install. Run:

    node research/validation_framework/tests/test_framework.cjs
    node research/validation_framework/cli.cjs --synthetic > synthetic-aggregate.json
    node research/validation_framework/cli.cjs --synthetic --interchange > synthetic-interchange.json
    node docs/parallel-work/validate-contract.cjs

The W1 GitHub workflow runs these commands alongside the existing browser clustering, LSA, partitions, density, GMM, stability, latent, corpus and reviewed-unit regressions. Public inputs and outputs are invented synthetic examples. CI has no private transcripts or pinned vector caches.

For an **authorized cached development-only** frame and a source-compatible settings array:

    node research/validation_framework/cli.cjs --input /private/dev-frame.json --settings /private/settings.json --private-output /private/w1-evidence.json

To compare pinned semantic representations, add the option --cache /private/pinned-cache. The local pinned_cache.py bridge reuses research/semantic_review/encoder.py, enforcing the existing MiniLM lock, encoder implementation hash, cache digests, identical observation order and text SHA-256, normalized vectors and offline execution. Python and its locally pinned semantic-review dependencies must be installed. A missing cache is a blocked case, not synthetic evidence about the real model. The private output must be outside the public GitHub checkout, has exclusive creation and restricted permissions, and is never emitted to standard output.

## Inherited statistical engines

The package imports, without modifying, site/analysis-core.js for lexical TF-IDF; site/cluster-core.js for PCA/LSA and k-means; site/cluster-algorithms.js for PAM and Ward/average linkage; site/hdbscan-core.js for density/noise; and site/gmm-core.js for regularized EM. All methods fit on retained full-dimensional scores, never UMAP/MDS coordinates. The pinned MiniLM vectors are cached high-dimensional source-bound model outputs; PCA on these embeddings is refitted per grouped sample. Lexical TF-IDF, vocabulary and PCA/LSA are refitted per group sample. The source corpus and all original methods remain unchanged.

## Comparability, missingness and uncertainty

- Exact matching requires the original source schema, SHA-256 and hash basis plus ordered observation ID and text-hash pairs. A saved representation must contain exactly this population; neither a changed population nor altered row order can be silently accepted. Cross-representation comparison is a named paired design, not an assertion that different feature spaces are identical.
- Inventory counts, eligible source segments, excluded or unavailable sources, assigned observations, HDBSCAN noise, and attempted/successful/failed/skipped fits have different denominators and are separately reported. No uncollected transcript is interpreted as evidence of no issue mention.
- Resampling uses a shared seed and identical group omissions for all settings. Meeting resampling blocks every passage by verified meeting ID. Recorded-affiliation resampling uses transitive affiliation/source-parent group closure so that no common original segment is divided among samples; unknown affiliations remain unknown. Fewer than three independent groups prohibit the resampling exercise.
- ARI and adjusted mutual information are computed only on observations assigned in both fitted partitions when both have at least two represented groups. AMI uses the arithmetic average of marginal entropies and exact hypergeometric expected mutual information. Assignment-status transitions and pairwise co-assignment consistency use explicit eligible and evaluable denominators; label numbering is arbitrary.
- Stability summaries report the number planned, attempted, successful, failed, skipped and assessable; withheld metrics remain null. GMM memberships are model-conditioned responsibilities; HDBSCAN strength is geometric, not calibrated confidence. Group replicates do not manufacture independent passages or confidence intervals.
- Source audits expose meeting concentration, within-meeting pair share, duplicate text hashes, recorded role/genre × cluster distributions and missing affiliation. Country metadata is not an independently verified speaker, government stance, vote or diplomatic position. Source-linked disagreements identify pairs of observations with different coassignment, not merely different cluster ordinal numbers.

## Hypothesis and inferential boundary

A possible future null reference asks whether apparent thematic structure is explained entirely by source meeting blocks and associated genre/role features, with no additional independent national alignment. **That hypothesis is not tested here.** Group exchangeability is unverified; sources are dependent; model-grid search creates multiplicity; no permutation calibration or preregistered rejection rule exists. The current evidence supports only descriptive computational stability and sensitivity. Do not attach a p-value, claim statistical significance, rank national alignment, or infer causation.

## Schemas and safe delivery

The input schema is un.source-validation.frame.v1. It carries the upstream schema, source SHA-256 and hash basis, split (synthetic or authorized development), immutable original IDs/text digests, meeting and parent lineage, source status and exclusion reasons. Optional source text is validated against its UTF-8 SHA-256 when supplied, used only in process memory for lexical fitting, and never serialized to the published output. Original raw-byte vs decoded UTF-8 source hash bases are explicitly distinct. Saved vectors require a representation identity/version, an immutable model transformation hash, exactly matching IDs/text hashes and finite common-dimensional vectors.

The internal result schema is un.source-aware-validation.v1; records contain settings, fit/seed, representation identity, source/selection hashes, status, membership type, failure and convergence information. The interchange adapter produces un.parallel-analysis.v1 per docs/parallel-work/INTERCHANGE_V1.md, with model–observation results, exclusion reasons, source-linked evidence pointers, complete fit accounting and methodological limitations. Its relational validator checks cross-field invariants. Public aggregate output contains no transcript text or source-level evidence. All 37 October 5–6 reserved holdout transcripts remain unopened.

## Explicit non-delivery accounting

Tests cover known clusters, null structures, duplicate-heavy samples, high-noise density cases, insufficient groups, failed kernels, corrupted text and parent hashes, wrong embedding source, duplicate IDs, unverified speech claims, invalid offset spans, and forbidden holdout dates. Failures remain visible in the failure ledger. No method automatically substitutes another kernel or changes observation denominator after failure.

## Coordinator ownership exception

The requested branch and implementation paths differ from the coordinator's earlier W1 reservation. This PR intentionally uses research/validation_framework/** and the uniquely named workflow .github/workflows/source-aware-validation-w1.yml, as explicitly requested. docs/parallel-work/OWNERSHIP.md instead reserves research/parallel/w01-source-validation/** and holds workflow edits for the coordinator. **Coordinator approval of this deviation, or subsequent coordinator-led relocation, is required before merge.** No shared coordination document, frozen research source contract, existing site component, or evaluation lock has been changed.
