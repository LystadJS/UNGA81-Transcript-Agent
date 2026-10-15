# C0 implementation acceptance receipt — 15 October 2026

**Implementation candidate, not self-approved release.** Branch `coord/c0-product-contracts`; base `da4ab9ed11dba3693d11aa12f5333963b1b85478` (initial inspection `691f13bb53232f72a40461855c8e08a78b21befe`; intervening changes were coordinator-ledger documentation only). Exact final commit and hosted run/job identities belong in the draft PR's append-only acceptance comment so recording a test does not change the tested source. No merge or deployment requested or performed.

## Completed locally before initial commit

- New metadata-only query, capability, product and external-decision contracts; separate derived readiness contract; pure ES-module validators, signed gate verification, immutable session state and memory-only filtered export.
- Requested/resolved scope, distinct original hash bases, parent/code-point evidence, explicit fit/view populations, complete fit/assignment denominators and negative-case withholding are tested.
- Native Node 22.16.0 suite: **111 tests PASS; zero failed/skipped**. Tests include key/signature/expiry/destination/head/tree/source/population mismatches, conflicts, unknown fields, numeric and identifier boundaries, invalid-import/stale-async clearing and partial-source/no-match distinctions. Keys are generated only in test memory.
- Python 3.13.5 with jsonschema 4.26.0: **52 independent standard-schema and hash/mutation checks PASS; zero skipped**. CI pins jsonschema 4.23.0 for an additional reproducibility check.
- Seven generated schema documents and four synthetic examples pinned by `interface-lock.json`. Deterministic two-directory emission and byte-for-byte comparison required by CI.
- Additive scoped ownership register and seven worker handoffs prepared. Original OWNERSHIP.md remains unchanged. No worker branch creation or implementation is claimed.

## Current evidence and unresolved dependency facts

PR71 is already merged engineering-only; its historical syntax failure is not current work. PR82 is open at `32112ff5793c1be763db709aa3ef536fb409428a`. Independent PR87 now reports engineering HOLD for R identifier coercion and inconsistent derived identifier bounds; hosted original native-R tests run, but independent probes fail. C0 does not patch PR82 or PR87; V1's handoff preserves those failures and requests repairs/repinned independent review. Main also records actual pinned PR66 ONNX execution. Its new 16-family authored contrast benchmark reports 0/16 intended paraphrase-over-contradiction orderings for both MiniLM and a newly fitted TF-IDF baseline (run 38769887728). This is scoped counterevidence, not a general error rate or a test of the archived lexical transform. Neither is promoted to a stance model.

## Acceptance matrix at implementation commit

| Gate | Recorded status |
|---|---|
| New C0 local native synthetic tests | PASS, 111/111 |
| Independent JSON Schema checks | PASS, 52 checks |
| New interface artifact hashes | PASS locally; remote equality to be checked after push |
| Source privacy within this implementation | Metadata and invented fixtures only; no source text/model vectors/keys |
| Full local Git checkout | BLOCKED: `git ls-remote` failed to resolve github.com |
| Full local native upstream suites | NOT RUN; no substituted V8/mock pass claimed |
| Hosted exact worker and effective-tree suites | NOT RUN at commit creation; inspect new workflow and append exact results in PR |
| Real source authentication and model-quality study | NOT RUN, outside C0 |
| Operational key provisioning / actual human approval | NOT RUN, outside C0 |
| UI/browser/rendered integration | NOT RUN, assigned U1/C1 |
| Scientific and publication authority | WITHHELD; all existing gates unchanged |

The new coordinator-only workflow is read-only, path/branch limited, and has separate worker-head/effective-tree jobs. It runs native C0 tests, independent schema/replay checks, original v1 interchange, source-inventory, source-comparability, W1 historical-link and merged-PR71 tests. It never builds/deploys Pages, downloads models, reads private originals or executes heldouts. A successful original suite is not evidence that PR82's independent defects are repaired.


## Independent PR91 security review and repaired candidate — 15 October 2026

The earlier 111-test implementation receipt is historical, not final independent acceptance. New checks reproduced omitted signed vetoes, misplaced comparison/display gates, unsafe data-object hooks, asynchronous binding/validation mutation and reserved global-section identity. See `research/integration/product_contracts/INDEPENDENT_REVIEW.md` and the mandatory `test_independent_review.mjs` suite.

Local source-exact review: 64 independent cases yield 21 pass/43 fail against initial `4ea131fb33ea7735b6543e8ba2110ecb268743ab`, then 64/64 pass after repairs. Original 111 tests remain and pass; combined 175/175, no skips. Independent schema/hash checks 52/52, deterministic emission unchanged against the existing interface lock. Original and current head checks are not conflated. Full repaired-head hosted evidence and final independent engineering disposition will be appended to the PR discussion after actual execution without altering that tested commit.

Every change is C0-owned. PR71's accepted code, PR82/87, other worker namespaces, shared/frozen protocols, source records, site files and release manifests are unchanged. Ownership guard reports only observed path/mode facts, not an unsupported runtime private-read count. This review does not authorize merging, public delivery, real data or operational signing keys.
