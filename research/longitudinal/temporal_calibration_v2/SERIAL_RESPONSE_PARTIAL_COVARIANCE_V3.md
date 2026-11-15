# V3 prospective serial-response and covariance-sensitivity development review

**Disposition: DEVELOPMENT-ONLY NEGATIVE/CONDITIONAL EVIDENCE. NOT A V3 FREEZE, NOT A CONFIRMATORY HOLDOUT, AND NOT AN EMPIRICAL FIT.** The prior v2 engineering-negative acceptance, all original thresholds, source records, sealed evaluation, and real-fit prohibitions are unchanged.

## New estimators and what they identify

`v3_serial_partial.py` compares three audited-response slope gamma estimators using *observed respondents* and *independently randomized q-audited nonrespondents* only. Original-meeting inclusion uses 1/pi weights; audited nonrespondents use 1/(pi*q), with explicit whole-year response/audit support, missing-outcome leakage and positivity refusals.

- **Pooled logit:** current auditable but year-heterogeneity-omitting reference method.
- **Year fixed-effects logit:** estimates one annual response intercept per calendar year and a common conditional gamma. It can eliminate omitted latent year *intercepts* from the conditional response slope *if* the within-year slope and audit model are correctly specified and support exists. Repeated year contributions are not declared independent; the year-profile score lag-2 standard error is a **development diagnostic only**.
- **Estimated AR1 year-effects:** estimates a rho proxy from *fitted* annual intercepts (not generating truth) and refits with an explicitly declared year-effect smoothing penalty 6.0. Neither the AR1 nuisance value, the penalty nor the resulting gamma SE is a confirmed valid T16 inferential model. Shrinkage can reinstate year-confounding bias.

These methods do **not** authenticate real UN response audits; only synthetic randomized q is available. No method is authorized to fit the historical panel. A year-specific intercept absorbs serial latent propensity variation but by itself does not identify the random-year AR1 covariance law or substantiate a confidence interval with 16 year blocks.

`covariance_union()` compares **wide**, **narrow** and **externally constrained** nuisance *assumption sets*. Each computes a union of two-era GLS intervals over hypothesized rho and **effective** diagonal nugget fractions, estimating beta and total scale from observed annual measurements only. The narrower set presupposes a more restrictive rho/nugget range; it is **not** a new point estimator. The external version obtains a *development-only*, independent Gaussian equal-error replicate-pair variance lower bound and removes hypothesized covariance configurations whose diagonal independent variance falls below that lower bound. This links external measurement evidence to the admissible nuisance region without assuming the true simulation variance. These are **sensitivity envelopes, not calibrated confidence intervals or formal frequentist identified sets**. Correlated source replicate errors, absent external provenance, invalid annual support and empty constrained grids refuse.

The nuisance covariance is `sigma_AR² R(rho) + (sigma_year_nug² + sigma_measure²) I`. Year nugget and measurement error have identical `I` derivatives. True intrinsic year-nugget variance remains unidentified absent distinct external information, even when measurement error can be constrained independently. The sensitivity restrictions are hypothetical and MUST be externally justified and locked before any confirmatory use.

## Exact invented development design

Entirely **new disjoint development namespace**: `UNGA81-V3-SERIAL-PARTIAL-NEW-DEV-20261015-NO-HOLDOUT`. The generator was written separately from v2 and the earlier v3 dependence experiments. All truths remain evaluator-only and all missing unaudited outcomes are `NaN` in the estimator input.

- Gamma: T16/T32, nine original meetings per year, three fixed strata of three original meetings, two drawn per stratum without replacement (pi=2/3), twelve recurring fictional affiliation effects and a declared preadmission structural risk exclusion. Outcomes and year-specific response propensity intercepts have separately declared Gaussian serial innovations (rho=0 or .65), including correlated outcome/response shocks; true conditional gamma=-1.25. Randomized independent nonrespondent audit q=.35, .025 or 0. Three gamma methods across six scenarios.
- Covariance: T16/T32 scalar two-era true beta=.20; stationary AR1 rho=.05/.65/.85, independent year-nugget, annual observation noise and an entirely *separate* independent Gaussian replicate-pair measurement experiment (32 pairs). Negative controls: nonstationary variance shift and correlated replicate errors. Three sensitivity alternatives across six scenarios.
- Repetitions: **30 per scenario**, explicitly a limited development diagnostic budget, not a preapproved confirmatory Monte Carlo study. Even a 90% binomial hit rate at n=30 has Monte Carlo SE roughly 5.5 percentage points; no method selection or threshold adjustment may be justified from these exploratory results.

## Fresh numerical development results

Independent development execution used Python 3.13.5 / NumPy 2.3.5 / SciPy 1.17.0 with `OPENBLAS_NUM_THREADS=1`, `PYTHONHASHSEED=0`. All numbers below are observed finite-seed engineering evidence.

### Gamma point recovery and serial-year uncertainty

