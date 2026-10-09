# Supervised country-position annotation — first-pilot status

**9 October 2026 | Status: SOURCE/REVIEW INTAKE READY (engineering) — real reviewed labels and empirical outputs withheld.**

## What is implemented

The private-only pilot workflow now supports an original-PV-quality-gated historical source register, a source-hash-bound country/time split, separate anonymous review packets, neighboring source evidence, voluntary owner review attestation, and a source-checked finalized-label status audit. These mechanisms do **not** train a model or classify any actual country.

The first two draft tasks are **support for ending the U.S. Cuba embargo** and **support for Ukraine's sovereignty and territorial integrity**, each coded as a named proposition rather than a topic. The original M12/M17 kernels remain synthetic-only and the browser's fictional alignment viewer remains a demonstration.

| Gate / input | Actual status | Next acceptance evidence |
| --- | --- | --- |
| Predeclared proposition and sampling plan | COMPLETE — engineering protocol | Owner reviews the proposed codebook, or provides concrete amendments before real labeling |
| Historical original-PV corpus and private source-quality CSV | NOT AVAILABLE IN THIS CONVERSATION | Authorized private 2016–2023 strong-match canonical texts and original-PV quality data |
| Actual source-level allocations | NOT RUN | Digest-locked pilot_plan.json plus private splits.csv generated from verified input |
| Actual owner-reviewed issue labels (these two propositions) | 0 CONFIRMED HERE | Owner-reviewed packet and un.review.v1 source-linked decisions |
| Actual owner-reviewed stance labels (these two propositions) | 0 CONFIRMED HERE | Matching original passage offsets, attested review, owner finalization |
| Independent adjudicated stance gold | 0 | Not assumed in the owner-approved single-reviewer pilot |
| Calibration/testing, classifier fitting, inference | WITHHELD | Fully source-separated owner labels and independent method-specific evidence |
| Country-alignment map publication | WITHHELD | Statistical/interpretive validation and separate release authorization |

**Existing labels are not interchangeable:** The earlier 24-owner-decision AI *relevance* pilot is not a policy-proposition stance label set. Likewise, assistant-provisional quick-reader country statements are not human gold. No human stance decisions were supplied in the current conversation and none were fabricated.

## Historical frame and limitations

The prospective input is the **restricted original-PV-strong 2016–2023 General Debate subset** from the earlier P2/W4 source work. Its previously reported 99-country, 523-observation pilot was purposive and nonrandom, and not a census. This annotation implementation **does not possess those individual original private records**, and it cannot presume that all 99 country affiliations or the planned time/country strata will qualify.

The protocol withholds the 2024–2025 modality discontinuity, sources missing their full-text/OCR/translation verification, collective or unresolved speaker capacities, and the 37 reserved 5–6 October 2026 meeting texts. The planner reads only metadata for ineligible sources; a packet refuses any passage table carrying reserved-date source records.

The fixed allocation policy is chronological and country-disjoint: **2016–2019 train; 2020–2021 calibration; 2022–2023 test**, with 60/20/20 country quotas derived from a SHA-256-ranked seed. Real achieved source and country counts **cannot be asserted** until the owner-provided private corpus is validated. All omitted country/period source rows enter a reasoned withholding ledger.

The annotation target is **96 train, 32 calibration, 32 test proposition–passage pairs**, split equally between the two first propositions; 70% lexical screening and 30% unfiltered candidate controls are *sampling methods, not labels*. Shortages are explicit. Test review packets require an affirmative unlock and cannot inform tuning.

The code validates canonical source text bytes against the supplied text SHA-256 and passage Unicode offsets. The **original PDF byte hash recorded in source_quality.csv remains a prior private-audit attestation**, not something this planner independently reopens or authenticates.

## Owner handoff

From an authorized private Windows/local workspace, supply (or place in the designated private directory) complete un.review.v1 sources.csv, passages.csv and original speech texts, plus a **real** source_quality.csv. Run the private plan command documented in README.md. Then review the development packet in the offline annotation.html interface and return the exported private draft.

The owner must make, confirm and finalize actual choices. Merely invoking the tools, generating a split file, checking a UI box during synthetic tests, or retrieving public transcripts does not create human-reviewed stance gold. All private row-level inputs and outputs must remain off public GitHub.

Run the separate **status** command after actual owner finalization; it requires the exact frozen split file, verified source text and offsets, owner records, review timestamps and finalized labels. It reports aggregate class/task counts without releasing passages or predictions. It never marks training or publication eligible.

## Verification and publication controls

The preexisting read-only **Supervised country positions — synthetic acceptance** GitHub Actions workflow runs native Node/Python/R and Chromium checks on this research namespace. The added tests use fictional inputs, synthetic review fields and fake sources expressly marked as engineering fixtures.

No site or D1 code, original research kernels, frozen source hashes, existing owner decisions, evaluation locks, O1–O5 gates, Pages workflows, live assets or portfolio mirror was changed by this annotation pilot.

**Scientific disposition:** Source-separated evaluation design prepared. **Actual independent real-source split and human label creation remain incomplete until the private corpus and owner decisions are available.** No empirical country alignment or publication is authorized.
