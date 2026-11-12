# V3 — Integrated serial-year likelihood versus sharp gamma-set/no-fit

**Coordinator methodological decision: ENGINEERING-DEVELOPMENT PASS; PROSPECTIVE STATISTICAL FREEZE NOT ACCEPTED.** This file concerns only new invented synthetic development data. The v2 negative result remains frozen; the v3 confirmatory holdout, real 2008–2023 corpus fit, original source records, 37 reserved 2026 transcripts, website and shared release gates were not opened or changed. It is not independent human-statistician signoff.

## What was independently assessed

The first estimator, `v3_integrated_markov.py`, is a *genuinely integrated* finite-state response likelihood rather than the earlier two-stage intercept empirical Bayes. It specifies a symmetric binary hidden year state `Z_t∈{-1,+1}` with stationary two-state Markov transition `P(Z_t=Z_{t-1})=s` and implied serial correlation `2s-1`. Conditional on `Z_t`, an independent binary Y has `P(Y=1|Z_t)=expit(mu+kappa Z_t)`; response obeys `P(R=1|Y,Z_t)=expit(alpha+gamma Y+delta Z_t)`. Randomized independent audit `A` observes otherwise missing Y among selected nonrespondents with known q. The observed-data likelihood multiplies Bernoulli outcome/response probabilities for known Y and **sums over missing Y** for unaudited nonrespondents, then **exactly sums all latent year-state histories** via a stable two-state HMM forward recursion. Alpha, gamma, outcome distribution, year-effect magnitude and state transition are all estimated from observable/respondent or independently audited information. No true generating nuisance values enter fitting. An independent brute-force 2^3 path enumeration checks the integrated forward-likelihood identity.

**Important restriction:** this is a two-state Markov model on a *fictional binary scalar outcome*, **not** an integrated Gaussian AR(1) continuous-year model for original UN speech trajectories. The likelihood conditions on ignorable original meeting selection and **IID actor/meeting observations within year given the latent state**; it does not integrate repeated-person/meeting/source-cluster random effects, uncertain genres/translations, source verification probability or historical multi-era sampling. Neither a marginal gamma nor a calibrated gamma interval is produced. Multistart optimizer agreement is not misclassified as identification; nuisance curvature and boundaries remain recorded as unapproved diagnostics.

The alternative, `v3_partial_identification.py`, supplies two defensible outcomes rather than assume point identification:

1. **Population sharp set under independently defended missing-outcome bounds.** Let `p1_y=P(Y=1|R=1,year=y)`, `p0_y=P(Y=1|R=0,year=y)`. The common conditional logit gamma is `logit(p1_y)-logit(p0_y)`. If a genuinely authenticated independent mechanism bounds `p0_y∈[a_y,b_y]`, then the year-wise gamma interval is `[logit(p1_y)-logit(b_y), logit(p1_y)-logit(a_y)]`; intersect the continuous intervals across years. This is sharp **at the population-moment level**, assuming correct constant gamma and unrestricted year intercepts, not a confidence interval from finite original speech counts. If no audit or external bound establishes missing outcomes, `p0_y∈[0,1]` and the gamma set is `(-infinity,+infinity)`; the correct outcome is `NO_FIT_UNRESTRICTED_MNAR`.
2. **Finite-sample independently audited conditional gamma set.** For an explicitly source-certified IID-within-year binary sample and randomized missing-outcome q, use exact Clopper–Pearson intervals for the respondent-positive and audited-nonrespondent-positive probabilities separately within each year, with two-sided per-group alpha `0.10/(2T)`. By Bonferroni over 2T binomial groups, the simultaneous bounds have **at least 90% coverage conditional on any dependent sequence of latent calendar-year states**. Transform with logits and intersect year gamma sets. Independence of calendar years is *not needed for the union bound*. This result **does require** within-year conditional IID, independent randomized q and original meeting selection/provenance assumptions. It is **not valid for unverified historical repeated actor/meeting clusters**; the code refuses a synthetic actor-dependence violation. Empty or unbounded sets are refusals, not point estimates. It does not claim to identify marginalized response gamma or an annual covariance nugget.

In particular, an exact binomial confidence set can be formally justified under stronger design assumptions even while the integrated likelihood's finite-T nuisance and gamma interval remain unvalidated. **The two methods target the same conditional binary gamma only when both modeling assumptions hold.** Neither automatically transfers to semantic embedding differences or historical UN original-source populations.

## New independent development experiment and numerical results

Namespace `UNGA81-V3-EXACT-TWO-STATE-AND-CP-NEW-DEV-20261015`. The development-only generator is separately written from v2's synthetic source engines and earlier v3 development work. Each T16/T32 year has nine fictional original meetings sampled as two of three in each of three meeting strata (pi=2/3), twelve fictional actor positions, a declared preadmission structural risk exclusion, known response indicators and randomized independent q when present. Unknown Y values are **NaN** in every estimator input. The evaluator alone receives the true gamma/year-state parameters.

