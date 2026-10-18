# US-relative trajectories: coordinator-only integration plan

**Version 0.1 | 15 October 2026 | Planning only**

**Decision:** prepare a prospective mandatory gate first; then, only under separate integration authorization, integrate **PR #82 → PR #92 → PR #93**. Keep historical review workflows and receipts intact. No merge, retarget, deployment, empirical execution or protection-setting change is authorized by this plan.

The companion JSON is planning metadata, not an analytical interchange schema or an approval receipt. All integration stages remain `NOT_EXECUTED`.

## 1. Verified snapshot and scope

Live PR metadata and `main` were read on 15 October 2026. Exact pins, rather than PR labels or remembered branch tips, govern this plan. [S1–S4]

| Role | Branch / target | Pinned head |
|---|---|---|
| Current integration base | `main` | `da4ab9ed11dba3693d11aa12f5333963b1b85478` |
| Phase 1 producer and source contracts, #82 | `coord/us-relative-phase1` → `main` | `81110db49786a05f9c8f8ce4d5103c92fe255586` |
| Phase 2 offline views, #92 | `coord/us-relative-phase2` → `coord/us-relative-phase1` | `76fbfd73f440306dfd9fc72a6431704f7b09b45d` |
| Independent reviewer and ledger, #93 | `coord/pr92-independent-review` → `main` | `3789018a0bd031d8bea65fd9b1973a8313bff314` |
| Executed #93 reviewer code | Historical reference, not a new product head | `0ba50379ff63cafb2ccd10aed6608e78f6a202db` |
| Retained Phase 1 reviewer, #87 | Evidence dependency only; not an additional planned merge | `dc8f98dec92cd34242f9ed7c6ce85814291ada38` |

PRs #82, #92 and #93 are open, draft and unmerged. The #93 head adds an acceptance ledger after its executed reviewer commit. Its successful run validates #92, not the combined tree containing all #93 additions. [S1–S3]

**Allowed integration deltas:** #82 has 15 paths: 14 in the Waggoner subtree and its existing coordinator bridge entry point; #92 adds 12 paths relative to #82, comprising 11 `phase2/` files and one new coordinator workflow; #93 adds four reviewer/workflow/ledger paths. The companion manifest records all **31 unique paths**. Every existing bridge test must remain. Any extra path, deletion, mode change, symlink, submodule or generated public asset stops integration for review.

No changes are permitted to W4 estimators, weighting/baseline rules, numerical tolerances, frozen contracts/gates, source hashes, human decisions, real/private corpora, the 37 reserved transcripts, `site/**`, `un/**`, release manifests, Pages, or the portfolio mirror. Documentation and candidate trees must be inspected without opening transcript contents.

## 2. Reuse evidence without overstating it

| Evidence | Verified historical result | Reuse boundary |
|---|---|---|
| #82 repair review, run `38769872958` | Exact repaired head and effective tree against `5f0a872cff0899819b21326e6c18b7af794556c5` passed mandatory R and retained R1/R2 probes | Does not cover a new base or prospective gate implementation |
| #92 implementation, run `38779954475` | Exact head and effective tree against current pinned `main` passed | Does not establish permanent required-check enforcement |
| #93 independent review, run `38792204591` | Same #92 head and effective tree passed source recalculation, contrast and original suites | Does not validate a combined #82/#92/#93/gate-adoption tree |

The validated #92 head tree is `7be21e90e6142a62e1f12f04e04f28707107178a`; its effective tree against the pinned `main` is `f61c3b7efc5b2e4cc4c730a870ffdd1e834fa571`. Six retained ZIP archives were SHA-256 and CRC checked while preparing this plan. No analytical or browser suite was rerun for this documentation task.

Keep all failed historical runs, the original R skip, R1/R2 failing reproductions, original axe incomplete results and their separate measured resolutions. Archive download hashes appear in the companion manifest. Preserve reviewed evidence before its 14-day hosted retention expires; do not present expired artifact links as available. A rerun creates new evidence, never replacement history. [S1–S3]

## 3. Close the gate-adoption gap before product integration

Current workflows are valuable evidence producers but not a complete prospective gate:

| Existing workflow | Observed limitation | Required coordinator treatment |
|---|---|---|
| `coord-w2-w4-evidence.yml` on `main` | Runs bridge tests, but does not provision R or invoke the Phase 1 `--require-complete` runner | Preserve it; add an explicit mandatory-R gate rather than treating its green result as R acceptance |
| #92 `coord-us-relative-phase2.yml` | PR-only, phase2-path-filtered; integration base is hard-coded | Preserve the historical workflow; a prospective gate must cover Phase 1/upstream changes and the actual resolved base |
| #93 `coord-pr92-independent-review.yml` | Reviewer-path-filtered; candidate and base are fixed historical SHAs | Preserve it as reproducibility evidence, not the future product check |
| #93 `test_review.py` | Intentionally pins original HTML and historical contrast-selector inventories | Retain pins; any intentional visual change needs a separately reviewed successor expectation, never automatic repinning |

