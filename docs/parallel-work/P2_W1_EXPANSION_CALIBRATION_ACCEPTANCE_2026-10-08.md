# P2→W1 original-source authentication, 2016–2023 PV expansion and uncertainty calibration

**8 October 2026 — engineering research acceptance report.** This product reports original-source verification and **private, noninferential** W1/W4 numerical checks. It is not a public diplomatic-country alignment result or approval of an uncertainty interval.

**Preregistration:** [P2 W1 expansion and calibration protocol](P2_W1_EXPANSION_CALIBRATION_PREREG_2026-10-08.md), committed as `4d0e498b50e491b04f28ecc4e07089fc0bc4dcc7` **before retrieval/inspection of the expansion PDFs**.

## Original-UN-document source coverage

All **50 predeclared additional official PV documents** were downloaded from original UN document endpoints and transferred only as recipient-encrypted artifacts. They passed full PDF SHA-256 integrity, header/EOF, page count and extractability checks: **2,337 pages, 38,301,595 original PDF bytes, zero failed downloads**. The combined 55 original 2016–2023 PV documents and 50 new PDFs cover **all 105 unique PV meeting symbols enumerated by the supplied UN General Debate speaker index** for sessions 71–78. Together: **5,184 full pages and 84,661,892 verified original PDF bytes**. These are downloaded original bytes checked against our independent *local* digest ledger, not a publisher-signed UN hash.

The exact Harvard Dataverse v14 tar archive SHA-256 remains `55077dccf7242cdf544aa95c4797c68e443b0c37344c9c112a2e2392ddfcf8e5`. The committed source reader replays its text bytes against the archive, and the source comparison recomputes seven-token normalized shingles against the **complete extracted UN PV**. No original PDF or speech text is committed here.

| Historical opportunity | Earlier P2 | After expansion | Interpretation |
| --- | ---: | ---: | --- |
| Official 2016–2023 PV source meetings available | 55 | **105 of 105 indexed** | Complete *index meeting-symbol* coverage, not independently certified state-membership census |
| Harvard 2016–2023 country speeches passing original PV full-speech gate | 840 in earlier inspected PVs | **1,543 of 1,545** | Two remain below at least one preregistered source-matching condition |
| Original 99-country pilot, verified country-year source cells | 523 / 792 | **790 / 792** | 267 previously unverified cells promoted by original-document evidence |
| Pilot cells still unverified | 269 | **2** | One original Harvard text missing, one source-text threshold not met; **not** verified no-speech or zero |
| Known 2024–2025 source-method discontinuity | Excluded | Excluded | Earlier modality comparability problem remains |

The source-corroboration rule was fixed **before** this expanded audit: normalized seven-token overlap >=90%, >=8/10 speech deciles with coverage >=80%, and coverage of the beginning/end >=40%. The two residual historical source cases are not silently promoted by relaxing the rule. Three General Debate addresses missing from the original UN speaker index have original PV corroboration from the earlier P2 stage, but a missing index row is still an index-quality issue. Country affiliation remains the unit; repeated independently verified humans are **not** identified.

## Source-authenticated P2-to-W1 input contract

The coordinator branch adds a read-only `research/source_acquisition/p2_expansion/p2_to_w1_source_adapter.cjs` that refuses to construct a W1 development frame until it has:

1. Verified the **entire original Harvard v14 tar** against its expected SHA-256.
2. Independently SHA-256 checked **all 105 complete original PV PDF files** and their per-observation PDF byte/link identities.
3. Recomputed the original UTF-8 speech-content hash against the supplied Harvard archive extract and checked dates/meeting symbols/recorded affiliations.
4. Required the preregistered entire-speech comparison attestation, source classification and actual meeting date provenance for every `available` observation.
5. Audited all **792** expected actor×year cells and preserved two `unverified` rows with unknown, null source identifiers; neither is inserted into the W1 eligible fit population.
6. Applied a declared exact source-bound selection manifest before W1 numerical fitting, without changing W1 numerical algorithms or mislabeling source schema.

The W1 **input-only** `un.source-validation.frame.v1` source-schema enum and relational verification gain an additive, fail-closed `un.p2.original-pv-reconciled.v1` source path. The **existing `un.parallel-analysis.v1` 1.0.0 analytical schema is unchanged and continues to refuse direct P2 export**; the separate `un.parallel-source-inventory.v1` companion represents all 790 verified and two unverified cells. A new historical analytical v2 output or appropriately reviewed source-bound compatibility adapter remains required before W5/W6 browser use.

Actual private original-PDF/Harvard replay validated the committed adapter on two W1 runs and **eight adversarial mutations** (source type relabeling, original PDF bytes, Harvard text SHA, false full-speech match, invented event date, person attribution, forged availability and unsupported date authority). All eight correctly failed closed.

## Canonical W1 method execution

The strict P2 input rules accepted two **separately declared** same-observation numerical evaluations of existing W1 k-means and hierarchical Ward LSA clustering, without W1 kernel changes. W1's source-population cap is **600 observations**: the full 790-case source inventory was authenticated, **not fitted in one 790-case canonical W1 run**.

| Diagnostic | Original 523-source cohort | Expansion-balanced 600-source QA sample |
| --- | ---: | ---: |
| Observations / original source meetings | 523 / 55 | 600 / subset of indexed 105 |
| Cohort construction | Original P2 strong-audit observed set | SHA-256 observation-ID rank, 75 verified speeches per year |
| W1 full fits | 2/2 success | 2/2 success |
| W1 whole-meeting grouped refits | 4/4 success | 4/4 success |
| Affiliation/source closure schedules | 2 withheld | 2 withheld |
| ARI k-means versus Ward | 0.4756 | 0.5609 |

