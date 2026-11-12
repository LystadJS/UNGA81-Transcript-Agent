# Independent review of merged PR #60 (engineering acceptance only)

Review date: 2026-10-15. Reviewer workstream: independent null calibration.
Read-only upstream: `research/integration/w1_w2/nuisance_estimation/reml.cjs` Git blob `a56e04db558e129e5ea4d107a312d6c5c627dcad`, candidate design `design.candidate.v0.json` Git blob `eac3c87b2de555db55202d91cf440eaef228e4d0`, plus synthetic, tests and README from `main` `25ba1a7948c33188f21986af3cffbe73bbcafdba`. No changes to these files.

## Computational assessment

The candidate minimizes a Gaussian restricted negative log likelihood with `V = vm*I(meeting) + va*I(affiliation) + vy*rho^|year gap| + ve*I(row)`. Its Cholesky evaluation solves `V^{-1}` implicitly; the log-determinant accumulation from Cholesky factors of `V` and `X'V^{-1}X` is algebraically consistent with the standard REML objective, up to a covariance-independent fixed-effect normalizing constant. The selected synthetic responses do not appear to pass generating variance or rho values as arguments to `fit`. These are **static-review findings**, not a new numerical objective re-execution or proof of optimizer accuracy.

The numerical candidate uses three rho starts (-0.7, 0, 0.7), bounded coordinate descent with finitely many descending step sizes and a default 1000 evaluations. It does **not** compute a profile-likelihood confidence region, observed-information Hessian, independent optimizer agreement, or parameter coverage. Finite objective / Cholesky success can occur with flat, confounded or locally optimized covariance profiles; `verify` itself explicitly disclaims provable covariance identifiability. A warning at |rho|>0.77 is not a calibrated rejection rule. The hard |rho|<0.85 bound can bias estimates near or beyond that range. Treat optimization budget exhaustion and near-boundary estimates as reliability failures, not positive fits.

## Independent assessment of reported stress evidence

The PR #60 coordinator report gives eight fitted scalar panels across four feasible synthetic regimes, with four withheld scenarios. It reports severe conditional-selection recovery failure in E8: estimated rho -0.849 against fictional rho +0.65, absolute error 1.499; E3 showed near-boundary estimates. These are **inherited, source-referenced PR #60 results** rather than rerun independent experiments. Its 19 source-safe CI tests and analytic iid-intercept control establish engineering behavior, not finite-sample identification or calibrated type-I error. The candidate has no reported nuisance-parameter confidence interval coverage. On that evidence, inferential acceptance is **FAIL / WITHHELD**.

## Unresolved requirements for scientific use

1. Independent general-design REML implementation must match objective values at fixed parameter vectors (not merely optimize to similar minima). Check normalization, perturb X, covariance gradients, near-singular V, and alternative bounded optimizers.
2. Separate year AR1 variance from meeting and year-level nugget components, and quantify a profile-likelihood curvature / information condition before treating rho as identified.
3. Predeclare independent seeds, recovery bias/RMSE, boundary frequency, coverage criteria and failure denominators before >=200 feasible panels per stress regime and >=1000 for confirmatory calibration.
4. Use observed source-selection masks and explicit MNAR sensitivity. The selected-panel conditional-X estimator does not identify source attendance probabilities or population inference.
5. Fit a verified token/representation nuisance law; a Gaussian scalar proxy does not establish the lexical covariance or representation effects needed by W1/W2.
6. Re-estimate all nuisance parameters and refit the full frozen W1/W2 candidate search in **each** reference draw. Independent source-family closure and multiple-testing controls must be checked before external replication or rejection claims.

## Disposition

**STATIC NUMERICAL DESIGN REVIEW COMPLETE; STATISTICAL ACCEPTANCE WITHHELD.** Do not reuse PR #60's synthetic fit recovery as accepted nuisance truth. PR #57's frozen critical values and its 13 scientific gates remain unchanged. No empirical text, private source, or sealed 37-meeting holdout was accessed.
