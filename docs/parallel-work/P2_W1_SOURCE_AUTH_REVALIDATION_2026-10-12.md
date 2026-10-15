# P2→W1 authenticated original PV replay and estimated-covariance calibration

**Audit:** 12 October 2026. **Preregistered** before the newly acquired source replay and the new synthetic multi-year known-truth simulation: [protocol](P2_W1_MULTYEAR_FEASIBLE_COV_PREREG_2026-10-12.md). Public-safe aggregate [receipt](P2_W1_MULTYEAR_REPLAY_AGGREGATE_2026-10-12.json). All original UN PDFs, complete Harvard texts, country/year speaker rows, 600-row W1 fit records and file-based private attestation remain in approved private artifacts, **not GitHub**.

## 1. Independent original-document replay and population reconciliation

- Original document scope **2016–2023** General Debate, sessions **71–78**, never 2024–2026. Exactly **105/105** official UN plenary/PV PDFs reacquired via UN document endpoints and checked against freshly computed raw-byte SHA-256 after recipient-encrypted transfer. Complete **5,184 PDF pages / 84,661,892 original bytes**, all complete document structures and extractable text.
- **Publisher hash nuance:** the UN did not supply independent signed checksums of those original PDFs; SHA-256 compares locally acquired originals with private acquisition manifest after decryption. The original Harvard `UNGDC_1946-2025.tar.gz` bytes are separately verified against the published v14 MD5 and pinned tar SHA-256 `55077dccf7242cdf544aa95c4797c68e443b0c37344c9c112a2e2392ddfcf8e5`.
- Independently recomputed full source-document text correspondence using the prespecified seven-token, ten-decile and opening/ending rules. **1,543/1,545** Harvard country-year speech texts pass; two are quarantined. Text correspondence is not proof of true human speaker identity, diplomatic stance or source-language/translation invariance.
- The preregistered, fixed **99-affiliation × eight-year = 792** candidate frame now has **790 verified and 2 unverified** source cells. The remaining cells are *not speech absence or zero vectors*. The fixed selected-affiliation denominator does not prove a population-level UN membership census.

## 2. Source-authentication vulnerability and correction

The earlier P2→W1 adapter independently hashed all 105 original official PDF files and the **whole** authentic Harvard tarball, but did not check that **each selected text** came from the claimed exact Harvard tar member. A controlled negative test changed a fictional speech, recomputed its claimed SHA and kept the authentic archive unchanged: **the former adapter incorrectly accepted it**. This was a genuine trust-boundary weakness, not a failed PV acquisition.

`research/source_acquisition/p2_expansion/p2_to_w1_source_adapter.cjs` now extracts the exact `ISO3_session_year.txt` member bytes from the published-hash-bound tar, hashes **all 790 accepted rows**, and compares each actual original member SHA to the P2 claim and supplied W1 input text. Missing/duplicate original members fail closed; the same forged-row test now **rejects** as required. Additional synthetic archive-member tests cover exact positive, missing member, duplicate member and forbidden future source. Native W1 clustering algorithms, input source role and the frozen analytical `un.parallel-analysis.v1` remain unchanged.

The original, uncompromised P2 data are accepted into the separate W1 source-bound input `un.source-validation.frame.v1` under source schema `un.p2.original-pv-reconciled.v1`—not fraudulently recoded as a legacy consumer schema. **Legacy analytical v1 P2 export stays withheld.** The separate `un.parallel-source-inventory.v1` companion remains responsible for all 792 source states and null unverified dates.

**Canonical W1 engineering fit:** a declared SHA-ID-ranked 75-observations-per-year sample of **600** verified original-PV speeches (backend cap). K-means and Ward full fits **2/2** successful; whole-meeting omission refits **4/4** successful; country-affiliation/source-connected schedules **2 skipped**, not accepted as independent cluster resamples. Method agreement **ARI 0.558, AMI 0.568**. The full 790-row source cohort is authenticated but **NOT FIT in one canonical W1 run**. No diplomatic/policy movement is inferred from algorithm agreement.

## 3. New preregistered multi-year covariance calibration

