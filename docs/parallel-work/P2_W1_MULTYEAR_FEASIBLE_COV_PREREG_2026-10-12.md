# P2→W1 revalidation and feasible multi-year covariance calibration — preregistration

**Frozen:** 12 October 2026, before the *new* source-byte replay and the new simulation runs. This is an additive reproducibility study; previously published 8 October 2026 results are historical observations and **not blinded**. No prospective or geopolitical causal claim follows.

## Objective and source scope

Independently replay the existing P2 original-PV authentication contract on all **105** documented original General Debate UN meeting symbols for 2016–2023 (GA 71–78). Recover the 105 full official PDF bytes into **private recipient-encrypted** outputs from the UN Official Document System without accessing 2024–2026 or the 37 reserved October 5–6 2026 meetings. Pin SHA-256, page count, meeting symbol and extracted text. Independently recompute the seven-token/ten-decile whole-speech matching rule for the uploaded publisher-MD5-verified Harvard v14 tar, and preserve exclusions, persons versus recorded affiliations and missing versus unverified rows. No source text or per-country vectors to public GitHub.

**Fidelity criteria fixed before replay:** seven-word shingles ≥0.90, ≥8/10 speech deciles with ≥0.80 match, and both first and last 30 shingles with ≥0.40 match. Unique Harvard country×session keys, non-duplicated original PV hashes, source meeting ID/year mapping, and country role attribution require independent checks. Never bypass errors or recode a source as verified merely to approach the archived 1,543/1,545 outcome.

## Authenticated P2-to-W1 contract audit

Test both existing authenticators (`research/source_acquisition/p2_expansion/p2_to_w1_source_adapter.cjs` and the W1 `frame.cjs` P2-specific gate) using the recovered 105 original-PV bytes, pinned Harvard source tar SHA-256 and complete/accepted row-level text hashes. Check the exact 792-country-year inventory, source-verification statuses and source text/meeting/date basis. Explicitly test adversarial mutations: wrong source bytes, changed Harvard text, forged speaker/person promotion, meeting/date mismatch, duplicated source, unsupported source schema, false strong-match metrics and forbidden 2026 holdout. Distinguish independent recomputation of whole-PV match from merely trusting an attestation field. Retain the **old** `un.parallel-analysis.v1` analytics schema and `un.parallel-source-inventory.v1` companion unchanged.

Original W1 numerical fits remain unchanged. If running W1, max allowed source-backed population **600**, with exact source/selection hashes and skip/failure denominators. No inference from a nonrandom 600-row subset.

## Preregistered prospective synthetic multi-year study

**Purpose:** test when feasible *estimated* serial-year covariance estimators become numerically plausible in a toy model, without supplying real UN confidence intervals. This extends the previous preregistration rather than retroactively tuning it.

**Synthetic DGP (completely specified):**
- Fixed **99 synthetic country trajectories**, with **8, 12, 16, or 24** annual blocks (4, 6, 8, 12 years per era); annual scheduling and meeting memberships follow a deterministic cycle of the official 2016–2023 PV meeting distribution but **all future years and all outcome values are synthetic**.
- Equal country-period signed scalar contrast estimand `beta=+0.20`. Per-row outcome `y_it=0.2*post_t + a_i + u_t + m_{g(i,t),t} + e_it` with independent country intercept `a_i~N(0,0.40²)`, source-meeting-within-year shock `m~N(0,0.12²)`, and observation noise `e~N(0,0.25²)`. Common year effect has marginal SD **0.20** and is either iid normal or stationary AR(1) with **rho=0.65** and stationary innovations SD `0.20*sqrt(1-rho²)`. Parameters are known **only to the simulator**, never supplied to the estimators.
- Two fixed, outcome-independent sampling masks: (A) near-census, two deterministic missing country-years per eight-year block reflecting the documented 790/792 rate (not the original private exact mask); (B) *restricted coverage stress*, original documented per-year marginal capacities `[56,53,71,72,63,66,83,59]` of 99, assigned deterministically by seed and balanced so each country has at least two observations per four-year era. Repeat each eight-year mask in additional synthetic year blocks. Both are **synthetic surrogates**, not proof of actual selection ignorability. Missingness is fixed and never decided using simulated outcomes.
- Monte Carlo **R=400** per scenario (4 lengths × 2 year worlds × 2 fixed masks = **16 scenarios, 6,400 attempted simulations**), master seed **20261012**. No bootstrap/parameter method tuning after inspecting calibration results.

**Intervals for the known signed scalar beta**, nominal two-sided **90%**:
1. Naive 99-country paired t, treating country trajectories as independent despite shared year/meeting shocks.
2. Welch t on unweighted annual source-year means, assuming iid years (expected to fail AR1).
3. **Feasible AR(1) GLS with data-estimated covariance**, estimating rho by bounded REML profile over `[-0.85,0.85]` from the **observed yearly means** and period indicator, estimating marginal year residual variance from the GLS residual quadratic, using Student-t reference df `T-3` to account approximately for one estimated serial nuisance parameter. Critically neither rho nor the year-effect SD is fixed to its true DGP value inside the estimator. Report rho boundary hits, nonconvergence, interval width and failures; do not describe this as oracle GLS or guaranteed small-sample calibration.

For each method/scenario report attempted/eligible/failed counts, coverage, Wilson 95% interval, Monte Carlo SE, median width, bias, true beta, mean fitted rho and rho boundary count where applicable. A method **passes synthetic DGP-specific calibration** only if ≥380 usable replications, absolute coverage deviation ≤0.04 from 0.90 and Wilson interval covers 0.90, with no hidden non-delivery. This criterion does **not** grant inference on eight actual historical years. Report all failures, including inability of REML to distinguish low N_year from period effects; never tune bounds, df, cutoff or masks after simulations.

**Mandatory controls:** zero-effect `beta=0` implemented as an invariant shift of the same synthetic outcome generator and unit-tested, correct interval containment logic, year/month scope validator, deterministic same-seed replay for at least one scenario, and tampered-source negative controls. Avoid falsely labeling coverage rates as political significance.

## Empirical/statistical acceptance

- Original PDF full-source bytes and concordance must be independently replayed with actual sources; a public aggregate record alone is not reauthentication.
- A validated source-ingestion adapter may carry exact existing source hash and population identity; private 792-row companion remains authoritative missingness record.
- A synthetic feasible-GLS pass in T=12 or T=24 **cannot** retrospectively justify country/year political inference on the real 2016–2023 T=8 panel with four years per era, purposive PV selection and unmodeled speechwriter/language/agenda dependence.
- Keep the 37 reserved 2026 October meeting transcripts unopened, frozen evaluation/O1–O5 gates unchanged, private source and person rows out of public GitHub, and W4 scientific/browser release ineligible until separately accepted.

**Completion receipt:** versioned source/fit identities, exact new document bytes and source-matching counts, simulation table for 16 scenarios, parameter-estimation diagnostics, explicit success/failure/NOT_RUN gates, full method SHA and no private speech outputs in the public PR.
