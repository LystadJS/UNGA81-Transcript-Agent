# NMF components and reviewed inclusion

**NMF now runs in the browser and preserves overlapping passage weights.**
Open the [workspace](https://lystadjs.github.io/un/transcript-agent/#analyze) or the
[reviewed-corpus comparison](https://lystadjs.github.io/un/transcript-agent/nmf-audit.html).
Select **NMF — overlapping components**, choose a component count, and optionally
enable component stability. Source links, term-weight charts, mixtures, optimization
diagnostics and grouped refits are included in the report. JSON retains the full
component vocabulary and term weights; CSV retains each passage's raw and normalized
weights. Downloaded HTML is script-free. Cancellation terminates the worker, and
changed settings disable exports until the analysis is rerun.

For the reviewed substantive subset, import the original saved collection, choose
the reviewed inclusion policy, and load the completed passage review JSON. The
browser verifies the exact collection bytes, complete source ID/text-hash coverage,
explicit decisions and reviewer timestamps. **Save transcripts keeps all original
records, and imported collections retain their exact file bytes.** This preserves
the review hash through download and reimport, including whitespace and a byte-order
mark. The analysis records the selected policy and excluded IDs separately.
Review files and transcript text are processed locally, without submission.

## Method and interpretation

The existing tokenizer, stoplist, sublinear term frequency, smoothed inverse
document frequency and L2 row scaling produce a nonnegative matrix X. NMF fits
X approximately equal to W H using Frobenius multiplicative updates, without
centering, PCA, LSA, UMAP, whitening, regularization or hard cluster assignment.
The [Lee–Seung paper](https://papers.nips.cc/paper/2000/hash/f9d1152547c0bde01830b7e8bd60024c-Abstract.html)
defines the update family; [scikit-learn's decomposition guide](https://scikit-learn.org/stable/modules/decomposition.html#non-negative-matrix-factorization-nmf-or-nnmf)
provides the reference context. The JavaScript kernel is an original implementation.

Default settings are six components, three strictly positive random starts,
seed 42, 300 iterations and tolerance 0.0001. Starts use deterministic derived
seeds. To inspect an alternative start in the workspace, choose one starting point
and enter that start’s reported seed. The lowest residual wins; all starts and their aligned agreement remain
visible. Every ten iterations, residual decrease divided by initial residual is
compared with the tolerance. Meeting that stopping rule is not proof of a global
optimum. Iteration-limited fits remain explicitly provisional. Near exact
reconstruction, direct residual calculation avoids cancellation in the Gram identity.

Each H row is rescaled to unit L2 length and its W column is rescaled inversely,
preserving W H. Passage shares normalize that row of W to sum to one. They are
**descriptive mixture weights, not probabilities, stance scores or thematic labels**.
Zero reconstructed weights have undefined shares. The component chart averages
shares across usable passages; undefined shares contribute zero and remain flagged.
Top sources rank by absolute W loading, not just share. Browser excerpts show the
opening of the original passage, with source links for full context. Public static
comparisons publish links and metadata, without embedding new transcript text.

Relative residual is ||X − W H|| / ||X||. The reported squared reconstruction
fraction is 1 − ||X − W H||² / ||X||². It measures in-sample approximation of the
uncentered matrix; it is neither centered explained variance nor predictive accuracy.
There is no automatic best component count. Component IDs are local to each fit.

Limits: 600 selected passages, at least four usable passages, 2–12 components,
fewer components than usable passages, and no more components than terms.
There is no silent sampling or vocabulary truncation. Zero-term passages have
explicit exclusion records. Duplicate handling and eligibility filters remain
the existing browser pipeline. Frozen R D1 methods and release gates are unchanged.

## Stability and fixed comparison protocol

Whole meetings or recorded affiliations remain together. The browser defaults to
30 uniform samples retaining 80% of groups, rounded up with at least one omitted,
seed 31415. Each sample refits vocabulary, IDF and NMF with derived initialization
seeds. At least three groups are required. Missing affiliation and non-UN meeting
fallbacks retain the existing documented grouping rules.

Components are aligned by an exact maximum-weight one-to-one assignment over
cosines between complete unit-length H rows. Terms missing from a vocabulary are
zero, rather than renormalizing only the shared terms. Cosine is 0–1; mixture L1
difference is 0–2 and uses shared passage IDs after alignment. Neither is ARI.
Component-level means, extrema, fitted/converged sample counts, distinct omission
sets, reasons for skipped fits and converged-only cosine summaries are retained.
These describe sensitivity to omissions and initialization, not confidence intervals.

The reviewed audit uses the original 460 segments (458 nonzero vectors), the
194 substantive segments and the broader 198-segment subset. It compares ranks
4, 6 and 8 without selecting from their results. Each rank uses three starts;
rank 6 receives 30 full-pipeline meeting refits per policy: nine full fits and
90 grouped fits, totaling 297 optimization starts. All selected fits met the
configured stopping rule. Six meetings yield just six distinct leave-one-meeting
omissions; repeated fits add initialization checks, not independent source evidence.

| Inclusion | Usable | Rank-6 squared reconstruction fraction | Mean refit cosine | Mean mixture L1 |
| --- | ---: | ---: | ---: | ---: |
| Complete corpus | 458 | 22.4% | 0.918 | 0.226 |
| Reviewed substantive | 194 | 21.3% | 0.877 | 0.597 |
| With mixed remarks / fragment | 198 | 21.1% | 0.897 | 0.546 |

Full-to-substantive component alignment averages only 0.364, with mixture L1
1.098 on the 194 shared passages. Changing inclusion changes vocabulary, IDF,
sample size and the factorization together; this is not a causal estimate of
removing procedure. Reconstruction fractions across different matrices are not
a model-quality contest.

The full fit includes term combinations such as `assembly, address, excellency,
escort, request` and `minister, affairs, foreign, floor, give`. The substantive
fit instead includes both issue terms and stylistic wording. Its weakest
component mean cosine is 0.768; starting-point mean cosines to the selected
fit are 0.852 and 0.882 for the two alternatives. Source examples can combine
different substantive positions: shared wording does not establish shared policy.
No thematic names have been assigned.

## Reproduce and validate

```sh
node tools/compare_nmf.cjs corpus.json reviewed-mask.json nmf-output
node tools/render_nmf_comparison.cjs nmf-output/comparison.json nmf-audit.html
node tools/test_browser_nmf.cjs
python tools/check_nmf_reference.py --node node --corpus corpus.json --fits nmf-output
```

The independent checker compares 50 multiplicative-update iterations against
scikit-learn from identical supplied initialization, reconstructs all nine real
full-data fits with NumPy, and checks cross-policy alignment with SciPy's assignment
solver. Tokenization for those matrix checks is shared with production; they are
not independent transcript collection or tokenization validation. Unit tests cover
known low-rank reconstruction, convergence disclosure, scale normalization,
permutation-invariant alignment, missing vocabulary, limits, resampling, invalid
reviews, filtering and source-safe rendering. Browser acceptance covers actual
worker execution, completed-review import, source links, CSV/JSON/HTML/original
exports, stale results, cancellation, mismatch rejection and mobile layouts.
See [validation evidence](nmf-validation.json) and [comparison data](nmf-comparison.json).

## Recommended next steps

1. Inspect the top source examples and alternative starts for each substantive
   component, especially the less stable components. Name a pattern only after
   checking contradictory and mixed passages.
2. Compare the saved four-, six- and eight-component results, documenting a useful
   level of detail instead of choosing the lowest in-sample residual.
3. Expand beyond six meeting groups before making stronger stability claims.
   Audio/source verification remains a separate task for suspected transcript issues.
4. Proceed to regularized Gaussian mixtures on the existing retained PCA/LSA
   representations, with covariance constraints, soft membership and the same
   inclusion and grouped-refit checks. Keep component naming separate.
