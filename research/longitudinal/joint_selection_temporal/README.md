# W4 joint source-selection and calendar-year covariance calibration

**Methods status:** Synthetic engineering-only. The two-stage selection component and profile-REML year-covariance component are implemented, independently tested, and evaluated against an independently seeded holdout. **Temporal-covariance reliability failed, so the new real 2008–2023 representation was deliberately NOT FIT.**

## Identification: what can and cannot be learned

Selected original UN meeting probabilities are known for the 2008–2015 64-PV design. A speech's final source/verbatim-text match can nevertheless fail because of transcription, translation, speaker matching or archive availability. Missing speech outcomes may correlate with linguistic content. **Selection on unavailable outcomes is not identifiable from the verified speeches alone.**

This implementation uses a **sequential two-component joint correction**, **not** an exact joint maximum-likelihood fit for all speaker, selection and temporal effects. In synthetic experiments it estimates (1) a weighted transcript-response logistic model from ordinary available outcomes and independently randomized second-phase audits of originally missing outcomes, then (2) source-weighted, within-year response-stratified annual means and (3) their calendar-year AR(1) covariance via a fixed-grid restricted Gaussian likelihood. It reports all nuisance estimates and does not give the model the true generating rho, gamma or variance. This is a meaningful test of response adjustment and serial covariance *together*, but it does not establish a fully observed original-UN country/year population likelihood.

The synthetic first-stage original-PV meeting sampling probability is known. For each nonresponder the **independent random verification** has fixed audit probability **0.40**. If that audited outcome is missing, the design records a failure; no invented outcome is inserted. In `AR1_MNAR_no_audit`, there is no nonrespondent random audit and the estimator abstains rather than claiming to learn gamma.

**Real-data gate:** actual 2008–2015 source verification used 64 original PVs from a 118-meeting frame, 855 ISO3-resolved indexed speech rows, 832 seven-token strong full-PV matches and 828 unambiguous country-year observations. It did **not** implement randomized independent outcome audits of missing source transcripts. Earlier 2016–2023 source material was acquired under a separate near-complete meeting methodology and does not provide a newly joined common observation/representation identity. The public [aggregate receipt](../../../docs/parallel-work/W4_JOINT_SELECTION_HOLDOUT_AGGREGATE_2026-10-13.json) contains these source restrictions, and the source-attested early speaker rows remain private.

## Frozen preregistration and dev/holdout separation

[Coordinator preregistration](../../../docs/parallel-work/W4_JOINT_SELECTION_TEMPORAL_PREREG_2026-10-13.md) was committed before synthetic development and heldout simulation. A separate [frozen development-receipt](../../../docs/parallel-work/W4_JOINT_SELECTION_FROZEN_DEV_RECEIPT_2026-10-13.json) was committed **before** reading independent holdout outcomes.

- Development seed namespace: `UNGA81-JOINT-DEV-20261013`, 120 replications ×18 identifiable scenario combinations = **2,160 attempted, 2,120 delivered**, 40 support failures counted. Learned pooled per-year-horizon interval critical multipliers: **T16: 2.208411; T24: 2.003855; T32: 1.840906**. Receipt SHA-256 `a9bda3652748cba980fe900317161a78be8f6fdaed91b5a2bb67b431e21b6639`.
- Independent holdout seed namespace: `UNGA81-JOINT-HOLDOUT-20261014`, implemented in **separate `heldout_world.py` code** rather than importing development DGP. **24 scenarios × 240 panels = 5,760 attempts**. Identifiable scenarios: 18 (4,320 attempts; 4,260 supported fits; 60 failures). Nonidentified no-audit MNAR: six (1,440 refused out of 1,440, **zero unsafe fits**).
- Locked methods compare uncalibrated `t_(T−3)` confidence intervals with one per-T critical multiplier calibrated on the development set **only**. Every scenario reports eligible/failed/refused counts, Wilson 95% uncertainty on synthetic coverage, median and upper width, fitted year-correlation bias/RMSE and frequency at the parameter grid boundary, and recovered response-gamma bias/RMSE.

