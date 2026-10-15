# Independent reproducibility and security audit — engineering handoff

**Audit scope:** source-safe public repository metadata and synthetic validation controls only. **No private transcript bytes, withheld evaluation meetings, empirical vectors, owner annotations or release credentials were accessed.** No D1 O1–O5, frozen evaluation locks, production manifests or deployment files were modified. This record is an engineering candidate, **not** scientific or publication acceptance.

## Audited repository state

- Worker branch: `feat/independent-reproducibility-audit`; pull request [#71](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/71), draft and unmerged.
- `main` read during this continuation: `2c27536f6480718ae14ae95e04a38a30e5344a77`, later refreshed to `1af11061e3fa65d51b28d42a1b98bef250b6168b`. Main changed during audit, including coordinator PR #73. The worker did not rebase or alter other workers' files.
- Original worker PR head before this continuation: `096dfe1f63819a6bd6a56d9222d43c603bda548f`. Record the new final exact head in PR metadata when reviewing.
- Authoritative interchange JSON Schema Git blob: `3786a08eb6c4a7de7db2845138ffe4ae51f4b2c3`; research method catalog Git blob: `6aca560d961369fda7637869853e92366df86bde`. Both are pinned as **read-only upstream identities**.
- Newly generated `method_inventory.json` lists 30 registered backlog methods (29 declared synthetic kernels and M26 not implemented), 12 established daily adapters, declared runners and required gates. Declared kernel test status is inherited from the upstream registry, not independently rerun evidence.

## Independent, source-exact engineering review — 15 October 2026

The reviewer fetched the PR code and coordinator contract through the authorized GitHub connector, reconstructed a **limited runnable source tree**, and independently checked Git blob identities. A **full Git repository checkout remains unavailable** because `git ls-remote https://github.com/LystadJS/UNGA81-Transcript-Agent.git HEAD` fails DNS resolution in this execution environment. This fact prevents claiming complete repository-wide or exact-head GitHub Actions acceptance. No substitute private source material was opened.

**Reviewed worker code head before documenting this review:** `1f8978b7af449e55d2a642d6a154f9c9e2de7b06`. The final PR head after this documentation-only commit must be rechecked separately. Latest verified `main`: `1af11061e3fa65d51b28d42a1b98bef250b6168b`.

### New executable tests and repair evidence

```sh
# In an offline local tree populated from authenticated GitHub file blobs:
python3 -m unittest discover -s research/reproducibility_audit -p 'test_*.py' -v
python3 research/reproducibility_audit/run_qa.py --repo-root . \
  --synthetic-envelope /tmp/unga71-envelope.json \
  --public-root /tmp/unga71-staging \
  --changed-path-list /tmp/unga71-changed-paths.txt \
  --output /tmp/unga71-final-qa.json
# Execute natively in a future full repository checkout:
node docs/parallel-work/validate-contract.cjs
```

- **Python 3.13.5, source-verified local tree: 86/86 tests PASS, 0 FAIL, 0 SKIP**. All ten runnable audit Python files plus the authoritative schema, catalog and inventory, 13 files total, were verified by `git hash-object` against GitHub. The legacy `test_audit.py` and previously skipped actual-coordinator-schema case are included in the 86.
- **Regression red-to-green:** five new tests proved the original comparability checker wrongly accepted changed model parameters, method/fit version, matching missing text hashes, duplicate observation identities or altered cohort definitions. Repaired `protocol.py` with explicit source, population, representation, fit-policy, model-parameter and producer identity checks. Three new security tests proved archives, escaped JSON and HTML-entity synthetic sentinels were previously missed; repaired `security.py` to fail closed on compressed assets and examine decoded JSON strings and markup.
- **Official coordinator interchange smoke tests:** the source-exact `validate-contract.cjs` was executed in a JavaScript V8 isolate using read-only fs/path/assert adapters against verified GitHub schema and original Markdown synthetic example. It reported **1 positive and 13 negative controls PASS**. **This is not a native Node process in a complete checkout**; that native command remains NOT RUN.
- **Two isolated synthetic numerical replays:** PASS with seed `271828`, Python stdlib only; fixture SHA256 `88ba2f60c77b87e71c30e4022d1c2ad90905f44454ee76ad7783cce1f5a260e0`, expected output SHA256 `1639ed5e207c3704860cf5190f3233198882bc190cead010905fbd6f4a290130`. Neither run is an original W1/W4 numerical fit.
- **Standalone QA receipt:** correct exit **3**, `engineering_acceptance:WITHHELD`, `publication_authorized:false`. Eight explicitly supplied synthetic checks **PASS** (schema, synthetic interchange, inventory, owned paths, replay, privacy, evaluation isolation, synthetic aggregate staging scan). Authenticated original source hashes, sealed evaluation identities and current-head Actions **NOT RUN**. The staging scan is **not** a full Pages/public-build privacy audit.
- **Runtime and resources:** Python `3.13.5`, Node `v22.16.0` available; no `Rscript`. Offline, single-thread synthetic arithmetic; replay has two independent child-process restarts each with ten-second timeout. No remote network, empirical fitting, source text or evaluation-set access.

### Engineering acceptance matrix — coordinator disposition

| Gate | Status | Evidence / blocker |
| --- | --- | --- |
| PR exclusive changed paths and frozen-file protection | PASS | GitHub exact changed filename listing: 13 worker-owned paths, no shared files, no symlinks in verified tree |
| Source-exact synthetic harness regressions | PASS | 86 tests, zero skips/failures, code + schema blob verification |
| Pinned authoritative v1 schema, relational and denominator negative controls | PASS for audited synthetic fixtures | Actual coordinator schema and clean + corrupted interchange fixtures checked; does not certify all empirical adapters |
| Method inventory and exact registered source catalog | PASS | 30 methods, 29 declared synthetic kernels, catalog blob matched, claims inherited |
| Reproducible synthetic arithmetic and replay restart | PASS | Deterministic fixture/seed, independent reference and output SHA |
| Synthetic privacy and evaluation leakage negative controls | PASS | Escaped/archived sentinels and identity overlaps detected |
| Native upstream Node and complete repository regressions | NOT RUN | Cannot obtain full repository checkout in execution environment; V8-adapted upstream smoke tests are partial evidence |
| Applicable GitHub Actions against current PR head | NOT RUN | No workflow runs, combined statuses or check-runs reported at validated head; workflow is coordinator-owned |
| Complete public build privacy/manifest scan | NOT RUN | Only explicit synthetic aggregate staging tested |
| Original source-byte/source-selection authentication | NOT RUN | Original private bytes excluded from authorized synthetic audit |
| Sealed evaluation identity isolation | NOT RUN | Evaluation identities deliberately not opened |
| Statistical calibration and empirical source eligibility | NOT RUN | Separate frozen research gates remain unmet/unassessed |
| Human review of empirical interpretation | NOT RUN | No owner-reviewed scientific or publication decision |
| Publication authorization | FAIL / WITHHELD | Explicit publication lock remains unchanged |
| **Full PR engineering acceptance** | **WITHHELD (NOT RUN required gates)** | Exact-head Actions, native upstream regressions, complete checkout and coordinator integration review incomplete |

**Coordinator decision:** recognize the 86/86 source-exact synthetic audit controls as **engineering test evidence only**. Do **not** mark the entire PR accepted or merge/deploy until remaining applicable engineering gates are independently executed against the final GitHub head. Neither clean synthetic testing nor the absence of GitHub workflow failures proves CI success.

## Findings for the integration coordinator

1. **High — PR #25:** Its latest recorded Actions run `37816285803` concluded **failure**. Preserve draft and resolve source acquisition/secure intake failures before accepting historical coverage.
2. **High — PR #68:** Synthetic/interchange Actions for the reviewed head concluded success, but temporal-correlation recovery remained **0/18** in the previous W4 diagnostic. Passing a build does not establish calibrated longitudinal inference. Require independently seeded development/holdout recovery, nuisance estimation and positivity/selection sensitivity.
3. **High — PR #74:** Its own metadata report documents substantial genre overlap, absent verified oral-delivery language, multiple original-PV candidates and unestimated inclusion probabilities. Current recorded metadata-only workflows passed, but none of these facts authorizes a substantive longitudinal fit. Treat registry/source-quality claims as worker-reported until independently checked against approved metadata receipts.
4. **High — PR #66:** A declared locally executable encoder scaffold lacks verified checkpoint inference, tokenizer, exact dependency pins and cross-representation negative controls. Do not treat deterministic placeholder-vector tests as semantic model evaluation.
5. **High — PR #67:** Null-calibration primitives do not yet independently establish the nuisance-preserving null distribution, fit attempt denominators, independent holdout calibration or null-significance claims.
6. **Medium — PR #69:** Current-head latent CI is not real Chromium/browser QA. Confirm accessibility, denominators, graphical views and accepted interchange adapter, then recheck after any head changes.
7. **Medium — PR #70:** Readout templates require exact-source/offset verification and owner interpretation controls; standalone synthetic tests and upstream CI should be executed.
8. **Medium — PR #64:** Historical comparability tests have no exact-head CI; private original/document selection cannot be inferred from synthetically valid metadata.
9. **Coordinator-only — PR #72:** C5 synthetic release metadata changes shared `site/release.json`. Keep publication authorization distinct from a successful latent-comparison check and recheck live asset/mirror identity before any deployment.

These are **triage findings** from exact PR metadata, changed paths, workflow conclusions and self-reported PR limitations; no claim of independent private-source scientific replication or complete code-level audit of other PRs.

## Prioritized next executable repairs

1. Run `node docs/parallel-work/validate-contract.cjs` and `python3 -m unittest discover -s research/reproducibility_audit -p 'test_*.py' -v` against **the actual current PR head** with the pinned upstream schema present. Resolve any normative-schema discrepancy rather than altering shared contracts.
2. Add coordinator-owned, path-limited CI for this worker's complete synthetic suite (worker ownership forbids editing `.github/workflows/**`), then capture exact run IDs, jobs, conclusions and environment.
3. Conduct a documented privacy scan of an approved actual public build, excluding private inputs, and compare staged/public release manifests. **No worker deployment or Pages changes.**
4. Use authenticated, authorized source metadata only to verify hash basis, source-family isolation and known evaluation identities. If sealed/held-out population is not authorized for audit, explicitly retain `NOT RUN` and withhold scientific eligibility.
5. Require separately documented coordinator human review and publication authorization; do not merge draft branches solely on synthetically clean checks.

**Disposition:** engineering draft / no merge / no deployment / no private transcript retrieval.

## Coordinator exact-head CI reconciliation — 2026-10-15

Full-checkout independent native regression PASS on coordinator effective-tree commit `15b3087f503f6ba774ea34ecf3f459479453aef9`, GitHub Actions run `38753795947`: Python audit 86/86 and applicable Node W1/P2/W4/source/interchange regressions PASS. Coordinator-owned exact-head workflow merged to main in PR #79 (`4a913fd0f36dbb2970fc7b08facebf64e66e3bf1`). This documentation-only change triggers fresh PR-head CI and **must not** be reported as exact-head PASS until the new run is inspected. No scientific, source, privacy, evaluation or publication restriction is changed.

## Coordinator full public-build privacy audit — 2026-10-15

**New engineering evidence; no empirical release approval.** The actual accepted static build was generated with `python3 tools/build_pages.py` in a clean GitHub-hosted full repository checkout, based on main `93b17c8779d959f5dd5559adb7f56381210f2f89` and original worker source blobs. Exact current worker source is unchanged in the coordinator-only effective tree except the specifically documented scanner repair. The early scanner identified five row-shaped observations in `parallel/w05-browser/experimental/method-lab/fixtures/synthetic-contract.json`; no claim was made that these were private source observations. The fix permits only the exact SHA-256 `c1d307ef967361d91377c0e2faf4600814fb9ab41931ecc781c733e18571c515` at that explicit fixture path; modified or relocated copies remain rejected. No generic source-record exemption or scientific gate was changed.

**PASS** [Actions run #38764067792](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38764067792), job `116522577328`, coordinator full-build effective tree `0eaee26dc548872e1e63a5974e690e5db22b7c27`: 89 Python unit/negative-control tests passed (0 failed); built accepted static assets; scanner covered **154 files / 8,543,016 bytes**, **0 findings**. Canonical SHA-256 of sorted filename+byte-length+file-digest inventory: `1be69e17bd11b3483d2d61c8be639899de0611a28f56e207126d5e123414bda2`. Public build generator reported 163 files/dirs (the scanner's 154 count counts regular files only). This validates the scanner's enumerated threat signatures and exact staged artifact inventory; it does **not** certify that unknown private content could never evade static signatures.

**PASS** worker-head GitHub Actions native regression [run #38763945202](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38763945202) against `0649858140ffe842b0c774eb289ac054e2a4fd32`. The earlier coordinator full-checkout test `38753795947` and exact PR-head `38754190654` also passed. Re-run exact-head CI after this documentation update before any merge.

**WITHHELD:** original source/private byte reauthentication, sealed 37-meeting holdout execution, statistical/null calibration, human review and D1 O1–O5 publication. This module makes no empirical fit or delivery change; the test branch and scanner receipt are engineering-only.