The two ARIs measure *algorithm agreement in different source-selected populations*, not historical alignment or improved methodology. Because repeated countries bridge meetings and years, the W1 affiliation/source group closure has one connected group and cannot yield independent-country bootstrap replicates. Refusals are recorded as skipped checks. All W1 actual-source runs, native fit evidence and original input frames remain private.

## Frozen W4 movement: source-selection sensitivity

The prior fixed 64-dimensional reference was fitted only on the 252 verified 2016–2019 speeches originally selected and the **267 newly source-verified speeches** were projected without any refitting of vocabulary, IDF or SVD. All original 523 vectors reproduced with a maximum absolute difference of `5.11e-15`.

| Descriptive fixed-reference diagnostic | 523 original verified sources | 790 expanded verified sources |
| --- | ---: | ---: |
| Matched country affiliations | 99 | 99 |
| Mean within-country 64-D Euclidean distance | 0.5398 | **0.3867** |
| Norm of common-country centroid displacement | 0.2774 | **0.1924** |

The large shift in these statistics after adding source records is evidence of **meeting/source selection sensitivity**. It must not be represented as reduced geopolitical movement or recalibrated inference. Retaining the **old, partially selected** training basis is intentional for a paired numerical comparison; it is not a new final 2016–2019 population-trained reference. A separate future reference re-fit is a different frozen experiment.

The original W4 module also ran on all 792 inventory cells (790 available, two unverified), with 99 matched recorded country affiliations, **105/105 whole-source meeting deletions**, eight/eight annual deletions and sixteen/sixteen one-year-from-each-era deletions. Every perturbation retained the matched actor population. Conditional mean distance deletion ranges: meeting **0.3821–0.3958**, year **0.3867–0.4181**, paired years **0.3906–0.4384**. These are **sensitivity ranges, not confidence intervals**. There are zero genuinely paired independent meeting source families across the two eras; W4's bootstrap correctly remains withheld.

## Preregistered synthetic known-truth calibration

The synthetic experiment was declared before expansion: **600** Monte Carlo worlds, seed 20261008, true additive scalar beta **0.20**, nominal **90%** interval coverage, 199 year-bootstrap draws per simulation, shared country, meeting and calendar-year random effects. It uses the real pre-/post-expansion *missing-source patterns as fixed, private masks*, but **not original UN speech texts or fitted political labels**.

| Interval method (expanded 790-mask) | Year shocks independent | Year shocks AR(1), rho=.65 |
| --- | ---: | ---: |
| Naive country-paired t | **18.5%** | **14.3%** |
| Four-year-per-era Welch year-level t | **92.0%** | **70.2%** |
| Whole-year within-era bootstrap percentile | **78.8%** | **53.3%** |

Only the year-level Welch method passes the preregistered known-truth synthetic calibration criterion in the *independent-year* world (Wilson 95% coverage bounds approximately **89.6–93.9%** around 92.0%). With serially dependent years the same method severely undercovers at 70.2%. The source-group bootstrap fails to produce an evaluable interval in **all 600 pre-expansion simulations under each world** because many resampled years omit an entire selected country-period; these failures were counted, not fixed by imputation. The expanded bootstrap is evaluable but undercovers in both worlds (78.8% / 53.3%).

**No real-source confidence interval passes the release gate.** The simulation assumes Gaussian shock components, fixed selection masks and two particular year processes; it cannot validate exchangeability, actual outcome-dependent missingness, common policy agenda, effective independent years, or a 90% interval for observed W4 64-D distances. With **four years per comparison era**, a real year-cluster asymptotic SE, significance claim, or source-level political movement conclusion remains withheld.

## Acceptance, privacy and scope

| Gate | Decision |
| --- | --- |
| Exact 105 original UN PV source bytes and 1,543 historical full-speech corroborations | **PASS**, selected 2016–2023 document universe |
| 790-case original source authentication and 792-case sidecar | **PASS**, private descriptive input |
| Canonical W1 P2 input and method regression | **PASS** under additive restricted source schema; 523 and 600 cohorts |
| W4 expanded frozen-reference and grouped sensitivity | **PASS**, private descriptive only |
| Preregistered synthetic simulation and failed-replicate audit | **PASS**, known-truth simulation only |
| Real-world sample selection, policy/stance inference, calibrated uncertainty | **WITHHELD** |
| Legacy v1 original-P2 analytical export; public browser or research publication | **WITHHELD** |

No original UN PDF, Harvard speech, source-bearing country-year row, human speaker identity, 64-D vector, private comparison ledger, person match, evaluation-lock record or private decryption key is included in this public PR. Only code, synthetic tests and aggregate numerical receipts are versioned. All **37 reserved October 5–6, 2026 meeting transcripts remain unopened**. W4 source/method PR #18 stays independent and unmerged. The separately versioned private P2 source-inventory companion remains the authoritative missingness ledger until public upstream certification.

**Follow-up scientific design:** freeze a fresh full-coverage 2016–2019 reference in a separate experiment, extend years or independent repeated intervention opportunities, model annual shocks and selection explicitly, and calibrate candidate multiway/serial-dependence estimators against held-out real original-source samples and simulated designs. Do not infer that simple source expansion by itself removes confounding.
