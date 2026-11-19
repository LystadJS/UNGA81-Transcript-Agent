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

## Verified release 1.74.0

A new browser/Python sidecar implements optional question-based generated drafts.
The browser exports a 64 KiB evidence packet with up to eight questions and 100
literal-search-matched passages. Standard-library Python validates the context and
text hashes, then calls a configured loopback OpenAI-compatible chat server once
per question with matching passages. Empty searches make no request. No runtime or model is
selected, downloaded or bundled; local server configuration determines whether
inference actually stays local. Environment proxies and redirects are refused.

Model replies require bounded bullets with exact quotations from the question's
own passages. Malformed, unknown or altered citations refuse the whole draft.
The returned JSON is always unreviewed. The browser binds it to the prepared
source scope and question order, displays cited context after the country-first
report and can download a separate review HTML. Ordinary report exports, JSON,
ZIP, preferences and device saves exclude the draft; users retain the original
report JSON and returned draft JSON separately. Source/settings changes clear the
session-only view; stale imports/exports cannot restore old work. Exact quotation
matching does not validate factual entailment or model identity.

The new protocol uses fictional HTTP fixtures; no real generative inference or
reserved transcript retrieval has occurred. Hardware/model choice and factual,
citation and diplomat acceptance remain outstanding. No browser inference, model
weights, dependencies, backend or Hugging Face storage are added. Existing report
v4/preferences v2 and scientific/source gates remain unchanged.

| PR | Change | Checked head / merge |
| --- | --- | --- |
| [Source #335](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/335) | Personal model draft input, Python generation and browser review | Three checks passed at `2b74150`; merged `7487e0a` |
| [Source #336](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/336) | Visible collective/unverified-capacity quotation caveats | Three checks passed at `890a649`; merged `1e43029` |
| [Website #188](https://github.com/LystadJS/LystadJS.github.io/pull/188) | Canonical mirror, source/release pins and deployed draft checks | Audit/regression passed at `dd0a2f9`; merged `6e2d403` |

Both public URLs serve 1.74.0. All 197 preferred-site files match expected SHA-256
hashes. Fifteen reporting browser workflows pass live with fictional sources:
reporting, personal drafts, calendar, affiliation navigation, bulk appendix,
inventory addition, saved-source addition, package opening, source removal,
replacement, device library, packages, Word, print/PDF and archive handoff. The
personal-draft and main reporting workflows also pass at the original URL, whose
four changed assets match canonical source hashes. A local runner ended after
eleven preferred-site suites completed; only the four unfinished suites were
rerun, and all four passed. Skipped PR live jobs are not
deployed test passes.

Local validation passes 264 Python tests, fifteen reporting browser workflows,
reporting/facilitator contracts, 2,077 retained checksums and the 205-entry public
build. The 196-file mirror synchronizes with zero copied/removed files on repeat.
Synthetic chat checks cover transport, redirect/proxy refusal, byte bounds,
private new output/no overwrite, exact citations and evidence gaps. Cross-runtime
Unicode seals bind every selected passage identity, including unmatched source
revisions. Browser checks cover context, safe text, question/scope mismatch,
stale imports/exports/clear, ordinary-export isolation, dirty protection,
optional-module failure and mobile. New browser tests reuse the shared QA helper.

One JavaScript runtime module and one separate standard-library Python command
are added, with focused tests and setup guidance. No generated output or model
weights enter the source tree. The unchanged deterministic reader, saved-report
schemas, retained R artifacts, publication gates and 37 unopened meetings preserve
the previous scientific boundaries. This remains engineering validation; real
model inference, diplomat sessions and government-browser policy acceptance have
not been recorded. The prior QA consolidation reduced its cohort by 4,333 bytes.

The [previous checkpoint](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/f0927f2541ea17578b24dd3176c124934abfc040/docs/OVERNIGHT_WORK.md)
retains the verified 1.73.0 deployment and QA receipts, with links to earlier releases.

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
checks on Linux R 4.5.0 (Matrix 1.7.3, cluster 2.1.8.1, igraph 2.1.4). At the cleanup checkpoint, the Python
suite passed 256 tests, including six inventory-maintenance checks; the current
264-test total is recorded above. This does not
establish Windows, live Shiny, PDF or scientific acceptance.

Fresh full offline replays before and after cleanup both exit successfully with
identical validation: 39 country sections, 507 coding cells, five report packets,
42 methods accounted and 133 prerequisites. Seven fitted candidates remain withheld;
no released model or semantic-accuracy claim follows from structural QA.

The R cleanup did not change browser assets or add Hugging Face storage.

1. Complete personal-model factual/citation acceptance for 1.74.0, then expand
   broader workflows within the execution/storage constraints.
2. Continue dependency-based cleanup with appropriate personal-runtime checks.
3. Complete actual diplomat usability sessions; evaluate any optional generative
   reporting independently from the deterministic reader and stance classifier.
4. Preserve all 37 reserved meetings, the single-reviewer owner mode and publication
   gates. Do not infer national positions from collectives, mentions or similarity.

An optional personal generation runtime/model and RAM/GPU target remain
unspecified. Establish those constraints before selecting generation dependencies
or downloading model weights. Generation needs separate factual/citation acceptance;
it must not replace the deterministic country overview or stance-model gates.

## Earlier receipts

The [1.56.0 checkpoint](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/44ff0106f5a3ac8e82b4da22602c341f2593454f/docs/OVERNIGHT_WORK.md)
and its linked immutable archives retain earlier deployment, cleanup and operational
receipts. Use their original dates and scope, not expired activation instructions.
Keep this file a current handoff rather than an append-only log.
