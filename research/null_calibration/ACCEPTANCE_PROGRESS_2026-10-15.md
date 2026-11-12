# Engineering acceptance progress — 15 October 2026

**Decision: WITHHELD; engineering-only draft PR #67.** No empirical text or held-out original transcripts accessed. All changes strictly under research/null_calibration/. Frozen PR #57 values, its 1999 x 1000 reference schedule and G01–G13 remain unchanged.

## GitHub/source references
- Starting main reviewed: 25ba1a7948c33188f21986af3cffbe73bbcafdba; starting workstream head b1f402eb70efbeda024ca363fd1c04988e20c140.
- Immutable synthetic design lock (branch blob): f6b28fcbe2ee27febdb51f1a1cf05d19cecef02a. It fixes 16 development worlds, 120 holdout worlds, 99 reference draws, seed 810081 and nine named scenarios for the **future confirmatory exercise**.
- Existing preliminary PR #57 frozen design: SHA256 bfffab858c6a478e7205d5c230450cb7fcc62445e5d4889ba1e366bd3bd79ea9 (inherited GitHub record, NOT recalculated).
- Independent PR #60 static candidate review: PR60_INDEPENDENT_REVIEW.md. Reported severe E8 rho-recovery failure (-0.849 vs +0.65) is inherited, NOT independently reproduced in this smoke.

## Newly executed local development smoke (not locked confirmation)
- Environment Python 3.13.5, stdlib, no network. Command on local development implementation: python3 -m unittest -v test_study.py (8/8 PASS); python3 study.py --worlds 2 --refs 9 --out smoke.json.
- Local development artifact SHA256 a35b6c147a548df53e420f163355a174a2bff08b16b8ce156e4310a47827d535. This is **not the checksum of the committed study.py** or a repository-distributed output; the local prototype differs from the GitHub version. The local tests therefore do not establish exact-head PR CI acceptance.
- Local smoke: 7 scenarios x 2 phases x 2 worlds = 28 worlds. 20/28 complete, 8/28 withheld. Five scenarios complete 4/4 each; eight-year, crossing-family, MNAR scenarios withheld 4/4 each. 180/180 attempted references successful on completed worlds; 0 reference numerical failures. Zero rejection events were observed across the 20 completed worlds with 9 references each. **No valid false-positive or power estimate:** 9 references implies minimum attainable p=0.1, making alpha=0.05 rejection impossible. The observed zero rejections are mechanically inevitable, not favorable performance. No parametric covariance-interval coverage was estimated.
- Local fixture seeds originate from master 810081 and SHA256 phase/scenario/index derivation; source identities per world are SHA256 of canonical JSON rows. Local receipt bytes are not included in the repository to avoid confusing development smoke with confirmatory results.

## New committed implementation
- study.py: synthetic AR1-year/group/length/count design, prevalence and group-variance **moment proxy estimation from observed simulated counts**, estimate/refit per reference, independent seed partitions, full attempted/withheld ledger and Wilson summaries.
- test_study.py: synthetic deterministic controls, explicit refusal of invalid IDs, wrong representations, invalid counts, source-family overlap, eight-year weak design, and outcome-dependent selection.
- No actual W1/W2 numerical fitting, no independent source-level replication, no estimated AR1, affiliation covariance, speech random effect, lexical/embedding feature covariance or selection model. Those are statistical and acceptance blockers.
- Unlike the tested local prototype, newly committed modules have **not yet run on the exact GitHub head**. Do not cite the local 8/8 as PR CI passing. Exact-head validation command: `cd research/null_calibration && python3 -m unittest -v test_calibration.py test_study.py`.

