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


## Follow-up exact-head request — 2026-10-15 14:24Z

Pinned main requested by owner: `964ba0899665bb03bbe4fc54b4c65426d7c4d35d`. PR head at the start of this follow-up: `b84002ab1845d2c42fd27306a94171f085d99713`. GitHub branch comparison: PR 29 ahead and 5 behind merge base `1e78e81a2270a6b643b9c344863199107e9138f2`, with 25 changed paths entirely owned; no cross-namespace changed paths. No rebasing or merged-tree tests claimed.

**Environment attempts:** `git ls-remote https://github.com/LystadJS/UNGA81-Transcript-Agent.git HEAD` failed `Could not resolve host: github.com` in the local container. The directory `/mnt/data/pr67_exact` is a partial manually reconstructed research module, not a repository checkout; it lacks the upstream W1/W2, PR60, and interchange files. Executing `python ci_integration.py --root . --head b84002ab1845d2c42fd27306a94171f085d99713 --main 964ba0899665bb03bbe4fc54b4c65426d7c4d35d` there returned **exit 1** with `blocker=no_git_checkout`, `ready=false`, `publication_eligible=false`, `suites={}`. This is an appropriate refusal, **not a successful upstream run**.

**Newly executed available local Python regressions:** `python -m unittest discover -p 'test_*.py' -v`: **38/38 passed**, Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, Node 22.16.0. Raw local log SHA-256 `381b3ba34f60b18da264952db9cb98cdee29325d1a19c583e2b752439e258b2c`. This set includes four additional noncommitted local tests for an experimental runner; the result must not be reported as 38 exact-head committed tests. The committed owned test suite's relevant 34 tests passed earlier. The local `hierarchical_reml.py` Git hash `d15326fc3b2fbc29509e5277cf8f5a8604f4e3b3` differs from current GitHub blob `b6a94c52decaf959f8cb996f762009390f3ba18c`. **Exact-head source-byte verification remains incomplete.**

**Hosted checks:** GitHub connector queried workflow runs and combined statuses for pinned PR head `b84002ab1845d2c42fd27306a94171f085d99713`; both returned zero entries. This does not constitute CI PASS. No upstream W1/W2 `test-null.cjs`, PR60 `test_estimator.cjs`, coordinator `validate-contract.cjs`, or full-checkout integration tests were executed this turn. No eligible owned-path failure was identified; inventing a fix or changing upstream ownership would be inappropriate.

**Coordinator acceptance outcome:** Ownership PASS, local module tests PASS (with exact-file caveat), complete checkout FAIL to obtain, actual upstream tests NOT RUN, hosted CI NOT RUN, scientific identification FAIL, empirical/release gates WITHHELD. Frozen PR57 thresholds, source/evaluation holds, and PR60 originals untouched. Leave PR #67 draft and unmerged.

**Next:** Run the committed `ci_integration.py` in an actual full repository checkout at exact current head and pinned main ref; capture fixture/source hashes, node/python versions, stdout SHA and complete upstream result ledger; test the effective merge tree separately and review hosted exact-head CI before coordinator engineering acceptance.


## Effective merge-tree runner and new verification — 15 October 2026, 14:29Z request

**Pinned comparison:** main `964ba0899665bb03bbe4fc54b4c65426d7c4d35d`; source PR head before this extension `c5ec759903a9b628a71fe264269488b7ad6fc66a`. The new module and test changes are exclusively inside `research/null_calibration/**`; `main` remains five commits ahead of the branch merge base. GitHub static comparison verifies **27 owned paths, zero changed-path overlaps**. This is not an executed actual-repository merge tree.

**Defect corrected:** the original `ci_integration.py` covers only four commands and cannot validate an effective merge tree. Newly added `merge_tree_integration.py` checks the exact HEAD/main commit objects and both frozen PR57/PR60 Git blobs, asks native Git to compute `merge-tree --write-tree`, checks merge conflicts, constructs an ephemeral local merge commit and detached worktree without updating any ref, runs all **12 declared native Python/Node tests**, records per-suite exit/status/stdout SHA256/duration, and removes its worktree. No remote merge, no threshold edits, and no private dataset reads are authorized. The first local development attempt hung because `git commit-tree` lacked `-m`; fixed before commit. The failure is retained in this report.

