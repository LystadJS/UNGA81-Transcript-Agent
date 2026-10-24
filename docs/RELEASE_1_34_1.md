# 1.34.1 — verified vote ingestion and report reuse

This update adds adapters for the inspected official General Assembly v6 and Security Council v7 CSV formats. Country identities use exact registry code joins while preserving the historical source name and code. Adopted decisions remain separate from resolutions; resolution subparts retain their original identity. Non-voting and adoption without an individual vote never become affirmative ballots or inferred absence.

The original files remain in private staging outside this repository. The GA CSV's decompressed SHA-256 is `8c2e1c6aaf427c685835e7fdf74833375ed711a28d1ee9e393163903e99e11a5`. The SC CSV's SHA-256 is `c73e8d7b61ee1323e8a48af2fcbb5b8d14ab05619030862793a79ecfb0cbb5c2`. Source citations, versions, limitations and reconciliation records are documented in the implementation agenda.

The private database contains 7,740 SC rows from 516 adopted resolutions in the rolling window, reconciled against published totals. The full GA input window reconciles 205,738 rows across 1,066 resolution/decision groups against the publisher totals. The database has accepted 98,000 of these rows with zero quarantine so far; the remaining 107,738 rows are not imported. Durable cursors preserve the exact source, adapter, country registry and requested window. These are raw voting records, not materialized humanitarian policy opinions.

The import reached local storage capacity. Only our superseded reproducible scratch backup was removed. The GA download was compressed and its decompressed hash verified before replacing the original. The runner now stops before consuming a 200 MiB free-space reserve plus its next-batch margin. Bulk continuation requires at least 1 GiB free; no user collections were deleted.

The browser now caches completed reports using the full snapshot, inputs and method versions, verifies cached results before reuse and discards corrupted entries. Archive controls use the available width, and archive charts/tables inherit the report layout. Saving and reopening continue to preserve the frozen result rather than silently updating it.

The public archive remains unprovisioned. There is no complete ten-year statement database or accepted fitted political trajectory. Two primary-source resolution reviews remain provisional and private; a full-resolution vote does not establish agreement with every individual policy provision. Model acceptance still requires appropriate empirical evidence.

Validation: Node engine, cache-integrity, model, report and experimental-candidate checks passed locally. All 38 Python ingestion/store/assessment checks passed locally. Actual-browser CI and publication are recorded after final integration checks. No reserved transcripts or private source artifacts are included in the release.
