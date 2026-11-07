# Independent methodological review and prospective v3 freeze requirements

**Disposition:** CONDITIONAL DESIGN ACCEPTANCE FOR SOFTWARE PREPARATION ONLY. Full v3 statistical protocol, prospective study and thresholds are **NOT FROZEN**; no development calibration or holdout is authorized. The separate frozen v2 study and its failure remain untouched. This assessment is an engineering review of assumptions, not independent source authentication or independent confirmation of the future v3 estimators.

## Review findings

1. **Target/estimand separation — CONDITIONAL PASS.** A scalar two-era mean contrast with a known synthetic beta can test temporal methods, but cannot validate a nonlinear lexical/semantic 64-dimensional empirical movement estimand. Calendar-year count, not actor-year row count, controls dependence identification. A T=16 claim must stand on T=16 evidence. Any extrapolation from T24–48 is nonconfirmatory for available 16 years.
2. **Meeting sample — CONDITIONAL PASS.** Fixed original-meeting inclusion probabilities in the synthetic mechanism are valid by construction. Historical 90/28 audit originals, 64 original-PV meeting sample and P2 years have different selection protocols and must not be pooled simply because years overlap. At-risk actors with structural preadmission nonopportunities must be excluded from the denominator, not counted as missing text. The era-shift stress world is explicitly *not source comparable* without separate transport weights and populations.
3. **Missing-outcome identification — CONDITIONAL PASS on artificial randomized phase-II audit; REAL FAIL.** Even with randomized q, response slope gamma estimation additionally requires outcome/response overlap, positivity and specified response functional form. If an external randomized nonresponder audit does not recover missing outcomes, the MNAR response model remains unidentified, and no interval or gamma recovery is eligible. Fitted gamma is **not yet implemented in the v3 prototype**. The existing P1/P2/PR #74 original-source inventories do not constitute such an audit.
4. **Covariance estimation — PARTIAL.** No feasible method may read true generating rho, true nugget, hidden speech outcomes or year shocks. Constraining the nugget to zero is a falsifiable model assumption, not independent identification. The ridge candidate estimates a penalty-constrained nuisance covariance; a noisy objective valley and boundary hits must cause withholding of confident rho claims. Estimating the annual mean and its selection variance in a preliminary stage does not automatically identify year shocks separately from source-measurement errors. The prototype external-nugget and union families are **declared not implemented and withheld**.
5. **Nonstationarity, representation and selection confounding — NOT IMPLEMENTED.** These must be genuine prespecified stress/negative controls, not warnings added after viewing future holdout performance. Independently identify or bound genre, delivered language, translation and recurrent speaker effects; do not infer stable country voice from recorded affiliation.
6. **Protocol preregistration — NOT RUN.** The v2 holdout is public prior evidence and cannot be designated an independent confirmatory v3 holdout. No v3 holdout generator, seed, outputs or performance claims exist. The proposed JSON is deliberately marked `PROPOSED_NOT_FROZEN` and cannot authorize anything.

## Proposed primary factorial and Monte Carlo design — still requiring coordinator signoff

- **Primary T16 factorial:** 3 original-meeting sampling masks × 4 response regimes × 4 year rho values × 3 independent year-nugget SD values = **144 scenarios**, each with 300 development draws and 600 new holdout draws (43,200 + 86,400 attempts). The six-factor dimensional representation extension and nonstationary stress are **not part of the primary scalar confirmation**.
- **Additional exploratory horizons:** T8,24,32,48; do not pool their effective sample with T16. Budget and scenarios must be versioned and committed separately before their holdouts.
- **MC precision:** 600 Bernoulli coverage successes yield ideal 90% binomial SE `sqrt(.9*.1/600)=0.01225` (about 2.4 percentage points for a normal 95% MC interval); actual SE worsens when fits fail. At 95% completion, denominator 570 yields SE ≈0.01256. Report Wilson bounds and support-completed and all-attempt denominator sensitivity. Multiple testing across 144 worlds must use explicit intersection family criteria, not selective reporting.
- **Parameter recovery:** report absolute rho bias, RMSE, grid boundaries and a profile-width/weak-identifiability measure; jointly with interval coverage, beta bias, length, false-confidence, gamma recovery, positivity, weight concentration, convergence and support failures.
- **Oracle controls:** label known true covariance GLS only as `oracle`, never pass oracle quantities to feasible fits or use oracle acceptance to waive recovery.
- **No-audit MNAR:** all attempts must refuse; conditional MAR fitting in a no-audit cell is not a substitute for MNAR identification.
- **Numerical design:** predeclared rho and nugget parameter grids and penalties; externally measured year nugget requires independent measurement-register source and error model, not simulated true nugget injected as a plug-in estimate.
- **Candidate decisions:** joint statistical acceptance requires every prespecified critical T16 world and diagnostic gate. A partial-identification interval can be accepted as a *separately prespecified descriptive uncertainty set* but must not be counted as recovered point rho.

