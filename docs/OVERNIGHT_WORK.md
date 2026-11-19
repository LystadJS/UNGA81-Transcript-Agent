# Current work checkpoint

Updated 19 November 2026, UTC. Continue the PowerTranscript-like
reporting application and broader feasible diplomatic workflows with JavaScript-only
browser execution, separate personal R/Python tools, bounded Hugging Face storage
and a focused source tree. Full DiploTools parity is not established.

## Standing authorization

On 18 November the user explicitly approved all merges from that point onward.
This supersedes the former merge blocker. Merge tested project PRs and publish
the required mirror without repeating that approval request; respect repository
protections, later user instructions and the scientific/source gates in AGENTS.md.

## Verified release 1.77.0: manual campaign outreach notebook

A new browser-only notebook covers an initial manual campaign workflow: campaign
details, one current lead-contact/status row per country/territory, user-entered
status and follow-up dates, source reference and notes. The shared 249-entry
geographic registry is a place picker, not an electorate. Counts describe rows;
reported support is not an actual vote, verified identity or prediction.

Apply commits a country form to session memory; JSON explicitly saves the full
notebook. CSV exports all country rows but excludes campaign-level notes. The
script-free reading HTML includes campaign notes and complete records for print.
Filters change only the list, not counts or downloads. Imports/compact JSON and
reading copies are bounded to 1 MiB without truncation. No account, automatic
storage, history, reminders or messages are provided. Full multi-contact election
CRM and authenticated collaboration remain additional work.

Strict schema/date/unique-place/UTF-8 checks precede replacement. Keep/Escape,
unapplied/dirty-form protection and latest-operation/revision guards retain work;
old reads/errors and stale confirmations cannot replace newer edits. Country
identity stays fixed during editing. Failed download starts preserve dirty state.
Current interface/core contracts and all fifteen existing reporting browser
workflows pass locally. New checks cover exact encoded limits, independent CSV
parsing, safe HTML, malformed UTF-8/files, CRUD, filter/export scope, unapplied
forms, full-registry mobile layout and stale reads/confirmations. Desktop/mobile
visual inspection used fictional records only. All 2,077 retained checksums and
the 209-entry public build pass.

[Source #345](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/345)
merged as `3a5d334cf88fb60bb720aa12c3a4c2e8a0a68b25` after all four checks passed.
[Website #192](https://github.com/LystadJS/LystadJS.github.io/pull/192) merged as
`4be7867b4fe1c8f1d481c887e5db560331e066dc` after audit and regression passed.
The mirror contains 200 public files; repeat synchronization copied/removed zero.
All 201 preferred-site canonical URLs (including its manifest) match expected
hashes. An older query-string index cache was separately observed; canonical
index bytes match. The campaign browser suite and all fifteen reporting suites
pass at the preferred site. The original site passes the campaign and main report
suites and all eight changed-asset hashes. These are fictional-data engineering
checks; actual participant and government-client acceptance remains unrecorded.

Four new essential public files reuse the existing theme/app styles and country
registry. No model, package dependency, backend, personal R/Python change or
Hugging Face storage is added. Notebook data is manual and private by user choice;
no records or generated outputs are committed or uploaded. Source policy/model
gates and all 37 reserved meetings remain unchanged. See the
[data contract](CAMPAIGN_NOTEBOOK.md).

## Previous verified application and facilitator

Application 1.76.0 and the model-free four-file facilitator remain available. The
[previous checkpoint](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/cdd2b699f329f300d62b34154bcd8dcf21fb4132/docs/OVERNIGHT_WORK.md)
retains 197 preferred-site hashes, fifteen live reporting workflows, three
original-site suites, 264 Python tests, 2,077 package checksums and the 205-entry
build, plus source #343's model-free paired draft/Word/HTML rehearsal. These are
engineering receipts at their original scope, not new user/model acceptance.
Actual model, desktop Word and diplomat/government-browser validation remain
outstanding.

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
   Extend campaign workflows beyond one lead/current row with explicit contact and
   dated interaction requirements; keep shared authentication and election eligibility
   separate from manual outreach records. Preserve browser/personal-runtime boundaries.
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
