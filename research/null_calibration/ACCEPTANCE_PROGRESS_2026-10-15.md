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

## Next executable action
Run exact-head local/CI suites against committed study.py and test_study.py, fix any failures, then implement a source-family-preserving W1/W2 candidate-search/refitting adapter and truly estimated year/meeting/speech/affiliation covariance with parameter identification diagnostics. **Do not run or reinterpret the locked holdout until each model/statistic, null design and failure policy is implemented and development-only checks pass.** Keep this PR draft/unmerged.
