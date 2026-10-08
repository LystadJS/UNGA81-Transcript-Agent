# W4 longitudinal data: acquisition and validation plan

**Coordinator research specification — 8 October 2026.**
**Status:** proposed acquisition and acceptance protocol; NOT a completed dataset, real-data experiment, statistical validation, source authorization or publication approval. The executable W4 work remains in PR #18. This specification does not change its code, any evaluation lock, or a release gate.

## 1. Research questions, units and adequacy

1. **Country-represented discourse over time (first priority).** One independently identified General Debate national address per represented state and annual UNGA session, with exact delivered-text version, source and speaker metadata. The repeated analytical actor is the **recorded country affiliation**, not the person, government policy position or an individually authenticated government decision.
2. **Person-level change (secondary).** Same verified human speaker across multiple time points. Never promote a country-year label or name spelling match into a repeated-person identity.
3. **Comparable agenda/venue change (secondary).** Repeated speeches or source segments from a named committee/agenda/genre series across annual or shorter periods; analyze separate strata before any pooled model.
4. **Cluster correspondence (only after W1/W2/W3 source and fit validation).** Original fit settings, assignment status, representation and population must remain linked. Cluster ordinal labels are arbitrary; apparent splits and merges are descriptive.

**Pilot target (planning value, not sufficient sample size):** 30–50 region/language/source-diverse countries over four available General Debate sessions. Include cases with absences, language changes, translated statements and speaker turnover.

**Primary research target:** General Debate sessions 2016–2025, supplemented by 2026 only after primary-source and text-version checks. Inventory the member-state universe for each session rather than assuming 193 observations occurred each year. Seek 8 or more genuinely observed annual periods for reported country trajectories; do not delete incomplete countries silently. An 11-year sequence supports richer description but does not automatically yield a calibrated change-point test. A single speech per country per year is **not replicated within-country evidence**; do not present passage-level variation as independent speech sampling.

For actor-specific uncertainty rather than only cross-country descriptive sensitivity, collect genuinely distinct comparable interventions or meeting opportunities within periods. A useful expansion target is three or more eligible meetings per actor-period in a fixed issue/genre, *where they actually exist*; actual dependence must be established, and missing cells remain missing. There is no universal numerical threshold establishing scientific sufficiency.

## 2. Mandatory source and observation tables

These are **private, versioned** input tables; they are not to be committed with original text, source-linked row-level analysis or raw embeddings to public GitHub.

| Dataset | Minimum fields | Validation invariant |
| --- | --- | --- |
| Period and expected-inventory table | period_id, actual start/end, session, country/representative registry, expected speech/meeting, observed/absent/unavailable/revised/excluded reason | An absent or uncollected speech is never a zero vector, a non-mention, or a real null source hash |
| Canonical sources table | original URL and UN Digital Library record/document symbol; event date and first verified availability; delivered/PV/prepared/ASR text kind; original language, analyzed language, translation; original-byte SHA-256 and hash basis; canonical-text SHA-256; source version, duplicate/translation family and license | Reconcile raw bytes versus canonical text explicitly; preserve superseded versions and independent extraction provenance |
| Speaker/actor table | speaker name as recorded, authority record if available, independently confirmed speaker_id, recorded role, affiliation, country code as of event, actor_kind (verified_speaker/recorded_affiliation/unknown), decision evidence | Never infer a verified speech from a verified speaker; no country-to-person joins without evidence |
| Observation table | stable observation and parent IDs, verified meeting ID, genre/agenda, country-year/actor trajectory ID, source family ID, source/date/split, review/availability status, Unicode code-point offsets for passages when verified | Unique source ID + original text digest; passages must remain nested in parents and meetings |
| Representation and map ledger | representation ID/version/fingerprint, original frozen vocabulary/IDF or embedding checkpoint and preprocessing, feature dimension, training period/selection hash, model artifact digest, map fitting policy/fit ID, display error | Identical frozen high-dimensional representation across compared dates; no vocabulary/checkpoint refit labelled as comparable geometry |
| Fit and failure ledger | imported partition fit ID, method/settings digest, training selection hash, seed, assignments including 0/noise and null/not-fitted, attempted/successful/failed/skipped fits, population denominators | Fit identity is **not** display-map identity; do not omit failures or alter eligible-population counts |

Where source records truly have not been obtained, store unknown hashes and IDs as **null plus a missing reason** in the source inventory; do not invent hashes to satisfy the current implementation. Recorded country affiliation and individual verified speaker are different units. Meeting IDs are official slugs/symbols, not fabricated from titles. Period dates reflect actual event dates, not acquisition timestamps.

## 3. Ranked acquisition pathways

### A. Main path: existing General Debate corpus plus official UN source reconciliation

