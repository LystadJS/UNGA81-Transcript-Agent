# Fixed AI keyword baseline — 1 October 2026

The baseline predicts relevant when the reviewed quotation contains a whole-word,
case-insensitive match for **artificial intelligence**, **AI**, **machine learning**
or **autonomous weapons**. Otherwise it predicts not relevant. These are the
existing pilot sampling terms, specified before executing this evaluation. No
parameters were trained, no model service was called, and no rules were changed
after viewing the results. It uses the quotation only, not surrounding context.

## Held-out September 28 result

| Measure | Keyword baseline | Always not relevant |
|---|---:|---:|
| True positives | 1 | 0 |
| False positives | 0 | 0 |
| False negatives | 2 | 3 |
| True negatives | 21 | 21 |
| Precision | 100% (1/1) | Undefined: no positive predictions |
| Recall | 33.3% (1/3) | 0% (0/3) |
| F1 | 50.0% | 0% |
| Accuracy | 91.7% (22/24) | 87.5% (21/24) |

The rule has low observed coverage: it misses two of the three human-labelled
relevant passages. Zero false positives and 100% precision are based on only one
positive prediction, not evidence of dependable precision at scale. The 24
passages come from 14 countries, so country-level clustering also limits
interpretation. No claim of BERT superiority follows from this result.

The 48 development passages produced 24 true positives, zero false positives,
three false negatives and 21 true negatives: precision 100%, recall 88.9%,
F1 94.1%, accuracy 93.75%. Those packets were enriched using this same vocabulary,
so these are diagnostic development results, not representative performance.

## Integrity and validation

The evaluator checked the frozen test export SHA-256, current reviewed-bundle
identity, both development identities, country separation, test date and complete
binary labels. Exact specification and runner hashes are recorded with the
[results](../research/validation/i9/ai-baseline-v1.json). Individual predictions
and source quotes remain private in `review-work/ai-baseline-v1`.

Eight unit tests passed, including word boundaries, acronym matching, confusion
counts, undefined metrics, invalid labels and mismatched lengths. Two additional
checks confirmed rejection of a changed frozen export and an existing output
directory. No source labels were altered. This is an audit-only lexical benchmark;
it does not enable real-data fitting in the neural runner or release a daily model.

## Recommended next steps

1. Use development errors and additional development labels to improve coverage;
   do not adjust keyword rules or BERT hyperparameters to fit these test errors.
2. Prespecify a regularized TF-IDF/logistic baseline and split development data
   by source/country for tuning. The current 48 labels are a small pilot.
3. Implement a bounded real-data training adapter before fine-tuning the selected
   BERT checkpoint. Compare models under the same fixed evaluation protocol.
4. Obtain an additional untouched test sample for stronger claims. The current
   benchmark can be retained, but repeated comparisons must not become tuning on
   its labels; only three positive cases make recall especially unstable.

```powershell
python tools/test_ai_baseline.py
python tools/evaluate_ai_baseline.py research/ai_baseline_v1.json review-work/ai-test-sep28 review-work/new-baseline-run --development review-work/ai-pilot-r2 review-work/ai-later-review
```
