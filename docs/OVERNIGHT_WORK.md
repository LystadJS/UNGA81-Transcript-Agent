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

## Verified release 1.61.0

| PR | Change | Checked head / merge |
| --- | --- | --- |
| [Source #305](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/305) | Dated country overview and matched U.S. excerpts | Three checks passed at `5ac3a6a`; merged `326845b` |
| [Website #174](https://github.com/LystadJS/LystadJS.github.io/pull/174) | Canonical public sync and exact source/release pins | Audit/regression passed at `fd3ee75`; merged `c9a3fc5` |

Both public URLs serve 1.61.0. All 195 portfolio files (194 manifest entries plus
the manifest) match expected SHA-256 hashes. All seven reporting browser suites
pass against the actual preferred URL with fictional sources; the expanded meeting
reporting suite also passes at the source URL. No skipped PR live-verification job
is counted as a live pass. The live print test includes the dated country table
and preserves its complete evidence, source context and original schema behavior.

Multi-meeting reports automatically show each recorded affiliation's existing
object-specific extracts in source-date order, with links to the dated meeting,
source/collective gaps and matching U.S. excerpts from that same meeting. Individual
meeting tables also show matched U.S. quotations. Matching uses the same issue ID
and case-insensitive displayed object wording. It assigns no agreement score,
current stance or verified policy change. Evidence is never carried forward,
including between meetings on the same date; those rows sort by title without
claiming within-day chronology. Exact repeated quoted wording appears once per
extract and adds no weight. Original source records and full CSV are unchanged.

The view reuses existing quick-reader outputs, not a second classifier. Renderer
metadata is 1.6; report v4 and preference v2 remain unchanged. Imports rebuild
derived views from verified original sources, ignoring forged saved chronology.
No country selection is required. Passage filters, appendix choices and briefing
questions leave the country overview intact. HTML, Word, print/PDF and package HTML
include it. Printed dated rows stay together when they fit on a page.

Local checks pass 256 Python tests, seven browser suites, existing report/package
contracts and a new source-bound country-timeline contract. Cases include opposing
country/U.S. verbs without agreement inference, exact objects, no same-day or
cross-date carry-forward, missing U.S./country sources, collective-only observations,
repeated wording, escaped titles, immutable inputs, rebuilt imports and single/empty
report boundaries. Browser checks cover automatic rows, U.S. quotations, unchanged
filter/export state, local context, dated keyboard links, offline HTML, three native
Word tables and complete PDF. Independently extracted the 39-page fictional print
stress case and inspected its country table after preserving row pagination.
These are engineering checks; no diplomat session, government-browser dialog or
desktop Word-rendering acceptance is claimed.

The build remains 203 entries and the mirror 194 files. Four public assets and the
manifest change; canonical sync is idempotent. Core-script and changed stylesheet
URLs are versioned, with transformed CSS hashes retained in the mirror. No new
application file, dependency, model, server, upload or Hugging Face storage is added.
All 2,077 R-package checksums remain valid; the scientific/source gates, original
records and 37 unopened reserved meetings are unchanged.

The preserved [1.60.0 receipt](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/fdb98cf7ef1396ef455a0561d088f213ad5154bc/docs/OVERNIGHT_WORK.md)
records native printing, PDF checks and stylesheet cache handling. Use historical
results at their original versions and scope.

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

1. Continue useful reporting work from the verified 1.61.0 release, then expand
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
