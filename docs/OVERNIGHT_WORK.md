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

## Verified release 1.63.0

| PR | Change | Checked head / merge |
| --- | --- | --- |
| [Source #309](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/309) | Explicit loaded-source collection removal | Three checks passed at `75ccf29`; merged `a01edcc` |
| [Website #176](https://github.com/LystadJS/LystadJS.github.io/pull/176) | Canonical mirror, release pins and live removal test | Audit/regression passed at `c81af3d`; merged `1857c90` |

Both public URLs serve 1.63.0. All 195 checked portfolio files (194 manifest
entries plus the manifest) match expected SHA-256 hashes. Nine browser suites
pass against the actual preferred URL with fictional sources: reporting, source
removal/addition, replacement, packages, device library, archive handoff, Word and
print/PDF. Removal also passes at the original source URL. Skipped PR live jobs
are not counted as deployed verification. The first original-URL removal check
reached the older page during rollout; after release and changed-asset hashes
matched 1.63.0, a fresh removal check passed.

Manage loaded source collections displays meeting/segment counts and original
collection JSON bytes. Unlike unchecking a meeting, explicit removal reduces the
sources carried in saved JSON. Keep is the default and Escape preserves current
work. The dialog lists every affected meeting and counts removed notes/appendix
choices. Whole original bundles are removed; remaining source bytes and identities
are unchanged. Remaining selections, annotations and reusable settings stay intact.
Prepared exports are invalidated until preparation. Last-collection removal
explicitly clears the current assessment and source-bound annotations while
retaining mission settings and questions. A newer edit/source operation invalidates
an older confirmation. Downloaded files, saved device copies and the archive stay
unchanged; neither removal nor preparation is automatic saving.

Local validation passes 256 Python tests and nine synthetic reporting browser
suites plus pure contracts. New cases cover whole-bundle removal, exact kept source
identity, selective annotation pruning, unchecked bundles, invalid state refusal,
input immutability, default Keep/Escape/focus, smaller saved JSON, stale decisions,
explicit last-assessment clearing, unchanged device storage, reopening and mobile
layout without transcript requests. The mobile confirmation was visually inspected.
Usability instructions now include source removal; no actual participant session
or diplomat acceptance is claimed.

The public build remains 203 entries and the mirror 194 files. Five assets and
the manifest change; sync is idempotent. Core/main script and stylesheet URLs are
versioned. No application file, dependency, schema, model, server, upload or
Hugging Face storage is added. All 2,077 R-package checksums remain valid;
scientific gates, original records and all 37 reserved meetings are unchanged.

The preserved [1.62.0 receipt](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/37df49ef9fe2684f172cfa2312e005ced35b2c68/docs/OVERNIGHT_WORK.md)
records source addition and links earlier reporting checkpoints. Use historical
results at their original version and scope.

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

1. Continue useful reporting work from the verified 1.63.0 release, then expand
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
