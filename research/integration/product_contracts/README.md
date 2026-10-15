# C0 source-safe product contracts

**Version 1.0.0 interface candidate; synthetic engineering only. No merge, empirical fit, publication, delivery or site wiring.** The user authorized implementation of the question-first audit's C0 lane on 15 October 2026. Base inspected: `691f13bb53232f72a40461855c8e08a78b21befe`.

## Implemented contract boundary

`schemas.mjs` exports closed Draft 2020-12 shapes. Three input wrappers are `un.research-query.v1`, `un.product-capability.v1` and `un.evidence-product.v1`. `un.product-decision.v1` represents external decisions, and `un.product-readiness.v1` is the derived, non-authoritative safe read model. Receipt/key shapes are also explicit. No existing upstream schema, method, source hash, review decision or threshold changes.

These are **metadata/reference wrappers**, not transcript or numerical-vector containers. They contain bounded opaque IDs, integer denominators, digest-bound upstream artifact references and code-point spans. No free-form narrative, original text, embeddings, HTML, URL, signing key or self-attested gate belongs in a product. R1's separately approved prose remains in its existing readout artifact; C0 carries a bound reference, not a second copy of its contents. A reference is not permission to fetch or display its target.

The upstream registry includes the actual PR82 result name `un.us-relative-trajectories.v1`; this is a typed reference, not registration as an official parallel-analysis producer. `un.parallel-source-inventory.v1` retains the complete unverified/missing universe. Existing corpus, review, latent, readout, source-inventory and `un.parallel-analysis.v1` validators remain the sole upstream authorities. C0 validates wrapper relationships, not the underlying scientific result.

## APIs

- `parseStrict(text)`: rejects duplicate/escaped-duplicate keys, prototype keys, invalid Unicode, unsafe numbers, excessive nesting and input over 2 MiB. Use this at the JSON import boundary, not plain JSON.parse.
- `validateQuery(query)`: immutable requested/resolved substantive scope, recorded defaults, real inclusive calendar dates and New York timezone. IDs are never numerically coerced; `01` and `1` differ. The UI/catalog layer resolves raw user labels before constructing this canonical query. No model knobs are admitted.
- `validateCapability(capability)`: task/regime/recipe configuration and limits. No capability object certifies itself as approved. Multi-node fallback traversal/cycle checking belongs to U2.
- `await validateProduct(product, query, capability)`: closed shapes, exact query/policy digests, source/registry/hash basis, fit versus display populations, complete attempt ledger, assignment counts, evidence joins, country capacity, spans and result bindings.
- `await assess({query, capability, product, receipts, trustedKeys, destination, now})`: recomputes per-section gate vectors and safe output. Unknown authority, wrong signature, stale/conflicting decisions, changed worker/tree/product/population and malformed imports cannot enable a section.
- `await exportReadModel(input)`: rechecks local-export authority and serializes only the filtered safe read model into memory. It never writes a file, sends mail or serializes the unfiltered input product.
- `createSession()`: load, snapshot and invalidate; clears old results before imports and guards against stale asynchronous completion. Snapshots are copies, not permissions. Export must be re-assessed, never authorized from a saved can_export flag.

The implementation uses Web Crypto SHA-256 and Ed25519, with no network calls or runtime packages. It is an ES module usable in Node 22; future browser integration must test the actual browser's crypto support and fail closed if absent. No browser conformance is claimed by the Node tests.

## Readiness and evidence precedence

| Output | Required independent decisions |
|---|---|
| Descriptive section | Engineering, source, review, destination-specific output authority |
| Comparison/trend | Above plus comparability |
| Map | Above plus display validation |
| Inferential section | Above plus applicable statistical acceptance |
| Local export | A separate exact-destination output authorization; view permission is insufficient |
| Public site, email, real development | Prohibited by this initial implementation even if a test signer supplies PASS |

Gate values remain separate: pass, fail, not_run, not_applicable and conflict. Not-applicable never substitutes for a required pass. A failed optional map gate cannot erase a valid descriptive section. Missing/unverified records make an otherwise empty result partial, not a complete zero. Frame = eligible + excluded + missing + unverified. Planned fits = attempted + skipped; attempted = succeeded + failed. All ledger IDs remain present. Display population is a declared subset of the fit population, never an implicit refit.

