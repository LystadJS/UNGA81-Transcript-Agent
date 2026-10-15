# U2 implementation evidence: 15 October 2026

Implementation candidate, synthetic-only. Independent coordinator engineering acceptance is pending. No merge or deployment.

## Input identities and scope

- Current main inspected: `da4ab9ed11dba3693d11aa12f5333963b1b85478`.
- Accepted C0 parent: `884097997f89b0040e4418480378f077e3b65434` (PR91).
- Accepted U1 consumer: `afb92e82881dc11003170899aef9958682d61abe` (PR95).
- New branch: `feat/question-first-router`, stacked draft against `coord/c0-product-contracts`.
- All implementation, tests and documentation are confined to `research/integration/question_router/**`. No C0, U1, source inventory, workflow, shared site or release file is modified.

## Newly executed local validation

| Suite | Observed outcome |
|---|---|
| U2 native metadata, routing, source bindings, trust and race tests | 126 PASS; zero failed/skipped |
| Read-only accepted U1 controller integration | 17 PASS; zero failed/skipped |
| Unchanged accepted C0 contract/signature/state tests | 175 PASS; zero failed/skipped |
| Independent C0 JSON Schema/hash checks | 52 PASS; zero failed/skipped |
| Dependency identity checks | Ten C0/inventory files and one accepted U1 controller match SHA256 and Git blobs |
| Nine-case metadata demonstration | Byte-identical across two executions; zero models run |

Runtime: Node 22.16.0, Python 3.13.5, local jsonschema version recorded in the delivered receipt. These are executions on a byte-verified source subset, not a full Git checkout, browser QA or new scientific observations. Native original inventory validation executes directly on every metadata fixture. The complete upstream source/W1/PR71 suites have not been rerun for U2.

The Git remote attempt failed with `Could not resolve host: github.com`. Original inventory validator/schema bytes were retrieved through the GitHub connector and verified against exact blobs `52be70fd2f6c86960217599be9dd478566bc83a2` and `80e1dba753f3bdb2fd59cf584b0c87748e1f9cc8`. No replacement validator was used. C0/U1 sources were restored from their accepted source packages and hash-checked; dependency-lock.json records every consumed/tested identity.

No U2-specific hosted exact-head/effective-tree result is asserted in this pre-commit record. Historical successful C0/U1 workflows are dependency evidence, not U2 acceptance. U2 owns no workflow; the coordinator handoff specifies separate complete-checkout verification. Exact pushed identity and any returned CI statuses belong in the PR discussion/delivered receipt without altering tested sources.

## Explicit unresolved integration items

1. U2 correctly reports no-product/unsupported-history as `unavailable`. The accepted U1 controller's exception path currently reduces an absent bundle to generic `failed / could_not_create`. A separate U1/C1-owned mapping is needed; U2 does not create a fake authorized status product.
2. U2 deliberately delivers no source prose. `getEvidence` is unavailable pending a separately authorized evidence service. Metadata routing and controller integration are tested; a real evidence drawer is not integrated by this task.
3. Full-checkout native upstream/effective-tree acceptance, independent U2 review and served U1+U2 browser integration remain NOT RUN. No accessibility, empirical model quality, authentic source, production key/ledger or public-output privacy certification is claimed.

There are no failing tests in the executed suite. Unexecuted obligations are not relabeled passes. All original source hashes, completed owner choices, 37 reserved transcripts, G01–G13, temporal v2/v3 holds and D1 O1–O5 remain untouched. No merge, force push, deployment, mirror, email, real transcript, external model or operational signing key.
