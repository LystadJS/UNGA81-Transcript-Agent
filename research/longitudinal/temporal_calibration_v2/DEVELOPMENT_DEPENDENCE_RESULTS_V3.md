# V3 dependence-aware gamma and year-nugget diagnostics — development-only

**Disposition: NUMERICAL IDENTIFICATION NOT ESTABLISHED / FREEZE NOT APPROVED.** Fresh invented development worlds only. No prospective v3 holdout generated, no historical UN source outcomes read, no v2 frozen method/threshold/receipt edited, and no release/real-fit authorization.

## Reproduction and provenance

At source head containing `v3_dependence_benchmark.py` and `v3_dependence_study.py`, run from repository root:

```bash
OPENBLAS_NUM_THREADS=1 PYTHONHASHSEED=0 python -m research.longitudinal.temporal_calibration_v2.v3_dependence_study --phase development --repetitions 60 --out /tmp/new-unga81-v3-dependence-dev
python -m unittest discover -s research/longitudinal -p 'test_*.py' -v
```

The runner refuses existing directories, `--phase holdout`, and `--phase real`. The independently seeded **new development namespace** is `UNGA81-V3-DEPENDENCE-DEV-20261015-NO-HOLDOUT`; it does not reuse v2 or planned v3 confirmatory holdout. The generator independently constructs nested meeting/actor/year effects and phase-II audited transcript recovery, with generating truth available to evaluator code only. All failures are recorded by scenario, replicate, method and exact exception reason to `development_failure_ledger.json`; `development_aggregate.json` includes the complete per-method/per-scenario outcomes and failure reasons. No source-bearing rows, transcript bytes, original PDF documents or human labels are included.

Independent local development execution: Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, Linux; 60 repetitions per scenario. SHA-256 of generated complete `development_aggregate.json`: `ca50c8aab8efbfb2212ef2931ce524a5617ab77dbcf3d0110c1ad453a4c7afc4`. SHA-256 of the **complete synthetic failure ledger**, with every failed method attempt: `e4cfc4387e37eeac35f3dccd5e6d93254b5f15b63fcf5b66722986cc3d8091f3`. These are local execution receipts, not a claim of confirmed byte-identical replay on a different NumPy/Python runtime. All results are fictional and source-free.

## Gamma uncertainty: three dependence-sensitive comparisons

Methods share the audited outcome-dependent response **point estimator** `response_gamma()`, which estimates gamma by meeting-weighted respondent/nonrespondent logit with randomized second-phase q. Annual complete score sums are the resampling unit, not source observations treated as independent calendar years.

- `year_score_lag0`: source-weighted cluster sandwich with no temporal lag terms; reference baseline.
- `year_score_lag1/lag2`: Bartlett score-HAC including one/two year lags, with prespecified fixed bandwidths, positive-definite checks and finite-year support refusal.
- `circular_year_block4`: 160 independent linearized circular moving-block score draws of consecutive **four-year blocks**; never resamples individual speeches as independent years. It does **not** refit selection or gamma per bootstrap sample.

Development gamma attempts: **420 synthetic panels × 4 methods = 1,680 method attempts**; **1,200 method completions**, **480 recorded refusals**. Panel-level 420 attempts / 300 with successful fits / 120 refusals. **60/60 no-audit MNAR panels correctly refused**; all 60 weak-q panels also refused for insufficient independently recovered support. Every method counts each refusal.

Nominal-90% **diagnostic hit rates** against structural truth, not validated confidence-interval coverage (60 fitted development panels in each row):

| World | Independent-year L0 | Bartlett L2 | Circular block-4 | Mean gamma bias |
| --- | ---: | ---: | ---: | ---: |
| IID-year, correctly specified T16 | 83.3% | 76.7% | 70.0% | +0.016 |
| AR1 rho=.65, correctly specified T16 | 83.3% | 85.0% | 80.0% | -0.006 |
| AR1 rho=.65, omitted serial response effect T16 | 75.0% | 71.7% | 61.7% | +0.059 |
| AR1 rho=.65, omitted serial response effect T32 | 75.0% | 75.0% | 73.3% | +0.072 |
| AR1 rho=.85, omitted serial response effect T16 | 75.0% | 73.3% | 65.0% | +0.082 |

