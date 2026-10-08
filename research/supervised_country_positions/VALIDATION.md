# Supervised country positions — engineering validation

**Decision (8 October 2026):** PASS for native **synthetic engineering** checks; empirical eligibility and public release remain WITHHELD.

**Evidence run:** [GitHub Actions 37832756972](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/37832756972).  All three jobs succeeded at exact source head ecdcb1747d45061fe8b6783e648d0aa33477a9eb. The recorded successful head is the source-code baseline; subsequent documentation-only changes require latest-head rechecks.

| Gate / executable test | Actual status | Evidence |
| --- | --- | --- |
| Native Node.js 22, proposition validation, source and position accounting | **PASS** | 17/17 checks, including invalid-input refusal, real-data and release blocks, Unicode quote offsets, source-family counting, conflicting/insufficient/conditional positions and matched-proposition denominators. |
| Native Python 3.11, blind private annotation workflow | **PASS** | 6/6 tests; verifies source digests and offsets, closed reserved dates, private output/overwrite controls, draft identity and no auto-gold fabrication. |
| Native R 4.6.1, existing M12/M17 | **PASS** | Four logged assertions: unchanged M12 fit on synthetic input; unchanged M17 fit on synthetic input; empirical inputs rejected; country leakage rejected. The adapter handles the original source-file import explicitly without editing research/engines.R or engines_more.R. |
| Real Chromium 154 via Playwright 1.55.0 | **PASS** | Desktop 1440px and mobile 390px, each for the viewer and annotation page (4 scenarios). Source evidence, accessible keyboard selection, year changes, source-linked inspection, draft export/import, incompatible draft refusal, rejection of publication-eligible reports, and no outbound HTTP requests. |
| Reproducible fictional report builder | **PASS** | Native Node produced fictional JSON; Python asserted dataset_kind synthetic_engineering, publication_eligible=false, daily_adapter_integrated=false, model_fitted=false, and each evidence record synthetic_only. |
| CI workflow privilege/scope | **PASS at runtime; coordinator ownership exception required** | New *isolated* .github/workflows/supervised-country-positions.yml runs solely on this research subtree, with contents:read. No existing workflow or publication pathway was changed. |
| Source/label independent empirical validation | **NOT RUN** | No real corpus labels, speaker adjudication, probability calibration, source-modality control or country alignment accuracy was evaluated. |
| D1/publication website integration | **NOT RUN / WITHHELD** | No O1–O5 flag, D1 daily adapter, production browser entry point, site release manifest or portfolio mirror changed. |

## Diagnosed and corrected failures (not silently reclassified)

1. Run 37832116139: Playwright module unavailable because the CI NODE_PATH expression was accidentally escaped. Corrected workflow interpolation.
2. Run 37832227474: Real browser found that author CSS overrode the viewer's HTML hidden state before importing a report. Corrected with an explicit [hidden] style; the prior failed browser assertion remains recorded.
3. Run 37832614488: Native R exposed the original I6 script's assumption that sys.frame(1)$ofile is present during source(). Corrected the **new adapter only**, parsing original research/engines.R expressions and explicitly loading the exact existing engines_more.R companion. Original M12/M17 computations and guards remain unchanged.
4. Run 37832756972: Full successful native Node/Python/R/Chromium acceptance on the corrected source commit.

## Exact reproduction commands

From the repository root on supported native runtimes:

    node research/supervised_country_positions/test_positions.cjs
    python3 research/supervised_country_positions/test_prepare_review.py
    Rscript research/supervised_country_positions/test_m12_m17_adapter.R

For browser interaction QA, install a separate Playwright 1.55.0 runtime and Chrome/Chromium and run:

    node research/supervised_country_positions/test_browser.cjs

The precise GitHub Actions dependency setup, environment controls and test invocations are in the dedicated PR workflow. Its only source text is invented engineering-fixture language, never the user's private review material.

## Engineering limits and release policy

This validation does **not** establish any substantive U.S., China or third-country policy alignment. The six propositions are draft examples, no owner-confirmed human stance gold was supplied, and no real-data classification model was trained. Source-family agreement counts are descriptive; no diplomatic confidence intervals, political-affiliation scores or causal influence claims are authorized.

Original UN/source checksums, private transcripts, the 37 reserved October 5–6 meeting texts, prior owner human decisions, W1–W7 analytical gates, and D1 O1–O5 publication controls remain untouched. PR #36 must undergo coordinator ownership and latest-main reconciliation; successful synthetic CI is engineering readiness, not permission to merge or publish automatically.
