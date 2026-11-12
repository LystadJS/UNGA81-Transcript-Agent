# W4 Prospective V3 — hierarchical conditional gamma and external-scale covariance review

**Independent code/method review decision: ENGINEERING DEVELOPMENT PASS; STATISTICAL FREEZE NOT ACCEPTED.** This is a source-free *new development* benchmark, not independent human statistical signoff, not a prospective V3 holdout, and not a real historical UN speech model. The existing frozen V2 T16 temporal-correlation recovery failure remains binding. No v2 estimator, original v2 freeze threshold or source record is changed.

## 1. Conditional gamma target and hierarchical identification

The target is the **common within-calendar-year conditional response logit slope** `gamma` from

`logit P(R_imy=1 | Y_imy, year=y, included meeting)=alpha_y+gamma*Y_imy`.

This is *not* the marginalized gamma, a model of country positions, or an effect identified without missing-outcome verification. Positive `pi` probabilities for original-meeting inclusion and independently randomized positive `q` auditing of nonrespondent original speech **outcomes** are required. True calibration outcomes and generating rho are deliberately excluded from feasible estimator inputs. Original-source genre, delivered language, translation method, year roster, repeated-person identities and archival sampling generations must pass distinct comparability gates before any real application.

**New `v3_hierarchical_external.py` candidate:** (1) fit the original source-weighted annual intercept and conditional gamma FE logit using only observed/respondent or audited nonrespondent outcomes; (2) treat fitted annual intercepts as noisy measurements (approximate inverse conditional intercept curvature), estimate an AR1/nugget covariance from their marginal Gaussian pseudo-REML over a prespecified nuisance grid; (3) refit the original weighted response logit with a centered Gaussian annual-effect penalty using the *estimated* covariance; (4) report the gamma plug-in Hessian sensitivity. The Gaussian marginal REML is an **approximation to year-intercept estimates**. It is **not an integrated hierarchical Bernoulli random-effects likelihood**; it does not integrate uncertainty in rho/nugget/variance, actor/meeting dependence, the response/audit design or source inclusion probabilities. The current penalty and candidate grid are *development settings, not frozen methodological restrictions*.

Year random-intercept shrinkage assumes a credible process model; if annual response shocks correlate with annual Y distributions, penalization can restore the very confounding reduced by free year intercepts. The feasible year-effect `rho_hat` is derived from *estimated* intercepts, not generator truth, but that fact alone does not confer identifiability or reliable T16 recovery. The model is not an approved hierarchical interval estimator.

## 2. External covariance scale and conditional finite-year bound

The prior continuous covariance model is

`Sigma=s²[(1-lambda)R_AR1(rho)+lambda I]`.

The original termwise polynomial variance upper bound holds algebraically for any **continuum** `0<=rho_lo<=rho<=rho_hi<.95` and `0<=lambda_lo<=lambda<=lambda_hi<=1`, given an admissible marginal total annual-scale upper bound `s²_max`. Intrinsic calendar-year nugget variance and annual measurement noise remain aliased in the diagonal absent separately defended external information; this procedure does **not** identify them individually.

The new external development calibration simulates **40 independent hypothetical Gaussian worlds**, one anchor-year measurement from each, on the *same annual scalar scale*. The upper scale uses `(n-1)*sample_variance / chi2.ppf(.025,n-1)`, a nominal **97.5% one-sided upper bound** if those Gaussian draws are genuinely independent with common population scale. Combining its 2.5% calibration error allocation with a 7.5% nominal Gaussian two-era contrast tail yields a **Bonferroni nominal noncoverage bound at most 10%**, under all assumed source, scale, unbiasedness, Gaussian and covariance-range conditions. The critical value is `Phi^-1(.9625)`, not the earlier unconditional 1.64485.

This is a valid *conditional mathematical statement*, not verified unconditional coverage for the UN: the hypothetical independent repeated annual worlds have **no authenticated historical analog**, and the public original-PV audit is NOT an independent sample of comparable latent year deviations. Calibration evidence is externally simulated, **not real external source-supported**. No current source receipt authenticates the assumed variance upper, probability sampling, comparable genre/translation/representation or unbiased source-selection-adjusted annual mean. The code refuses shifted-population calibration and dependent external repeats in explicit controls and sets `historical_source_scale_verified=false`.

## 3. Independent invented development study and exact denominators

New seed namespace `UNGA81-V3-HIERARCHICAL-EXTERNAL-NEW-DEV-20261015`, separate code and seeds from all v2 and earlier v3 simulations. **12 synthetic development draws per scenario**: six gamma worlds × three methods = 216 gamma-method attempts; seven covariance worlds × two continuous nuisance rectangles = 168 covariance-method attempts. Methods share each simulated panel; these are **not 384 independent annual series**. Full source-free exact-head CI receipts preserve all failure reasons/replicate identities.

| Study | Method attempts | Completed | Refused |
| --- | ---: | ---: | ---: |
| Conditional gamma (pooled, year FE, hierarchical empirical Bayes) | 216 | 138 | 78 |
| Continuous covariance bound (wide and narrow) | 168 | 120 | 48 |
| **Total** | **384** | **258** | **126** |

Gamma failures: 36 no-audit and 36 weak-audit method refusals plus six absent-year-support refusals at T32. Covariance: 24 source-population-shift and 24 dependent-external-calibration refusals. All 126 failed method attempts are retained in `v3_hierarchical_external_failure_masks.json` with method, scenario, replicate and reason. `test_v3_hierarchical_external_replay.py` independently reruns the full 12-per-cell study and checks every result against `v3_hierarchical_external_development_receipt.json` and every failure bitmask; not just aggregate totals. No v3 holdout was run.

