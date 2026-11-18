# Current work checkpoint

Updated 18 November 2026, America/New_York. The active objective is a usable
PowerTranscript-like reporting application, followed by broader diplomatic
workflows, with JavaScript-only browser execution, separate personal R/Python
tools, limited Hugging Face storage and a focused source tree.

## Publication boundary

On 18 November 2026 the user explicitly approved all merges from that point
onward. This standing authorization supersedes the former merge-approval blocker;
respect checks and repository protections, but do not request the same approval
again. Source #291/#292/#293 and website #167/#168 are merged. Release 1.56.0
is verified live at both the source Pages URL and preferred portfolio mirror.
All 194 checked portfolio files (193 manifest entries plus the manifest itself)
matched their expected SHA-256 hashes. Five reporting suites passed against the
actual live portfolio, using fictional sources and no reserved transcripts.

## Current increment — 1.57.0

`feature/device-report-library` extends the single device copy into an eight-report
library, sharing 25 MB of UTF-8 report JSON. The IndexedDB v2 upgrade preserves
and moves the v1 slot atomically; no duplicate source store remains. Write/count
limits and report-revision checks share transactions. Titles, dates and sizes are
listed without automatic source opening. Stale tabs must refresh before opening,
replacing or removing a changed report. Report/preference schemas are unchanged.

Local storage tests passed the existing save/replay/failure paths plus multiple
reports, title escaping, stale tabs, concurrent storage bounds, blocked-tab
migration/recovery and upgrade quota-error rollback. The four other reporting
browser suites, syntax/diff checks and the allowlisted 202-entry build passed.
Source/mirror publication and live acceptance are in progress. No Hugging Face data, model, dependency or external API is added.
The last verified live release remains 1.56.0 until the new deployment is checked.

## Published changes

| PR | Scope | Base / verification |
| --- | --- | --- |
| [Source #291](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/291) | Release 1.55.0: eight reusable briefing questions, original supporting passages and unanswered gaps | main; merged as `7c42c87`; all three hosted checks passed |
| [Source #292](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/292) | Release 1.56.0: one explicitly saved device report, verified replay and JSON fallback | main; merged as `29be705`; all three hosted checks passed |
| [Source #293](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/293) | Remove three historical generated snapshots and consolidate current status documents | main; merged as `a4346e8`; browser/numerical checks passed at the exact reviewed head |
| [Website #167](https://github.com/LystadJS/LystadJS.github.io/pull/167) | 1.55.0 mirror, corrected source/release verification pins | main; merged as `f6d7254`; audit and regression passed |
| [Website #168](https://github.com/LystadJS/LystadJS.github.io/pull/168) | 1.56.0 mirror, storage module and archived evidence links | main; merged as `4aa57a7`; audit and regression passed |

These five PRs are complete. Do not open equivalent replacement PRs. Treat skipped
post-deployment jobs as skipped; the live verification above was executed directly.

## Verified engineering work

Eight Node reporting contract suites and six Chromium reporting/archive suites
passed. The device test exercised actual IndexedDB save/reload/replay, cancelled
actions, corrupt data, quota failure, delayed saves, restricted-browser fallback
and mobile layouts. Five suites also passed against the actual deployed portfolio:
meeting reporting, device storage, replacement protection, ZIP packages and archive
handoff. These tests use synthetic sources and do not establish diplomatic accuracy.
The public build contains 202 entries; all 193 mirror files match their manifest.
These are synthetic engineering checks, not diplomat or model acceptance.

Three generated comparison snapshots were verified against public commit
`5d0ca060b7cfb90509b47ed4ac0c87a532eb637e`. Removing current-tree copies saves
16,269,686 bytes. All nine doc/renderer/report links are pinned to that immutable
archive; archived inputs regenerate all three current HTML audits byte for byte.
Git history remains intact. Frozen D1 artifacts, historical checksums, source
corpora and current R/Python tools were preserved. No Hugging Face data was added.

## Workspace and next work

The source checkout is `/workspace/UNGA81-Transcript-Agent`, currently on
`feature/device-report-library`. The partial website checkout is
`/workspace/portfolio-site`, on `feature/un-device-reports`; unchanged absent
paths are marked skip-worktree. Preserve unrelated `assets/css/cv.css` work.
Use the existing sync script and explicit paths; never stage website deletions
from the partial checkout. Its Git trees can be written with `--missing-ok`
while retaining unchanged promisor objects; review the exact staged paths first.

1. Continue from this verified 1.56.0 release. Standing merge authorization is
   recorded above; preserve checks and repository protections.
2. Continue dependency-based cleanup; the larger `un/` fixtures have live
   validation references and must not be deleted merely because they are old.
3. Complete representative diplomat usability sessions and evaluate any optional
   generative reporting separately from the existing deterministic reader.
4. Preserve all 37 reserved meetings and model acceptance gates. Do not infer
   national positions from collective statements, mentions or text similarity.

## Historical receipts

Earlier activation logs, expired scheduling instructions and detailed receipts
are preserved in the [archived checkpoint](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/44cf6ba28a5b38693547407a4ac2414e6b607c82/docs/OVERNIGHT_WORK.md).
They are evidence of their original dates and scope, not current instructions or
fresh acceptance. Keep this file a current handoff rather than an append-only log.
