# W1–W2 source-dependence and null-calibration requirements

**Decision date:** 13 October 2026. **Owner:** coordinator, with owner approval for any release or reserved-source use. **Status:** prospective, fail-closed *acceptance requirements*; **not a preregistered hypothesis test**, empirical evaluation authorization, validated null, or change to the frozen O1–O5/held-out protocol.

**Decision now: INFERENCE WITHHELD.** Merged PR #50 establishes source-bound W1 grouped hard-assignment and W2 *descriptive* coassignment/LOO/subsampling sensitivity (synthetic engineering). It does not prove that source meetings, speeches, affiliations, countries or years are independent, nor that nuisance-only structure has been eliminated. No country positions, coalitions, agreements, statistical nonrandomness or confidence intervals may be inferred from its results.

## 1. Scope and observation hierarchy

Define **one analysis population and one question at a time**, before touching any new evaluation corpus.

| Scope | Upstream state | Boundary |
| --- | --- | --- |
| UNGA81 October 2026 HLW development | Whole source meeting → original source segment → validated parent/speech (only where authenticated) → selected passage; recorded country affiliation is metadata | Development 1–4 October may be used only with its authorized original bytes; all **37 reserved 5–6 October meetings remain sealed** unless the owner separately authorizes a prospective evaluation |
| Historical P2/W4 General Debate 2016–2023 | Original Harvard **member bytes**, complete official UN PV PDF bytes, meeting/year and recorded affiliation → source-verification ledger → explicit W1 selected subset | Original country×year inventory and W1 fit population are **different denominators**. The accepted aggregate records 792 possible cells, 790 attested and 2 unverified, but a separately authenticated **actual original TAR member-to-claimed-row comparison** is required; PR #51 documents a prior caller-supplied-text acceptance weakness; evaluate its separate correction under its own acceptance process. Neither earlier aggregate acceptance nor an unmerged correction suffices for this gate |
| W1/W2 synthetic | Invented source IDs, text hashes, meetings, known latent/nuisance structure | Suitable for validating code and calibration proposals, never an empirical diplomatic sample |

A full meeting inventory is **not** a count of fitted observations. A missing UN transcript or a missing original text is **unknown**, not zero issue occurrence, nonparticipation, model abstention, or an excluded fitted passage. Source segment ≠ verified speech ≠ independently authenticated person ≠ recorded country affiliation. Avoid treating adjacent passages, duplicated source records, translated versions, speech families, or different W1 random seeds as independent replications.

## 2. Required source-and-dependence census (gate G01–G04)

Before any new confirmatory empirical W2 refitting or inferential testing, deliver a private, source-hash-verified *observation graph and coverage ledger*:

1. **Byte-to-row proof.** For every eligible text row, independently hash the actual original source bytes (UN PV PDF and, for historical P2, the precise original Harvard TAR member), record canonical extracted-text SHA and **hash basis** separately, confirm source URL/document symbol and true event date, exact member path and selected text, and resolve duplicate/translated/extracted modalities. A digest recomputed solely from user-supplied claimed text is not original-byte authentication. Incomplete and disputed rows remain quarantined.
2. **Inventory and selection.** Record inventory opportunities, verified available, verified-not-selected, selected eligible, excluded, not-collected, unavailable, unverified, model not fitted, assigned, noise/unassigned and fit failures **with noninterchangeable denominators**. Freeze all eligible IDs/text SHAs, representation/vocabulary/checkpoint IDs, selection digests, sampling frame, weights and transformations; use fixed original-source IDs, not row positions or display coordinates.
3. **Dependence edges.** Privately build a typed graph linking identical/near-duplicate text, raw PDFs, translations, source families, shared parents/speech, repeated recorded affiliation, independently verified recurring human only where established, meeting, session/date, year, language, agenda/genre/role and known source-modality or collection changes. Disclose components, edge types, group sizes, concentration, overlaps, cross-meeting family connections, unavailable lineage, and effective group opportunities, without releasing source-linked rows.
4. **Feasible resampling unit.** Test whether a proposed unit keeps every provenance-linked segment together. Report meeting-only, source-family closure, affiliation closure, meeting×year and cross-classified actor/year structures separately; do not assert that meeting or affiliation IDs are independent by definition. If one connected closure component contains most observations, cluster-bootstrap independence is **not identified** by counting nominal meetings or countries. W1's ≥3-group engineering minimum is **not** a minimum for statistical inference. If exchangeability or a generative dependence model cannot be justified and calibrated, group omissions stay **descriptive only**.

