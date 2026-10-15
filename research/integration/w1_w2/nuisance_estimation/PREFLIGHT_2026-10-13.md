# Synthetic nuisance-parameter estimation preflight — 13 October 2026

**Scope:** eight invented scalar nuisance-covariance scenarios. Design candidate v0 committed as **1233733cee873ea2fb7598e539e451ea89be0de2**, *before the estimator/test execution*, and never used as a real-source scientific null. Its source SHA-256, as recorded by the GitHub Actions receipt, is **517ec5122fd23cc86fda46c9886b9971c389a9c5630fb030f9ecdfa3db4e875b**.

**Implementation:** real Gaussian restricted-likelihood numerical objective with nonnegative unknown meeting, affiliation, year, residual variances and unknown year AR(1) rho; deterministic bounded optimizer. The simulator provides the truth **only after** fitting, never to fit. The **iid-intercept restricted likelihood** receives an independent analytic closed-form check. Source families crossing meetings, one-meeting/year confounding, eight-year insufficiency and response-dependent MNAR missingness are refused rather than reduced to independent rows.

## Executed preflight results (NOT validation)

The design declared **two previews per feasible scenario**, one per expected-refusal scenario. The original CI probe had one preview per feasible scenario; the later check implemented the predeclared two-preview rule. Both rounds are kept in the GitHub Actions history. Actual source texts, country records and the 37 sealed meetings were not accessed.

| Scenario | Generating rho | Estimated rho (preview 1, 2) | Outcome |
| --- | ---: | ---: | --- |
| E1_iid_16y | 0 | −0.297, −0.128 | Numerical fit, estimated rho differs from zero in finite synthetic panels |
| E2_ar1_16y | +0.65 | +0.593, +0.570 | Numerical fit, no finite-sample reliability conclusion |
| E3_ar1_24y | +0.65 | +0.775, +0.659 | **Boundary warning** in first panel; covariance identification not accepted |
| E4_years8 | +0.65 | Not estimated | WITHHELD: four years per era |
| E5_single_meeting_per_year | +0.65 | Not estimated | WITHHELD: meeting/year covariance confounding |
| E6_shared_source_family | +0.65 | Not estimated | WITHHELD: same original family spans meetings |
| E7_mnar_mask | +0.65 | Not estimated | WITHHELD: outcome-dependent selection unknown |
| E8_declared_x_selection | +0.65 | **−0.849**, +0.393 | **Severe weak-identification/recovery flag** even under declared-X selection |

**Critical conclusion:** E8's first fitted rho has absolute error **1.499**, demonstrating that a numerically positive-definite model, finite restricted likelihood and independent parameter estimation can still produce a severely wrong nuisance estimate under selection/finite-year uncertainty. E3 additionally reaches the near-boundary warning. These observations are **evidence against claiming estimator reliability**; they are not cherry-picked away or used to retune the frozen design.

This is a **preflight with eight finite numerical fits**, not the proposed ≥200-panel bias study or ≥1,000-panel coverage experiment. Even the apparently close E2 estimates are not a method acceptance. No interval, covariance-parameter uncertainty propagation or type-I error calibration was run. The Gaussian scalar response is not actual token counts or a validated UN latent representation.

## Final engineering acceptance requested

- Check exact design and source fingerprints, no true generating variances/rho in estimator input, no UN source bytes or reserved source access.
- Independently verify the likelihood objective, numerical optimizer convergence/conditioning, duplicated parent/source-family splitting refusal, calendar-year gaps, missing source/selected source distinction, source-mask selection and original cohort hashes.
- The **analytical and numerical warning gates remain NOT ACCEPTED**, especially E8's selection-dependent rho. No empirical W1/W2 nuisance model can be promoted from this candidate.
- Before any calibration, independently benchmark against a second covariance estimator, quantify bias/RMSE/boundary rate and profile-likelihood uncertainty over ≥200 synthetic worlds per admissible regime, lock estimator error tolerances *before* that study, and ensure a **new lexical-count / feature-transformation-aware** nuisance process is fitted using actual authorized development sources, never the sealed evaluation.
- Refit nuisance parameters and the **entire W1/W2 token representation and full searched null pipeline** inside every future parametric reference draw. Source-dependence, source-selection and Monte Carlo error must be jointly calibrated; one scalar REML fit is not sufficient.

**G01–G13: 0 PASS, 13 NOT_RUN.** This is a separately reviewable methodological failure/feasibility report, not a valid significance test, independent actor-vote inference or publication approval.
