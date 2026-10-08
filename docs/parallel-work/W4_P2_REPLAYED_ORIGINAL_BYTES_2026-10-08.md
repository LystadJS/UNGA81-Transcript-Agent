# W4 P2 — independent original-PV byte and text replay

**Execution:** 8 October 2026, on the owner's newly uploaded two private P2 archives. **Decision:** original UN-PV PDF byte identity, pages, source symbols, and whole-document text extraction PASS for the full 63-document historical subset. Historical real W1/W4 model fitting and public inference remain **WITHHELD**.

## Newly executed validation, distinct from prior aggregate-only review

The original 63-file UN General Assembly verbatim-meeting ZIP and separate analytical/reconciliation ZIP were made available as actual private bytes. Both archive CRCs, directory paths, symlink restrictions, and file inventories passed. The full original-PV acquisition manifests stored separately in the two archives agreed byte-for-byte.

| Independent fresh check | Result |
| --- | --- |
| Original 2016–2024 A/session/PV PDFs and SHA-256 | **63/63 PASS** |
| Declared original PDF byte length | **63/63 PASS** |
| Independent PDF page count | **63/63 PASS**; **3,370 pages** |
| Original-PV symbol printed on first page | **63/63 PASS** |
| Complete re-extracted official meeting text SHA-256 and length | **63/63 PASS** |
| Source manifest consistency across both provided archives | **63/63 PASS** |
| Recorded official PDF bytes | **53,218,960** |
| New byte/source/text discrepancies | **0** |

The PDF extraction uses original whole-meeting documents, including all pages, and matches the earlier entire-PV text digest. It does not mean a particular individual speech or person has been independently authenticated. **The UN did not supply a publisher-signed reference checksum**; integrity is established relative to the independent, user-supplied prior acquisition and extraction manifests, with exact first-page official document symbols.

## Private analytical ledger source links and selection

- All **985** country-year source rows linked to an acquired UN original-PV now reconcile to a freshly byte-validated exact-PDF SHA-256 and page count.
- The archived full-speech correspondence score fields, seven-token-shingle/decile and opening/ending thresholds reproduce the source-classification totals: **840 strong matches in 2016–2023**, **94 partial/variant and 50 insufficient in 2024**, and **one Harvard text omission**; **752** other original-PV candidates remain unacquired.
- **Important separate limit:** the new uploads do **not** contain the *original Harvard v14 individual country-speech text bytes*. Thus, the 840 recorded overlap scores were checked for correct threshold classifications and original-source identity, **not freshly recalculated from the Harvard speech texts**. Full two-sided Harvard-original/PV text matching still requires that separate archive.
- The original complete **99-affiliation × 8-year = 792** country-year private inventory was rechecked. **523** cells have strong prior speech/PV correspondence, **269** are explicitly unverified, never counted as no speech. The **252** prior-era and **271** later-era source-corroborated cells each match the correct original-PV digest.
- The selection SHA-256 was **independently recomputed** from all 523 sorted (year, recorded affiliation, original-PV PDF digest, Harvard corpus text digest) tuples: `3ebec834635e4d493e8035aeede3321efb951aa22f2f61d81f6ac7a0f65a4c89`. There are **55** original PV meeting/source groups, so 523 country-year rows are not independent sampling units.
- All **96** recorded same-year wrong-PV negative controls used different acquired official meetings. None passed the strong 90% threshold; the maximum saved wrong-document overlap is **2.793%**. This checks document specificity, **not** a source-group statistical null or diplomatic significance.
- The 24 priority flags remain source-provisional, with six unresolved modality/validation gates. **No human speaker identities were independently authenticated**; no gold label is inferred from country, name similarity, or translation.

## Reproducibility and privacy

The complete re-run was executed privately with a reproducible offline Python verifier (PyMuPDF, Python standard library). The resulting **private** download package includes the 63-row original-PV hash/size/page/text ledger, discrepancy ledger, validation receipt, source-free summary and replay code. Neither input ZIP nor the private detailed rows were committed to GitHub. The new aggregate companion [JSON](W4_P2_REPLAYED_ORIGINAL_BYTES_AGGREGATE_2026-10-08.json) contains only public-safe totals and explicit unsupported-claim gates. The previous [metadata-only checkpoint](W4_P2_SOURCE_READINESS_UPDATE_2026-10-08.md) correctly reported private PDFs unavailable *in that earlier execution*; this record supersedes only that missing-bytes status and does not rewrite the earlier audit.

## Gates that remain closed

| Gate | Decision |
| --- | --- |
| PDF original bytes, official page count, full-PV text extraction | **PASS privately** |
| Private analytical correspondence linkage / selection digest | **PASS to recorded source hashes and scores** |
| Recompute full Harvard-v14 speech/PV seven-token overlap from *both* raw texts | **NOT RUN** (Harvard original speech archive unavailable here) |
| Independently verified individual human identity and speech/role boundary | **NOT RUN** |
| W1 real-data grouped meeting and source-family resampling | **NOT RUN** |
| 2016–2023 frozen lexical/semantic representation with original source selection | **NOT RUN** |
| W4 empirical descriptive real-data fitting | **WITHHELD** |
| W4 calibration, significance, political stance or causal-policy inference | **WITHHELD** |
| W4 publication eligibility | **WITHHELD** |

**Frozen safeguards:** none of the 37 reserved October 5–6, 2026 transcript meetings was opened, downloaded, embedded, scored or moved into a development frame. Original evaluation-lock hashes, human review decisions, D1 O1–O5, public browser/release manifests and other worker code are unchanged. The next defensible step is to obtain the Harvard v14 speech archive, independently replay original country-speech text comparison against the 63 SHA-verified PVs, preserve the complete private missing-cell inventory, then form a source-bound W1 development frame with a frozen high-dimensional feature basis. Do not infer drift before these gates pass.
