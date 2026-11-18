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

## Release 1.74.0 candidate: personal generated drafts

A new browser/Python sidecar implements optional question-based generated drafts.
The browser exports a 64 KiB evidence packet with up to eight questions and 100
literal-search-matched passages. Standard-library Python validates the context and
text hashes, then calls a configured loopback OpenAI-compatible chat server once
per answered question. Empty searches make no request. No runtime or model is
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

Local validation passes 264 Python tests, fifteen reporting browser workflows,
reporting/facilitator contracts, 2,077 retained checksums and the 205-entry public
build. New checks cover synthetic chat transport, redirect/proxy refusal, byte
bounds, exact citations, missing evidence, no overwrite, Unicode cross-runtime
seals, stale browser work and ordinary-export isolation. Publication and deployed
validation remain pending. The last verified deployment is 1.73.0: 196 preferred-site hashes, fourteen live reporting
browser suites, 256 Python tests and 2,077 retained package checksums. The prior
source-only QA consolidation keeps shared loopback/browser helpers and reduced
its cohort by 4,333 bytes. New browser tests reuse that helper.

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
checks on Linux R 4.5.0 (Matrix 1.7.3, cluster 2.1.8.1, igraph 2.1.4). The Python
suite passes 256 tests, including six inventory-maintenance checks. This does not
establish Windows, live Shiny, PDF or scientific acceptance.

Fresh full offline replays before and after cleanup both exit successfully with
identical validation: 39 country sections, 507 coding cells, five report packets,
42 methods accounted and 133 prerequisites. Seven fitted candidates remain withheld;
no released model or semantic-accuracy claim follows from structural QA.

The R cleanup did not change browser assets or add Hugging Face storage.

1. Complete deployment and personal-model acceptance for 1.74.0, then expand
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