1. Acquire and pin the *specific* version of the Harvard Dataverse **United Nations General Debate Corpus** (DOI 10.7910/DVN/0TJX8Y). A third-party package documentation reports a March 2026 v14 release covering 1946–2025; verify the actual archive version, manifest, missing years, per-year countries and raw text before relying on that claim. Never treat cleaned corpus rows as independently verified UN source bytes.
2. Obtain the UN Dag Hammarskjöld Library General Debate speaker/meeting index, Digital Library record 4067189; its January 2026 CSV describes the **1st–79th sessions (through 2024)**. Treat this as authoritative metadata, not as a full-text corpus. Match on session, country/entity and official meeting/speech record, then cross-check speaker/role where recorded.
3. Build a full expected country-session grid. Investigate duplicate entries, absent sessions, state renamings and membership, historical ISO3 aliases, national delegation substitutions, observers, multiple/continued statements and mistaken merges; count each separately.
4. For a stratified sample and every identified mismatch, compare English or original-language corpus text with the official **A/{session}/PV.{meeting}** General Assembly verbatim record and original General Debate statement where available. Record that PVs are edited records of what was actually delivered, whereas prepared statement PDFs can differ from the oral delivery. Flag differences rather than silently replacing text.
5. Freeze an audited source release (manifest, original text hashes, accepted errors, provenance and explicit absent records) before any W4 fitting. Keep original text and person-linked review privately; publish only code, summary statistics and synthetic fixtures.

**Strength:** Near-complete comparable annual country-level genre with substantial history and available source metadata.
**Limit:** One annual speech per country; year-wide agenda shocks, speechwriter turnover, language/translation effects and changing state representation can still explain differences. No actor-specific confidence interval follows from a single address.

Sources:
- https://digitallibrary.un.org/record/4067189/
- https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/0TJX8Y
- https://www.ungdc.bham.ac.uk/
- https://www.un.org/dgacm/en/content/verbatim-reporting-service

### B. Close 2025–2026 source gaps and audit format differences

Use https://gadebate.un.org/en for 80th/81st debate archive links and submitted country PDFs; retrieve official PV records through https://documents.un.org/ and https://digitallibrary.un.org/ as released. The official 81st General Debate occurred 22–28 September 2026. Maintain an explicit provisional/source-version flag where an official PV is not yet published. Use https://transcripts.un.org/en/about and its meeting JSON metadata only as a **quarantined secondary discovery/cross-check route**: its automatic transcripts and speaker attribution are explicitly unofficial and error-prone; do not silently join ASR and official English translations as a uniform text series.

### C. Higher-frequency matched-agenda secondary panels

Build a distinct repeated series of **General Assembly First/Third Committee debates** for stable subjects, or Security Council public PV interventions for repeat country/role/agenda combinations. Verify actual speech coverage, speaker attribution and stable document type. The peer-reviewed/public UNSC debates 1995–2017 dataset (65,393 interventions reported) is a candidate seed/index, **not** a substitute for cross-checking PV originals or extending verified coverage. Do not mix PV full text with SR summaries in one feature distribution. Different rotating delegations and changing Security Council participation must be modeled as exposure/roster effects, not inferred change.

**Strength:** Multiple legitimately distinct meeting opportunities within periods, actor/source-level dependence diagnostics, potential shorter-period series.
**Limit:** Strong selection by who speaks on an agenda, meeting-wide dependence, nonrandom membership and uneven representation; substantially more validation work than A.

### D. Institutional/bulk-access escalation

For bulk Digital Library export or unavailable official files, approach the Dag Hammarskjöld Library and appropriate UN documentation units; ask for a legally suitable export of source metadata, symbols, stable record IDs and approved download pathways. The Digital Library export guidance states logged-in users may need library-staff assistance for exports over 100 records. Respect access controls, APIs, rate limits and license terms; do not bypass anti-bot checks or publish raw source text merely because research access succeeded.

Useful documentation:
- https://digitallibrary.un.org/help/search-engine-api?ln=en
- https://www.un.org/en/node/75080
- https://digitallibrary.un.org/pages/?page=newVersion_02

## 4. Acceptance gates and independent audit

| Gate | Acceptance evidence | If not satisfied |
| --- | --- | --- |
| Inventory completeness | Per-year expected versus collected versus verified versus unavailable and excluded counts; named sources and duplicate versions, with denominators | No unrestricted population claims |
| Independent source linkage | Originals and metadata independently cross-checked against official UN records, real raw-byte/text hashes, adjudicated mismatches | No empirical ingest into W4 |
| Text and actor QA | Stratified dual inspection (starting target: 10% or at least 100 texts, subject to actual frame size), oversample languages/OCR/ASR/conflicts, resolve major inconsistencies, report error rates and intervals without claiming a probability sample when purposive | Withhold uncertain records; no government-person position inference |
| Time and representation comparability | No overlapping periods, no invented daily points; one frozen lexical/semantic basis and training cutoff, document/translation type stratified | Withhold noncomparable period contrasts |
| Sampling and dependence | Group by real source meeting, parent, actor trajectory, and year; test source/genre/agenda concentration, duplicated texts and common year-wide shocks | Sensitivity-only; no calibrated inference |
| Alignment and correspondence | Predeclared independent full-rank stable anchors, residual and conditioning diagnostics, same eligible fit identities, noise/null ledger | Withhold refit display arrows and unsupported matches |
| Robustness and negatives | Roster-only placebo, missing-meeting perturbation, speaker turnover, translated/original-language sensitivity, altered vocabulary/embedding basis, source-version perturbations, agenda/year effects, document-length adjustment | No accepted substantive movement |
| Statistical eligibility | Design-specific sampling assumption, effective independent units, power/sensitivity simulation, leakage-free temporal evaluation and uncertainty calibration | Descriptive outputs only |
| Publication eligibility | Source rights and provenance, privacy and row-level restrictions, reproducible approved results, human interpretation review, no altered reserved protocol or D1 release gate | No public research finding or UI promotion |

