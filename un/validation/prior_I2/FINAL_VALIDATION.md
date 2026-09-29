# Final validation — 2.3.0-d1-i2

**Result:** frozen TF-IDF, PCA, PCoA and the conditional O3 display boundary are implemented and executed. **The 39-country source map is withheld**, not published. Four of 42 analytical adapters are implemented; 38 remain unimplemented. No claim of a complete or empirically validated 42-model stack is made.

## Actual execution environment

R 4.6.1 (2026-06-24), Matrix 1.7-5 (packageVersion normalizes to 1.7.5), Linux/Debian 13, C.UTF-8, cairo PNG. All new numerical adapters use actual Matrix/stats code. The inherited source/JSON/MIME workflow was tested in explicit `--minimal=true` mode. That flag does not replace Matrix/PCA/PCoA with a mock; it selects the existing offline I/O adapters. See recorded sessionInfo files.

## Passed acceptance checks

| Check | Observed result |
|---|---|
| Parsing | **34 shipped R scripts parsed successfully**, including retained D1 design scripts |
| Legacy regression suite | **87 tests, 0 failures** |
| D1 foundation regression suite | **94 tests, 0 failures** |
| New I2 numerical/provenance/publication/CLI suite | **101 tests, 0 failures** |
| Final combined test total | **282 tests, 0 failures**; not a model-accuracy estimate |
| Source preservation | Original I1 ZIP SHA unchanged; all **9** example-source files identical |
| Reference coverage | **39 statements / 39 countries**, **3,448 frozen terms** |
| Inherited summaries/labels | 155 existing points and 507 inherited/provisional codes retained; no gold promotion |
| Method accounting | **42 terminal decisions; 133 prerequisite records** |
| Actual source execution | M01 and M02 executed; M05 and M06 fitted/projected and **withheld_quality**, with valid artifacts retained |
| Projection display checks | **17 checks per method**, recomputed against exact source/model inputs |
| Numerical display contracts released for this source example | **0** |
| Published analytical sections | Exactly **O1–O5**, Iran/Cuba/Ukraine/AI order retained |
| Country organization | 39 readouts, regional order and alphabetical ordering preserved |
| MIME | 1 HTML body, 1 plaintext body, 1 CID seal; X-Unsent: 1; empty sender/recipient; no MIME defects |
| Audit PNG execution | All **5** standalone scripts executed, including the 2 new projection figures |
| Archived R rebuild | EML, both HTML forms, plaintext and **all 5 audit PNGs** byte-identical (**9/9 files**) |
| Rebuild method | All 5 figure scripts actually reran successfully; equality is not inferred only from copied PNGs |
| History/model immutability during rebuild | **563** stored files unchanged |
| Historical store verification | 1 commit, 546 unique statement/label objects; raw blobs verified |
| Reference CLI | List and full source verification executed; no reference bytes changed |
| Browser | Chromium at 390, 720, 1280 and 1600 pixels; no detected overflow/errors, decoded seal, exactly 5 slots |
| Operational effects | No live model call, email, Windows task, repository deployment or credential inclusion |

## Why the actual map is withheld

| Diagnostic | Actual PCA value | Frozen display rule |
|---|---:|---:|
| Reference variation retained in two dimensions | 9.122% | at least 40% |
| Current pairwise energy retained | 9.122% | at least 40% |
| Raw pairwise-distance stress | 0.735374 | at most 0.45 |
| Pairwise-distance Spearman correlation | 0.515361 | at least 0.70 |
| Mean k-neighbor overlap (k=5) | 0.435897 | at least 0.50 |
| Second-to-third eigengap ratio | 0.143135 | at least 0.05 |

The replay additionally fails source-scope, known-language/genre and source-flag checks. These are separate from geometric fidelity. Its low-dimensional coordinates are retained with an **AUDIT ONLY** label. PCoA is computed in the same Euclidean geometry, is an audit challenger, and is not a fallback to make the email more visually populated. Thresholds were frozen before the source fit; none was lowered in response to this result.

The four other analytical slots remain explicitly unavailable pending their own methods and evidence. No rhetorical movement, topic emergence, policy-position score, coalition claim, confidence region or forecast is created to fill a slot.

## What the new tests establish

Exact TF/IDF formulas and duplicate handling; frozen vocabulary/IDF; statement and country normalization; OOV and zero-vector behavior; sparse/dense resource limits; source hashes; provenance/language namespace separation; availability/event-time gates; corrupt-pointer and corrupt-model rejection; numerical comparison with stats::prcomp and stats::cmdscale; PCA/PCoA geometric equivalence; fixed-reference out-of-sample and batch-invariant transforms; negative-eigenvalue, asymmetry, degeneracy and missing-coordinate handling; tamper rejection; all 17 display gates; exact five-slot routing; positive O3/PNG/MIME conformance; challenger exclusion; and read-only CLI execution. A lowered threshold in only the live config fails the preserved-policy check.

The positive publication fixture uses deliberately constructed botanical/geological/music text and **explicitly simulated observed metadata** inside a temporary validation directory. It is not a real UN sample, independent semantic holdout, statistical calibration or production evidence. Its temporary history/model objects are removed. A separate test confirms engineering/replay provenance cannot pass the display gate.

## Reproducibility and preservation

Reference EML SHA-256: `0dd6fdfa4fb657ab34573d804d8f7ecbda26046639c9d2ab1fc28051e8d82967`

`independent_integrity_and_reproduction.json` contains all 9 output hashes and figure execution ledgers. `state_before_rebuild.json` binds the immutable-history/model comparison. `source_bytes_preserved.json` verifies the original release and inherited source files. The exact policies, vocabulary, sparse feature matrices, centers/loadings, eigenvalues, PCoA anchors, source snapshot and diagnostics are in the completed run.

After verification, active example state was relocated **byte-for-byte** to `examples/hi2`, `examples/mref` and `examples/cache_reference`; the active directories are empty. See `reference_relocation.json`. Existing I1 reference examples remain separately identifiable. This packaging step does not claim a new acquisition or model fit.

The archived rebuild preserves the original method ledger. An executed row there describes the original source run, not a second model training event. The actual rebuilt figures have their own successful script records.

## Limitations and checks not performed

No live UN or paid OpenAI request, production jsonlite/httr2/xml2/digest/base64enc path, package installation/renv restoration, Windows PowerShell/DPAPI/Task Scheduler action, native chromote execution, or native Microsoft Outlook render was tested in this milestone. No new dependency lock is fabricated. The new Matrix/stats numerical code **was** executed. Browser/MIME checks used independent development Python tools; those are not shipped or required by the daily workflow.

The thresholds are engineering display defaults, not guarantees of semantic/political meaning, independent-country sampling, inferential coverage or out-of-sample model accuracy. No historical semantic recoding, human-gold ingestion, embedding, classifier, clusterer, movement, driftmapR, network, forecasting or diffusion adapter is silently represented as completed. No large-corpus or peak-memory benchmark is claimed; the source-bound caps are tested.

Earlier development failures are retained in the logs rather than counted as successful tests: foreground tool timeouts with verified stale-lock recovery; an initial figure syntax error; floating-point self-distance handling; a clipped figure footer and placeholder text repair; correct rejection of an incompatible earlier development reference; a missing CLI table-column argument; and a CLI test harness that initially captured stdout instead of exit status. Final runs use corrected code. No source text, issue label or release threshold was changed to manufacture a pass.
