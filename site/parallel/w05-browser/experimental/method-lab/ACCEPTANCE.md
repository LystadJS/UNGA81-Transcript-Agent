# W5 acceptance record — 8 October 2026

**Classification: engineering-only; no public release or statistical inference.**

## Executed evidence

| Gate | Result | Basis |
| --- | --- | --- |
| Main, interfaces and ownership inspected | PASS | Branch from `773ecc90310d674905889441491937b8a13a3515`; upstream analysis, cluster, NMF, latent and parallel v1 contracts read |
| Relational validator | PASS — 13/13 | Synthetic V8 checks for orphan/duplicate IDs, unavailable sources, mismatched coverage, mixture sums, invalid source basis, withheld split, version and comparisons |
| JavaScript source syntax | PASS — 6/6 initial files | Parsed contracts, adapters, worker, task controller, browser controller and Node test; final recheck needed |
| Worker cancellation | PASS — simulated | Terminated active task, ignored late result, safely started another |
| Existing computational pipeline | PASS — synthetic V8 harness | Six synthetic browser records, PCA k-means/LSA PAM/NMF, six retained per fit, 90 progress callbacks, source-bound pack/replay. Used a **noncryptographic digest shim** due to missing WebCrypto, so not a native cryptographic test |
| Validator benchmark | PASS — V8 isolate only | Median of five validation+normalization runs: 5 rows 0 ms, 100 rows 2 ms, 300 rows 5 ms, 600 rows 9 ms; 600-row fixture had 1,800 results and ~686 KB JSON; no sampling. Not a device or inference benchmark |

## Not yet accepted

| Gate | Status | Required step |
| --- | --- | --- |
| Native SHA-256, legacy/current archive and failure tests | NOT RUN | Execute `node site/parallel/w05-browser/experimental/method-lab/test-method-lab.cjs` and log stdout/exit status |
| Desktop/mobile browser behavior | NOT RUN | Execute `BROWSER_BIN=chromium node site/parallel/w05-browser/experimental/method-lab/test-browser.cjs`; test 1440px/390px, source inspection, export invalidation and outbound requests |
| Actual browser/Node numeric parity | NOT RUN | Browser suite compares retained PCA/LSA score matrices with tolerance 1e-7. Do not compare UMAP display coordinates |
| Device resource and cancellation load tests | NOT RUN | Record available heap, process RSS, wall time, cancellation and errors using authorized development data |
| Full coordinator v1 structural schema validation | PARTIAL | Run authoritative schema validator as well as relational adapter tests |
| W1 source-aware validation and W2–W4 production envelopes | BLOCKED | Await source group/selection audits, family pair-opportunity accounting, graph diagnostics and longitudinal source identity |
| Optional local MiniLM | NOT IMPLEMENTED | Pinned local model, tokenizer, licensing, numeric parity, browser privacy review and cold/warm inference/device memory benchmarks required |
| Production wiring/website mirror | NOT APPLICABLE | Coordinator-only separate PR following upstream acceptance |

### MiniLM feasibility boundary

A hypothetical 600 × 384 float32 embedding array occupies **921,600 bytes (~0.88 MiB)**. A 600 × 600 float64 similarity matrix occupies **2,880,000 bytes (~2.75 MiB)**. These are arithmetic storage requirements, **not** measured MiniLM model size, tokenizer memory, peak RSS or inference time. No MiniLM model was loaded, run or downloaded. Inference feasibility cannot be approved on these estimates.

### Dependencies / privacy

- W1: validate source-group dependence and nuisance hypotheses before inferential interpretations.
- W2–W4: supply accepted `un.parallel-analysis.v1` envelopes with correct IDs, hashes, settings, missingness and fit ledgers. Synthetic examples do not certify correctness.
- Coordinator: verify exclusive W5 diff and fresh main, run both suites and existing source/browser regressions, review PR checks, and integrate shared UI or release only in a separate PR.
- **No** reserved October 5–6 meeting text, private annotations, credentials, frozen evaluation lock, original source hashes or D1 publication gates were inspected or modified. Public fixtures are synthetic and text-free.

This record intentionally distinguishes executed V8 checks from pending native Node, browser and mobile acceptance.
