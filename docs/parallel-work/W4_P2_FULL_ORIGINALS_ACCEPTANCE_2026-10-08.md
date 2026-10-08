# W4 P2 full original-document verification — aggregate acceptance

**Date:** 8 October 2026. **Decision:** Complete official source-PDF acquisition, byte-integrity replay and full-speech content verification **PASS for the examined historical subset**. W4 empirical fitting, calibrated inference and public publication remain **WITHHELD**.

## Source acquisition and authentication limits

The independently authorized P2 job retrieved **63 complete original General Assembly verbatim meeting records** (sessions 71–79, 2016–2024) from UN Official Document System or UN Dag Hammarskjöld Digital Library links. These contained **3,370 pages and 53,218,960 PDF bytes**. The originals were transferred with recipient-only X25519/AES-GCM encryption, decrypted in the private verification environment and individually SHA-256-checked against the download manifest. All 63 locally captured PDF digests and complete extracted-text files passed replay checks. **The UN did not publish a separate reference SHA-256 for those PDF bytes**, so this is independent local byte-integrity and source-URL verification, not an external UN-signed digest.

No original PDF bytes, speech content, source/person row-level records or private encryption key are committed to public GitHub. The full original-PV private ZIP and a separate private analysis ZIP are delivered through the conversation only.

## Complete-speech correspondence: Harvard v14 versus original UN PVs

The assessment read **the entire original official meeting PDF** for each of 63 records, using all extracted pages. It compared Harvard's full country speech against normalized **seven-token shingles** and checked content across **ten speech deciles** and both ends. A strong match requires >=90% overall seven-shingle coverage, >=8 deciles with >=80% coverage and matching beginning/ending evidence. This is full-*speech-content-to-meeting-record* agreement, **not** cryptographic equality of a plain-text speech and a PDF or independently authenticated speaker identity.

| Year | Original PVs acquired | Strong Harvard speech matches |
| --- | ---: | ---: |
| 2016 | 7 | 82 |
| 2017 | 9 | 92 |
| 2018 | 6 | 115 |
| 2019 | 7 | 120 |
| 2020 | 7 | 107 |
| 2021 | 7 | 105 |
| 2022 | 7 | 128 |
| 2023 | 5 | 91 |
| 2024 | 8 | **0** |
| **Total** | **63** | **840** |

Out of **985** corpus/source-key candidates in the acquired official PVs, 840 pass the strong gate (all 2016–2023), 94 are partial/variant, 50 insufficient, and one exists in original UN records but not the Harvard speech archive. A further **752** candidate country-year records lacked an acquired original PV; their source status remains unverified, **not a verified absence**. No 2025 official-PV verification was attempted.

### Source-method discontinuity

Harvard v14's 2024 texts have **44.5% median seven-shingle overlap** against original official PVs in the sample, versus approximately **98.5–98.8%** in 2016–2023. None of the 144 2024 texts compared passes the common 90% gate. The corpus release describes mixed 2024 OCR, translation and other modality inputs, with 2025 English simultaneous-interpretation ASR; **2024–2025 are not measurement-invariant with the earlier speech texts** under the current feature contract. This finding identifies input/source-version differences, *not political movement or a quantified ASR error rate*.

A mechanical negative control tested 96 valid speech excerpts against deliberately **wrong original meetings in the same year**: median correct-document overlap **98.57%**, median wrong-document **0.52%**, maximum wrong-document **2.79%**, and zero false strong matches. This validates the proposed document-specificity check, not a drift significance hypothesis.

## Critical/high discrepancy outcomes

Of the 24 previously prioritized flags, source-level review produced: 14 workbook recorded-country/speaker affiliations corroborated against original official PVs (12 additionally meet the full-speech text gate, two 2024 are text variants); three national speech records missing from the supplied UN speaker index but present in original UN PVs with full Harvard text agreement; one official national address absent from Harvard archive; and **six unresolved source-method, identity or eligibility gates**. These are **source-document corroborations, not authenticated personal identities or human gold annotations**.

Original 2020–2021 PVs also distinguish introductory speakers from prerecorded leaders/annexed texts; do not count two role records as two independent national speeches. Zero names were independently authenticated as real people, and no owner/human adjudications were fabricated.

## Restricted W4 candidate panel

A **risk-stratified, nonrandom** matched-country observation frame is provisionally feasible for **2016–2023 only**. Require at least two original-PV-strong country-represented speech observations in each period, 2016–2019 and 2020–2023. The resulting **99 country affiliations** have **523 strong-match observation cells** across a **792-cell** country×year inventory and **55** distinct source-PV meeting records. The remaining **269** cells are *unreviewed or without strong corroboration*, **not zero speech occurrences**. Candidate selection SHA-256 is `3ebec834635e4d493e8035aeede3321efb951aa22f2f61d81f6ac7a0f65a4c89`. Source-meeting selection was purposive, so do not infer population performance from its restricted denominator.

| Gate | Decision |
| --- | --- |
| 63 complete original UN source PDFs, local byte hashes and extracted text | **PASS** |
| 840 original-PV corroborated 2016–2023 complete speech comparisons | **PASS on sampled pairs only** |
| Original recorded speaker/role evidence | **PARTIAL**; human person identity still unverified |
| Full national speech census or probability sampling | **NOT RUN** |
| Source text comparability for 2024–2025 | **FAIL / NOT DEMONSTRATED** |
| Frozen high-dimensional representation, verified year/genre/source grouping | **NOT RUN** |
| W1 statistical source dependence and W4 null-source compatibility | **NOT RUN** |
| W4 real descriptive model fit | **WITHHELD** |
| W4 calibrated statistical inference | **WITHHELD** |
| Research/website/publication release | **WITHHELD** |

## Reproducibility, confidentiality and next work

The private verification package contains original PDF SHA manifests, complete speech-correspondence records, a 120-cell sample ledger, 24 original source-case dispositions, 96 wrong-meeting controls, the 99-country candidate/792-cell grid, its source/selection digest and runnable analysis scripts. The original PDFs are in a separate private ZIP. **101/101 local consistency checks passed** for source bytes, counts, source exclusions, negative controls, private identities and eligibility withholding.

Next: source-bind the 99-country candidate with W1, preserve all 269 unreviewed cells and meeting source dependence, freeze a training-time lexical/semantic representation, correct W4's null-source inventory adapter **before** any real-data fitting, and pilot descriptive comparable changes under a preregistered selection and modality policy. Independently adjudicate source-role changes and expand source-PV verification to unreviewed cells. W4 inferred, calibrated or published claims cannot follow from this documentation.

**Frozen evaluation:** none of the 37 reserved October 5–6 2026 meeting transcripts were read. No W1/W4 method source, sealed evaluation lock, owner decisions, O1–O5 gate, shared browser asset, original source checksum or website mirror is changed here. W4 PR #18 and the original-source transfer PR #32 remain unmerged. This PR is **coordinator documentation only**, and the aggregate companion [JSON](W4_P2_FULL_ORIGINALS_AGGREGATE_2026-10-08.json) contains no source-linked row data.
