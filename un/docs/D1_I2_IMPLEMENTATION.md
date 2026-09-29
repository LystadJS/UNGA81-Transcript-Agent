# D1-I2 implementation — frozen TF-IDF and projection display contracts

**Release 2.3.0-d1-i2.** This document distinguishes implemented computations, display permission, and unimplemented models. No institution, policy, or country is evaluated or ranked by these methods.

## 1. Implemented scope

| Method | Actual adapter | Published role |
|---|---|---|
| M01 | Existing lexicon candidate retrieval with exact source passages | Diagnostic; not a classifier |
| M02 | Immutable vocabulary/IDF; sparse statement transforms; explicit country pooling; cosine matrix | Representation, not calibrated relevance or agreement |
| M05 | Centered, unscaled reference PCA; fixed-basis projection; independent numerical checks | Conditional O3 descriptive display only |
| M06 | Euclidean PCoA; frozen-anchor out-of-sample transform; independent spectrum checks | Audit challenger only |
| Other 38 methods | No executable adapter | Explicit not_implemented, every prerequisite retained |

A method can fit successfully yet end as `withheld_quality`. The run ledger preserves its artifact, actual fit/reference-reuse status, time interval and failed display checks. `executed` is not synonymous with “trained classifier,” and `reused_reference_fit` still performs a new daily transform. Full M02/M05/M06 result-cache reuse is not claimed; frozen reference objects are reused, while current transformations and diagnostics are recomputed.

The immutable original 42-row D1 design registry is preserved. Adapter availability and actual R dependencies belong to the runtime ledgers, not a rewritten historical design status column. M02 uses Matrix plus R directly, rather than claiming execution of quanteda or every candidate package listed in D1.

## 2. TF-IDF contract

The observational unit for document frequency is **unique exact source text**, not country-day labels and not individual words. Duplicate statement versions are rejected/deduplicated by the source layer. Duplicate exact texts do not multiply reference document frequency.

Tokens are Unicode letter runs, lowercased under a recorded R/PCRE/locale environment. No stemming, translation, transliteration or inferred language is performed. Two-character-or-longer tokens are retained except for a versioned, authored English stoplist. Negations `no`, `not` and `nor` remain. Generic greetings are removed. All original source text is retained unchanged.

For reference text count N and document frequency df_j:

```
idf_j = 1 + log((1 + N) / (1 + df_j))
tf_dj = 0 if count_dj = 0; otherwise 1 + log(count_dj)
w_dj  = tf_dj * idf_j
x_d   = w_d / ||w_d||_2 when the norm is positive
```

Natural logarithms are used. Terms must occur in at least two distinct reference texts and no more than 98% of them. At most 10,000 terms survive, with deterministic frequency and lexical tie-breaking. This explicit smoothed convention is not presented as quanteda's default weighting.

Within each country, unique-text statement vectors are averaged with **equal statement weight** and the resulting country vector is L2-normalized. Multiple statements are preserved as independent source records before aggregation. Zero contributing vectors remain visible in coverage diagnostics; a partly missing aggregate cannot be published just because its pooled norm is positive. Cross-country exact duplicates are retained as observations but block automatic display.

The full cosine matrix is `X %*% t(X)`. A zero vector's similarity row/column is NA, not zero similarity, neutrality or absence. Unknown words do not expand the vocabulary. Each statement records eligible-token count, in-vocabulary count, OOV count/fraction and nonzero status. The four fixed topic names are neither removed nor given artificial extra weights.

## 3. Reference identity and chronology

Reference paths are scoped by an explicit namespace plus provenance class, genre, source language and translation-version signature. Replay and engineering data cannot seed the observed-input namespace. Mixed/unspecified language may be processed for audit but cannot pass the known-English display gate.

The first reference is fitted once (`bootstrap_then_frozen`); subsequent runs use its immutable `ACTIVE.rds` pointer. A changed reference is not a silent daily refit. Select a new `feature_reference_namespace`, preserve the old one, document the change, and rebuild a comparable series before interpreting cross-version movement.

The reference stores its source texts/identities, event cutoff, acquisition cutoff, freeze time, stopwords, vocabulary/DF/IDF, reference sparse vectors, pooling metadata, implementation fingerprints and R/Matrix/PCRE/locale identity. Corrupt pointers, modified source content, incompatible policies, changed implementation/environment, and future cutoffs fail explicitly. No automatic repair or force-rebootstrap flag exists.

Source event time and local knowledge time remain separate. A current-day reference is labeled **cross-sectional reference fit**, not a historical validation or longitudinal movement. Rebuilding an archive uses its saved reference and observations; it never queries the active store or retrains a model.

## 4. PCA and PCoA

PCA uses `stats::prcomp(center=TRUE, scale.=FALSE, rank.=2)` on the bounded reference country matrix. It stores the complete returned singular-value spectrum, reference center, first two loading vectors and source labels. Feature variance scaling is not applied to TF-IDF columns. Projection is `(X_new - reference_center) %*% reference_loadings`; adding other new observations cannot move an already projected new point.

Signs are fixed deterministically by the largest absolute loading (lexical tie order). A repeated eigenvalue can still make orientation intrinsically nonunique; the subspace gate checks the second-versus-third eigenvalue separation. No axis is named after a substantive political interpretation.

