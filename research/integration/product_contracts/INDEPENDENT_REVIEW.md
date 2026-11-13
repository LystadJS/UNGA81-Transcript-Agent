# Independent C0 PR91 review — security repairs and acceptance evidence

**Scope:** metadata-only synthetic engineering. No merge/deploy, operational approvals, private source reads, held-out execution or scientific acceptance.

## Exact starting source

PR91 `coord/c0-product-contracts`, initial head `4ea131fb33ea7735b6543e8ba2110ecb268743ab`, main `da4ab9ed11dba3693d11aa12f5333963b1b85478`. Sixteen local files matched exact repository Git blob identities. The initial 111 native tests and 52 independent standard-schema checks passed again before repairs. That result did not establish correctness of all trust boundaries.

## Independently reproduced defects

| ID | Finding on original head | Repair and regression |
|---|---|---|
| C0-R1 | Removing a valid signed source FAIL from an otherwise passing set restored `ready`; individual signatures did not certify the complete current decision set. | Require a current host-supplied complete-set SHA-256 commitment, separately from uploaded receipts; verify all retained signatures and scopes as before. Omission, addition, substitution, expiration and export checks covered. |
| C0-R2 | Display references outside `map`, comparison templates inside descriptive overviews and comparison artifact references could avoid the corresponding gate. | Derive mandatory comparability/display gates from actual templates, uncertainty and typed references as well as section kind. Keep valid independent descriptive sections visible. |
| C0-R3 | Required non-enumerable getters, array getters/toJSON hooks, sparse/custom arrays and hidden fields escaped the data-only boundary. | Descriptor-checked ordinary dense JSON data; canonical copying without serialization hooks; safe outer-context checks, cycle/depth bounds. |
| C0-R4 | Standalone asynchronous validation/binding observed mutable input after crypto yielded, despite the assessment wrapper's snapshot guarantee. | Synchronous snapshots in both public APIs before their first await. |
| C0-R5 | A section could use reserved ID `all`, colliding with the decision payload's global scope selector. | Reject that section ID before verification; no IDs are coerced or rewritten. |

No existing source/representation/holdout/statistical/publication gate has been relaxed. No cryptographic primitive is replaced. Gate evidence authenticity remains the responsibility of separately authorized producers; a signed declaration is not proof of its empirical truth.

## Independent red-to-green evidence

The exact same 64-case independent suite was run against the three unchanged original C0 source modules and the repaired source. Original: **21 PASS, 43 FAIL, 0 SKIP**; repaired: **64 PASS, 0 FAIL, 0 SKIP**. Some cases test the newly required completeness API; 43 is the number of failed assertions/test cases, not 43 separate vulnerabilities. Ten earlier direct probes produced one positive control PASS and nine failing safety assertions. The failing original source remains preserved by its immutable Git commit.

All 111 original test cases and assertions remain; their synthetic signing helper now explicitly provisions the trusted set commitment. Cases intended to test signature, authority or conflict still reach those checks by deliberately pinning the corresponding test ledger. Combined local result: **175 PASS, 0 FAIL, 0 SKIP**. Required independent Draft 2020-12/schema/hash mutations: **52 PASS**. Generated schemas/examples match both a separate restart and the initial interface lock byte-for-byte. No schema version or lock bytes changed.

Native local runtime: Node22.16.0, Python3.13.5, jsonschema4.26.0. The local tree is a Git-blob-verified source subset; direct GitHub DNS checkout is unavailable. It is not called a full local repository test. The coordinator-owned workflow runs full-checkout exact worker and effective-tree native upstream regressions plus an immutable original-head red replay, preserving expected failures rather than suppressing repaired-head failures.

## Acceptance boundary

At patch preparation, hosted repaired-head jobs are pending. The final PR91 acceptance comment must record the actual repaired SHA, actual checked-out worker/effective trees, run/job IDs, complete results, ownership refresh and current-main comparison. No hosted PASS is claimed before those jobs finish. The initial CI receipts apply only to the initial SHA and remain historical evidence.

The requested review can finalize **synthetic engineering acceptance** after corrected-head native checks and independent probes pass. Real source authentication, cryptographic key custody/provisioning, current trusted-ledger/revocation delivery, UI/served-browser integration, full changed-product build scan and empirical interpretation remain unexecuted/outside this C0 change. The runtime remains synthetic-only, public-site/email/development outputs remain prohibited, and all 37 reserved transcripts, human decisions, D1 O1–O5 and research inferential locks remain intact.
