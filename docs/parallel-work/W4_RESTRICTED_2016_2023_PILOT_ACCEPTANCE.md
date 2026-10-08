# W4 source-aware 2016–2023 frozen lexical pilot — private descriptive acceptance

**Recorded:** 8 October 2026. **Decision:** A reproducible source-bound **private descriptive engineering pilot has executed** on the restricted 99-country/523-observation General Debate panel. Its frozen representation, W1 original numerical code, and W4 original numerical framework were run locally on authorized P2 inputs. **Inferential calibration, population generalization, public scientific publication and browser integration are not eligible.**

The companion [aggregate-only receipt](W4_RESTRICTED_2016_2023_PILOT_AGGREGATE.json) contains no original UN texts, fitted vectors, named-country movement results or private speaker records. The source-linked panel, saved feature checkpoint, W1/W4 outputs, reproducible Python and hash manifest were delivered in the **private conversation artifact**, not committed.

## Private observed population

| Quantity | Actual count | Important denominator |
| --- | ---: | --- |
| Originally inventoried country × annual session cells | 792 | 99 recorded affiliations × eight 2016–2023 sessions |
| P2 full-original-PV corroborated Harvard speech texts | 523 | 252 in 2016–2019; 271 in 2020–2023 |
| **Unverified** country-session cells | 269 | 144 reference; 125 later; not confirmed nonparticipation |
| Verified original UN General Debate meeting sources | 55 | Source-level group, not independent passage-level observations |
| Bahamas missing UN-index dates recovered from PV title pages | 3 | 2016, 2017, 2023 |

Original Harvard corpus text hashes were rechecked byte-for-byte against uploaded v14 and P2 source records; all selected original PV meeting digests were checked against their private 63-document manifest. Actor is **recorded country affiliation**, never an independently identified repeated person. The P2 sample uses purposive original-meeting selection and conditions cohort inclusion on source corroboration observed in **both** periods. All missing cells remain explicitly `unverified` in the corrected W4 private panel.

## Frozen reference feature system

- **Training exclusively 2016–2019:** 252 source-backed full speeches; exactly 6,000 reference-selected TF–IDF terms, fixed vocabulary and IDF; 64-dimensional randomized TruncatedSVD (`random_state=20261008`), then L2 normalization.
- **Transformation only 2020–2023:** 271 speeches passed through the identical vocabulary, IDF and 64-D decomposition. The future texts were not used to fit the vocabulary, SVD, or feature weights.
- **Pinned private checkpoint fingerprint:** `8da03a179847a8fccb7e8123b8dd278f5edf5d22ad7e74489401a5f2d5cfa054`. Saved tokenizer/TF–IDF object, SVD matrix and 523×64 projection replay exactly after reload (maximum absolute difference zero on this environment).
- The two-dimensional map is **only the saved reference's first two latent coordinates**, not a newly refitted map; W4 correctly uses an identity alignment and does **not** manufacture a Procrustes operation. The numerical distances refer to normalized high-dimensional LSA vectors, not diplomats' political positions.

## Executed W1 source-aware numerical validation

The repository's canonical W1 Node runner executed locally on the original 523 text/hash IDs, restricted to one declared source population, using two LSA clustering configurations (k-means and hierarchical Ward, k=5), with four whole-meeting scheduled resamples per method. **Two full fits and eight meeting-group refits succeeded.** Pairwise model agreement: ARI **0.4971**, adjusted mutual information **0.5458**, and pairwise assignment consistency **0.8203**, all **descriptive**.

Original meeting source IDs supplied 55 groups. Group-and-affiliation transitive closure produced **one** connected component across 99 affiliations; hence **two affiliation schedules were withheld** with explicit skipped failure ledger entries. They were not misrepresented as independent country or passage-level replicates. A separate exploratory 64-D frozen-basis study completed 55 whole-meeting leave-one-out displacement sensitivities, not confidence intervals. A longer W1 ten-resample attempt did **not** complete before timeout and is recorded as **non-delivery**, not a passing result.

