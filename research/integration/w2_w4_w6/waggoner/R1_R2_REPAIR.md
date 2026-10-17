# R1/R2 repair — 15 October 2026

The original independently reviewed candidate is commit `32112ff5793c1be763db709aa3ef536fb409428a`. Its failure evidence remains in PR82 discussion and coordinator PR87/run `38767398755`: four independent probes passed, two failed and one errored in each execution mode. Do not rewrite those historical receipts or turn failures into expected passes.

## R1

The R synthetic table reader now declares every input column as character. Only `v0` through the final declared feature are explicitly parsed as finite bounded decimal/scientific numbers. Numeric-looking identifiers, leading zeros and literal `NA` remain strings; empty feature fields remain missing. Malformed numerical text, nonfinite values, overflow, out-of-bound values and observed rows without complete vectors are rejected.

Source grouping, equal-meeting/equal-genre weights and all numerical formulae/tolerances are unchanged. The original `01` versus `1` reproduction must yield weights 0.25/0.25/0.5 and a distance of 3.0, not 2.33333333333333. The `001`/`002` period test is retained.

## R2

Source identifiers retain their original 160-character bound. A dedicated `country_period_id` schema type requires three uppercase country-code letters, `/`, and a valid unchanged source token, with an exact maximum of 164 characters. Only profile/comparison IDs and transition comparison references use this derived type. No truncation, remapping or universal token-bound increase is applied. This is a correction to an unmerged research-side schema, not a change to an official interchange or frozen scientific gate.

## Verification and scope

Eight new test methods cover the original reproductions, scientific-notation and large numeric-looking IDs, literal/boolean-looking period IDs, invalid numerical input, missingness, 1/156/157/159/160-character positive boundaries and 161-character source rejection, Python/Node replay and independent Draft 2020-12 validation. `run_tests.suite()` retains the original 32 tests and adds these eight. `--require-complete` continues to fail on any skipped test.

The original independent coordinator test methods and mathematical expectations must remain unchanged when repinning PR87's candidate and blob identities. Local repair probes and the 26-panel R supplement passed before commit; hosted exact-head and effective-tree acceptance remain pending at this commit and must be recorded from actual execution.

No publication, merge, empirical input, reserved transcript, fitted representation, baseline policy, weighting policy, source ledger or scientific threshold is changed. Mandatory-R workflow changes belong only in the separate coordinator review PR.
