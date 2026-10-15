# W4 P1 — independently authenticated 2008–2015 General Debate originals

**13 October 2026. Source/provenance authentication only. No longitudinal inference, new W4 lexical fit, publication or merge authorized.**

Protocol fixed in e698629266914929a33e832e8b0df32bd5e59187; original PV symbol universe and audit split were frozen *before* original-document acquisition in 755ad1e5224a93a13763a8932f6275198f78c9f4. The new research estimand is 2008–2015 versus 2016–2023 (8+8 years), not a post-2020 intervention effect. The original 2016–2023 reference and release gates are unchanged.

## Pre-acquisition source and denominator register

The UN speaker index agrees with the UN Dag Hammarskjöld Library's public General Debate meeting-symbol ranges (https://research.un.org/en/docs/ga/generaldebate). That corroborates the meeting universe but does not authenticate full speech content.

| Year (session) | Indexed PV meetings | Speaker index rows | Original PV audit holdout (unread) | Development PVs |
|---|---:|---:|---:|---:|
| 2008 (63) | 12 | 192 | 3 | 9 |
| 2009 (64) | 11 | 194 | 3 | 8 |
| 2010 (65) | 12 | 208 | 3 | 9 |
| 2011 (66) | 18 | 197 | 4 | 14 |
| 2012 (67) | 16 | 194 | 4 | 12 |
| 2013 (68) | 18 | 191 | 4 | 14 |
| 2014 (69) | 15 | 196 | 3 | 12 |
| 2015 (70) | 16 | 191 | 4 | 12 |
| **Total** | **118** | **1,563** | **28** | **90** |

The partition ranks the SHA-256 digest of the frozen namespace W4-EXT-AUDIT-20261013, year and official PV symbol, reserving ceil(20%) of original PVs within each year. Its private canonical JSON digest is 9f82613e7057a66f9ca7ccb550fade49797d4457fd67ada2443ef6a00edb9ef5. The exact audit membership is privately registered and not committed. The 99-affiliation × 16-year expected frame contains exactly 1,584 distinct cells; unknown source opportunities stay unverified, not zero.

## Direct original-source results

Read-only encrypted GitHub Actions run [38457300153](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38457300153) obtained all **90/90 predeclared development official PV PDFs**, with zero acquisition failures, and exported only a recipient-encrypted byte archive. The X25519 decryption key remained local.

Independent local replay validated the decrypted source against the original acquisition manifest: **90/90 full PDF SHA-256, PDF header/EOF, first-page original PV meeting symbols, first-page official meeting dates, and full text extractability.** Totals are 3,407 pages and 43,696,584 complete PDF bytes. These are locally verified original-byte identities; no independent UN publisher-signed SHA-256 attestation was available. They establish neither verified individual speakers nor authenticated Harvard correspondence by themselves.

A first-page text-order problem caused an initial false failure for 50 PDF headers when only the first 1,600 extracted characters were checked. Searching the entire *first page* restored all 90 genuine header/date matches without changing source criteria. Two earlier CI runs failed source-free X25519 self-tests due to a variable typo and acquired zero documents; both failures are retained in GitHub run history.

## Original Harvard v14 TAR-member and full original PV speech checks

The original Harvard v14 TAR matched its recorded SHA-256 and MD5 and **1,538/1,538** original 2008–2015 speech members decoded as strict UTF-8. The frozen 99-affiliation pre-2016 population has **785 original Harvard speech members out of 792** expected candidate cells; seven are absent from the Harvard archive and must not be represented as no-speech.

The country-label/index mapping was frozen on metadata before opening new PV texts: 697 direct normalized matches, 82 fixed aliases, and 13 ambiguous/unlinked opportunities. From these, 601 development original-PV comparisons were eligible. Exact raw original Harvard TAR-member speech text was rehashed and matched against complete official PV text using the original unmodified strong rule: seven-token overlap >=0.90, >=8 of 10 speech deciles >=0.80, and beginning/end >=0.40. **600/601 passed**; one failed, retained as source-unverified. The first comparison script timed out while repeatedly seeking the compressed TAR and delivered no result. A sequential TAR-member replay completed all 601 checks, using the *same thresholds and population*.

