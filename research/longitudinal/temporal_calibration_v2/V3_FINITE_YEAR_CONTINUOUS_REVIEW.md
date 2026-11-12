# W4 prospective v3: finite-year gamma refits and continuous covariance sensitivity

**Status: development-only engineering evidence; no statistical freeze or release.** This is a new, independently seeded fictional development study and a mathematical variance-bound proof, not an authorized v3 holdout or a real 2008–2023 model. Original v2 preregistrations, thresholds, results, code, sources and 37 reserved October 2026 transcripts remain unchanged.

## Conditional estimand and finite-year gamma uncertainty

The target of the response model is the *conditional within-calendar-year* logit outcome slope, assuming a common gamma and otherwise unrestricted annual logit intercepts. This is not a marginal response-model coefficient. Feasible estimation requires actual original-meeting inclusion probabilities `pi`, strictly positive independently randomized phase-II recovery probabilities `q` for missing transcript **outcomes**, verified original meeting/actor/source linkages, and adequate within-year response/audit support. The synthetic panel alone does not establish any such historical audit.

`v3_finite_year_continuous.py` uses **circular consecutive four-year or eight-year blocks of complete years**, resampling all selected original meetings, their actor rows, observed responses and their already randomized recovery-audit outcomes *as wholes*, then **refitting the year-fixed-effects logistic model** in each bootstrap draw. It retains every failed refit, enforces at least 75% completed bootstrap support and refuses eight-year blocks at T16 because fewer than three blocks would be available. A basic percentile interval and bootstrap SE are reported as **diagnostics only**. It does not recreate the source-meeting or audit sampling stage per draw, preserve actor trajectories across unrelated circular blocks, or establish short-T bootstrap consistency. It does not supply a calibrated 16-year confidence interval.

A separately computed year-score HAC lag-2 diagnostic remains a reference. Neither technique resolves unequal spoken languages, repeated verified speakers, informative source selection, common-gamma misspecification or 16-year nonstationary trends.

## Continuous nuisance variance bound: formal conditional claim

For an equal-year two-era mean contrast `beta_hat = w'Y` with `w=(-1/T_pre,...,+1/T_post)`, suppose annual deviations are **unbiased jointly Gaussian** with
`Cov(Y) = s²[(1-lambda)R_AR1(rho) + lambda I]`,
where `0 <= rho_lo <= rho <= rho_hi < .95`,
`0 <= lambda_lo <= lambda <= lambda_hi <= 1`, and a separately defensible external source supplies `s² <= s²_max`.

For every lag k, `w'R(rho)w = w'w + Σ c_k rho^k`, `c_k = 2 Σ_i w_i w_(i+k)`. On a nonnegative rho interval, a rigorous **upper** bound is obtained by evaluating terms with `c_k >= 0` at `rho_hi` and terms with `c_k < 0` at `rho_lo`. The resulting expression is affine in `lambda`, so its maximum is attained at a lambda endpoint. Consequently `V_max=s²_max max_lambda[(1-lambda) U_AR+lambda (w'w)]` exceeds `Var(w'Y)` **for all real rho/lambda within the declared continuous rectangle**, not merely a finite nuisance grid. A Gaussian `beta_hat ± z_.95 sqrt(V_max)` is then at least nominal-90% *conditional on all these restrictions and unbiasedness*. This mathematical claim does **not** establish that these bounds are source-valid, that selection-adjusted year summaries are unbiased, that the annual law is Gaussian, or that an external scale upper bound actually exists for UN sources.

The development generator explicitly labels `s²_max=.12` as an invented hypothetical assumption, **not an independently measured empirical scale**. Tests numerically verify the analytic bound over a 17×15 interior mesh but the proof is termwise algebraic for the full nonnegative continuum. The narrower assumed nuisance rectangle is nested inside the wider one, hence its conservative maximum variance cannot exceed the wider bound under identical scale assumptions. The code does not recover rho or the year nugget and neither envelope is a formal nuisance-parameter identified set. Negative controls place true rho, scale, stationarity or annual-mean bias outside assumed conditions; their observed beta hits have no interpretation as coverage guarantees.

## New development experiment and all denominators

Namespace `UNGA81-V3-FINITEYEAR-CONTINUOUS-NEW-DEV-20261015`, independent of prior v2/v3 confirmation. Separate generator/evaluator identities for all known truth, never fed to either estimator. Synthetic meeting strata, recurring fictional actor effects, year/meeting noise, outcome-dependent response, audit q, short support, changing gamma, and nonstationary covariance are explicitly represented.

