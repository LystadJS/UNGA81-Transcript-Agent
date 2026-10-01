# September 28 held-out review packet

Open http://127.0.0.1:8773/ while the local server is running. The private HTML is
`review-work/ai-test-sep28/index.html`. It has 24 unlabelled passages from 14
countries, with source links, surrounding context, intervention checks, draft
storage and a downloadable backup. Save only after personally reviewing choices.

The pool began with 28 country-attributed September 28 records. Two overlapped
countries in the completed development packets and were excluded. The remaining
26 records produced 370 passages. All passed the duplicate screen. A seeded
shuffle (28092026) selected the first 24 eligible passages without keyword
enrichment. This is passage-level sampling, not equal sampling per country.

The duplicate screen compared casefolded words and five-word shingles against
all 48 reviewed development quotations, plus overlapping 150-word windows
(75-word stride) through their full source documents. It also compared test-pool
passages against one another. Near duplicates require at least 20 shingles and
either containment >=0.8 or Jaccard similarity >=0.6. No exact or near duplicates
were detected at these thresholds. This cannot rule out paraphrases, translation
variants or all shared boilerplate; it is not a semantic guarantee.

The selected source/passages/codebook files are hash-bound in the
[packet record](../research/validation/i9/sep28-packet.json). Keep the selected
packet fixed. Do not add AI examples because the random sample has few positives,
or use test labels to tune thresholds, the codebook or BERT. Flag non-address or
uncertain interventions as insufficient and report exclusions. Any changed test
protocol should be recorded as a new revision.

Validation: 23 existing loader tests passed. Targeted checks detected normalized
exact duplicates and near duplicates and retained unrelated text. A copied
engineering fixture saved and loaded successfully; the actual test packet has no
assistant-assigned labels. This is retrospective event-date evaluation, not a
claim of predictions made before the speeches occurred.

Reproduce with a new output directory:

```powershell
python tools/test_packet.py review-work/ai-evaluation-recovered/candidates.json review-work/new-test --development review-work/ai-pilot-r2 review-work/ai-later-review
python tools/pilot_review.py serve review-work/new-test --port 8773
```

Recommended next step: complete and save this test review, then freeze the labels
and evaluate a prespecified baseline. With only 24 passages, any performance
estimate will be imprecise, especially if few AI-positive examples are sampled.
No classifier training or evaluation has been performed in preparing this packet.
