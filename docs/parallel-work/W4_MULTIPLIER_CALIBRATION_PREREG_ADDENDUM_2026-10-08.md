# W4 preregistered calibration addendum: actor-preserving positive cluster weights

**Recorded 8 October 2026, before computing this addendum's simulation results.** This is an *additional method*, not a revision of the first preregistered bootstrap failure. Preserve the first design's zero-delivery outcome unchanged.

## Why

In the original 199-draw ordinary row, meeting, and year bootstrap, most replacement draws eliminated at least one of 99 originally matched country affiliations; therefore zero of 1,200 simulated panels produced enough fixed-99-cohort draws to meet the predeclared full-cohort interval rule. A potential alternative is a **positive cluster-weight bootstrap**, which retains every original observation's source opportunity while changing the influence of each calendar-year block (and optionally each nested meeting). The fixed-population estimand remains the equal-99-affiliation average of signed later-minus-earlier scalar values.

## Fixed design and two methods

Exactly reuse the originally preregistered observed 523-row 99-country×8-year×55-meeting attendance mask, synthetic outcome process, true shift scenarios, Gaussian actor/year/meeting/observation shocks (SD 0.10/0.15-or-0.25/0.10/0.12), and both 0 and 0.10 known shifts. Seed **20261009**. For the base year-SD=0.15, evaluate **400 synthetic panels per shift**. For the stress year-SD=0.25, evaluate **200 synthetic panels per shift**. Use **199 bootstrap draws per panel**, and 95% percentile intervals. Reports must include empirical coverage, binomial MC standard error, delivery fraction, average/median width and true bias, plus 0% false population attrition where expected.

- **Positive whole-year Dirichlet multiplier:** For each era independently draw `(w_y: four years) ~ 4 * Dirichlet(1,1,1,1)`. Every speech within a calendar year receives the same strictly positive multiplier. Actor-period means are weighted by the positive year weights, leaving all 99 baseline actors in the cohort. This uses only four year clusters per era, so it is a *finite-design simulation*, not a reason to treat bootstrap percentiles as calibrated.
- **Positive year + meeting hierarchical multiplier:** The same era-specific year Dirichlet; within each year independently draw strictly positive meeting multipliers `n_meetings_year * Dirichlet(1,...,1)` across **actual original PV meeting IDs**. Each speech receives `year_weight * meeting_weight`; all country-year and meeting source cells remain present. Year effects are still sampled as whole blocks; this additional within-year reweighting does not create new independent years.

No resampling of individual speeches; no zero or negative weights; no refitting the frozen vector basis, no missing-source imputation. Compare both methods to the originally preregistered (non-delivering) ordinary replacement bootstrap only as an **additional design**; do not overwrite or retroactively relabel the original.

## Acceptance decision

An interval procedure is **simulation-calibrated under this specified generative design only** if: (a) ≥90% simulation-panel delivery and ≥180 fixed-cohort bootstrap draws per panel; (b) ≥92% empirical coverage of the known shift in **all four** (zero/positive × base/high-year-noise) scenarios; and (c) source/year group and no-leakage checks pass. We require **all four** scenarios, not selecting favorable results after running. Failure must be shown in aggregate including attempted and withheld denominators. Even passing does **not** authorize real 64-dimensional W4 confidence intervals: the synthetic response is a *signed scalar* and variance components, missingness mechanism, political interpretation, reference training uncertainty and sampled meeting representativeness remain unvalidated. Real population inference and publication are withheld regardless.
