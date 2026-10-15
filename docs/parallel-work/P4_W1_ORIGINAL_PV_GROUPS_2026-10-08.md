# P4 — Source-dependent historical W1 preflight, real original-PV metadata

**Date:** 8 October 2026. **Status:** independent real historical-source *metadata* audit PASS; synthetic W1 grouping/contract tests PASS; raw Harvard v14 text and native W1 empirical fitting WITHHELD. This is a coordinator-only engineering checkpoint, separate from any scientific or public research release.

## Actual private source evidence

The P3 owner-supplied private 792-cell inventory was independently audited against all **63 original UN-PV PDF SHA-256 bytes**, checking the exact PDF source identity for each of its 523 original-PV corroborated country-year cells and recomputing source-group and year coverage. Two fully independent local reruns produced identical public-safe aggregate SHA-256 `72189c9684fe2b2cf97a229d66d08ebeb103ade9059514910d441a1e6fc0da53`. A separate **private** 55-original-PV leave-one-group-out ledger and readable method report were delivered to the owner, not committed.

| Scope | Source-corroborated | Date-corroborated |
| --- | ---: | ---: |
| Country-year observation cells | **523** | **520** |
| Distinct original-PV meeting documents | **55** | **55** |
| Largest original-PV source block | 16 | 16 |
| Within-original-PV observation-pair fraction | **1.8300%** | **1.8312%** |
| Leave-one-PV coverage opportunities | **55** | **55** |
| Private PV-group coverage checks | **55/55 PASS** | **55/55 PASS** |

The full inventory retains **99 recorded affiliations × 8 years = 792** year opportunities: 520 corroborated and date-known, three original-PV-corroborated but without independently verified event dates, and 269 original-source-unverified (not no-speech) cells. Annual source-corroboration ranges from **53** to **83** country-year cells, so original-PV risk-stratified acquisition produces substantial year coverage imbalance.

## Why current affiliation resampling cannot work

Existing W1 `research/validation_framework/frame.cjs` uses transitive union of observations that share **recorded affiliation OR source-family** for affiliation-group resampling. The private P3 metadata, independently checked in an offline Python union-find implementation using the same rule, form **one single connected component spanning all 520 date-verified observations**. A *single* transitive block fails the W1 rule requiring at least three independent groups and **must be skipped**, not retuned to manufacture apparent uncertainty.

In contrast, W1 whole-meeting grouping is 55 original-PV source blocks and permits meaningful **descriptive coverage and leave-one-meeting-out sensitivity**. These are not 55 statistically independent speeches, and year-level common shocks and purposive source selection remain unmodeled. No inferential bootstrap confidence intervals, statistical source-group exchangeability, significance tests or political alignment claims are warranted.

## Native W1 engineering API used without changing it

New coordinator implementation `research/integration/p4_historical_w1_preflight.cjs` validates a private `un.w1.p3.longitudinal-source-inventory.v1` **full 792-row original inventory** and invokes the *unchanged* W1 `unionGroups`, `schedule` and `auditSources` APIs. It preserves original meeting/source-family identities, source/text SHA types, year dates and all three original missingness states, and exports **only aggregate** diagnostics. It deliberately does **not** turn archived Harvard-hash rows into a source-authenticated W1 `un.source-validation.frame.v1`, fit any model, issue a `un.parallel-analysis.v1` envelope or upload private rows to CI.

`research/integration/test_p4_historical_w1_preflight.cjs` uses 99 *fictional* affiliations across eight years with a known 792/523/520/3/269 source/missingness inventory and 55 invented original-PV groups. **10/10** synthetic positive/corruption/false-authentication and W1 native-grouping tests passed on CI; merged W1 source-aware `test_framework.cjs` **20/20** passed. The test explicitly refuses unknown native upstream source schemas; no source-safety change is requested to the accepted W1 validator.

**Actual private source-data execution and native W1 execution are distinct:** the real 792/520 private grouping, PDFs, year-missingness and 55-source leave-one-out checks were independently run locally in Python; native W1 source-group functions were executed on corresponding fictional structures in GitHub CI. **W1 native grouping on the actual private historical input remains NOT RUN in this checkpoint**. This separation prevents synthetic CI from being described as empirical model validation.

## Next empirical prerequisites

1. Recover the **exact Harvard v14 original tar**; the Harvard API returned HTTP 400. The GitLab/R `text2map.corpora` version and independent websites are *repackagings*, not automatically the pinned original. Compare per-file SHA-256 before accepting any alternative. Recompute full original Harvard speech/PV seven-shingle/decile/beginning/ending comparisons from both original texts; previous 840 strong classifications have only been rechecked from archived scores.
2. Resolve three dated-original-source disagreements; independently authenticate source-delivered speaker role and speech spans before any person-specific repeated panel.
3. Approve a **distinct historical-source upstream contract**: native W1 currently requires recognized source schema, maximum 600 fit rows, source event dates and actual text identity. Retain all 792 country-year inventory rows separately; no silent 272-cell deletion or relabeling as availability-zero. Do not misrepresent a historical PV ledger as `un.review.v1` or `un.passage-corpus.v1` until its complete authoritative source contract is actually constructed.
4. Validate the raw original Harvard text SHA and one fixed training-only high-dimensional feature basis before declaring the 520 subset analytically eligible. Only then assess W1 whole-meeting/year grouped *model stability*, and only after independent inference/calibration gates consider W4 descriptive trajectories. The W1 affiliation-group policy should continue to skip on this actual giant component.

**Frozen holdout:** the 37 Oct 5–6 2026 reserved meeting transcripts remain unopened; the evaluation lock, 24 completed owner decisions, D1 O1–O5, original source hashes, W4 worker PR #18, website and research browser are unchanged. No public country-level real-world output or statistical publication authorized.
