# I6: research implementations and review-data foundation

**The daily D1 pipeline still has 12 executable adapters.** This directory adds
18 standalone computational kernels toward the remaining 30-method backlog.
They are tested with explicitly synthetic engineering fixtures and are not
connected to the daily publication path. The other 12 kernels still need
implementation. A kernel is not a completed or released end-to-end method.

No new result can populate O1–O5. All kernel outputs have
`publication_eligible=false` and `daily_adapter_integrated=false`. Real and
unreviewed datasets are deliberately rejected until a reviewed-bundle loader,
source binding, method-specific acceptance and daily integration are implemented.
Passing the data checker alone does not remove that restriction.

## Implemented computational scope

| IDs | Scope now exercised in code |
|---|---|
| M03 | Validated cached-vector pooling: passages → statements → equally weighted country means. Encoder inference is still absent. |
| M04 | Cosine relevance against named prototypes in the same representation; no probability claim. |
| M10 | Deterministic UMAP sensitivity view with saved fit; no use as diplomatic distance. |
| M11 | Low-dimensional logistic baseline; rank, convergence and separation rejection. |
| M12, M15 | Fixed-policy elastic-net binary head; M15 requires representation identity. One issue at a time. |
| M13 | Bounded, single-thread probability forest. |
| M17 | Named-proposition four-class regularized head, calibration and abstention; never substitutes “neutral” for insufficiency. |
| M21 | HDBSCAN labels, noise, outliers and membership diagnostics. |
| M22 | Matched high-dimensional within-country cosine/chord distance. |
| M23 | Historical-only isolation forest with explicit missing-data refusal. |
| M24 | Observation-index, independent-Gaussian mean change via PELT/MBIC. Other dependence models are not implemented. |
| M25 | Rigid Procrustes on full-rank shared anchors; reports scale mismatch without silently rescaling. |
| M27 | Maximum-overlap cluster correspondence with arrivals, departures, splits and merges retained. |
| M37 | Binary next-comparable-observation logistic baseline. No calendar-date event prediction or complete multi-target forecaster. |
| M39 | Equal-duration, first-event complementary-log-log hazard; associations only. |
| M40 | Gaussian network-lag likelihood with preexisting graph and explicit bounded rho. |
| M41 | Ordinal conditional-choice relational events over known dyadic risk sets. Waiting-time modeling is absent. |

Classifier kernels enforce forward time, disjoint countries/content/observation
IDs and identical feature order across train, calibration and test. The fixed
hyperparameters are engineering policies, not optimized claims. Numerical test
scores are computed on untouched test rows and returned with a prevalence
baseline for binary tasks. This does not establish performance on diplomatic text.

## Remaining twelve kernels

| ID | Work still required |
|---|---|
| M14 | Versioned boosted-tree backend, bounded tuning and matched evaluation |
| M16 | Approved text-transformer checkpoint/tokenizer, fine-tuning implementation and measured resource/learning-curve acceptance |
| M18 | LDA fit/inference, count vocabulary, held-out topic quality/stability |
| M19 | Structural-topic metadata specification and fit/inference validation |
| M20 | Passage-embedding clustering plus class-level TF-IDF descriptors and exemplars |
| M26 | Exact pinned driftmapR interface and supported-regime/resampling evidence |
| M28 | Hidden-state fit and cutoff-respecting filtering for repeated sequences |
| M29 | Latent-transition measurement/invariance specification and estimation |
| M30 | Time-dependent mixture estimation, not repeated independent clustering |
| M35 | Appropriate graph likelihood, stochastic-block estimation and stability |
| M38 | Temporal neural architecture, approved sequence inputs and benchmark/resource acceptance |
| M42 | Bayesian hazard/exposure specification, priors, sampler/convergence and predictive validation |

`catalog.json` records all 30 backlog IDs and their original prerequisites. It
does not overwrite the D1 registry or advertise these prototypes as daily adapters.

## Run the engineering tests

From the repository root, with R installed:

```powershell
Rscript research/setup.R
Rscript research/test_engines.R research/library
python tools/test_review_data.py
```

The tests construct synthetic inputs in memory/temporary folders. No actual
human labels are fabricated for the project. Numerical fixtures check known
geometry, simulated changes and associations, deterministic behavior, bounds,
noise/coverage handling, and leakage/invalid-input rejection. See
[acceptance](validation/README.md) for executed results.

For a trusted, explicitly synthetic input R list matching a fixture in
`test_engines.R`, the immutable engineering runner is:

```powershell
Rscript research/run.R M11 input.rds research/runs/example.rds
```

It saves the input and code hashes, seed, runtime and package versions with the
result and writes a separate output checksum. It neither downloads a model nor
sends text to an external service. These outputs are ignored by Git.

## Build the real datasets next

Follow the [step-by-step dataset guide](../docs/DATA_GUIDE.md). Start with a small
independent annotation pilot, then expand using error analysis and learning
curves. Historical and event data need their own observation and comparability
contracts. Keep research examples, reviewed data, model acceptance and publication
decisions distinct.

Primary API/method references: [glmnet](https://glmnet.stanford.edu/articles/glmnet.html),
[uwot](https://cran.r-project.org/web/packages/uwot/refman/uwot.html),
[dbscan](https://cran.r-project.org/web/packages/dbscan/refman/dbscan.html),
[ranger](https://cran.r-project.org/web/packages/ranger/refman/ranger.html),
[isotree](https://cran.r-project.org/web/packages/isotree/refman/isotree.html),
[changepoint](https://cran.r-project.org/web/packages/changepoint/refman/changepoint.html),
[clue](https://cran.r-project.org/web/packages/clue/refman/clue.html).
