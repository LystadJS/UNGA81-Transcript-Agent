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

## Verified release 1.57.0

| PR | Change | Verified result |
| --- | --- | --- |
| [Source #295](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/295) | Bounded device report library | All three checks passed at `e254a13`; merged as `0f0907b` |
| [Website #169](https://github.com/LystadJS/LystadJS.github.io/pull/169) | Exact public sync, release/source pins, expanded live device acceptance | Audit and regression passed at `7a325d3`; merged as `4f6e049` |

Both public URLs serve 1.57.0. All 194 checked portfolio files (193 manifest entries
plus the manifest) matched expected SHA-256 hashes. Five reporting suites passed
against the actual portfolio: device library, meeting reporting, replacement
protection, ZIP packages and archive handoff. The library suite also passed against
the source Pages URL. Tests used fictional sources and no reserved transcripts;
they establish engineering behavior, not diplomat usability or model accuracy.
Do not open equivalent replacement PRs or count skipped CI jobs as live passes.

The device library holds eight reports sharing 25 MB of UTF-8 report JSON. It
lists titles, New York save times and sizes without opening sources automatically.
Read/write revision checks reject stale-tab operations, and count/byte limits
share the write transaction. The prior single slot migrates atomically without a
duplicate source store. Blocked-tab recovery and upgrade quota-error rollback
passed. After failure, the retained v1 JSON can be downloaded unchanged and
unverified, without upgrading or deleting it. Source verification happens on
normal import/open. Restricted browsers retain file-based reporting.

Report schema v4 and preference schema v2 are unchanged. No model, dependency,
server, automatic report saving or Hugging Face data was added. The public build
still contains 202 entries and the mirror still contains 193 public files.

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
establish Windows, live Shiny, PDF or scientific acceptance. Fresh full offline replays before and after cleanup both exit successfully with
identical validation: 39 country sections, 507 coding cells, five report packets,
42 methods accounted and 133 prerequisites. Seven fitted candidates remain withheld;
no released model or semantic-accuracy claim follows from structural QA.

Browser release 1.57.0
and its public assets remain unchanged; no Hugging Face storage was added.

1. Continue useful reporting work from the verified 1.57.0 release, then expand
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
