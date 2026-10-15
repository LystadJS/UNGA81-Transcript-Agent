# Research visualization/browser validation v2

**Status:** Draft PR #69; engineering-only; synthetic-only; no merge/deployment authorization. Every file is under `site/experimental/research-validation-v2/**`. No transcript material, actual UN actor/source relationships, refitting, public-manifest changes, or edits to accepted W5/W6 kernels.

## Accepted semantics and integration

- The source-of-truth contract is `docs/parallel-work/INTERCHANGE_V1.md`. The accepted source-bound W1/W2 frame and `site/research-consensus.js` supply **weighted conditional co-assignment** (coassigned weight / assigned-both weight) with separate planned, missing, noise and failed opportunities, not the older W6 equal-family illustrative mean. The renderer **does not recalculate** W2 association or fit any models.
- C5 PR #56 **was merged** as synthetic engineering-only integration at `ecfc201ccfcd442c9f29e92777c1d9241beab4d9` (verified against `main` `1af11061e3fa65d51b28d42a1b98bef250b6168b`). Its accepted W4 five-file original-source receipt, saved rigid/pinned alignment and meeting/genre weights remain authoritative. Historical unverified/nullable-date W4 observations cannot be projected into legacy v1.
- `adapter.js` provides `fromW2(env, sidecar, {validateW2})`, `fromW4(files, {validateW4})`, `fromW6Themes(env, panel, {validateEnvelope, validatePanel})`. Adapter calls the **independently accepted validator** supplied by the importing coordinator and checks source/selection/representation compatibility and synthetic-only status before building a display envelope. Mock validators in local tests do not authenticate real files. Never bypass the upstream originals/receipt check.
- `renderer.js` accepts only the explicit `un.research-validation-v2.synthetic` fixture schema, `fixture_kind: synthetic`, `publication_eligible: false`, `evaluation_role: engineering_only`. The full source inventory is retained, including missing, failed, excluded and unattributed source groups. It fails closed on forged hashes, unknown/duplicate source IDs, missing pair opportunities, ill-typed or incorrect denominators, omitted family/failure ledgers, negative weighted prevalence, invalid period gates and inappropriate fit comparisons. Source/population IDs and observed zeros remain distinct from missing evidence.
- Four SVG views with accessible corresponding numeric tables: consensus pair matrix (missing/unstable and method-family drilldown), country×latent-theme profile (not stance), longitudinal actor-period plot (uncertainty, missing periods and failed alignment withholding), and method comparison (all attempts, successful/failed/skipped/unassigned). Source identity, SHA-256, source hash basis, selection hash, representation, review and exclusion reasons are available via provenance inspection. Illustrative synthetic SVG geometry is not causal, positional or inferential.
- Deterministic `exportJSON` and `htmlDocument`/SVG outputs and `index.html` saved-run replay do not require network storage. Changing an uploaded run clears the old result and invalidates export availability. Browser URLs and links are disabled for invented sources; never display private transcript/row-level material.

## Validation evidence (2026-10-15)

Local pre-push run: `node --test site/experimental/research-validation-v2/tests.cjs`: **54/54 PASS** (Node 22.16.0). Fixture seed: none; all synthetic values fixed, deterministic. Browser: `python site/experimental/research-validation-v2/browser_smoke.py --output /tmp/rv2-browser-check`, Playwright/Chromium, 1440×900 desktop and 390×844 mobile: **PASS with fallback**. The execution environment blocks navigations to localhost, file and data URLs with `ERR_BLOCKED_BY_ADMINISTRATOR`; the QA script injects the actual project HTML scripts/CSS/fixture into Chromium using `page.set_content`, validating rendered SVG/tables, keyboard Enter inspection, export/replay, source provenance, stale/invalid data clearing and horizontal overflow without claiming a normal served-page navigation. No original sources accessed; no empirical fits executed.

GitHub connector supports commit/push; execution environment cannot resolve `github.com` for native `git clone`. The browser fallback and upstream integration mean **full independent coordinator acceptance remains withheld**. Do not infer CI success for this worker from a generic latent numerical workflow.

## Deterministic commands

```bash
node --test site/experimental/research-validation-v2/tests.cjs
python site/experimental/research-validation-v2/browser_smoke.py --output /tmp/rv2-browser-check
python -m http.server 8000
# Open http://localhost:8000/site/experimental/research-validation-v2/ in an unrestricted browser
```

## Coordinator-only integration patch proposal (do not make these edits in worker PR)

1. After exact-head review, add a **separate nav link** from `site/research.html` to the standalone v2 demo, and copy the new isolated assets under `site/experimental/research-validation-v2/**` in the approved build allowlist. No unbounded recursive publish.
2. For actual validated synthetic W2 imports, call `UNResearchConsensus.validate(originalEnvelope, originalSidecar)`, then `UNResearchValidationV2Adapter.fromW2(envelope, sidecar, {validateW2: UNResearchConsensus.validate})`. Preserve source ID+text hash joins and original weighted ratio.
3. For W4, call C5 original five-file reader/validator `UNResearchEvidence.loadW4Files(files)` (which checks exact SHA256 and saved alignment); only then `fromW4(files, {validateW4: ...})`. Refuse source or selection changes without a new reviewed fit. Do not convert real historical W4 inventories into synthetic.
4. Reuse accepted W6 `validateEnvelope` and `validatePanel` before `fromW6Themes` and reject incompatible component/observation populations.
5. Coordinator runs actual served-page desktop/mobile/keyboard QA, W1/W2/W4 original source and relational regression suites, checks asset privacy and latest-head CI, then separately assesses release/Pages/portfolio mirror authorization.

**Protected:** 37 reserved October 5–6 transcripts, private originals, D1 O1–O5, frozen research null gates, 24 owner decisions, original SHA records, `site/release.json`, `tools/build_pages.py`, website mirror. No observed national positions, coalitions, issue absence, source-level independent replication, p-values or causal movement established.

## GitHub main reconciliation — 15 October 2026

The initial October 15 draft handoff described C5 PR #56 as unmerged. Subsequently GitHub committed its synthetic engineering integration on `main` at `ecfc201ccfcd442c9f29e92777c1d9241beab4d9` and coordinator ledger `1af11061e3fa65d51b28d42a1b98bef250b6168b`. Treat the PR #56 description's older 'unmerged' heading as historical; the latest Git commit history is authoritative. The new v2 PR does **not** replace the merged C5 read-only source validators, edit their consumer/renderer files, or authorize the separately tracked release manifest / website mirror. Coordinator should review duplication and integration scope before merging this worker. All source-privacy, 37 reserved transcripts, D1 O1–O5, W1/W2 inference G01–G13 and W4 temporal identification restrictions continue.
