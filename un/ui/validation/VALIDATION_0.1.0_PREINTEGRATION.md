# Validation record — Shiny MVP 0.1.0

**28 September 2026. This is a prototype validation, not the existing D1 checkpoint's acceptance record.**

| Check | Actual outcome |
|---|---|
| Native R reference checks | **97 passed / 97; 0 failed**, R 4.6.1, Debian 13. |
| End-to-end dataset | 18 explicitly fictional English training statements dated 24 September 2026. No real UN transcript run claimed. |
| Fixed-topic retrieval | Explicit defaults plus arbitrary replacement topics; exact quote/span checks, multi-label behavior, passage exclusions, and unresolved non-matches. |
| Full-corpus invariance | Two different watchlists produced identical feature fingerprints and clustering assignments on identical scoped sources. |
| Numerical execution | Actual TF-IDF, hierarchical clustering, PAM, PCA, PCoA, and roster-deletion sensitivity. All outputs remain research-only. |
| Publication | Exactly five unavailable analytical packets; payload injection, sixth-slot insertion, and release flags rejected. |
| Source handling | Metadata not used as speech evidence; empty, undated, duplicate, out-of-range, and non-English cases checked; ZIP traversal rejected. |
| Export protection | Text/HTML escaping, literal pattern handling, and CSV formula-prefix protection checked. |
| Independent export checks | **21 passed / 21; 0 failed.** MIME parser and body round-trip; source quote spans and hashes; manifest verification; five-slot and no-send receipts; PDF readability/bounds. |
| PDF | Actual five-page file generated with existing Python/Playwright + Chromium fallback. Pages rendered and visually inspected; regional headers kept with following material. |
| Static interface preview | Rendered at 1440 and 390 px; no horizontal overflow or recorded JavaScript errors. Read-only layout, not a live Shiny session. |
| Shiny controller acceptance | **NOT EXECUTED**. Six required packages missing; dependency download access unavailable. The test records exit status 3 rather than claiming success. |
| Actual D1 integration and inherited tests | **NOT EXECUTED**. Checkpoint source ZIP bytes unavailable through the file materialization path. |
| Current transcript archive | **NOT EXECUTED**. Source ZIP bytes unavailable. |
| Windows / native Outlook / native `pagedown` | **NOT EXECUTED**. |
| Remote deployment / scheduled task / outbound email / external AI calls | None performed. |

## Evidence files

`test_results.csv` and `test_run.log` contain each R result. `R_sessionInfo.txt` records the actual R environment. `export_validation.json` and `.log` contain the independent checks. `shiny_runtime_status.txt` and `shiny_test.log` retain the live UI test's missing-dependency result. `static_preview_validation.json` identifies the preview-only scope.

`demo_run/` contains the executed request, source archives, evidence, features, research diagnostics, packets, HTML, plaintext, EML, PDF, session information, output manifest, and provenance. `manifest.csv` intentionally excludes the subsequently written completion result and changing progress record; the final package inventory covers those files. A manifest is a byte-integrity record, not proof of model validity or source authenticity.

## Problems found and corrected before delivery

1. Topic lists initially serialized with label names as a JSON object. Labels are now unnamed before object construction, and an independent JSON parse confirms an array of four topic objects.
2. A matrix clipping operation initially lost dimension attributes. The cosine/distance matrices now retain their shapes before numerical methods run.
3. Native headless browser startup was unreliable in this container. PDF generation now has a tested, optional existing-Playwright fallback; failure still leaves email/HTML usable and reports PDF unavailability.
4. Container file-URL navigation was unavailable. The fallback renders only the generated self-contained HTML bytes rather than navigating to local files.
5. Static screenshot capture needed explicit local rendering settings. The preview was checked without claiming that it exercised the Shiny controller.
6. Formula-looking CSV values are now exported as text; originals remain preserved for exact evidence checks.
7. PDF regional headings were initially stranded at page bottoms. Print break rules now keep each regional heading with its following country material.

## Interpretation

These are deterministic engineering and synthetic-data tests. They do not estimate real-transcript extraction accuracy, model calibration, stability in a real diplomatic corpus, government-device compatibility, production multi-user safety, or end-user acceptance. The supplied Shiny controller test and D1 integration plan still have to be executed against the actual dependencies and checkpoint before an integrated release can be declared.