These limitations are visible in the checked workflow source and retained reviewer source. [S5–S7]

**Prospective patch, not applied here:** reserve `.github/workflows/coord-us-relative-integration.yml` and `research/integration/w2_w4_w6/usref_integration/**` for coordinator-owned gate glue. Do not duplicate or edit workstream estimators. Keep this gate-adoption change separate from the accepted three-PR payload and identify its own tested head.

The proposed stable required status is **`usref-integration-required`**. Its finalizer must use `always()` with explicit dependencies, require literal success from every mandatory job, inspect nonempty receipts and reject failures, errors, skips, cancellations, missing runtimes, missing artifacts and mismatched identities. No `continue-on-error`, fake substitute check, optional-R acceptance, `--if-present` or missing-file-success path is allowed.

Trigger the prospective gate on `pull_request` including `edited` for base retargets, on `push` to `main`, and on `merge_group` if the repository uses a merge queue. Do not put path filters on the required workflow. Run full product coverage once the product is present; use an explicitly declared bootstrap/Phase-1 stage before that, not opportunistic file-existence checks. A removed required module is a failure. On unrelated pre-adoption changes, a bootstrap receipt must not masquerade as product acceptance.

GitHub documents that filtered workflows can remain pending, skipped jobs can report success, latest-SHA checks are necessary, and merge queues require a separate event. A manual-dispatch result must not be assumed to satisfy a required PR check. [S10] This plan deliberately requires stronger zero-skip evidence than a generic green badge.

### Protection and authorization boundary

The live `main` protection read returned **403: Resource not accessible by integration**. The visible ruleset collection returned `[]`; this does not establish that all branch protections are absent. Required contexts, expected check source, bypass permissions and merge-queue configuration remain **UNVERIFIED**. [S9]

Before any future product merge, an authorized administrator/coordinator must provide a verifiable protection snapshot and, under separate authorization, require the new status while preserving every existing requirement. Do not remove requirements, enable bypass, change merge strategy or infer protection from `mergeable: true`. Missing enforcement evidence is a hard integration stop, not a blocker to completing this plan.

Bootstrap and prove the gate using separate, pinned reviewer checkouts before product modules are on `main`. #87 may supply its seven retained Phase 1 probes read-only; this plan does not merge #87. At Phase 1, require native R plus Phase 1 and upstream checks. At Phase 2 and later, require all browser/contrast checks too. Test the complete proposed three-PR plus gate tree before any authorized rollout.

## 4. Ordered execution runbook

```text
CURRENT TASK: documentation only; no repository integration

Future, separately authorized:
  G0  Re-pin state, retain evidence, verify ownership/protections
   ↓
  G1  Stage/prove mandatory gate + combined-tree dry run
   ↓
  G2  Authorized gate adoption; verify required status enforcement
   ↓
  I82 Integrate #82 → main; verify actual landed commit
   ↓
  I92 Retarget #92 → main; validate delta; integrate; verify landed commit
   ↓
  I93 Integrate #93 reviewer/ledger additions; verify final combined tree
   ↓
  CLOSE Record engineering-only acceptance; no public release
```

| Stage | Coordinator action | Exit criterion |
|---|---|---|
| G0 | Refresh `main`, all PR heads/bases, reviews, modes, changed paths, rules and existing required checks | Pins either match or a documented delta invalidates/replaces affected evidence; all restrictions preserved |
| G1 | Prepare the separate gate patch and disposable exact-head/effective-tree/combined-tree checkouts; exercise missing-R, missing-browser, failed-job, stale-base, missing-artifact and gate-removal negative controls | Gate fails closed; all applicable suites pass; combined tree contains only approved payload plus separately reviewed gate paths |
| G2 | Obtain separate integration authority; adopt and require the validated gate through the repository's permitted process | Verifiable required-status enforcement exists before #82 lands; no product or release permissions are inferred |
| I82 | Revalidate #82 against the then-current `main`; integrate only after repository requirements and explicit authority pass | Original repaired producer and all R1/R2 tests preserved; exact landed commit passes mandatory native R; stop before #92 on any failure |
| I92 | After #82 is on `main`, retarget #92 from the Phase 1 branch to `main`; re-read its entire diff and reviews | Only the expected 12-path Phase 2 delta remains; accepted Phase 1 blobs are not duplicated, replaced or removed; exact head, actual-base integration and landed-commit browser checks pass |
| I93 | Revalidate #93 against the now-integrated product; integrate its four paths with original historical pins unchanged | New prospective gate validates the actual product; old reviewer workflow is not mistaken for current integration evidence; final combined tree and landed-commit suites pass |
| CLOSE | Append an integration receipt linking actual heads/trees, gate version, runs, checksums, protection snapshot and preserved holds | Engineering-only disposition; no automatic UI wiring, source intake, calibrated inference or publication |

