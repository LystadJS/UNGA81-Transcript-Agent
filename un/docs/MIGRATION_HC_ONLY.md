# Migration — hierarchical clustering only

1. Keep v2.3 and its completed runs unchanged. Extract this complete release into a **new directory**. Do not patch only the new R files into an old release: accounting and validation also changed.
2. Restore authorized non-secret user settings. Keep the new R files and `config/hierarchical_policy.json`; do not transfer old runtime paths or latest-output pointers. Configuration `implementation: I2` and the I2 packet schema deliberately remain compatible; checkpoints additionally record `hierarchical_extension: D1-HC-1`.
3. The new actual package dependency is `cluster` for silhouette diagnostics. The clustering itself uses `stats::hclust` and Matrix. `cluster` availability is **not** PAM execution. Normal setup installs/freezes it with the other dependencies. Do not silently modify an old lockfile. Create a new dependency environment/lock in the new release, or review a deliberate lock update before restoring it. Retain the original lock with its old release.
4. Run the inherited suites and `tests/run_hierarchical_tests.R`; the Windows `Test-Workflow.ps1` now invokes all four. Inspect `audit/hierarchical/`, M07/M09 ledger rows, the audit figure and the five-section email. A successful replay is not live API acceptance.
5. Only after local acceptance, disable the old scheduled task and install a task pointing at this release. This download does not modify your computer, install a task, obtain an API key, or send anything.

## References and archives

The shipped active `history/`, `models/` and `cache/` directories are intentionally unseeded. Preserved validation examples have distinct names under `examples/`. Do not copy a replay reference into the observed-source namespace to make deployment easier.

To continue an already established **compatible observed-source** reference, transfer the whole trusted historical/model store after validating its hashes, namespaces and exact R/Matrix/tokenizer environment. Never weaken the environment gate. A changed environment/reference requires an explicit new namespace and a reconstructed comparable series; cross-platform byte identity is not assumed.

`hierarchical_only.R` reads a completed source run directly and leaves it untouched. It verifies the input manifest, M02 content, source identity and runtime before computing. It is the shortest path for auditing the same frozen feature artifact without running the other models.

## Scope reduction from the interrupted request

Only M07 is newly registered. All earlier incomplete v2.4/PAM working files are superseded by this separate hierarchical-only build from v2.3. M09 remains `not_implemented`. The original D1 registry is preserved for future work, but no unimplemented method is described as executed.