### Held-out synthetic results

| Measure | Outcome | Locked target |
|---|---|---|
| Nominal 90% calibrated-interval coverage | **12 / 18** identifiable scenarios passed | Every T16 identifiable scenario passes before real fit |
| AR(1) rho point-recovery reliability | **0 / 18** passed | Absolute bias ≤0.12, RMSE ≤0.25, parameter-grid boundary frequency <5% |
| MNAR response gamma, with independent audit | **6 / 6** scenarios passed | Bias ≤0.20, RMSE ≤0.45 |
| MNAR without independent audit | **1,440 / 1,440 abstentions**, 0 unsafe fits | Abstain in all |
| New 2008–2023 real representation | **NOT FIT** | Requires full preregistered numerical and source gates |

In the **T16, AR1 rho=0.65, randomized-audit MNAR** holdout, near-census sampling yielded calibrated interval coverage **90.8%** but year-rho RMSE **0.336**; the stratified meeting source design yielded **88.1%** coverage and rho RMSE **0.367**. Neither is reliable enough under the frozen covariance cutoff. At T32, some rho estimates improve, but numerical calibration and source selection still cannot validate 16 actual UN General Debate annual periods.

**The key result is a failed inference gate, not a new significance test.** Calibrating a t critical multiplier can improve synthetic coverage under these exact DGPs without making covariance parameters reliably identified. A 90% synthetic scalar-period interval cannot automatically be used for the real W4 nonlinear Euclidean discourse shift. The actual selected-source universe is nonrandom with unknown original-text verification response. Both types of uncertainty matter.

## Reproduce and audit

From the isolated `research/longitudinal/joint_selection_temporal` subtree (Python 3.11, pinned NumPy/SciPy):

```bash
python -m unittest discover -s research/longitudinal/joint_selection_temporal -p 'test_*.py' -v

# Development only: execute once, freeze and retain SHA-256 BEFORE testing
python research/longitudinal/joint_selection_temporal/calibrate_development.py --out /private/dev/locked_cutoffs.json

# Independently implemented and separately seeded holdout:
python research/longitudinal/joint_selection_temporal/calibrate_holdout.py \
  --frozen-development /private/dev/locked_cutoffs.json --out /private/holdout/new_run
```

The source-compilation CI also executes the full existing W4 method regressions and original coordinator v1 interchange tests. Synthetic validators include independent Cholesky likelihood, independent constrained response-logistic minimization, source-meeting selection counts, beta=0 shift checks, source probability/date/field tampering, no-audit refusal and hidden-Y leakage rejection. The actual historical source preflight is reproduced **privately** with `source_comparability_preflight.py` against the owner-supplied P2 CSV, UN original index and source-meeting frame. Raw UN names, text, per-country observations and computed vectors are never part of the code or public receipt.

## Mandatory prerequisites before revisiting real W4

1. Conduct and verify genuinely randomized second-phase original-source checks of selected missing/failed transcript outcomes, including known audit probabilities, source text versions, original UN meeting/affiliation evidence, time and language. If such missing texts cannot be recovered, do not pretend the audit identifies MNAR.
2. Obtain a defensible temporal covariance estimator with independent heldout recovery and coverage across all preregistered T16 source-world/selection conditions; do not tune the current holdout DGP to pass.
3. Independently reconcile the **same country-year speech and source-generation population** for 2008–2023 and declare training cutoff and comparable lexical preprocessing **before** fitting any new basis. Do not refit/relabel the existing 2016–2019 frozen checkpoint.
4. Validate downstream 64-D Euclidean movement uncertainty separately from the synthetic signed-scalar regression effect. Define the actual population estimand, temporal shocks and source/actor dependence. Preserve the difference between source-affiliated countries, real individual speakers and government policy positions.

**Unchanged protections:** the old 2016–2019 fitted representation and all source hashes, reserved October 5–6 2026 meetings (37), frozen human review, D1/O1–O5 and public browser release remain untouched. No actual W4 calibrated confidence interval, population extrapolation, political-position inference or publication.