### Gamma point recovery and nominal-90% *diagnostic* hits

| Development scenario (completions) | Pooled gamma bias | Year-FE gamma bias/hit | Two-stage hierarchical gamma bias/hit |
| --- | ---: | ---: | ---: |
| IID T16 (12/12) | +.009 | −.006; **9/12** | +.007; **7/12** |
| Correlated T16 (12/12) | +.349 | −.022; **10/12** | +.018; **8/12** |
| Correlated T32 (10/12) | +.474 | −.018; **7/10** | +.022; **7/10** |
| q=.02 weak audit T16 | 0 eligible | 0 eligible | 0 eligible |
| q=0 missing audit T16 | 0 eligible | 0 eligible | 0 eligible |
| Changing gamma T16 | No common structural gamma | withheld from hit calculation | withheld from hit calculation |

Generating conditional gamma is −1.25 in constant-slope cells. Hierarchical pseudo-REML **flagged weakly identified nuisance profiles in 12/12 fitted correlated-T16 panels** and returned median `rho_year_hat=.88` against generating `rho=.65` (top edge of the exploratory grid). Gamma bias improvement over the pooled logit did not translate into calibrated intervals; two-stage Hessian SE ignored estimated nuisance and source-dependence uncertainty. The year-FE comparator is more accurate than the hierarchical candidate for nominal-90% diagnostic hits in the T16 correlated world. **No hierarchy estimator has passed a statistically validated T16 criterion.**

### External-scale covariance sensitivity

| Development scenario (per method) | Wide diagnostic beta hits | Narrow diagnostic hits | Assumed conditions genuinely held? |
| --- | ---: | ---: | --- |
| Matched synthetic external worlds, T16 (12) | 12/12; median width 1.301 | 11/12; width 1.094 | 11/12 scale upper bounds covered generating scale |
| Strong T16 rho=.85 (12) | 12/12; 1.461 | 12/12; 1.229 | wide 12/12; narrow 0/12 (rho outside narrow rectangle) |
| True rho outside assumed region (12) | 12/12; 1.166 | 12/12; .981 | 0/12 |
| Shifted external source population (12) | 12/12 REFUSED | 12/12 REFUSED | source matching failed |
| Dependent external worlds (12) | 12/12 REFUSED | 12/12 REFUSED | independence failed |
| Biased annual source outcomes (12) | 12/12; 1.319 | 12/12; 1.109 | 0/12 |
| Heavy-tailed annual process (12) | 12/12; 1.279 | 12/12; 1.076 | 0/12 |

A 12-world diagnostic hit rate has large Monte Carlo uncertainty (nominal 90% Bernoulli SE about **8.7 percentage points**). Many intervals contain generating beta even when their required assumptions are **false**; neither such hits nor numerical completion establish identification or coverage. In the correctly matched Gaussian world, 11/12 independently calibrated scale bounds covered the true marginal scale, consistent with the intended finite-sample diagnostic but not evidence of universal empirical validity.

## 4. Independent prospective freeze matrix

| Gate | Decision | Why |
| --- | --- | --- |
| Owned, source-safe engineering paths and original v2 hash invariance | Engineering PASS | No frozen estimator, original source, or release gate edits |
| Full new development failure-denominator and exact-replay integrity | Engineering PASS | All 126 failed attempts retained; no selective exclusion |
| Conditional within-year gamma interpretation | CONDITIONAL | Valid only under observed independent outcome audit and correct common slope/selection model |
| Genuine integrated hierarchical AR1 response likelihood | NOT IMPLEMENTED | Only two-stage empirical Bayes and plug-in Hessian |
| Serial-year/meeting/actor dependence calibrated gamma interval at T16 | FAIL / NOT ESTABLISHED | Weak year covariance profile and small-sample diagnostics |
| Nuisance rho and year-nugget recovery | FAIL / NOT ESTABLISHED | Boundary/weak profiles and diagonal variance alias |
| Continuous covariance upper-bound algebra | CONDITIONAL PASS | Proof holds over declared nuisance rectangle and true upper total scale |
| Authentic independent external year-scale evidence | NOT VERIFIED | Synthetic independent worlds are not original UN source audits |
| Complete historical audit `pi`, randomized outcome-recovery `q`, genre/translation/roster | NOT VERIFIED | Synthetic design is not real provenance |
| Independent reviewer approval and final method/threshold/seed/holdout producer freeze | NOT OBTAINED | Current v3 protocol remains `PROPOSED_NOT_FROZEN` |
| Original v2 statistical recovery or real 2008–2023 fitting | WITHHELD | Existing negative result and publication gates unchanged |

**Coordinator outcome: `STATISTICAL_FREEZE_NOT_ACCEPTED`; source-safe engineering and development-negative results are reviewable.** This is a model/code review, not a signed external statistician acceptance, and it does not allow a holdout, historical fit, merge, public release or retrospective threshold changes.

## 5. Next permissible statistical work

Specify and prospectively evaluate an **integrated** conditional response likelihood with correlated year effects and meeting/actor dependence or defend a partial-identification/no-fit outcome when external response or variance audits do not exist. Derive source-authenticated upper annual-scale and nuisance-region receipts in comparable units. Before a new independent holdout, obtain separate statistical/coordinator approval of the conditional estimand, model family/penalties, failure accounting, T16 interval-completion and false-confidence cutoffs, independent generator and seed/hash freeze. Previously inspected v2/v3 development or holdout outcomes cannot substitute for a fresh confirmation.
