# Integration map to the inspected v2.1 R workflow

**Status:** proposed changes, not applied. Exact source-file hashes are recorded in `validation/source_provenance.json`.

| Current file / interface | Preserve | Required implementation change |
|---|---|---|
| `run_daily.R` | Source modes, America/New_York reporting dates, immutable run IDs, lock ownership, explicit failures, no sending | Add a registry-driven analytical phase after source/evidence preparation. The current wildcard execution of every `Figure_*.R` must not turn every backend chart into an email requirement. Execute display builders from the five-slot manifest instead. |
| `R/01_sources.R` | Source bytes, hash checks, collection exclusions and exact country attribution | Retain statement/meeting/agenda/genre IDs, event time and first-seen time before `group_countries()` combines records. Build stable passage IDs and near-duplicate groups without changing original text. |
| `R/02_analysis.R` | Exact evidence links, current full-text issue/summarization route, distinct failed/extractive/model-reviewed states | Add task schemas for proposition-specific stance and released classifier outputs. Gold-label storage must be separate from automatic review results. Keep text instructions in retrieved documents inert. |
| `R/03_pipeline.R::prepare_run()` | Immutable source/audit/checkpoint generation and regional ordering | Add a historical observation store and analytic snapshots with version compatibility, source availability times and genre/issue strata. Archive the complete all-method daily summary, with subtask stage ledgers where needed. |
| `R/06_policy.R` | `FIXED_ISSUE_IDS`, existing `REGION_ORDER`, `order_country_readouts()` | Keep fixed-topic and regional ordering. Add the exact O1–O5 publication policy without changing the underlying administrative regions. Preserve the warning about mixed-version replay data. |
| `R/04_email.R::build_email()` | Approved masthead/table styling, native-R MIME helper, `X-Unsent`, CID embedding, escaped text, country metadata and summaries | Consume `report_packets` rather than arbitrary model or figure outputs. Replace the legacy three-figure analytic block with O1–O5. Remove the separate selected-requests section or fold its evidence into an allowed slot/country readout. Generate the executive takeaway solely from accepted evidence. |
| `R/04_email.R::FIGURE_FILES` and MIME images | Inline PNG mechanism and 840-pixel cap | Replace hard-coded three-figure enumeration with an allowlisted image manifest containing only the five-slot assets that actually exist. Retain audit-only charts separately. Do not require exactly four total images on every nonempty day. |
| `R/05_validate.R::validate_output()` | MIME/UTF-8/CRLF/table/CID/address checks, country/topic accounting, regional order | Validate exact five analytical sections, publication-gate evidence, variable image count (seal plus eligible allowlisted assets), unavailable-slot notes, and plaintext parity. Retain source and issue reconciliation checks even when the issue bars are no longer inline. |
| `R/05_validate.R::finalize_run()` | Content hashes, per-date outputs, late-source revisions, no-send status | Include all-model execution/reuse/blocker accounting and publication-decision traces before committing the draft. A failed research branch must not claim success or erase the remaining validated output. |
| `rebuild.R` | Offline archived replay contract | Expand the frozen checkpoint to include analytics policy, reference features, model versions, codebook/label versions, model artifacts or immutable hashes, report packets, plot inputs and trained-reference cutoffs. No new API calls when reproducing an archive. |
| Standalone `R/Figure_*.R` files | Individual scripts and READMEs | Retain the original three as audit-only. Add distinct standalone builders for the country map, optional movement view and optional network-change view. Table outputs O1/O2 need no extra plot. |
| Windows scripts | Local secrets, scheduling and separate setup/tests | Separate daily inference from weekly/monthly candidate fitting. Do not overwrite a task automatically during migration. Pin newly installed dependencies after actual Windows acceptance. |

## Proposed new modules

`R/07_history.R`, `R/08_features.R`, `R/09_method_registry.R`, `R/10_supervised.R`, `R/11_topics_clusters.R`, `R/12_movement.R`, `R/13_networks.R`, `R/14_forecast_diffusion.R`, `R/15_publish_packets.R`.

These are planned filenames, not files shipped as implemented models in D1. The first functional milestone is an orchestrator and publication router with truthful blocked states; each subsequent method is independently implemented and validated behind its registered adapter.

## Migration invariants

- The existing v2.1 release and completed archives stay byte-for-byte unchanged.
- A new design release is not installed by copying only `build_email()` into the old directory.
- A historical observation derived under mixed legacy codes is not automatically pooled with new semantic codes.
- Source backfills revise observation vintages but do not leak into historical as-of forecasts.
- Current country readouts remain intact even when advanced analytical slots are unavailable.
- Neither the new model layer nor the report renderer has a send-email capability.
