# Final validation — hierarchical clustering only

**Release 2.4.0-d1-hc-only.** Completed source-backed R implementation of **M07 only**, starting from the complete v2.3.0 D1-I2 release. No PAM adapter is added or executed. This is an implemented audit capability, not empirical approval to publish clusters or a complete 42-model system.

## Actual runtime and executed checks

R **4.6.1** (2026-06-24), Matrix **1.7-5**, cluster **2.1-8.2**, Linux, C.UTF-8. New numerical calculations ran in the real R packages. The inherited I/O/MIME workflow used explicit `--minimal=true`; its production third-party package paths and live services were not tested here.

| Check | Actual final result |
|---|---|
| R syntax | **39 shipped R scripts parsed successfully** |
| Existing regression suite | **85 tests; 0 failures** |
| D1 foundation suite | **94 tests; 0 failures** |
| I2 feature/projection suite | **101 tests; 0 failures** |
| New hierarchical suite | **59 tests; 0 failures** |
| Combined final suites | **339 tests; 0 failures** |
| Hierarchical-only source CLI | Executed successfully; original M02 bytes unchanged |
| Integrated daily replay | Executed successfully; valid EML and complete audit |
| Country / frozen-term support | **39 countries; 3,448 frozen terms** |
| Candidate grid | **15** linkage/k combinations retained |
| Roster subsamples | **100** subsets, 31 of 39 countries without replacement |
| Candidate–replicate accounting | **1,500/1,500 executed**, no missing or duplicate planned records |
| Source and numerical screens | **13** M07 checks; all retained |
| All-method accounting | **42** method records; **133** prerequisite records |
| Implemented adapters | M01, M02, M05, M06, M07; **37** others not implemented |
| M07 / M09 terminal status | **withheld_quality / not_implemented** |
| Original example files | **9/9** source/example files byte-identical to parent |
| Frozen reference preservation | Complete reference object, vocabulary and sparse statement/country matrices identical to parent |
| Reader-facing email | Exactly **5** analytical sections, **39** countries, **5** regional headings |
| Fixed topics | Iran, Cuba, Ukraine, AI retained in order |
| MIME | 1 HTML body, 1 plaintext body, 1 inline seal; all CIDs resolved, no parser defects, X-Unsent: 1 |
| Audit figures | All **6** standalone R figures executed; hierarchy never embedded in email |
| Archived rebuild | **10/10** EML/HTML/plaintext/PNG outputs byte-identical |
| State during rebuild | **575** history/model/cache file hashes unchanged |
| Archive verification | Every file in all three completed run manifests read and hashed |
| Browser layouts | Chromium **390, 720, 1280, 1600 px**; no horizontal overflow, 39 country sections, 5 slots, loaded seal |
| Operational effects | No email, API call, task installation, GitHub write, or credentials included |

The actual inherited regression script contains **85** tests; previous conversational totals of 87 are not reused. Counts above come from executed final logs, not old release prose.

## Actual source result: retained for audit, not publication

The highest-silhouette average-linkage audit cut is **k=2**, with group sizes **38 and 1**. None of the predeclared average-linkage cuts k=2–6 passes the minimum-size / maximum-share screen. A complete or Ward alternative was not substituted to manufacture a qualified result.

| Diagnostic | Observed | Predeclared engineering screen |
|---|---:|---:|
| Mean silhouette | **0.0439686785** | >=0.15 |
| Mean subset adjusted Rand | **0.573** | >=0.75 |
| Minimum group size | **1** | >=3 |
| Largest group fraction | **38/39** | <=0.85 |
| Large-group mean subset Jaccard | **0.9790322581** | >=0.75 for every group |
| Singleton evaluability | **0/100** | >=80% for every group |

The singleton Jaccard is **undefined**, not zero or perfectly stable. It is exported as missing and rendered “Not evaluable.” The large-group overlap does not compensate for the singleton or weak separation. The replay also fails independent provenance, declared-language/genre and source-flag screens. **8 of 13 checks fail.** No threshold was lowered after seeing the source results.

The subsamples assess **conditional sensitivity to deleting countries from this roster**, with fixed vocabulary, IDF and candidate k. They are not confidence intervals, independent-country sampling evidence, calibrated semantic validity, policy-position measurements or proof of geopolitical blocs. M07 remains audit-only even if every engineering screen passes in another dataset; it has no publication producer in this release.

## Reproducibility details

`hierarchical_only.R` consumed the **exact prior M02 artifact** and independently recomputed/validated its hierarchical result. It did not collect sources, refit vocabulary/IDF, or fit PCA/PCoA/PAM. Separately, the integrated replay reused the same frozen reference and features and produced the email plus audit.

`rebuild.R` checked the completed source-run manifest and generation-code hashes, reused its archived model artifacts, independently recomputed numerical proofs and actually reran all six figure scripts. EML, both HTML variants, plaintext and all six audit PNGs were byte-identical. The inherited 155 summary points and their source references remain unchanged; no fresh semantic review or human-gold promotion occurred.

After those checks, active history/model/cache directories were relocated byte-for-byte to `examples/hhc`, `examples/mhc`, and `examples/chc`. The active directories ship empty. `reference_relocation.json` records preservation. Historical replay commits from earlier incomplete attempts are preserved rather than erased; acquisition does not imply successful email publication.

## Corrected development failures

Earlier test-harness syntax/count errors and the proof comparison's JSON integer/double representation mismatch were corrected before final passes. The figure now explicitly loads the Matrix namespace before inspecting a sparse object. End-to-end tests exposed an undefined diagnostic passed directly to strict HTML escaping; the rendering layer now displays **Not evaluable**, while numerical missingness and failed gates remain unchanged. A regression test covers this case. The initial independent plaintext check expected internal identifiers instead of the deliberately reader-facing numbered headings; the harness was corrected, not the email.

Failed/interrupted runs are not counted as delivered. Their bounded logs and exclusion records are retained under `validation/incidents/`; bulky obsolete working fixtures are not included in the release. No source text, label or numerical threshold was edited to create a passing source result.

## Evidence files

- `regression_tests.log`, `foundation_tests.log`, `i2_tests.log`, `hc_tests_final.log` and matching machine-readable test results.
- `standalone_final.log`, `integration_final.log`, `rebuild_final.log`, each with a zero exit receipt.
- `frozen_preservation.json`: exact parent reference/vocabulary/matrix comparisons and R parsing count.
- `independent_final_checks.json`: MIME, source, country/slot, M07/M09 and replicate checks.
- `reproduction_and_state.json`, `state_before_rebuild.json`: exact output hashes, figure rerun records, state-preservation checks and manifest verification.
- `browser_checks.json`, `render_checks/`: independently rendered browser checks.
- `hierarchical_source_audit/`: complete standalone M07 run, source-bound artifact and diagnostic CSVs.

## Explicit limitations

No native Microsoft Outlook rendering, Windows PowerShell/DPAPI/Task Scheduler execution, live UN/OpenAI request, third-party package installation/renv restoration, or normal JSON/HTTP package-backed I/O path was tested. Browser and independent MIME checks used development Python tools; **Python is not shipped or required by the daily workflow**. No large-corpus memory benchmark, cross-platform byte-identity guarantee, fresh labeling or semantic validation is claimed. The supplied frozen reference enforces its R/Matrix/tokenizer environment; build a new local reference rather than disabling that safeguard on another platform.

The RDS store retains the existing single-writer/integrity contract, not a new database durability guarantee. Only load trusted archives. Preserve the full release and its data/model archives for reproduction.
