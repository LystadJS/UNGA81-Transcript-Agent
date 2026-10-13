# W1/W2 nuisance-preserving null calibration: synthetic-only

**Status:** engineering-only simulation protocol and tests, not inferential readiness or a valid original-UN-source hypothesis test. All 37 October 5–6 reserved meeting transcripts remain unopened.

## Design freeze and custody

- Frozen BEFORE any numerical simulation: protocol.v1.locked.json, commit **35dd737a7fd1d7896464df45fa77e2f2a28db4ca**.
- Original Git blob SHA-1: **95ee908bd710b7a6f075b685f0181a6fc979c33e**.
- Protocol file SHA-256: **bfffab858c6a478e7205d5c230450cb7fcc62445e5d4889ba1e366bd3bd79ea9**.
- The independently evaluated lock.cjs recomputes file bytes and fails if they differ. A statistical redesign must create a new version and prospective commit, never rewrite v1.
- The freeze covers scenarios, null hypothesis, cross-source statistic, searched strata, five W1 methods, grouped refit settings, seed derivation, failure policy, alpha and Monte Carlo budgets. **It freezes a fictional simulation design only**, not a future UN empirical hypothesis, validated null mechanism or G05 real-source statistic.

## Null, alternative, statistic and methods

The fictional null conditions on known invented source meeting/year/affiliation dependencies, attendance and unavailable sources, source families, parent IDs, duplicates, role/agenda/genre/language and exact passage length. The null contains **no planted cross-meeting theme**. The positive control plants one of three invented global lexical themes across meetings independently of nuisance grouping.

Each numerical draw runs the existing W1 TF-IDF and PCA/LSA kernels, actual k-means, PAM, Ward, GMM and HDBSCAN implementations (fixed seed 17, parameters in the locked JSON), real whole-meeting seeded child refits (3 samples, group seed 31), source-bound W1 versioned v1 exporter, W2 family-balanced coassignment/uncertainty and the source/failed-fit/noise ledger. **No toy substitute clustering score is used**.

The frozen max statistic examines **three** cross-meeting pair strata: all eligible cross-meeting pairs, different-genre pairs, and different-language pairs. Source-parent/family-identical pairs are excluded. Each stratum is the share of all originally eligible source-crossing pairs meeting association ≥0.75, coverage ≥0.45 and ≥2 contributing families, multiplied by the square root of its pair-count share among all cross-meeting pairs. The final statistic is the maximum across the three preselected strata, including search multiplicity. Every stratum requires ≥8 eligible pairs; null association remains missing and is never coerced to zero, although pairs with no jointly assigned evidence cannot qualify.

For each fictional observed world, the reference generator redraws known oracle meeting/year/affiliation lexical effects and source-conditioned token emissions while keeping the source inventory, source group IDs, selections, nuisance covariates, duplicates, lengths and missingness fixed. It **refits the full W1/W2 pipeline** under each null draw. Corrected conditional-tail fraction is (1 + number of null statistics at least observed) / (1 + references attempted), but it is **not a p-value for actual diplomatic text** because real nuisance parameters/exchangeability have not been established. Reference failures prevent delivery, not silent deletion.

## Frozen scenarios

| World | Planted cross-source latent signal | Primary nuisance and limitation |
| --- | --- | --- |
| N1_independent | No | Six groups, lengths and language/genre variation |
| N2_meeting_dominant | No | Six unequal groups, strong agenda/meeting vocabulary, parent/source duplicates |
| N3_cross_classified | No | Eight groups, recurring affiliations, original source family crossing meeting boundaries; meeting-only fitting MUST be withheld |
| N4_year_independent | No | Eight independent-year shocks, four years per era, fixed nonrandom attendance |
| N5_year_serial_ar1 | No | Same fixed attendance with AR(1) year shocks, rho=0.65, including serial dependency |
| P1_cross_meeting_theme | Yes | Positive planted cross-meeting lexical themes; known-truth code/geometry control only |

