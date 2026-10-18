# Browser 1.14.0 — clearer text measures and reusable filters

The report builder uses shared word-count rules, displays country expressions with their specific objects, and restores saved report filters when reopening a collection.

## Changes

- The meeting reader and descriptive reports share Unicode letter-and-number tokenization for word counts.
- Descriptive TF-IDF, similarity and dictionary themes remove narrowly recognized procedural sentences. A short procedural stop list also suppresses parliamentary formula terms. Their processing audit records removed sentences, suppressed terms and zero-vector exclusions from similarity pairs. Original text, source identities, word and segment totals, topic matching and exports remain intact. Clustering and NMF retain their existing inputs.
- Country expressions retain the extracted action and object. Condemning attacks on aid workers is displayed as condemnation of attacks rather than opposition to aid. Source links and attribution qualifications remain visible.
- Imported transcript JSON restores saved report filters when present, so users can inspect the original selection before rerunning it. Older collections without saved filters restore collection dates and scope, with all regions and all passages selected.

## Required validation

The reusable Pages release gate includes shared-tokenization and object-expression regression tests plus synthetic browser acceptance for saved filter restoration. Existing numerical, source, quick-reader and recovery checks remain required. Local engineering results and deployment runs must be reported separately after execution; this record does not claim new live-service acceptance or classifier accuracy.

No external generative AI endpoint is introduced. The reserved October 5–6 meetings remain outside this work. Original transcript text and analytical publication gates are preserved.

## Executed engineering checks

On October 18, 2026, 18 Node regression entry points passed. Edge browser acceptance passed 9 saved-filter checks, 13 recovery checks, 12 meeting-reader checks, 13 comparison checks and 8 script-free report checks. The fixed October 1 development collection passed the 27-check live browser harness with 92 passages from two meetings and no page errors.

The exact saved October 16 Sudan meeting was reopened locally without UN requests: dates and scope restored automatically, all 38 original segments remained, both report medians were 42, and attacks on aid workers were shown with their actual condemning action. Original source records and hashes were retained. This source replay is a targeted regression check, not independent classifier validation. Public build integrity and the artifact scanner passed with no findings. No reserved meeting transcripts were opened.
