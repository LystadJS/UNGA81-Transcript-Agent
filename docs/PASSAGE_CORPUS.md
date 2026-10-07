# Expanded passage corpus and weighting contract

**Implemented research contract:** reproducible full source-segment partitions, original-byte lineage, explicit analytical populations, separate descriptive weights, development-only lexical fitting, and a reserved temporal comparison frame. This phase does not replace the browser workflow or change the frozen R/D1 publication gates.

## Frozen source frame

The declared window is **1–6 October 2026**, the six completed calendar dates preceding implementation. Every meeting in the retrieved UN transcript inventory is retained, including missing-transcript entries and empty dates. There is no topic, country, keyword, clustering-result or availability-based source selection.

| Role | Dates, inclusive | Meetings | Content access in this stage |
|---|---|---:|---|
| Development | 1–4 October 2026 | 21 | Only these transcript endpoints may be collected |
| Reserved temporal comparison | 5–6 October 2026 | 37 | Inventory metadata only; transcript text remains unopened |

The observed inventory contains no meetings on 3 or 4 October. The two later dates were reserved before development transcript collection or model fitting. This is not a random 80/20 split and does not guarantee matching genre distributions. It is an operationally reserved comparison frame, **not a claim that nobody has ever seen these public transcripts**.

`research/corpus/plan.json` records the selection, length, language, duplicate, weighting and review policies. `inventory.json` preserves the metadata snapshot and original response digests. `frame.json` binds the plan, parsed inventory, exact meeting identities, dates and endpoints with SHA-256 digests. The initial inventory snapshot retains parsed metadata plus original response hashes, not the original response byte streams. Original transcript response bytes, in contrast, are retained in full when development sources are collected.

Rebuilding uses the frozen inventory; it does not silently update availability or reassign a holdout when the live service changes. A different frame is a new version, not a replacement of the old experiment. Meeting and date disjointness does **not** establish independence: recurring committees, speakers, affiliations, shared boilerplate and near-duplicate uploads may span both periods. Exact source/text overlap is checked before any supported held-out transformation; near-duplicate assessment remains separate work.

## Observation and source lineage

```text
Frozen inventory meeting
  └─ Original response bytes + SHA-256
       └─ Original source segment + JSON pointer + speaker metadata
            ├─ Explicit speech identity and extent, when reviewed
            └─ Contiguous passages + parent offsets + passage hashes
```

The builder preserves every source segment, including empty, procedural, uncertain and non-English records. It does not merge all of a country's interventions and call the result a speech. Unknown or ambiguous affiliation matches remain null; names and country positions are not inferred from wording. Recorded body/category metadata are retained as grouping variables, not independently adjudicated event genres.

The source text representation joins the original sentence strings with one space, matching the current collector's extraction convention. Each original sentence has a JSON pointer and code-point interval in this representation; the unaltered response bytes remain recoverable from the source bundle. Offsets are **zero-based Unicode code points, end-exclusive**, not UTF-16 indices or byte positions. Every parent is partitioned without overlap or omitted characters. Original whitespace and emoji survive reconstruction; no correction notes become replacement text.

The v1 partitioner balances consecutive whitespace-delimited tokens across windows of at most 160 tokens. It deliberately makes no claim that these windows are rhetorical or semantic units. Partitions below 40 tokens remain stored but are excluded from the analytical population. Whole-parent, observed-text coverage is reported separately from analytically eligible coverage. A reconstructed source segment is not proof that all delivered words were transcribed.

Exact normalized text duplicates are flagged but retained across distinct source occurrences. Repeated diplomatic language may be meaningful; removing it globally by default would change the question. Duplicate source identities are rejected. The normalization is for an audit hash only and never overwrites original text.

## Two explicit populations

| Population | Inclusion | Permitted interpretation |
|---|---|---|
| `reviewed_speeches` — default | Eligible English windows with confirmed substantive/mixed/right-of-reply type, explicit speech identity, and complete or near-complete observed speech extent | Reviewed speech-partition exploration, subject to declared coverage |
| `source_segments` | Eligible English windows, including provisional segments; explicit procedure, suspected-transcription-issue and uncertain review decisions remain excluded | Audit-only source-segment exploration, not a speech count or publication-ready policy finding |

Both populations retain short-text, language and reviewed-type exclusion reasons. Missing/unavailable transcripts are counted as missing, never as zero mentions. Unreviewed sources are not marked human-confirmed by an automated process.

`un.corpus-boundary-review.v1` binds the exact source-bundle digest and every choice to its source-record/text hash. New templates contain `confirmed: false`. Confirming a whole source-segment boundary requires a reviewer, timestamp, type, extent and explicit speech ID. Near-complete declarations require a coverage note. Multiple segments may share a speech ID only within the same meeting and with consistent recorded speaker and affiliation metadata. V1 confirmations apply to whole original source-segment boundaries; internal mixed-speaker boundary editing remains a separate reviewed-unit task.

The owner's completed 24 audio/boundary pilot decisions remain unchanged. This contract does not claim that those purposive excerpts are complete partitions, does not re-request their review, and does not automatically import their correction notes as text. A new corpus requires new-source boundaries, not a repetition of the completed pilot.

## Weighting objectives

Weights are computed **after explicit eligibility selection and before any fit's missing/noise exclusions**. Let N be eligible passages, S eligible reviewed speeches, M represented meetings, C known represented countries, n_s passages in speech s, S_c speeches of country c, and n_m passages in meeting m.

