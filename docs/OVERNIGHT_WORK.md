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

## Verified release 1.59.0

| PR | Change | Verified result |
| --- | --- | --- |
| [Source #300](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/300) | Native browser-only Word report export | All three checks passed at `7103b6f`; merged as `a80cd4b` |
| [Website #171](https://github.com/LystadJS/LystadJS.github.io/pull/171) | Canonical public sync, source/release pins, deployed Word test | Mirror audit and website regression passed at `6527e6d`; merged as `67f77d2` |

Both public URLs serve 1.59.0. All 195 checked portfolio files (194 manifest
entries plus the manifest) match expected SHA-256 hashes. Six reporting suites
pass against the actual preferred URL with fictional sources: reporting,
replacement, packages, device library, archive handoff and native Word export.
One transient asset HTTP 503 passed on retry; no source or code repair was needed.

The Word export uses native editable headings, country tables, lists, source links
and meeting bookmarks from the complete report renderer. Questions, selected
evidence and separately labeled notes remain present. Filters do not narrow the
report. Word is a reading copy: edits cannot be imported, and downloading Word
keeps unsaved-work protection. JSON/ZIP remain the resumable formats. The report
ZIP's existing contents and all saved schemas remain unchanged.

The document's 25 MB bound includes XML and ZIP overhead. Tests cover deterministic
bytes at the exact limit, payload/container failure, unsupported XML characters,
matching timestamps, unchanged current work/other exports, stale-export prevention,
keyboard and mobile behavior. Independent standard-library parsing verifies every
part, CRC, ordered full rendered text, editable tables, links, bookmarks and notes.
A separate local python-docx reader also opened the 33,775-byte fictional sample.
This is structural compatibility, not desktop Word rendering or diplomat acceptance.
The usability guide includes an actual Word-environment task; no participant
session has been performed.

Local validation passes 256 Python tests, six synthetic browser suites and the
existing report-package checks. The Word suite passes against the live source
URL. No skipped PR live job is counted as a live test. The public build contains
203 entries and the mirror contains 194 files. One 9 KB runtime module reuses the
existing ZIP writer; no dependency, server, model, upload, remote media or Hugging
Face data was added. All 2,077 R-package checksums remain valid.

The preserved [1.58.0 receipt](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/a80cd4b27bf45487f24493dbae9be7b89cbccc1f/docs/OVERNIGHT_WORK.md)
records passage filtering and the earlier device-library receipt. Keep its original
version and scope when using those historical results.

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

1. Continue useful reporting work from the verified 1.59.0 release, then expand
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
