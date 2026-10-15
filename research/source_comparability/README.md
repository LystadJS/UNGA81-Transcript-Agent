# Historical source comparability — audit-only adapter

**Status:** engineering-only; no source-bearing empirical outputs, substantive fits, country-stance inference, or publication. Version `un.historical-source-audit.v1`, contract `1.1.0`, Node.js 22 (built-in modules only). Ownership: exclusively `research/source_comparability/**`.

## Contracts and source population

The JSON reader `readManifest(path)` accepts a `schema`, `contract_version`, `fixture_kind` (`synthetic` or `private_development`), `publication_eligible:false`, and three arrays:

- `frames[]`: `id`, `start_year`, `end_year`, `source_schema`, `source_hash_basis`, `source_sha256`, `selection_sha256`, and declared `meeting_design`, `genre`, `language`, `translation_modality`, `roster_definition`, `selection_design`, `sampling_unit`, `frame_unit`. Frame and selection SHA-256 retain their original hash bases. One source frame does not silently represent both historical eras.
- `receipts[]`: stable `document_id`, official verified `meeting_id`, `source_family_id`, `year`, `available` and `transcript_available` tri-state values, original `source_sha256` and `source_hash_basis`, canonical `text_sha256` and `text_hash_basis`, `source_verification`. Available original/document hashes must be correctly formatted. Bytes are never stored in the manifest; original-document verification is optional and conducted in memory. `duplicate_group` explicitly identifies an authorized duplicate-original family rather than silently counting duplicates.
- `observations[]`: stable `id`, `frame_id`, `document_id`, `meeting_id`, `source_family_id`, `speech_id` (may be null), recorded `country`, `year` and exact `event_date`, `source_status`, `missing_reason`, `attribution` and `attribution_receipt_id`, `actor_kind`, `outcome_status`, `inclusion_probability` with `probability_unit`, `speech_length`, `genre`, `language`, `translation_modality`, `text_sha256`. **Country is a recorded affiliation, not a verified human identity or a national position.** Absent / unverified rows must retain missing reasons and null unknown identities.

The accepted coordinator `un.parallel-source-inventory.v1` sidecar is **not** relabeled as an original-source audit manifest or `un.parallel-analysis.v1`. Call `auditInventory(sidecar)` on an independently accepted inventory; it runs the unchanged `docs/parallel-work/source-inventory-v1.cjs` validator and returns a **text-free, aggregate-only** 2008–2015 / 2016–2023 census with inherited source commitments and separate unknown/other-missing counts. It refuses unsupported legacy v1 binding. A country-year inventory alone cannot prove meeting→speech lineage, inclusion probabilities, source authenticity, or comparability. `auditInventory` therefore marks those gates NOT RUN or NOT IDENTIFIED.

## Audit-only return interface

`audit(manifest, {originals?, canonicalTexts?})` runs offline. The optional maps use `document_id => Buffer` for original source bytes and `document_id => string|Buffer` for canonical text. It returns an `evaluation_role:engineering_only`, `publication_eligible:false`, `inference_eligible:false` object containing totals, reason-specific counts, per-frame/year denominators, distributions by genre/language/translation, speech-length ranges and unique meeting/affiliation counts, within-frame metadata comparisons, cross-frame comparison states, and original/text validation statuses. Only **synthetic** fixtures emit ID-level problems and eligibility. Private fixtures return redacted aggregate diagnostics and never serialize supplied byte or text values.

### Eligibility matrix

| Decision | Meaning | Permitted claim |
| --- | --- | --- |
| `eligible_metadata:true` | Matching available document/transcript receipt, valid text digest and hash basis, meeting→speech→recorded-country→year linkage, attributable speech, observed outcome, positive declared inclusion probability at its actual sampling unit, valid length and descriptive strata | Source-manifest eligibility **conditional on inherited receipt evidence**, not original authentication or an inference license |
| `eligible_metadata:false` | One or more explicit missing, invalid, incompatible or unverified conditions; diagnostics retain reason and denominator | Exclusion/missingness **not** a zero diplomatic observation or failed fit |
| `supported` (within-frame only) | Two years have eligible metadata under the **same declared frame**, with compatible observed genre/language/translation sets | Descriptive metadata comparison only |
| `uncertain` | Distinct 2008–2015 / 2016–2023 source frames with no authenticated selection and measurement bridge, or insufficient within-frame coverage | No pooled inference or assumed cross-era comparability |
| `inadmissible` | Incompatible source schema/hash basis, meeting/genre frame or sampling design/target unit | Refuse the proposed direct comparison |

A first-stage meeting selection probability does **not** identify the probability that a country's speech text is observed. All outputs explicitly withhold MAR/MNAR identification, temporal dependence calibration, representation equivalence, model fitting, formal statistical inference, and publication. Original source hashes supplied by the caller are **not** publisher attestations. Receipts with no original bytes: `private_source_validation:NOT RUN`. The 37 reserved October 5–6, 2026 transcripts cannot enter a 2008–2023 frame and are never opened.

## Reproduce (offline; no additional dependencies)

```sh
node --version
node --check research/source_comparability/audit.cjs
node --test research/source_comparability/audit.test.cjs
node research/source_comparability/audit.cjs research/source_comparability/fixtures/synthetic-manifest.v1.json
```

The committed fixture is synthetic. Test arrays exercise malformed digests, duplicated identities, missing documents/transcripts/year/speech/attribution/outcomes, source/text hash mismatches, wrong hash basis, false source population overlap, zero/missing/out-of-range probabilities, incorrect probability units, structural non-risk, divergent designs, privacy and replay. No RNG, external API, external files, original PDF text, embeddings or 2026 holdout data are used. Private inputs are **not** included or made available by this code.

### Integration restrictions

- Input sources: original 2008–2015 and 2016–2023 populations are separately identified. Original archived source PDF/Harvard member identities and hashes remain under their W1/P2/W4 authoritative validators; this module never mutates or reads their private files.
- No edits to W1/W4 source adapters, `un.parallel-analysis.v1`, `un.parallel-source-inventory.v1`, D1 O1–O5, source records, Shiny/browser, release manifests, publication settings, or 37 withheld Oct 2026 transcripts.
- Upstream ownership and design records: `AGENTS.md`; `docs/parallel-work/{OWNERSHIP,PR_ACCEPTANCE,INTERCHANGE_V1,SOURCE_INVENTORY_COMPANION_V1}.md`; coordinator ledger of 15 October 2026; W4 independent source audit receipt. New historical data need authenticated original bytes, independently checked selection registers and translation/genre/roster/meeting sampling compatibility before inference is reassessed.
- No accepted `un.parallel-analysis.v1` export is produced: a source audit **cannot** fabricate fitted models or speech-level identities from country-year inventory. This is an explicitly audit-only read model for coordinator integration.
