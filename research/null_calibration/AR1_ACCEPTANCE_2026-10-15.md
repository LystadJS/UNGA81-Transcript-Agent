# Independent AR(1) nuisance-estimation engineering acceptance — 2026-10-15

**Decision: SCIENTIFIC ACCEPTANCE FAIL / WITHHELD.** New `temporal_ar1.py` estimates year-level nuisance variance and AR(1) rho exclusively from invented observed count rows; `resample_ar1` resimulates source-preserving year shocks with that estimated rho. It neither receives truth nor reads any empirical evaluation text. Existing PR #57 values, 37 reserved meetings, PR #60 files and publication gates are untouched. This is a deliberately restricted moment-method candidate, not a validated W1/W2 nuisance estimator.

## Test and provenance basis
- GitHub branch `feat/independent-null-calibration`, PR #67. Owned paths solely `research/null_calibration/**`.
- Committed Git blobs: `temporal_ar1.py` **16deea98c425e70d6069026de83f779d95221564**; `test_temporal_ar1.py` **3be32816e04de6295c6e418c3ca3aafcba46cc26**; `benchmark_ar1.py` **5791559d23cb1b5bf85b5f55c32ba360a4e6003f**. These Git blob SHA-1 hashes identify committed bytes; they are not fixture SHA-256.
- Local test execution: Python **3.13.5**, standard-library only, `python3 -m unittest -v test_temporal_ar1.py`: **6 passed / 0 failures**, using the locally authored mathematical implementation plus an independently recreated copy of `study.world`. The GitHub `test_temporal_ar1.py` and `benchmark_ar1.py` blob hashes match those local files exactly. The GitHub `temporal_ar1.py` blob does **not** match the local copy byte-for-byte because commentary/docstrings differ. Its numerical algorithm is materially the same on source inspection, but **exact-head end-to-end tests remain NOT VERIFIED**.
- Generated fixture design: master seed **810081**; deterministic `study.seeded` SHA256 scheme; 100 development synthetic worlds per scenario, 30 independent reference bootstrap fits per world; generator rho truth **0.55** held in benchmark scorer only (never passed to estimator). No frozen-design holdout or PR #57 1,999 reference draws used.
- All confidence intervals below are **uncorrected 2.5%/97.5% percentile intervals** over successful reference nuisance re-estimates, reported only if **all 30/30** fits succeeded. These are not guaranteed valid confidence intervals and are evaluated for coverage, not asserted to have it.

## Independent numerical recovery (local development execution)
| Regime | Worlds fitted / attempted | Reference fits succeeded / attempted | Complete intervals | Covering truth | Mean rho | Bias | RMSE |
|---|---:|---:|---:|---:|---:|---:|---:|
| 24 years, 4 meetings/year | **100/100** | **2,961/3,000** | 78/100 | 66/78 (84.6% conditional) | 0.420369 | -0.129631 | 0.261659 |
| 24 years, 4 meetings/year, misspecified heterogeneous meeting shocks | **99/100** | **2,823/2,970** | 50/99 | 35/50 (70.0% conditional) | 0.398722 | -0.151278 | 0.302578 |
| 16 years, 2 meetings/year | **92/100** | **2,316/2,760** | 19/92 | 15/19 (78.9% conditional) | 0.306001 | -0.243999 | 0.410764 |

**Failure accounting:** balanced: 37 bootstrap rho-boundary failures, two bootstrap nonidentified year variances, and 22 incomplete intervals; misspecified: one world boundary refusal, 135 bootstrap boundary failures, 12 bootstrap year-variance failures and 49 incomplete intervals; sparse: seven world boundary refusals, one world year-variance refusal, 266 bootstrap boundary failures, 178 bootstrap year-variance failures and 73 incomplete intervals. Failures are not silently converted to nonrejections or deleted from attempted denominators. Complete interval coverage is conditional on selection; unconditional nominal 95% coverage is **not established**, and rates are **not** publication-eligible.

**Development receipt SHA-256** (canonical pretty JSON stdout excluding printed checksum): balanced `aeb5643afbd7d6d32c61aa5035b84f984192090f09d3c402b6bdfa8188f9bca4`; misspecified `8e5ccc97f41072faaa3665802218baad9f1ccc17a78392adf6116dd3aa246d5e`; sparse `ebccf45e742142c0d023f4f27e5ddc45619c0038648fca74459d020cd4a3bd62`. These hashes identify local development-output reports, **not files committed to GitHub**. Local source is not byte-identical to the GitHub estimator; exact-head benchmark reproduction remains required.

## Engineering assessment
- **PASS (local development):** deterministic synthetic seeds, independently estimated year-rho and year-variance, estimated parameter used in reference generation, explicit source-family/short-year/one-meeting/selection/duplicate refusals, all six local targeted tests.
- **FAIL (statistical):** substantial finite-sample downward rho bias and subnominal conditional percentile coverage under all three regimes; sparse designs often unidentifiable; misspecification worsens coverage.
- **NOT RUN:** full committed baseline `test_calibration.py`, `test_extended.py`, `test_study.py`, and the new committed code together; latest-head GitHub Actions; numerical comparison to PR #60 REML likelihood at matched parameter vectors; source-family replication; W1/W2 refit; locked 16 development/120 holdout worlds × 99 references.
- **BLOCKED scientific use:** this independent count-proxy estimator has no estimate of affiliation/parent/speech covariance or selection probabilities, no source-authenticated original text/representation nuisance, no valid rho uncertainty construction, and no W1/W2 max-statistic search. This cannot establish null false-positive rates, real-data identification or calibration readiness.

## Commands for exact-head execution
```bash
cd research/null_calibration
python3 -m unittest -v test_calibration.py test_extended.py test_study.py test_temporal_ar1.py
python3 benchmark_ar1.py --worlds 100 --replicates 30
python3 benchmark_ar1.py --worlds 100 --replicates 30 --misspecified
python3 benchmark_ar1.py --worlds 100 --replicates 30 --years 16 --meetings 2
```

**Next step:** independent exact-head checkout, run all regressions and compare receipt SHA-256 hashes. Then improve estimator identification and uncertainty by predeclared likelihood/profile or hierarchical covariance alternatives in *development-only* simulations; never retrospectively adjust frozen thresholds or infer scientific acceptance from failed stress panels.