| Scheme | Per-passage weight | Question represented |
|---|---|---|
| `equal_passage` | 1 / N | What share of eligible passages belongs to each pattern? |
| `equal_meeting` | 1 / (M × n_m) | What is the average within-meeting passage composition? |
| `equal_speech` | 1 / (S × n_s) | What is the average reviewed-speech passage composition? |
| `equal_country` | 1 / (C × S_c × n_s) | What is the average country profile, averaging speeches equally within country? |

These are **descriptive composition weights**, not probability-sampling weights, national voting weights or evidence of representative sampling. Speech and country schemes are withheld unless every selected passage has a confirmed complete/near-complete speech identity. Country weighting additionally requires every selected passage to have a resolved country; there is no fictitious 'unknown country' and no silent known-country-only renormalization.

Reports retain all eligible denominator mass: cluster 0 is `unassigned`, while missing model outputs or unusable vectors are `not_fitted`. Neither is silently dropped to improve agreement. The reported reciprocal sum of squared weights is named `kish_weight_concentration`; `independent_sample_size` is null. Many passages from one meeting do not create many independent meetings.

**Weighted fitting is intentionally not enabled.** The current validated model kernels use equal-passage fitting. Requests for country- or speech-weighted fitting fail explicitly; attaching a weight column cannot change PCA, k-means, PAM, hierarchy, HDBSCAN, GMM or NMF objectives by implication. Method-specific weighted implementations and numerical calibration remain separate work, as required by the roadmap.

## Development-only reference and comparison lock

The lexical reference learns vocabulary, document frequencies and IDF from the declared development population only. It records source/passages hashes, the tokenizer module hash, plan/frame/corpus digests, and the feature bound. Subsequent transforms reuse the stored vocabulary and IDF without fitting. All-out-of-vocabulary text stays an explicit zero vector with coverage counts.

This separately versioned reference uses NFKC/lowercase Unicode letter/number tokenization and **retains negation**, with no stop list. It is therefore not advertised as numerically identical to the browser's existing stop-word-filtered TF-IDF. The browser implementation is not modified. The frozen reference is lexical only: it is not a fitted PCA transform, semantic encoder or substantive result.

The bounded development adapter can run the existing clustering kernels on these vectors, with the declared audit-only population and composition summaries. The existing 4–600-observation envelope is enforced: oversized inputs are withheld without sampling. Grouped refit stability is disabled here because the existing refitter reconstructs its own lexical features; a new frozen-reference refit adapter requires separate validation.

Before a held-out transformation, a comparison lock must bind the frame, lexical reference, explicitly declared fitted-development-model digest, research question and planned metrics. The lock does not authenticate that an externally supplied model was trained correctly, does not supply an evaluation result, and is not an access-control security boundary. It makes the intended evaluation inputs inspectable. The CLI deliberately has **no held-out collection command** in this release. Reserved-source acquisition, duplicate quarantine, model-specific out-of-sample projection, evaluation accounting and inspection logging must be implemented before evaluating the reserved set. No held-out performance or null-calibrated 'nonrandom structure' is claimed here.

## Reproduce

Requires Node.js 22 and the repository's already-vendored numerical modules; no new npm package, API key, remote model or text upload is introduced. These steps run from the repository root, including on Windows. Output directories/files must not already exist.

```sh
node tools/check_passage_corpus.cjs
node tools/test_passage_corpus.cjs
node tools/passage_corpus.cjs collect-development research/corpus/frame.json research/corpus/work/source
node tools/passage_corpus.cjs build research/corpus/frame.json research/corpus/work/source/source-bundle.json research/corpus/work/build
node tools/passage_corpus.cjs audit research/corpus/work/build/corpus.json
node tools/passage_corpus.cjs reference research/corpus/work/build/corpus.json research/corpus/development-options.json research/corpus/work/reference.json
node tools/passage_corpus.cjs analyze-development research/corpus/work/build/corpus.json research/corpus/development-options.json research/corpus/work/analysis.json
```

Create the ignored `research/corpus/work` parent directory before the first collection. The explicit example options select provisional source segments for audit only. Omit that option to use the default reviewed-speech population, which is correctly withheld before new-source boundary confirmation. To run a bounded individual development meeting, add its exact frozen `meeting_id` to a copied options file; never reduce the corpus by silently sampling passages.

To apply completed new-source boundary choices, pass the review file as the fourth build argument and use a new output directory. The builder rederives originals and passages from the saved response bytes; edited IDs, offsets, hashes, source metadata or invented derived coverage are rejected on load.

Outputs include `corpus.json`, `passages.csv`, `coverage.csv`, `parent-coverage.csv`, `weights.csv`, `audit.json` and a pending boundary-review template. The source bundle retains exact raw response bytes. CSV cells protect against spreadsheet formula injection. Store text-bearing outputs locally; `research/corpus/work/` is ignored by Git. Neither private owner inputs nor these generated corpora are mirrored to the public application.

## Acceptance and limits

`Passage corpus contract` CI checks frozen-frame reproduction, exact source reconstruction, Unicode bounds, missing-data accounting, explicit review provenance, all weighting formulas, noise/failure denominator preservation, leakage guards, frozen vocabulary behavior, source-only acquisition, no-overwrite behavior, and bounded integration with the existing numerical kernel. Existing analytical/source regression suites also run. Synthetic test choices are explicitly labeled as engineering fixtures, never owner review.

The separate live-development run records actual collection and corpus counts without opening the held-out text. Its machine-readable receipt belongs alongside this guide; engineering acceptance alone does not establish source quality, national positions, representativeness, independent replication, or a statistically nonrandom diplomatic grouping.

Reference for the no-test-data-fitting principle: [scikit-learn, Common pitfalls / data leakage](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage). Source status: [UN Transcripts](https://transcripts.un.org/en) states that these automatic transcriptions are not official UN records or documents.
