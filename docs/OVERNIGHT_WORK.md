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

## Release 1.80.0 candidate: reviewed contact-only transfer

The notebook exports a separate `un.campaign-contacts.v1` JSON with country labels
and complete profiles, including contact notes, excluding campaign/lead/status
fields, country notes and conversations. Import validates the complete file and
resulting notebook before a country-grouped review. Explicit approval appends
new profiles, skips identical saved IDs and refuses differing contents under an
existing ID. Matching names/addresses are not merged or treated as verified people.
New countries start Not assessed with empty leads and history. Existing notes,
statuses, leads, conversations and filters remain intact. Full JSON saves work;
contact-only downloads never clear unsaved full-notebook protection.

The current form must have no pending changes. An unchanged edit form refreshes
its profile array before any later Apply. No-op imports do not dirty work. All
per-country, total and complete-state 1 MiB bounds apply before mutation. Latest
operation/revision guards cover both file controls; obsolete selections clean up
independently, and canceled previews release hidden contact details. No runtime
file, dependency, backend, model weight, private record or HF storage is added.
Local core and both campaign browser suites pass: privacy scope, immutable append,
replay/conflict refusal, complete-state budgets, Keep/Escape, pending/unchanged
forms, stale read/preview decisions, cross-control cleanup and mobile. Fictional
desktop/mobile preview inspection passed. All 2,077 checksums and the 209-entry
public build pass. CI/deployment receipts are pending.

## Previous verified release

[Release 1.79.0 checkpoint](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/cd606b7aea9aa50cfa345cd7efa4f18869f0294b/docs/OVERNIGHT_WORK.md)
retains 201 preferred-site hashes, five original-site assets and the reusable
profile workflow passing live at both URLs; source #349 and website #194 passed
before merge. It links 264 Python tests, 2,077 retained checksums, a 209-entry
public build and prior reporting/model-free facilitator receipts. These are
engineering checks at their original scope, not user/model acceptance. Actual
model, desktop Word and diplomat/government-browser acceptance remains outstanding.

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
   Rehearse the campaign workflow with actual users, then prioritize reviewable bulk
   contact transfer or explicit calendar follow-ups. Contact copies stay independent;
   keep shared authentication and election eligibility separate from manual records. Preserve browser/personal-runtime boundaries.
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
