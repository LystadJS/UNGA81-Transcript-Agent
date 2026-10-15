# PR #67 — independent annual-mean profile REML comparison (engineering-only)

**Date:** 2026-10-15. **Result: FAIL / SCIENTIFIC READINESS WITHHELD.** This is a development-only synthetic comparison, not the prospective frozen PR #57 null study, not PR #60's five-component covariance estimator, and not an empirical-source analysis. Neither original transcripts nor the reserved 37 heldout meetings were read. No frozen critical values, G01–G13 release gates, or PR #60 files were modified.

## Source and execution
- Starting worker head: `b1f9079d6a8333af5f57e54f3f1b90fb9da164a6`; all new edits under `research/null_calibration/**`.
- Committed `profile_reml.py` Git blob `e73cd98caf321c3f2916f7ada9406552b9160742` was **byte-matched by local `git hash-object`**, and its numerical implementation was executed locally.
- Benchmark: `compare_reml.py` (committed; local comparison code is semantically equivalent but byte-different), master seed **810081**, 50 independent development worlds per scenario. Year shock truth **rho=.55** used by benchmark scorer only. No oracle generating nuisance parameters supplied to either estimator.
- Python **3.13.5**, NumPy **2.3.5**, SciPy **1.17.0**; local commands `python3 compare.py` and `python3 -m unittest -v test_profile_reml.py test_temporal_ar1.py`.
- **11/11 local targeted tests PASS (0 failed)**: 5 REML plus 6 prior AR1 tests. Both committed test files have exact local matching Git blob identities; `temporal_ar1.py` source-equivalent local implementation differs in comments/docstrings from committed Git blob. **Full exact-head suite remains NOT VERIFIED**, not PASS.
- Local `compare_output.jsonl` SHA-256 **a6d48e61c6a902baec5be07d6e5eda9fd93e42d19e72d8824ab6816603a45c58**; locally executed `profile_reml.py` SHA-256 **5dd6bc6f921f77a510da7bfd16d02cfd167360d0fc4055c07f79d62ed7a26180**. The numerical-receipt hash is on locally authored source-equivalent compare.py and is **not** an exact-head CI artifact.

## Estimators and identification limits
- Moments: upstream `temporal_ar1.estimate_ar1` uses pooled meeting prevalence, subtraction of within-year dispersion, then lag-one year covariance; no confidence interval is returned by this method.
- Reduced Gaussian REML: source-group checks inherited from the moments estimator; fit annual mean prevalence with an intercept and covariance `year_variance * rho^abs(year_i-year_j) + diag(within-year meeting variance / meetings)`. For each of 21 prespecified rho grid points in [-.85,.85], optimize year variance; include GLS intercept, covariance log determinant and `log(1'V^-1 1)` restricted correction. Use 1-df 3.8414588 likelihood-ratio cutoff for *exploratory* profile intervals, refuse unbounded or boundary profiles. Independent of PR #60's objective.
- Heteroskedastic within-year variances are plugged in as known and not jointly estimated; finite-sample uncertainty in them is **ignored**. Annual-mean Gaussian approximation is misspecified by truncation/binomial emissions, and subtracting nuisance variation can confound year correlation. Grid interval boundaries are approximate; incomplete profiles cannot be described as a valid 95% CI.
- Neither model supplies an identified affiliation/speech/parent covariance, missing-source selection model, representation effect, nor full W1/W2 family-balanced clustering refit. This is **not** a comparison of equally complete scientific estimators.

## Numerical results (50 worlds in each scenario)

| Synthetic scenario | Estimator | Converged / attempted | Mean rho | Bias | RMSE | Profile intervals covering truth / complete |
|---|---|---:|---:|---:|---:|---:|
| Balanced 24y × 4 meetings | Moments | 50/50 | 0.438344 | -0.111656 | 0.275275 | N/A |
| Balanced 24y × 4 meetings | Reduced REML | 12/50 | 0.162917 | -0.387083 | 0.403022 | 10/12 (83.3% conditional) |
| Heterogeneous meeting dependence, 24y × 4 | Moments | 49/50 | 0.419761 | -0.130239 | 0.280856 | N/A |
| Heterogeneous meeting dependence, 24y × 4 | Reduced REML | 13/50 | 0.150385 | -0.399615 | 0.413496 | 9/13 (69.2% conditional) |
| Sparse 16y × 2 meetings | Moments | 48/50 | 0.300316 | -0.249684 | 0.417883 | N/A |
| Sparse 16y × 2 meetings | Reduced REML | 7/50 | ~0 | -0.550000 | 0.559304 | 6/7 (85.7% conditional) |

