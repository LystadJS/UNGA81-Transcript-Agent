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

## Verified release 1.73.0

| PR | Change | Checked head / merge |
| --- | --- | --- |
| [Source #332](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/332) | Stale preference-import protection | Three checks passed at `b025461`; merged `bf49852` |
| [Website #187](https://github.com/LystadJS/LystadJS.github.io/pull/187) | Canonical mirror and source/release pins | Audit/regression passed at `0a719c0`; merged `935dbd1` |

Both public URLs serve 1.73.0. All 196 preferred-site files match expected SHA-256
hashes. Fourteen reporting browser suites pass live with fictional sources:
reporting (including delayed preference reads), calendar, affiliation navigation,
bulk appendix, inventory addition, saved-source addition, package opening, source
removal, replacement, device library, packages, Word, print/PDF and archive handoff.
The expanded reporting suite also passes at the original URL, whose three changed
assets match canonical hashes. Skipped PR live jobs are not deployed test passes.

The audit reproduced a delayed local preference-file read replacing a mission name
typed after selection. Imports now capture the workspace revision, loaded-source
operation counter and latest preference-selection serial. An older result cannot
replace newer edits, prepared work or a later source operation. Only the latest
preference selection may apply, including when that newer file is invalid or the
selection is cleared. Older errors cannot replace the latest import status, and
older cleanup cannot clear a newer selected file.

The local status shows Checking while reading, applied after a valid current
import, or current-settings-kept after workspace changes. Valid current imports
still invalidate prepared exports; current read/validation errors remain visible.
Sources, notes, meeting selection, preview, export readiness and dirty-work
protection stay intact when an obsolete result is refused. The existing 8 KiB
preference and 25 MB full-report budgets, schemas, country coverage and source
verification are unchanged. Guards are session-only; no stored field is added.

Local validation passes 256 Python tests, fourteen existing reporting browser
suites, facilitator checks and pure contracts. Expanded browser checks hold and
resolve/reject fictional file reads to verify newer edits/preparation, retained
replacement protection, two pending selections, newer invalid files, stale errors,
current errors, source operations kept without replacement, clearing selection and
input cleanup. Existing mobile, preference round-trip, download-failure, source
verification and format checks pass. These are deterministic engineering races,
not actual diplomat or government-browser usability sessions. No real or reserved
transcript was retrieved.

The public build remains 204 entries and mirror 195 files. Three existing assets
plus the manifest change; repeat sync copies zero files. No public file, dependency,
schema, model, backend, personal R/Python analysis or Hugging Face storage is added.
All 2,077 retained package checksums remain valid. Scientific/source gates and all
37 reserved meetings are unchanged. Runtime QA outputs remain ignored and outside
the published application and Git tree.

The [previous checkpoint](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/966194717b73728ce0c6254d6bdf25155a633d01/docs/OVERNIGHT_WORK.md)
records release 1.72.0 and links earlier receipts. Use those results at their
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

## Shared reporting QA fixture

Fourteen reporting browser suites now use one [loopback server and browser launcher](../tests/reporting_browser_fixture.cjs).
All post-launch workflow checks remain byte-identical. Including the shared helper
and its new contract, this QA cohort falls from 185,606 to 181,273 bytes: 4,333
bytes of net reduction. The contract checks MIME/UTF-8 responses, versioned asset
URLs, dynamic script-free reading copies and root/traversal refusal using fictional
temporary files. It runs in Node before Playwright installation; browser loading
stays lazy and retains existing module/executable overrides.

Fourteen workflows pass locally and live, along with the new HTTP contract,
256 Python tests, 2,077 retained checksums and the 204-entry public build. All 196
preferred-site hashes remain unchanged; repeat mirror sync copies zero files.
The public app stays at 1.73.0, with no runtime, dependency, schema, model or storage
change. The separate facilitator keeps its public-build/network-isolation setup.

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

1. Continue useful reporting work from the verified 1.73.0 release, then expand
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
