# Independent prospective v3 identification and freeze review — coordinator decision

**Disposition: STATISTICAL FREEZE NOT ACCEPTED. Engineering review and development-only falsification evidence: reviewable.** This is an independent methodological/code review, **not** a signed independent-statistician authorization, preregistration, new confirmatory holdout, or approval for real UN inference. All source and publication gates remain closed.

## 1. Scope and evidence

Reviewed the exact source-contract implementation under `research/longitudinal/temporal_calibration_v2/**`, the source-free prospective design, the gamma/year-effects and covariance-sensitivity modules, the preserved negative v2 findings and the completed synthetic development results. No new v2 outcomes, real original PV material, private source rows, or reserved October 2026 transcripts were opened. Only mathematical deterministic counterexamples, ordinary development-source regression tests, and previously executed **development-only** scenarios support this decision.

The separately recorded development design (30 synthetic replicates × 6 gamma worlds × 3 estimators, and 30 × 6 covariance worlds × 3 sensitivity alternatives) produced **540 gamma attempts = 312 completed + 228 refused; 540 covariance attempts = 450 completed + 90 refused**, with all **318 failures** indexed by scenario/method/replicate/reason. These are *attempt* denominators, not 1,080 independent panels; paired methods share the same simulated world. Full existing CI replay checks preserve these identities. No attempt can be relabeled a success by exclusion.

## 2. Year-fixed-effects gamma — the estimand must be conditional

The proposed model is

```text
Pr(R_iym = 1 | Y_iym, X_iym, year=y, included meeting)
    = expit(alpha_y + gamma * Y_iym + b' X_iym).
```

The `year_fixed_effects` estimator currently fits **only** a common `gamma` and separate `alpha_y` intercepts; it does not fit source/meeting-specific coefficients `b` or a verified serial random-effect likelihood. Its target is **the conditional within-year logistic response slope** under (i) correct slope/intercept specification, (ii) sufficient within-year outcome variation and response overlap, (iii) original-meeting sampling positivity with genuine known inclusion probabilities, (iv) independent randomized second-phase recovery of the otherwise unobserved nonrespondent outcomes with known `q`, and (v) correct affiliation, source, genre and measurement provenance.

The marginal slope after integrating year heterogeneity is **not generally the same parameter**, even when the conditional model is correct (logistic noncollapsibility). A mathematically exact equal mixture of annual intercepts `-1.5, +1.5` with conditional `gamma=-1.25` gives the **marginal logit difference quotient approximately -0.794834**, not -1.25. Treating the development beta/gamma recovery as certification of the marginal missingness model would change the estimand without authorization.

With **no independent randomized outcome audit**, even a binary toy response table has incompatible missing-outcome populations producing *opposite signed* response slopes. For 50% responding and a 70% positive-outcome proportion among respondents, missing positive fractions .2 and .8 produce slopes approximately **+2.23359** and **-0.538997** with exactly the same observed data. These are structural nonidentification witnesses, not missing values to impute as zero.

A serial-year response intercept can be included as a fixed effect without asserting year independence for point estimation. **Valid finite-T standard errors do not follow.** Only 16 dependent calendar-year blocks exist; repeated actors and meetings create additional dependence. The current score-HAC lag-2 standard error is descriptive, the year effects are estimated rather than known, and the optimizer's 6.0 penalty in the smoothed alternative is a specified regularizer, not a validated integrated AR(1) random-effect likelihood. The empirical-rho plug-in is itself noisy and can shrink away confounding correction.

**Development evidence:** under correlated outcome/response-year effects at T16, 29/30 fits completed and pooled gamma bias **+0.411**, year-FE **-0.039**, smoothed **+0.158**. The year-FE 90%-shaped diagnostic hit **25/29 = 86.2%**; its approximate Wilson 95% interval is **[69.4%, 94.5%]**. This neither certifies 90% nominal coverage nor rigorously establishes undercoverage at this tiny simulation denominator. The **correct iid T16** development world had year-FE diagnostic hits **23/30 = 76.7%**, demonstrating why nominal interval calibration remains unproven. No outcome is a verified real audit.

**Decision:** retain FE conditional gamma as a possible **point-estimator research candidate only**. Marginal gamma, common-slope transport, year-propensity nuisance recovery and a calibrated 16-year interval are **NOT ACCEPTED**.

## 3. Covariance partial identification — separate measurement noise and intrinsic nugget

Annual covariance is assumed:

```text
Sigma = sigma_AR^2 R(rho) + (sigma_year_nug^2 + sigma_measure^2) I.
```

Intrinsic year-nugget and measurement-error derivatives are identical `I`; without external information their component variances are exactly observationally aliased. A deterministic witness transfers .01 variance units from the intrinsic year component (.025 → .015) to measurement noise (.0144 → .0244), producing exactly the **same** annual covariance at any horizon. More actors or meetings within the same 16 years do not solve that algebraic problem.

An independent, source-valid replicate error experiment can bound `sigma_measure²` only if replicates measure the same latent quantity with defensible independent, equal-variance error and consistent units. It cannot alone certify positive intrinsic nugget or point rho recovery. The current external bound is conditional on a **Gaussian equal-error, independent pair** model, and the proposed filtering compares the externally estimated measurement lower bound with `estimated_total_scale × candidate_effective_nugget_fraction`. This is a **one-sided admissibility assumption** applied after the year-data fit, not a calibrated joint confidence region for rho, nugget and beta. Selection by an estimated bound adds calibration uncertainty; row/meeting sampling variance and translation/genre mismatch are not automatically included.

