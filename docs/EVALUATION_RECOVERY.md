# Later-date evaluation recovery — 30 September 2026

The owner resolved the final ambiguous pilot passage as **not relevant** in chat.
Revision 2 contains 12 relevant and 12 not-relevant labels. The original review
and audit attachment remain intact; the new attachment explicitly supersedes the
old bundle through its revision metadata. Use `review-work/ai-pilot-r2` for further
work, rather than pooling both revisions as independent labels.

The existing high-level-week archive supplied four later general-debate sessions.
Recovery verified their stored SHA-256 hashes, source identities and dates, and
reconstructed candidate text from raw transcript segments. No speeches were
invented or date-shifted. Private candidates are saved in
`review-work/ai-evaluation-recovered/candidates.json`.

| Source date | Country-attributed candidate records |
|---|---:|
| September 24 | 38 |
| September 25 | 37 |
| September 26 | 34 |
| September 28 | 28 |
| Total | 137 |

Six unidentifiable-affiliation records were excluded. One candidate shares a
country with the development pilot. These are grouped country records, potentially
containing several interventions, not 137 verified individual national addresses.
The original UN service identifies the text as automatic speech recognition,
not official records. Hash checks establish preservation, not transcription accuracy.

## Practical next steps

1. Inspect country identity and intervention boundaries, removing procedural and
   right-of-reply material if the evaluation target is national addresses only.
2. Reserve September 28 for a held-out test; use September 24–26 to develop the
   codebook and review additional training/calibration passages. Keep whole source
   records together; never split nearby paragraphs across training and test sets.
3. Review an initial 24–40 passages sampled across the eligible later-date records.
   Use a random sample for performance estimation; label any AI-enriched diagnostic
   sample separately. The owner can remain the sole reviewer/finalizer.
4. Check exact and near-duplicate text across partitions. Resolve the overlapping
   country according to the intended test: exclude it for the current strict
   country-disjoint validator, or explicitly revise that protocol if testing future
   speeches from previously seen countries is the operational goal.
5. Freeze the held-out labels, run a lexical baseline, then implement a bounded
   real-data training adapter and compare it with the selected small BERT candidate.
   Keep predictions audit-only while inspecting errors.

## Obstacles and limits

- The recovered candidates have no human relevance labels yet. Country metadata
  and automated transcripts also need a targeted quality check.
- The 24-label pilot is small and enriched; its balanced counts do not estimate
  prevalence or establish enough data for useful BERT fine-tuning.
- Event dates are later, but all archive material was collected on September 30.
  This can support a retrospective event-date holdout, not a claim that a model
  trained today predicted events in real time on September 24–28. Preserve both
  event and availability timestamps; never backdate review or availability.
- The current research fitting guard still accepts synthetic data only. The
  reviewed-data loader supports real audit attachments, not real model fitting.
- No new classifier performance, stance capability or diffusion result is claimed.

## Reproduce

With the existing private archive and reviewed revision, choose a new destination:

```powershell
python tools/recover_evaluation.py review-work/hlw review-work/ai-pilot-r2 review-work/new-evaluation
```

The destination is immutable. Raw text and individual labels stay outside Git.
Aggregate evidence and official source links are in
[the recovery record](../research/validation/i9/later-date-recovery.json).