The typed source graph checks meeting, parent and source-family closure; meeting + affiliation closure; meeting + year closure; recurring affiliations, duplicates, concentration, attendance and years. It does **not** assert that a repeated-affiliation graph or four-year-era series can produce independent source replicates. N3 refuses its numeric meeting bootstrap entirely; its attempts and withheld reasons remain in the denominator. N4 and N5 may execute fictional oracle numerical tests, but they are **not a real few-year confidence interval**.

## Budgets, delivered results and scientific limits

Frozen nominal global FWER α = 0.05; full prospective simulation requirements are **at least 1,000 independent null outer worlds per regime × 1,999 reference draws per world**, with one-sided 95% Wilson upper type-I rate ≤0.075 across every preregistered null regime. The completed smoke and pilot runs are substantially smaller and **cannot** establish such calibration.

| Executed mode | Worlds attempted | Completed W1/W2 | Withheld source-closure worlds | Reference draws attempted / successful / failed |
| --- | ---: | ---: | ---: | --- |
| Smoke, 2×7 | 12 | 10 | 2, N3 | 70 / 70 / 0 |
| Pilot, 4×19 | 24 | 20 | 4, N3 | 380 / 380 / 0 |

All five numeric-admissible regimes (N1, N2, N4, N5, P1) completed each pilot reference draw. Deliberately invalid N3 did not run a false meeting-independent null. These are **numerical and dependence stress diagnostics**, not known-true error-rate or power acceptance. The oracle parameters are supplied by the fictional generator rather than independently estimated from UN source data. Even executing every expensive full shard would not remedy this G07/G04 deficiency.

### Reproduction (Node.js 22; no original corpus or model downloads)

~~~sh
node research/integration/w1_w2/null_calibration/lock.cjs
node --test research/integration/w1_w2/null_calibration/test-null.cjs
node research/integration/w1_w2/null_calibration/run.cjs --mode smoke --output /tmp/new-w1-w2-null-smoke
node research/integration/w1_w2/null_calibration/run.cjs --mode pilot --output /tmp/new-w1-w2-null-pilot
node docs/parallel-work/inference-readiness-v1.cjs
~~~

The CLI requires a fresh out-of-repository output directory. It writes only aggregate JSON, G01–G13 status and a separate SHA256.json integrity manifest using restricted file permissions. No original source rows, raw synthetic tokens, vectors, private reviews, held-out material or speaker/political labels are exported. The optional costly full-shard mode requires an explicit command-line acknowledgment, one independent world index and the frozen 1,999 reference draws. aggregate.cjs checks nonoverlapping shard indices/seeds and full delivery; a favorable incomplete shard is never a scientific PASS.

## G01–G13 assessment

readiness.cjs compares every generated report with the already-merged, **unchanged** thirteen-gate register at docs/parallel-work/w1-w2-inference-readiness.v1.json. **All thirteen scientific gates remain NOT_RUN.** Synthetic numerical verification does not authenticate original bytes (G01), a real inventory or graph (G02–G03), exchangeable groups (G04), a real frozen confirmatory statistic (G05–G06), estimated source nuisance (G07), a fully verified real null (G08), adequately calibrated type-I error (G09), externally validated nuisance controls (G10), independent authorized held-out sources (G11), complete private original-source provenance (G12), or owner publication authorization (G13).

G03/G04 cannot be bypassed merely by redefining a connected source family as multiple independent meetings. Source/genre/agenda dependence and serial year shocks are known to produce spurious apparent stability. Current W2 coassignment fractions remain descriptive, not probabilities of diplomatic agreement; p-values/confidence intervals, government positions, political alignments, coalitions, influence, D1 release and website mirror are **WITHHELD**.

**Next prospective scientific step:** independently characterize a new authorized source/design population and estimate/validate the nuisance/selection process; propose a distinct data-specific locked test and full dependence-aware Monte Carlo calibration before opening any confirmatory empirical evaluation source. A passing synthetic pilot cannot authorize this step.
