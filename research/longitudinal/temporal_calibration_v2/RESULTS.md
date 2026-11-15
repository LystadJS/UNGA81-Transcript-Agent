# Independently frozen temporal-v2 simulation: engineering readout

**Outcome:** Documented numerical calibration failure, not a successful inferential estimator. Reproducibility of the *synthetic execution* does not authenticate historical UN meeting source bytes or justify any new real 2008–2023 model. The previously accepted W4 and frozen analytical thresholds are unchanged.

## Exact execution denominators

| Stage | Attempted | Identifiable delivered | Correct no-audit refusals | Other support failures | Unsafe fits |
| --- | ---: | ---: | ---: | ---: | ---: |
| Development | 3,600 | 2,829 | 720 | 51 | 0 |
| Independent holdout | 7,200 | 5,653 | 1,440 | 107 | 0 |

Every identifiable successfully delivered world contributed **three interval-method assessments** (IID baseline, constrained AR1, regularized AR1+nugget); this is **not** three independent panels per world. Thus there were 16,959 evaluated holdout intervals, with 321 method-attempt noncompletions from 107 failed panels; 4,320 attempted method fits correctly withheld across 1,440 no-audit panels. The holdout includes 24 identifiable scenarios and six unaudited nonidentified scenarios, 240 attempts each. Failure categories: 102 absent audit support in at least one year, five insufficient response-stratum counts, 1,440 expected identification refusals. All failures remain in the output denominators.

## Locked synthetic holdout acceptance

| Metric | IID-year baseline | Constrained AR1 | Regularized AR1 + nugget |
| --- | ---: | ---: | ---: |
| Coverage scenarios passing 90% ±5pp AND Wilson containment | 6/24 | 18/24 | 19/24 |
| ρ recovery scenarios passing bias, RMSE **and** grid boundary | N/A (fixes rho=0) | 1/24 | 0/24 |
| All eight identifiable T16 source/selection worlds pass jointly | No | No | No |
| Approved for further empirical fitting | **No** | **No** | **No** |

The original PR #62 temporal recovery limits remain `|rho bias| ≤ .12`, `rho RMSE ≤ .25`, `grid boundary <5%`. The calibrated nominal-90% intervals use independently frozen development multipliers. Passing interval coverage does **not** imply an identified nuisance process; coverage may pass while ρ recovery fails sharply, particularly with an independent year nugget.

### Representative T16 results (nominal 90% intervals after development calibration)

| World and source mask | Feasible model | Usable /240 | Coverage | ρ RMSE | ρ grid-end rate | Median width |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| AR1 + audited MNAR, near-census | Constrained AR1 | 240 | 91.7% | .308 | 12.9% | .595 |
| AR1 + audited MNAR, stratified 2/3 | Constrained AR1 | 237 | 86.9% | .360 | 13.9% | .578 |
| AR1 + audited MNAR, near-census | Regularized AR1+nugget | 240 | 90.0% | .297 | 18.8% | .588 |
| AR1 + audited MNAR, stratified 2/3 | Regularized AR1+nugget | 237 | 86.9% | .350 | 19.8% | .589 |
| AR1 + **extra year-nugget** + audited MNAR, near-census | Constrained AR1 | 240 | 90.0% | .489 | 21.2% | .652 |
| AR1 + **extra year-nugget** + audited MNAR, near-census | Regularized AR1+nugget | 240 | 90.8% | .477 | 26.7% | .663 |

Additional long-horizon comparison: under audited MNAR with near-census sampling, regularized-AR1 ρ RMSE is **.297** at T16, **.253** at T24, **.200** at T32. Those observations are not evidence that 32 years would invariably identify ρ: model misspecification, selection and year-level nugget remain credible alternatives. The 2008–2023 UN analysis has only 16 calendar years, and the 90+28 archival source audit is not a longitudinal sample enlargement.

## Independent numerical oracle and failure diagnosis

- Known-parameter oracle: separate exact Gaussian GLS/Cholesky control for 500 newly simulated T16 stationary-AR1 panels; **460/500 (92.0%)** nominal-90% intervals covered the known beta. It uses **true covariance given by the oracle harness**, entirely separate from the feasible estimated-parameter pipeline. The oracle was not fed missing original transcript outcomes or claimed as real coverage.
- Estimated nuisance: both feasible AR1 methods estimate rho, nugget restrictions and scale solely from the observed year means; a sampling/measurement sensitivity diagnostic is exported separately. Their low T16 ρ point reliability is consistent with weak AR1-versus-year-nugget separation and correlation of actor/meeting observations.
- Selection: distinct original-meeting sampling probabilities and randomized transcript-response recovery were simulated. Selection gamma was fitted, not supplied; no-audit MNAR always abstained. Source-weighted strata can fail when an audited nonresponse outcome is absent in a year; these failures are not renamed to convergence successes.
- False confidence: each method×scenario includes `false_confidence_count` and `false_confidence_rate_per_attempt`, defined as the frequency of a **missed true beta with misleadingly narrow interval (width ≤ .8)**. Treat them as DGP-specific diagnostics, not frequentist certainty for empirical effects.
- Model misspecification: independent nugget world adds year-specific noise of SD .15 to the AR1 process; constrained zero-nugget covariance is structurally wrong there. Ridge penalties constrain but do not manufacture identifiability. A small profile objective difference is flagged instead of converted into rho certainty.

## Source, design and publication decisions

The `un.historical-source-audit.v1` adapter is **metadata-only, proposed interface**, reports unavailable original documents vs missing transcripts vs missing outcomes separately, verifies syntactic identities and declares no independent original-byte authentication. It rejects incompatible cohort designs and source populations, and never exports a pooled empirical model.

An actual outcome-dependent verification model requires externally documented randomized second-phase original-text audit with known probabilities and recoverable outcomes. Nothing in the synthetic q=.40 experiment supplies it. Actual original UN speech matching, positivity, historical source generation across eras, genre/translation effects, repeated speaker identities, language-model/64D lexical uncertainty and dependency-aware 16-year inference remain unresolved. The 37 reserved Oct 5–6 2026 meeting transcripts, frozen W1/W4 preregistrations and D1 O1–O5 remain untouched.

**Decision:** engineering acceptability as a documented independent synthetic failure is reviewable; a *defensible 16-year real inference candidate* is **NOT available**. No new real model, country profile, policy stance, interval, browser integration or publication was produced.