For the T16 rho=.65 *omitted response-year effect* world, the median diagnostic gamma SE was 0.193 (L0), 0.180 (L2) and 0.166 (block-4), showing that dependence-sensitive methods can be **more overconfident**, not automatically safer. The omitted year response shock changes the target of an outcome-only logistic model; variance corrections **cannot repair structural-gamma bias**. Even in correctly specified development worlds, none demonstrates acceptably calibrated coverage here, and the 16 annual blocks do not justify standard asymptotic claims. These finite simulation results do not establish a winner.

## Nugget identifiability, external replicate noise and failures

A stationary-year Gaussian covariance of the form `sigma² AR1(rho) + (year_nugget² + measurement_noise²) I` has **identical** covariance-score derivatives for the two diagonal nuisance variances. Its unrestricted four-parameter expected covariance information has rank three at rho=.65, irrespective of horizon; at rho=0 it has rank two. Pure annual outcome covariance can never separately identify the diagonal components. Only independently justified external measurement information can break the *exact* measurement-vs-nugget alias, not the weak AR1-vs-year-nugget finite-sample separation.

With externally fixed measurement-noise variance, the local Fisher curvature remains extremely weak near rho=.05: at T16, dimensionless information condition number ~371,346 (with year nugget 0.025), versus ~27.4 at rho=.65. A positive local information eigenvalue is not reliable point recovery.

The exploratory **non-oracle** within-era quasi-moment fit uses observed year means, separately estimated external replicate error variance and lag-1/lag-2 moments; it never receives generating rho/nugget. Its predeclared refusals are explicit, **not successful covariance recovery**.

Covariance development: **480 fits attempted (8 source-free cells × 60)**; **29 usable**, **451 refusals**. Refusal categories: 373 nonpositive lag moments, 53 negative implied variance components, 25 out-of-support rho ratios.

| Synthetic covariance world | Usable / 60 | rho RMSE on completed fits only |
| --- | ---: | ---: |
| T16, rho=.05, nugget=0 | 2 | .697 |
| T16, rho=.05, nugget=.025 | 2 | .657 |
| T16, rho=.65, nugget=0 | 2 | .219 |
| T16, rho=.65, nugget=.025 | 2 | .253 |
| T32, rho=.05, nugget=0 | 2 | .342 |
| T32, rho=.05, nugget=.025 | 3 | .561 |
| T32, rho=.65, nugget=0 | 9 | .228 |
| T32, rho=.65, nugget=.025 | 7 | .211 |

**Do not interpret low RMSE on 2/60 fitted worlds as estimator success.** Successful fits are a severely selected subset, with unknown error over refused attempts. The experiment is a diagnostic of insufficient information, not an acceptable alternative covariance estimator.

## Count and failure ledger reconciliation

`gamma: 1,680 attempted = 1,200 completed + 480 refused`.

`covariance: 480 attempted = 29 completed + 451 refused`.

`all failed method attempts: 480 + 451 = 931`; the deterministic runner preserves the full 931-entry synthetic failure ledger, not just total failures. `holdout_attempted=0`, `statistical_acceptance=false`, `real_fit_authorized=false`.

## Prospective freeze disposition

**NOT ACCEPTED.** Preserve PR #68's prior engineering-only v2 *negative* outcome. The prospective v3 freeze candidate remains `UNAPPROVED_DESIGN_CANDIDATE_NOT_FROZEN`; no frozen threshold changes, no sanctioned real 2008–2023 model.

The next prospective protocol requires: (i) a correctly specified response model accounting for serial year propensity shocks, with individually audited missing outcomes and explicit positivity; (ii) externally justified measurement-error versus intrinsic nugget separation or partial-identification bounds; (iii) a credible T16 uncertainty strategy with all failure categories and minimum support rates; (iv) approved code hashes, independent confirmatory generator/seed namespace, exact thresholds and separate independent methodological signoff *before* any holdout.
