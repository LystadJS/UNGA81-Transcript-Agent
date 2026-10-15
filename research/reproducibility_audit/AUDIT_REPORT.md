# Independent reproducibility and security audit — engineering handoff

**Audit scope:** source-safe public repository metadata and synthetic validation controls only. **No private transcript bytes, withheld evaluation meetings, empirical vectors, owner annotations or release credentials were accessed.** No D1 O1–O5, frozen evaluation locks, production manifests or deployment files were modified. This record is an engineering candidate, **not** scientific or publication acceptance.

## Audited repository state

- Worker branch: `feat/independent-reproducibility-audit`; pull request [#71](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/71), draft and unmerged.
- `main` read during this continuation: `2c27536f6480718ae14ae95e04a38a30e5344a77`, later refreshed to `1af11061e3fa65d51b28d42a1b98bef250b6168b`. Main changed during audit, including coordinator PR #73. The worker did not rebase or alter other workers' files.
- Original worker PR head before this continuation: `096dfe1f63819a6bd6a56d9222d43c603bda548f`. Record the new final exact head in PR metadata when reviewing.
- Authoritative interchange JSON Schema Git blob: `3786a08eb6c4a7de7db2845138ffe4ae51f4b2c3`; research method catalog Git blob: `6aca560d961369fda7637869853e92366df86bde`. Both are pinned as **read-only upstream identities**.
- Newly generated `method_inventory.json` lists 30 registered backlog methods (29 declared synthetic kernels and M26 not implemented), 12 established daily adapters, declared runners and required gates. Declared kernel test status is inherited from the upstream registry, not independently rerun evidence.

## Newly executed local synthetic validation

Run in an isolated Python 3.13.5 environment, Node 22.16.0 available, `Rscript` unavailable, repository clone unavailable (DNS cannot resolve github.com). The local test candidate was authored from the connected GitHub metadata and pushed via the GitHub app; **these local runs do not count as exact-head CI execution of the final GitHub checkout**.

```sh
python3 -m unittest discover -s research/reproducibility_audit -p 'test_*.py' -v
python3 research/reproducibility_audit/run_qa.py --repo-root . --output /tmp/unga-repro-qa.json
```

- Local synthetic test suite: **63 attempted; 62 PASS; 0 FAIL; 1 SKIP**. The skipped test requires the upstream coordinator Schema file in an authenticated full checkout. Legacy `test_audit.py` has not been executed in this isolated candidate.
- Corrupt observation IDs, duplicate rows, wrong parent hashes, invalid spans, missing partial/failed fit denominators, wrong cluster labels, incompatible representation/source basis, zero-denominator diagnostics, reserved-date identities, evaluation source overlap and unapproved release fields are negative controls.
- An independent-process synthetic numerical replay ran twice with seed `271828`, with independent reference implementation, pinned fixture SHA256 `88ba2f60c77b87e71c30e4022d1c2ad90905f44454ee76ad7783cce1f5a260e0` and output SHA256 `1639ed5e207c3704860cf5190f3233198882bc190cead010905fbd6f4a290130`. The output is a **synthetic arithmetic fixture only**, not a replay of historical W1/W4 fits.
- Privacy negative controls for a fake transcript sentinel, fake private-key marker, cached-vector files, and JSON row-level source records were detected. A synthetic aggregate-only staging directory was also scanned clean. **Actual public Pages assets were not audited.**
- QA statuses deliberately report absent upstream schema, catalog checkout, original-source hashes, sealed evaluation identities and exact-head GitHub Actions as `NOT RUN`, not `PASS`. No proof of real release eligibility is inferred.

## Acceptance status matrix

| Requirement | Status | Evidence / blocker |
| --- | --- | --- |
| Exclusive path ownership | PASS on verified PR diff when checked; recheck after final head | Changes only in `research/reproducibility_audit/**` |
| Machine-readable method inventory | PASS (metadata enumeration) | Pin to catalog Git blob; downstream execution still NOT RUN |
| Synthetic provenance/relational controls | PASS (isolated synthetic subset) | Full authoritative schema test skipped locally |
| Original source/checksum authentication | NOT RUN | Private originals excluded from this worker's access |
| Longitudinal/evaluation source segregation | PASS synthetic controls; real NOT RUN | Sealed evaluation identity records unavailable |
| Deterministic synthetic numerical replay | PASS isolated runtime | Original W1/W4 model replay NOT RUN |
| Synthetic privacy sentinel controls | PASS isolated runtime | Complete Pages artifact scan NOT RUN |
| Frozen gate mutation check | PASS exact changed-path constraint (subject to final PR recheck) | No forbidden paths edited by this worker |
| Current-head CI and upstream regressions | NOT RUN | No applicable PR-head Actions workflows returned; Node/R full checkout unavailable |
| Human review | NOT RUN | No owner-validated decisions changed |
| Statistical calibration / source eligibility | NOT RUN | Distinct scientific prerequisites |
| Public release authorization | FAIL / WITHHELD | Owner/coordinator release gate remains closed |

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
