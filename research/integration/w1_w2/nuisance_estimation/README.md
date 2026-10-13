# W1/W2 nuisance-parameter estimation: separately reviewed candidate v0

**Status:** engineering candidate only. This is a **new design/prototype review**, independent of merged PR #57's frozen synthetic-oracle experiment. It is neither an amendment to that immutable v1 protocol nor a frozen empirical preregistration. No original UN speech, private 2016–2023 Harvard member, human evaluation label, D1 gate or any of the 37 reserved October 5–6 transcripts may be accessed through this module.

## 1. Unresolved methodological deficiency

PR #57 correctly refits actual W1/W2 numerical methods under six **fictional oracle nuisance regimes**. It fixes the nuisance covariance parameters at their known, invented generating values. That validates computation **conditional on those parameters**, but not a practical null model in which the parameters must be **estimated with uncertainty from authorized sources**.

Moreover, retaining a cross-classified affiliation structure (countries recorded in several meetings and years) is not the same as identifying independent source opportunities. Dropping an affiliation term, treating all passages as independent or considering just eight calendar years can severely distort variances. A fitted parametric null must rerun parameter estimation on the appropriate design source, including failed fits and estimation uncertainty, rather than silently reusing a fixed oracle covariance.

This prototype is deliberately narrower than a true W1 text/latent null: it estimates dependence for **one invented Gaussian scalar lexical-nuisance proxy**. Neither W1's actual token-count distribution nor the high-dimensional TF-IDF/LSA embedding generative law is estimated. A scalar covariance success cannot be interpreted as G07/G09 acceptance or a real-text p-value.

## 2. Proposed estimand and estimation model

The first-stage *candidate* covariance is defined for a synthetic selected observation i:

y_i = x_i' beta + u_{meeting(i)} + v_{affiliation(i)} + g_{year(i)} + epsilon_i.

Here the fixed X matrix contains an intercept, invented genre/language/role indicators, length and two agenda contrasts. Meeting and recorded-affiliation random effects are independent mean-zero Gaussians of unknown variances. The latent year effect is a stationary Gaussian AR(1), with **unknown** autocorrelation rho and unknown stationary variance. Independent residual error has a fourth unknown variance.

For selected i and j, the covariance hypothesis is:

V_ij = sigma_m^2 * I(same meeting) + sigma_a^2 * I(same affiliation)
       + sigma_y^2 * rho^abs(year_i - year_j)
       + sigma_e^2 * I(i=j).

The four variance components and rho are **jointly estimated** by minimizing the candidate Gaussian **restricted negative log likelihood**. The pure Node implementation uses Cholesky solutions of V and X' V^(-1) X, removes fitted fixed effects in the restricted objective, and uses deterministic multistart bounded coordinate optimization. The optimizer's arguments accept only a prevalidated synthetic source panel, search budget and seedless deterministic settings; oracle variance/rho parameters are never passed to fit. The Gaussian model is a **feasibility candidate** and may be rejected after statistical review.

The log variance bounds and |rho| below 0.85 are engineering regularization, **not an independent scientific justification**. Optimizer diagnostics include objective, numeric Cholesky positivity, boundary/zero variance warnings, number of objective evaluations, and source counts. No standard errors, confidence intervals or p-values are emitted. A small or zero variance component and a flat/boundary rho profile require nonidentifiability disclosure, not post-hoc constraints tuned to get an attractive estimate.

## 3. Identifiability and data-selection gate

The estimator **fails closed** on:

- Fewer than 12 distinct synthetic years for *engineering preflight*; at least **16 years** are proposed before any future serious covariance reliability exercise. The historical 2016–2023, eight-year/four-per-era P2/W4 panel is **not inferentially eligible**.
- Fewer than two independently identified source meetings in any year, which makes meeting/year variance hard to separate.
- Too few observations, meetings with single eligible observations, insufficient repeated affiliations, rank-deficient nuisance X, unreviewed year gaps, or exact source IDs that do not match the frozen selection/source manifest.
- One original source family or parent span across multiple meetings when meeting-level independence is assumed.
- Selection depending on an **unobserved response (MNAR)**: the process cannot be inferred from a fixed selected sample; neither an ignorable missingness claim nor inverse-probability weights are fabricated.

Selection based on **declared observed X only** is allowed for the *conditional selected-panel* prototype, not for a whole-inventory/general-population claim. Verified-but-not-selected and unavailable original-source opportunities receive **null**, not zero outcome. Missing/unverified speaker-country is not promoted to a verified person or policy position.

Meeting and affiliation are crossed source features; many nominal groups can still form **one source-dependent connected component**. Years may contain strong common shocks even when nominal meeting labels differ. The design checker audits the source parent/family/meeting/affiliation/year structure separately; its ability to compute a covariance matrix **does not mean effective sampling groups or exchangeability were established**.

## 4. Candidate scenarios declared before executing estimator tests

The machine-readable design at design.candidate.v0.json was committed **before running its own synthetic estimator tests**. It is an independently reviewed, revisionable candidate, **not** the already frozen oracle protocol nor a confirmatory scientific preregistration.