The pre-2016 development verification resulted in 600 authenticated cells from **88** original meeting families, not 600 independent documents or people. No 28 reserved source-quality PVs or 37 October 5–6 2026 evaluation meeting transcripts were opened.

## Final 16-year source coverage

| Year | Verified 99-country candidate cells | Unverified |
|---|---:|---:|
| 2008 | 76 | 23 |
| 2009 | 66 | 33 |
| 2010 | 71 | 28 |
| 2011 | 76 | 23 |
| 2012 | 77 | 22 |
| 2013 | 79 | 20 |
| 2014 | 80 | 19 |
| 2015 | 75 | 24 |
| **New 2008–2015** | **600** | **192** |
| **Previously authenticated 2016–2023** | **790** | **2** |
| **Full 2008–2023** | **1,390** | **194** |

All 194 unresolved remain explicitly unverified, not speech absences: 178 pre-2016 cells associated with the still-unopened source-quality audit PV meetings, seven missing original Harvard TAR members, six unresolved index-to-recorded-affiliation mappings, one below the full-speech correspondence threshold, and two inherited 2016–2023 source-unverified records.

The 2016–2023 private source validation is inherited from earlier work and **was not newly rerun this turn**. This audit proved byte-for-byte invariance of the inherited 792-cell slice in the new derived private 1,584-cell inventory. The newly promoted 600 source cells are separately versioned.

## PASS/FAIL/NOT RUN acceptance

| Criterion | Decision | Grounding |
|---|---|---|
| Pre-acquisition UN meeting-index universe and frozen 28-PV audit holdout | **PASS** | 118 original PVs / 1,563 index records, deterministic private split |
| Full original document integrity on 90 development PVs | **PASS** | Independent raw bytes and complete first-page identity checks |
| Original Harvard TAR-member/full-PV strong correspondence | **PASS for 600 development observations** | 600/601; failed record not promoted |
| Full 99 × 16 expected inventory | **PASS** | 1,584/1,584 retained, missing is not zero |
| Preregistered overall verified source coverage >=95% | **FAIL** | 1,390/1,584 = 87.75% |
| Preregistered each-year verified coverage >=90% | **FAIL** | All eight new pre-2016 years below 90% |
| >=90 affiliations having >=6 annual observations in each era | **FAIL** | Only **69** qualify in 2008–2015 |
| Independent source-quality validation of 28 audit original PVs | **NOT RUN** | All intentionally unopened |
| New 2008–2015-trained TF–IDF/SVD64/reference-fit uncertainty | **NOT RUN** | Pre-registered source readiness fails |
| New W1/W4 empirical 16-year numerical fits | **NOT RUN** | Do not prematurely narrow the country/year universe |
| Preregistered 36-cell × 600 synthetic 64-D refit calibration | **NOT RUN** | Separate confirmatory phase |
| Calibrated real-world longitudinal confidence intervals and political-position inference | **FAIL / WITHHELD** | Source selection, year effects, missingness and representation uncertainty unresolved |
| Public empirical release, source-site publication, frozen protocol changes | **FAIL / UNAUTHORIZED** | No release or evaluation approval |

Open PR #51 addresses a former weakness in the P2→W1 original Harvard TAR-member binding; this local P1 comparison **did** verify the exact archive members, but the shared W1 input adapter remains gated on separate acceptance of the repaired production code. The source-only PR must not be read as a native W1 source integration approval.

Original PDFs, source-level SHA and index mappings, Harvard texts, private 600-row correspondences, 1,584-row private inventory, or the local recipient decryption key **must not be committed to public GitHub**. The only public material here is source-only code and non-identifying aggregate documentation and digest commitments. The 37 unopened 2026 evaluation transcripts, original evaluation-lock metadata, owner review decisions, frozen D1 O1–O5 release gates, browser, website mirror and source hash originals are unchanged.

**Next phase:** independent source-quality audit of the 28 pre-2016 UN PV originals under the frozen holdout protocol, targeted resolution of original Harvard text omissions and six affiliation ambiguities, then reassessment of observed-year coverage. Full 64-D training-only lexical inference and calibrated statistical intervals remain withheld until all prerequisites pass.

