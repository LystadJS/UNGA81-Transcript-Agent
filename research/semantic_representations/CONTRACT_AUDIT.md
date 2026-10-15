# PR #66 — interchange and regression integration audit (2026-10-15)

**Disposition: engineering-only DRAFT; DO NOT MERGE.**

## Exact reviewed sources

- Latest inspected main: `1af11061e3fa65d51b28d42a1b98bef250b6168b`.
- Official schema: `docs/parallel-work/interchange-v1.schema.json`, blob `3786a08eb6c4a7de7db2845138ffe4ae51f4b2c3`.
- Official normative contract: `docs/parallel-work/INTERCHANGE_V1.md`, blob `b7b78780605988305fc245e1136c4c671ff7a80e`.
- Official synthetic validator: `docs/parallel-work/validate-contract.cjs`, blob `345682f607ecba7633cdb35bcf4e7fa965d03d10`.
- Coordinator PR acceptance: `docs/parallel-work/PR_ACCEPTANCE.md`, blob `5538f976aceed9fd8853a098ad7c0eda17da70fc`.
- Paths changed in this PR: exclusively `research/semantic_representations/**`; no D1, W1–W7, browser loader, frozen source or publication edit.

## Newly executed

1. Python 3.13 local synthetic suite: `cd research/semantic_representations && python3 -m unittest discover -v -p 'test_*.py'`: **92 PASS / 0 failed / 0 errors**, including 9 new official-example / relational refusal tests; local code in `interchange.py` has identical Git blob SHA as pushed file `37e0279319cf0e5d23abeeeb6d2ca78ba42d409b`. The remotely submitted test file has the same named test cases and 85 test methods; its byte identity differs from the local test file, so full **exact-head test execution is NOT VERIFIED**.
2. `python3 -m compileall -q .`: PASS locally.
3. Coordinator's normative synthetic JSON mapping example: **PASS** in the updated Python read-only consumer, 1 observation/1 model. Fixture was vendored under this namespace without source text.
4. Official GitHub schema parsed successfully and a schema-driven structural check against its original JSON example: **PASS**. Four of five mutation examples rejected structurally; setting `publication_eligible:true` is a **relational** violation rather than a JSON-schema constraint and is rejected by the Python consumer. This is **not** a claim that the original Node validator ran.
5. Read-only consumer newly refuses unverified speech IDs, missing parent hashes, missing/unavailable reasons, reserved October 5–6 development dates, orphan evidence/diagnostics, inconsistent eligible populations, unnormalized soft memberships, missing model coverage, and mismatched failed-fit denominators.
6. Initial overstrict inventory >= passage-count assertion was removed after a local regression: meeting/source inventory and passage observations have different denominators. This confirms the normative contract's intended distinction.
7. Live GitHub commit check contexts / Actions workflow runs for previous head were both empty; no acceptance CI evidence.

## Regression blockers / not run

- **Official Node validator and shared upstream regression suites:** NOT RUN. The execution environment cannot resolve `github.com` for a fresh repository checkout, and GitHub connector access does not provide a remote shell or workflow dispatch. Current `parallel-contract.yml` only triggers on coordinator-owned `docs/parallel-work/**` changes, not this worker's PR paths. Do not infer green CI from an empty list of runs.
- **Authoritative complete schema validation of every PR-produced read model:** NOT RUN. The official validator checks its own synthetic example; this W8-adjacent research consumer does not register as an authorized W1–W7 producer.
- **Empirical checkpoint / original-source / matched saved lexical inference:** NOT RUN; authenticated private material unavailable. All 37 October 5–6 reserved meetings unopened; D1 O1–O5 and release gates unchanged.
- **Full package-wheel hash reproductions** and cross-host numerical replay: NOT RUN.

## Coordinator-only next steps

1. Check out **exact PR head** and latest `main` in CI-capable trusted environment; run:
   ```sh
   node docs/parallel-work/validate-contract.cjs
   cd research/semantic_representations
   python3 -m unittest discover -v -p 'test_*.py'
   python3 -m compileall -q .
   ```
2. Run relevant existing browser/latent/corpus/source/reviewed-unit regressions, inspect every result and log by head SHA.
3. Validate official schema and relational invariants on synthetic envelopes using the original Node validator; do not claim the copied fixture substitutes for a full integration contract test.
4. Keep PR draft until coordinator confirms exact-head acceptance. No public deployment, merge, private source publication or change to official W1–W7 schema is authorized.
