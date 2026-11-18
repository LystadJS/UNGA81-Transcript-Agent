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

## Verified release 1.60.0

| PR | Change | Checked head / merge |
| --- | --- | --- |
| [Source #302](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/302) | Complete native printing / browser PDF | Three checks passed at `52b36f2`; merged `b21add4` |
| [Website #172](https://github.com/LystadJS/LystadJS.github.io/pull/172) | Canonical mirror and deployed print test | Audit/regression passed at `018210f`; merged `f1e3bc6` |
| [Source #303](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/303) | Version the changed print stylesheet | Three checks passed at `4904146`; merged `2a58233` |
| [Website #173](https://github.com/LystadJS/LystadJS.github.io/pull/173) | Hash transformed CSS in mirror URLs | Audit/regression passed at `e4b39d8`; merged `8cf6aba` |

Both public URLs serve 1.60.0 with the final style-cache fix. All 195 checked
portfolio files (194 manifest entries plus the manifest) match expected SHA-256
hashes. Seven browser suites pass against the actual preferred URL with fictional
sources: reporting, replacement, packages, device library, archive handoff, Word
and print/PDF. The print suite also passes at the original source URL with the
simulated stale unversioned stylesheet. No skipped PR live job is counted as a pass.

Printing uses the complete report renderer, beyond preview limits. Workspace
controls are excluded; source identities are expanded, quotation/table clipping
is removed and meeting navigation targets distinct print headings. Native dialog
closing or Return to report clears the print view and restores its title. Browser
failure, stale/oversized reports and missing closing events preserve current work.
Printing does not mark resumable work saved or claim that a PDF was created.
Save JSON/ZIP separately. The browser controls PDF destination and final size;
printable HTML has a 25 MB bound. No popup, PDF library, model or server is added.

A simulated stale unversioned stylesheet exercises the source URL fix. The mirror
font transform previously replaced source CSS versions with one shared tag. It
now hashes actual transformed local styles after font changes; source style
updates invalidate their cache even when the typography theme is unchanged.
Seven sync fixtures pass, including changed-CSS invalidation and repeat-sync
idempotence. Shared typography links and unrelated CV work are preserved.

Local validation passes 256 Python tests and seven synthetic reporting browser
suites. The print suite covers 64 source segments, the full appendix beyond the
50-passage preview, an unclipped long quotation, notes, source details, unanswered
gaps, native/keyboard events, CSS isolation, anchors, recovery, dirty/stale protection
and size/browser refusal. Independent local PDF extraction verifies the 38-page,
133,658-byte stress-test file's final passage, long-quote end, notes and hashes,
two source URLs and four internal navigation links. Three rasterized pages were
inspected for table margins, qualifications, source identity and note readability.
The actual live portfolio PDF also passed independent extraction: 38 pages,
279,395 bytes, complete long/end passages, source identities, notes, question gap,
two source URLs and four internal navigation links; workspace controls are absent.
These are engineering checks, not actual government-browser dialogs or diplomat
usability acceptance. The usability guide includes those unrun participant tasks.

The public build remains 203 entries and the mirror 194 files. There is no new
application file, dependency, source input, upload or Hugging Face storage. All
2,077 R-package checksums remain valid; saved report/preference schemas, ZIP
contents, scientific gates and the 37 reserved meetings are unchanged.

The preserved [1.59.0 receipt](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/b21add458fa15974e6fcc96a99a39d8aa8dd7b72/docs/OVERNIGHT_WORK.md)
records native Word export and prior reporting checkpoints. Use historical results
at their original versions and scope.

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

1. Continue useful reporting work from the verified 1.60.0 release, then expand
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
