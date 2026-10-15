# Prospective synthetic-only null calibration protocol v0.1

## Status
Engineering prototype; not a preregistered empirical study, not a replacement for frozen PR #57 thresholds. No empirical text, models, evaluation lock or publication controls are accessed. All results remain engineering-only.

## Three distinct nulls
- **Assignment stability:** repeat fits do not exceed nuisance-preserving repeatability after matching source group, meeting, speech, length, prevalence and representation.
- **Latent structure:** a prespecified held-out cluster-separation statistic does not exceed the distribution induced by a fitted nuisance-only generator, conditional on observed source design.
- **Cross-source replication:** a development-selected structure has no transferable out-of-group performance advantage over a source-group-preserving null. Replication requires independent source families, not multiple passages from the same family.

Do not treat coassignment, stability, or source replication as an inferential p-value. The `calibrate` API only calibrates a supplied prespecified scalar statistic against independent null simulations; it does not implement clustering or an estimator.

## Design freeze before holdout
1. Freeze population and unit, group/parent identifiers, representation hashes, source hash basis, statistic, nuisance model, estimator, number of attempts, family weights, alpha, seeds and failure policy.
2. Split development and holdout seeds, and, for external replication, entire source families. Holdout must not influence model/threshold choice.
3. Estimate nuisance parameters from each synthetic replicate's training groups. Never pass simulator truth to the inference estimator. Preserve parameter estimates, convergence and weak-identification diagnostics in the attempt ledger.
4. Fit the same complete candidate-search procedure to each reference replicate; do not compare a selected observed maximum with a single unselected null fit.
5. Calibrate on development reference statistics using the finite-sample upper order statistic; strict exceedance on untouched holdout. All failures and unassigned cases remain in denominators. A failure of estimation/identifiability blocks a readiness decision.
6. Independently evaluate null type-I error and known-structure power/coverage over separately seeded holdouts. Report exact attempted counts and binomial uncertainty; do not retune thresholds based on results.

## Synthetic generator and stress axes
`generate` creates group-correlated length-varying token counts with configurable latent signal, source-group imbalance and heterogeneous dependence. This is a **toy generator**, not a calibrated diplomatic-text simulator. It does not yet model cross-meeting speech nesting, tokenizer/embedding effects, source-family replication or realistic lexical covariance. It cannot validate scientific coverage claims.

Required additional stress experiments before readiness: few effective groups, imbalance, unidentifiable nuisance components, misspecified group dependence, correlated representation families, estimation failure, missing/duplicate source hashes, source-group shift, unassigned fits, known-structure alternatives and nuisance-only negative controls.

## Balanced consensus
Each method family contributes one total vote, shared equally among its converged settings. Pairwise eligible opportunities exclude unassigned observations and failed fits; their denominators and the full attempt ledger are reported. Failed families must be surfaced separately. Pairwise fractions are not probabilities of diplomatic agreement.

## Acceptance commands
`cd research/null_calibration && python3 -m unittest -v test_calibration.py`

Requires Python >=3.10, standard library only. Deterministic fixture SHA is computed by `digest(generate(31))`. Record actual Python version, commit SHA and output in the coordinator review.

## PR #60 independent review — pending
PR #60 is an unaccepted nuisance-estimation candidate. Before adopting it, review estimator parameter identifiability, group-level degrees of freedom, true-parameter leakage, boundary estimates, nonconvergence, unequal source groups, sandwich/bootstrap calibration and misspecified dependence. No claim of its validity is made here.

## Explicit readiness decision
**NOT READY for statistical acceptance.** This implementation establishes a synthetic generator, fit-accounting consensus and fail-closed scalar calibration primitive. Missing are actual nuisance estimation, multilevel simulation, independent source-level replication estimator, full simulation sweeps, numerical type-I/power/coverage evidence and PR #60 code-level review. Frozen PR #57 critical values remain unchanged.
