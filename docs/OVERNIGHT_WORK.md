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

## Verified release 1.58.0

| PR | Change | Verified result |
| --- | --- | --- |
| [Source #298](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/298) | Exact recorded affiliation and speaker-name filters | All three checks passed at `6741a3c`; merged as `eb450ec` |
| [Website #170](https://github.com/LystadJS/LystadJS.github.io/pull/170) | Canonical public sync, release/source pins | Mirror audit and website regression passed at `3bdf0c4`; merged as `07d7d2e` |

Both public URLs serve 1.58.0. All 194 portfolio files (193 manifest entries plus
the manifest) match expected SHA-256 hashes. The expanded reporting suite passes
against the live source URL. All five synthetic browser suites also pass against
the preferred portfolio URL: reporting, replacement, packages, device library and
archive handoff. Local checks pass 256 Python tests and the same five browser suites.
These are engineering checks, not diplomat usability or model-accuracy acceptance.
Do not count skipped PR live-verification jobs as live passes.

Exact country/affiliation and recorded-name controls narrow the passage list,
combined with all-word search and appendix-only view. Clearing filters preserves
notes and appendix choices. Names remain source labels, collective evidence stays
visible and missing metadata has a separate option. Filters leave prepared reports,
mandatory country coverage, neighboring context, saved-work JSON and full CSV intact.
Source replacement resets the filters; removing a meeting discards unavailable
values. The usability guide includes a corresponding participant task, still unrun.

Report schema v4 and preference schema v2 are unchanged; release metadata now
correctly lists those existing schemas. No model, dependency, server, automatic
saving or Hugging Face data was added. The public build still has 202 entries;
the mirror has 193 files and canonical sync is idempotent. The preserved
[1.57.0 receipt](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/eb450ec609ea1b2ee73f266f22fb73ebf12e4585/docs/OVERNIGHT_WORK.md)
records the device-library deployment and earlier checks.

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

1. Continue useful reporting work from the verified 1.58.0 release, then expand
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
