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

## Verified release 1.68.0

| PR | Change | Checked head / merge |
| --- | --- | --- |
| [Source #322](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/322) | Personal report-review calendar export | Three checks passed at `a724cf4`; merged `dff0d95` |
| [Website #182](https://github.com/LystadJS/LystadJS.github.io/pull/182) | Canonical mirror and live calendar suite | Audit/regression passed at `e1eece7`; merged `61384f3` |

Both public URLs serve 1.68.0. All 196 preferred-site files match expected SHA-256
hashes. Fourteen reporting browser suites pass live with fictional sources:
reporting, calendar, affiliation navigation, bulk appendix, inventory addition,
saved-source addition, package opening, source removal, replacement, device library,
packages, Word, print/PDF and archive handoff. The calendar suite also passes at the
original URL, whose four changed assets match canonical hashes. Skipped PR live
jobs are not counted as deployed tests.

A prepared report can download one personal all-day ICS reading entry after the
user explicitly chooses a valid date. The date is independent of source dates.
The entry identifies the prepared report and source references; report-level
assessment is optional and off by default. Transcript text and passage notes are
excluded. No account connection, invitation, attendee, organizer or alarm is added.
The calendar client controls import, visibility and alerts; private classification
is a hint, not encryption or an access guarantee.

Calendar downloads do not mark report work as saved. JSON/ZIP remain the resumable
formats. Calendar options are session-only, reset on replacement and are absent
from saved report JSON. Async export checks the prepared report, workspace revision,
date and assessment option before downloading. Failed, oversized or stale exports
preserve report work. An unavailable optional exporter leaves report preparation
and other exports usable.

Local validation passes 256 Python tests, fourteen reporting browser suites,
facilitator checks and existing pure contracts. Independent Python parsing checks
CRLF, 75-octet UTF-8 folding, escaped Unicode text, deterministic identities,
Gregorian date boundaries and exclusive next-day end dates. Browser checks cover
explicit date/default-off assessment, download contents, retained dirty-work
protection, stale date/report refusal, byte limits, missing-module isolation,
replacement reset and mobile widths. This is engineering verification; actual
calendar-client import, Office, government-browser and diplomat acceptance remain
outstanding. No real or reserved transcript was retrieved.

The public build contains 204 entries and the mirror 195 files. Four application
assets plus the manifest change; repeat sync copies zero files. One essential
calendar-export module is added, with no new dependency, schema, model, backend or
Hugging Face storage. Saved report v4 and preferences v2 remain unchanged. All 2,077
R-package checksums remain valid; personal R/Python execution, scientific gates and
all 37 reserved meetings are unchanged.

Publication used the connected GitHub Git-data API while command-line Git
credentials were unavailable. Uploaded blobs and staged tree hashes were checked,
and canonical commit hashes verified locally before moving local refs. No force
push or unrelated website change was included.

The [previous checkpoint](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/08a514e9d2b7774c7f794cca07f88098b4101d6c/docs/OVERNIGHT_WORK.md)
records release 1.67.0 and links earlier receipts. Use those results at their
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

1. Continue useful reporting work from the verified 1.68.0 release, then expand
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
