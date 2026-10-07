# Source audio and smaller-passage pilot

The [review interface](https://lystadjs.github.io/un/transcript-agent/passage-pilot.html)
accepts a private packet locally. The prepared offline HTML contains the same
interface, original parent text and twelve embedded clips; it needs no server.
Neither interface sends imported text, audio or choices to a remote service.

## Current state — 7 October 2026

All 24 owner choices have been saved and validated against the exact packet.
Twelve passages are included with their proposed offsets unchanged. The audio
decisions are six supported, five discrepancies and one unclear; no included
passage overlaps a disputed or unclear span. The original corpus and all 460
prior passage-type decisions remain unchanged. Individual notes and clips remain
local. See [reviewed import and correction provenance](REVIEWED_UNITS.md).

## Preparation record — 5 October 2026

Five original UN transcript snapshots matched the saved corpus hashes exactly.
Their identified UN Web TV recordings expose English audio/interpretation tracks.
Twelve bounded clips were retrieved, hashed and decoded, then compared using the
existing local `Systran/faster-whisper-base.en` model at revision
`3d3d5dee26484f91867d81cb899cfcf72b96be6c` (CPU/int8, beam 5, VAD enabled,
no previous-text conditioning). The check records the actual model-weight hash.

**The preparation findings below are machine comparisons, preceding owner review.**
The second recognizer makes additional errors. None of its proposed wording has
been substituted into the source. At preparation, all twelve concerns awaited a
listening decision; unresolved was a valid choice. Agreement between recognizers is not
independent human corroboration, and disagreement does not establish which is right.

| Concern | Comparison finding | Present status |
|---|---|---|
| A01, chair transition | No speech recognized around the unrelated entertainment wording. Silence from a recognizer does not establish absence in the recording. | Unresolved |
| A02, Vanuatu name | The second recognizer uses Vanuatu, but produces a different session-number error. | Candidate discrepancy |
| A03, Vanuatu wording about coercion | Both transcripts render the suspect word as cohesion. | Unresolved; do not correct from plausibility |
| A04, Vanuatu reports/benefits | Both versions contain broken wording; their proposed names differ. | Unresolved |
| A05, Vanuatu small-state phrase | The new version includes additional words but still reads awkwardly. | Candidate discrepancy |
| A06, Vanuatu name | The second recognizer also fails to recover a reliable name. | Unresolved |
| A07, Vanuatu session number | Neither rendition gives reliable wording. | Unresolved |
| A08, Kyrgyzstan introductory name | Another name variant appears. | Unresolved |
| A09, Kyrgyzstan anniversary | Both versions say 31st. This agreement does not authorize changing the number to match an expected anniversary. | Unresolved |
| A10, Rwanda introductory names | Additional inconsistent name variants appear. | Unresolved |
| A11, Rwanda Charter anniversary | The new transcript says 80 years where the saved text says eight years. | Candidate discrepancy |
| A12, Azerbaijan connectivity | The new transcript says unimpeded, but its geographic names remain unreliable. | Candidate discrepancy |

Exact source IDs, sentence indices and concerns are in
[the retrieval plan](audio-concerns-plan.json). Clip intervals, hashes and bounded
findings are in [the verification record](audio-verification.json). Full text,
clips, fresh machine transcripts and individual review decisions remain local.
The former suspected-transcription classification and all 460 saved type choices
remain unchanged.

## Pilot design

Twelve proposals come from Palau, Fiji and Vanuatu, the three leading substantive
membership-change examples. Each complete parent is first divided at existing
source-sentence boundaries, aiming for 180 words and avoiding more than 250 when
possible. Long individual sentences remain whole; final chunks can be short.
Four evenly spaced chunks are selected from each parent, including the first and
last. This purposive boundary test is neither a representative sample nor a
complete partition of those speeches. Introductory and closing chunks deliberately
test whether more context is needed. No thematic, relevance or stance labels are
assigned and no new clustering is fitted from the unreviewed proposals.

| Parent | Original words | All candidate chunks | Selected chunks | Selected words |
|---|---:|---:|---:|---:|
| Palau | 1,599 | 9 | 4 | 635 |
| Fiji | 2,403 | 13 | 4 | 702 |
| Vanuatu | 3,918 | 21 | 4 | 698 |

Each proposed excerpt is an exact slice of the saved parent text. Offsets are
zero-based Unicode code points with an exclusive end. The finalized derivative
also records UTF-8 byte offsets, the original parent ID, source URL, raw-source
hash, parent-text hash, corpus hash and derived-text hash. The unit ID includes
the parent, offsets and a hash prefix. No whitespace normalization, corrected
wording or Unicode normalization is applied. Text offsets refer to the saved
parent string, not to HTML, serialized JSON bytes or the audio clock.

## Review and finish

1. Open the prepared `review.html`, or load `speech-pilot.json` in the public
   interface. Enter your reviewer name or role. No choices are preselected.
2. In **Check audio**, listen to each clip and compare the saved wording. Record
   supported, differs, or unresolved. Supported/differs requires a listening
   attestation; a discrepancy also requires a note. The optional machine text is
   a comparison aid, never a default decision.
3. In **Review passages**, read each excerpt and its parent context. Adjust the
   offsets directly or select a span in the original speech and choose **Use
   selected text**. Record include, exclude, or needs further work.
4. Choose **Save review choices**. Keep the downloaded
   `speech-pilot-review.json` with the packet. Save before closing; choices are
   not silently persisted to a shared browser or uploaded.
5. After all 24 decisions are recorded, **Export reviewed passages** creates an
   audit dataset. Disputed/unresolved audio spans and items needing further work
   are withheld. Approved overlapping passages within a parent are rejected,
   requiring boundary adjustment or exclusion. An unresolved audio concern
   elsewhere does not disqualify a non-overlapping unit.

Boundary approval is not full factual or audio verification of a passage. This
check covers only the twelve selected concerns; other transcription errors may
remain. No reviewer may infer a source correction solely from a plausible name,
date or political claim. A future correction needs a separately versioned text
and an explicit alignment to the preserved original.

The dataset has its own `un.reviewed-speech-units.v1` schema. It cannot silently
replace the browser's original transcript corpus. Its audit status remains
separate from the frozen D1 pipeline and from existing classifier evaluation.
Any later model comparison must keep related units in their parent speech and
meeting group. Count parent speeches for coverage; twelve excerpts are not twelve
independent national addresses. Retain the full-parent baseline and disclose
omitted text before comparing representations or assigning thematic labels.

## Reproduce and validate

The retrieval tool consumes unchanged source JSON plus media metadata produced
by the existing `yt-dlp` recovery path. Its optional dependencies are pinned in
`tools/hlw-recovery-requirements.txt`. It requests eight seconds of context on
either side, limits each clip to 90 seconds, checks decoded duration and records
failures without asserting verification.

```text
python tools/check_audio_concerns.py corpus.json source-metadata docs/audio-concerns-plan.json models new-audio-output
python tools/prepare_speech_pilot.py corpus.json reviewed-mask.json source-metadata new-audio-output/audio-checks.json new-pilot-output
node tools/test_speech_pilot.cjs new-pilot-output/speech-pilot.json
node tools/test_speech_pilot_ui.cjs new-pilot-output/review.html new-pilot-output/speech-pilot.json browser-test-output
node tools/finalize_speech_pilot.cjs new-pilot-output/speech-pilot.json speech-pilot-review.json new-reviewed-output
```

The importer rejects changed parent text, broken slice/audio hashes, mismatched
packet identity, invalid offsets, duplicate/unknown decisions, missing reviewer
provenance, future timestamps and unconfirmed listening claims. Tests use clearly
marked engineering choices outside the actual review packet; these are not owner
decisions. See [validation](speech-pilot-validation.json).

Next: build saved-run comparisons of the approved units and their full-parent
baseline. Reconcile the unclear audio item and any correction wording separately.
Broader methodological claims still require more independent meetings. The earlier
[preparation validation](speech-pilot-validation.json) remains a historical record;
[reviewed import validation](reviewed-units-validation.json) records current acceptance.
