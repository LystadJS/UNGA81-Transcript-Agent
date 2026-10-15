# Coordinator W4 P1/P2 stacked-to-main acceptance — 15 October 2026

**Status:** engineering-only source authentication records and encrypted acquisition tools. **No real 16-year W4 models, estimates, confidence intervals, national positions, or empirical publication.**

## Git topology and exact source

PR #52 (prospective expanded-year design) was accepted and squash-merged into main as `55f7c03c0944865e0f273f9d05648936174fdb31`. PR #59 was merged into the feature branch `coord/w4-expanded-year-design-20261013` (stack commit `b61af8e53ca59d59fdf80e5794c12a3ebbecf1bb`), **not main**. PR #61 was merged into `coord/w4-p1-original-pv-intake-20261013` (stack commit `5deb9e74e11f649444d6c29ed80d42629dc1600c`), **not main**.

This coordinator integration is based on main `1e78e81a2270a6b643b9c344863199107e9138f2` and adds **only eleven previously absent P1/P2 files** by directly reusing their exact Git blob SHA objects from `5deb9e74e11f649444d6c29ed80d42629dc1600c`; it does not replay/squash the historical preregistration, replace any file, change study timing, or alter prior original-source records. The canonical original P1 split `9f82613e7057a66f9ca7ccb550fade49797d4457fd67ada2443ef6a00edb9ef5` remains intact.

## What the new files mean

- P1 frozen 118 historical original-PV symbols: **90 development source documents + 28 independent source-quality audit documents**, neither including the 37 2026 evaluation transcripts.
- Original P1 acquisition received 90 encrypted-PV documents [Actions 38457300153](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38457300153), PASS. Comparing that executed acquisition SHA to PR #59 final head showed only later aggregate documentation changes, not a changed downloader/split.
- P2 independent 28-PV audit [Actions 38475062057](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38475062057), PASS. Comparing its code SHA to PR #61 final head showed only additional aggregate tests/docs/CI. Exact-head P2 [denominator CI 38477579226](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38477579226), PASS.
- Private original-source research reports **1,574/1,584 candidate actor-year opportunities verified**, ten unresolved. These are **aggregate prior private-audit claims, not a new independent original-PDF/Harvard replay in this PR**. Authenticating source bytes is distinct from verifying positivity, MAR/MNAR, source-genre comparability and period selection.
- The independently frozen **64-PV probability meeting-sample design** merged as PR #58 is a separate sampling estimand from this **90+28** split. Do not combine source weights, treat its 64 meetings as this design's 90 development meetings, or fit using 28 quality-audit records.

## Evidence gates

| Gate | Engineering decision |
| --- | --- |
| Public-source scope, deterministic split and recipient-only encryption | PASS for reviewed code / prior executed acquisition |
| Independent private original UN-PV/Harvard source bytes replay in *this* coordinator PR | NOT RUN |
| Frozen original author decisions, old source hashes and 37 Oct 2026 reserved text | UNCHANGED / NOT ACCESSED |
| Original observed source-selection/positivity MAR/MNAR verification | NOT RUN |
| Newly refit 64D lexical 2008–2023 models, 21,600 synthetic calibration | NOT RUN |
| Actual country inference and empirical release | WITHHELD / FAIL |
| Published browser, site release or D1 O1–O5 change | NOT APPLICABLE / NONE |

Review the [protocol](W4_EXPANDED_YEAR_SELECTION_REPRESENTATION_PREREG_2026-10-13.md), [P1 source report](W4_P1_2008_2015_ORIGINAL_SOURCE_ACCEPTANCE_2026-10-13.md), and [P2 source audit](W4_P2_2008_2023_INDEPENDENT_SOURCE_AUDIT_ACCEPTANCE_2026-10-13.md). No protected source, loader, site, numerical method, or original record is changed. Only a separate privacy/source-comparable and independently calibrated study can enable a future real fit.
