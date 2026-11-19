# Current work checkpoint

Updated 19 November 2026, UTC. Continue the PowerTranscript-like
reporting application and broader feasible diplomatic workflows with JavaScript-only
browser execution, separate personal R/Python tools, bounded Hugging Face storage
and a focused source tree. Full DiploTools parity is not established.

## Source-free historical/research action subset

The full 46-workflow PR opening was rejected by automatic approval review because
its CI could retrieve source/model material and produce artifacts. No full PR was
created. The candidate remains on `maintenance/historical-ci-actions`; only two
source-free push runs occurred (nuisance and roster), both passed.

The reduced candidate changes 129 references in 38 workflows: 35 source-free
validation workflows and three dormant legacy configurations whose events cannot
run on a maintenance branch, PR or `main`. The eight unchanged acquisition/live/
model workflows retain 28 older references. Static event/path checks show none
is activated by the reduced diff. No manual dispatch is made. All 61 YAML files
pass actionlint; parsed structure changes only action refs. Source/model inputs,
permissions, retention and scientific/held-out gates are preserved. App 1.84.0,
public assets and HF storage are unchanged; managed testing remains deferred.
The [audit record](OPERATIONS.md#source-free-historicalresearch-action-subset)
identifies the remaining blocked workflows and the automatic-review reason.

## Action-runtime maintenance — application unchanged

Current first-party Node 24 actions replace 45 references in 15 active-build,
scheduled-operation and manual-only workflows. All scripts, triggers, permissions,
language versions, inputs and scientific/source gates stay intact except the
explicit Pages hidden-file option preserving `.nojekyll` under the new uploader.
Local actionlint 1.7.12 and structural invariants pass; the Pages tar recipe retains
all 200 files in the 209-entry allowlisted build byte for byte. See the
[maintenance record](OPERATIONS.md#github-action-runtime-maintenance) for exact
versions, primary releases and validation scope. No private/model workflow was
manually dispatched, and no operational acceptance or whole-repository cleanup
claim follows. Forty-six historical/research workflows still have 157 older
references; some file edits can trigger acquisition work, so their migration is
separate. Browser release 1.84.0, runtime files, dependencies and HF storage stay
unchanged; managed testing remains deferred.

[Source #366](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/366)
merged as `5199c648d6e0ca30b8d7fc5247bedc8e16d1f5ef` after all four checks passed.
The actual Pages pipeline passed with the new actions; all 200 original-site
files match, including `.nojekyll`. [Website #200](https://github.com/LystadJS/LystadJS.github.io/pull/200)
merged as `a9ed0820184c451d0427279f2e72fd197c403c5e` after audit/regression passed.
It upgrades eight more references in two verification workflows. Post-merge audit,
synthetic research verification and deployed-file checks pass. The regular
comparison/meeting job retains its existing Node 24 actions and runs separately.
Total scope is 53 references in 17 workflows, with 157 older references in 46
historical/research source workflows still outstanding. Mirror synchronization
changes zero files; the temporary tool/build/archive was removed. No private
workflow dispatch, application release or managed-client acceptance was added.

## Report copy for email — 1.84.0

The prepared ordinary report can be copied as complete formatted HTML and plain
text for manual email-editor pasting. Provenance is expanded and plain text keeps
source URLs. The two UTF-8 representations share 25 MB without truncation.
Passage-list filters do not reduce the copy; personal model drafts are separate.
No clipboard read, account access, sending, runtime file, dependency or storage
is added. API/core failures preserve ordinary exports and current work. Submitted
browser writes cannot be cancelled: completion explicitly identifies an earlier
snapshot after report/source work changes. Tests intercept writes and inspect
native ClipboardItem payloads; no OS/Outlook round-trip is claimed. Managed testing
remains deferred. The reporting contract links current primary Microsoft guidance.

[Source #364](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/364)
merged as `62bdf677b32b1f22b5afa6f283645c340d6bdb2d` after numerical, browser and
operational contracts passed, including sixteen reporting UI suites, four
campaign suites, the facilitator and read-only archive checks.
[Website #199](https://github.com/LystadJS/LystadJS.github.io/pull/199)
merged as `b59979453775d29196916b2c2c8520ea7a2d203f` after audit and website
regression passed. Both public deployments serve 1.84.0. All 201 preferred-site
canonical hashes and four changed original-site asset hashes match. The new
email-copy contract, existing report UI, ordinary report Word and personal
draft/Word pass live at both URLs with fictional inputs. Copy tests intercept
writes and inspect native ClipboardItem payloads without OS clipboard reads or
actual Outlook access; no paste acceptance or sending is implied. Repeat mirror
sync copies/removes zero of 200 public files; the build remains 209 entries.
Current R/Python execution, storage and scientific gates are unchanged.

## Campaign editable Word briefing — 1.83.0

The campaign notebook now offers a complete editable Word reading copy using the
existing native Word/ZIP writers. It retains campaign notes, all country rows,
contact profiles and interaction logs independently of list filters. Full JSON
remains resumable work; Word edits cannot be imported. The complete binary shares
the notebook's 1 MiB bound, with refusal rather than truncation. Missing/older
optional modules disable only Word; pending fields, stale edits/source operations
and download failures keep current work. No runtime file, dependency, model or
storage is added. Managed testing remains deferred; desktop Word acceptance is
unrecorded.

[Source #362](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/362)
merged as `40418ededaaac4bda995ffafe1c5458dcca46621` after numerical, browser and
operational contracts passed, including fifteen reporting UI suites, four
campaign suites, the facilitator and read-only archive checks.
[Website #198](https://github.com/LystadJS/LystadJS.github.io/pull/198)
merged as `d08d2c600b7c9f32e5d10abd950c03007e0af360` after audit and website
regression passed. Both deployments serve 1.83.0. All 201 preferred-site canonical
hashes and five changed original-site asset hashes match. Four campaign suites,
ordinary report Word and personal draft/Word pass live at both URLs with fictional
inputs. Independent DOCX parsing checks complete text in order, XML/CRC structure,
privacy scope, resumable-JSON guidance and exact whole-file bounds. Stale data/
source decisions, failed downloads, pending forms and missing/older modules keep
work. The shared report Word/package bounds and draft prefix remain validated.
Repeat mirror sync copies/removes zero of 200 public files; the build remains
209 entries. No model, private transcript or client/account acceptance is implied.
Managed testing remains deferred; desktop Word rendering is unverified.

## Campaign follow-up queue — 1.82.0

The owner deferred managed Edge/Outlook testing and requested continued changes.
The campaign list now offers earliest follow-up and latest manually logged
interaction ordering, dated/undated filters and alphabetical ties. Missing dates
sort last; no dates or activity are inferred. Views compose with search/status/
cutoff, preserve unapplied work and complete exports, and reset on New/Open/Clear.
No schema, runtime file, dependency, model or Hugging Face storage was added.
Managed-client acceptance remains deferred, not passed.

[Source #360](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/360)
merged as `37030fe36ee3c263b4c66e19e816f586797e3e9b` after numerical, browser and
operational contracts passed (including fifteen reporting UI suites, three
campaign suites, the facilitator and read-only archive checks).
[Website #197](https://github.com/LystadJS/LystadJS.github.io/pull/197)
merged as `25f218d545aa08e81c555dce6f37a2fb7c6a4304` after audit and website
regression passed. Both public deployments serve 1.82.0. All 201 preferred-site
canonical hashes and all four changed original-site asset hashes match. Three
campaign suites and the report-calendar regression pass live at both URLs with
fictional inputs. Repeat mirror sync copies/removes zero of 200 files; the public
build remains 209 entries. Tests do not establish participant/client acceptance.
The first local facilitator attempt lacked an explicit browser path; the rerun
with the installed Chromium passed. No reserved meetings were opened.


## Standing authorization

On 18 November the user explicitly approved all merges from that point onward.
This supersedes the former merge blocker. Merge tested project PRs and publish
the required mirror without repeating that approval request; respect repository
protections, later user instructions and the scientific/source gates in AGENTS.md.

## Verified source-only reporting and campaign rehearsal kit

The existing facilitator now creates six fictional JSON files using Node alone:
three source-validated reporting files, a paired hand-authored draft, a campaign
notebook and contact-only transfer. The campaign has one current Contacted Kenya
record/profile, one earlier conversation and a November 21 follow-up. The
transfer adds two profiles, skips one unchanged ID and introduces an unassessed
United States record without a date. No genuine identity, pledge or vote is used.

The expanded engineering smoke rehearses contact review/import, preserving current
assessment/history, explicit November 22 follow-up entry, full notebook/contact
JSON, complete contact CSV, follow-up ICS and complete HTML despite a list filter.
Ten private downloads are retained. All six fixtures, downloads and receipts remain
outside the public build, which is removed on exit; fixture URLs return 404 and
external requests are blocked. Private permissions, failed-output cleanup and
visible-session lifecycle checks remain. The tool records no model inference,
calendar-client import or participant acceptance; actual external client actions
must be recorded separately. The owner has now selected Microsoft Edge and Outlook; exact edition/build,
account type, managed policy and actual client observations remain unrecorded.

Local facilitator tests pass, including Node-only generation, schema/planned
counts, report/draft pairing, campaign outputs, metadata privacy and cleanup.
[Source #355](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/355) passed
its full contract check and merged as `6f353a8808fcfc3b1a93ae3369a51c15aa6cf649`.
App assets are byte-identical to the verified 1.81 checkpoint; repeat mirror
synchronization copied/removed zero of 200 public files. No website publication
is needed. Models, dependencies and HF storage are unchanged; public application 1.81.0 remains verified. This prepares actual
user/client work and does not substitute for it.

## Edge and Outlook rehearsal target

The owner selected Edge and Outlook. The [usability guide](REPORTING_USABILITY.md#edge-and-outlook-rehearsal)
now specifies a short file/calendar pass and current Microsoft import paths for
classic Windows, new Windows and web editions. New Outlook file import has an
explicit Microsoft 365 Exchange account limitation; the exact client/account has
not been supplied. The rehearsal captures actual versions, retained downloads,
November 21/22 all-day dates, text, visibility, alerts and duplicates. It imports a
file snapshot, not a subscription, and leaves full JSON as resumable work.

Native Edge engineering verification subsequently passed: 19 local UI suites,
the facilitator contract, six preferred-site suites and 201 deployed file hashes,
using Edge 157.0.4341.60 on unmanaged headless Linux with Playwright 1.62.0 at source
`8a8741f78dff79223f22b2679ef937ef8d414836`. See the
[scoped receipt](REPORTING_USABILITY.md#native-edge-engineering-receipt). The official
package was hash-verified, extracted privately and removed after testing; no app
fix or dependency change was needed. No Outlook account or calendar was accessed.
Actual managed-client and participant acceptance is still outstanding.
This update changes documentation only; release 1.81.0 and all public assets remain
unchanged. Personal generation hardware/runtime and permitted vendor workflow
requirements remain separate unresolved inputs.

## Public vendor evidence refresh

On 19 November the public vendor homepage was rendered in an isolated browser:
it provides broad reporting/campaign claims and demo links, not a detailed feature
checklist. The February 2026 Venture Kick account also confirms broad position
coordination and secure-communication claims. The [capability matrix](CAPABILITIES.md)
now distinguishes these categories from local comparisons/file exchange and lists
requirements for any authorized shared service. No account, demo booking or message
was used. Secondary/AI-generated product details remain unconfirmed. App assets
and release 1.81.0 are unchanged. Full parity requires permitted vendor workflow
evidence and actual user/client observations; marketing is not acceptance.

## Verified application checkpoint

[Release 1.81.0 checkpoint](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/9e90de4926bd51b5c15e1c04f7ec396fe798a7e7/docs/OVERNIGHT_WORK.md)
retains source #353 and website #196 passing-check merges, 201 preferred-site
hashes, four changed original-site assets, three campaign suites plus the report
calendar regression passing live at both URLs, 264 Python tests, 2,077 checksums
and a 209-entry public build. It links prior reporting/facilitator receipts. Those
are engineering checks at their original scope. Actual model, desktop Word,
calendar-client, government-browser and diplomat acceptance remains outstanding.

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
264-test total is recorded in the previous checkpoint above. This does not
establish Windows, live Shiny, PDF or scientific acceptance.

Fresh full offline replays before and after cleanup both exit successfully with
identical validation: 39 country sections, 507 coding cells, five report packets,
42 methods accounted and 133 prerequisites. Seven fitted candidates remain withheld;
no released model or semantic-accuracy claim follows from structural QA.

The R cleanup did not change browser assets or add Hugging Face storage.

1. Complete reporting usability and personal-model factual/citation acceptance.
   Rehearse reporting, contact handoff and calendar follow-ups with actual users in
   the intended browser/calendar clients. Record task completion, recovery and client
   findings separately from synthetic QA. Keep shared authentication and election
   eligibility separate from manual records; preserve browser/personal-runtime boundaries.
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
