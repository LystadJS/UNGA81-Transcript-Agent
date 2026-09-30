# Research implementations and review-data foundation

**The daily D1 pipeline still has 12 executable adapters.** This directory adds
29 standalone computational kernels toward the 30-method daily-adapter backlog.
They are tested with explicitly synthetic engineering fixtures and are not
connected to the daily publication path. One kernel (M26) still needs an identified package/interface and
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

## I7 additions and outstanding work

Nine further kernels are now implemented and tested: M14, M18, M19, M20,
M28, M29, M30, M35 and M42. See [I7 scope and reproduction](I7.md) for their
contracts, package versions, limitations and primary sources. This brings the
R total to 27. [I8](I8.md) adds two Python paths: M16 local BERT fine-tuning
and M38 a GRU sequence model. The standalone total is now 29; M26 remains
unimplemented. No new daily adapter is implied.

`catalog.json` records all 30 backlog IDs and their original prerequisites. It
does not overwrite the D1 registry or advertise these prototypes as daily adapters.

## Run the engineering tests

For neural setup, an offline fictional demo and saved-model predictions, see
[I8](I8.md). Run `python research/methods.py` to check current method accounting.

From the repository root, with R installed:

```powershell
Rscript research/setup.R
Rscript research/test_engines.R research/library
Rscript research/test_more.R research/library
python tools/test_review_data.py
```

The tests construct synthetic inputs in memory/temporary folders. No actual
human labels are fabricated for the project. Numerical fixtures check known
geometry, simulated changes and associations, deterministic behavior, bounds,
noise/coverage handling, and leakage/invalid-input rejection. See
[current I8 acceptance](validation/i8/README.md), [prior I7 acceptance](validation/i7/README.md) and [prior I6 acceptance](validation/README.md) for executed results.

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