PCoA uses **Euclidean chord distance** on the identical normalized feature vectors:

```
d_ij = ||x_i - x_j||_2 = sqrt(2 * (1 - cosine_ij))
B    = -0.5 * J * D^2 * J
Y    = U_2 * sqrt(Lambda_2)
```

Self-distances are set exactly to zero before the square root to remove finite-precision roundoff. Material negative eigenvalue mass is rejected, not silently corrected with Cailliez, Lingoes or another changed distance definition. The retained eigenpairs are verified against an independently reconstructed centered Gram matrix.

For a new row of squared distances delta to the frozen reference anchors, with reference row means r and grand mean g:

```
b_new = -0.5 * (delta - mean(delta) - r + g)
y_new = b_new * U_2 / sqrt(Lambda_2)
```

This is a rectangular fixed-reference extension. It does not refit cmdscale on the combined old/new sample or recenter using the new batch. Tests verify the reference reconstruction, batch invariance, comparison with stats::cmdscale, and equivalence to frozen PCA up to the reference rotation. With Euclidean TF-IDF these methods describe the same geometry; their agreement is not independent substantive corroboration.

Resource bounds are enforced before dense decomposition. The implementation does not support unbounded all-history dense matrices, every possible non-Euclidean distance, kernel PCoA or automatic eigenvalue correction.

## 5. Frozen display policy

`config/feature_policy.json` and `config/projection_policy.json` must match their preserved `design/D1-I2/` copies. The threshold files were written before fitting the 39-country source example. They were not tuned to its result. A policy revision is an explicit new design/validation decision, not an edit to make one map pass.

The numerical defaults are:

| Gate | Required condition |
|---|---|
| Reference/current support | At least six usable countries in each |
| Legibility | At most 75 current countries |
| Reference variation retained by two axes | At least 0.40 |
| Current pairwise squared-distance energy retained | At least 0.40 |
| Raw distance stress | At most 0.45; no coordinate stretching |
| Pairwise distance rank correlation | At least 0.70 |
| k-nearest-neighbor overlap | At least 0.50 |
| (lambda2-lambda3)/lambda2 | At least 0.05 |
| Negative-eigenvalue mass / positive mass | At most 1e-9 |
| Maximum current statement OOV fraction | At most 0.35 |
| Eligible-token support per reference/current statement | At least 30 |

Seventeen recorded checks combine those metrics with complete nonzero coverage, one known English genre, observed-input provenance for reference and current texts, no cross-country exact duplicates, and no source flags/collection errors. Neighbors use k=min(5, floor((n-1)/3)), with deterministic distance-then-ISO3 tie breaking. Missing, constant and degenerate results remain undefined and fail the applicable gates.

These thresholds are **engineering display defaults**, not calibrated bounds on semantic error or geopolitical meaning. They do not establish confidence intervals, causal effects, policy-position validity, independence of countries or out-of-sample classification accuracy.

## 6. Five-output integration and release boundary

Only the `M05:tfidf-pca-display-v1` factory may create a ready O3 packet. It independently checks source/snapshot/time identity, the frozen feature transformation, projection equations and diagnostics, source-bound coordinate CSV, complete label layout, PNG size/hash and the release receipt. A changed Boolean, substituted CSV, altered metric, extra payload field, future artifact, challenger substitution, sixth section or unregistered image is rejected.

The two “allow” configuration flags remain false: they reject generic/automatic promotion. They are not overrides for the hard-coded, independently validated descriptive O3 contract. No user-edited flag is sufficient to release a result.

O1/O2/O4/O5 remain unavailable pending their own producers. The four fixed topics and regional country readouts stay visible. Exactly five analytical sections remain in HTML and plaintext. A valid display may add **one** PCA CID image alongside the seal. Otherwise only the seal is embedded. The legacy three issue charts and both projection alternatives remain in the audit; dropping a PNG into a directory cannot create an extra email analysis.

Figures use deterministic ISO3 labels, region colors/shapes, equal geometric aspect and no confidence ellipses, clusters or arrows. Label placement moves text only, not data points. An image/label-layout failure independently blocks inline publication even if numerical checks pass.

## 7. Important remaining work

No supervised classifier, embedding encoder, topic model, clusterer, rhetorical-movement model, driftmapR inference, country network, forecasting or diffusion adapter was added here. No gold-label ingestion, semantic recoding, empirical release calibration, `targets`, DuckDB, GPU benchmark, weekly retraining scheduler or email-sending capability is implied.

RDS integrity checks do not make untrusted RDS safe to load. Keep full store/model/report backups. Hashes bind trusted objects to their recorded bytes; they do not authenticate a malicious actor who replaces every file and manifest.

## 8. Public numerical documentation consulted

- R `stats::prcomp`: https://stat.ethz.ch/R-manual/R-devel/library/stats/html/prcomp.html
- R `stats::cmdscale`: https://stat.ethz.ch/R-manual/R-devel/library/stats/html/cmdscale.html
- quanteda TF-IDF documentation (context, not a claimed executed backend/default): https://quanteda.io/reference/dfm_tfidf.html

The exact code and the tests, not a citation alone, define this implementation. See `validation/FINAL_VALIDATION.md` for the executed profile, actual findings and untested operational paths.
