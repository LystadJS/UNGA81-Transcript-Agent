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

## Verified release 1.65.0

| PR | Change | Checked head / merge |
| --- | --- | --- |
| [Source #315](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/315) | Add selected inventory transcripts while keeping current work | Three checks passed at `51256ce`; merged `2973d45` |
| [Website #179](https://github.com/LystadJS/LystadJS.github.io/pull/179) | Canonical mirror, release pins and live collection-addition test | Audit/regression passed at `1196ede`; merged `da69078` |

Both public URLs serve 1.65.0. All 195 preferred-site files match expected SHA-256
hashes. Eleven reporting browser suites pass on the actual preferred URL with
fictional sources: reporting, inventory addition, saved-source addition, package
opening, source removal, replacement, device library, packages, Word, print/PDF
and archive handoff. The new inventory-addition suite also passes on the original
source URL, whose three changed assets match canonical hashes. Skipped PR live
jobs are not counted as deployed verification.

Add selected transcripts extends a loaded report directly from the meeting
inventory. Up to five new meetings are retrieved explicitly in the browser.
Current source bytes, settings, questions, global/passage notes, appendix and
selected/unchecked meetings stay intact. New loaded meetings are checked; request
checkboxes clear after success. Prepare again and save JSON/ZIP to retain the
addition. There is no automatic save or upload. Load remains the separate
replacement workflow with its original confirmation and partial-replacement gates.

Every addition is atomic. Overlapping meeting identities/revisions, capacity and
unavailable/reserved metadata are refused before source requests. Combined source
and complete saved-JSON limits are checked before applying. Failed, marked-partial,
cancelled or stale retrieval applies nothing, including a first completed bundle
when the second fails. Newer edits or source operations supersede pending work.
Incomplete sources can be inspected in a separate report without overwriting the
current report. Existing ten-bundle/100-meeting/15,000-passage/25 MB source bounds
and the 25 MB complete saved-JSON budget remain unchanged.

Local validation passes 256 Python tests, eleven reporting browser suites and
existing pure contracts. New cases cover exact retained source/annotation replay,
unchecked meetings, original-source revalidation, stale exports, request-choice
reset, overlap/capacity/policy refusal before requests, failed/partial retrieval,
complete-state size refusal, cancellation, multi-bundle rollback, newer edits and
source removal, unfinished questions and mobile. All network responses in these
new tests are intercepted fictional data; no real transcript was retrieved.
The usability task requires a facilitator-provided synthetic inventory and must
be deferred on the production inventory. No participant session or diplomat
acceptance is claimed.

The public build remains 203 entries and mirror 194 files. Three assets plus
the manifest change; repeat sync copies zero files. The main script URL is
versioned. No application file, dependency, schema, server, model or Hugging Face
storage is added. All 2,077 R-package checksums remain valid; separate personal
R/Python execution, scientific gates and all 37 reserved meetings are unchanged.

The [1.64.1 receipt](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/6b0325d9e12a80677c62557d80929a65ac0caa95/docs/OVERNIGHT_WORK.md)
records package-opening instruction cleanup and links the 1.64.0 functional
release. Use those results at their original version and scope.

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

1. Continue useful reporting work from the verified 1.65.0 release, then expand
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
