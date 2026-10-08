# Preregistered P2→W1 source authentication, PV expansion and uncertainty calibration

**Frozen before expanded original-PV files are examined: 8 October 2026.** Engineering research protocol, not preregistered political inference. No original/held-out transcripts, actor-level outputs, or historical source files in public GitHub.

## Population, source and sampling plan

- Historical scope: General Debate sessions 71–78, **2016–2023**. All 99 country affiliations of the existing frozen pilot and eight actual annual debate sessions remain fixed. **Do not use 2024–2025** mixed extraction/ASR or any October 5–6, 2026 reserved meeting.
- Initial evidence: 523 full-original-PV corroborated speeches and 269 unverified country×year cells; 55 original PV meetings. This is a selection-biased P2 pilot, not a sampled probability census.
- Expansion: take the *entire* 50-symbol union of **previously unacquired official UN PV meeting identifiers** found in those 269 unverified country-year cells' independent UN index rows. This is targeted recovery of missing source opportunities, **not a probability sample**. A sole cell without an UN index symbol stays unresolved. The 50 official meeting-symbol filenames are determined before download and may be committed as public source symbols without revealing country-linked results.
- Retrieve original full PDF bytes only from exact official UN document / UN Library URLs, decrypt **only privately**, compute SHA-256, total pages and extract all available text. A downloaded URL alone is not an attestation of full speech text or human identity.
- Per-cell promotion from `unverified` to `available` requires: (1) authentic official PV document symbol, byte hash and event date from official index/header; (2) exact underlying archived Harvard v14 speech-byte/hash correspondence; (3) full-speech normalized **seven-token-shingle coverage >=90%**, **at least 8/10 deciles >=80%**, and opening/ending corroboration; (4) recorded affiliation match (not a verified human). Ambiguous one-to-many/duplicate/translation records remain quarantined. Preserve all rejected and still unverified cells with explicit reason and a complete denominator ledger. The year×country candidate universe stays exactly **99×8 = 792**, with no imputed zeros.
- Report before/after year coverage, source-meeting coverage, newly promoted verified speech count, failure/unsupported PV counts, selection fraction, and changes to country-period inclusion thresholds (>=2 verified speeches in each four-year era). Refit of the existing 2016–2019 64-D representation is **not allowed** for an apples-to-apples expansion sensitivity: apply the original saved fitted vectorizer/SVD to newly verified 2016–2023 text, and report out-of-vocabulary sensitivity separately. The old pilot remains a frozen control.

## P2→W1 contract acceptance

Create a coordinator-owned, source-authenticated *private* adapter targeting W1's native `un.source-validation.frame.v1` structure with **explicit** P2 upstream provenance, without relabeling `un.p2.original-pv-reconciled.v1` as another source schema. Original W1 numerical kernels, source/time/sampling locks and `un.parallel-analysis.v1` remain unchanged. An additive W1 input recognition rule is permissible only with an explicit P2 attestation validator and new synthetic negative tests. **The legacy v1 interchange adapter must continue to refuse** unsupported original P2 schema; use the separate source-inventory companion for unverified cells.

A development row is eligible only after verifying original Harvard speech bytes, independent original PV PDF bytes and source URL/symbol, full-PV comparison evidence, documented date/role provenance, and selected-fit/parent/source population fingerprint. W1 model output must carry exact original source hash basis, selection SHA, meeting-group dependence, failed/skipped fits, and no private text in public exports. Tampering any hash, source modality, date, country/year key, training-selection manifest or full-match status must fail closed. A P2 source-row hash alone is not independent validation.

## Predeclared uncertainty assessment

### Actual historical data