The existing W4 source-family bootstrap requires at least **six** complete repeated source families to run, but that is a **code threshold only**, not independent-source proof or statistical power. If country trajectories are resampled, geographic bloc/year dependence remains; meeting/genre-level variation cannot be manufactured by splitting one source into passages. For global year effects, report matched-country changes both raw and after appropriate leave-one-country-out contemporaneous agenda references; treat adjustments as specified sensitivity analyses, not independent political attribution.

## 5. Required changes to W4 before empirical ingestion

1. **True missingness compatibility:** the present W4 validator requires non-null source/text hashes and meeting ID even when source status is unavailable/inventory-failed. Implement separate expected-inventory/missing-source rows accepting **null** original hashes/meeting IDs with explicit reason and enough inventory lineage; never generate placeholder hashes or fictitious official meetings. Also handle genuinely empty periods with a withheld diagnostic, not invented observations.
2. **Different grouping identities:** retain source/duplicate family, speaker/person identity, country trajectory, actual meeting and period as distinct fields. Current source-family bootstrap may not have independent source families in an annual country panel; do not relabel countries as independent documents merely to clear its six-group code threshold.
3. **Source-authenticated ingestion:** require a verified W1 read-only adapter joining original source/schema + original ID + original hash and compatible units. The current W4 synthetic validator enforces shapes, not independent authenticity of claimed original bytes or speaker identity.
4. **Fit/population consistency:** the importing method must provide verified original cluster-fit/settings/training population and complete failure ledger. W4's imported labels currently record zero new attempts, not all upstream attempted/failed fits.
5. **Empirical study design:** predeclare analytic years, same-genre comparisons, reference-fit policy, anchors, checks for reference-versus-refit discrepancy, year/agenda effects, duplicate rules, block-resampling, and allowable public interpretation before looking at full results.
6. **Capacity check:** W4 currently caps the panel at 20,000 observation rows and frozen feature dimension at 1,024. Whole country-year panels fit more readily than fine-grained passage panels; establish batch/aggregation or tested resource changes before large committee-scale work.

## 6. Sequence and artifacts

| Phase | Deliverable | Exit rule |
| --- | --- | --- |
| P0. Inventory | Country × annual session expected/observed grid, source and rights register, first missingness report | All cells accounted for without fabricated absence |
| P1. Historical acquisition | Frozen UNGDC version, UN speaker index and primary document-symbol crosswalk; separate 2025/2026 supplements | Source identity/version and duplicate decisions auditable |
| P2. Independent QA | Stratified official-PV/source comparisons, speaker/affiliation audit, quality/errors ledger, missingness audit | Critical errors resolved or cases explicitly withheld |
| P3. Representation and compatibility | One pinned high-dimensional basis, private W1 source contract, corrected W4 missingness adapter, approved time/genre/weighting plan | Comparable source-bound panel generated with no reserved data |
| P4. Empirical diagnostic run | Pinned W4 comparison/exports; matched/roster change, anchor/stress checks, family/meeting sensitivity and negative controls | Descriptive readiness decision, with failures and non-delivery |
| P5. Scientific eligibility | Repeated-meeting extension, dependence and power/coverage calibration, uncertainty and independent validation | Explicit empirical versus inferential versus publication decisions, never automatic promotion |

**Proposed output names (private unless aggregate text-free):** source_inventory.csv, source_registry.csv, actor_authority.csv, observation_frame.csv, crosswalk_exceptions.csv, panel_missingness.csv, representation_manifest.json, reviewed_audit.csv, negative_controls.json and w4_acceptance_report.json. Public GitHub accepts code, synthetic fixtures, blank schemas and aggregate numerical receipts only. The local original text, embeddings and row-level sensitive/source-linked results must stay in authorized private storage.

**Frozen exclusions:** Do not open, download, parse, score or inspect any of the 37 reserved October 5–6, 2026 meeting transcripts. This data-acquisition plan targets General Debate years and separately authorized non-reserved meetings; it does not waive the held-out lock or alter O1–O5. PR #18 is not merged or automatically publishable by adoption of this plan.
