# PR #36 — supervised country-position engineering acceptance

**Coordinator scope and decision, 8 October 2026.** This ledger records the source-bound, **synthetic-only** engineering acceptance review for [PR #36](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/36). It is **not** an empirical, policy-position, statistical inference or public release decision. It must not be read as permission to open the 37 reserved meetings.

## Exact inputs and recorded evidence

- Baseline at initial review: `main` `03177cdd55ec0e93d479960e8280f9747df02a55`.
- PR #36 head initially reviewed: `791f10f61046c1e128c9907099ad84eeddf05f01`, after a non-force merge with that baseline; `main...head` comparison had zero commits behind and 16 changed files.
- Exactly 15 files were newly added in the private-safe research implementation directory `research/supervised_country_positions/**`, plus one new read-only `.github/workflows/supervised-country-positions.yml`. No shared source, browser loader, existing workflow, D1 adapter or existing research kernel changed.
- Exact-head CI: [GitHub Actions run 37833249784](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/37833249784), **completed: success** on head `791f10f61046c1e128c9907099ad84eeddf05f01`. Three completed successful jobs: Node/Python `113503710376`, R `113503710105`, and Chromium `113503894856`. Historical failed runs were corrected, not substituted for the latest passing run.
- Workflow exception: the coordinator separately and explicitly accepts **only PR #36's named, new, read-only synthetic CI workflow** in `OWNERSHIP.md`, subject to rechecking unchanged privileges, paths and accepted tests just before merging PR #36.

## Acceptance gates (PASS / FAIL / NOT RUN / NOT APPLICABLE)

| Requirement | Decision | Evidence and limitation |
| --- | --- | --- |
| Fresh full filename list, source-code scope and namespace | **PASS, recheck at merge** | GitHub PR listing and main/head compare; 15 new research files, exactly one new separately authorized CI workflow. No W1–W7 ownership overlap. Other open source/inventory and graph PRs have distinct code/output responsibilities. |
| Source schemas and method isolation | **PASS for engineering prototype** | `un.review.v1` template import and unchanged M12/M17 R kernels. Separate `un.country-positions.evidence.v1` / `un.country-positions.report.v1` are synthetic-only; no conflation with `un.parallel-analysis.v1` partition memberships. |
| Development original-source or holdout bytes | **NOT APPLICABLE to synthetic-only PR** | No actual UN original document was read, fitted or committed. Original development/meeting hash recomputation and sealed 37-meeting evaluation are deliberately not attempted; synthetic source hashes cannot establish independent real-source accuracy. |
| Private content and publication barriers | **PASS for changed-code scope** | No real source text, private annotation rows, credentials, cached embeddings or model outputs included; `dataset_kind=synthetic_engineering` and `publication_eligible=false` enforced; source text hash and Unicode offset guards and private export refusal tested. |
| Native Node.js 22 engineering tests | **PASS** | 17/17 tests, source integrity, counts, missing/conditional/collective evidence, duplicate family and output guards. |
| Native Python 3.11 review tests | **PASS** | 6/6 private packet/source review tests. Owner decisions are not created or rebranded as independent gold. |
| Native R M12/M17 | **PASS** | Four native assertions: both existing research kernels run on synthetic input; real input and cross-split country overlap rejected. R 4.6.1 and installed glmnet. |
| Real browser QA | **PASS** | Four Chromium 154 / Playwright 1.55.0 scenarios at 1440 px and 390 px: visible/hidden, keyboard, imported files, local draft export/replay, source inspection, invalid input refusal and **zero external source requests**. |
| Reproducible build/fixture and failures | **PASS with scope limit** | Node generated invented report; native Python asserted synthetic-only/unpublished outcome. Earlier `NODE_PATH`, HTML `hidden` CSS and nested R source-loader failures have fixes and later exact-head passing tests. |
| Missingness, counts and source dependence | **PASS for synthetic protocol only** | Observations/cells and excluded-ledger explicit; a source-family contributes one stance opportunity. No confidence interval or source-level independence claim. |
| `un.parallel-analysis.v1` schema/relational acceptance | **NOT APPLICABLE** | This producer is expressly supervised, not a W1–W7 clustering/latent interchange exporter; **must not** encode political stance probabilities as GMM/NMF/consensus memberships. |
| Existing shared browser/latent/packaged D1 regression | **NOT APPLICABLE to additive namespace** | Shared modules, import paths, public asset builder, package manifests, and D1 O1–O5 producer unchanged. New standalone HTML stays outside `site/**`. |
| Real stance accuracy, independent external replication and calibration | **NOT RUN; WITHHELD** | No independently established human gold, representative reference-sample denominators, source-role adjudication, external held-out evaluation or calibrated country-level inference. |
| Website deployment and mirror | **NOT APPLICABLE** | No production Pages asset, site release, or website mirror edited or authorized. |

## Interpreting this approval

The feature demonstrates that code can carry **explicit policy propositions**, collect blind annotations, run pre-existing M12/M17 on **fictional inputs**, and render **fictional** source-linked country agreement. The apparent US/China reference actors in fixtures are invented labels, not estimates of real diplomatic alignment. Topic similarity is not a policy stance; policy-agreement edges are not alliances, influence, or causal ties.

**Engineering-only acceptance is appropriate provided the named CI workflow ownership exception is accepted and all exact-head checks pass immediately before merge.** The permitted merge changes neither the frozen O1–O5 gates nor any real-data fitting or publication rule. If either CI or the namespace exception fails, stop; do not merge.

## Closing actions required before declaring merged

1. Merge this coordinator-only ownership/acceptance documentation change; confirm its new `main` SHA and applicable contract CI.
2. Reconcile PR #36 against that `main` without a force push. Re-fetch all paths and re-run/inspect applicable exact-head GitHub Actions checks. Confirm the PR remains eligible for engineering-only review and has no incompatible upstream changes.
3. Merge PR #36 with `expected_head_sha` only if the checklist is green. Verify the merge SHA, final `main`, and that `site/**`, `un/**`, frozen source locks and portfolio mirror remain unchanged.
4. Do **not** deploy, unlock real source fitting, create national positions, or promote synthetic assertions into empirical claims.

**Release status: ENGINEERING-ONLY / REAL-DATA AND PUBLICATION WITHHELD.**
