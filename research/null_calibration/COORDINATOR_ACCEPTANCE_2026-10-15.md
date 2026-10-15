# PR #67 — Coordinator engineering acceptance handoff (2026-10-15)

**Disposition: HOLD / ENGINEERING-ONLY DRAFT. No merge or deployment. Scientific readiness remains WITHHELD.**

## Exact refs and source safety
- Reviewed current `main`: `964ba0899665bb03bbe4fc54b4c65426d7c4d35d`.
- Starting PR #67 head: `84d94189836327c314515f8c5f22e6cc804469c5`; follow-up changes `ci_integration.py` at `82e6e760d95505d5ea586e1c01013c613cb34f15`, tests at `db43732058d25e451cc3e566e52f161a02792d8e`.
- `main` advanced five commits beyond merge base `1e78e81a2270a6b643b9c344863199107e9138f2`. Its newly changed files include coordinator/browser/historical-source additions and a subsequent coordinator-ledger-only update, but no path in `research/null_calibration/**`. This verifies **path non-overlap**, not executable merge-tree or API compatibility.
- Latest PR effective diff at this step: 24 changed paths, **24/24 within `research/null_calibration/**`**. No frozen source/human-decision/heldout text, shared schema, site, workflow or coordinator-owned source file modified.
- Upstream native entrypoint Git blobs fetched read-only from `main`: PR57 `test-null.cjs` `602c12d4fe4c2b35560abcd0741196f4bae0d745`; PR60 `test_estimator.cjs` `87921fa28ba9ecda1c7e6443bd86f2f692fd4d7f`; coordinator `validate-contract.cjs` `345682f607ecba7633cdb35bcf4e7fa965d03d10`.
- Frozen PR57 protocol expected Git blob `95ee908bd710b7a6f075b685f0181a6fc979c33e`; PR60 candidate expected Git blob `eac3c87b2de555db55202d91cf440eaef228e4d0`. Runner independently verifies both identities in an actual checkout **before** running native tests. Original frozen PR57 critical values, G01–G13, private sources, sealed 37 meetings and D1 O1–O5 are unchanged.

## Owned-path changes and test execution
- Added `ci_integration.py`: off-network, fail-closed, exact HEAD/main guard, frozen PR57/PR60 Git blob guard, native Node suites and Python regressions, bounded subprocesses, results ledger and exit status. The runner never fetches sources, rewrites a baseline or invokes publication/deployment.
- Added `test_ci_integration.py`: tests absent checkout, wrong-ref refusal, failed subprocess and fixed immutable identities.
- Git blobs checked against local byte-identical tested files:
  - `ci_integration.py` `7ca80ab281eb035b1705c7615954c88e98132733`;
  - `test_ci_integration.py` `a536e224209545a8e70553adff18cf25b9518652`.
- Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, Node 22.16.0. Command in local reconstructed source directory:
  `python3 -m unittest -v test_calibration.py test_extended.py test_study.py test_temporal_ar1.py test_profile_reml.py test_hierarchical_reml.py test_ci_integration.py` => **34 tests, 34 PASS, 0 FAIL, 0 ERROR**. Earlier 30 tests plus four new runner tests. This is a local file-level suite, **NOT** an exact-head full repository or GitHub Actions pass. Existing local `hierarchical_reml.py` Git blob `d15326fc3b2fbc29509e5277cf8f5a8604f4e3b3` differs from the committed `b6a94c52decaf959f8cb996f762009390f3ba18c`; byte-exact current-head all-file acceptance remains unverified.
- Controlled fail-closed integration runner test:
  `python3 ci_integration.py --root /mnt/data/pr67_exact --head db43732058d25e451cc3e566e52f161a02792d8e --main 964ba0899665bb03bbe4fc54b4c65426d7c4d35d` => **exit 1**, `blocker=no_git_checkout`, `ready=false`, `publication_eligible=false`, no suites claimed run. This is the expected correct behavior.
- Attempted `git ls-remote https://github.com/LystadJS/UNGA81-Transcript-Agent.git HEAD`: failed `Could not resolve host: github.com`. Local source directory is **not** a full Git checkout. GitHub connector supports read/write source files but not executing remote tests. At reviewed head, Actions workflow runs/statuses returned empty arrays, **NOT PASS**.

## Coordinator gates
| Acceptance criterion | Status | Evidence |
|---|---|---|
| Current main, PR diff, ownership | PASS | Main SHA and 24 changed paths fetched |
| No shared/frozen file rewrites | PASS | PR diff and GitHub source-path comparison |
| Deterministic toy controls and local Python suite | PASS, local only | 34/34, explicit mismatch caveat |
| Verified exact merged tree against main | NOT RUN | No complete checkout |
| Exact-head native PR57 W1/W2 full null tests | NOT RUN | Missing upstream checkout |
| Exact-head PR60 estimator tests | NOT RUN | Missing upstream checkout |
| Exact-head v1 interchange regression | NOT RUN | Missing upstream checkout |
| Applicable GitHub Actions exact head/run log | NOT RUN | No run/status returned |
| Scientifically identified nuisance covariance | FAIL | Hierarchical REML 12/90 accepted; 78 failed/withheld |
| False positive, coverage, source replication | WITHHELD | No valid confirmatory nuisance null |
| 37 heldout source restriction, frozen critical values | PRESERVED | No reserved text or threshold changes |

## Exact-head coordinator execution recipe
Obtain an execution-capable checkout with `main` pointing to `964ba0899665bb03bbe4fc54b4c65426d7c4d35d` and HEAD pointing to **the newly current PR #67 head**. Then from the repository root:

```bash
python3 research/null_calibration/ci_integration.py \
  --root . --head <EXACT_PR67_HEAD_FULL_SHA> \
  --main 964ba0899665bb03bbe4fc54b4c65426d7c4d35d \
  --receipt /tmp/pr67-upstream-integration.json
```

The runner requires both original frozen Git blobs before executing four native suites (owned Python, PR57 W1/W2, PR60 nuisance, coordinator interchange); it exits nonzero on every failure or missing command and never overwrites a requested existing receipt. Before coordinator acceptance, validate the temporary integration merge tree against latest `main`, inspect all applicable GitHub jobs and logs at the **final** head, rerun relevant upstream suites on the merged tree, and apply only owned-path fixes. Do not merge or deploy PR #67.

**Blocking next action:** execute the above in a complete checkout/hosted runner. Fix any genuine owned failures, preserve results and the failed statistical scenarios, then reassess engineering-only acceptance independently. Scientific readiness remains withheld regardless of engineering test outcome.

## Main refresh after original review

Latest verified main **964ba0899665bb03bbe4fc54b4c65426d7c4d35d** adds one commit relative to previously reviewed `1af11061e3fa65d51b28d42a1b98bef250b6168b`. The only file newly changed is `docs/parallel-work/COORDINATOR_INTEGRATION_LEDGER_2026-10-15.md` (coordinator-owned); it does not touch W1/W2 numerical sources, interchange schemas or PR #67 paths. Main is **five commits ahead** of the PR merge base. This is a static changed-path check, not a full integration regression. The execution command above now targets the refreshed main. Full checkout and exact-head CI remain NOT RUN; existing refusal and statistical holds are unchanged.
