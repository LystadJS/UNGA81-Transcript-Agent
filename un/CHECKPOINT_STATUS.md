> Historical D1-I4 milestone. Current I5 implementation and acceptance:
> [I5 extension](../docs/I5.md), [validation](validation/i5/README.md).

# Checkpoint status — 2.5.0 D1-I4

## Frozen milestone

**Implemented analytical adapters:** M01, M02, M05, M06, M07, M09.  
**Not implemented:** 36 of the 42 D1 registrations.  
**Reader-facing analytical outputs:** exactly O1–O5; no clustering output is reader-facing.  
**Daily language:** R-native. Python is not required by the shipped workflow.

## New in this checkpoint

- M09 PAM / k-medoids on frozen M02 TF-IDF geometry.
- Candidate k=2..6 selection with size constraints.
- Full-data medoids and assignments.
- 100 fixed-seed roster-deletion stability replicates per k.
- ARI, clusterwise Jaccard/evaluability, coassignment and medoid-retention diagnostics.
- Frozen PAM policy and tamper checks.
- Standalone PAM replay and audit figure.
- Cross-method M07 vs M09 audit on the same 39-country lexical space.

## Acceptance state

All five R engineering/regression suites pass: **371 tests, zero failures**. Source-backed M07 and M09 outputs both fail their frozen release screens and remain audit-only. No release gate was weakened after observing the results.

Next analytical development should proceed from this checkpoint rather than an earlier partial PAM branch.
