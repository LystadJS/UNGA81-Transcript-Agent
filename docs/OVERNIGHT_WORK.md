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

## Verified release 1.69.0

| PR | Change | Checked head / merge |
| --- | --- | --- |
| [Source #324](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/324) | Separate source-bound passage-notes spreadsheet | Three checks passed at `4599ee2`; merged `400b8ef` |
| [Website #183](https://github.com/LystadJS/LystadJS.github.io/pull/183) | Canonical mirror and source/release pins | Audit/regression passed at `b597995`; merged `5c99f1b` |

Both public URLs serve 1.69.0. All 196 preferred-site files match expected SHA-256
hashes. Fourteen reporting browser suites pass live with fictional sources:
reporting (including the notes spreadsheet), calendar, affiliation navigation,
bulk appendix, inventory addition, saved-source addition, package opening, source
removal, replacement, device library, packages, Word, print/PDF and archive handoff.
The expanded reporting suite also passes at the original URL, whose four changed
assets match canonical hashes. Skipped PR live jobs are not deployed test passes.

Prepared reports with passage notes offer a separate CSV in an expandable
spreadsheet-follow-up section. Each row identifies user-authored interpretation,
the prepared report timestamp and original source identity/revision/hash/pointer.
Only notes from the prepared selected meetings appear, in original source order;
search and appendix choices do not narrow them. Transcript text and report-level
assessment are excluded. The full evidence CSV continues to exclude notes, and
the original five-file report package remains unchanged.

The export is disabled without prepared notes and invalidates with report inputs.
Failed or oversized exports preserve the report and other exports. Downloading a
notes spreadsheet leaves unsaved-work protection active. JSON/ZIP remain the
resumable formats, and CSV edits cannot be imported. Existing quoting and formula
prefix protection are shared rather than duplicated. JSON retains exact note text.
The CSV is not encrypted; review analyst content before sharing.

Local validation passes 256 Python tests, fourteen reporting browser suites,
facilitator checks and existing pure contracts. Independent Python CSV parsing
checks multiline Unicode and quotes, formula prefixes, note labels, source fields,
empty output and selected-meeting scope; invalid duplicate/out-of-scope notes are
refused. The browser checks the actual file, filtering independence, source-text
and assessment exclusion, no-note and stale-input disabling, dirty-work protection,
export/size failure preservation and mobile widths. A direct comparison with the
merged 1.68 implementation verifies unchanged evidence CSV bytes on fictional
source and formula/Unicode/quote cases. These are engineering checks; actual
spreadsheet-client and diplomat acceptance remain outstanding. No real or reserved
transcript was retrieved.

The public build remains 204 entries and mirror 195 files. Four existing assets
plus the manifest change; repeat sync copies zero files. No public file, dependency,
schema, model, backend, personal R/Python analysis or Hugging Face storage is added.
All 2,077 retained package checksums remain valid. Source gates and all 37 reserved
meetings are unchanged. Command-line Git credentials are working again; this
increment uses normal tested branch publication and approved merges.

The [previous checkpoint](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/f052401e250b179cf0ad220fd993d3ea772bddbe/docs/OVERNIGHT_WORK.md)
records release 1.68.0 and links earlier receipts. Use those results at their
original version and scope.

## Runnable usability setup

The [facilitator tool](../tools/reporting_usability.cjs) replaces the guide's inline
fixture generator. `--fixtures-only` creates the three source-validated JSON files
using Node alone. The default local session uses the existing personal QA setup
(Node, Python public builder and Playwright), serves only the public build on
loopback, intercepts fictional inventory/transcript responses and blocks other
external browser requests. It adds no dependency to the government-browser app.

`--smoke` passes an automated import/add/export/source-revalidation and network
blocking check. The tool contract also verifies private temporary files, fixture-only
operation without Playwright, separate duplicate downloads, closed-session cleanup
and a metadata-only receipt whose participant acceptance is always `not_recorded`.
The interactive close lifecycle is exercised with a headless driver on this host;
a visible session needs a graphical display and remains to be run with actual
participants. No real transcript, held-out source, participant response or human
acceptance is created by these checks. The synthetic-inventory setup gap is addressed;
actual representative-user sessions and work-browser policies remain untested.

The facilitator adds no public asset, schema, model, Hugging Face storage or
personal R/Python analysis code. Fixture files/downloads stay
outside the checkout, and temporary public-build copies are removed on normal exit.
The guide now names the executable setup rather than an unavailable synthetic
inventory. Record actual participant findings separately.

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

1. Continue useful reporting work from the verified 1.69.0 release, then expand
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
