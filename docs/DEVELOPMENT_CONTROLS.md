# Development controls and synthetic held-out evaluator rehearsal

**Status (8 October 2026): completed development-only controls; not a held-out evaluation.** All 37 reserved meetings from 5–6 October 2026 remain **metadata-only and unopened**. Only cached, source-hash-verified **1–4 October development** materials and artificial synthetic fixtures were used. None of the resulting p-values is a probability of diplomatic alignment, a test of global cluster existence, or an independent holdout result.

## Inputs, freeze and intent

The previous nuisance-reference plan, `reference.py`, saved lexical/semantic model fits and `evaluation-lock.json` are unchanged. The frozen strict machine-only development population is **1,641 technical passages from 523 observed source segments in 16 meetings**, not 523 verified full speeches. The initial 999-draw conditional references included controls for meeting and original parent length tercile; recorded role was also examined. Previously disclosed source dependence, transcription, role attribution, machine classifications and missingness remain.

This phase asks whether the original lexical/semantic and same-country neighbor associations may arise because **source metadata or explicit country words are shared**. It adds transparent negative controls, text masking with frozen transformations, and a synthetic evaluator to exercise release logic. It deliberately does not reinterpret the earlier reference statistics as a test of policymaker-relevant political structure.

## 1. Nuisance-only negative controls

The code creates two source-parent vector populations with deterministic random feature codebooks, *without accessing the parent text or any saved linguistic embedding*. Control A contains only meeting ID, genre, recorded actor role and frozen length tercile. Control B adds recorded country identity, mimicking the non-substantive ability of an encoder to recover a speaker's country name. The **same conditional 999-draw reference tests** and Holm correction are then applied to each control. These are confounding demonstrations; the null test may validly detect an association even when its source is non-political.

| Control and diagnostic | Observed | Conditional null mean | Holm-adjusted p |
|---|---:|---:|---:|
| Metadata only — cross-representation neighbor overlap | 0.3652 | 0.2328 | 0.002 |
| Metadata only — recorded-country neighbors | 0.0186 | 0.0194 | 0.845 |
| Metadata + artificial country-identity feature — neighbor overlap | 0.4187 | 0.0998 | 0.002 |
| Metadata + artificial country-identity feature — recorded-country neighbors | 0.2391 | 0.0188 | 0.002 |

**Interpretation:** Exceeding a development reference threshold does not show that any text contains meaningful political alignment. Agenda/metadata alone can create the tested geometry. The artificial country-identity feature produces a strong same-country score without a single substantive sentence. Neither is a formal false-positive-rate calibration against a justified political-null distribution.

## 2. Country-name masking sensitivity

The code derives 687 candidate name aliases from the **existing frozen country registry**, excluding ISO-3 codes, selected ambiguous names, and demonyms. It also includes explicitly declared English abbreviations for the United States. Non-overlapping word-boundary matches are replaced with the constant lexical token `nation` in a **derived copy only**; each original character span and hash is preserved in the private audit. This is *not* a comprehensive geopolitical-entity or demonym redaction model. The matching policy can over-mask non-country mentions and under-mask grammatical variants, institutional names, and national adjectives.

The original passage identities/order, 523 parent groups, original nuisance length strata, original fitted TF–IDF vocabulary and IDF, original LSA components, pinned MiniLM ONNX model, saved semantic PCA center/components, and k-means centroids are **fixed**. No reclassification, model refit, new parameter selection or recalibration occurs. Semantic masking is encoded offline from the altered development text with the SHA256-locked MiniLM artifacts, preserving all WordPieces by chunking. Exact masked-text digests and per-chunk offsets are recorded.

| Metric | Original text | Country names masked |
|---|---:|---:|
| Mean lexical/semantic 15-neighbor overlap, excluding same meeting | 0.3940 | 0.4076 |
| Same recorded country among 15 nearest semantic neighbors | 0.0911 | 0.0376 |
| Conditional-null mean for recorded-country neighbor share | 0.0158 | 0.0152 |
| Holm-adjusted p for country label recurrence | 0.002 | 0.002 |

**Coverage:** 3,330 matched country-name occurrences; 1,243 of 1,641 passages altered; 469 of 523 source parents affected. All **258,930 masked WordPieces** were represented in 1,642 chunks, with **zero truncation**. Frozen semantic k-means centroid prediction changed for **213 passages**, with original-versus-masked partition ARI **0.7466**. Mean original/masked semantic-vector cosine: **0.9228**. This is descriptive model sensitivity, not validated stance performance.