For longitudinal data, explicitly retain country repetition across years, common agenda shocks, within-year meetings, calendar-year serial correlation and nonrandom attendance. Prior W4/P2 source audits found four years per comparison era, and serial-year synthetic intervals undercovered: do **not** substitute ordinary year-cluster sandwich SEs, naive affiliation resampling, 55/105 nominal meetings, or W1 leave-group-out percentiles for calibrated inference. A wider historical corpus or a demonstrated finite-sample dependence model is required for historical population inference. An inferred single connected dependence graph can still support sensitivity analyses; it cannot by itself supply independent draws.

## 3. Specify the inferential target before calibration (G05–G06)

**Candidate null family (not yet preregistered):**

> Conditional on the declared source inventory/selection, meeting/year and affiliation dependencies, language/genre/role/agenda, passage length, token marginals, source-specific boilerplate and verified duplicate structure, there is **no additional cross-source latent-discourse association** detectable by the frozen family-balanced W2 procedure.

This is a null about **language structure beyond a chosen nuisance model**, not a null that country positions are equal, actors did not coordinate, votes have no effect, or that all observed words are independent. Failing to reject is not evidence of no latent structure.

Freeze a **single primary global statistic** and its direction, unit/weighting, eligible cross-source pairs, minimum effective pair opportunities, cluster/threshold definition and rejection rule *before further real-data analysis*. A group-pair-balanced fraction of adequately covered cross-source pairs with stable consensus is a possible design **to be assessed on synthetic data**, not an approved fixed test today. Any inspected alternatives (k, preprocessing, representation, method families, coassignment or coverage cutoffs, groupings, source exclusions, semantic encoders, cluster-stability statistics and subgroup searches) must be included in the selection/multiplicity correction, or selected only on disjoint design data. Never call W2's existing conditional coassignment proportion a p-value, posterior probability or government agreement probability.

Keep four distinct outputs:

- **W1 numerical stability:** ARI/AMI, refit failures, fitted dimension/version and group omission diagnostics.
- **W2 descriptive cross-method agreement:** pair coassignment numerator/assigned-both denominator plus full *planned* denominator, family/seed/configuration audit and missing/noise/failed-fit ledgers.
- **Dependence sensitivity:** distinct whole-source LOO and without-replacement subgroup deletion outcomes, including non-delivery; these are not a bootstrap or confidence intervals.
- **Inferential null evidence:** only after an independently accepted, calibrated sampling/reference design that refits the *entire frozen search pipeline*. Until then the value, interval and significance fields are **null/withheld**.

## 4. Null reference generator requirements (G07)

**Randomly permuting rows of a text matrix is not a cluster-significance test.** Reordering rows leaves most clustering geometry intact; it does not destroy latent dependence or simulate a defensible null.

A proposed conditional or parametric nuisance reference must be **fitted only on the declared design population**, not use sealed evaluation labels, outcomes or source text. Document, for each null draw, which joint features are *held fixed*, *estimated* and *randomized*: inventory attendance/missing-source mask; original-group sizes and speaker/affiliation recurrence; meeting/year effects including annual autocorrelation; length/token-frequency/language; agenda/genre/role; duplicates/boilerplate and extraction modality. Construct negative controls in which cross-source clusters are absent but these nuisance patterns are present, and positive controls containing a planted cross-source latent structure **independent of nuisance-only structure**.

Minimum adversarial regimes to freeze:

- N1: independent source groups, varying passage length/token prevalence, no planted global clusters.
- N2: dominant meeting/agenda/genre/role lexical blocks, duplicated parent/source content, highly unequal group sizes.
- N3: cross-classified recurring affiliation × meeting and shared source-family edges, including one large connected component.
- N4: historical repeated affiliation + meeting nested in year with iid and **serially correlated** year shocks and nonrandom year/country/source availability.
- P1/P2: known sparse/overlapping latent structure, differing representations, cluster splits/merges and high HDBSCAN noise.

Each nuisance generator must reproduce *predeclared* real-source nuisance summaries within frozen tolerances **without preserving or introducing the proposed additional latent signal**. Diagnose whether it destroys source-independent signal while keeping dependence; compare at least two substantively different defensible null families where feasible. A nuisance mechanism that cannot be empirically justified or calibrated must result in **WITHHELD**, not a convenient alternative permutation. Nonindependent simulation draws or data-trained nuisance parameters require their own estimation-uncertainty/coverage assessment.

## 5. Full-pipeline null calibration and multiplicity (G08–G10)

Freeze a design document and source-safe numerical implementation (code SHA, deterministic seeds, input/source hash/version, group-selection algorithm, representation and parameter grid, baseline/negative controls, excluded reasons, runtime cap, memory cap, failure policy) **before the proposed inference is attempted**. It cannot retrospectively preregister the already inspected 2026 development or historical pilot results.