**12 new development worlds per cell**, eight worlds and two compared methods = **192 method attempts = 120 completed + 72 correctly refused**. All 72 failed attempt keys are retained losslessly by scenario, method, 12-bit replicate mask, refusal reason and expected status. Both methods correctly refuse all twelve q=0, weak q and repeated actor-effect stress panels. A changing-gamma stress scenario deliberately violates common gamma; no common true slope or diagnostic hit rate is assigned, even though estimators can produce model-dependent outputs.

| Development scenario | Integrated Markov gamma bias / RMSE | Median estimated Markov year rho | Audited conditional gamma-set hits | Median set width |
| --- | --- | ---: | ---: | ---: |
| IID year states, T16 | +.010 / .127 | .072 (true .020) | 12/12 | 3.632 |
| Correlated states, T16 | +.025 / .211 | .667 (true .640) | 12/12 | 3.901 |
| Persistent states, T16 | +.001 / .203 | .866 (true .880) | 12/12 | 4.156 |
| Correlated states, T32 | -.039 / .135 | .677 (true .640) | 12/12 | 3.943 |
| q=.025 weak audit, T16 | REFUSED | — | REFUSED | — |
| q=0 no independent outcome audit, T16 | REFUSED | — | NO FIT | — |
| Repeated actor-effect dependence, T16 | REFUSED | — | REFUSED | — |
| Changing conditional gamma, T16 | common target invalid | — | common target invalid | conditional set not certified |

The generating conditional gamma for constant-slope worlds was `-1.25`. A 12/12 success for an exact-binomial interval **does not empirically validate coverage**: the scenario denominator is only twelve and the interval is very wide (roughly 3.9 log-odds units in the primary correlated T16 world), limiting practical discrimination. Its mathematical ≥90% claim is *conditional on verified binomial design assumptions*, not a measured historical guarantee. Estimated Markov nuisance correlation in these tiny simulations does not establish reliable rho recovery. Many fitted scenarios retain weak/boundary nuisance diagnostics; no model produced a calibrated structural gamma interval.

## Reproducibility and fail-closed execution

Run in an execution-capable full repository checkout:

```bash
OPENBLAS_NUM_THREADS=1 PYTHONHASHSEED=0 python -m research.longitudinal.temporal_calibration_v2.v3_integrated_study --phase development --repetitions 12 --out /tmp/new-v3-integrated-partial-development
python -m unittest discover -s research/longitudinal -p 'test_*.py' -v
```

The runner rejects `--phase holdout`, `--phase real`, invalid repetition budgets and overwriting completed output. `test_v3_integrated_markov.py` tests brute-force likelihood enumeration, numerical fit/refusal states, audit positivity, source lineage, the exact-binomial finite-sample construction, population sharpness and opposite-sign/no-fit implications. `test_v3_integrated_replay.py` independently executes all 12 fresh worlds/cell and verifies every failed-fit identity and the committed source-free aggregate. No original text, original-source bytes, country-linked speech outcomes or reserved 2026 records enter this study.

## Statistical decision and prospective restrictions

**Integrated model: NOT ACCEPTED for inference.** It successfully fits the correct fictional binary HMM mechanism in development, but a 16-year two-state model is not an accepted continuous serial-Gaussian response hierarchy, its nuisance confidence region and gamma intervals are not calibrated, and real meeting/actor/source dependence and actual q audit design are not identified.

**Partial identification: CONDITIONAL MATHEMATICAL ACCEPTANCE, NOT EMPIRICAL AUTHORIZATION.** The sharp common-gamma population set and the CP/Bonferroni finite-sample confidence set have explicit mathematical guarantees under their defined probability and sample-design assumptions. Without an authenticated real independent outcome audit or independently defensible population bounds, the appropriate real-data conclusion is **NO FIT**. More years, countries or speeches do not supply that missing independent mechanism.

**V3 prospective freeze: NOT ACCEPTED.** The next authorized statistical decision is whether any original-source setting can establish IID/cluster-adjusted within-year units, randomized and independently verified missing-outcome q, genre/translation/representation comparability and source selection positivity. If not, preregister an explicit nonidentification refusal or source-limited descriptive estimand. A future independent statistical signoff must separately freeze model, nuisance bounds, finite-year uncertainty rules, exact failure denominators, code hashes, seeds and independently implemented prospective holdout generator before *any* v3 holdout. Do not edit original v2 thresholds, re-use earlier v2/v3 development as a holdout, merge PR #68 or publish real model conclusions.
