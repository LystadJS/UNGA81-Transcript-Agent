# W4 meeting- and year-dependent uncertainty audit — 8 October 2026

**Bottom line:** **79 of 79 deterministic source-deletion sensitivity checks completed** on the authorized private 99-affiliation, 523-original-PV-corroborated speech panel. Meeting deletions have smaller effects on the summary than year deletions, but those perturbations remove different numbers of speeches. **No calibrated confidence interval, p-value, independent-source bootstrap, historical population claim or diplomatic political-movement inference is justified.** Companion [aggregate receipt](W4_MEETING_YEAR_DEPENDENCE_AGGREGATE_2026-10-08.json) is public-safe; 792 source-linked inventory rows, 523×64 frozen vectors and original meeting-specific results remain private.

## Statistical estimands and observation units

Using the **unchanged** L2-normalized 64-dimensional reference-trained lexical representation, define a recorded country-affiliation average vector in each period. Reference (2016–2019) averages are based only on original-PV-corroborated speeches from that interval; comparison (2020–2023) observations are projected with the **same** 2016–2019 fitted vocabulary, IDF and SVD checkpoint. The two descriptive statistics are (1) **mean within-affiliation Euclidean period distance** and (2) **norm of the common-affiliation mean displacement vector**. All 99 affiliations contribute equally once in each period, with available source meetings contributing to actor means. There are **252 reference + 271 comparison = 523** verified observations and **144 reference + 125 comparison = 269** unverified cells.

This is a nonrandom *verified-source subset*, not a 193-member-state census; its coverage varies from 53 to 83 verified speeches by calendar year. The 269 source-unverified cells are never imputed as speech nonparticipation, zero mentions, vectors or cluster abstention. No individually verified repeated people are implied by national affiliations.

## Dependence and resampling decision

The observed provenance links **55 actual UN meeting sources** (nested within 2016–2023 years) and **99 countries recurring across multiple meeting/year blocks**. The actor–meeting bipartite source graph has **one connected component containing 154 actors-plus-meetings**, not 55 or 99 exchangeable independent observational blocks. Original PV meeting families are not independently paired across the two comparison periods. With **only four calendar years per era**, a year-cluster sandwich variance, iid resampling of meetings, resampling individual country speeches, or a standard asymptotic two-way cluster-robust confidence interval is not justified. The ordinary W4 paired-family bootstrap remains **withheld (zero attempted draws)**.

To study sensitivity without making those independence assumptions, we deliberately omit:
- **55 whole UN meetings**, one at a time, keeping every other meeting's source-linked observations intact.
- **8 whole calendar years**, deleting every speech/meeting in that year, holding the fitted representation fixed.
- **16 paired year deletions**, each deleting one of four years from each era, also holding the representation fixed.

Each scenario recomputes the two period means on the *same 99 matched affiliations*. Every attempt succeeded; no matched affiliations were lost. That common actor count makes the comparisons well defined, but a deleted year can reduce the number of available speeches in a country average. Hence the ranges below measure **sensitivity to selected source composition and reweighting**, not sampling variability for an invariant repeated-source estimand. Crucially, we did **not** retrain the 2016–2019 reference representation after deleting a year that originally helped fit it; training-year deletion results are explicitly *conditional on the stored fit*. A full leave-year-out feature refit would be a different experiment requiring aligned comparable bases.

## Observed numeric sensitivity

| Diagnostic (same 99 country affiliations) | Original | Leave one meeting (55) | Leave one year (8) | Leave one year per era (16) |
| --- | ---: | ---: | ---: | ---: |
| Mean within-country 64-D distance | **0.5398** | 0.5382–0.5538 | 0.5418–0.5991 | 0.5687–0.6239 |
| Norm of mean 64-D country shift | **0.2774** | 0.2754–0.2825 | 0.2743–0.2906 | 0.2738–0.2983 |
| Matched affiliations | 99 | 99 in every attempt | 99 in every attempt | 99 in every attempt |
| Attempted / completed | — | 55 / 55 | 8 / 8 | 16 / 16 |

The maximum absolute mean-within-country change is **0.0140** after omitting a whole meeting, **0.0593** after omitting one year, and **0.0841** after one-per-period year deletion. In particular, omitting **2019** gives 0.5991 versus 0.5398 without deletion; omitting **2023** gives 0.5418. These are contextual perturbations, not outlier declarations or inferential probabilities.

The comparison basis and time-varying source populations are still confounded by common-year agenda effects, meeting participation, unreviewed speechwriter/person changes, translation and meeting selection. All analyzed years stop at 2023; the previously identified 2024–2025 extraction/ASR discontinuity is not introduced.

## Backward-compatible data export gate

The new [source-inventory companion](SOURCE_INVENTORY_COMPANION_V1.md) preserves the full **792** expected country×year cells and distinguishes `available` (523) from `unverified` (269), with genuinely nullable date/source/meeting identifiers. Both 396-cell periods reconcile exactly and the new inventory digest is checked. It is a **separate** `un.parallel-source-inventory.v1` document; the existing `un.parallel-analysis.v1` 1.0.0 schema and its old-reader behavior are unmodified.

The original P2 source schema `un.p2.original-pv-reconciled.v1` is not approved in old v1. Thus real P2 input generates a **standalone private companion** with a refused legacy binding, rather than relabeling P2 records into old source types or fabricating dates. Even once a legitimate eligible-only v1 projection is approved, it would describe only the source-verified 523-row cohort, **never** imply that the 269 other rows are absent/zeros. Old consumer interoperability cannot be claimed for P2 until a separately reviewed source adapter exists.

## Replication and limits

- Research code: W4 `research/longitudinal/dependence_sensitivity.py` on unmerged PR #18, plus independent private conditional-source script and negative controls delivered with the authorized private package.
- Source companion: coordinator `docs/parallel-work/source-inventory-v1.cjs`, JSON Schema and synthetic tests, plus offline private exporter. The shared schema and all 37 held-out October 5–6, 2026 meeting sources remain unchanged.
- Executed private sensitivity: 55 meeting checks, 8 annual checks and 16 paired-year checks; baseline numerical values match W4's original 99-country private comparison within floating-point tolerance.
- Quality-control requirements: country/year unique source cells, source-hash consistency within meeting, genuinely nullable unknown source metadata, no vector fabrication, all period denominators, and explicit failures/release statuses. Independent v1 compatibility and new contract checks are separately run in CI.

**Empirical descriptive sensitivity assessment: completed for the nonrandom restricted pilot. Calibrated longitudinal uncertainty and source-population inference: withheld. Public/website/diplomatic release: withheld.**

**Next empirical design:** expand the source-verified, fixed-genre annual panel toward a near-complete per-year census, quantify selection and language/genre differences, obtain enough genuinely distinct time/meeting opportunities to justify a specified dependence model, and separately calibrate coverage by simulation and held-out original-record validation. Do not treat repeated actors, meeting/year blocks or source-linked passages as independent by fiat.