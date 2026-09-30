# I7 acceptance - 29 September 2026

Freshly executed on Windows with R 4.5.3 and an isolated QA library:

- **55/55** new-method and integration-boundary checks.
- **43/43** existing research-kernel regression checks.
- **31/31** reviewed-dataset tool checks.
- **129 checks, zero failures.**
- All six research R files parsed.
- New M20 CLI output saved; SHA-256 independently verified.
- Reusing the same output name was rejected as expected.

Fixtures are synthetic. No private inputs or reviewed labels were added. Tests
cover calibration partitions, held-out token evaluation independence, metadata
and vocabulary identity, passage descriptors/exemplars, forward-only filtering,
future-information rejection, model serialization, planted graph communities,
first-event risk constraints, Bayesian effect recovery and sampler diagnostics.

M42's synthetic four-chain fit passed R-hat < 1.01 and bulk/tail ESS >= 400 for
all parameters. This does not establish real-data calibration, causal diffusion,
prior robustness or out-of-sample performance. The group prior scale is fixed.

STM reports its documented K=2 scaling-model advisory on the two-topic fixture.
The known fractional-success warning from binomial EM weighting is captured in
the state-model result; other state-fitting warnings abort. Locale startup
warnings are retained in the logs; trailing whitespace is normalized. Final tests found no numerical failures.

The daily pipeline and files under `un/` were not changed. No new daily replay,
Shiny browser acceptance or Outlook acceptance is claimed. The 12 daily adapters
and O1-O5 publication gates retain their previous behavior. I6 evidence in the
parent directory is historical; this directory records the new executions.

See [method scope and limitations](../../I7.md), `summary.json`, `tests.csv`,
`regression.csv`, the execution logs and `runtime.log` for evidence. M16, M26 and
M38 remain unimplemented; the project is not a fully implemented 42-method system.
