# Five-level stance model: candidate and acceptance contract

**Status: no accepted trained checkpoint or owner-reviewed production benchmark is included.** The source code implements preparation, training, inference and evaluation interfaces. Synthetic tests verify these interfaces; they do not establish stance accuracy.

## Intended use

Estimate a recorded actor's expressed stance toward a precise policy proposition in an English UN transcript passage. Retain the dated source, exact text offsets, surrounding context, issue version, attribution, probabilities and model identity. The model does not infer an entire government's enduring policy from an isolated statement.

Substantive labels are `strongly_oppose`, `oppose`, `neutral`, `support` and `strongly_support`. Strength means expressed commitment/intensity, not confidence or verbosity. Explicit neutrality differs from no expressed position. Conditional, mixed, unclear and unattributable material remains separately identifiable, and uncertain classifications abstain.

## Candidate and execution

The initial candidate is `distilbert/distilbert-base-uncased` with a proposition-conditioned classifier. Training requires an explicit immutable upstream revision and verified local files; the configured null candidate revision is a missing setup value, not an automatically selected floating model. The existing pinned MiniLM representation supports retrieval/discovery and does not itself establish stance.

Training uses a separate manual workflow and local source files. ONNX Runtime CPU provides inference. A candidate is not promoted automatically by finishing training or passing unit tests. Quantization requires comparison against the unquantized model and repeat acceptance; it is not assumed equivalent.

The existing rule engine and TF-IDF/logistic baseline remain comparators. Generated issue candidates are distinguishable from validated catalog propositions. No external AI API receives transcript text.

## Owner pilot and data collection

Begin with a blind 300-example owner pilot. Preserve source hashes and split identities, require actual owner confirmation, and retain ambiguous cases rather than forcing a label. This pilot assesses codebook usability and the feasibility of distinguishing the five levels. It cannot establish comprehensive coverage across all venues and issues.

Expand in batches until the untouched benchmark covers at least 30 source-disjoint meetings, materially represented venues, eight policy areas and at least 100 emitted test predictions per substantive class. Complete-source annotation from at least 20 test meetings is required to assess issues missed by retrieval. The test must use later dates and distinct source families; related passages cannot leak between training, calibration and test.

Rare strong/neutral examples may limit eligibility. Do not fabricate balancing labels or describe a small slice as validated. The owner's single-reviewer mode does not measure independent inter-reviewer agreement.

Example private preparation:

```sh
PYTHONPATH=src python -m un_transcript.models prepare-pilot --segments /private/current-segments.json --catalog config/issues.json --output /private/pilot
```

Use the CLI help for train/evaluate input schemas. The workflow requires private dataset and source-model commit hashes; neither reviewed labels nor model artifacts belong in the public Git repository.

After training, run `calibrate` on the calibration split and write a new calibrated candidate directory. Generate held-out outputs with `predict-benchmark --split test`, then run `evaluate` with the frozen registration and policy. The separate `approve --confirm-release` command requires a passing receipt and the owner's actual release confirmation; routine daily inference does not require per-prediction approval. Neither workflow invokes `approve` automatically.

## Frozen acceptance requirements

`config/model-policy.json` binds the machine-readable requirements. They are prospective thresholds, not achieved results:

| Metric | Required result |
| --- | --- |
| Exact precision among emitted stances | At least 90% overall and 85% for each class |
| Opposite-polarity error | At most 2% |
| Coverage of assessable stance opportunities | At least 75% |
| End-to-end exact-label recall, including missed retrieval | At least 65% |
| Macro-F1, treating abstentions as misses | At least 0.70 |
| National/collective attribution error | At most 1% |
| Adequately sampled venue/area slice precision | At least 80% |

Also report probability calibration and uncertainty. A zero-emission model fails coverage/recall and cannot pass on an undefined precision denominator. Conditional or conflicting cases cannot be relabeled neutral to improve scores. Training thresholds are selected using calibration data; untouched results cannot be reused as development evidence while retaining the same acceptance claim.

## Limits

ASR errors, interpretation, collective speakers, quotations, conditionals, cross-sentence referents and changing policy objects can alter meaning. Source linkage establishes traceability, not semantic truth. An inference is not an official UN record, government policy certification, alliance measure or causal finding. Category codes are ordinal; default reports must not average them as equal-interval measurements.

Public stance remains unavailable until the required real labels, trained artifacts and passing source-bound acceptance receipt exist. Collection and exploratory reporting continue independently.

## Upstream license retention

New candidates preserve the exact pinned upstream `LICENSE`, model card and any supplied `NOTICE` as hash-bound candidate artifacts before training begins. The manifest records the model card's declared license identifier, upstream revision, source URL and notice hashes. Missing or ambiguous notice evidence stops training; resuming cannot silently replace a candidate's notices. These notices describe the upstream model, not redistribution rights for UN transcripts or owner annotations.

On 12 November 2026, a read-only check of `distilbert/distilbert-base-uncased` at revision `12040accade4e8a0f71eabdb258fecc2e7e948be` found declared license `apache-2.0`, LICENSE SHA-256 `43070e2d4e532684de521b885f385d0841030efa2b1a20bafb76133a5e1379c1` and model-card SHA-256 `b925a22d8efd7a29608a0e10d3f2fb33d5d80df7de4ac6e34093853cd8e0274e`. This check downloaded notices only, not weights, and did not train or accept a model. Training still requires an explicit immutable revision and actual owner-reviewed labels; the frozen pilot policy and registration are unchanged.