## Freeze sequence (must be completed before any real development calibration or holdout)

1. **Independent review/signoff:** coordinator/statistician approves the estimand, populations, positive-inclusion meeting sampling, response/audit mechanism, representational restrictions and candidate model licenses. Record conflicts and externally identified nonrandom transcript-selection assumptions.
2. **Freeze DESIGN first:** commit immutable JSON with final factorial combinations and cardinalities, seed namespace commitment for dev, locked future-holdout seed-derivation procedure (but **do not draw holdout**), negative controls, optimizer tolerance/bounds, family eligibility, all denominators and full T16 acceptance rule. The currently proposed values are *provisional*, not thresholds.
3. **Freeze implemented producer and verification:** record exact Git commit and SHA256 of each generator, estimator and evaluator module, plus Python/NumPy/SciPy dependency pins. Audit dev-vs-future-holdout independence, no truth leakage and separation of original meeting selection from response/audit. Require an independent holdout generator implemented and audited **before** the first holdout execution.
4. **Development calibration only after approval:** generate new dev worlds; choose penalties/critical values solely from approved development data, with attempts/nonconvergence and broken support recorded, no holdout peeking. Commit a second freeze receipt binding final tuning, code hashes, literal acceptance thresholds and independent seeds **before** holdout.
5. **Holdout immutable once started:** execute a one-time independently seeded holdout with precommitted identities; reject any changed receipt or source producer. Failures must enter denominators; never tune against observed holdout performance.
6. **Publication and real-fit stop:** even a successful synthetic holdout requires distinct source-authenticated 16-year genre/translation/roster and independent random nonrespondent outcome audit gates, then newly authorized lexical representation and real inference. No new source-model fit is triggered by synthetic success.

## Prototype implementation matrix

| Component | Current v3 prototype |
| --- | --- |
| Synthetic original-meeting pi and nested actor/year/meeting effects | Implemented for bounded smoke |
| Structural at-risk denominator | Implemented |
| Transcript response and independently randomized nonresponder audit q | Implemented synthetically |
| Absent audit and missing outcome truth leakage refusal | Implemented |
| IID, zero-nugget AR1 and ridge grid feasible fits | Prototype implemented; **no coverage calibration** |
| Fitted response slope gamma | **Not implemented — blocks completed scientific study** |
| Externally estimated nugget, union sensitivity interval | **Withheld — not implemented** |
| Era-shift design transport, independent source comparability | **Not implemented** |
| Nonstationary stress, full 64D lexical uncertainty | **Not implemented** |
| Development-only bounded smoke | Executable; **not calibration evidence** |
| Full prospective development / confirmatory holdout | Explicitly refused until freezes, and holdout runner does not exist |
| Real source audit and empirical inference | Explicitly prohibited |

## Immutable controls and next statistical decision

Nothing under v2 `inference.py`, `run_study.py`, `synthetic_dev.py`, `synthetic_holdout.py`, original `frozen_development_v2.json`, `holdout_*.json`, `holdout_*.csv` or the existing v2 requirements is modified by this v3 design. No source, private document, 37 reserved 2026 meeting transcripts, frozen O1–O5 gate, PR #64/74 register or historical 2008–2023 representation is accessed.

**Next executable approved engineering step:** implement gamma estimation, nonstationarity and externally estimated-nugget negative controls in a separately reviewed v3 development module; test with fresh invented data and documented rates. **Next statistical decision:** external independent review and commit of the final v3 design/freeze before any confirmatory simulation. This is not authorization to merge PR #68 or fit real data.
