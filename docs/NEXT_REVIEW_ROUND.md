# Random development and fresh test review — round 2

This round addresses the poor precision observed in the first learned-model
comparison. It creates two new unlabelled 24-passage packets:

- Development validation: September 24–26, at http://127.0.0.1:8774/.
- Fresh test: September 28, at http://127.0.0.1:8775/.

Review the development packet first. Both forms show source links, neighboring
context, national-address eligibility checks, blank relevance choices, browser
draft storage and a downloadable backup. A local server must be running to save.
The owner remains sole reviewer and finalizer. Preparation does not assign labels
or claim completed human review.

## Sampling and separation

Both samples use a deterministic random shuffle without AI-keyword enrichment.
The development pool had 1,204 passages after country exclusions; one normalized
exact duplicate was removed. Its selected 24 passages cover 23 countries. The
fresh test pool had 108 passages after exclusions, with no further detected
duplicates; its selected 24 passages cover 11 countries. See
[packet hashes and screening evidence](../research/validation/i10/round2-packets.json).
All countries in either earlier development packet or the earlier test packet
are excluded. The new test also excludes countries selected for new development.
The existing lexical duplicate screen checks prior reviewed quotations, full
source-text windows and passages within each new pool. The fresh test additionally
checks the new development source windows. Detailed counts and thresholds are
recorded in the packet evidence; this does not guarantee semantic uniqueness.

These are conditional samples from the remaining eligible countries and passages,
not a representative estimate of the entire General Debate. Country grouping,
ASR quality and human intervention-boundary decisions remain limitations. A fresh
sample from the same archive is not an independent external corpus.

The private workspaces are `review-work/ai-random-dev-v2` and
`review-work/ai-fresh-test-v2`. Existing packets are preserved. Raw passages,
individual choices and tokens stay outside Git.

## Development-only tuning plan

The [fixed plan](../research/development_tuning_v2.json) fits candidates on the
existing 48 development labels and selects settings using only the new random
development-validation labels. It tests logistic C values 0.1, 1 and 10, BERT
learning rates 0.00003 and 0.00005, five or ten epochs, and thresholds 0.3–0.7.
The selection metric is validation F1, with prespecified tie-breaking rules.

If the random validation sample lacks one class, collect more development labels;
do not use test outcomes to compensate. After selection, freeze all settings,
refit on resolved development labels and evaluate the fresh test once. The old
test is retained only as historical evidence. Excluded or insufficient-context
labels must be reported, not treated as negative cases.

**Tuning and new model evaluation are pending human labels.** No new accuracy
claim is made by creating these packets. The next action is to complete the
development form; collect the fresh test labels separately and keep them out of
model and threshold selection.

## Reproduction

Validation: 23 existing loader tests passed. Both packet copies successfully
saved and loaded engineering-fixture labels while real packets stayed blank.
Country sets are disjoint. Browser checks at 1440px and 390px confirmed 24 cards,
blank choices, unchecked confirmation and no horizontal overflow in both forms.

With the existing reviewed packets and recovered archive in a new workspace:

```powershell
python tools/prepare_next_review.py review-work
python tools/pilot_review.py serve review-work/ai-random-dev-v2 --port 8774
python tools/pilot_review.py serve review-work/ai-fresh-test-v2 --port 8775
```

Preparation refuses to overwrite existing packets. Use the existing created
forms rather than rerunning over them. Development validation is a model-selection
set, so its best score must not be presented as final held-out performance.
