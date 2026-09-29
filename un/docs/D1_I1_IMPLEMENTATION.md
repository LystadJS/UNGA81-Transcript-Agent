> Historical I1 document retained for provenance. For the current release, read D1_I2_IMPLEMENTATION.md and MIGRATION_D1_I2.md.

# D1-I1 implementation record

**Release 2.2.0-d1-i1 · foundation milestone**

## Completed

| Component | Implemented behavior |
|---|---|
| Historical statement store | Content-addressed RDS statements/passages, exact source byte archives, separate event and acquisition clocks, ordered hash-chained commits, version/reversion history, as-of queries and read-only verification |
| Labels | Separate immutable automatic/inherited label objects linked to contributing statements; codebook versions preserved; no gold promotion |
| Method accounting | All 42 D1 registrations and all 133 required gates evaluated; actual dependency availability, execution intervals, stage, cache/artifact identity and non-delivery reasons retained |
| M01 | Source-linked lexical candidate retrieval on the active codebook, with exact sentence evidence; non-hit means unresolved; no trained classifier or publication claim |
| Publication | Exactly O1–O5; unavailable reason/HTML/plaintext parity; no numerical payload or model promotion through config flags; no released producer ships here |
| Outlook | Existing full-width styling, inline seal, UTF-8, CRLF, unsent MIME and region-first readouts retained; audit charts excluded from reader-facing body |
| Rebuild | Frozen packets and snapshot retained; completed archived output rebuild does not mutate the active historical store or call external services |

## What is not completed

**41 analytical method adapters are not implemented.** Their prerequisites are assessed, but that is not execution, model fitting, validation or calibration. D1-required gold-label ingestion, homogeneous historical semantic recoding, feature/reference store, PCA/PCoA, embeddings, clustering, topic models, stance classifiers, movement, `driftmapR`, networks, forecasts and diffusion remain later stages.

The inherited narrative-summary/model-review route is not one of the 41 trained analytical models. It remains the existing source-summary workflow, and its labels do not become human gold. A two-model-pass result is not a released statistical classifier. All five analytical slots therefore remain unavailable in this milestone. The four fixed-topic names and available-text denominator remain visible; inherited/provisional prevalence is audit-only.

`targets` orchestration, DuckDB and Parquet export are not implemented in this foundation. The explicit base-R registry runs sequentially. D1 permits retaining RDS/CSV initially; the store records a backend/schema version and caps history queries. No large-corpus memory benchmark or GPU benchmark is claimed. Installation does not load every package in the design registry.

## Registry and gates

`config/method_registry.csv` is the unchanged D1 design specification. Runtime availability appears in each run's ledger; its design-only status column is not rewritten to imply implementation. The loader verifies this registry against the preserved D1 copy. To change its prerequisites, create a reviewed registry revision rather than weakening them in place.

The terminal states are `executed`, `reused`, `not_due`, `failed`, `withheld_quality`, `not_implemented`, and explicit data/labels/history/dependency/authorization/resources/version/supported-regime blockers. An unimplemented method remains `not_implemented` even when it also lacks data; the independent gate ledger retains every blocker. Actual stage and fit status distinguish an M01 transform from training.

M01 cache reuse requires an exact input/active-codebook/code/R-version fingerprint, hash-verified bytes, valid availability time, and renewed source-evidence validation. A malformed or corrupt cache yields an explicit failure instead of a silent fallback. Failed implemented branches do not erase the other method registrations. Source-preparation failures produce a 42-row no-delivery ledger and no successful email claim; incremental method rows remain available after interruption.

## Evidence-backed publication boundary

The five packets carry source snapshot, source/analysis cutoffs, definition, model/release status, eight quality-check records and actual artifact references. A sixth slot, reorder, disguised title, future cutoff, stale numeric payload, forecast, unregistered image or fabricated ready model is rejected. This release deliberately has an empty ready-producer registry. Quality flags alone cannot promote a result. Later producers require a code change, exact artifact/validation contract and independent tests—not just a user-edited Boolean.

Unavailable does not mean no development. The O2/O4/O5 reasons distinguish missing comparable history from no validated method. No coordinates, rhetorical distances, network links, confidence intervals, country evaluations or forecasts are fabricated to fill the five slots.

## Changed interfaces

`R/07_history.R`, `R/09_method_registry.R`, `R/15_publish_packets.R` and `R/16_analytics_pipeline.R` implement the foundation. `history_tool.R` provides read-only queries and explicit stale-lock recovery. Collection preserves ungrouped metadata; `prepare_run()` freezes the inputs; `prepare_analytics()` commits history and runs accounting; the renderer consumes packets only; `validate_output()` validates both the old country/MIME invariants and the new D1 invariants.

The original three standalone `Figure_*.R` scripts are still executed individually, but through an explicit audit-only allowlist. A failed audit chart is logged and does not prevent the remaining qualified draft. Models cannot make an extra figure inline by dropping a file into a directory.

## Acceptance boundary

See `validation/FINAL_VALIDATION.md` for executed R tests and archived-reference checks. Live UN/OpenAI requests, production package-backed operation, Windows Task Scheduler/DPAPI and native Outlook are not established by Linux offline tests. No existing local installation or GitHub repository has been modified, no key included, and no message sent.

## Next implementation milestone

Implement versioned current-day representations and primary-task release contracts. Start with a frozen TF-IDF feature adapter, PCA/PCoA diagnostics and source-bound issue review; add valid training/gold-label intake separately. Do not enable an inline map or classifier until its publication evidence exists. Preserve this I1 release for its archived runs.