| ID | Synthetic years | Truth | Expected candidate action |
| --- | ---: | --- | --- |
| E1_iid_16y | 16 | Independent year shocks, crossed meetings/affiliations | Attempt nuisance covariance REML; report warnings |
| E2_ar1_16y | 16 | Serial year shocks, rho 0.65 | Attempt **estimated** rho; compare to truth only after fitting |
| E3_ar1_24y | 24 | More year opportunities with serial dependence | Attempt bounded nuisance covariance estimation |
| E4_years8 | 8 | Four years per era | WITHHOLD: insufficient year blocks |
| E5_single_meeting_per_year | 16 | Meeting nested one-to-one in year | WITHHOLD: confounded meeting/year |
| E6_shared_source_family | 16 | Same original family crosses two meetings | WITHHOLD: source-family split |
| E7_mnar_mask | 16 | Attendance depends on unobserved outcome | WITHHOLD: unidentified selection |
| E8_declared_x_selection | 16 | Selection depends on declared observed covariates | Conditional fitted-sample estimate **only**, not population inference |

All inputs, responses and affiliations are invented, source-ID and SHA-linked and have no original transcript text. True simulation parameters exist only in a **separate diagnostic structure** unavailable to the fitter. One synthetic simulation estimate does not validate bias, uncertainty coverage, finite year dependence or actual linguistic-word-count residuals.

## 5. Prospective independent validation required (none passed yet)

Before this design is eligible for a source-dependent W1/W2 null generator, the coordinator and a separate statistical reviewer must accept:

1. **Source provenance and sampling frame:** independently source-hash original UN/PV and actual Harvard TAR member bytes, 99×year population opportunity/selected/verified/missing frames and source-family graph. Do not rely on the 2026 synthetic frame to satisfy G01–G04. Independently confirm speaker/affiliation and time metadata only where authenticated.
2. **Estimability and likelihood:** choose between REML, a defensible cross-classified alternative or a multivariate discrete-count nuisance model. Validate objective/gradient and fixed-effect rank using an independent reference implementation, test near-zero components/flat rho and random-effect correlations, and preserve optimizer failures and boundary cases.
3. **Selection model:** specify what source attendance is observed, what missingness can reasonably be conditioned on, where year/affiliation selection makes response-dependent missingness plausible, and how sensitivity bounds or exclusions are handled. A missing original UN speech cannot be imputed as a zero.
4. **Known-truth estimation calibration:** predeclare ≥200 panels per approved feasible scenario for initial recovery screening, later ≥1,000 independent panels per prespecified world for bias, RMSE, boundary frequency and uncertainty *coverage*. Recovery tolerances and confidence levels must be frozen **before** the expanded synthetic calibration. Compare at least one independently derived estimator rather than judging a single REML implementation by its own optimizer output.
5. **Nested nuisance re-estimation:** when producing future *null reference* worlds, refit both source nuisance parameters **and the entire W1→W2 representation/method/grid/selection pipeline** at every draw, including failures and undefined pair denominators. A fixed oracle \`rho=0.65\` or a single plug-in nuisance covariance from the observed world is not enough to establish type-I error. Reassess the target null under model misspecification, source selection and a single connected source component.
6. **Multiplicity and independence:** carry the entire predeclared W2 three-strata max-statistic search, all parameter-grid selection and independent source groups into the null; otherwise withhold any p-value. A prospectively authorized, no-leakage real source holdout and separate human release approval remain required for G11–G13.

No actual synthetic bias/coverage/parameter-identifiability gate is marked PASS by this initial engineering PR. The estimator's nonnegative Gaussian covariance and Cholesky success are computational requirements, **not** evidence that the random-effects assumptions hold for original UN text.

## 6. Synthetic-only reproducibility

Node 22, standard library only:

~~~sh
node --test research/integration/w1_w2/nuisance_estimation/test_estimator.cjs
node research/integration/w1_w2/nuisance_estimation/run_prototype.cjs /tmp/new-source-free-covariance-preflight
node research/integration/w1_w2/null_calibration/lock.cjs
node docs/parallel-work/inference-readiness-v1.cjs
~~~

The synthetic exporter creates a fresh output directory outside the repo, a source-free JSON receipt, a **fictional** estimate-versus-known-truth diagnostics file, and a SHA256 manifest. The receipt explicitly records that **all 13 scientific G01–G13 gates remain NOT_RUN**, the required nested lexical null with estimated nuisance parameters was not performed, and empirical/publication authorization is false.

**Referenced background (method choice, not evidence of validity here):**
- Luo & Kwok, *The impacts of ignoring a crossed factor in analyzing cross-classified data*, Multivariate Behavioral Research, 2009. DOI 10.1080/00273170902794214.
- Lee & Young, *Parametric bootstrapping with nuisance parameters*, Statistics & Probability Letters, 2005. DOI 10.1016/j.spl.2004.10.026.
- Simulation evaluation of autocorrelation estimation with short time series, *Evaluation of statistical methods used in the analysis of interrupted time series studies*, 2021, PMC8403376.

**Review outcome requested:** classify this code and design as **engineering feasibility only**, review the source/identifiability guards and statistical REML correctness independently, and leave empirical calibration withheld. No change to the frozen 37-meeting source lock, O1–O5, prior original hashes, published evidence, site release or website mirror.
