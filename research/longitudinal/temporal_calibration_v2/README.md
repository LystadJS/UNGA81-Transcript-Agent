# W4 — Temporal covariance and transcript-selection calibration v2

**Disposition: DOCUMENTED SYNTHETIC FAILURE / ENGINEERING-ONLY. No candidate meets the preregistered temporal-correlation recovery requirements at T=16. No historical W4 model, 64D lexical representation, original transcript or private source has been read or fit.** This isolated subtree neither replaces the W4 estimators nor changes preregistrations, selection registers, independent source-quality audits, 37 reserved October 2026 transcripts, frozen thresholds, or D1 O1–O5.

## Reconciliation of inherited evidence

- Original PR #58: estimated AR1+nugget ρ reliability failed all 18 tested scenarios; feasible serial-year coverage also failed. This was **prior evidence**, not rerun in this branch.
- PR #62: independent holdout 5,760 attempts, 4,260 usable identifiable fits, 60 support failures, 1,440 appropriate unaudited MNAR refusals; ρ recovery **0/18**. Original scalar-contrast cutoffs remain `|bias(ρ)| ≤ .12`, `RMSE(ρ) ≤ .25`, `ρ grid-edge frequency < .05`, completed fraction ≥ .95, nominal 90% coverage within ± .05 **with Wilson-95 interval containing .90**, and median interval width ≤ .80. We preserved these; we did not retune them after looking at holdout.
- Coordinator P1/P2 source integration: **118 meeting symbols = 90 development + 28 independent source-quality audit originals**, a separate selection population from the 64-meeting first-stage probability sample. The 90+28 audit material may not be pooled with the 64-sample inverse-inclusion weights, and the 28 original quality-audit documents cannot be treated as model-tuning units. Prior private source-coverage receipts are not new verification in this PR.
- PR #64 proposes `un.historical-source-audit.v1` source-comparability metadata. `source_adapter.py` checks that proposed structure conservatively; this does **not** declare PR #64 accepted or independently attest original bytes.

## New simulation study and assumptions

The purely invented panel has 99 recurring fictional affiliation effects, 12 original-meeting family groups per year, two declared frame gaps per year, and T = 16/24/32 years with the pre/post break fixed at the midpoint. A scalar true effect +0.20 is known to the **evaluator only**. Outcomes include actor effects (SD .40), meeting nested in year (SD .12), residuals (SD .25), stationary serial-year process (SD .20; ρ=0 or .65), and a **separate year-level nugget shock** (SD .15 in an explicitly misspecified stress world). Near-census includes all meetings; the alternative selects precisely two of three meetings per each of four strata per year, with declared first-stage probability 2/3.

Source verification is separately simulated using a response-logit with outcome coefficient `γ=0` (MAR stress) or `γ=-1.25` (MNAR stress). Every included nonrespondent undergoes **independently randomized** phase-II outcome recovery at probability q=.40, except in the known-unidentified q=0 MNAR world. All unobserved outcomes are `NaN` in `observed`; generator truth is returned in a separate evaluator-only object. A weighted logistic estimator independently estimates γ from respondents and audited nonrespondents. A response-stratified source-weighted Hájek year mean uses ordinary respondents and inverse-q audited nonrespondents. Whole-meeting leave-one-out estimates **conditional descriptive variation**, not an independently calibrated design variance. Empty response/audit strata fail rather than imputing a year mean. If q=0 under potentially informative nonresponse or independent audit provenance is false, estimators refuse all inferential intervals.

**Temporal candidates:** `iid_year` is a deliberately misspecified no-correlation baseline; `ar1_constrained` estimates ρ and year scale under zero added nugget; `ar1_nugget_ridge` estimates ρ, nugget fraction and year scale by fixed-grid penalized profile REML. The latter uses the predeclared penalty `λ² + 0.3(ρ/.92)²`. Both allow rho -0.20 through .92 on the frozen grid and explicitly report grid endpoints and profile support width. Weak profile separation (range ≥ .5 within 2.71 objective units) is flagged, not converted into a precise population claim. Nuisance parameters are **never provided by the generator** to feasible fits. `oracle_gls()` is a separately named known-parameter numerical control, unavailable to empirical or feasible simulation paths.

