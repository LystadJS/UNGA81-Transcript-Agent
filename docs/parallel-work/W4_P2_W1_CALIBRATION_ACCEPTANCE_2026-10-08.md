# W4 original-source P2→W1 adapter, historical PV expansion and calibration

**Coordinator checkpoint — 8 October 2026.** This work completed an authenticated *private* P2-to-W1 engineering adapter and two separately preregistered simulations; **statistical inference, original P2 legacy-v1 binding, and public research publication remain withheld.** The [aggregate machine receipt](W4_P2_W1_CALIBRATION_AGGREGATE_2026-10-08.json) contains no source-linked private observations.

## 1. Authenticated P2-to-W1 adapter

Rechecked **63 original complete UN General Assembly PV PDF file hashes** against the P2 private original document-byte manifest; streamed the actual Harvard Dataverse v14 publisher-file archive and matched all **523 original speech-file byte SHA-256 values** to the P2 source-correspondence grid and the source-backed W4 panel. The 523 belong to 55 original PV meetings across 99 *recorded country affiliations* in 2016–2023. All **269 unverified** country×year cells remain separate with null source identities and no zero speech or zero-vector imputation. Three Bahamas dates are supported by their PV titles, not the incomplete official speaker CSV.

The new `research/source_acquisition/general_debate/p2_w1_authenticated.py` verifies original PV bytes, each original Harvard text, full-speech correspondence threshold, country×year and UN meeting joins, source text hashes, original date basis, and source-status meaning. It fails closed on tampered hashes, wrong meetings, insufficient speech correspondence and false identity promotions. It writes only into a new private output outside the GitHub checkout. Its W1 input remains explicitly typed `un.p2.original-pv-reconciled.v1`, **which is not accepted by old legacy v1**. The P2 source schema must be accepted separately before production consumers may use this input; it is never relabeled to a different approved corpus type.

**Local canonical W1 execution:** on the authenticated full-text 523-record frame, original W1 k-means and Ward methods both fitted; four meeting-group refits succeeded, and two affiliation-group schedules were correctly skipped due inadequate independent transitive groups. In this explicitly distinct LSA6 exploratory specification, ARI **0.47555**, AMI **0.53812**. Only a *local temporary source-schema enum extension* was applied; numerical algorithms and the committed W1 implementation were unchanged. The local extension is an engineering compatibility test, **not a production `un.parallel-analysis.v1` acceptance**. This LSA6 exploratory partition must not be compared numerically to W4's separately trained 64-D frozen reference.

The user's complete source-bearing private evidence, fitted source text, local W1 execution, and model/checkpoint details are in the private downloadable ZIP, **not GitHub**.

## 2. Original-PV source coverage expansion

A risk-prioritized list of **38 additional** official UNGA General Debate meeting symbols from 2016–2023 was frozen before source access. The separate read-only Actions [run 37845226174](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/37845226174) obtained all **38 complete official PDFs**, SHA-256-hashed their bytes in memory and confirmed text extractability. No source text or PDF was uploaded or published; only an aggregate per-year acquisition receipt. These 38 are outside the original selected 63-PV archive. The original 2016–2023 selected subset contains 55 distinct verified UN PV meetings; **93 distinct historical meeting documents** have now been subject to some original-document integrity checking across the two batches.

**Important non-delivery:** the expanded 38 original PDFs and per-file digests were *not* retained in the private source archive. Full speech-to-Harvard comparisons, revised country×year eligibility, translation quality and source inclusion rates **remain NOT RUN** for these 38. The restricted W4 validated cohort remains **523** speech observations from 55 meetings, **not 523 plus new addresses**. More document access alone does **not** demonstrate a reduction of original speech-selection bias. A private source-preserving transfer/retrieval followed by full 7-token/10-decile matching and roster correction is still required.

## 3. Preregistered longitudinal uncertainty simulations

The [first preregistered design](W4_P2_W1_CALIBRATION_PREREG_2026-10-08.md) held fixed the **actual 99-affiliation × 8-year × 55-meeting, 523-observation attendance mask**. It generated synthetic continuous scalar outcomes (not actual speech embeddings), with persistent actor shocks SD 0.10, year shocks SD 0.15 (stress 0.25), meeting shocks SD 0.10, and observation shocks SD 0.12. True signed effects were **0 and +0.10**. Four predeclared scenarios contained 400, 400, 200 and 200 Monte Carlo panels, with 199 bootstrap draws each. The estimand was an equal-affiliation later-minus-earlier signed scalar mean on the **same 99 original actors**.

