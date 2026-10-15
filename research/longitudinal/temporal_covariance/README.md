# W4 historical meeting sampler and temporal-covariance research

**Scope:** coordinator-owned, source-safe **2008–2015 original-PV sampling + 2016–2023 previously verified comparator**. Engineering and source QA only; no real W4 interval, diplomatic position or website release.

## Frozen source design and actual audit

Preregistration [13 October 2026](../../../docs/parallel-work/W4_2008_2023_COVARIANCE_PREREG_2026-10-13.md) preceded original PDF acquisition and the new simulation run. The previously provided **UN General Debate speaker index** (January 2026; SHA-256 `841ae22d6485a7e3c0bce84830f09c43d75421ce9b3a58408d20dfec3cbbaf43`) yielded 118 official historical original-PV meeting symbols in 2008–2015. After sorting meetings within year, four chronological quartiles/year each selected **two meetings without replacement**, seed 20261013. Exactly **64 official PV files** are pinned in `selected_official_pvs_2008_2015.txt`; source-frame SHA-256 `70373a36d240cbd0403f3d5d6c7f8df2049a09122de34fc4863ec2af8766ad9d`, selected-list design SHA-256 `e90e4b0182154ce367d6b1db55ea7f0d4047e3badcf5fcc9b1c9c3c01c612f2b`. First-stage inclusion probability for a PV is `2/N_{year,quartile}`; it is **not** the probability of fully verified Harvard speech text.

**Actual source acquisition:** 64/64 complete original UN PDFs, 2,435 pages and 29,118,824 bytes, acquired through official UN endpoints and sent as private 1-day recipient-encrypted artifacts. Every original PDF was rehashed after decryption. Source verification on the uploaded Harvard v14 archive and matching UN index rows produced **858 selected speaker-index rows**, **832** full-original-PV seven-word speech matches, **828 unambiguous country-year** matches, two country-years with multiple strong source candidates and **three PLO observer labels** kept outside the member-country denominator. Historical UN names were mapped explicitly, preserving original labels: `Libyan Arab Jamahiriya → LBY` (two indexed records) and `Cape Verde → CPV` (three records); this is an archival code match, not person identity adjudication. No individually authenticated repeated speaker persons.

The source-matching cutoff: normalized seven-token-shingle correspondence ≥90%, ≥8 of 10 speech deciles ≥80%, and beginning/end checks ≥40%. Unknown, ambiguous, prepared-versus-PV and non-indexed source modalities are not silently promoted. Every original PV byte digest, country/name/source match and exception is private.

**Design-based frame-only check:** inverse-first-stage-probability Horvitz–Thompson estimates of the index's own yearly speaker-row totals have mean absolute relative error **6.43%**, with a 2015 underestimate **19.37%**. Two original meetings per stratum make a simple within-stratum index-row-count variance calculable, but not a fully verified text-response/selection variance. Official index completeness and actual response propensity are not established; public population generalization is prohibited.

**Historical comparator:** the earlier source audit verified 105 original PV meeting files and 1,543 complete Harvard speech correspondences for **2016–2023**, a distinct prior-source record. The newly verified 2008–2015 subset gives eight more years of original-source **potential observations**, not an already fitted or harmonized 2008–2023 representation. A common historical feature basis, matched actor populations, selection/genre/language comparability and source distribution must be frozen in a separate empirical study.

## Model and independent synthetic calibration

- `temporal_covariance.py`: a year-level Gaussian model with **estimated** serial AR(1) correlation, year-level nugget share and marginal variance. The **observed year-effective sample size** comes from source meeting inclusion weights; `rho` and nugget are selected by fixed-grid profile restricted ML, and `sigma²` by the restricted GLS residual quadratic. No true simulation parameters are supplied to the estimator.
- `synthetic_worlds.py`: separate synthetic source/actor/meeting/year generator, including a known meeting-first-stage probability sample and an outcome-dependent **nonignorable** second-stage source-response stress.
- `independent_calibration.py`: preregistered R=300 ×18 = **5,400 synthetic panels** (8/16/24 years ×2 sampling masks ×3 year/selection worlds), three 90% interval schemes per panel (16,200 intervals): year-Welch, feasible estimated-AR1-REML GLS, and the prespecified covariance-family envelope. Every method/scenario retains attempted/evaluable, coverage, Monte Carlo SE/Wilson bounds, bias, widths, rho bias/RMSE and boundary selections.
- `test_independent_covariance.py`: 72 **independent Cholesky numerical** parameter/GLS-envelope verification fixtures, the frozen probability selection policy, and refusal of bad observations. These are algorithmic controls, not verification of the true historical year covariance.
- `source_sampler.py`: fail-closed offline sampler that accepts only the original UN index SHA, exactly reproduces the prespecified meeting-frame and selected SHA identities, and never prints raw country/speaker records.

### Calibration decision

The nominal 90% interval criterion passed **6/6** independent-year scenarios for Welch and feasible AR1 REML; **0/6** each for serially correlated year shocks, and **0/6** each under informative source selection. The broad covariance-grid envelope **overcovered** (often 95–100%) and passed **0/18** nominal calibration checks; it was frequently too wide. **Point estimation of rho passed the preregistered reliability criterion in 0/18 scenarios** (bias/RMSE/boundary failures). There were **0 failures among 5,400 simulated panels**. Monte Carlo outcomes, all 54 method×scenario rows and full source-year QA are available privately; public aggregate [receipt](../../../docs/parallel-work/W4_EXTENDED_YEAR_COVARIANCE_AGGREGATE_2026-10-13.json) excludes original source-linked rows.

| Serial-year AR1 rho=.65, two-stage source mask | T=8 | T=16 | T=24 |
|---|---:|---:|---:|
| Year-Welch coverage (nominal 90%) | 69.0% | 61.0% | 55.7% |
| Feasible estimated AR1 REML coverage | 80.0% | 79.7% | 83.0% |
| Grid-envelope coverage (overconservative) | 94.0% | 97.3% | 95.7% |

**No serial-year source-mask scenario was calibrated.** The broad envelope is not a valid empirical CI simply because its simulated coverage exceeds the nominal level: coverage, width and covariance-family assumptions must all be justified, and the actual source-verification nonresponse mechanism is unknown.

## Reproduction and privacy

Local synthetic execution (Python 3.11+, NumPy, SciPy):

```bash
python research/longitudinal/temporal_covariance/independent_calibration.py --selftest
python -m unittest discover -s research/longitudinal/temporal_covariance -p 'test_*.py' -v
python research/longitudinal/temporal_covariance/independent_calibration.py --out PRIVATE_NEW_DIRECTORY
```

Source sampler (only if already authorized to inspect original UN Library CSV):

```bash
python research/longitudinal/temporal_covariance/source_sampler.py --un-index /private/original/GA_debate_speech_dataset_20260129.csv
```

The original PDF retrieval is manually source-scoped through `secure_historical_pvs.py` and the path-limited read-only workflow; only recipient-encrypted private originals are uploaded to an expiring artifact, no plaintext or decryption key. Its historical source matcher and audit receipts are in the user's private package. Never commit UN documents, source-linked speaker/country-year joins, 64D vectors or the source encryption private key. The 37 reserved October 5–6 2026 meetings, original W1 v1 contracts, D1/O1–O5 gates and active website are untouched.

**Acceptance:** original historical meeting sampling and selected-source QA PASS; synthetic covariance-model implementation and test execution PASS; **covariance reliability and real-world calibrated temporal uncertainty FAIL/WITHHELD**. Do not refit/promote the original 2016–2019 frozen representation as a cross-2008 comparison or publish a causal/national-position interpretation.