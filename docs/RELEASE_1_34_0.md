# 1.34.0 — historical issue infrastructure

The source-free engineering milestone adds a maintainer SQLite ledger, bounded incremental ingestion/publication contracts, privacy-filtered historical bundles, a verified IndexedDB browser cache and a single-button archive report workspace. The existing saved-collection workflow remains available.

The new workspace uses materialized country observations rather than re-extracting unchanged transcripts. It separates humanitarian access and civilian protection by source context, counts countries once per question, retains recorded unknowns, and automatically displays each country's observed relationship to the changing U.S. reference. Official documents and votes do not enter statement-opinion counts. Unsupported topic qualifiers and conflicting source identities are withheld.

Saved archive reports freeze input dates/topic/body, as-of date, snapshot/version identities, exclusions, evidence and results. Reopening displays the frozen result without fetching new sources. Long jobs use a worker and can be cancelled; failed operations preserve the prior valid report.

The archive configuration is explicitly `not_provisioned`. No ten-year complete database, automatic remote feed, production scheduler, fitted political trajectory, calibrated uncertainty or empirical accuracy is claimed. Official catalog downloads were inaccessible; normalized adapters are not evidence of remote format coverage. Experimental categorical candidates remain outside the main observed report. The audit-only checkpoint and 37 reserved transcripts are untouched.

See [execution ledger](implementation-agenda/STATUS.md), [data contract](implementation-agenda/DATA_CONTRACT.md), [source feasibility](implementation-agenda/SOURCE_FEASIBILITY.md) and [evaluation contract](implementation-agenda/EVALUATION_CONTRACT.md) for completed engineering and remaining gates. Newly executed validation and publication results will be appended after CI/live checks.