**Failure counts / exact attempted denominators:**
- Balanced: REML 6 `rho_boundary` + 32 `unbounded_profile_interval` = 38/50 refusals; moments 0/50.
- Misspecified: REML 4 `rho_boundary`, 32 `unbounded_profile_interval`, 1 inherited `rho_near_or_beyond_boundary` = 37/50 refusals; moments 1/50.
- Sparse: REML 9 `rho_boundary`, 32 `unbounded_profile_interval`, 2 inherited `rho_near_or_beyond_boundary` = 43/50 refusals; moments 2/50.
- Across 150 worlds: **moments 147/150 fitted; REML 32/150 accepted; 25/32 conditional intervals covered truth**. Because all other REML profiles were withheld, overall parameter interval coverage is **not identified** and the conditional fraction is not a general coverage result.

## Computational cost (local single-process wall time)
| Scenario | Moments total / attempt | REML total / attempt | REML likelihood evaluations |
|---|---:|---:|---:|
| Balanced | 0.02008s / 0.000402s | 1.00793s / 0.020159s | 10,221 |
| Misspecified | 0.01894s / 0.000379s | 0.90233s / 0.018047s | 9,756 |
| Sparse | 0.00856s / 0.000171s | 0.65884s / 0.013177s | 10,295 |

Timing differences are exploratory single-machine measures, not stable deployment benchmarks; reported REML total includes attempted/refused fits.



## Exact-source local verification addendum — 2026-10-15

After the original development comparison, reconstructed the **actual committed Python source and tests** in the local execution directory and compared `git hash-object` of each against GitHub's blob ID. All matched, including `calibration.py` f71bcc60cdd107a6df46bee92937ce9a206302d0, `study.py` edcae986c67137e328f63a436e094d9eb0667eab, `temporal_ar1.py` 16deea98c425e70d6069026de83f779d95221564, `profile_reml.py` e73cd98caf321c3f2916f7ada9406552b9160742, `compare_reml.py` 634b99492e081ec1bf04058a0afe8e0a61049995, and all five unit-test files (their Git blobs were checked against the exact branch).

**PASS — full owned Python regression suite:** `python3 -m unittest -v test_calibration.py test_extended.py test_study.py test_temporal_ar1.py test_profile_reml.py`: **27 tests, 27 pass, 0 failures, 0 errors**, Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0. This is a genuinely newly executed, byte-for-byte committed-source local validation, **not** a GitHub Actions CI result and not an upstream full-repository integration regression.

**PASS — exact-source numerical benchmark replay:** `python3 compare_reml.py` from hash-matched committed files reproduced all 150 world-level numerical fits and all convergence/bias/RMSE/coverage denominators above exactly. As expected, wall-clock times differed slightly on replay: per-attempt moments **0.000382/0.000363/0.000163 seconds** and reduced REML **0.019845/0.018006/0.013300 seconds** for balanced/misspecified/sparse cases; total REML evaluation budgets unchanged at 10,221 / 9,756 / 10,295. Timing is non-deterministic and must not be treated as a fixture checksum.

This closes the prior **local exact-source Python-test blocker**. However, applicable GitHub Actions checks and full upstream W1/W2 and coordinator integration regressions are **not yet executed or attested**. The scientific covariance and identification failures remain; no inferential gate is promoted.

## Exact-head acceptance status and next work
New source is pushed to existing draft PR #67. GitHub Actions runs and combined statuses on prior head returned empty; without a runnable full GitHub checkout, **do not claim exact-head baseline regression PASS**. Required at new head:

```bash
cd research/null_calibration
python3 -m unittest -v test_calibration.py test_extended.py test_study.py test_temporal_ar1.py test_profile_reml.py
python3 compare_reml.py
```

**Readiness: NO.** Independent REML comparison did not rescue weak year-dependence identification. Next identify year versus meeting noise using a better hierarchical likelihood and jointly profile uncertain sampling variances, add independent objective/reference controls, and run full exact-head suite. Continue development only; do not run or use frozen holdout to tune.
