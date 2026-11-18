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

## Verified release 1.64.0

| PR | Change | Checked head / merge |
| --- | --- | --- |
| [Source #311](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/311) | Direct report-package ZIP reopening and source addition | Three checks passed at `988f90b`; merged `69e5f6f` |
| [Website #177](https://github.com/LystadJS/LystadJS.github.io/pull/177) | Canonical mirror, release pins and live package-open suite | Audit/regression passed at `5f5f6b9`; merged `b9ad696` |

Both public URLs serve 1.64.0. All 195 checked portfolio files (194 manifest
entries plus the manifest) match expected SHA-256 hashes. Ten reporting browser
suites pass against the actual preferred URL with fictional sources: reporting,
package opening, source removal/addition, replacement, packages, device library,
archive handoff, Word and print/PDF. Package opening also passes at the original
source URL, whose four changed assets match canonical hashes. Skipped PR live
jobs are not counted as deployed verification.

Open and Add sources accept original report-package ZIPs directly, preserving
JSON support. No manual extraction is required for the app's own packages. The
reader bounds the whole file to 25 MB, accepts only the five original uncompressed
entries, verifies contiguous matching local/central headers and CRCs, then checks
SHA-256 file hashes and manifest/report metadata. Original source bytes are
revalidated through the existing saved-report path before any replacement prompt.
Imported HTML is never rendered or executed; every derived claim is rebuilt.
Checksums establish consistency, not source authentication. ZIPs outside
this exact format are refused; extracted report.json remains available.

Keep/Replace, Escape, preserved invalid-import state and stale-operation checks
apply to direct packages. Source addition keeps current settings and annotations,
excludes incoming report notes and refuses overlapping meetings. A ZIP renamed
with a JSON suffix is detected by its signature. Neither import nor preparation
is automatic saving. Export schemas, notes, source selection and storage limits
remain unchanged.

Local validation passes 256 Python tests and ten synthetic reporting browser
suites plus pure contracts. New checks cover independent ZIP entry extraction,
original package round-trip, malformed/extra/missing/encrypted/compressed/trailing
structures, offsets and size fields, CRC/SHA-256/manifest mismatches, exact size
bounds, corrupt original sources, Keep/Escape, retained notes/settings/sources,
source addition, overlap and delayed-edit refusal, mobile and no transcript
requests. A separate compatibility check generated a fictional package with the
actual archived 1.63 writer and reopened it losslessly with the new reader.
Usability instructions now include direct ZIP reopening; no actual participant
session or diplomat acceptance is claimed.

The public build remains 203 entries and the mirror 194 files. Four assets and
the manifest change; sync is idempotent. Package/main script URLs are versioned.
No application file, dependency, schema, model, server, upload or Hugging Face
storage is added. All 2,077 R-package checksums remain valid; scientific gates,
original records and all 37 reserved meetings are unchanged.

The preserved [1.63.0 receipt](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/51c94bdab12869fe4e6a2e3cdd908e1dfc137962/docs/OVERNIGHT_WORK.md)
records source removal and links earlier reporting checkpoints. Use historical
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

1. Continue useful reporting work from the verified 1.64.0 release, then expand
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
