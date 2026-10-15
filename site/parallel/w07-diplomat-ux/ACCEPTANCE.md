# U1 implementation acceptance record

15 October 2026. **Implementation candidate; engineering acceptance WITHHELD pending strict served-browser and coordinator review.**

Base: C0 `884097997f89b0040e4418480378f077e3b65434`, tree `ea7571664f79cb78b4e134ce0f9e2f1283893f17`. Refreshed main: `da4ab9ed11dba3693d11aa12f5333963b1b85478`. Original C0 review and passing hosted runs are inherited dependency evidence, not new U1 CI.

## Newly executed

| Check | Result |
|---|---|
| U1 controller, trust, replay, evidence and native HTTP | 58 tests PASS, zero failures/skips |
| Unchanged accepted C0 native tests | 175 tests PASS, zero failures/skips |
| C0 dependency identities | 8/8 exact Git blob and SHA256 matches |
| C0 independent JSON Schema/hash controls | 52 PASS |
| Native HTTP entry/module/headers and distinct trust transport | PASS inside U1 tests; not a browser result |
| JavaScript/Python syntax | PASS |
| Actual served Chromium attempt | BLOCKED at navigation: `net::ERR_BLOCKED_BY_ADMINISTRATOR` |
| Browser interaction, responsive layout, rendered focus, visual review | NOT RUN; 22 checks authored, zero executed after blocked preflight |
| Exact-head/effective-tree full-checkout U1 CI | NOT RUN in this environment |

The full local Git access attempt failed with `Could not resolve host: github.com`. Native tests ran from a source subset bound to the accepted C0 blobs, not a claimed full repository checkout. GitHub source pushes and changed-path validation are recorded separately against the final commit in the PR discussion so recording evidence does not change tested source bytes.

No browser navigation restrictions were disabled or bypassed. There is no injected-DOM fallback or fabricated screenshot. All native positive results and the actual browser block are retained in the delivered engineering package. A dedicated U1 workflow was not created because U1 owns no workflows; its coordinator runner commands and Git metadata guard are included.

## Behavior covered natively

Minimal country/topic/date/meeting requests; leading-zero meeting identity; explicit versus default dates; complete/partial/no-match/failed/unavailable coverage; collective attribution; unchanged highlighting; memory-only saved result replay; bounded strict imports; unexpected authority fields; omitted signed veto and complete conflict; current key revocation, expiry and ledger mutation; invalid/canceled/out-of-order inputs and pending exports; authorized evidence identity/hash; source withholding; private in-process signing keys; and constrained loopback HTTP serving.

A U1-specific tightening prevents a destination-authorized export from exposing a section that is not also visible in the fresh current view. C0's implementation and tests are unchanged. The explicit output remains C0's filtered read model; the UI never serializes the original product or test signatures.

## Remaining gate

A coordinator must pin the final U1 commit, run the supplied exact-head and effective-tree guards, execute the native suites and strict HTTP Chromium cases in an allowed full checkout, inspect the rendered desktop/mobile screenshots and source/export behavior, and repair U1-owned failures. Current schema/CI success is not a substitute for that browser review. Broader accessibility, real data, model/trajectory integration and release permission remain separate.

Only `site/parallel/w07-diplomat-ux/**` is changed. The PR must remain DRAFT and UNMERGED. No shared entry point, stylesheet, workflow, upstream contract, source, frozen gate, release manifest or mirror was changed. No real or reserved transcripts, model download, V3 holdout, operational credentials or actual human decisions were used. No merge or deployment.