1. **Complete refitting under each reference draw.** Recreate permitted source/nuisance structure, tokenize and fit the declared original representation, fit the same k-means/PAM/Ward/HDBSCAN/GMM configurations and relevant grouped refits with matching attempted/skipped/failed logic, assign/source-join all eligible rows, recompute family-balanced W2 pair opportunities, stable groups and **the full selection/max-statistic rule**. Null draws must not be compared against a fixed observed latent fit when the declared target includes refitting uncertainty.
2. **Global multiplicity:** default proposed inferential target is **family-wise error ≤0.05** across all searched model settings, thresholds, representation families, source-group choices, hypothesized groups and examined cross-source subgroups, by a max-statistic/reference procedure or genuinely locked independent confirmation. A global finding does **not** automatically validate any individual observation pair. A separate adjustment and source-linked review protocol is required for pair/group claims.
3. **Monte Carlo p-value:** only where an exchangeability-valid or separately calibrated Monte Carlo reference is justified, use at least the positive corrected tail count \((1+\#\{T_b\ge T_{\mathrm{obs}}\})/(B+1)\). **B ≥1,999** final reference draws are a proposed minimum (finer grid needed for more stringent multiplicity); report Monte Carlo standard error and seeds. This arithmetic alone does **not** make a misspecified nuisance generator exact.
4. **Outer calibration (known truth):** prospective minimum **1,000 independent synthetic null worlds per preregistered dependence/nuisance regime**, with final reference generation budget recorded separately from outer worlds. For proposed nominal 0.05 FWER, require the **one-sided 95% binomial/Wilson upper bound on realized false discoveries ≤0.075 in every prespecified null regime** (a finite-Monte-Carlo feasibility screen, not a guarantee of real-world calibration). Report the numerator, denominator, uncertainty and non-delivery; never drop failed simulations or report only delivered/most favorable regimes. Increase repetitions or withhold when Monte Carlo precision is inadequate.
5. **Power and calibration honesty:** report known-structure retrieval/power against a **predeclared synthetic minimum detectable effect**; report family-weight/density/noise sensitivity, type-I rejection conditional on source group count and missingness strata, and whether negative nuisance controls create stable spurious clusters. No universal best-model score. Do not set thresholds by looking at the future evaluation set.
6. **Failure controls:** missing sources remain unknown; zero assigned-both pairs yield a null association, not 0; nonconverged fits and skipped source-block refits contribute to *planned* denominators; generator failures, wrong source hashes, unsupported representation versions, insufficient groups and numerical resource/time limits yield an explicit failed/withheld decision, never an automatic fallback.

These numerical budgets and alpha criteria are **prospective requirements, not completed tests**. If computational feasibility, nuisance calibration, exchangeability or effective independent group count fails, do not relax the rule retroactively and do not publish a p-value or CI.

## 6. Independent evaluation and interpretation (G11–G13)

- **No source leak:** design/evaluation ID and original-content/source-family graph overlap must be explicitly tested, not inferred from nonoverlapping filenames, meeting dates or country affiliations. Any overlapping source family, near duplicate, identity or pooled vocabulary/IDF training crossing a claimed independent evaluation boundary must be reconciled or disqualify that independence claim. A historical analysis must also block future-year vocabulary fitting from contaminating earlier years.
- **No unapproved holdout:** the **37 October 5–6, 2026 reserved transcripts remain unopened**. Separate owner authorization and a dated frozen hypothesis, split, code, source-validation and stopping rule are required before any evaluation run on them. Prospective independent groups/years may be necessary if the already-inspected development set is exhausted.
- **Empirical execution:** only authenticated eligible original-byte inputs may be fitted privately, after gates G01–G10 have verifiable accepted receipts. Results and row-level source-linked evidence remain private until a separate interpretation/privacy/publication decision. The descriptive 2016–2023 P2/W4 population remains a different study; passing a 2026 nuisance test does not validate multi-year uncertainty or historical political movement.
- **Interpretation:** even valid rejection establishes only excess source-conditioned *linguistic* structure under the specified null. It does not authenticate speakers or governments, or identify policy agreement, coalitions, votes, causal influence, diffusion or political positions.
- **Release:** a human coordinator/owner approval, separate source-level scientific review and publication gate is required beyond any positive synthetic CI. Do not modify the original W1/W2 evaluation gates, source checksums, P2 original files, D1 O1–O5, public browser release manifest or portfolio mirror as part of this requirements record.

## 7. Machine-readable fail-closed status

Companion: **w1-w2-inference-readiness.v1.json**, tested by **test-w1-w2-inference-readiness.cjs**. It records 13 gate IDs with owner, dependencies, status, evidence identity and required acceptance criteria. As of 13 October 2026, every *inferential* gate is **NOT_RUN**, proposal_frozen is false, inferential_eligible is false, empirical_evaluation_authorized is false and public_release_eligible is false.

**Gate categories:** G01 source bytes; G02 inventory/selection; G03 dependence graph; G04 feasible sampling assumptions; G05 locked estimand/statistic; G06 methods/multiplicity; G07 nuisance generator; G08 complete-pipeline null; G09 Monte Carlo error calibration; G10 positive/negative/nuisance controls; G11 independent holdout and leakage; G12 provenance/reproducibility/interpretation; G13 explicit publication authorization.

A gate may change to PASS only with a **specific new report hash/URI, reviewer and decision date**, and all prerequisites; the code rejects undocumented self-certification or publishing an unvalidated model. A synthetic engineering PASS in PR #50 is *not* an inferential PASS. This is a requirements register, **not** a frozen new inferential protocol. Any final preregistration requires a distinct dated document/commit approved **before testing on its new target data**.

## References for method design (not evidence of these gates passing)

- Christian Hennig (2007), *Cluster-wise assessment of cluster stability*, Computational Statistics & Data Analysis, DOI: https://doi.org/10.1016/j.csda.2006.11.025. Stability can result from methodological inflexibility; not a significance test.
- Cameron, Gelbach & Miller (2011), *Robust Inference With Multiway Clustering*, Journal of Business & Economic Statistics, DOI: https://doi.org/10.1198/jbes.2010.07136. Describes multiway variance procedures, not finite-sample validation with the project's small/connected clusters.
- MacKinnon & Webb (2018), *The wild bootstrap for few (treated) clusters*, The Econometrics Journal, DOI: https://doi.org/10.1111/ectj.12107. Few-cluster procedures need design-specific checks; not automatic validation for transcript data.
- Phipson & Smyth (2010), *Permutation P-values Should Never Be Zero*, Statistical Applications in Genetics and Molecular Biology, DOI: https://doi.org/10.2202/1544-6115.1585. Correct Monte Carlo tail accounting does not rescue an invalid reference generator.

**Next binding action:** independent statistical review of this requirements proposal, then a new, prospective **locked null-design document and synthetic-only calibration implementation**. None of the empirical or publication gates is satisfied by a proposal's merge.