The proposed `wide`, `narrow`, and `externally_constrained` alternatives are **unions over finite discrete, hypothetical nuisance grids**, not rigorous continuous-parameter partial-identification sets. Even in the development stationary rho=.65 case, generating `(sigma_nug²+sigma_measure²)/(sigma_AR²+sigma_nug²+sigma_measure²)=.49622` exceeds the `narrow` grid maximum .45; the exact generating rho .65 also falls between discrete .50/.70 support points. A nominal interval containing beta cannot validate a false nuisance restriction. The current 90%-shaped `t(T-3)` intervals are **not** proven to have 90% coverage uniformly across nuisance values, post-fit range restrictions, or model misspecification.

Development T16 rho=.65 yields 26/30 diagnostic beta hits for wide, narrow and external variants; widths respectively 1.044, .903 and .819. At rho=.85, the external constraint **drops** nominal hits relative to the wide alternative (28/30 versus 30/30). Nonstationary cases violate the assumed covariance family. **None** licenses a calibrated beta interval or a year-nugget estimator.

**Decision:** retain these as explicitly labeled **conditional sensitivity displays**, not actual identified sets, valid confidence regions, or inference calibration. Independently justify and predeclare the nuisance parameter continuum, measurement uncertainty combination rule, plausible history-level variance units, and a coverage method before any final freeze.

## 4. Coordinator freeze-decision matrix

| Gate | Finding | Reason |
| --- | --- | --- |
| Source-safe, exclusively owned code | PASS (engineering) | No existing W4 estimators, original text, shared contracts or frozen v2 protocol edited |
| Original v2 negative result and SHA retention | PASS (engineering) | Frozen v2 record remains the accepted negative result |
| Complete development failed-attempt accounting | PASS (engineering) | 318/318 failed attempts indexed and replay-tested |
| Candidate source/hash inventory | PASS for **unapproved** candidate | Self-declared proposal is not a signed methodological freeze |
| Correct conditional gamma estimand | CONDITIONAL | Audit, model specification, positivity and comparability assumptions required |
| Marginal gamma interpretation | FAIL | Noncollapsibility witness |
| Real MNAR audit identification | NOT VERIFIED | No independently randomized recovery of historically missing outcomes |
| Serial-year gamma interval coverage at T16 | NOT ESTABLISHED | Finite-year, repeated-meeting/actor dependence and limited development diagnostics |
| Intrinsic year-nugget identification | FAIL from annual data alone | Exact diagonal covariance alias |
| External measurement variance assumptions | NOT VERIFIED for real data | Requires independent, commensurate original-source replicate experiment |
| Continuous covariance partial-ID set | NOT IMPLEMENTED | Current grid is finite and assumption-dependent |
| Uniform interval coverage under nuisance/misspecification | NOT ESTABLISHED | Exploratory t-shaped envelopes only |
| Final freeze thresholds, code, independent generator and seeds | NOT FROZEN | Candidate status explicitly unapproved; no independent confirmatory producer |
| Independent methodological authorization | NOT OBTAINED | A code review is not a signed independent statistical protocol approval |
| v3 holdout / real 2008–2023 fit | NOT RUN / PROHIBITED | All statistical gates remain closed |

## 5. Exact prospectively required decisions before any freeze

1. **Separate target parameters:** predeclare conditional `gamma` and optional marginalized response function, including observation unit, at-risk population, genres, languages and time-invariant versus year-specific response effects. If both are needed, design genuinely separate estimators and multiplicity-aware acceptance.
2. **Audit design:** independently authenticate original meeting sampling probabilities, randomized second-phase *outcome* recovery `q` (not mere document metadata), individual outcome/linkage verification and overlap; preserve meeting/year/actor dependence and all unavailable-cell denominators.
3. **Finite-year uncertainty:** prespecify and test an appropriately dependence-aware estimator, including year-effect parameter uncertainty, repeated actors/meetings, estimated nuisance, uncertainty under 16 serially correlated blocks, failures and false confidence. No point-bias improvement can waive interval gates.
4. **Nugget vs measurement:** independently justify latent observation-noise model and relative units, separate the process nugget, define continuous nuisance region, partial-ID set and valid uncertainty construction; evaluate incorrect-bound/translation/nonstationary negative controls.
5. **Freeze mechanics:** precommit the complete factorial population, primary T16 cutoffs, optimizer penalties, every attempted-fit denominator, model selection strategy, independent holdout generation/seed/code hashes, immutable receipt validation and coordinator/independent-statistician signoff. Do not change original v2 freeze or use old v2/v3 development worlds as a new holdout.
6. **Distinct real-fit gate:** even a future successful independently frozen v3 synthetic study never unlocks historical fitting or publication automatically. The 37 October 2026 reserved transcripts and D1 O1–O5 remain sealed.

**Final prospective decision: `STATISTICAL_FREEZE_NOT_ACCEPTED`. The next workstream is a new development-only identification/uncertainty protocol, not a replay or retrospective threshold change. PR #68 must remain draft and unmerged.**