- Descriptive estimands only: for each recorded country affiliation, equal-genre period average of **fixed 64-D normalized lexical vectors**, and (i) mean country-wise Euclidean distance between 2016–2019 and 2020–2023, (ii) length of their population-common centroid shift. Work with the **same** source-/date-verified 99-country universe; if expansion causes unequal eligibility, report both the original population and separately denominated wider sample; never silently substitute.
- Define source hierarchy: speech nested in PV meeting and year; observed countries recur across multiple meetings and years; year-wide shocks and shared agenda are common. `source_family_id` must map to the original PDF, not a fabricated independent speech. Meeting and country two-way cross-classification can form one connected graph: do **not** claim 99 independent-country replicates or 55 independent meetings.
- Run deterministic whole-meeting deletion, whole-year deletion, one-year-from-each-era deletion on **unchanged historical frozen basis**, retaining source groups; account for all attempts, changes in country matching, and missing source. These diagnostics are **sensitivity ranges, not confidence intervals**.
- Compare the old 523-row and expanded cohorts on their common source-backed cells and fixed 99-country population; distinguish coverage changes from substantive lexical movement. Report year-level contribution, source concentration and whether any year accounts for the apparent trend.
- No confidence interval/p-value for actual 2016–2023 results may be released until effective group/selection/exchangeability and coverage assumptions are independently established. With only **four years per era**, year-cluster asymptotics are not justified regardless of Monte Carlo performance.

### Synthetic calibration (no original text)

Freeze simulation before seeing expanded results. `R=600` Monte Carlo panels, seed **20261008**, common **99 country affiliation×8 year** grid, actual privately audited source-meeting and original available/missing selection pattern (both old and expanded masks as separate strata), predeclared period effect **beta=0.20**, two sources of cross-classified dependence: country random intercept SD **0.40**, meeting-specific shock SD **0.12**, within-country/year speech residual SD **0.25**, and year shocks SD **0.20**; country intercept and year/meeting shocks are independent Gaussian.
1. **iid-year world:** independent N(0,0.20²) calendar-year effects. No claim that observed UN years satisfy this.
2. **serial-year world:** AR(1) Gaussian calendar shocks with correlation **rho=0.65** and marginal SD 0.20, plus fixed source/selection mask (no additional random missingness). The old and expanded masks are nonrandom, preserved from actual corpus opportunities; neither is called an ignorable missing-data process.

Compare **nominal 90%** confidence intervals for the known scalar additive beta on the first frozen reference-axis analogue:
- **Naive actor-paired t interval:** pooled country period-mean difference, Student t with degrees of freedom (country count−1), ignoring shared year/meeting shocks.
- **Whole-year Welch interval:** year-mean contrast, four years in each era, Satterthwaite degrees of freedom, including the per-year observation-mask differences; treats 8 actual years as if independent, invalid if AR1.
- **Within-era year-block bootstrap:** resample complete calendar-year blocks within each era, B=199 seeded draws, recomputing source/actor mean contrast, using percentile 5th–95th. If a draw leaves country-years with no measured speech in an era, record replicate failure and never silently change the matched population.
- Report 90% coverage over R true-known beta simulations, Monte Carlo standard error, median width, empty/failed replicates, and differences by old/expanded source-availability mask. **Do not tune algorithms or nominal level after seeing outcomes.**
- Decision: a scheme is *synthetically calibrated in the stated DGP* only if observed coverage is within +/-0.04 of nominal 0.90 **and** Wilson 95% coverage interval includes 0.90 with at least 570 evaluable simulations. This does **not** validate confidence intervals on real data; real-data inferential gate remains withheld. Undercoverage must be reported rather than disguised.

### Security and release

The source PDFs, full-PV text, original Harvard archive, country-level source identifiers, 523+ vector rows, speaker-matching evidence and any expanded per-country row-level results remain in approved private storage. Public GitHub may contain code, synthetic tests, this preregistration, aggregate numerical receipts and source-uncertainty limitations only. **No** 37 reserved October 5–6, 2026 meeting transcripts, original holdout metadata lock, D1 O1–O5 gates, source checksum originals or owner reviewer decisions may be accessed or modified.

Any unexecuted source validation, failed document download, Monte Carlo replicate or aborted fit must be counted, with reasons, **not reported as a pass**.