**Stacked-branch rule:** never merge #92 into `coord/us-relative-phase1` as a shortcut. Preserve that branch until retargeting and ancestry checks finish. Prefer an ancestry-preserving method only when repository rules permit it. If the permitted squash/rebase method changes ancestry, compare the original #82→#92 delta with the new-base result; stop if Phase 1 changes reappear. A fresh coordinator candidate containing only the verified Phase 2 delta may then be prepared, with new exact-head evidence and an explicit mapping to #92. No force-push or silent history rewrite.

Re-read reviews after retargeting; GitHub warns that base changes can alter the commit timeline and make review comments outdated. [S11] Do not perform any retarget in this planning task.

## 5. Mandatory acceptance matrix

Counts below identify retained test inventories, not a license to replace them with a count-only assertion. Preserve test IDs, fixture hashes and expectations; additions are allowed with review, removals are not.

| Gate | I82 | I92 / I93 / combined tree | Required evidence |
|---|---:|---:|---|
| Phase 1 native R/Python/Node | 40 tests | 40 tests | `--require-complete`; no skips; R1/R2 cases retained |
| W4 core and bridge | 25 and 49 tests | 25 and 49 tests | Original synthetic lineage and weighting tests; the 49 include the 40 |
| #87 independent R1/R2 probes | 7 tests | 7 tests, retained pinned reviewer | Original test bodies/expectations, actual target-root receipt |
| Phase 2 Python / JS | Not yet introduced | 4 / 12 tests | Deterministic source-safe build, replay, export and state checks |
| Full model replay | Not yet introduced | 8 models / 6 Phase 1 blob pins | Independent Node source/model/receipt validation |
| Strict Chromium | Not yet introduced | 17 tests | Served loopback and native file replay, all five exports, keyboard, cancellation, missingness, corruption, 320/390 px and reduced motion |
| Independent contrast/calculation review | Not yet introduced | 7 methods | Historical 444 targets, broader 48 selections and export checks; source-row recomputation of 240 comparisons / 192 transitions |
| Official interchange / scientific holds | Required | Required | Existing source-contract and frozen inference-readiness guards unchanged |
| Required-status finalizer and provenance | Required | Required | Exact job identities, literal-success outcomes, nonempty matched receipts and actual protection requirement |

Keep all nine axe scans and original incomplete items. For the frozen interface, reuse the independently measured resolution only when HTML/CSS/catalogue and selector hashes match; otherwise require a new resolution. Text/graphic criteria remain 4.5:1/3:1 with unrounded comparisons and negative controls. Full WCAG, manual screen-reader, actual browser-zoom and Firefox/WebKit certification remain outside the accepted scope. [S3, S8]

### Known test entry points

These are future execution instructions, not tests claimed to have run during planning. Use separate restricted candidate/reviewer checkouts; install the pinned tested environment through an approved dependency cache or setup step. Analytical and browser execution must remain source-offline. Build only in a new temporary directory outside every repository.

```sh
# From the selected candidate checkout, after runtime and identity preflight:
python -m research.integration.w2_w4_w6.waggoner.run_tests --require-complete --receipt "$OUT/phase1.json"
python -m unittest discover -s research/longitudinal -p 'test_*.py' -v
python -m unittest research.integration.w2_w4_w6.test_w4_bridge -v
node docs/parallel-work/validate-contract.cjs
node docs/parallel-work/test-w1-w2-inference-readiness.cjs

# Additional mandatory commands once Phase 2 is in the declared candidate stage:
python -m unittest research.integration.w2_w4_w6.waggoner.phase2.test_build -v
python -m research.integration.w2_w4_w6.waggoner.phase2.build --out "$OUT/build"
node research/integration/w2_w4_w6/waggoner/phase2/verify_catalogue.cjs "$OUT/build"
PHASE2_BUILD_DIR="$OUT/build" node --test research/integration/w2_w4_w6/waggoner/phase2/test_views.cjs
python -m research.integration.w2_w4_w6.waggoner.phase2.test_browser \
  --build-dir "$OUT/build" --artifact-dir "$OUT/browser" --require-axe --axe "$AXE_JS"
python "$REVIEWER93/research/integration/w2_w4_w6/pr92_review/test_review.py" \
  --build "$OUT/build" --out "$OUT/independent" --axe-results "$OUT/browser/axe-results.json"
```

