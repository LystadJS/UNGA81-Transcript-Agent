# Synthetic engineering validation and release gate

**Implementation:** feat/supervised-country-positions  
**Scope:** new files under research/supervised_country_positions only.  
**Decision:** ENGINEERING PROTOTYPE — empirical inference and public publication WITHHELD.

## Checks completed in this development session

| Check | Status | Evidence / limitation |
| --- | --- | --- |
| JavaScript syntax and logical fixture suite | **PASS (V8 harness)** | 17 checks ran against the committed source after loading CommonJS modules in a V8 adapter with mocked Node filesystem and cryptographic modules; all 17 completed without recorded failures. This is **not** native Node 22 execution and does not independently verify the mock hash against actual bytes. |
| Synthetic frame schema and source identities | **PASS (V8 harness)** | Unknown propositions, mismatched codebook version, forbidden real/publication flags, forged quotes and missing hash identities rejected. |
| Country × year × proposition accounting | **PASS (V8 harness)** | 72 fictional matrix cells; missing observations remain missing; collective and unverified observations excluded; duplicated source families do not receive duplicate votes; within-speech contradiction withheld. |
| Matched-proposition pair accounting | **PASS (V8 harness)** | Each included pair requires two shared substantive propositions, explicit agreement/disagreement counts and a common denominator; conditionals/descriptive positions excluded from edges. |
| Offline page script parsing | **PASS (V8 syntax)** | Both annotation and viewer inline scripts parsed. No remote script, stylesheet import, fetch request, or innerHTML assignment found in the inspected sources. |
| Original-source SHA-256 verification in Node | **NOT RUN natively** | The source code calls Node crypto on each entire synthetic parent text. The V8 test double checks the interface and rejection behavior, not cryptographic replay. |
| Native Node 22 regression suite | **NOT RUN** | Use the committed test_positions.cjs file; there is no dedicated workflow created under the currently coordinator-owned GitHub Actions namespace. |
| Python 3 private-packet tests | **NOT RUN** | Six standard-library tests committed in test_prepare_review.py: source offsets/hashes, sealed dates, private paths, draft integrity and label consistency. |
| Native R M12/M17 source and synthetic fitting tests | **NOT RUN** | Test file committed; requires R, glmnet and the original I6 research dependencies. No new real classifier fitted. |
| Actual desktop/mobile browser interaction | **NOT RUN** | Syntax/source review does not establish keyboard operation, responsive layout, export fidelity or source-link navigation in a browser. |
| Independent reviewer gold labels and calibration | **NOT APPLICABLE / NOT RUN** | No owner or other human policy stance labels were supplied or fabricated. |
| Held-out diplomatic source evaluation | **NOT RUN** | No sealed reserved meeting, private historical corpus, or actual national stance was inspected. |
| D1/publication website integration | **NOT APPLICABLE** | No daily adapter, O1–O5 change, browser loader, public manifest or mirrored website assets were changed. |

## How to reproduce locally

    node research/supervised_country_positions/test_positions.cjs
    python3 research/supervised_country_positions/test_prepare_review.py
    Rscript research/supervised_country_positions/test_m12_m17_adapter.R
    node research/supervised_country_positions/build_synthetic.cjs /tmp/fictional-positions.json

Then open annotation.html with a **private** source-reviewed packet or viewer.html with the **fictional** generated JSON. Keep all source text, review drafts, original bytes, private fitted models and real country-level results off public Git.

## Outstanding acceptance requirements

A coordinator must run native Node/Python/R tests and a genuine browser QA; compare base/head SHAs; verify source/fixture hashes; evaluate privacy and integration compatibility; and review the proposition codebook before any merge decision.

Empirical eligibility additionally requires independent source and role verification, completed and attributable human review, frozen train/calibration/test policy, model calibration and abstention, and examination of differing text modalities, missingness, source-group dependence and reference-actor sensitivity.

**Publication gate is unconditional in this branch:** only explicitly synthetic_engineering inputs are accepted by the numerical prototype, and both generated reports and original M12/M17 wrappers force publication_eligible=false. This report does not authorize weakening any existing source, review, held-out, or D1 gate.
