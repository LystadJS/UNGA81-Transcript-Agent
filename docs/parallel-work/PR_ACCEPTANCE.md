# Coordinator PR acceptance checklist (required for every worker)

Every check is recorded as **PASS / FAIL / NOT RUN / NOT APPLICABLE** with evidence; a blank field does not imply PASS. A PR may be draft or accepted as engineering-only; do not merge merely because it has no Git conflict.

## 1. Fresh repository and ownership
- [ ] Fetch latest `main` immediately before review; record full base and head SHA, diff and exact changed filenames from GitHub; repeat after any head movement.
- [ ] Confirm branch matches `OWNERSHIP.md`; every added/modified/deleted/renamed path falls within the one exclusive worker namespace. Reject overlap and altered shared or frozen files.
- [ ] Compare upstream interfaces with latest `main`, including `un.browser.corpus.v1`, `un.latent-comparison.v1`, `un.passage-corpus.v1`, `un.review.v1`, and the v1 adapter schema as applicable.
- [ ] Check open PRs for semantic collisions (same browser interface, model ID or output responsibility), not only overlapping filenames. Never force-push or enable auto-merge.

## 2. Source and privacy gate
- [ ] Recompute/verify relevant original *development* source/text and selection hashes; record hash basis, bytes/text distinction, source IDs and read-only upstream version.
- [ ] Assert no transcript content was opened for **any** of the 37 reserved October 5–6 meetings; preserve metadata-only lock and existing seal, original hashes, human decisions and O1–O5 gates.
- [ ] Confirm tests contain only synthetic data; public files include **no** original transcript text, source-bearing row-level analytical artifacts, private reviews, cached vectors, credentials, secrets or annotated passages.
- [ ] Audit missing and unavailable inventory/source content without collapsing it into a substantive absence. Unresolved speaker/country remains explicitly unverified.

## 3. Reproducible method evidence
- [ ] Provide deterministic command(s), fixture SHA, code commit/version, dependency/runtime versions, seeds and resource limits; test independent restart/replay when relevant.
- [ ] Test known-structure and negative controls, corrupted hashes, duplicate IDs, missing parents, invalid offset spans, label collisions, wrong representation basis and failed/partial fits.
- [ ] Account for **all attempted** fits, non-converged runs, exclusions, insufficient observations and unassigned/noise observations; report denominators before and after selection.
- [ ] Verify correct unit of dependence (meeting/source/speech where independently established), weighting objective and training/evaluation leakage safeguards. No source-group bootstraps described as independent source replication without support.
- [ ] Store explicit method limitations: stability ≠ significance; similarity ≠ stance; co-assignment ≠ policy agreement; embedding/display distances ≠ influence; nil evidence ≠ zero issue occurrence.
- [ ] Validate `un.parallel-analysis.v1` structural schema **and** relational invariants from `INTERCHANGE_V1.md` using synthetic tests (schema checks alone do not validate hash lineage).

## 4. CI and integration
- [ ] Inspect *every* applicable GitHub Actions check for the latest head SHA, run ID, conclusion, failing/blocked/skipped jobs and relevant logs; do not claim PASS when only historical logs exist.
- [ ] Run appropriate existing regression suites for affected consumers (browser numerical, latent, corpus, source and reviewed units); distinguish inherited from newly executed evidence.
- [ ] For W5/W6/W7, render-check keyboard/mobile, failed/empty/abstention states, saved-run replay, provenance/source URLs, accessibility and no-refit behavior in an actual browser.
- [ ] Re-fetch `main` and recheck changed paths/heads **immediately before merge**. Reject stale/incompatible PRs. Merge with the exact expected PR head SHA.
- [ ] After merge verify `main` SHA and tests; increment shared roadmap only via a separate coordinator-owned change, not a worker overwrite.

## 5. Public deployment (only when source/browser integration accepted)
- [ ] Coordinator builds source browser with `python3 tools/build_pages.py <fresh-output-dir>`; verifies public asset list and manifest hashes.
- [ ] No private text-bearing artifacts in build output. `site/release.json` and current public manifests updated only in coordinator PR after accepted interface change.
- [ ] Mirror with website repo's existing `scripts/sync_un_project.py`, verify resulting website commit SHA, live `/un/transcript-agent/` assets and content hashes against approved build.
- [ ] Record live checks, propagation/cache caveats and rollback reference. **No website mirror before source PR passes.**

## PR handoff template

```text
Workstream / branch / PR / base SHA / head SHA:
Exclusive path list:
Source schema + hashes + selection + meeting/speech provenance:
Adapter contract version + model/representation version:
Synthetic fixtures; seed; runtime; exact test commands/results:
Attempted / successful / skipped / failed / unassigned denominators:
Nulls, sensitivity, source-dependence and limitations:
CI checks/run IDs; inherited vs newly executed:
Public privacy/holdout/frozen-gate declaration:
Coordinator-only integration requests (files NOT changed by worker):
Release status: engineering-only / integration candidate / withheld
```