Under the preregistered fixed-cohort requirement ordinary row/meeting/year **replacement resampling produced zero eligible intervals in all 1,200 panels** per method: resampled source opportunities were lost, so some actors had no observations in one or both periods. Estimated coverage is *undefined*, not a measured 0% coverage. Across scenarios, valid fixed-cohort draw rates: individual rows **0%**, whole meetings **less than 0.02%**, whole years **46–47%**.

The separate [preregistered actor-preserving addendum](W4_MULTIPLIER_CALIBRATION_PREREG_ADDENDUM_2026-10-08.md) was committed **before its simulation**. It used positive Dirichlet whole-year weights, and positive hierarchical year + nested-meeting weights. Both methods kept every country, achieving **100% interval delivery**. The *nominal* 95% percentile interval coverages nevertheless were:

| True shift | Year shock SD | Year-positive weights | Year + meeting positive weights |
| --- | ---: | ---: | ---: |
| 0.00 | 0.15 | 63.25% | 59.0% |
| +0.10 | 0.15 | 67.5% | 64.0% |
| 0.00 | 0.25 | 62.0% | 58.5% |
| +0.10 | 0.25 | 66.0% | 63.5% |

The preregistered acceptance requirement was **≥92% coverage on all four simulations**, with adequate delivery. **Both actor-preserving procedures FAIL** by a wide margin. Monte Carlo coverage SEs are approximately 2.3–3.5 percentage points, not sufficient to explain the 20–36-point shortfalls. This is an *explicit design-specific simulation failure*, not a statement about the uncertainty of observed country-political stances.

### What this means statistically

Observed UN meetings nest inside **only four year blocks in each comparison era**; 99 actors recur across year/meeting blocks, and original PV selection was nonrandom. Independent rows, independent countries, ordinary meeting bootstrap and asymptotic year-cluster intervals are unjustified; positive weights solve cohort attrition but **do not calibrate inference** under realistic shared-year shocks. Neither the reference-trained TF–IDF/LSA checkpoint uncertainty nor source-selection bias was generated or calibrated in these scalar simulations. Year/meeting structure must be replicated over more annual blocks and the variation model justified externally before confidence intervals can be considered.

## 4. Acceptance decisions and limitations

| Gate | Decision |
| --- | --- |
| Original 63 PDF and 523 Harvard speech-byte hash joins | **PASS** |
| W1 local source-authenticated numerical execution | **PASS; local P2 allowlist only** |
| Old v1 production P2 source schema and publication adapter | **WITHHELD** |
| Additional 38 original UN PV PDF byte/extraction checks | **PASS in transient runner** |
| Durable per-file PDF archive / new full speech matches | **NOT DELIVERED** |
| Ordinary original-population bootstrap interval production | **FAIL** |
| Positive whole-year / nested-meeting percentile coverage | **FAIL** |
| W4 calibrated uncertainty, diplomatic position inference | **WITHHELD** |
| Public research/browser release | **WITHHELD** |

**Implementation changes:** Only additive original-source adapter, synthetic tests, historical public meeting list, aggregate-only Actions workflow, preregistered documentation and aggregate receipts. **Do not change** old W1 numerical kernels, W4 PR #18, current v1 schemas, 37 reserved October 5–6 2026 meetings, evaluation lock, original corpus hash records, D1 O1–O5 release gates or website mirror. This PR must not merge W4 automatically or publish source-linked country results.

**Next scientific step:** obtain 38 original PDFs in approved *private* storage and independently match full Harvard speech texts; move toward a near-complete session-by-country denominator and a richer within-year meeting series; implement a separately reviewed versioned P2 W1 upstream schema; then recalibrate uncertainty with predeclared source/year/actor sampling assumptions, nonrandom selection and feature-fit uncertainty. Synthetic calibration failures cannot be repaired by dropping country-years or pretending 523 speeches are iid.
