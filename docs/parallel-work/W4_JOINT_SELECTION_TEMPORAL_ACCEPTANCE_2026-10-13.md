# W4 joint transcript-selection and serial temporal covariance — acceptance report

**Date:** 13 October 2026. **Research conclusion:** a source-safe two-phase joint correction model was implemented and its independent heldout synthetic calibration executed. **Temporal covariance parameter reliability FAILS**, and actual original-source transcript selection is not identified. The preregistered stop rule was enforced: **NO new 2008–2023 real-data representation was fitted** and no real confidence intervals were estimated.

## Frozen test and reproducibility

The [new preregistration](W4_JOINT_SELECTION_TEMPORAL_PREREG_2026-10-13.md) was committed before implementing/executing the estimator or examining holdout synthetic outcomes. The [frozen development receipt](W4_JOINT_SELECTION_FROZEN_DEV_RECEIPT_2026-10-13.json) was committed *before* independent holdout evaluation. This separation matters: development critical values were learned from **2,160 attempted / 2,120 supported** synthetic development panels, retaining 40 support failures. Frozen development receipt SHA-256: `a9bda3652748cba980fe900317161a78be8f6fdaed91b5a2bb67b431e21b6639`. Critical values for T=16,24,32: **2.208411**, **2.003855**, **1.840906**, respectively. No critical values, model grid, generator world, seed or acceptance tolerance changed after the independent holdout opened.

The **independently written** holdout generator uses a separate seed namespace and does not import the development generator. Exactly **5,760** holdout panels were attempted: T=16/24/32 × two original-meeting sampling masks × four temporal/response worlds × 240 replications. Of the 4,320 identifiable panels, **4,260** delivered complete fitted estimates and **60** support failures remained in the failure ledger. Under MNAR with no random missing-outcome audit, the method correctly **abstained in all 1,440/1,440 panels**, with zero unsafe fits. All 42 scenario/method rows, Wil­son intervals, residual failures and seeds are delivered in the owner's **private downloadable research package**, not the public website.

## Statistical identification and estimator

The input is synthetic country-affiliation/year speech-feature data nested in official-*like* meetings. The outcome design is `Y_it = beta*post_t + country_i + year_t + meeting_{g,t} + speech_it`, with shared year shocks (iid or stationary AR1 rho 0.65), country SD .40, meeting SD .12 and within-speech SD .25. Text-response selection is either outcome-independent or logit-MNAR (gamma −1.25), with distinct known first-stage meeting inclusion probabilities.

**This is a sequential, identified two-phase joint correction—not one fully optimized joint likelihood for actor, meeting, response and temporal covariance.** It combines (a) a **weighted logistic model of transcript response conditional on observed/audited speech outcomes**, (b) independent randomized phase-II verification of unavailable outcomes with known `q=0.40` to construct response-adjusted Hájek annual means, and (c) an AR(1)+nugget covariance family fitted by profile REML to those annual means. Correlation, nugget, scale, and selection dependence gamma are **estimated from the observed (redacted) synthetic data**, never supplied their true parameters. Tests reject hidden outcome leakage, a claimed audit unsupported by actual randomization, forged source probabilities and false publication decisions.

The real 2008–2015 original-PV sample has **64 verified meetings from a 118-meeting indexed frame**, **855 resolved index speaker records**, **832 original-PV strong full speech correspondences** and **828 unambiguous country-year matches**. Its first-stage meeting selection is known. Its **second-stage outcome-dependent text verification is not independently randomized or identified**. The previously source-verified 2016–2023 panel was acquired using a different meeting strategy; no newly accepted single 2008–2023 source/person/language/representation population exists. A name/role/source hash does not establish a selection model for missing textual outcomes.

## Independent calibration result — 90% nominal scalar-period intervals

| Preregistered test criterion | Result | Acceptance |
|---|---|---|
| Holdout identifiable coverage criteria | **12 of 18** scenarios pass | **FAIL** complete gate |
| Temporal rho recovery (bias, RMSE, boundary) | **0 of 18** scenarios pass | **FAIL** |
| Selection gamma recovery with actual synthetic phase-II audit | **6 of 6** audited MNAR scenarios pass | PASS for locked synthetic design only |
| No-audit MNAR identifiability | 1,440 of 1,440 refuse, zero unsafe fits | PASS identification protection |
| New 2008–2023 real source comparable frozen reference fit | **NOT RUN** | Correct mandatory stop |
| Real confidence intervals, diplomatic political positions or publication | **WITHHELD** | Not eligible |

For the 16-year serial-dependence-plus-MNAR world, independently calibrated interval coverage was **90.8%** (near census) and **88.1%** (two-of-three meeting mask), but temporal-rho RMSE was **0.336** and **0.367**, exceeding the preregistered **0.25** cutoff. At 32 years, some rho fits improve, but holdout coverage and source-generalizability gates still fail. **Near-nominal interval coverage does not imply correct temporal covariance parameter recovery or reliable real-world statistical inference.** This study targets a synthetic *signed scalar beta*, not the nonlinear original W4 full-64D Euclidean distance functional.

The test code independently cross-checks the estimated-covariance GLS fit against Cholesky-whitened regression and the response logistic likelihood against a different bounded optimizer, with new tests for source-sampling counts, true hidden-outcome redaction, null beta shifts, randomized-audit requirements and fail-closed real fitting. All normal source-free W4/synthetic v1 regressions remain unchanged.

## Explicit real-data stop-gate outcome

The private `source_comparability_preflight.py` inspected the exact original UN Library CSV bytes and previously authenticated P2 selected source rows without any feature refitting. It verified the early original meeting sampling strata, per-year denominator, original text hashes and source count. It recorded **five withheld conditions**:

1. Independent 16-year synthetic AR1 parameter recovery/interval calibration failed.
2. Rho reliability was not established across all identifiable worlds.
3. **No independently randomized audited second-phase original UN transcript outcomes** exist for nonresponding selected source records.
4. The 2008–2015 sample and 2016–2023 historical cohort lack one independently accepted common source/genre/translation/feature-training selection.
5. The real underlying country/year speech response mechanism and historic member population are not validated for unrestricted inference.

The executable `real_fit_stop_gate.py` returned **`WITHHELD_NOT_FIT` with exit code 2**. It did not create fitted models, vectors, vocabularies or new real period projections. Even if future computational flags all pass, the gate only permits **provisional human review**, never autonomous publication or actual real-data training.

## Coordinator files, acceptance and immutable protections

This engineering PR may add only `research/longitudinal/joint_selection_temporal/**`, this preregistration and aggregate-only acceptance documents under `docs/parallel-work/**`, and its uniquely named read-only CI workflow. No existing W1 numerical/ W4 accepted methods, original Harvard source digests, shared `un.parallel-analysis.v1`, D1/O1–O5 gates, review annotations, browser/website files, 37 reserved October 5–6, 2026 meetings or historical original source PDFs were changed or published. The real source-linked speaker/provenance rows and all simulation holdout scenario records remain in the private research package.

**Decision:** model implementation and independent numerical/identification validation **PASS engineering checks**; finite-sample estimated temporal covariance reliability **FAIL**; cross-year real representation **NOT FIT**; real-W4 confidence intervals, country policy inference and public release **WITHHELD**.

**Next non-inferential research:** develop a source-valid independent random audit of missing original speeches, validate whether archival text outcomes can be recovered with identifiable audit probabilities, preregister an estimator with stronger time-shock parameter recovery on independent synthetic validation worlds, and only then freeze a **new** source-comparable real 2008–2023 feature representation. Do not tune this failed holdout retrospectively.
