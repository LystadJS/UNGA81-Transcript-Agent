# PR97 independent prospective-gate review

**Decision: HOLD / CHANGES REQUIRED. Review complete; gate engineering acceptance withheld.**

This decision concerns the prospective gate's enforcement, not a reversal of the
verified successful historical product execution. No adoption, branch merge,
retargeting, protection change, publication, deployment or real-source access is
performed or authorized. PR97 is unchanged.

## Exact identities and execution

| Item | Identity |
|---|---|
| Candidate PR97 | `ab559b74842e9a9165bf619f4869015d90588e8c` |
| Reviewed main | `da4ab9ed11dba3693d11aa12f5333963b1b85478` |
| Independent reviewer PR98, executed source | `2afc87819807f64c3a77fcbb75070ccec574bc1d` |
| New hosted review run | `38809798568`, attempt 1 |
| Exact-head review job | `116679851682` |
| Effective-tree review job | `116679851743` |
| Candidate/effective tree | `4f32c29a83ea69bffce2add75e2487396fde15a4` |
| Independently reconstructed combined tree | `e9f9dc9d4b8951059d6a210f7a99d3425c699f87` |

Both new review jobs concluded **FAILURE** because the eight rejection assertions
below exposed candidate defects. In each job the unchanged original gate controls
passed **30/30**. The new suite ran **15 methods: 7 passed, 8 assertion failures,
0 errors, 0 skipped tests**. No expected-failure decorator, continue-on-error or
weakened assertion converts these failures into passes.

## G97-1: mandatory evidence can be missing or explicitly adverse (P1)

Locations: `gate.py:307-316` and `run_suites.py:175-207`, under
`research/integration/w2_w4_w6/usref_integration/`.

`read_bundle` verifies only files listed by the producer. `audit_bundle` requires
raw logs, but does not require the full build or independent observation records;
it checks existence rather than contents of the axe/contrast files. The finalizer
validators accept all four of these temporary-copy mutations:

| Retained regression | Invalid input accepted |
|---|---|
| Test 08 | Delete the entire saved build/manifest directory and its manifest entries. |
| Test 09 | Delete `evidence/independent/observations.json` and its manifest entry. |
| Test 10 | Set a measured contrast record to `passed: false`, ratio `1.0`; refresh its digest. |
| Test 11 | Add an explicit axe color-contrast violation; refresh its digest. |

All outer identity bytes and their binding remain unchanged. Each probe calls the
actual `read_bundle`, `audit_bundle` and `validate_final` functions in sequence;
all return acceptance. The separately reconstructed identity trees also match.
The probe is not a new live required-check run and does not forge an external
signature. It tests the finalizer's own completeness and contradiction rules.

**Required repair:** define required evidence by stage independently of a supplied
file manifest, require and hash every required member, verify the saved build
manifest against its files, and validate axe/contrast/coverage structures and
outcomes. Zero violations and complete, successful per-target resolutions must be
checked together. Retain original incomplete reports alongside their separate
resolution records; do not suppress them. Missing evidence must reject acceptance.

## G97-2: native execution identity and retained test inventory are not bound (P1)

Locations: `run_suites.py:21-28,44-50,175-207`.

Native checks accept a success flag and a minimum count without comparing the
native execution head or test count to the outer identity and raw inventory.
Raw test IDs are checked for uniqueness/cardinality and consistency with the
producer's summary, not against the required retained inventory.

| Retained regression | Invalid input accepted |
|---|---|
| Test 12 | Phase1 native `head_sha` changed to a different valid-shaped SHA. |
| Test 13 | Native `tests_run: 999` with the unchanged 40-test raw log. |
| Test 14 | Replace the retained R1 regression's raw ID and summary ID with an unrelated placeholder, preserving totals. |

The live candidate's R1 regression was **not** removed. These are evidence-copy
mutations demonstrating that the aggregate would not detect the inconsistency.

