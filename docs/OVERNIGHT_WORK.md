# Current work checkpoint

Updated 18 November 2026, America/New_York. Continue the PowerTranscript-like
reporting application and broader feasible diplomatic workflows with JavaScript-only
browser execution, separate personal R/Python tools, bounded Hugging Face storage
and a focused source tree. Full DiploTools parity is not established.

## Standing authorization

On 18 November the user explicitly approved all merges from that point onward.
This supersedes the former merge blocker. Merge tested project PRs and publish
the required mirror without repeating that approval request; respect repository
protections, later user instructions and the scientific/source gates in AGENTS.md.

## Verified release 1.62.0

| PR | Change | Checked head / merge |
| --- | --- | --- |
| [Source #307](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/307) | Add saved sources without replacing current work | Three checks passed at `1a89682`; merged `24e1e42` |
| [Website #175](https://github.com/LystadJS/LystadJS.github.io/pull/175) | Canonical mirror, source/release pins and live addition test | Audit/regression passed at `4b4279a`; merged `5fab209` |

Both public URLs serve 1.62.0. All 195 checked portfolio files (194 manifest
entries plus the manifest) match expected SHA-256 hashes. Eight browser suites
pass against the actual preferred URL with fictional sources: reporting, source
addition, replacement, packages, device library, archive handoff, Word and print/PDF.
The source-addition suite also passes at the original source URL. No skipped PR
live-verification job is counted as a live pass.

Add sources from JSON extends an existing report using original-bound collections
or supported saved-report files. Current settings, questions, global/passage notes,
appendix and meeting selections are retained. Incoming report annotations and
preferences are not copied. All its loaded sources remain, including unchecked
meetings; its selected meetings are checked. No source request or automatic save
occurs. New evidence invalidates prepared exports until preparation.

Source validation and the combined ten-bundle/100-meeting/15,000-passage/25 MB
source bounds remain unchanged. Before committing, the complete resumable JSON
is measured in UTF-8 with current settings, notes and selections. Overlapping
meeting identities/revisions are refused, including unselected bundles. There is
no partial merge or silent source replacement. Invalid/reserved/corrupt files,
file/state-size failures and stale operations keep current work. Unfinished question
fields and focus survive an addition; edits and newer source actions supersede
older pending additions. Saved report v4/preference v2 and device-library limits
are unchanged.

Local validation passes 256 Python tests and eight synthetic browser suites,
plus source-addition, country and package contracts. Cases cover original-byte
verification, true revised sources, all-bundle overlap, reserved/corrupt data,
foreign-annotation exclusion, unselected source retention, existing selections,
notes/appendix, exact saved-JSON bytes, incomplete editor fields/focus, delayed
edits/older operations, stale exports, mobile and no transcript requests. The
usability generator now supplies a nonoverlapping fictional report with a distinct
incoming assessment, alongside the original single/two-meeting files. The generated files were checked
against the production registry/policy: the additional file appends and the
overlapping two-meeting file is refused. No actual
participant session or diplomat acceptance is claimed.

The public build remains 203 entries and the mirror 194 files. Four assets and
the manifest change; sync is idempotent. Core/main script URLs are versioned; no
application file, dependency, model, server, upload or Hugging Face storage is
added. All 2,077 R-package checksums remain valid; scientific gates, original
records and 37 unopened reserved meetings are unchanged.

The preserved [1.61.0 receipt](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/a5abb7f6038d14f09d314014fe063e053203d945/docs/OVERNIGHT_WORK.md)
records the dated country overview, same-meeting U.S. comparisons and prior
reporting checkpoints. Use historical results at their original version and scope.

## Source tree and remaining work

The source checkout is `/workspace/UNGA81-Transcript-Agent`; main is the source of
truth. Keep implementation work in isolated branches. The partial mirror checkout
is `/workspace/portfolio-site`; preserve unrelated `assets/css/cv.css` work and
never stage absent website files as deletions. Use scripts/sync_un_project.py and
explicit staged paths. Missing unchanged promisor objects can be retained through
`git write-tree --missing-ok` after reviewing the exact staged set.

Prior cleanup removed about 16.48 MB of generated snapshots and repeated status
content. The current R cleanup removes another 226 generated output files
(50,521,390 bytes) plus three obsolete checkpoint scripts. Exact copies remain in
commit `ea18ad83b030e10abfb32d2525c17ada5f5939b9`; Git history is unchanged.
All 1,673 retained RDS fixtures and protected original records remain byte-identical.
The current 2,077-file checksum inventory is checked in CI; generated outputs and
personal runtime paths are ignored. Frozen-run tests now require explicit archive
selection rather than following the user's latest run.

Seven suites pass 453 default R checks plus two explicitly selected archived-run
checks on Linux R 4.5.0 (Matrix 1.7.3, cluster 2.1.8.1, igraph 2.1.4). The Python
suite passes 256 tests, including six inventory-maintenance checks. This does not
establish Windows, live Shiny, PDF or scientific acceptance.

Fresh full offline replays before and after cleanup both exit successfully with
identical validation: 39 country sections, 507 coding cells, five report packets,
42 methods accounted and 133 prerequisites. Seven fitted candidates remain withheld;
no released model or semantic-accuracy claim follows from structural QA.

The R cleanup did not change browser assets or add Hugging Face storage.

1. Continue useful reporting work from the verified 1.62.0 release, then expand
   broader workflows within the execution/storage constraints.
2. Continue dependency-based cleanup with appropriate personal-runtime checks.
3. Complete actual diplomat usability sessions; evaluate any optional generative
   reporting independently from the deterministic reader and stance classifier.
4. Preserve all 37 reserved meetings, the single-reviewer owner mode and publication
   gates. Do not infer national positions from collectives, mentions or similarity.

## Earlier receipts

The [1.56.0 checkpoint](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/44ff0106f5a3ac8e82b4da22602c341f2593454f/docs/OVERNIGHT_WORK.md)
and its linked immutable archives retain earlier deployment, cleanup and operational
receipts. Use their original dates and scope, not expired activation instructions.
Keep this file a current handoff rather than an append-only log.