A trusted **host-side** keyring supplies public verification keys with narrow gate and destination authority. It is never loaded from uploaded product/receipt JSON. Each signed payload binds the full product, query, capability, source/selection, fit/view population, worker commit and effective tree plus issuance/expiry and exact section/destination. Hashes establish consistency; signatures only establish the configured signer's identity, not source truth. Only an authorized source/review/scientific process may issue that gate after running its authoritative checks. No operational keyring or real approval is provisioned here. Tests generate ephemeral keys in memory; none are committed or exported.

Engineering uses coordinator_acceptance evidence, not PR prose, mergeability, an arbitrary CI success or a model's own declaration. A CI run is evidence for its actual worker/effective tree; it does not authorize source, inference or publication gates. Source, comparability, owner-review, statistical, display and output decisions each require their matching evidence kind and delegated signer. Conflicting active decisions with the same binding yield conflict; the implementation never selects the newest or most optimistic receipt. Superseding/revoking a decision requires a separately adjudicated trusted ledger update; no self-authored supersedes flag exists. Every supplied stale/malformed receipt fails closed.

Structured signed decisions are a **new integration interface**, not a claim that historical PR comments already have digital signatures. Historical evidence in DEPENDENCIES.json is a handoff snapshot, not a runtime authority store.

## Dependencies incorporated

- Merged PR71 accepted worker `8838ff1eb6717bde27265dd4ce8295a2d0ba28ac`, merge `e25b61c6d03562a9f054be0412b6869198089fe4`: reuse its existing audit and exact-path/hash fixture exception. Its historical syntax failure was repaired; Q1 is new-product follow-up.
- Open PR82 worker `32112ff5793c1be763db709aa3ef536fb409428a`: reuse its contracts/producer/Node/R implementation, not a new US baseline. **New independent PR87 review places it on engineering HOLD**: R converts `01`/`1` identifiers, and 160-character input periods overflow derived ID bounds. Hosted native-R coverage now exists, but independent probes fail. V1 must repair those defects and obtain repinned review before accepted display integration. Do not call the old R skip the only remaining blocker.
- PR66's updated main ledger records actual pinned ONNX execution at worker `5c4aeb79107dc118cebff1761c70e5a9af021281`; that does not establish model quality or empirical source acceptance. M1 consumes the evidence without duplicating the encoder.

## Reproduce (synthetic only)

```sh
node --test research/integration/product_contracts/test_contracts.mjs
node research/integration/product_contracts/emit_contracts.mjs /tmp/c0-generated
python research/integration/product_contracts/check_schemas.py /tmp/c0-generated
node research/integration/product_contracts/emit_contracts.mjs /tmp/c0-replay
diff -rq /tmp/c0-generated /tmp/c0-replay
```

Use new output directories. The independent Python check requires jsonschema (CI pins 4.23.0); missing dependencies are errors, not skipped passes. `interface-lock.json` pins seven generated schemas and four examples. The emitter refuses byte drift and overwrites. Initial lock creation is explicit `--write-lock` and exclusive-create only; workers must not regenerate an accepted lock. This is an interface candidate lock for parallel development, **not** a scientific protocol freeze.

The coordinator-owned workflow runs both the immutable worker head and GitHub's effective PR tree, records their actual SHAs, enforces C0 changed-path ownership, runs native tests and independent schema/replay checks, then existing interchange, source-inventory, W1/source-comparability and merged-PR71 suites. No builds, model downloads, private source reads, held-out execution, deployment or write tokens.

## Handoff and limitations

See `docs/parallel-work/C0_PRODUCT_OWNERSHIP.md`, `c0-ownership.json` and `C0_WORKER_HANDOFFS.md`. New lanes can use the reviewed C0 commit as a stacked read-only dependency; existing PR70/82 branches are not rebased or merged by this work. C1 alone connects future accepted consumers to shared browser/build files.

This is not an empirical model evaluator, catalog/search implementation, source authenticator, PKI deployment, human-review substitute, UI renderer or publication service. No real source integration or operational authority is enabled. Synthetic test success never changes the 37 reserved transcript lock, G01–G13, temporal v2 failures/v3 holdout, original hashes, completed owner choices or D1 O1–O5.
