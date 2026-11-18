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

## Verified release 1.67.0

| PR | Change | Checked head / merge |
| --- | --- | --- |
| [Source #320](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/320) | Native recorded-affiliation report navigation | Three checks passed at `cf8fecf`; merged `1720737` |
| [Website #181](https://github.com/LystadJS/LystadJS.github.io/pull/181) | Canonical mirror, cache/release pins and live affiliation suite | Audit/regression passed at `b7ff38c`; merged `5f696f3` |

Both public URLs serve 1.67.0. All 195 preferred-site files match expected SHA-256
hashes. Thirteen reporting browser suites pass live with fictional sources:
reporting, affiliation navigation, bulk appendix, inventory addition, saved-source
addition, package opening, source removal, replacement, device library, packages,
Word, print/PDF and archive handoff. The new navigation suite also passes at the
original URL, whose four changed assets match canonical hashes. Skipped PR live
jobs are not counted as deployed tests.

Reports with multiple recorded affiliations include an alphabetical jump index.
Links focus the first country row in the collection overview, or the single-meeting
country table; return links focus the index heading. Single-meeting summaries and
source statistics remain ahead of the index. All affiliations, dated observations
and comparison gaps remain rendered. Nothing is filtered or selected by navigation.
Empty/single-affiliation reports omit the unnecessary index. Labels remain escaped
and targets use numeric generated IDs rather than source text.

Native links work in browser reports, JavaScript-disabled standalone HTML, Word
bookmarks and printed PDF destinations. Print targets retain their separate prefix
and ARIA references. Saved reports rebuild the index from verified original source;
no navigation field is serialized. Notes, appendix choices, search state, source
bytes, full CSV and analytical comparisons remain unchanged. No source request or
automatic saving occurs.

Local validation passes 256 Python tests, thirteen reporting browser suites,
facilitator checks and existing pure contracts. New checks cover alphabetical
single/multi navigation, unique valid destinations, keyboard row/return focus,
unchanged prepared state and controls, script-free HTML, mobile, unsafe-label
escaping and empty/single-affiliation boundaries. Independent OOXML parsing verifies
all internal hyperlinks and six bookmarks in the two-country/two-meeting fixture.
A separate PDF parser resolves the index and both country destinations in the
40-page synthetic stress PDF. This is engineering verification, not actual Office,
work-browser or diplomat acceptance. No real or reserved transcript was retrieved.

The public build remains 203 entries and mirror 194 files. Four assets plus
the manifest change; repeat sync copies zero files. Renderer and stylesheet URLs
are versioned. No application file, dependency, schema, model, backend or Hugging
Face storage is added. All 2,077 R-package checksums remain valid; personal R/Python
execution, scientific gates and all 37 reserved meetings are unchanged.

The [previous checkpoint](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/aeaa2e2536d9fdd2f6e7a250b0943e1df0c01049/docs/OVERNIGHT_WORK.md)
records release 1.66.0 and links earlier receipts. Use those results at their
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

1. Continue useful reporting work from the verified 1.67.0 release, then expand
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
