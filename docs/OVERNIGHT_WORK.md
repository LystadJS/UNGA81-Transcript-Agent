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

## Release 1.79.0 candidate: reusable campaign contact profiles

Country forms now stage reusable, unverified profiles with a name, role, address
and notes. Explicit copying fills lead or new-interaction fields, with Keep/Escape
before replacing populated destinations. Copies remain independent: editing or
removing a profile never rewrites prior interaction snapshots, lead fields or
status counts. Removal asks before clearing that profile and its editing fields;
newer edits invalidate stale decisions. Pending fields block country Apply until
added, updated or cleared. Apply commits the form; JSON saves it.

V3 JSON reads strict v1/v2 without inventing contacts or history. Up to 25 profiles
per place and 1,000 total share the 1 MiB notebook limit. A separate contact CSV
exports every profile; original country/interaction CSV scopes stay separate.
Script-free HTML and JSON include complete profiles and logs. Cached earlier
layouts preserve imported profiles through edits/saves; mismatched core files
refuse entry with a reload message. No new runtime file, dependency, backend,
model, private records or Hugging Face storage is added.

Local core/browser checks pass for strict limits/IDs, independent contact CSV
parsing, v1/v2 migration, complete exports versus filters, explicit lead/log copying,
snapshot preservation, stale removals, cached layouts and mobile/reading-copy
long-text layout. Fictional desktop/mobile visual inspection passed. All 2,077
checksums and the 209-entry public build pass. CI/deployment receipts are pending. Reusable profiles are not
verified identities, a synchronized directory or authenticated election CRM.
Actual diplomat/government-browser acceptance remains unrecorded.

## Previous verified release

[Release 1.78.0 checkpoint](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/b5dd9a11da4de39e4bef0e4c91acd894b1dcac1e/docs/OVERNIGHT_WORK.md)
retains 201 preferred-site hashes, five original-site asset hashes and the dated
campaign workflow passing live at both URLs, plus three passing source checks,
two website checks, 264 Python tests, 2,077 checksums and 209-entry public build.
It links the preceding fifteen live reporting and model-free facilitator receipts.
These remain engineering checks at their original scope, not user/model acceptance.
Actual model, desktop Word and diplomat/government-browser validation is outstanding.

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
   Extend campaign workflows with reusable contact profiles and explicit links to
   dated interactions; keep shared authentication and election eligibility
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
