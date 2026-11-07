# Prospective W4 temporal-identification study — v3 protocol proposal

**Status: DESIGN ONLY / NOT PREREGISTERED / NOT EXECUTED.** This is a protocol for a *new* study. It is neither an amendment to the frozen v2 development/holdout nor evidence of acceptable 16-year inference. Before any v3 development simulation, the coordinator must independently approve and commit a versioned protocol and its design-specific thresholds. No v3 random seed has been run, no new holdout inspected, no real 2008–2023 representation fitted.

## Unchanged restrictions and reason for the new design

PR #62 failed rho recovery in all 18 assessed settings. The frozen v2 study retained that problem: constrained AR1 recovered rho in 1/24 assessed identifiable scenarios, regularized AR1+nugget in 0/24; neither passed all eight T16 design/world cases. Its thresholds, development receipt, scenarios, results and real-fit stop are **immutable historical records**. The accepted v2 output is a reproducible *negative result*, not a calibrated estimator. This proposal must not reweight the v2 holdout or relabel its scenarios as new confirmatory evidence.

Only 16 distinct calendar-year shocks are available in the target 2008–2023 contrast; additional speeches or countries do not increase this temporal sample size. The 90/28 original-PV source-quality audit, 64-meeting probability sample, and later 2016–2023 P2 source frame are not automatically comparable or exchangeable. Successful source authentication is distinct from a known probability-of-inclusion design, independent observed delivery language, source verification missingness, and randomized missing-*outcome* audit.

## Primary research question and estimand

For synthetic repeated-actor meeting panels with a known design, can a feasible method construct 90% two-era **scalar** contrast intervals with calibrated repeated-world coverage *and* separately recover the prespecified nuisance dependence parameters under weak short time-series support? Primary unit for temporal dependence: **whole calendar year**. Meetings nest within years; affiliations recur across meetings. The synthetic beta is an intentionally known generating contrast, not political stance. This study does not establish uncertainty for nonlinear 64D lexical/discourse-distance estimands; transferring results requires separate lexical-refit and source-design experiments.

Define the observed source process in stages:
1. Original-meeting frame and fixed at-risk population, including preadmission structural ineligibility. Meeting inclusion `S_{my}` with recorded design-specific probability `π_{my}`, positive on the target frame.
2. Within sampled meetings, original speech/text response `R_{imy}`, potentially outcome-dependent, with response probability `g(Y, X, m, y)`.
3. An **independent randomized second-phase outcome-recovery audit** `A_{imy}`, applied only to nonrespondents with prespecified strictly positive `q_{imy}`, auditable assignment, original outcome retrieval and verified linkages. `A=1` must recover the previously missing outcome; mere metadata verification does not suffice.
4. Genre, translation, roster and representation measurement layers are separate, with their own missingness and uncertainty.

Without independently documented q-based outcome recovery, an unrestricted outcome-dependent response model is not point identified. **Mandatory refusal**, even if coverage on an assumed MAR simulation looks acceptable.

## Candidate comparison, with assumptions

All nuisance covariance parameters must be estimated *from available data*. A supplied-true-covariance Gaussian GLS is an explicitly labeled oracle calibration control and cannot enter feasible estimation or model selection.

| Family | Required assumption | Failure to distinguish |
| --- | --- | --- |
| IID-year control | Serial covariance = 0 | Bias from serial shocks; never treated as default independence |
| AR1 without nugget | Stationary AR1; independent year-nugget exactly zero | Unverifiable exclusion restriction |
| AR1 with fixed *externally measured* nugget | Independent replicate measurement study provides year-nugget variance; no information from holdout outcomes | Replicate noise may not represent calendar shocks |
| Hierarchical shrinkage AR1+nugget | Penalty scale set by development-only simulation or external sources; covariance parameters estimated | Penalty-induced shrinkage/boundary bias |
| Partial-identification / union interval | Declared bounded rho and year-nugget assumptions fixed before testing | Wide or noninformative uncertainty; not a point rho recovery pass |

Do **not** relabel fixing a nuisance parameter to its generating truth as a feasible estimator. Fixing nugget=0 or introducing a prior is an externally justified restriction that must be reported, and evaluated under wrong-restriction stress tests. Compare joint coverage/rho recovery and coverage-only robustness **separately**; no interval-only success can excuse failed nuisance identifiability under the original acceptance rule.

## Planned factorial design (not yet frozen)

- T=8,16,24,32,48 calendar years for synthetic feasibility curves; **T16 is mandatory primary**, longer T only extrapolation, never proof of available historical data.
- Source designs: near-census, fixed stratified 2-of-3 meeting sampling, and declared era-shifted meeting-design stress; no silent 90/28-to-64-probability transfer.
- Year process: iid, AR1 rho near zero, moderate positive and strong positive; zero/moderate/high year nugget; nonstationary regime-change negative control.
- Response: conditionally ignorable MAR, audited outcome-dependent MNAR (randomized q>0), unaudited MNAR (q=0, expected universal abstention), weak-positivity and audit failure.
- Repeated actor, year and meeting shocks with whole-group resampling; nontrivial link between source response and actor/year to expose positivity and residual confounding.
- Representation: reference-fixed scalar truth first, then a separately defined source-comparable training-only 64D lexical-refit uncertainty layer **only after an independent methodology approval**. Do not use the reserved 2026 meeting holdout.

