# US-relative trajectories — Phase 1

**Engineering-only, synthetic-only, nonpublished.** This coordinator sidecar implements contracts and arithmetic, not visual renderers or empirical diplomatic trajectories. It does not modify W4's estimator, the official interchange, any workflow, site asset, manifest, publication gate or source record. No release or merger is authorized by this implementation.

## Scope and ownership

All new implementation lives in `research/integration/w2_w4_w6/waggoner/`. The only existing file changed is the coordinator's `test_w4_bridge.py`, which adds the new test suite to its existing CI entry point while retaining its original tests. This avoids overlapping the active W4 worker namespace or touching the deployed W6 runtime. It is the research-side location proposed by the visualization specification, with the Phase 1 producer colocated here rather than independently editing W4.

Specification: `UNGA81_Waggoner_US_Relative_Visualization_Spec.md`, version 0.1, SHA256 `c0d4bdbda25abe8812361bca10bd8b7ddde2105217d5d0a7c6d0efa870ac683a`. Eight supplied golden cases are preserved semantically; the original design fixture hash is recorded in `golden_cases.json`. Initial repository base: `93b17c8779d959f5dd5559adb7f56381210f2f89`.

## Behavior

- Require the canonical structured grouping key `USA`, nationally representative capacity, synthetic attribution/review evidence, actual dates for available observations, and exact source/parent/meeting identities. Speech text and raw HTML are not admitted by the closed schema. Staff, collective and unverified affiliations are excluded, never converted into national evidence.
- Use one contemporaneous US profile per period for the complete declared comparison set. Country display selection returns copies; it cannot refit or change baseline membership.
- Require common declared topic, genre, language and source-type support. An absent required genre withholds that country-period. Pair-specific support and fixed-initial-period reference modes are explicitly rejected in Phase 1; neither is silently approximated.
- Preserve W4 equal-meeting-within-genre and equal-genre weighting, exposing each original source's final weight. Preserve actor/person identities rather than replacing them with country codes. The strict initial source-unit policy allows only one vector per original parent; repeated references, overlapping spans and alternate fragmentation need a separately reviewed partition policy.
- Compute Euclidean country-minus-US vectors, gaps, comparator/US/relative displacement and exact symmetric algebraic gap contributions in the declared frozen full-feature or retained-score space. The space kind is explicit; retained dimensions are not relabeled as full original text.
- Project only through a supplied fixed orthonormal linear basis. A missing, nonlinear, incompatible or nonorthogonal display is withheld without discarding a valid high-dimensional metric. US-centered and absolute coordinates are both returned, with the visible fraction of each squared gap.
- Keep the complete declared period skeleton. Only adjacent usable endpoints produce transitions. Missing US evidence produces unavailable comparisons, not zero, interpolation or carry-forward. US self-distance is zero only when observed.
- Keep uncertainty and sensitivity explicitly unavailable. No inferential tests, calibration, model fitting, holdout execution or empirical country-position claims occur.

`coverage.included` counts observations eligible under the source-selection rule, not necessarily observations in a usable profile: complete required genre support is an additional profile-level condition. Every profile's state and contribution list must be consulted. Inventory counts have the explicit unit `source_observation`; no independent-sample claim is made.

## APIs

`us_reference.py`: `build_us_reference(panel, receipt)`, `validate_result(result, panel, receipt)`, `adapt_w4(panel, annotations, plan, producer_receipt)`, `point_metrics()`, `transition_metrics()`, `select_comparisons()`.

`read_model.cjs`: `validateSyntheticSource()`, `validateFigureModel()`, `importReadModel()`, `pointMetrics()`, `transitionMetrics()`. Invalid import returns `model: null`, preventing stale read-model reuse. This is a Node research validator, not a browser mount or public loader.

`arithmetic.R`: independent base-R profile, weight, state, temporal-edge and metric oracle on fictional TSV tables. It is not a second authentication service. All operational consumers must use the source-bound validated sidecar.

`make_schema.py` deterministically builds `schema/us_relative.schema.json`, a Draft 2020-12 research sidecar, NOT an amendment to `un.parallel-analysis.v1`. Build it explicitly before using either validator; importing a numerical API does not generate files. Python and Node implement only the schema's documented closed subset and reject unsupported validation keywords. Tests cross-check against the independent `jsonschema` package when installed.

## Reproduce from repository root

```sh
python -m research.integration.w2_w4_w6.waggoner.make_schema
python -m research.integration.w2_w4_w6.waggoner.run_tests --require-complete --receipt /tmp/us-relative-receipt.json
python -m unittest research.integration.w2_w4_w6.test_w4_bridge -v
```

Use Python 3.11+, Node 22+, R 4.3+, and the existing `research/longitudinal/requirements.txt` for the native W4 adapter. Install `jsonschema` for the independent Draft 2020-12 check. The producer, validators and base-R arithmetic need no additional numerical fitting packages. No test downloads sources or models. Missing runtimes/dependencies produce explicit skips; `--require-complete` treats any skip as incomplete acceptance.

The existing coordinator W2/W4 evidence workflow runs the bridge test entry point, so this change is included in its native tests without altering workflow ownership or adding deployment triggers. Hosted workflow success must be tied to an exact commit; skipped parity tests are not passes.

## Integrity, numerical tolerances and limits

External synthetic receipts establish internal consistency only, not independent source authentication or permission. The supplied panel, country annotation ledger and adapter plan are separately bound; W4's original panel digest and representation fingerprint are retained. The sidecar uses documented `sha256/usref-wire-v1` typed bytes (null/boolean/string/list/object and normalized binary64 numbers) to avoid R/JavaScript/Python JSON decimal formatting differences. Original source metadata, offsets, hashes and transform bytes are exact; JavaScript replay uses relative/absolute `1e-10` tolerance only for independently recomputed floating arithmetic. This is not a statistical gate or a modification of frozen thresholds.

Limits: 20,000 source observations, 20,000 country-period cells, 256 periods, 256 country codes, 32 required genres, 2–1,024 metric dimensions and bounded identifiers. The Node JSON command-line input is capped at 32 MiB. These new sidecar limits do not extend the browser collector's limits. Private development and reserved dates are rejected; there is no corpus loader, networking, model fetch, email or publication permission.

## Acceptance boundary

At initial commit, implementation tests are authored but not yet claimed to pass. Exact-head results and any unresolved issues belong in the PR/acceptance receipt. Phase 2 still owns visual components, browser accessibility/export/cancellation QA and biplot diagnostics; Phase 3 owns independently approved real-source bindings; Phase 4 owns any release. Statistical holds and all 37 reserved transcripts remain unchanged.