`OUT`, `AXE_JS` and `REVIEWER93` must be explicitly checked by the future wrapper; unset or invalid paths fail before execution. The #87 invocation and target-root environment must be taken from its pinned existing harness, not guessed. Provision R 4.3.3, Python 3.13.16, Node 22.23.3, Playwright 1.57.0, Chromium 143.0.7499.4 and axe-core 4.10.3 as the retained acceptance baseline; record actual binaries and dependency versions. An unavoidable runtime change requires a new compatibility receipt, not an undocumented substitution. No new data/model downloads.

## 6. Tree identity, safety and rollback

For each run record **event/status SHA**, candidate head, actual resolved base, tested tree, reviewer commit/tree, prospective gate commit, dependency blob hashes, test inventory, runtime versions, raw results and artifact SHA-256. A successful reviewer-PR check anchored to a different SHA is evidence, not the product's required status. Likewise, `git rev-parse HEAD` alone does not identify a working tree populated by `read-tree`.

Construct disposable trees without updating protected refs. Check conflicts and exact path/mode diffs; compare all unaffected trees by Git object identity. Product code, reviewer additions and prospective gate glue need a combined-tree receipt. If a head, base, dependency or runtime changes, rerun affected acceptance; do not blindly repeat unchanged historical tests merely to accumulate green badges.

The inspected Pages workflow is triggered by specified main-branch public paths or manual dispatch. None of the 31 integration paths or these plan documents matches that path list. [S12] Recheck all deploy-capable triggers before future integration; do not dispatch Pages, run `build_pages.py`, publish a release, sync the mirror or add generated HTML to a public tree. Repository branches/PRs contain code and engineering documents only, never source-bearing private artifacts.

On a conflict or failed preflight, stop the stage and preserve logs. Before integration, discard only disposable outputs. After an authorized integration, any failure freezes later stages; prepare a new coordinator revert PR in reverse dependency order (#93, #92, #82 as applicable) and test it. Do not reset `main`, force-push, weaken a gate, delete failed receipts or revert unrelated changes. A revert itself requires separate authorization and all nonpublication checks.

## 7. Completion and next executable task

**This plan is complete when:** live pins and path inventories are recorded; dependency order is acyclic; mandatory R/browser/contrast gates and enforcement gaps are explicit; retained archives match their digests; plan documents are validated and committed on a separate draft coordinator PR; all original PR heads and `main` remain unchanged.

**Integration remains NOT_EXECUTED.** Open prerequisites are prospective gate implementation/validation, a verified protection snapshot, a fresh combined-tree receipt and separate authorization to integrate. No additional user input is needed to finish the plan.

**Next instruction:** Implement the coordinator-only prospective integration gate and combined-tree dry-run checks for PRs #82, #92 and #93, retaining the #87 regression evidence and historical review pins, without merging, retargeting, changing branch protections, publishing or opening real transcripts.

## Source register

[S1] [PR #82 live record](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/82), repaired head and run `38769872958`.

[S2] [PR #92 live record](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/92), original stacked base and implementation run `38779954475`.

[S3] [PR #93 live record](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/93), executed reviewer and acceptance ledger; run `38792204591`.

[S4] [Pinned main commit](https://github.com/LystadJS/UNGA81-Transcript-Agent/commit/da4ab9ed11dba3693d11aa12f5333963b1b85478). Live `git/ref/heads/main` returned this SHA during planning.

[S5] [Existing coordinator evidence workflow](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/da4ab9ed11dba3693d11aa12f5333963b1b85478/.github/workflows/coord-w2-w4-evidence.yml).

[S6] [Phase 2 workflow](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/76fbfd73f440306dfd9fc72a6431704f7b09b45d/.github/workflows/coord-us-relative-phase2.yml), cross-checked in the supplied source archive.

[S7] [Independent reviewer workflow](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/3789018a0bd031d8bea65fd9b1973a8313bff314/.github/workflows/coord-pr92-independent-review.yml) and corresponding retained `test_review.py`.

[S8] [Committed engineering acceptance](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/3789018a0bd031d8bea65fd9b1973a8313bff314/docs/parallel-work/PR92_OFFLINE_ENGINEERING_ACCEPTANCE_2026-10-15.md).

[S9] Live GitHub GET `/repos/LystadJS/UNGA81-Transcript-Agent/branches/main/protection`: 403; GET `/repos/LystadJS/UNGA81-Transcript-Agent/rulesets?includes_parents=true`: empty visible collection. Access failure retained as uncertainty, not absence of controls.

[S10] [GitHub required-status-check documentation](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks), consulted 15 October 2026.

[S11] [GitHub base-retargeting documentation](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/changing-the-base-branch-of-a-pull-request), consulted 15 October 2026.

[S12] [Pinned Pages workflow](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/da4ab9ed11dba3693d11aa12f5333963b1b85478/.github/workflows/pages.yml); ownership and immutables follow the repository's existing `AGENTS.md` and `docs/parallel-work/OWNERSHIP.md`.