**Comprehensive synthetic local validation:** `python3 -m unittest -v test_calibration.py test_extended.py test_study.py test_temporal_ar1.py test_profile_reml.py test_hierarchical_reml.py test_ci_integration.py test_merge_tree_integration.py` — **40/40 PASS**, Python **3.13.5**, NumPy **2.3.5**, SciPy **1.17.0**, Git **2.47.3**, Node **22.16.0**. Full test log SHA256: `ca3ba86d8acf80925d248da41a1df8b2094ceec9222d774c48f9730ea04f1fee`. Every imported production Python module in this test scope was byte-matched to a GitHub blob, including corrected `hierarchical_reml.py` `b6a94c52decaf959f8cb996f762009390f3ba18c`. New module Git blob `2e8e51b1c6c94cf2d9f634abf7066462328fd1c1`, new six-case test Git blob `7f5c5ff197d8ae5f62fe138df29c74cfe3a4b7dd`, both identical to locally executed files.

**Six real local Git fixture tests:** (1) non-conflicting synthetic branches generate a real merged tree and run a positive smoke in a detached worktree; (2) a real conflicting merge is refused before test execution; (3) wrong head and altered frozen SHA are refused; (4) missing upstream test scripts remain NOT_RUN; (5) missing .git checkout refuses; (6) nonzero test subprocess refuses. **6/6 PASS.** None substitute for running the actual source repository tests.

**Actual pinned integration attempt:** `git ls-remote https://github.com/LystadJS/UNGA81-Transcript-Agent.git HEAD` failed DNS (`Could not resolve host: github.com`); a real full repository checkout could not be obtained in this runtime. `python3 merge_tree_integration.py --root . --head f5b1136514c8f1f0b3161eff578bf84c63d79e38 --main 964ba0899665bb03bbe4fc54b4c65426d7c4d35d --receipt /mnt/data/pr67-merge-tree-refusal.json` on the partial local source directory correctly returned **exit 1, blocker=no_full_git_checkout, ready=false, suites={}**; refusal receipt SHA256 `9ebb741d09c7a8b4514149b25cdf7dcd01ce0adfb3050f4984dd05ca603ebf76`. GitHub Actions and commit status for last inspected head also returned zero runs/statuses. Native upstream W1/W2, PR60, consensus, grouped refits, interchange, and readiness tests remain **NOT RUN**; do not upgrade an owned-only PASS or a toy merged-tree PASS into an exact-head full-checkout PASS.

**Coordinator suite inventory (full checkout only):** Python owned regression; PR57 frozen lock and numerical null; PR60 design guard and nuisance estimator; W1 framework and schema; W2 consensus; W1/W2 bridge and grouped source refits; v1 interchange; W1/W2 frozen readiness. All twelve must PASS with complete receipt and review of official CI jobs. Independent source hashes, adapted v1 relational invariants, real-data coverage and statistical nuisance identification are separate held gates.

**Current acceptance:** file ownership PASS, locally byte-identical Python regression PASS, synthetic Git merge-fixture PASS; actual PR effective merge tree NOT RUN, twelve native upstream tests NOT RUN, GitHub exact-head CI NOT RUN, nuisance statistical identification FAIL, source/holdout/publication restrictions PRESERVED. This document is a worker handoff, **not coordinator authorization**, and PR #67 remains draft/unmerged.

