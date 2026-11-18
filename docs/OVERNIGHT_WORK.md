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

## Verified patch 1.64.1

| PR | Change | Checked head / merge |
| --- | --- | --- |
| [Source #313](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/313) | Remove superseded package extraction instructions | Three checks passed at `315be7a`; merged `19f94be` |
| [Website #178](https://github.com/LystadJS/LystadJS.github.io/pull/178) | Canonical mirror and verification pins | Audit/regression passed at `abda993`; merged `beff1f0` |

Both public URLs serve 1.64.1. All 195 preferred-site files match their expected
SHA-256 hashes. Existing package-download and direct-package-opening browser
suites pass against the preferred URL; package opening also passes at the original
source URL. The updated post-download status and export help direct users to open
the ZIP in the workspace; extracted report.json remains an alternative. The main
script URL is versioned. This patch changes instructions and cache/release metadata,
with no new application files, dependencies, schemas, models or storage.

The [1.64.0 receipt](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/7992df9bf87e50bab32016d249cee76285ee08c1/docs/OVERNIGHT_WORK.md)
records the full functional release: 256 Python tests, ten live reporting suites,
actual 1.63-writer compatibility and original-source checks. Use those results at
their original version and scope. The current source PR also passes its full CI
contracts, numerical and browser checks; skipped PR live jobs are not live passes.
No actual diplomat usability session or accepted stance model is claimed.

Direct package opening remains bounded to the original five-file uncompressed
format with matching ZIP headers, CRCs, SHA-256 file hashes, manifest/report
metadata and separately revalidated original sources. Imported HTML never renders
or executes; report claims are rebuilt. Keep/Escape, invalid-import preservation,
stale-operation checks, overlapping-meeting refusal and foreign-annotation exclusion
remain in place. File consistency does not authenticate a source or speaker.

The public build remains 203 entries and the mirror 194 files. Three assets and
the manifest change; repeat sync copies zero files. Hugging Face storage, separate
personal R/Python execution, source/scientific gates and all 37 reserved meetings
are unchanged. The current 2,077-file R-package checksum inventory remains valid.

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

1. Continue useful reporting work from the verified 1.64.1 release, then expand
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
