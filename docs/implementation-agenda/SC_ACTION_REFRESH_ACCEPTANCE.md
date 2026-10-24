# Private selected-action incremental refresh

The incremental workflow now has a separate private selected-voting-action lane, exposed through `runner.refresh_private_actions` and `python -m research.issue_history.refresh.sc_action_refresh_cli`. Completed, pinned source ingestion is a prerequisite. This lane neither imports sources nor exports public bundles.

## Accepted-state behavior

The existing durable cache reuses an unchanged source/review/proof/code/registry identity. A changed dependency rebuilds the derived action view. The workflow separately pins its implementation bytes and optional caller-declared source watermark. Repeating the same accepted identity leaves the accepted checkpoint pointer unchanged. Explicit refresh creates a new cache generation and accepted checkpoint.

Immutable accepted records and a separately atomic pointer preserve the last accepted state. Operational failure writes a sanitized advisory health result without replacing that pointer. A successful cache generation can precede a failed workflow acceptance: the old accepted artifact remains valid, while an unaccepted newer cache generation may remain on disk. A health-write failure after pointer acceptance does not undo a successful acceptance. Unsafe configuration or corrupt accepted state is rejected before workflow writes.

Cache and workflow state must occupy independently owned directories outside repository trees. Original inputs remain read-only. State records retain source/proof provenance; persisted health diagnostics omit source paths, voting records and raw exception messages. The minimum reserve remains 200 MiB plus the write margin. Database sidecars, aliases, ownership mismatch, changed artifacts and invalid proof identities are rejected.

Requested dates, observed selected-action dates and the nullable caller-declared snapshot watermark are separate fields. None establishes verified source freshness, archive completeness, a policy position or political agreement. Votes, statements and official documents remain separate.

## Validation

Seventeen new source-free refresh tests cover cache reuse, source/proof invalidation, workflow/watermark changes, failed attempts, interruption before pointer acceptance, tampered artifacts, advisory-health failure and private path/reserve safeguards. The combined local suite ran 122 Python tests successfully with one Windows hardlink test skipped; both existing Node draft/report checks passed. Linux repository checks and actual private acceptance are recorded in the execution ledger after publication.

No public browser assets changed. Website version 1.36.0 and prior browser save/reopen acceptance are unchanged; this engineering task does not claim a new browser deployment or populated opinion-archive acceptance.

Next: source-supported humanitarian issue bindings and separate statement-coverage review, preserving owner-label, public-data and fitted-model gates.