The same-country neighbor share falls by about 59%, indicating that literal country-name information explains an important part of the initial association. The residual remains conditional and potentially confounded by demonyms, agenda, speakers, attribution, and unmasked country cues. Cross-model overlap rises slightly under masking; neither change establishes stronger substantive latent structure.

## 3. Locked held-out evaluator — synthetic dry-run only

`holdout_dryrun.py` loads and validates the **existing sealed evaluation lock**, without any tool capable of retrieving real transcripts. It generates **37 fictitious meeting identifiers** with fictitious dates, artificial source-parent metadata, and artificial numeric vectors. Inputs containing actual-looking UN meeting IDs, source URLs, an actual reserved date, transcript fields or any non-synthetic provenance are rejected before calculation.

The rehearsal uses the **predeclared** 15 cross-meeting neighbor definition, 999 meeting × original length-bin reassignments, Holm multiplicity accounting, frozen 0.14090298 excess-effect floor and unchanged minimums (200 source parents, 8 meetings, 70% movable parents, 15 cross-meeting neighbors). It preserves all 37 synthetic meeting statuses including failures/unavailable; insufficient coverage is marked *inconclusive*, not zero or a passing result. Country-label evaluation is withheld when the predeclared repeated-country requirements are not met; a missing secondary result is conservatively counted in the two-test correction.

A separate **frozen-transform smoke test** generates source-free random feature counts in the saved lexical vocabulary and source-free 384-dimensional embedding inputs, applies the SHA256-verified saved LSA and PCA transforms, and predicts using the saved semantic k-means centers. It never fits or opens reserved content. This tests plumbing and numeric compatibility, **not** whether actual held-out acquisition, transcription, model inference, covariate shift or substantive performance will succeed.

| Synthetic scenario | Fictitious source parents | Exercised outcome |
|---|---:|---|
| Unrelated lexical and semantic geometry | 792 | Would not replicate |
| Deliberately correlated geometry | 792 | Would pass the heuristic gate |
| Insufficient population | 132 | Inconclusive |
| All meetings unavailable | 0 | Inconclusive |
| Frozen transforms on artificial features/embeddings | 792 | Saved transforms and 10-way semantic centroid predictions executed; artificial gate not replicated |

**No simulated outcome is reported as held-out evidence.** Passing a synthetic gate only verifies the decision logic under a constructed input.

## Source provenance, release gates and limitations

`research/reference_tests/` includes `negative_controls.py`, `mask_sensitivity.py`, `holdout_dryrun.py`, `verify_controls.py`, and `test_controls.py` alongside the unchanged frozen code. Real source-linked masked audits and vector arrays belong in the **private conversation checkpoint**, not this public repository. This repository commits code, methodological documentation and aggregate validation only.

The earlier original 24 owner-confirmed pilot decisions and the provisional machine-only review remain distinct. `site/`, `un/`, and publication controls are untouched. The held-out roster and original protocol hashes are unchanged. No new statistical independence, meaning of unsupervised clusters, country-policy stance, coalition, causality, or real held-out predictive accuracy is established.

The immediate scientific priority is to design and independently scrutinize a substantive nuisance/null design that addresses document identity, speaker recurrence, country self-reference, genre and agenda leakage before interpreting country proximity. The held-out period must remain untouched absent separate owner authorization and an external methodological review of the frozen estimands.

## Reproduce with the already delivered private development and semantic checkpoints

From the repository root (Python 3.13, Node 22, original model assets pinned in `research/semantic_review/model-lock.json`):

```bash
python -m unittest discover -s research/reference_tests -p 'test_*.py'
python research/reference_tests/negative_controls.py <development-checkpoint> <saved-semantic-results> negative.json
python research/reference_tests/mask_sensitivity.py <development-checkpoint> <saved-semantic-results> <verified-local-minilm-directory> masked-new-directory
python research/reference_tests/holdout_dryrun.py dry-nominal.json --variant nominal
python research/reference_tests/holdout_dryrun.py dry-correlated.json --variant correlated
python research/reference_tests/holdout_dryrun.py dry-insufficient.json --variant insufficient
python research/reference_tests/holdout_dryrun.py dry-all_unavailable.json --variant all_unavailable
python research/reference_tests/holdout_dryrun.py dry-transform-smoke.json --variant correlated --exercise-frozen-transforms <development-checkpoint> <saved-semantic-results>
```

All commands prohibit overwrite. The negative/masking CLI verifies the saved source/model hashes, and the dry-run accepts **only generated synthetic records**. The new checks are automated in a read-only CI job without any live transcript collection. The exact real-development validation record is in `DEVELOPMENT_CONTROLS_VALIDATION.json`.