| World (complete fits /30) | Pooled gamma bias | Year-FE gamma bias | AR1-smoothed gamma bias | Year-FE nominal-90% diagnostic hit |
| --- | ---: | ---: | ---: | ---: |
| Correct iid T16 (30) | -.028 | -.065 | -.044 | 76.7% |
| Serial independent response shocks T16 (23) | +.051 | -.055 | +.004 | 78.3% |
| Correlated outcome/response year shocks T16 (29) | **+.411** | **-.039** | **+.158** | 86.2% |
| Correlated outcome/response year shocks T32 (22) | +.444 | -.118 | +.114 | 81.8% |
| Weak audit q=.025 T16 (0) | withheld | withheld | withheld | withheld |
| No independent audit q=0 T16 (0) | withheld | withheld | withheld | withheld |

Year fixed effects reduce structural-gamma point bias in the correlated T16 *development* world; AR1 smoothing is more biased in that same world despite estimating its nuisance rho proxy. However, 86.2% of completed intervals containing the true gamma is not evidence of passing nominal-90% calibration, and misses under q support also matter. T32 cannot be interpreted as adding years to the actual 2008–2023 cohort.

### Hypothetical covariance sensitivity sets

| World | Wide envelope diagnostic hit; median width | Narrow envelope | External-replicate constrained |
| --- | --- | --- | --- |
| Stationary T16 rho=.65 | 86.7%; 1.044 | 86.7%; .903 | 86.7%; .819 |
| Strong AR1 T16 rho=.85 | 100%; .963 | 96.7%; .826 | 93.3%; .755 |
| Near-zero rho T16 | 100%; 1.447 | 100%; 1.218 | 100%; 1.106 |
| Stationary T32 rho=.65 | 100%; 1.088 | 100%; .842 | 100%; .850 |
| Nonstationary year nugget T16 | 100%; 1.836 | 100%; 1.589 | 96.7%; 1.485 |
| Correlated external replicate errors T16 | REFUSED | REFUSED | REFUSED |

These are **empirical diagnostic hits**, *not* validated 90% CI coverage. They depend directly on the externally assumed nuisance sets. In all current stationary simulation worlds, the **narrow** range excludes the evaluator's true effective nugget fraction (about .496 versus a maximum assumed .45), yet can still enclose beta by chance. A sensitivity envelope catching beta when its nuisance restrictions are false is not evidence of valid nuisance identification. Constraining the envelope by external measurement evidence reduces median width but can also lose diagnostic hits. The nonstationary case explicitly violates the covariance family assumptions.

## Complete attempt accounting and reproducibility

```
Response methods: 540 attempted = 312 completed + 228 refused
Covariance sensitivity: 540 attempted = 450 completed + 90 refused
Total new development method attempts = 1,080; failed = 318
```

All 318 refusals are retained exactly in the source-free `v3_serial_partial_failure_index.json` by scenario, method family, replicate bitmask and reason. Across distinct methods: 138 year-specific q/response support failures, 90 mandatory unaudited-MNAR refusals and 90 correlated external measurement refusals. The complete uncompressed development failure ledger SHA-256 in the local Python-3.13.5 environment is `0b9390788b4bab31bad532161f10e723a50d563640b034607b23753b888b9029`; aggregate SHA-256 `3707fdb4635addad1b5209379aefd4b744b76cd6e421388245c0b91280a4d7ef`. Hashes denote local execution artifacts; cross-runtime floating representation need not yield identical byte streams. The committed CI replay tests **exact failure identities**, not floating-output byte identity.

Reproduce from repository root:

```bash
OPENBLAS_NUM_THREADS=1 PYTHONHASHSEED=0 python -m research.longitudinal.temporal_calibration_v2.v3_serial_partial_study --phase development --repetitions 30 --out /tmp/new-v3-serial-development
python -m unittest discover -s research/longitudinal -p 'test_*.py' -v
```

The CLI refuses `--phase holdout`, `--phase real`, or overwriting any existing output directory. All target/failure information is invented and source-free; no real original PVs or 37 reserved October 2026 transcripts were accessed.

## Independent prospective freeze decision

**NOT ACCEPTED / NOT FROZEN.** Year-FE logistic is a *development-only point-estimation candidate*, not a calibrated T16 interval. AR1 annual-intercept smoothing requires prospective penalty/uncertainty work. External measurement calibration requires authentic source-independent Gaussian replicate evidence; nuisance range restrictions require independently justified admissible parameter bounds. No independent randomized follow-up audit of historically unavailable speech outcomes exists. The v2 T16 rho failure remains binding.

Before any new v3 confirmatory holdout, independently preregister: (i) conditional gamma target versus marginalized gamma; (ii) year intercept and source-response measurement assumptions; (iii) source-level positivity, q audit design and complete inclusion support; (iv) nuisance rho/effective nugget partial-ID assumptions and external source; (v) method choice and Monte Carlo/false-confidence/completion criteria; (vi) approved independent holdout generator, seed and code/hash receipt. Do not change the frozen v2 thresholds or use prior v2/v3 experimental outcomes as a fresh holdout.
