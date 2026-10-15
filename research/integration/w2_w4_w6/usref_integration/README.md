# Prospective US-relative integration gate

Coordinator-only; synthetic engineering. This gate implements stage G1 of the
pinned PR94 plan. It does not adopt the gate, change protections, integrate the
products, retarget PRs, deploy, publish, or authorize source access.

## Trigger and stage contract

`coord-us-relative-integration.yml` runs without workflow path filters on PR
open/synchronize/reopen/edit/ready-for-review, main push, and merge-group events.
Its single aggregate status is `usref-integration-required`. Every matrix job
must literally succeed. The always-running finalizer reconstructs every tested
Git tree, parses raw test inventories and native receipts, and checks hashes,
stage, event/status SHA, run/attempt, head/base and live freshness. No manual
workflow-dispatch receipt is accepted as a required PR status.

`stage.json` explicitly declares `bootstrap` in this proposal. The bootstrap
head/effective receipts mean gate controls, native W4 and frozen-contract checks,
NOT product acceptance. The combined mode merges immutable #82, #92 and #93
payload objects in that order with the actual event head/base. It changes only
the disposable stage declaration to `integrated`. This tree includes the actual
prospective gate. No Git ref, controller index or source PR changes. Local
unreferenced commit objects are ancestry envelopes, not branch merges.

Subsequent authorized coordinator stage advances are `phase1`, `phase2`, then
`integrated`. Change the stage with separately reviewed integration glue; never
infer it from missing modules. Each stage requires the complete corresponding
15/12/4-path payload and original blob identities. Partial products, removed
modules, stage downgrades, altered historical files, symlinks, submodules or
conflicts fail. An intended future product update needs a reviewed successor
policy and evidence; this gate never auto-repins a historical test expectation.

## Preserved evidence and validation

The original Phase1 runner still uses `--require-complete`; #87's seven retained
R1/R2 probes run verbatim from its immutable commit. Its historical declared head
and base remain in its original receipt and are not mislabeled as current
execution identity. #93's independent test harness runs from the actual combined
tree, or from the pinned reviewer for the explicitly declared Phase2 stage.
All original axe incompletes and their separate measured resolutions survive.

Full coverage includes 40 Phase1 tests, 25 native W4 tests, 49 bridge/sidecar tests
(including the 40), seven #87 probes, four build tests, 12 Node tests, eight model
replays/six Phase1 pins, 17 native Chromium tests and seven independent #93
methods, plus source interchange and frozen inferential guards. Raw unique test
IDs and outcomes are retained, not only totals. All required native result files,
nonempty raw logs and file digests are checked again by the finalizer. Native R,
Chromium and axe are mandatory even in provisioning bootstrap jobs; no skips or
`continue-on-error` paths exist. Runtime versions match the recorded acceptance
baseline in policy.json or the job fails for a reviewed compatibility decision.

Tests exercise wrong/missing base identities, skipped/failed/cancelled jobs,
absent/malformed/empty evidence, false stage/authority claims, unknown modes,
removed gate/product files, duplicate test IDs, conflicts, unsafe paths, and
missing runtimes. Real Git toy repositories verify ordered composition and that
refs/index/unrelated objects stay unchanged. No corpus is used by these tests.

## Source and execution boundary

Checkout starts sparse in coordinator gate files. The controller reads Git tree
metadata and materializes only exact gate/payload paths and the 15 named
upstream code/test/contract dependencies in `policy.json`. All dependency modes
and blobs must match the reviewed historical base before any contents are read.
There is no directory/extension fallback, including for source-like `.py` files. It never checks out `data/`, `un/`, reports,
private corpora, site assets or transcript files. Dependency installation is
runner setup; analytical execution accepts generated synthetic panels only.
Browser tests retain their original no-network behavior. The gate performs
GET-only GitHub freshness checks, not permissions/protection writes. Tokens used
for freshness reads are removed from test subprocess environments.

Artifacts contain only execution identities, synthetic results, build fixtures
(including intentionally corrupt negative controls), raw logs and receipts.
They are not Pages artifacts. No `build_pages.py`, mirror sync or release action
is invoked. The stable check is an executable proposal, not proof that repository
administrators have required it or prevented bypass. Branch-protection access
remains unavailable to this integration; enforcement is UNVERIFIED and every
receipt retains merge/publication/source authorization as false.

This workflow runs ordinary PR code with read-only contents permission. It is
not a signed independent authority, and cannot protect against an administrator
or a malicious change to the required workflow itself without external enforced
workflow/code-owner requirements. Adoption requires a separately verified
protection snapshot, trusted check-source configuration and explicit authority.

## Reproduce

Run `python research/integration/w2_w4_w6/usref_integration/test_gate.py -v` for
source-free controls. Hosted jobs use `gate.py prepare`, then `run_suites.py`,
and `gate.py finalize`. Event JSON and identity environment variables are
mandatory. Output must be a new directory outside all repository roots. Failed
and successful prior acceptance archives are not edited or overwritten.

No full WCAG, manual screen-reader, actual browser zoom or Firefox/WebKit
certification is implied by retained Chromium/contrast acceptance.

## G97 repair and status-base binding, 15 October 2026

Repair `6e18e715a5821db94651904edeef60d8e2f0ec3b` closes G97-1 through
G97-3. `evidence_contract.py` requires stage-defined supporting evidence
independently of producer manifests and verifies build/frame, native records,
scan/target coverage, measured contrasts and SVG text. Fixed mandatory test-ID
inventories are reconciled with raw outcomes and counts. PR87 historical labels
remain intact, with separate actual-execution bindings. The materializer uses
the explicit dependency inventory described above, retaining uppercase `.R`.

Follow-up `0f237cbfecf8bf747b1e6b15fcdb90a9bb71ff24` addresses PR payloads
whose reported base snapshot predates the actual GitHub status merge. For PR
events the gate resolves the base only after proving two ordered status-commit
parents, exact proposed head, ancestor relation of the reported base, and equality
with an independently recomputed merge tree. `event_base_sha` is retained and
`base_resolution` states this derivation. Existing live-reference checks still
reject later head/base drift, including drift after successful test execution.
Neither evidence from a stale status nor a different mutable base is substituted.

Run `38814014750` failed before tests on the base-snapshot mismatch. After the
follow-up, run `38814668297` passed all three execution jobs, including native R
and Chromium, but its aggregate rejected subsequent main-branch movement. The
metadata-only edited event `38815149989` retained the old status merge and failed
freshness again. Those failures remain recorded; no failed aggregate is called
accepted. This documentation update requests a fresh exact-head/status run.

Original gate30 and independent reviewer15 methods, including all eight rejection
regressions, are unchanged. Local reruns also cover 21 extended evidence/source
boundaries and nine independent synthetic Git status-binding cases. Current-base
hosted results and repinned PR98 review remain required before repair acceptance.
No adoption, product integration, retargeting, changed protection, publication or
real/private/reserved transcript access is authorized by any of these repairs.