**Required repair:** validate receipt kinds and mandatory fields, bind dynamic
native identity to the actual execution wrapper, reconcile exact counts and IDs
across native receipts/raw logs/summaries, and enforce the registered retained
regression inventory. Preserve the intentional historical PR87 head/base fields;
those are historical labels and need a separately validated actual-execution
wrapper, not rewriting to a new head. Additional reviewed tests may extend the
inventory; renaming or replacing mandatory tests must not pass on count alone.

## G97-3: code materialization is an open prefix/suffix filter (P1)

Locations: `gate.py:202-216` and `policy.json` materialization rules.

Test 15 creates an isolated toy Git repository containing only a fictional sentinel
at `research/longitudinal/private/synthetic-transcript.txt`. That path is not in the
31 approved payload paths. The unchanged materializer nevertheless reads its blob
and writes it into the candidate directory because `.txt` and the directory prefix
are permitted. The toy repository's refs and index remain unchanged.

**Required repair:** replace broad extension-based source selection with explicit,
reviewed code and synthetic-fixture dependencies, including allowed Git modes and
expected roles/identities. Unregistered source-like files must be excluded or
rejected before reading their blobs. Preserve the accepted uppercase `.R` payload
and required numerical/browser code. This is a prospective exposure risk, not an
assertion that a real transcript was opened in the prior run or this review.

## What independently verified

- All seven candidate code/workflow blob pins match the supplied source copies.
- All four original successful artifact archives and the retained initial failed
  combined archive pass SHA256 and ZIP CRC verification. Historical evidence is
  unchanged; mutations exist only in temporary copies.
- Each new hosted job verifies all **51 evidence-member hashes** in the original
  three matrix receipts, the original successful native receipts, nine axe scans
  with no reported violations, and all 444 historical contrast resolutions.
- Git trees were reconstructed using independent Git commands, without importing
  candidate tree helpers. The three intermediate payload trees, final combined
  tree and all **31** payload path/mode/blob identities match the recorded values.
  No unrelated path is added/deleted by composition. Refs and controller index are
  unchanged. Only Git metadata and the synthetic stage declaration are inspected.
- Working negative controls reject missing matrix modes, missing raw logs,
  unchanged-hash corruption, skipped native tests, a stale outer head and authority
  escalation. The pristine evidence remains accepted.

The review does **not** claim that arbitrary producer logs can be authenticated
cryptographically merely by parsing them. Its findings are specific missing
completeness, identity and cross-record checks in the declared gate. Malicious
workflow changes still require separately verified trusted-workflow/protection
controls; no such settings were read or changed here.

## Evidence retention and limits

| New reviewer artifact | SHA256 |
|---|---|
| Head `12007861709` | `e727f657b9536ec8ee89c3d11975bc971c406d17912725a17bc5a44131817f75` |
| Effective tree `12008331729` | `bc47621b11974c405bbdcd1befb9ce69363744d7244a187f6f76024d59d2d7a4` |

Both new archives were downloaded, verified, and inspected, including execution
identities, full original-control and independent-probe logs, failure receipts,
per-probe observations and independent tree reconstruction records.

The original native-R, numerical, source-contract and Chromium suites are verified
**historical evidence from run 38806920470, not newly executed product acceptance**.
This review newly executes the unchanged gate-control tests, new adversarial
validator/materializer tests and independent metadata-only Git reconstruction.
Local direct Git access failed due DNS; full Git reconstruction ran hosted.
Main-push/merge-group live behavior, branch-protection enforcement and full
accessibility conformance remain outside this review. No real source or reserved
transcript was opened; no frozen scientific gate or publication hold changed.

## Disposition

Keep PR97 unadopted and unmerged. Repair **G97-1, G97-2 and G97-3**, retain all eight
failing regression bodies/expectations, then rerun the independent review and the
full mandatory-R/Chromium combined-tree gate against exact repaired identities.
A successful old run is retained evidence, not acceptance of an unrepaired gate.
