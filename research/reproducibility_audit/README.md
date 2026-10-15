# Independent reproducibility audit (engineering only)

Run: `cd research/reproducibility_audit && python3 -m unittest -v test_audit.py`

Only synthetic fixtures and metadata are permitted. This standalone stdlib Python module does not open reserved transcripts, fit empirical models, change gates, or authorize publication.

## Scope and limitations

- Envelope checks implement a conservative **subset** of the normative interchange relational rules; this is not full JSON Schema validation. They reject missing IDs, duplicate IDs, invalid hashes/offsets, orphan/missing model results and invalid assignment states.
- `check_population` requires explicit same-basis source/selection hashes; a hash match alone is not proof of original-source authentication.
- `check_isolation` rejects shared observation, source family, parent or text hash; actual sealed evaluation identities must remain inaccessible unless explicitly authorized.
- `check_replay` checks receipt completeness and an output digest, not independent re-execution of a numerical method. Dependency/seed values must be independently attested by the caller.
- `scan_public` detects synthetic sentinels, common credential patterns and binary vector formats; it is not an exhaustive DLP scanner. Never run it on private source trees as a publication mechanism.
- No empirical release readiness is inferred from synthetic tests.

## Method inventory

| Method | Entry point | Runtime | Evidence |
| --- | --- | --- | --- |
| Interchange relational checks | audit.check_envelope | Python stdlib | synthetic unit tests |
| Identity leakage | audit.check_isolation | Python stdlib | synthetic unit tests |
| Population compatibility | audit.check_population | Python stdlib | synthetic unit tests |
| Replay receipt verification | audit.check_replay | Python stdlib | synthetic unit tests |
| Public artifact sentinel scan | audit.scan_public | Python stdlib | synthetic unit tests |
| QA status report | audit.qa_summary | Python stdlib | synthetic unit tests |

## Release-readiness matrix

| Gate | Status | Reason |
| --- | --- | --- |
| Engineering acceptance | NOT RUN | CI and full repository regression not executed |
| Statistical calibration | NOT RUN | No independently calibrated empirical tests |
| Source eligibility | NOT RUN | No authorized private original-source authentication |
| Human review | NOT RUN | No owner decision made in this audit |
| Publication authorization | FAIL | Explicitly withheld; engineering-only branch |

## Coordinator review priorities

1. Preserve draft/nonmerge status for PR #68 until temporal-correlation recovery and holdout calibration are independently demonstrated.
2. Require actual checkpoint execution, dependency locks and comparison controls before scientific acceptance of PR #66.
3. Require nuisance-aware simulation sweeps and independently seeded calibration for PR #67.
4. Require current-head Node/Chromium CI and accepted interchange relational checks for PR #69.
5. Re-evaluate PR #56 separately for public deployment authorization even if engineering CI passed on its earlier head.

All PR findings above are based on PR descriptions, not independent code execution. No claim of private-source or full CI verification.
