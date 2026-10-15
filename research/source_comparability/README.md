# Historical comparability audit (engineering only)

Run: `node --test research/source_comparability/audit.test.cjs`

CLI: `node research/source_comparability/audit.cjs /path/to/accepted-manifest.json`

Input contract: `un.historical-source-audit.v1`. The JSON root contains `frames[]`, `receipts[]` and `observations[]`. Frames require stable `id`, declared `year`, `meeting_design`, `genre`, `language`, `translation_modality`, `roster_definition`, `selection_design`. Receipts require `document_id`, `meeting_id`, `year`, `available`, `transcript_available`, `sha256` (original bytes) and `text_sha256` (canonical text). Observations require `id`, `frame_id`, `document_id`, `meeting_id`, `speech_id`, `country`, `year`, `attribution`, `outcome_available`, `inclusion_probability`, `speech_length`, `text_sha256`.

**Audit-only interface:** `audit(manifest,{originals?})` returns `totals`, `counts`, `problems`, per-observation `eligibility`, pairwise `comparisons`, `private_source_validation`, and `publication_eligible:false`. Original bytes are optional in-memory buffers keyed by document ID; absent originals produce `NOT RUN`. No private bytes are serialized. Hash bases are not interchangeable.

**Eligibility matrix:** eligible means all required identity, receipt, transcript, lineage, year, attribution, outcome, probability and text-receipt checks pass. Missing documents/transcripts and missing outcomes are separate classifications. The audit does not certify actual speaker identity or source authenticity without independently authenticated receipts. Cross-frame comparisons are inadmissible on unharmonized design differences, uncertain without common observed documents and speech-length evidence, otherwise provisionally supported only at the metadata level.

**Important limits:** 2008–2015 and 2016–2023 are distinct source populations by default. This is an intentionally conservative metadata adapter, not a harmonization estimator. Probability values are checked for range, not independently reconstructed from a verified selection register. Genre/language/translation/roster/design comparisons use declared frame labels; speech-length ranges and observed document overlap are descriptive. No model fitting, private corpus extraction, or publication authorization. Do not open the 37 reserved October 2026 transcripts. No existing W1/W4 trees, frozen checksums or shared schemas are modified.
