# Ten-year issue workflow: product contract

Status: implementation contract; empirical model acceptance remains separate.

The reader supplies a date range, topic, and committee/body selection, then selects Generate report. No country or method selection, installation, source-file import, or coding is required for the normal path. All recorded countries appear automatically. The initial supported issue is humanitarian access and civilian protection.

The report opens with a source-linked issue overview and country-level opinion distribution, followed by a country/policy matrix, source coverage, the changing U.S. reference position, and automatic country trajectories. Unknown, qualified, conflicting, collective, and unsupported evidence remain visible. Repeated passages do not increase a country's weight. Votes and statements have separate estimands and denominators.

The selected dates define the current briefing. A separate rolling ten-year historical window ends on the report's frozen as-of date (default: today's America/New_York calendar date). Saved reports freeze inputs, source snapshot, ontology/extractor/model versions, selected artifacts, exclusions, and results. Reopening reproduces those results; refreshing is an explicit new report operation.

An authoritative, versioned historical store materializes source revisions and country evidence once. Incremental ingestion invalidates only dependent outputs. Read-only public bundles contain permitted fields and are cached in the browser. Private review material and reserved transcripts are never bundled. Backend provisioning must not be represented as operational until deployment is verified.

Model competition occurs only among eligible models for the same estimand and evaluation split. Temporal/source holdouts, calibration, interval coverage, stability, and runtime gates determine eligibility and selection. No accepted candidate yields an observed-evidence baseline with explicit gaps, never fabricated estimates. Assistant-provisional labels are not human-confirmed benchmark labels.

Failure states include unavailable source coverage, unsupported topic/context, stale snapshot, incomplete download, damaged bundle, missing U.S. evidence, insufficient model support, and cancelled computation. Each must leave an actionable visible state and preserve the last valid saved report.

Initial engineering budgets, to be measured rather than claimed: cached fixture report within 2 seconds; first fixture load within 10 seconds; cancellable long jobs; no blocked interaction lasting over 100 milliseconds where worker execution is available. Record reference device, fixture size, cold/warm state, and actual measurements before acceptance.

Workers own separate modules and tests. The integrator owns shared entrypoints, release metadata, mirror synchronization, merges and deployment. Source-bearing private inputs remain outside the public repositories. Contract changes require explicit versioning and integration review.
