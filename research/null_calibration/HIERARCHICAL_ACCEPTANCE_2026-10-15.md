# PR #67 hierarchical temporal-covariance development audit — 2026-10-15

**Engineering-only. Statistical acceptance FAIL / WITHHELD. Do not merge or deploy.**

## Scope, provenance and freeze
- Base workstream head before this implementation: `953d82152ae66a48921abb7381c7a7607f6c236a`.
- New modules: `hierarchical_reml.py`, `test_hierarchical_reml.py`, `benchmark_hierarchical.py`, solely `research/null_calibration/**`. This candidate is *not* the original PR #60 full REML or the frozen PR #57 synthetic null.
- Synthetic only: generator `study.world`, seeded by `study.seeded(810081, 'hierarchical_compare_'+scenario, 'development', world_index)`. Three predeclared development scenarios: 24 years × 4 meetings balanced; 24 × 4 misspecified meeting variance; 16 × 2 sparse. Exactly 30 attempted worlds/scenario, rho truth .55 **scorer only**; independent estimator never receives generating parameters. 13 fixed rho grid points, [-.8,.8], two jointly profiled variance parameters, optimizer maxiter 65.
- Input is synthetic meeting-level binomial prevalence with estimated sampling variance; Gaussian covariance `Vy*rho^abs(year gap) + (Vm + estimated count noise) I`. REML uses Cholesky GLS fixed-intercept correction and joint bounded optimizer over meeting/year variances. Failed profile optimizations, boundary solutions, unbounded profile intervals, and prior source/identifiability refusals are explicit.
- The estimated count noise is a plug-in (not jointly profiled); truncated count emission, nonlinear representation effects, source selection, speaker/affiliation dependence and high-dimensional W1/W2 transformations are **not identified**. Acceptance conditioned on complete identifiable profile and bounded CI. Confidence interval coverage is reported *only among accepted fits*, never as population coverage.
- Git blobs via live GitHub: `hierarchical_reml.py` b6a94c52decaf959f8cb996f762009390f3ba18c; `test_hierarchical_reml.py` be15f6a872046e94e013713812c10c27a01f2577; `benchmark_hierarchical.py` 4adff200318ff656cc2eb28e206483bf90574d4b.
- Local environment: Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0. No external synthetic inputs, UN original data, credentials or private evaluation text.

## Independently executed development numerical comparison

| Scenario | Model | Attempted / accepted | Bias | RMSE | CI covers truth / accepted |
|---|---|---:|---:|---:|---:|
| Balanced | moments | 30 / 30 | -.118327 | .258287 | not supplied |
| Balanced | annual reduced REML | 30 / 6 | -.465000 | .485275 | 3 / 6 |
| Balanced | joint hierarchical REML | 30 / 6 | -.438889 | .454911 | 3 / 6 |
| Heterogeneous meeting | moments | 30 / 29 | -.177911 | .353762 | not supplied |
| Heterogeneous meeting | annual reduced REML | 30 / 8 | -.486250 | .511151 | 5 / 8 |
| Heterogeneous meeting | joint hierarchical REML | 30 / 5 | -.496667 | .507992 | 3 / 5 |
| Sparse | moments | 30 / 26 | -.168496 | .319535 | not supplied |
| Sparse | annual reduced REML | 30 / 5 | -.482000 | .489142 | 4 / 5 |
| Sparse | joint hierarchical REML | 30 / 1 | -.416667 | .416667 | 1 / 1 |

**Joint hierarchical failures:**
- Balanced: 4 rho-boundary, 20 unbounded profile (24/30 withheld).
- Heterogeneous: 1 incomplete optimizer profile, 4 rho-boundary, 1 inherited rho-boundary/weak identification, 19 unbounded profile (25/30 withheld).
- Sparse: 7 rho-boundary, 3 inherited near-boundary, 1 nonidentified year variance, 18 unbounded profiles (29/30 withheld).
- Aggregate: **90 attempted, 12 accepted, 78 refused; 7/12 accepted profile intervals contain .55**. This is not an unconditional interval-coverage estimate.

**Computational cost, local wall-clock single-process**: 90 attempts: joint hierarchical about 22.98 seconds (balanced 10.36, heterogeneous 10.10, sparse 2.52); annual reduced about 1.97 seconds; moment about .06 seconds. Joint profiles required 9,522 + 9,642 + 9,222 = **28,386 likelihood evaluations** including refused cases. Timings are environment-dependent and not a reproducibility checksum.

**Development receipt**: local `benchmark_hierarchical.py --worlds 30 --grid 13` descriptive JSON SHA-256 `ae9995760c44d4d01bb0522092d734ca69387db71ddabde11478d00f5c4edd3a` for the initially executed source-equivalent prototype. GitHub-committed benchmark blob matches local byte-for-byte; the committed hierarchical module has minor source-byte differences from the executed local prototype. A subsequent source-equivalent replay showed unchanged numerical fit denominators but different elapsed times/receipt hash. This is **not** a GitHub Actions artifact or full-checkout exact-head reproduction.

## Test evidence and integration blockers
- Newly executed local owned-suite: `cd /mnt/data/pr67_exact && python3 -m unittest -q test_calibration.py test_extended.py test_study.py test_temporal_ar1.py test_profile_reml.py test_hierarchical_reml.py` → **30/30 pass, 0 errors, 0 failures**.
- Frozen source safety: existing PR57 critical values, immutable protocol, D1 O1–O5, the G01–G13 statistical holds, PR60 source and the 37 sealed October 5–6 source meetings were **not changed or opened**.
- Upstream files verified read-only from `main`: `research/integration/w1_w2/null_calibration/test-null.cjs` (Git blob 602c12d4fe4c2b35560abcd0741196f4bae0d745), `research/integration/w1_w2/nuisance_estimation/test_estimator.cjs` (87921fa28ba9ecda1c7e6443bd86f2f692fd4d7f), `docs/parallel-work/validate-contract.cjs` (345682f607ecba7633cdb35bcf4e7fa965d03d10). **Their tests were NOT executed in a full checkout.** Runtime git clone attempt failed `Could not resolve host: github.com`; connector exposes GitHub content but cannot create a full execution-capable checkout or run Actions. Historical CI evidence is inherited, not retested. GitHub workflow/status query on prior PR head returned no applicable runs or statuses, not PASS.
- Integration commands requiring network-enabled checkout:
```bash
git checkout <exact PR 67 head>
python3 -m unittest discover -s research/null_calibration -p 'test_*.py' -v
node research/integration/w1_w2/null_calibration/test-null.cjs
node research/integration/w1_w2/nuisance_estimation/test_estimator.cjs
node docs/parallel-work/validate-contract.cjs
```
  Inspect additional upstream W1/W2 transitive imports and pinned Node 22 dependency installation before claiming integration. These commands are proposals, **not executed upstream PASS records**.

## Disposition and next executable action
**FAIL — statistical identification.** Joint variance profiling did not rescue rho bias or coverage under meeting/year dependence and worsened convergence relative to moments. Do not retry heldout calibration with retrospectively selected settings; do not reinterpret selective conditional coverage as calibrated inference.

Next: coordinator/execution-capable full-checkout exact-head regressions; separately preregister a new development-only covariance identification experiment with more independent year blocks, modeled binomial noise, group separation and an independently implemented likelihood/objective reference. No release, merge or change to frozen PR57 calibration until scientific and engineering gates independently pass.