**Exact-head native CI replay** ran 12 new development panels per cell with 20 attempted refits per eligible block bootstrap. For gamma, 6 scenarios × 3 methods × 12 = **216 method attempts: 105 completed, 111 refused**. All **1,160 bootstrap refit attempts completed** when their parent estimator passed support, while correctly refusing all unsupported parent fitting; no failed bootstrap refits were silently excluded. Source-free failure masks retain every method-refusal identity. Eight-year blocks correctly refuse the T16 cells, unaudited MNAR and weak q fail, and a T32 case lacks annual audit support.

Covariance: 7 scenarios × 2 continuous nuisance ranges × 12 = **168 sensitivity calculations, 168 delivered, 0 numerical refusals**. Outside-range, nonstationary and selection-bias controls deliberately return *uncertified sensitivity values*, not fitted-interval successes. All **111 method refusals**, including every scenario, method and replicate, are preserved in the machine-readable `v3_finite_year_failure_masks.json` and must match full independent CI replay.

### Sample development diagnostic outcomes (not inferential evidence)

| Source-free gamma world | HAC lag-2 90%-shaped hit | Refitted 4-year block 90%-shaped hit | Completed panel denominator |
| --- | ---: | ---: | ---: |
| T16, IID year and correctly specified slope | 9/12 (75.0%) | 7/12 (58.3%) | 12 |
| T16, serial outcome/response-year process | 10/12 (83.3%) | 7/12 (58.3%) | 12 |
| T32, serial outcome/response-year process | 10/11 (90.9%) | 9/11 (81.8%) | 11 |
| T16, changing within-year gamma | WITHHELD: no single common truth | WITHHELD | 12 |
| T16, q=.025 or q=0 | REFUSED | REFUSED | 0 |

A nominal-90% Bernoulli hit statistic based on 12 completed draws has Monte Carlo standard error about **8.7 percentage points**; sample differences cannot determine method superiority. The developmental evidence does not favor certification of the block-refit procedure. Each gamma method retains `calibrated_interval=false`.

| Continuous covariance world | Wide envelope 90%-shaped diagnostic hit | Narrow envelope diagnostic hit | Assumed covariance conditions |
| --- | ---: | ---: | --- |
| T16, rho=.65, lambda=.35, scale=.075 | 12/12 | 11/12 | Both assumed sets contain truth |
| T16, rho=.85, lambda=.70, scale=.115 | 12/12 | 12/12 | Only wide set contains truth |
| T16, rho=.92 (outside bounds) | 12/12 | 12/12 | Both false |
| T16, scale=.30 (above upper bound) | 12/12 | 11/12 | Both false |
| T16, nonstationary or biased annual summaries | 12/12 | 11–12/12 | Gaussian unbiased/stationary law false |
| T32, rho=.65, lambda=.35, scale=.075 | 12/12 | 12/12 | Both contain truth |

At T16, wide hypothetical width is **1.159** and narrow width **.975** under the invented external upper scale `.12`. Both are conservative and assumption-dependent. In particular, a zero-refusal model can still be invalid under wrong covariance assumptions—numerical delivery is not statistical success.

## Reproducibility, acceptance, and next decision

Run from a permitted full repository checkout:

```bash
OPENBLAS_NUM_THREADS=1 PYTHONHASHSEED=0 python -m research.longitudinal.temporal_calibration_v2.v3_finite_year_study --phase development --repetitions 12 --bootstrap 20 --out /tmp/new-v3-finite-continuous
python -m unittest discover -s research/longitudinal -p 'test_*.py' -v
```

The runner refuses overwrite, `--phase holdout` and `--phase real`. `test_v3_finite_year_replay.py` independently re-executes every fixed-seed development case, checks the retained aggregate and lossless per-method/per-replicate failure masks, and compares all 12-repetition scenario diagnostics within numerical tolerance. All source-free results are prohibited from being presented as observed diplomatic source evidence.

**Disposition: engineering-only design and falsification, prospective v3 statistical freeze NOT ACCEPTED.** The next prospective protocol must separately establish a valid empirical total year-scale upper bound and covariance region, an authentic randomized transcript-outcome audit, serial-year/actor/meeting-aware gamma uncertainty, common-slope model adequacy, realistic source nonstationarity, calibration sample-size requirements, and independent methodological signoff. Neither this experiment nor the previously examined v2 holdout may be used as an independent v3 confirmatory sample.
