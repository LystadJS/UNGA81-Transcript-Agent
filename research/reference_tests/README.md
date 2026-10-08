# Development nuisance-reference and held-out evaluation freeze

- `plan.json`: two prespecified conditional reference tests and nuisance strata.
- `evaluation_plan.json`: future one-shot held-out evaluation protocol, *not an authorization or evaluator*.
- `reference.py`: verifies saved development source/model/cache hashes; aggregates whole source segments; executes 999 blocked draws per test; Holm adjusts the two declared comparisons; builds a SHA256-sealed metadata-only future lock. No network and no holdout reader.
- `test_reference.py`: synthetic contracts, blocked reassignment invariants, fast-versus-direct computation, model-population failure paths, and protocol tamper checks.

Call `python -m unittest discover -s research/reference_tests -p test_reference.py`. The real-source CLI, inputs and interpretation are documented in [docs/NUISANCE_REFERENCE.md](../../docs/NUISANCE_REFERENCE.md). Retain text-bearing inputs/results as conversation checkpoint artifacts only; commit code and sanitized aggregate validation only. The sampled null shuffles do **not** prove global nonrandom diplomatic structure, policy alignment or a country's position.
