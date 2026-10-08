# Backward-compatible source-inventory companion — `un.parallel-source-inventory.v1`

**Coordinator specification, 8 October 2026.** Experimental source-aware engineering contract. Adds a distinct text-free inventory *document*, not a required field or changed enum in `un.parallel-analysis.v1` 1.0.0. The existing structural schema, `INTERCHANGE_V1.md`, source and D1 gates stay frozen.

## Why a separate sidecar

The W4 2016–2023 candidate panel contains **792 country×year cells**, of which **523** have original-UN-PV-corroborated speech texts and **269** have not been source-verified. Those 269 records are **unverified**, not verified absences, explicit zero mentions, failed numerical fits, or independent speeches. Many have no verified exact event date, meeting ID, text SHA-256 or original-source SHA-256. Legacy `un.parallel-analysis.v1` requires a date string and does not admit `source_status:unverified`. Calling them `unavailable`, inventing dates, adding unknown enum values, or silently changing the original population denominator would break provenance and backward compatibility.

**Contract choice:** Pair an unchanged, eligible-only `un.parallel-analysis.v1` envelope **where one can actually be generated from an already-approved upstream schema** with a separate `un.parallel-source-inventory.v1` companion. Old v1 readers continue to process the unchanged 523 eligible observations *as a restricted conditional cohort*; they **must not** claim that this is the full 792-cell country-year universe. New readers show the sidecar's real universe and its 269 unverified inventory cells separately. The source and selection hashes, period coverage, original meeting identities and country-year keys are independently validated before allowing the documents to be bound.

An unapproved historical upstream schema is **not relabelled** as an accepted v1 source type. In the actual W4 P2 pilot the `un.p2.original-pv-reconciled.v1` source schema is not in the coordinator legacy source enum: the sidecar is valid *standalone*, with `legacy_v1_binding.mode="withheld"` and a concrete reason. Binding will require a separately approved W1/P2 provenance adapter and a schema migration. An old v1 consumer must **never** interpret unsupported P2 as `un.passage-corpus.v1` merely to load the file.

## Schema and guards

The machine-readable schema is `source-inventory-v1.schema.json`; the read-only adapter is `source-inventory-v1.cjs`. A row includes:

- Stable observation ID and period ID; calendar **year** independently of nullable `event_date`.
- Explicit recorded actor unit and genre; source status `available / unverified / unavailable / failed / inventory_failed / empty_transcript / excluded_language`.
- Missing reason, actual original meeting and source-family IDs when known, exact original bytes and UTF-8 text hashes when known, source verification basis, and attribution review status.
- **No speech text, speaker name, private source URL, embedding, fitted coordinate, topic assignment or stance inference**. The adapter whitelists fields; a forged raw `text` field is rejected.
- Original upstream schema and hash basis, source SHA-256 and original selection SHA-256. An inventory SHA-256 binds the entire ordered source-state ledger.

A verified **available** row must have real event date, original meeting and source-family identifiers, SHA-256 for both original source and text, and `full_original_verified` provenance (or a deliberately synthetic fixture). An `unverified` row may have truly null date/meeting/hashes and must record a reason; it cannot be promoted to an observed zero or verified human speaker. The adapter enforces unique country×year keys for the country-year frame, date-in-period, nonoverlapping periods, meeting-to-year/source consistency, mutually exhaustive period/status counts, split and hash-basis consistency, and refusal of the frozen October 5–6, 2026 dates.

### Legacy binding rules

`legacy_v1_binding.mode="withheld"` (default) ensures no legacy interoperability claim. `verified_subset_projection` requires an **actual, unchanged**, 1.0.0, unpublished `un.parallel-analysis.v1` envelope with the **same approved source schema, original upstream source hash and hash basis**, the exact same available observation ID/text-hash/meeting/date population, and matching original selection SHA. A binding cannot be authenticated merely by setting a schema string or a `legacy_eligible` count. In particular:

1. All 523 *available* source-verified observations must be present in the legacy eligible cohort; the 269 unverified cells may exist only in the separate inventory.
2. No invented source dates or fabricated eligibility counts; a legacy consumer sees 523 and cannot silently claim to have analyzed the full 792.
3. Added source statuses and fields are not inserted into the frozen legacy schema. No browser/worker is automatically upgraded or published by this new companion.

## Statistical effect: descriptive, not inferential

The **2016–2019 frozen TF–IDF/LSA64 reference** was fitted on 252 eligible observations; 2020–2023's 271 eligible observations were only projected. The source-verified frame spans 55 original UN meetings across 8 years (4 years per comparison era), with 99 country affiliation trajectories crossing meeting/year blocks. In the verified actor–meeting graph, the source-group/actor closure forms **one connected component**. Meeting groups nest inside years; years are not replicated iid observations of a sampled population.

The sidecar preserves those denominators and source group IDs. It does **not** make meeting, country or year observations independent. The separate [dependence audit](W4_MEETING_YEAR_DEPENDENCE_2026-10-08.md) applies conditional leave-one-meeting, leave-one-year and paired-year deletion to the **pinned, unchanged 64-dimensional feature basis**. It reports all attempted/successful/excluded assessments, matched-actor counts, source dependence and sensitivity ranges. These are not bootstrapped confidence intervals, and no valid year-cluster asymptotic variance is claimed from 4 years per era. The original W4 paired-source-family bootstrap remains **withheld with zero attempted draws**.

## Release, ownership and replay

Test the synthetic source-inventory contract with `node docs/parallel-work/test-source-inventory-v1.cjs`, and the untouched legacy interchange via `node docs/parallel-work/validate-contract.cjs`. `source-inventory-v1.cjs` is pure, source-text-free and has no network or browser loader. No current D1 methods, site, W1 or W4 worker-owned files, original hashes, held-out lock or review decisions are changed in this coordinator PR.

The private 792-row companion and 79 deletion checks can be distributed only via authorized private storage, together with code and a redacted aggregate receipt. **Neither the source-linked rows nor fitted 523×64 embeddings belong in this public repository.** The 37 reserved October 5–6 meeting transcripts remain unopened. Scientific inference, cross-country generalization and publication require separately demonstrated sampling/dependence assumptions, representation robustness, attribution and release acceptance.

**Backward compatibility is a structural property of the companion approach, not permission to omit unknowns from research conclusions.**