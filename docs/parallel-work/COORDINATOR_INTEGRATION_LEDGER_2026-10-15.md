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
