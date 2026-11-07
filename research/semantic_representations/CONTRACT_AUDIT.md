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


## October 15, 09:24 EDT continuation — exact-module validation

- Direct git checkout attempt: `git ls-remote https://github.com/LystadJS/UNGA81-Transcript-Agent.git HEAD` → `Could not resolve host: github.com`. The local execution environment has Python 3.13.5 / Node v22.16.0, but no complete source checkout. GitHub connector verified current branch and base; there is no remote shell/workflow-dispatch facility in the connector.
- **99/99 PASS**, freshly executed via `python3 -m unittest discover -q -p 'test_*.py'`; `python3 -m compileall -q .` PASS. The new `interchange.py` Git blob `329c8312cf1dec46c85d146d33cc34a0c8e18542` and new `test_interchange_v1_compat.py` Git blob `4857f91c0606fa6d10d382992a6e44ed7f02c69a` match locally tested bytes. The older `test_pipeline.py` file still differs in bytes from the remote head: **a complete exact-head checkout/run remains NOT VERIFIED**.
- Source-bound synthetic CLI with 16/16 synthetic eligible observations ran twice in separate processes against the same private cache; first attempt `cache_hits=0,cache_misses=16`; replay `cache_hits=16,cache_misses=0`. The output reports differ ONLY in expected cache and attempt accounting; representation observations and neighborhoods replay consistently. Initial smoke-script failure stemmed from using a pre-created output file; the CLI correctly refuses output overwrite.
- **Integration defect fixed**: Official v1 permits `upstream.source_sha256:null` or `selection_sha256:null` when `missing_reason` is populated, but this reader previously rejected both before checking the explicit reason. Now metadata-only read accepts declared unknown provenance but malformed non-null digests and missing reasons fail closed. Comparisons requiring source alignment remain blocked by the stricter source-bound engine. Backward-compatible `1.x.y` version format now follows the official schema, while other major versions fail.
- Official contract Node test and upstream browser/numerical/corpus/source/reviewed suites: **NOT RUN**. No complete checkout; do not treat local Python pass as their substitute. For the new head, GitHub workflow runs and combined status contexts are empty.
- No empirical ONNX inference, official original-byte source access or reserved evaluation access. No edits outside this namespace, no merge, no deployment.

### Exact-head coordinator execution commands (still required)

```sh
node docs/parallel-work/validate-contract.cjs
node tools/test_browser_clusters.cjs
node tools/test_passage_corpus.cjs
node research/validation_framework/tests/test_schema.cjs
node research/validation_framework/tests/test_framework.cjs
python3 tools/test_reviewed_loader.py
cd research/semantic_representations
python3 -m unittest discover -v -p 'test_*.py'
python3 -m compileall -q .
```

Run any additional applicable latent/numerical tests after examining latest `main` and the current package scripts. The named commands above have not been executed in this environment. Record exact SHA and CI logs for each.


## October 15, 09:41 EDT — independent full-checkout attempt

**Requested exact-head upstream execution: BLOCKED, not PASS.**

- GitHub exact head prior to this documentation update: `dc6e0ebb79dd7498f6adbb13b326fe7c91bc8e62`; `main`: `1af11061e3fa65d51b28d42a1b98bef250b6168b`; 24 ahead/4 behind; all 19 paths within this exclusive namespace.
- Direct runtime inspection: `git 2.47.3`, `node v22.16.0`, `Python 3.13.5`, root privileges. `git ls-remote https://github.com/LystadJS/UNGA81-Transcript-Agent.git HEAD` **FAIL**, `Could not resolve host: github.com`. There is no full checkout, no `docs/parallel-work/validate-contract.cjs` in the workspace, and no authorized workflow dispatch surface.
- Independently ran `cd /mnt/data/semantic_work/research/semantic_representations && python3 -m unittest discover -q -p 'test_*.py'`: **99 tests PASS** in 1.812 seconds, `python3 -m compileall -q .`: **PASS**.
- **Git-blob source identity check** against the current PR: ten Python modules and `test_interchange_v1_compat.py` match GitHub byte-for-byte. However, local `test_pipeline.py` Git blob `5f7ba60ce263ff347b99e9eb1cebd6753520397f` differs from pushed `b991b62365b1a18fb33b956d9d8e8dcf7fc91e8b`; local `official_v1_synthetic.json` Git blob `58b1c6648c15de4a5085ff626fb5964b9bbd1a8e` differs from pushed `d22dad05461dc34e1a41aa7a7c0c7dd6528da194`. Therefore this is **local module execution with an inexact fixture/test pair**, **NOT a full exact-head test pass**.
- GitHub Actions runs and commit status contexts for the inspected head: **none returned**. This means **NOT RUN / no evidence**, not success.
- No upstream Node/browser/W1/corpus/reviewed tests could execute because their files and dependencies were unavailable. Original source authentication, semantic ONNX checkpoint, and empirical comparisons remain withheld.

**Coordinator completion condition:** provide a trusted execution-capable full checkout or CI runner with repository access; verify `git rev-parse HEAD` equals the exact current PR head; run the official Node contract validator, browser/latent/numerical, W1/source/corpus/reviewed suites, and exact-head Python tests. Capture exit codes, logs, dependency versions, run URLs/IDs, and compare `main` again. Keep PR draft and unmerged in the meantime.


## October 15, 09:50 EDT — renewed execution attempt

- Exact implementation head before this record: `5dc74a10d4094c8518ca5b48a87bb2994c5ab6bc`; latest checked `main` `1af11061e3fa65d51b28d42a1b98bef250b6168b`. PR branch 25 ahead, 4 behind. GitHub Actions PR-head runs: none returned.
- Full checkout command `git ls-remote https://github.com/LystadJS/UNGA81-Transcript-Agent.git HEAD` failed with `Could not resolve host: github.com` in this container. No project root checkout exists, so the official upstream Node suites cannot execute; **NOT RUN**, not PASS. This is external execution access, not a demonstrated upstream failure.
- **Fresh execution** in the available partial source tree, Python 3.13.5: `python3 -m unittest discover -v -p 'test_*.py'`: 99 PASS, 0 FAIL, 0 ERROR, 1.863 sec; `python3 -m compileall -q .`: PASS (exit 0).
- Git blob verification: `interchange.py` local and remote `329c8312cf1dec46c85d146d33cc34a0c8e18542`; `test_interchange_v1_compat.py` local and remote `4857f91c0606fa6d10d382992a6e44ed7f02c69a`. **Two discrepancies persist:** local `test_pipeline.py` `5f7ba60ce263ff347b99e9eb1cebd6753520397f` versus remote `b991b62365b1a18fb33b956d9d8e8dcf7fc91e8b`; local `official_v1_synthetic.json` `58b1c6648c15de4a5085ff626fb5964b9bbd1a8e` versus remote `d22dad05461dc34e1a41aa7a7c0c7dd6528da194`. The local 99 PASS cannot be promoted to exact-head suite PASS.
- No eligible ownership-local regression fix was identified from an upstream test because upstream test execution was impossible. Do not merge, deploy, access reserved sources, or alter gates.

**Next coordinator action:** provision a trusted full checkout/CI runner, verify the PR's exact SHA with `git rev-parse HEAD`, execute the official Node schema validator and named upstream suites from the prior section, reproduce Python tests from actual PR bytes, and attach run IDs, logs and exit statuses. Reconcile stale branch base only after coordinator-owned integration approval.
