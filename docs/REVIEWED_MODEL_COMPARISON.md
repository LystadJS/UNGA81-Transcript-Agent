# TF-IDF/logistic versus small BERT — 1 October 2026

Both requested models were trained locally using development labels only and
evaluated under one fixed protocol. Neither is ready for release: the logistic
model classified every test passage as relevant, and BERT produced 12 false
positives. The keyword baseline retained the highest F1 on this small test set.

| Model | TP | FP | FN | TN | Precision | Recall | F1 | Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Fixed keywords | 1 | 0 | 2 | 21 | 100% | 33.3% | 50.0% | 91.7% |
| TF-IDF/logistic | 3 | 21 | 0 | 0 | 12.5% | 100% | 22.2% | 12.5% |
| Small BERT | 3 | 12 | 0 | 9 | 20.0% | 100% | 33.3% | 50.0% |
| Always not relevant | 0 | 0 | 3 | 21 | Undefined | 0% | 0% | 87.5% |

Precision for keywords rests on one prediction; recall for learned models rests
on only three relevant passages. These 24 passages span 14 countries. No stable
population-performance claim or statistically established ranking follows.

## Fixed protocol and data separation

The [protocol](../research/reviewed_comparison_v1.json) was saved before this run.
Inputs were quotation text only. Country, dates, surrounding context and reviewer
rationales were excluded from model features. No threshold search, hyperparameter
search or early stopping occurred. Both classifiers use probability >=0.5.

- TF-IDF: lowercase word unigrams/bigrams, sublinear term frequency, minimum
  document frequency 1, maximum 5,000 features; L2 logistic regression C=1,
  liblinear solver, maximum 2,000 iterations. Vocabulary and IDF are fitted only
  on the relevant training partition.
- BERT: the selected Google 2-layer/128-hidden checkpoint, pinned revision
  `30b0a37ccaaa32f332884b96992754e246e48c5f`; full encoder fine-tuning and a new
  two-class head, 10 epochs, AdamW learning rate 0.00005, weight decay 0.01,
  batch size 8 and gradient clipping at 1.0. Inputs exceeding 512 tokens are
  rejected rather than silently truncated. Single CPU thread; seed 1102026.

First, each model fitted the 24 September 23 labels and validated on the 24
September 24–26 labels, with separate countries and source hashes. Logistic
validation F1 was 58.3%; BERT validation F1 was 76.5%. These results did not choose
settings. Both models were then reinitialized and refitted on all 48 development
labels with unchanged settings. Final fitted files and hashes were written before
the runner opened the September 28 test lock, export or labels.

The September 28 benchmark had already been used for the earlier fixed keyword
baseline. This is a fixed-settings comparison on that known benchmark, not a new
unseen benchmark. No learned-model settings were revised in response to its
outcomes. Do not tune either model on these test predictions.

## Interpretation and next steps

The enriched development set has 27 positives in 48 passages, versus three in
24 test passages. This sampling difference and the tiny training set are plausible
contributors to overprediction, not established causal explanations. The fixed
0.5 cutoff is not validated as an operational threshold. The observed false
positives rule out promoting either trained model into the daily briefing.

Recommended next steps:

1. Collect a randomly sampled development batch with ordinary non-AI language and
   review it using the same codebook. Keep it separate from this test packet.
2. Use grouped development validation to select regularization, training duration
   and any operational threshold; compare precision-recall tradeoffs there.
3. Obtain a new untouched test sample before making stronger performance claims.
4. Keep the keyword rule as a transparent reference and all model outputs audit-only.

## Validation and reproducibility

Six focused tests passed for vocabulary isolation, unresolved-label rejection,
country/content/date separation and valid forward splitting. The actual run
verified every checkpoint asset hash, the frozen test export, both development
identities, and both persisted models' prediction round trips. BERT encoder weights
changed during training. Model hashes stayed unchanged during test evaluation.

The generic synthetic research runner and daily release gates are unchanged. A
separate bounded adapter implements this user-authorized real-data experiment;
it accepts the two reviewed development packets and does not release daily models.
Private fitted models/predictions are in `review-work/ai-model-comparison-v1`.
Only aggregate results, runtime versions and hashes are published in
[I10 evidence](../research/validation/i10/comparison.json).

In the existing isolated neural environment, install `scikit-learn==1.7.2` and run:

```powershell
python tools/test_reviewed_models.py
python tools/compare_reviewed_models.py research/reviewed_comparison_v1.json research/runs/bert-pilot review-work/ai-test-sep28 review-work/new-comparison --development review-work/ai-pilot-r2 review-work/ai-later-review
```

Use a new output directory; completed runs cannot be overwritten. Runtime versions
and numerical artifact hashes are in the evidence. Repeat training only when a
new development experiment is justified, not to search for a favorable test run.
