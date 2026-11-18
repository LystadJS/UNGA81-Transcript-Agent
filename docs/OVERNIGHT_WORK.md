# Current work checkpoint

Updated 18 November 2026, America/New_York. The active objective is a usable
PowerTranscript-like reporting application, followed by broader diplomatic
workflows, with JavaScript-only browser execution, separate personal R/Python
tools, limited Hugging Face storage and a focused source tree.

## Publication boundary

On 18 November 2026 the user explicitly approved all merges from that point
onward. This standing authorization supersedes the former merge-approval blocker;
respect checks and repository protections, but do not request the same approval
again. Source #291/#292 and website #167 are merged. Cleanup #293 and website #168
have been retargeted to main; their publication and live verification are in progress.
The last verified live release before these merges was 1.54.0; do not claim a new
live release until deployed assets have been checked.

## Reviewable changes

| PR | Scope | Base / verification |
| --- | --- | --- |
| [Source #291](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/291) | Release 1.55.0: eight reusable briefing questions, original supporting passages and unanswered gaps | main; merged as `7c42c87`; all three hosted checks passed |
| [Source #292](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/292) | Release 1.56.0: one explicitly saved device report, verified replay and JSON fallback | main; merged as `29be705`; all three hosted checks passed |
| [Source #293](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/293) | Remove three historical generated snapshots and consolidate current status documents | main; applicable browser/numerical checks passed before this authorization update |
| [Website #167](https://github.com/LystadJS/LystadJS.github.io/pull/167) | 1.55.0 mirror, corrected source/release verification pins | main; merged as `f6d7254`; audit and regression passed |
| [Website #168](https://github.com/LystadJS/LystadJS.github.io/pull/168) | 1.56.0 mirror, storage module and archived evidence links | main; head `59cc403`; audit and regression passed |

Verify current checks before publication. Website #168 depends on source #292 and #293.
Do not open another equivalent PR or treat skipped post-deployment jobs as passes.

## Verified engineering work

Eight Node reporting contract suites and six Chromium reporting/archive suites
passed. The device test exercised actual IndexedDB save/reload/replay, cancelled
actions, corrupt data, quota failure, delayed saves, restricted-browser fallback
and mobile layouts. It also passed against the generated website mirror.
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
`cleanup/historical-report-snapshots`. The partial website checkout is
`/workspace/portfolio-site`, on `feature/un-device-reports`; unchanged absent
paths are marked skip-worktree. Preserve unrelated `assets/css/cv.css` work.
Use the existing sync script and explicit paths; never stage website deletions
from the partial checkout. Its Git trees can be written with `--missing-ok`
while retaining unchanged promisor objects; review the exact staged paths first.

1. Inspect hosted checks and any approval answers. Standing merge authorization is recorded above; preserve checks and protections.
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
