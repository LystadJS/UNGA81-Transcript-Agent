# Independent engineering review — PR #89 (15 October 2026)

**Decision:** PASS for a *synthetic-only, nonpublishing coordinator adapter* at `e25fe722b53da2a6f9cad9b44ec7a067bc45fa95`, subject to the continuing holds below. **Do not merge, deploy, open reserved transcripts, use real sources or alter D1.**

## Source of truth and reconciliation

- Review target: [PR #89](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/89), branch `coord/evidence-first-readout-adapter`. Original independently inspected head `9d47612d47e7ec42faa7513799c7f5582dbc9d3d`; companion renderer PR #70 `028e3d26f707401cbff498593ab27f64e2cc072a` remains draft/unmerged.
- Original one-commit `main` divergence: `691f13bb53232f72a40461855c8e08a78b21befe` → `5f0a872cff0899819b21326e6c18b7af794556c5`; it changed **only** `docs/parallel-work/COORDINATOR_INTEGRATION_LEDGER_2026-10-15.md`, with no adapter/interchange/source-contract conflict. Reconciled by non-force two-parent commit `e53bed9a7c692967fd3757bf6d5ff644c10a90d6`, preserving the exact latest ledger. Any subsequent coordinator ledger-only main movement must be tracked separately; it does not retroactively invalidate exact-head synthetic evidence.
- Changed PR paths: coordinator-only `research/integration/diplomatic_readouts/**` plus the uniquely named read-only path-scoped workflow `.github/workflows/coord-evidence-readout-adapter.yml`. No worker namespace, D1 producer, UI, Outlook, source files, original checksum, release manifest or website changes.
- Existing `AGENTS.md`, `PR_ACCEPTANCE.md`, `INTERCHANGE_V1.md` and PR #70 receipt/stance requirements remain authoritative. Source-data values are never inferred from country names, cluster numbers, display distances or speaker registry affiliations.

## Independent review findings and remediation

Three source/analytical join gaps were fixed entirely within the coordinator-owned adapter:

1. `coverage.unavailable_sources` must equal the independently enumerated unavailable/nonavailable observational rows; mismatched declarations now fail closed.
2. Duplicate supporting/contrary observation identities within a finding are refused to avoid artificial evidence repetition.
3. An exploratory model interpretation cannot use a `not_fitted` observation as support or contrary evidence. Missing and failed fits remain explicit, not silent assigned observations.

The new `PRIVATE_SOURCE_AUTHORIZATION.md`, `private_source_contract.py`, `private_source_contract.v0.schema.json` and ten synthetic unit tests supply **only a prospective metadata-only design preview** with all 13 private/owner/statistical/D1 gates fixed to `NOT_RUN`. The preview cannot approve access, publish, change reserved holdout status, issue a `ReviewDecision` or impersonate an authenticated source custodian. This is not implementation of real-source authorization.

## Exact-head hosted evidence

| Gate | Status and reproducible evidence |
| --- | --- |
| **Branch SHA and ownership** | **PASS.** [PR #89](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/89) exact head `e25fe722b53da2a6f9cad9b44ec7a067bc45fa95` when these checks ran; 12 coordinator-exclusive changed paths. |
| **Official interchange and source relational checks** | **PASS**, native `node docs/parallel-work/validate-contract.cjs`, `node research/validation_framework/tests/test_schema.cjs`, `node research/validation_framework/tests/test_framework.cjs`; tests include fixed v1 identity, exclusions, failed fits, source/selection hash basis. |
| **Consumer regressions** | **PASS**, `node tools/test_passage_corpus.cjs` and `node tools/test_latent.cjs`, including 24 existing reported latent checks. |
| **Readout/adapter security** | **PASS**, `python3 -m unittest discover -s research/integration/diplomatic_readouts/tests -v`: **43/43** tests, including three new source/fit regressions and ten private-authority refusal controls. |
| **Independent renderer dependency** | **PASS**, exact PR #70 source checked out read-only at `028e3d2`; `python3 -m unittest discover -s pr70/research/diplomatic_readouts/tests -v`: **46/46** tests. Not vendored or changed by this PR. |
| **Deterministic export/privacy** | **PASS**, five synthetic scenario cases generated twice to distinct temporary directories, byte-identical; manifest `7d9e3d3303cb00eb3f088a3260e58c18cc2164ffabb20e8793e32124f1f75ffb`. No original bytes, private rows or network-source fetch exported. |
| **Native W1→W2 input** | **PASS**, `node research/integration/w1_w2/make-synthetic.cjs` and independent adapter v1 validation of generated W1 source/fit ledgers (**24 eligible**). *Passing v1 metadata is not private-source authentication or statistical permission*. |
| **PR-head GitHub Actions** | **PASS**: branch [#38771260689](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38771260689) and PR [#38771269985](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38771269985), both completed successful at `e25fe722...`. Job PR `116547396444`. |
| **Original bytes from real UN sources / actual private registry** | **NOT RUN / WITHHELD.** Synthetic sources only. |
| **Human reviewer country-stance labels, null calibration, dependence and representational eligibility** | **NOT RUN / WITHHELD.** No inference or foreign-policy position claim. |
| **D1 O1–O5, R/Shiny, Outlook, real browser, email, publishing** | **NOT APPLICABLE for this isolated code; WITHHELD for future integration.** No changes to these surfaces. |
| **37 reserved Oct 5–6 texts / original review decisions** | **NOT ACCESSED/UNCHANGED** in PR source or CI; no permission requested. |

All test runs use GitHub Ubuntu, Node 22 and Python 3.13; `jsonschema` is development-only and pinned by `requirements-dev.txt`. The readout runtime itself remains standard-library only.

## Limitations and remaining gates

- `UpstreamValidation` and source-byte hashes are **consistency receipts**, not signed proof of original UN provenance, review, privacy clearance or independent statistical validity. The bridge refuses real/development source splits by design. Real private access requires a distinct custodian-backed, revocable authentication and rights policy on an approved private host.
- The synthetic input contract's `parent_text_sha256` is modeled as equal to the decoded observation's text hash. Genuine full-parent/child-passage linkage can differ and **must not be silently admitted**; require source/parent transformation identity and independently audited offsets before real-source extension.
- The adapter neither issues reviewer/stance decisions nor provides an accepted null/dependence test. No synthetic success is evidence of policy agreement, coordination or diplomatic realignment. Unavailable sources are unknown, not negative issue mentions.
- Coordinator/owner must decide whether and when to merge the code; **this ledger is engineering review, not merge or release authorization**. PR #89 and PR #70 stay unmerged. The new private-source proposal is deliberately unusable as a public or operational authorization token.


## Second coordinator-only main refresh

While acceptance checks were running, `main` advanced again from `5f0a872cff0899819b21326e6c18b7af794556c5` to `da4ab9ed11dba3693d11aa12f5333963b1b85478`, changing only the same coordinator integration ledger (nine new lines). A second non-forced two-parent reconciliation commit `aaa0dc9107b852f168359bf1a976762c304052a0` retained this exact latest ledger and all PR #89 implementation bytes. This is no source-contract or publication-gate change. Rerun exact-head synthetic acceptance against the final documentation head; do not infer source authorization from merger ancestry.

## Next executable task

Independent coordinator can inspect latest effective PR #89 merge tree and required CI checks, then design the future **private-host-only** custodian-signed source registry and reviewer-decision verification without reading reserved texts. A separate, explicitly authorized integration PR would be required to connect real accepted sources, R/Shiny/Outlook or D1 publication; revalidate original bytes, parent/child offsets, population and all O1–O5 gates at that time. No automatic merge or publication follows this record.