Use a **separate prospective v3 dev namespace and holdout namespace**. No reuse or inspection of the v2 holdout for v3 tuning; it is public history, not independent v3 confirmation. Store executed seed values, git SHA, package versions, generator and estimator hashes, source design/threshold version, all attempted fits and failure codes. The final factorial grid and target simulation count require pre-execution approval based on Monte Carlo precision and compute limits.

## Independent development/holdout sequence

1. **Protocol authorization (NOT RUN):** independent statistician/coordinator reviews identification and population assumptions, estimands, factorial grid, falsification controls, allowable family weights, Monte Carlo budget, and failure/refusal categories. No empirical source bytes needed for this design stage.
2. **Source-audit feasibility gate (NOT RUN):** independently verify historical meeting frame completeness, inclusion probabilities, original text response status, an actual independent probability-sampled randomized nonresponse outcome-recovery mechanism, genre, speech delivery language, roster and comparability across 2008–2023. Record signed or independently reproduced evidence provenance. *The existing P1/P2/PR #74 audits are not that randomized response experiment.*
3. **New dev runs (NOT RUN):** test candidate estimators and weak-identifiability diagnostics on development-only synthetic draws. Consider profile likelihood, externally calibrated nugget measurement, partial identification and effective observed calendar-year support. Record all failed fits.
4. **Lock receipt (NOT RUN):** commit a reviewed v3 freeze record containing code hashes, exact scenario population, thresholds, T16 primary criteria, power/Monte Carlo precision, acceptance aggregation, seed namespaces, and critical values before any holdout generation. Protect against mutation.
5. **Independent holdout (NOT RUN):** use a second independently implemented generator with separate seed namespace; run once under frozen producer/threshold hashes. Publish only source-free aggregate receipts and failures. Any corrective tuning requires a wholly new prospectively registered holdout, not reuse of this one.
6. **Decision:** PASS only when all predeclared primary T16 parameter recovery, interval coverage, convergence/completion, interval width, bias, false confidence and MNAR refusal constraints pass with declared denominator definitions. Otherwise FAIL, with full scenarios and uncertainty published. Passing synthetic gates **never automatically authorizes historical fitting**.

## Acceptance design and measurement

Carry over the original frozen v2 limits as **nonbinding reference values** for prospective planning: absolute rho bias <= .12, rho RMSE <= .25, rho boundary rate < .05, completion >= .95, 90% coverage within +/- .05 with Wilson-95 interval containing .90, median width <= .80. **These historical numbers remain unchanged in v2.** The independent v3 preregistration must choose and lock its own final thresholds *before v3 dev/holdout as specified* and justify whether rho parameter recovery is meaningful under explicit restriction cases. No retrospective adjustment from observed holdout coverage is permitted.

Mandatory output denominators: planned opportunities; included/unsampled meetings; at-risk speech opportunities; response/nonresponse and independently audited missing outcomes; annual support; attempted/completed/convergence-refused numerical fits; correct nonidentification abstentions; interval attempts; empirical misses; false confidence defined in a locked way; per-scenario nuisance bias/RMSE/boundary/profile width and Monte Carlo uncertainty. Preserve structural ineligibility, source absence, text nonresponse, source verification failure and missing outcomes distinctly. Show source selection effects separately from year dependence and from representation refits.

Negative controls: q=0 MNAR mandatory refusal; zero/near-zero meeting positivity mandatory refusal; same-label but incompatible original meeting designs mandatory refusal; shifted genre/language/roster or feature fingerprint mandatory refusal; short T / AR1-nugget observational equivalence explicit insufficient-information outcome; out-of-support true rho flagged, not silently clamped; convergence failures in attempted denominator; oracle/feasible results labeled separately.

## Existing source contracts and release disposition

The PR #64 proposed `un.historical-source-audit.v1` is **not automatically accepted**; compare exact accepted interface with coordinator after review. Adapter must never create missing outcomes, fabricate matching source hashes, recode structural membership gaps as speech absence, or implicitly pool distinct source sampling generations. PR #74 reports source-genre/translation/roster/selection uncertainties that independently preclude real fitting.

No production pathway, HTTP fetch, full source-file pointer, transcript text, source-bearing country-year receipt, new W1/W4 model fit, change to previous preregistrations, publication manifest edit, evaluation-lock change or 37 reserved October 2026 meeting read is authorized.

**Explicit status:** v3 protocol PROPOSED; development NOT RUN; freeze NOT COMMITTED; holdout NOT RUN; statistical identification NOT ESTABLISHED; real 2008–2023 fitting WITHHELD; PR #68 engineering-negative disposition unchanged. Coordinator must authorize a separate v3 prospective research workstream before execution.
