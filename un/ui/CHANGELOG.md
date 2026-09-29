# Changelog

## 0.1.0 — 28 September 2026

New separate Shiny application source and native-R reference runner. Added editable topic tags, explicit include/exclude definitions, scoped immutable requests, bounded TXT/ZIP/CSV intake, quote-backed literal candidates, full-corpus research methods, no-release five-slot draft rendering, unsent EML/HTML/PDF exports, evidence/provenance, Windows launchers, synthetic tests, and an explicitly blocked D1 boundary.

Compatibility note: this is **not** a modification of the 2.5.0 D1-I4 checkpoint. It does not include that checkpoint, its historical store, inherited country summaries, models, or an implemented adapter. No previous version files were changed.

## 0.2.0-d1-i4 — 28 September 2026

- Added pinned `interfaces/shiny_v1.R` integration with the 2.5.0 D1-I4 checkpoint.
- Added arbitrary user tracked issues without mutating the legacy four-topic codebook.
- Preserved full-corpus D1 analytics and the exactly-five-output publication firewall.
- Added isolated per-request D1 history/cache/reference namespaces.
- Added D1 country-readout HTML/EML patching for user tracked-issue rows while retaining `NOT READY` semantics for unreleased O1 classification.
- Added adapter regression and full replay acceptance tests.