**Exact next command from a full checkout** (where HEAD is the final PR #67 commit and pinned main object is present):

```bash
python3 research/null_calibration/merge_tree_integration.py \
  --root . \
  --head <FINAL_PR67_FULL_SHA> \
  --main 964ba0899665bb03bbe4fc54b4c65426d7c4d35d \
  --receipt /tmp/pr67-native-effective-merge.json
```

Fail closed on any missing file, unsuccessful native suite, conflicting tree or unverified frozen identity. Review the actual command outputs and current coordinator ledger before engineering acceptance. Do not merge, publish, calibrate empirical text, or revise PR57 critical values.


## Pinned-main Git-object reconstruction and executable test attempt — 2026-10-15 14:53Z+

**Requested pinned reference:** `main` `964ba0899665bb03bbe4fc54b4c65426d7c4d35d`; PR #67 reviewed head `8c35cab796574ad9ac2a987383306001dfb06509`. This section records *new execution in the current turn* and supersedes older local-evidence caveats where indicated. Neither original empirical source text nor the 37 sealed evaluation meetings was opened.

### Static effective merge-tree identity — PASS (not native regression execution)

Queried GitHub's exact pinned main root tree `c1926a6660e2d45c82599f0c6bbc43a83fea9582`, its research tree `358ccfd6d6cc9c64cad3fc559e8f4ac2c0264f35`, and PR head's exclusive new `research/null_calibration` tree `410deb2b5be84b9d2d9d464dd7a3679f7f58ad66`. Main contains **no** preexisting `research/null_calibration` directory. The PR tree contains exactly **27 ordinary 100644 blobs**, with no symlinks, submodules, executable or outside-owned paths. No changed-path intersection exists with the five commits advancing main beyond the common merge base.

Independently reserialized main's original root and research directories using Git canonical tree-object serialization and verified both recalculated SHA-1 values exactly matched GitHub's tree objects. Inserted the unchanged PR subtree into the pinned research directory and recomputed:

- expected merged `research/` tree: `b78e97e13ab40f10f05eee4687b80a5693db2fc4`;
- **expected merged root tree: `f9e7af82dc56d92cd187705a62695f1cc5037234`**.

An independent native Git `git mktree --missing` replay produced both same original main tree IDs and both expected merged IDs. This is a **static object-accurate no-conflict merge-tree calculation**, not `git merge-tree` run against actual original commit objects and **not** a complete executable checkout. It is specific to PR head `8c35cab...`; any subsequent documentation commit changes the PR subtree, requiring recomputation. Local proof script SHA256 `89392cc8f57f1877248c047a84b07d4edb31d3b6d3c6b8104f32335a1598593b`; console receipt SHA256 `42b0d7e119e9048b391257f0a268203527dafd61a391b8ae5b90cc9171aeb6e9`.

### Newly executed exact-blob Python regressions — PASS (owned suite only)

Reconstructed all 19 Python files from the reviewed PR subtree, checked their local `git hash-object` identities against the 19 exact GitHub blob SHAs: **19/19 match**, zero mismatches. Executed:

```bash
cd /mnt/data/pr67_exact
python3 -m unittest -v test_calibration.py test_extended.py test_study.py \
  test_temporal_ar1.py test_profile_reml.py test_hierarchical_reml.py \
  test_ci_integration.py test_merge_tree_integration.py
```

**40/40 PASS, zero errors/failures, 2.965 seconds**, Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, Node 22.16.0, Git 2.47.3. Fresh local log SHA256 `a145d9533c9ca3d0a9731cd94a283e454d3e72e6298b1a92aee4a5fa9103c7bf`. This is byte-exact PR-source *owned Python* evidence, not upstream Node W1/W2 integration; the reconstructed directory contains additional untracked local development files, but the explicitly named 40 tests came exclusively from the 19 verified PR Python files.

### Actual full-checkout attempt — BLOCKED, expected fail-closed refusal

Local `git ls-remote https://github.com/LystadJS/UNGA81-Transcript-Agent.git HEAD` returned exit **128**: `Could not resolve host: github.com`. The local directory has no `.git` and lacks full upstream source. The committed `merge_tree_integration.py` invoked with reviewed head and pinned main returned exit **1**, `blocker=no_full_git_checkout`, `merge_tree_sha:null`, `ready:false`, `suites:{}`, `scientific_eligible:false`, `publication_eligible:false`. Refusal JSON SHA256 `af5b8d5d690c6f0eb3eff52b7f1c70fec27564b2b6192e7305dafb5c0427db20`. This is correct withholding, not evidence of a native upstream run.

**NOT RUN:** PR57 W1/W2 native null, PR60 native nuisance estimator, W1 original framework/schema, W2 consensus, W1→W2 bridge and grouped refits, coordinator interchange, W1/W2 scientific readiness and full-checkout effective merged-tree regressions. No current-head GitHub Actions or combined statuses were returned (both empty). There were **no eligible owned-path test failures** to repair. Do not claim native acceptance.

### Coordinator status

Owned namespace **PASS**; frozen PR57/PR60 Git blobs verified against the pinned GitHub tree **PASS**; static expected merge-tree identification **PASS**; exact-blob local Python suite **PASS**; full checkout acquisition **BLOCKED**; actual upstream native suites **NOT RUN**; hosted exact-head CI **NOT RUN**; covariance scientific identification **FAIL/WITHHELD** (previous hierarchical recovery 12/90 accepted); all G01–G13, original source/evaluation and publication restrictions **PRESERVED**. Keep PR draft and unmerged. The current public `main` may advance independently of the requested pinned SHA; recheck before any integration approval, without silently changing this test basis.

**Next executable action:** in an execution-capable complete checkout holding pinned main and the latest reviewed PR head, run the committed `merge_tree_integration.py`, retain complete native job logs/results, validate exact source and frozen hashes, and independently inspect latest-head CI. No merge, empirical test, threshold change or deployment is authorized by this handoff.
