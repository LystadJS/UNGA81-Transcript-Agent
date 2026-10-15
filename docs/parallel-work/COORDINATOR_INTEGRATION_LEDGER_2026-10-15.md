# Coordinator integration ledger — 2026-10-15

Baseline main: `55f7c03c0944865e0f273f9d05648936174fdb31`.
Authority: `AGENTS.md`, `docs/NEXT_STEPS.md`, `docs/parallel-work/OWNERSHIP.md`, `PR_ACCEPTANCE.md`, `INTERCHANGE_V1.md`.
Review scope: repository metadata, exact PR changed paths, and Actions run conclusions. Full patch/security review, local regressions and deployment checks remain NOT RUN. **No PR in this ledger is newly approved for merge.**

| PR | Head SHA | Branch/base | Files / interface | Exact-head CI | Decision / blockers | Merge commit |
|---|---|---|---|---|---|---|
| #25 | `1759349c117de3606182746538d437f7fafa1de2` | coord/general-debate-p0-p1 / main | 10; source acquisition; historical metadata | FAIL 37816285803 | HOLD draft; nonmergeable, failed workflow, stale baseline, source validation outstanding | — |
| #32 | `83f2fe96baed9291cf5667295fd168c1f96519cc` | coord/p2-secure-original-pvs / main | 3; secure PV workflow and retrieval | PASS 37844727875 | HOLD draft; nonmergeable, stale baseline, security/source review | — |
| #40 | `d55f060b6409ce7ad09142d0b90853ba00d5b5f4` | coord/p3-harvard-v14-sourceframe / main | 17; provenance and historical W1 preflight | PASS 37846169268, 37846169270 | HOLD draft; nonmergeable, stale baseline, original-source and inference restrictions | — |
| #56 | `e7b6ddb4c6e83b6104e715e436688f1088c3b823` | coord/c5-w2-w4-research-browser / main | 12; research browser W2/W4/W6 view | PASS 38458651616, 38458650941, 38458650772, 38458650825, 38458650844, 38458650819 | HOLD draft; explicit distinct release authorization withheld, no deployment | — |
| #59 | `c40f7a60d923c118ceda8f7d53a255ee5881544c` | coord/w4-p1-original-pv-intake-20261013 / coord/w4-expanded-year-design-20261013 (#52) | 5; historical source authentication | PASS 38460258716 (interchange only) | HOLD; stacked, source-method approval/real source checks not independently repeated | — |
| #61 | `1c79dbc62840d9754a0bb9691ad168505ef2e1f4` | coord/w4-p2-independent-pv-quality-audit-20261013 / coord/w4-p1-original-pv-intake-20261013 (#59) | 6; audit, source selection | PASS 38477579330, 38477579226 | HOLD draft; depends on #59 and separate source gate; no inference authorization | — |

Already merged before this review (do not count as coordinator merges here): #51 `18bc4ae15c88d51ce06f3e5f822ccd5cca83641a`; #52 `55f7c03c0944865e0f273f9d05648936174fdb31`; #58 merged; #60 merged; #62 merged. Verify exact merge SHAs for #58/#60/#62 before downstream release operations.

## Dependency and interface decision

- #52 is already on main; #59 targets its old source branch instead of main; #61 targets #59. Rebase/retest/review serially; do not squash stacked branches without full effective-diff inspection.
- #25/#32 overlap in the `research/source_acquisition/general_debate/` functional area; compare semantics and versioned source identities before acceptance.
- #40 is a separate coordinator provenance proposal; assess its legacy source binding against merged #51 and newer historical W4 protocols.
- #56 changes shared browser/build surfaces and can trigger public Pages/mirror delivery; keep withheld pending the distinct owner/coordinator release authorization recorded in its PR.
- New workers: historical source comparability; semantic representations; null calibration; longitudinal inference; research visualization; supervised annotation/evaluation; diplomatic readouts; reproducibility/security. For each submission record exclusive paths, base/head, schema and hash basis, fixture/attempt denominators, CI run IDs, exact-head and merge commit. No submission received in this coordination snapshot.

## Hard exclusions

No 37 reserved Oct 5–6 2026 transcript reads, no source checksum rewrites, no changes to human decisions, D1 O1–O5, `research/reference_tests/evaluation-lock.json`, and no public original texts, private source-bearing rows, vectors, keys or individual empirical outputs. `un.parallel-analysis.v1` requires original source/selection hash basis, relational provenance, missingness and engineering-only publication lock. Engineering PASS never unlocks empirical inference, government stance claims or publication.

## Acceptance and delivery evidence

