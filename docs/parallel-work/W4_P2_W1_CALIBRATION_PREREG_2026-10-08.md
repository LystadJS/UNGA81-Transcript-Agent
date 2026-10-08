# W4 P2 → W1 authenticated adapter and historical uncertainty calibration protocol

**Predeclared on 8 October 2026, before running the new simulation.**  Historical source verification and uncertainty-calibration results must be reported separately.  The 37 reserved October 5–6, 2026 meeting transcripts remain unopened.

## A. Original-source validation and future acquisition

Start with existing independently corroborated Harvard v14 / UN official original PV 2016–2023 source sample: **523** source-verified country×session speeches from 55 source meetings, **269** unverified cells in an 8-year × 99-affiliation candidate panel.  Authenticate using both physical original PDF SHA-256 from 63-PV private archive, speech full-text digests, P2 crosswalk (country/year/meeting), source method, explicit date basis, and original cohort selection SHA.  A recorded country affiliation is not an individual speaker.  Build a private W1 frame **only for the 523 verified source rows**; retain 269 unverified observations in the separate coordinator `un.parallel-source-inventory.v1` sidecar.  Do not falsely promote this P2 schema into old `un.parallel-analysis.v1`; until a versioned W1 original-source adapter is formally accepted, fail closed at legacy interchange.

Expand original-PV verification through a **deterministic, frozen, risk-prioritized 38-meeting selection**: select up to five previously unverified GA PV meeting symbols per year, 2016–2023, ordered by the number of UN index speaker rows with that symbol, excluding the existing 63-PV sample and all 2026 material.  Source list stored in the coordinator branch separately.  Download only through normal public UN document interfaces; do not bypass controls.  Record bytes, SHA256, page count, source version, meeting date, text extraction quality.  Reconcile complete Harvard speech text to newly downloaded official PVs using the same preregistered 7-token/10-decile method and source-modality comparison.  New coverage is added only for source-, speech-, role- and date-verified rows, and any failures/non-deliveries are counted.  If the original bytes cannot be obtained, mark coverage expansion **NOT DELIVERED**, not verified.

## B. Target and dependence

Target statistic for empirical description is the 99-affiliation equal-weight mean within-affiliation 64-D difference between reference 2016–2019 and comparison 2020–2023, conditional on pinned 2016–2019 vocabulary, IDF and SVD.  This is not a political-movement estimand.  Its deletion sensitivities are not confidence intervals.  Meeting is nested within year; actors cross meetings and years; recorded 55-meeting/99-actor provenance graph is one connected component.  Only four years per era are observed; year effects and meeting selection can dominate.  No inferential significance or calibrated confidence region will be released unless simulation demonstrates adequate and robust operating characteristics.

## C. Predeclared simulation, calibration gate and seed

Use **the real observed (actor, year, meeting) attendance mask, but no real speech text, names, original speaker claims or vectors in public output**.  Freeze mask and seed `20261008` before simulating.  Generate a continuous *signed, scalar synthetic shift* (NOT the nonnegative norm of latent movement) under two known truths: `delta=0` and `delta=0.10`.  Synthetic generating mechanism:

`Y(i,t,m) = actor_i + delta * I(t >= 2020) + year_t + meeting_m + observation_e`

All effects zero-mean Gaussian and independent **at the level at which drawn**, with standard deviations `sigma_actor=0.10`, `sigma_year=0.15`, `sigma_meeting=0.10`, and `sigma_observation=0.12`.  The actor is persistent across years, the common year shock shared by all speeches in that year, and meeting shock shared by all speeches delivered at the same meeting.  This is a specified stress design for observed source dependence, *not* a claim that real speech embeddings are Gaussian or these variance components are empirical estimates.

Estimator: average the later-minus-earlier speech means for actors **with at least one retained observation in each era**, weighting each actor equally.  When simulated resampling removes any member of the original 99-actor common cohort, mark a denominator change separately and withhold that replicate from the fixed-population interval.  No missing speech is a zero outcome.

Test four procedures without changing the population silently:
1. **Naive independent-observation bootstrap**, resample observed speech rows by era, excluding replicates that lose any baseline matched actor.
2. **Whole-meeting bootstrap**, sample the original PV meeting groups with replacement within each era, preserving all speech rows in a meeting, excluding actor-loss replicates.
3. **Whole-year bootstrap**, sample four calendar-year clusters independently within each era, preserving all meeting/actor rows, excluding actor-loss replicates.
4. **Year-block deletion range**, conditional sensitivity only, never a confidence interval.  Report refusal/non-delivery if no valid replicate population is retained.

For bootstrap procedures use percentile 95% nominal intervals (2.5th and 97.5th quantile), **199 draws per synthetic dataset** and **400 Monte Carlo panels per truth**.  Predeclare that at least **90% of Monte Carlo panels** must yield a valid fixed-99-actor interval for a method even to be compared.  If valid, report empirical coverage of known `delta`, mean and median CI width, absolute estimator bias, and MC uncertainty `sqrt(p*(1-p)/N_valid)`.  **Eligibility** for a method-specific statement requires coverage **at least 92%** for *both* delta conditions, adequate valid-delivery rate, and no errors on source/group invariants.  Passing this narrow simulation would **not** authorize real-data confidence intervals without validation of the year/meeting variance parameters, selection mechanism, dependence misspecification and feature-fit uncertainty.

Sensitivity: repeat the bootstrap comparison under a **high year-shock condition** `sigma_year=0.25` holding all other parameters fixed, with the same seed but separate deterministic substreams, **200 synthetic panels per delta**.  Report failures, do not shift the acceptance bar after inspecting results.

No multiple-testing p-values, randomized treatment assignment, or independence assumptions beyond the simulated generating process.  Bootstrap intervals must be labeled **simulation-only**, not user-facing political conclusions.

## D. Exclusion and release

Original transcripts, PDFs, complete speaker/country rows, human review records, raw vectors, full resample trajectories and private keys stay in private storage.  Public PR can include pure code, synthetic tests, predeclared methods and **aggregate-only** counts/results.  No changes to held-out 37 meetings, evaluation lock, D1 O1–O5 gates, W4 original PR merge, published website or public country rankings.  W1 source schema needs independent coordinator acceptance; do not simply rename un.p2 originals to an existing unrelated legacy source type.