**Identification limitations:** 16 calendar years are 16 correlated time blocks, **not** 1,584 independent country-years; repeated actor and source-group effects create additional dependence. A flexible year nugget can mimic short-lag AR1 correlation. The two nested stages generate sampling error and selective nonresponse separately. Without an actual independent randomized audit of otherwise unavailable original transcript outcomes and a reconciled 2008–2023 source-generation population, the real MNAR response and longitudinal estimand remain unidentifiable. Synthetic audit success does not supply real source verification. This study targets scalar beta, **not** the nonlinear 64D discourse-distance estimand.

## Development → frozen cutoffs → independent holdout

- Development: 3,600 attempts = 30 scenarios ×120; 2,829 identifiable usable panels, 720 expected no-audit abstentions, 51 support failures. Critical multipliers learned solely from development, separately by horizon and estimator.
- **Frozen before holdout:** `frozen_development_v2.json`, SHA-256 `8a3abd19198332dc58c19299301c5ce1f0bd61749ef724e6093f2027bdf970fd`, committed as `527225986d0c7c2084490ce4fda6df272427577d`. It fixes method/source/horizon grids, original W4 recovery/coverage gates, independent seed namespaces, runtime code SHA-256 and multipliers. Running the holdout requires the unchanged file's expected SHA-256 and verifies all frozen executable-source hashes. The holdout uses an independently written PCG64DXSM world generator, a disjoint SHA-derived holdout namespace, and never imports the development generator.
- Holdout: 7,200 attempts = 30 scenarios ×240; 5,653 usable identifiable fits, 107 support failures, 1,440/1,440 correct no-audit refusals, zero unsafe fits. Fitted rho recovery passes 1/24 identifiable scenarios for constrained AR1, 0/24 for AR1+nugget ridge; neither family passes all eight T16 identifiable scenarios. See [RESULTS.md](RESULTS.md), `holdout_scenarios_v2.csv` (90 method-scenario rows), per-reason failure counts and source-free aggregate receipt.

## Reproduction (only public synthetic files)

Tested locally: Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, Linux, single-thread BLAS, `PYTHONHASHSEED=0`. Exact local environment pins are in `requirements.txt` (CI's older W4 dependencies should be treated as a distinct runtime). No external AI, transcript acquisition, original PDFs, PV hashes or private source inputs are needed.

```bash
python -m pip install -r research/longitudinal/temporal_calibration_v2/requirements.txt
python -m unittest discover -s research/longitudinal -p 'test_*.py' -v

# Development replay writes to a fresh, never-overwritten directory; its output is NOT independent holdout evidence.
OPENBLAS_NUM_THREADS=1 PYTHONHASHSEED=0 python research/longitudinal/temporal_calibration_v2/run_study.py \
  --phase development --out /tmp/new-temporal-v2-development

# Holdout replay uses the already-published, unchanged frozen development identity.
OPENBLAS_NUM_THREADS=1 PYTHONHASHSEED=0 python research/longitudinal/temporal_calibration_v2/run_study.py \
  --phase holdout \
  --frozen research/longitudinal/temporal_calibration_v2/frozen_development_v2.json \
  --frozen-sha256 8a3abd19198332dc58c19299301c5ce1f0bd61749ef724e6093f2027bdf970fd \
  --out /tmp/new-temporal-v2-holdout
```

Each run emits aggregate receipt, method×scenario metrics and a full **fictional** support-failure ledger in the selected local output directory. It refuses an existing output path. Replays do not change the originally frozen cutoffs. The code contains no real-data fitting entry point; both `real_fit` guards raise `PermissionError`. `source_adapter.audit_manifest()` only returns source metadata counts and explicitly withholds original-source authentication, pooling, real fitting, and publication.

**Statistical next decision:** retain `FAIL/WITHHELD` for T16 temporal dependence, investigate longer source-verified historical panels or externally justified covariance restrictions under a separate prospective protocol, and independently verify a randomized original-text nonresponse audit. No real 2008–2023 fitting or publication is authorized by this PR. Coordinator only: review exact head and CI, accept/reject as a *documented synthetic failure*, not as a validated empirical estimator.