**Compatibility condition:** the locally verified original P2 source schema `un.p2.original-pv-reconciled.v1` was added to **local** W1 input/output allowlists for this controlled run. No numerical W1 code was modified. This schema is **not yet approved in the shared main interchange**, so no claim of upstream official W1 production acceptance is made.

**Do not compare W1 and W4 scores as one geometry:** W1 Node refits its own six-dimensional LSA for same-cohort computational stability; W4 uses the independently frozen 64-dimensional pre-2020 reference. Their basis/selection procedures are different, so cross-run distance or ARI comparisons require a separate named protocol.

## Executed W4 real-data private diagnostic

The corrected W4 source branch (PR #18) now accepts explicit `unverified` P2 source rows with null original date, source/meeting identifiers and hashes, without inventing source text, fit labels, or zeros; observed rows still require original dates and source identities. On the real 792-cell private panel it retained **523** observations with comparable frozen vectors, **269** unverified cells and **99** matched recorded affiliations. Mean within-affiliation full-64-D Euclidean distance **0.5398** and common-actor centroid displacement **0.2774** are purely descriptive. Actor cluster correspondence has 84 shared confidently assigned actors; ambiguous members remain explicit. Two original UN PV meeting source families do not span separate annual eras as paired independent groups. W4 correctly withholds the paired-source bootstrap with **zero attempted draws**, and has no calibrated confidence interval.

GitHub Actions [W4 CI #37828129270](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/37828129270) passed **19/19** synthetic tests and the existing W1/source-browser regressions on the committed adapter. Local private replay used the same feature-branch implementation method and source only. **No** source-linked private vectors or national assignments were committed.

## Shared interchange and release blockers

1. `un.parallel-analysis.v1` (v1.0.0) requires observation dates as strings and does not permit `source_status:unverified`. The 269 P2 observations have genuinely unknown event dates. The corrected W4 adapter **fails closed** on attempting full 792-row v1 export. Neither fake dates nor mislabeling `unverified` as `unavailable` are acceptable. Coordinator must approve a separately versioned nullable-date/source-status contract or a separately typed read model before browser integration.
2. The sample is a selected historical subset; same-year global issues, meeting-level shared content, document translation and transcription practices, and country speaker turnover remain confounders. No person-level actor authentication.
3. The one connected affiliation/source-group closure and zero genuinely paired cross-period source families prevent justified bootstrap inference under W1/W4's current dependence policies. Whole-meeting leave-one-out is sensitivity only.
4. Clustering k=5 and feature dimensionality 64 were exploratory engineering settings; no independent calibration, multiplicity control, preregistered political null, external validation, or source-population sampling model exists.
5. Real-source comparisons cannot be released as diplomatic stance, policy convergence, coalition shifts, influence or country political movement.

## Explicit acceptance matrix

| Scope | Decision |
| --- | --- |
| Private verified 2016–2023 lexical reference freeze and exact replay | **PASS** |
| P2 source-based country-session and original PV integrity | **PASS for 523 P2 corroborated observations only** |
| W1 canonical Node grouped development method computation | **PASS under locally extended schema only** |
| W4 corrected nullable/unverified inventory and real private method execution | **PASS for private descriptive method test** |
| Shared v1 full 792-row source interchange | **WITHHELD** |
| Independent repeated-source bootstrap validity | **WITHHELD** |
| Calibrated uncertainty / hypothesis testing / causal inference | **WITHHELD** |
| Publication / diplomatic statements / browser deployment | **WITHHELD** |

**Files and frozen protections:** This coordinator-only PR must change only these two documentation files. The W4 implementation remains in **unmerged PR #18**. No reserved October 5–6, 2026 meeting transcript was opened; the 37-file evaluation lock, original corpus digests, D1 release gates, 24 human decisions and active public browser remain unchanged.

**Next technical acceptance:** Decide whether to add a new interchange contract supporting unverified inventory; reconcile W1's original-source schema and method settings; independently assess source- and year-dependent uncertainty on expanded real meeting sources. No automated publication/merge follows.