Fixed *before* the current Monte Carlo outcomes: 4 synthetic annual designs (8, 12, 16, 24 years), 2 known year-shock models (iid and serial AR(1) rho 0.65), 2 fixed **synthetic** source masks (near complete; restricted 523-like rate), `R=400` each = **6,400 independent known-truth scalar synthetic panels**. Country intercept SD .40, meeting SD .12, year SD .20, residual SD .25 and beta +.20; nominal **90%** interval coverage. No real country speeches, political annotations or unobserved real selection model entered the simulator.

Compare naive country-paired t, year-aggregated Welch t, and **feasible AR(1) GLS with rho and year variance estimated from its observed annual means** via bounded REML. The REML estimator does **not** receive the generating true rho or year variance. Its approximate Student-t reference df is `T−3`; this approximation is explicitly **under evaluation**, not assumed calibrated.

**Results:** all methods delivered 400/400 intervals in all 16 scenarios. The prespecified acceptance rule (at least 380 delivered, coverage within .04 of nominal, and Wilson 95% interval including .90) passed **8/16** year-Welch scenarios (all independent-year worlds), **2/16** feasible-REML scenarios (the independent-year 24-year worlds), and **0/16** naive country-t scenarios. **No method passed in any serially dependent year world**, even with 24 synthetic years. E.g., in the near-complete serial-year case, year-Welch coverage was 68.5% at eight years and 61.0% at 24; feasible estimated-AR(1) was 75.2% and 79.8%, respectively. With true rho=.65, mean fitted rho was only about .34 at 8 years and .54 at 24 years. The detailed 48 method×scenario rows, Wilson intervals, Monte Carlo SE, fit rho, estimated residual scale, biases, widths and boundary-hit diagnostics are delivered separately.

**Scientific interpretation:** using an estimated covariance parameter is better than pretending it is known, but it does *not* produce calibrated intervals under the tested serial-year and meeting-shock DGP. More calendar years alone cannot repair a misspecified or poorly identified dependence/selection model. Both synthetic source masks are **synthetic surrogates**, not a verified actual UN response-missingness mechanism. Prior October 8 simulation failures remain in the record; these new results do not revise preregistration retroactively.

## 4. Explicit gate matrix

| Gate | Decision |
|---|---|
| New original 105-PV acquisition, complete raw bytes and local SHA manifest | **PASS** |
| New entire-speech historical original-PV text comparison | **PASS 1,543 / 1,545**, quarantine two |
| Strict exact original Harvard member-to-observation SHA binding | **PASS**, tamper attack rejected |
| 790 verified + two unverified, original 792-cell universe | **PASS**, selected cohort only |
| Native W1 600-row source-authenticated method computation | **PASS**, descriptive engineering |
| W1 full 790-source one-fit inference | **NOT RUN**, W1 cap 600 |
| Estimated-covariance simulation under serial calendar-year dependence | **FAIL** 90% synthetic coverage criterion |
| Real W4 confidence intervals, significance, country political positions | **WITHHELD** |
| Old analytic v1 direct P2 export, browser/data publication | **WITHHELD** |

The source-coded attack test, original-source and population checks and unchanged W1 numerical suite are tested through [source-only Actions](../../.github/workflows/p2-w1-reaudit-tests-20261012.yml). All row-linked/source-byte evidence and synthetic scenario outputs remain separately downloadable in private packages; the public aggregate JSON contains no private country/year observation table.

**Reserved evaluation:** none of 37 October 5–6, 2026 meeting transcripts were opened. Frozen holdout locks, original source checksums, reviewer decisions, D1 O1–O5 release gates, site/browser and driftmapR code were not touched.

### Necessary next work

Reconcile remaining transcript fidelity issues and independent person/recorded-affiliation attribution, preregister a *new* longitudinal estimator suitable for limited correlated years and informative selection (not tuned to these results), validate whole-panel numerical comparison beyond the 600-row cap using a method whose population is source-identical, then evaluate calibration in independent simulated and later source-authenticated annual/meeting cohorts. **Do not label any present simulated coverage pass as a valid real-world W4 interval.**
