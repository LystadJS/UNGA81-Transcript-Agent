# Development nuisance-reference and held-out evaluation freeze

- `plan.json`: two prespecified conditional reference tests and nuisance strata.
- `evaluation_plan.json`: future one-shot held-out evaluation protocol, *not an authorization or evaluator*.
- `development-reference.json` and `evaluation-lock.json`: checked-in text-free development aggregate and sealed metadata-only held-out contract, with hashes verified by unit tests.
- `reference.py`: verifies saved development source/model/cache hashes; aggregates whole source segments; executes 999 blocked draws per test; Holm adjusts the two declared comparisons; builds a SHA256-sealed metadata-only future lock. No network and no holdout reader.
- `test_reference.py`: synthetic contracts, blocked reassignment invariants, fast-versus-direct computation, model-population failure paths, and protocol tamper checks.

Call `python -m unittest discover -s research/reference_tests -p test_reference.py`. The real-source CLI, inputs and interpretation are documented in [docs/NUISANCE_REFERENCE.md](../../docs/NUISANCE_REFERENCE.md). Retain text-bearing inputs/results as conversation checkpoint artifacts only; commit code and sanitized aggregate validation only. The sampled null shuffles do **not** prove global nonrandom diplomatic structure, policy alignment or a country's position.

## Additional development controls (8 October 2026)

`negative_controls.py` uses **only** pre-existing source metadata to generate deterministic nuisance-only vectors. `mask_sensitivity.py` masks registry-backed country names in copied development text, re-encodes with the pinned offline MiniLM checkpoint and reuses the frozen lexical and semantic transforms/centroids. `holdout_dryrun.py` has a **synthetic-only input schema** and exercises positive, negative, coverage-failure and frozen-transform cases. `verify_controls.py` reconciles the resulting local artifacts, original passage identities and all 37 fake meeting statuses; `test_controls.py` covers tampering and unwanted real-source input. See [development-control findings](../../docs/DEVELOPMENT_CONTROLS.md).

The immutable `evaluation-lock.json`, `reference.py`, `evaluation_plan.json` and `plan.json` **are not modified** by these experiments. The new CLI does not expose a real holdout-collection flag or accept actual held-out text. Do not commit real source passages, masks, vectors or review ledgers into the public repository; leave them in the private result package. All results are development diagnostics or explicit simulations, not held-out evidence or authorization to examine the reserved period.
