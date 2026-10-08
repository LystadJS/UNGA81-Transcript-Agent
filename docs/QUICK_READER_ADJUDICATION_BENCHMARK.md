# Expanded quick-reader adjudication benchmark — development only

**Status (8 October 2026):** complete 13-meeting expansion and source-linked, *assistant-provisional* benchmark. **No owner or independent-human gold labels have been supplied.** The existing seven-meeting QA and all 37 unopened reserved October 5–6 meetings are preserved. The results are **not** a representative accuracy estimate, and the fixed held-out protocol has not been evaluated or changed.

## Population and selection frozen before scoring

Use only cached original development corpus SHA256 `e8fb980cf638e2aef39d0ca3564836c6120201a059e806ccaaee3fd5cc4f593e`: 1,293 original source segments, 2,596 original partitions, 20 downloaded transcript-bearing development meetings on October 1–2, 2026 (October 3–4 contain no meetings in the frame). Exclude the seven meetings already covered by the metadata-stratified [first audit](MEETING_QUICK_READER_SAMPLE_AUDIT.md). **Inspect every one of the remaining 13 meetings** (923 source segments). This is a *census of the remaining development meetings*, not a randomized or out-of-sample evaluation.

Archive the pre-repair deterministic outputs before changing `site/meeting-quick-reader.js`. Bind every benchmark case to the original source-segment ID, SHA256, JSON pointer, and original UN meeting URL. Review the 20 original country–issue predictions; choose up to four additional *withheld*, issue-bearing, recorded-country source segments per meeting by a fixed SHA256 rank (`qr-bench-abstention-2026-10-08|source_id`) excluding originally emitted evidence parents; and separately preselect 27 named source-context anchors across all 13 meetings. These samples deliberately overrepresent borderline cases. Reviewers must not treat source-segment records as authenticated speeches or people.

The private checkpoint contains both the pre-repair output and an independent, source-linked review file. The public repository retains reusable code, methodology, tests, and **aggregate-only** validation, not private transcript excerpts, annotations, or the embedded-source offline review interface.

## Four separate metrics and honest denominators

| Measure | Unit and denominator | What it does **not** establish |
|---|---|---|
| **Attribution precision** | Original emitted country–issue entries with a reviewable individual-country / collective / unresolved capacity decision | Speaker identity or official government endorsement |
| **Stance precision** | The same emitted entries, scored separately for an explicit action and the *correct, nearby policy object* | Agreement on a whole issue, a proposition-level stance across all speeches, or recall |
| **Specific context coverage** | Curated, original-source named anchors; count covered only when the term appears in the quick-reader *opening narrative or source-linked procedural agenda cues*. Meeting title and generic theme chips do not count | All salient topics covered; certified formal agenda, or broader semantic paraphrase coverage |
| **Abstention correctness** | Reproducibly selected issue-bearing source-segment **withholds**, excluding uncertain labels from assessable denominator | Population recall, a country abstaining from a vote, or proof withheld cases contain no stance |

Also report **joint attribution-and-stance precision** and **post-correction same-development diagnostic**, always explicitly not independent testing. Output `null`, not 1 or 0, when a task has no assessed examples. Report all unresolved/unreviewed cases and every excluded unit. The unique segment/meeting units are dependent and cannot provide ordinary independent binomial confidence intervals without additional design.

## Provisional adjudication findings, original code

| Source-linked measure | Assistant-provisional audit result |
|---|---:|
| Individual-country attribution | **19/20** assessed candidate entries (95%) |
| Correct issue-specific expressed action/object | **15/20** (75%) |
| Joint individual attribution and correct action/object | **14/20** (70%) |
| Specific opening context anchors covered | **7/27** (25.9%) |
| Appropriate withholds in 36-case sample | **16/28** assessable; 12 possible missed expressions; 8 uncertain |

The first two percentages overlap in units but answer different questions. The repaired version retains **14/14** of the assistant-adjudicated jointly supportable entries in **these same inspected meetings**. That last fraction is **in-sample repair verification, not a new precision measurement** and must never be reported as 100% general model accuracy. There are **226** source-segment candidates for the withheld issue-bearing pool under the declared screening rule; only **36** are sampled for contextual adjudication. No global false-negative/recall rate follows.

### Material cases

- A Cuba source segment (`ga/c3/81/1#11`) says the speaker is delivering a collective statement on behalf of a longer group. The earlier rule missed the *“honor of delivering”* construction and wrongly emitted an individual-country entry. The revised group detector withholds it.
- Expressions welcoming a human-rights report or its *focus* are not automatically endorsements of human-rights policy. A reference to *international humanitarian law* is not a humanitarian-aid stance; concern about a sanctioned person addressing a meeting is not a stance on sanctions. These five action/object false matches are withheld after the repair.
- The untouched additional sample reveals many meaningful procedural introductions, briefings, and independently stated subjects that do not appear among the existing two generic synopsis paragraphs or maximum two agenda cues. The **7/27** anchored coverage finding is an explicit gap, not a missing source. The next version should add scalable *specific-topic orientation* without claiming an adopted formal agenda, and should be tested on a separately preselected development subset.
- The 36 withheld source segments include both correctly conservative cases (press speakers, collective interventions, quoted draft wording) and potentially missed nationally attributed statements. The abstention metric deliberately records both and retains eight unresolved cases. A pending classification is not coded as a negative.

## Reusable review contract and artifacts

`research/reference_tests/quick_reader_benchmark.cjs` builds a **source-hash-bound** benchmark from the exact private corpus, archived pre-correction quick-reader outputs, and immutable reviewer-selected context anchors. `score` enforces exact ID/hashes, complete per-case category labels, source-tied notes, and separate denominators. The offline browser interface created by `render_adjudication_view.cjs` displays original evidence and *assistant suggestions in a separate column*. Its answer fields begin blank; future reviewers can export/resume partial decisions. No server, external AI, background upload, or external API is required. A human review needs an affirmative reviewer name/time/confirmation and the explicit scoring flag; assistant decisions are never silently rebranded as human labels.

```bash
node research/reference_tests/quick_reader_benchmark.cjs prepare \
  PRIVATE_DEVELOPMENT_CORPUS.json SAVED_PRE_CORRECTION_REPORTS.json \
  PRIVATE_CONTEXT_ANCHORS.json NEW_DIRECTORY
node research/reference_tests/quick_reader_benchmark.cjs score \
  NEW_DIRECTORY/benchmark.json REVIEW_FILE.json NEW_METRICS.json
# Only when an actual reviewer deliberately submitted their own source-checked choices:
node research/reference_tests/quick_reader_benchmark.cjs score \
  NEW_DIRECTORY/benchmark.json OWNER_REVIEW.json NEW_OWNER_METRICS.json --human
node research/reference_tests/render_adjudication_view.cjs \
  NEW_DIRECTORY/benchmark.json PROVISIONAL_REVIEW.json NEW_OFFLINE_REVIEW.html
node research/reference_tests/test_quick_reader_benchmark.cjs
```

The exact source parser, model fits, original responses, prior human pilot, release gates, and original `evaluation-lock.json` are unchanged. **The 37 reserved transcripts have not been requested, read, scored, or opened.** Future human adjudication should address disagreement and unresolved labels before a policy-facing rate is cited; fresh separately authorized data are needed for a genuine independent accuracy estimate.