- PR changed-path inventories: PASS (six open PRs).
- Exact-head Actions run conclusions: PASS five PRs, FAIL one PR (#25); run/log contents NOT independently audited.
- Full PR patch, method and privacy audit: NOT RUN.
- Node/Python/R/Shiny/browser local regressions: NOT RUN.
- Post-merge CI, Pages build, portfolio mirror, deployed hash verification: NOT RUN (no authorized merges).
- Coordinator branch ledger publication: engineering-only documentation; not a release authorization.

## Coordinator refresh — 2026-10-15 12:35Z+ (supersedes open-state snapshot above)

**Verified new main:** `ecfc201ccfcd442c9f29e92777c1d9241beab4d9` (three commits newer than ledger baseline). PR #63 was merged as `1e78e81a2270a6b643b9c344863199107e9138f2`. The 40 newly changed paths on main encompass the previous C5 browser and historical-source integrations. The new browser release metadata PR #72 explicitly records #56 source merge `ecfc201ccfcd442c9f29e92777c1d9241beab4d9`; historical P1/P2 are no longer listed as open. This updated ledger makes **no new scientific or release gate assertion** about those merges. Confirm corresponding historical merge records and latest-main CI before asserting downstream readiness.

| PR | Exact head | Current disposition | Latest exact-head CI |
| --- | --- | --- | --- |
| #64 Historical source comparability | `f940800612858e0066e3fc0c4bbfc1f50f25ac10` | DRAFT; private source validation not run; schema review pending | NOT RUN/no returned runs |
| #66 Semantic representations | `f13b8bce9dc3c90e033043fc8173aa6bb59d2342` | DRAFT; model checkpoint/revision/hash and real inference not complete | NOT RUN/no returned runs |
| #67 Null calibration | `b1f402eb70efbeda024ca363fd1c04988e20c140` | DRAFT; nuisance estimator and independent calibration incomplete | NOT RUN/no returned runs |
| #68 Temporal calibration v2 | `c12d93edf8b5bf6fa0dc1ad817d65bd838a949f3` | DRAFT; 0/18 temporal-correlation recovery unresolved, no scientific eligibility | PASS #38734471164 (synthetic/interchange only) |
| #69 Research visualization v2 | `a096aebd623e3249494ba552701fb482f524ef51` | DRAFT; browser QA, complete heatmap and accepted adapter missing | PASS #38735107775 (latent acceptance only) |
| #70 Diplomatic readouts | `e9b309a7ee582a732a94d2ae7bac9590e1d58e54` | DRAFT; tests/verified source binding not complete | NOT RUN/no returned runs |
| #71 Reproducibility/security | `096dfe1f63819a6bd6a56d9222d43c603bda548f` | DRAFT; tests and full-schema/replay validation not complete | NOT RUN/no returned runs |
| #72 C5 synthetic release metadata | `cfa5c4df0f9f88bb706c16b5c72d4720c212ce64` | OPEN, non-draft; changes only `site/release.json`, mergeable; review release-metadata integrity and mirror prerequisites separately | PASS #38735797270 (latent acceptance) |
| #25 Historical source acquisition | `1759349c117de3606182746538d437f7fafa1de2` | DRAFT; old source retrieval failure unresolved | FAIL #37816285803 |

Eight new worker PRs (#64, #66–#71 plus an expected supervised workstream not yet present in the open PR list) are not scientifically accepted by this record. Seven observed worker PRs listed above plus additional pending worker submission: **do not assume missing PR was delivered**. CI run visibility is not equivalent to full test coverage; all unexecuted suites remain NOT RUN. Existing 37 reserved 2026 meeting transcript lock, frozen decisions, O1–O5 gates, original source bytes/hashes, private artifacts and empirical-publication restrictions remain unchanged.

**Next unblocked sequence:** independently inspect each worker effective diff and ownership list, prioritize source comparability and privacy/reproducibility; execute synthetic suites at exact heads in a suitable runner; make narrowly scoped worker fixes on their owned branches or coordinator-only integration revisions; merge only on full acceptance. For #72, examine release JSON metadata and required deployment workflow before any merge or mirror. No repository-wide regression, site build, Shiny or deployed SHA check was performed in this ledger refresh.

## PR #64 final engineering acceptance reconciliation — 2026-10-15

**Decision: HOLD DRAFT; DO NOT MERGE (CI provenance gate incomplete).** Latest verified main `1af11061e3fa65d51b28d42a1b98bef250b6168b`, unchanged since effective-tree validation. PR #64 head `bbac08871eba94c02900e3653746e19a2a346408`; seven exclusive worker files under `research/source_comparability/**`. PR remains draft, mergeable but **not accepted** under `PR_ACCEPTANCE.md` section 4.

**PASS — native effective-tree integration:** Coordinator-only validation commit `0cc01b7462a243a9b8391997250aac1d0d32f911` starts at the exact main SHA, copies all seven original PR #64 Git blobs unmodified, and adds only an isolated coordinator workflow. GitHub Actions [run #38749698104](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38749698104), job `116472543733`, completed SUCCESS. Real `actions/checkout@v4`, native Node 50/50 audit+integration, source inventory 14, interchange 1 positive+13 negative, P2 Harvard 4, P2-to-W1 7, W1 historical-link success, W4 P2 source-aggregate success; Python P3 6 and P5 8 pass. No original private data read; W4 aggregate records 1,574 verified, 10 unresolved, calibrated empirical inference/public release FAIL.

**NOT RUN — exact PR-head check:** GitHub returned zero Actions workflow runs associated with PR source commit `bbac08871eba94c02900e3653746e19a2a346408`. A successful coordinator effective-tree check demonstrates tested content compatibility but is a **different commit** and cannot be represented as a check run on the exact PR head. Existing `PR_ACCEPTANCE.md` requires checking every applicable GitHub Actions run for the latest head. No special waiver has been authorized. Do not conflate mergeable state, draft state and engineering sign-off.

**Scientific holds unaffected:** private original-PV/Harvard bytes and source selection not independently reauthenticated here; no country-level response positivity or MAR/MNAR identification, source-translation/genre/roster bridge, calibrated temporal inference, model fit, publication or held-out transcript access. The 37 reserved Oct 2026 transcripts, human decisions, D1 O1–O5 and provenance locks are unchanged.

**Next executable action:** arrange coordinator-owned exact-head check trigger or an accepted documented CI equivalence rule without worker workflow/ownership changes; inspect check logs and refresh main/head immediately before any possible protected exact-SHA merge. Continue draft hold until then.