## Acceptance checklist
| Criterion | Result |
|---|---|
| Exclusive scope/privacy | PASS on described file paths; coordinator must verify exact final PR diff |
| Distinct null hypotheses | PARTIAL (protocol; operational single proxy statistic only) |
| Synthetic group/length/prevalence and seeded reference generator | PARTIAL |
| Estimated nuisance (no oracle) | PARTIAL (pooled moments; rho unidentified) |
| Independent holds and attempted/failed accounting | PARTIAL (development smoke only) |
| Method-family balancing | PARTIAL (existing calibration.py, not integrated with study) |
| Source-level replication | NOT IMPLEMENTED |
| Identifiability/selection sensitivity | PARTIAL (fail-closed refusals; no selection estimator) |
| Frozen-design full 16/120 worlds x 99 references | NOT RUN |
| Statistically valid false-positive, coverage, power | NOT AVAILABLE |
| Independent review PR #60 | STATIC REVIEW; numerical independence NOT RUN |
| GitHub exact-head CI and coordinator approval | NOT VERIFIED |
| Scientific publication | WITHHELD |


## Independent numerical covariance diagnostic — follow-up (2026-10-15)

**Numerical FAILURE; not an exact-head GitHub CI run.** A separate offline Python 3.13.5 diagnostic on the **local prior-turn prototype** generated 200 synthetic independent 16-year worlds (two meetings/year, four passages/meeting), with AR1 year-shock generator coefficient 0.55 and source-group moments estimated without supplying the generator's coefficients. All 200 fits completed and all 200 single reference draws completed; zero failures. The statistic was observed yearly count-prevalence lag-one correlation, paired against one bootstrap reference on the same source design.

- Across 200 paired worlds, mean lag-one correlation in generated observations: **0.2836830483**.
- Across the same 200 worlds, mean lag-one correlation in nuisance reference draws: **-0.0646777548**.
- Mean paired difference: **+0.3483608031**, standard error **0.0263422250** (descriptive, not type-I coverage inference).
- Estimated year AR1 coefficients: **0/200**. The moment estimator has no rho component, and its independent-meeting bootstrap destroys year-level serial covariance.
- Local exploratory receipt SHA256 **edc3c4a2564fff9c86831bd81fa67ec485ffe20e38e3d15eb0a3ac8eca684e66**; local benchmark script SHA256 **6860633fcec47e65407c5cf87538427d657d13f9e2b35db533c3b0d0b8dc4ef9**. These hashes refer to the local prototype evaluation, **not committed source files**.
- A separate repository-owned and reviewable `benchmark_covariance.py` now runs a corresponding diagnostic against **committed** `study.py`, but its exact-head numerical output remains **NOT RUN / NOT VERIFIED**. Do not substitute local-prototype numbers for that output.

**Disposition:** covariance preservation **FAIL** for the tested prototype; scientific calibration remains withheld. These 200 worlds are a development stress experiment, not DESIGN_LOCK's 120 independent holdout worlds, and do not satisfy PR57's 1,999-reference budget. No observed p-values, type-I/coverage or power estimates are inferred from a single reference draw. The confirmed structural gap (rho not estimated, year shocks not sampled) requires design repair before confirmatory holdout use.

**Reproducibility/CI gap:** This execution environment cannot resolve github.com for a Git clone, while the GitHub connector supports read/write contents but not shell execution. The source files in this branch were inspected via the connector, but the complete exact-head committed test suite could not be executed. Latest-head GitHub workflow-run and combined-status queries returned empty arrays; **empty != PASS**. No CI workflow changes were made because worker ownership is limited to this namespace.

**Exact-head executable checks:**
`cd research/null_calibration && python3 -m unittest -v test_calibration.py test_extended.py test_study.py`
`cd research/null_calibration && python3 benchmark_covariance.py --worlds 200`

## Next executable action
Run exact-head local/CI suites against committed study.py and test_study.py, fix any failures, then implement a source-family-preserving W1/W2 candidate-search/refitting adapter and truly estimated year/meeting/speech/affiliation covariance with parameter identification diagnostics. **Do not run or reinterpret the locked holdout until each model/statistic, null design and failure policy is implemented and development-only checks pass.** Keep this PR draft/unmerged.
