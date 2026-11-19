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

## Source-only candidate: reporting and campaign rehearsal kit

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
must be recorded separately. Browser/calendar targets remain unspecified.

Local facilitator tests pass, including Node-only generation, schema/planned
counts, report/draft pairing, campaign outputs, metadata privacy and cleanup.
CI and merge receipts are pending. App assets, models, dependencies and HF storage
are unchanged; public application 1.81.0 remains verified. This prepares actual
user/client work and does not substitute for it.

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
