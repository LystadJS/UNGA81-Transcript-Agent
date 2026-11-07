# PR82 independent coordinator engineering review — 15 October 2026

## Disposition: HOLD / CHANGES REQUIRED

Candidate PR82 remains draft and unmerged. Candidate head: `32112ff5793c1be763db709aa3ef536fb409428a`; original base: `93b17c8779d959f5dd5559adb7f56381210f2f89`; current reviewed main: `f593301d27dc300ec6a77621846cc75bfacd43da`. No publication or release approval. This separate coordinator review adds tests and a read-only, pinned review workflow, not changes to the candidate estimator, frozen scientific gates or reserved sources.

## Verified supplement

The attached `UNGA81_Phase1_Validation.zip` has 12 matching SHA256 manifest entries. Its selected Python/R/schema files reproduce the candidate Git blob identities. Re-execution using R 4.5.0 and Python 3.13.5 reproduces 26 synthetic panels, 3,311 assertions, maximum error `1.3322676295501878e-15`; the independent R/NumPy 8-golden plus 250-seeded arithmetic audit reproduces maximum error `5.684341886080801e-13`. These results are genuine but do not cover all valid identifier forms.

Existing hosted run `38764083226` succeeded on effective merge `da62801f64c6a6eb9ae01e0aa6fb2fa4a81221ce` with the same tree as candidate head (`acfe96681c8fa545ec3eb16cb0ffce463c0d7cfa`). Its 41 bridge/sidecar tests include 40 passes and one R skip. That existing workflow invokes unittest, not the runner's `--require-complete` guard; its green result therefore does not automatically enforce R coverage. Current main has advanced; historical effective-tree evidence does not establish current-main integration.

## Reproduced correctness blockers

### R1 — R coerces source identifiers and changes the grouping estimand

`arithmetic.R` reads TSV inputs using `read.delim()` without explicit column classes. Valid string meeting identifiers `01` and `1` collapse to numeric `1` when the column is numeric-looking. For two original parents with vectors 0 and 2 in meeting `01`, and one with vector 5 in meeting `1`, the required meeting-balanced country profile is 3.0 with weights 0.25/0.25/0.5. The exact committed Python producer returns that result. The exact committed R implementation exits successfully but returns equal 1/3 weights and distance 2.33333333333333 (US profile zero). This is not a tolerance discrepancy. Numeric-looking period labels similarly need exact string preservation.

Required repair: declare identifier columns as character; parse only declared numeric feature columns; explicitly validate conversions and preserve missing values. Add independent tests for numeric-looking/leading-zero meeting and period identifiers. Do not change the weighting policy or tolerances to accommodate the wrong result.

### R2 — Accepted period identifiers can violate the producer's own output schema

The source contract and `validate_source()` accept a 160-character period identifier. The producer then constructs `USA/<period>` (164 characters), while output profile/comparison IDs retain the 160-character token bound. `build_us_reference()` rejects this otherwise admissible source with `SchemaError: String resource bound`. Source acceptance is not closed under the declared transformation.

Required repair: use a separately typed bound for derived IDs or a deterministic bounded identity, or tighten the input limit consistently before accepting input. Retain the original period identifier and source identity. Test the boundary across Python, Node and the independent standard JSON Schema validator.

## Hosted revalidation proposal

The new coordinator workflow pins both candidate head and reviewed main, provisions R, runs the original suite with `--require-complete`, and applies fresh adversarial tests in both exact-head and disposable effective-tree workspaces. It never merges a branch, pushes a candidate update, fetches UN sources, reads reserved transcripts, deploys assets, changes scientific thresholds or grants publication permission. A failing adversarial probe must leave the job failed; there is no continue-on-error acceptance shortcut. Hosted results must be recorded after execution in this review PR and PR82 discussion; at this commit those new runs are not claimed complete.

## Acceptance conditions

Repair R1 and R2 within PR82's owned subtree, pin the revised head, rerun all original tests with mandatory R and zero skips, rerun independent probes and applicable source/interchange regressions against current main, and reconcile changed-path/ownership evidence. Preserve the original failing reproductions. Until then engineering acceptance is withheld. Scientific acceptance, calibrated uncertainty, real-source binding and publication remain separately withheld regardless of engineering status.
