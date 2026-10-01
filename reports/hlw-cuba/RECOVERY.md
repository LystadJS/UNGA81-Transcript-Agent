# Recovery of 41 missing HLW transcript pages

Open [the recovery supplement](recovery.html) for the current event-level status,
linked text, and priority. `recovery.json` is the machine-readable ledger and
`recovery-check.json` records the validation actually performed. Counts in the
original Cuba brief remain the original collection baseline.

The completed pass provides alternative caption/transcription text for all 41
entries: 18 publisher caption files and 23 local machine-transcription drafts.
It also preserves six individual published statements, one organizer outcome
document, and one additional organizer-provided automatic transcript. Eighteen
recordings show probable overlap with existing full-day material. Three have
duration discrepancies, and nine local drafts have additional quality-review
flags; all automatic text remains unreviewed. The two literal Cuba candidate
cues concern disaster logistics and Caribbean–Africa investment links. They are
surfaced for review, not added to the original brief or interpreted as embargo
positions. The 15 unavailable background proceedings are outside this pass.

## Source order and coverage

Each of the 41 broader-HLW entries received an event-specific written-source
search. Organizer/delegation publications take precedence for the individual
statements they contain. Event descriptions, agendas, press summaries, speeches
from a different event, and 2025 editions do not fill a 2026 transcript gap.
Six complete individual statements were archived and extracted with recorded
offsets and hashes: the PGA on social business; UNOPS and UNCTAD on the grids accelerator;
Russia on demographic resilience; the ICRC-hosted joint IHL statement; and UN
Women opening remarks on feminist multilateralism. None is presented as the
complete record of a multi-speaker event. The organizer's 22 September GLN
communiqué is archived separately as an outcome document, not a transcript.
UNOPS marks its text check against
delivery; the PGA and UN Women label their publications as delivered.
The ILO Live organizer page additionally provides a downloadable automatic
transcript of the workplace financial-health event. Its original DOCX and
extracted text are retained separately, including the WIPO Speech-to-Text
disclaimer. This is not a prepared speech or a human-reviewed transcript and
is not counted among the six published individual statements.
The UNCTAD statement was captured from the browser's rendered visible text
after direct HTTP retrieval returned 403. Its ledger explicitly identifies this
capture method; its source hash is a hash of that saved text capture, not the
original HTTP response. The collector preserves this cached capture. A fresh
retrieval may require opening the publisher page in a browser again.

Public English captions were retrieved from UN Web TV for 18 event recordings.
These remain publisher captions, with their automatic/unreviewed status visible.
They are not the missing UN Transcripts JSON and do not change that endpoint's
availability flag. Seventeen show substantial seven-word-sequence overlap with
full-day SDG Media Zone transcripts already collected. The overlap screening is
not an exact timestamp alignment or proof of complete event coverage. In
particular, the Early Warnings clip is indexed on 23 September but strongly
matches the 22 September full-day record; retain both source dates pending
reconciliation.

For recordings without English captions, local speech recognition uses the
explicitly English audio/interpretation track and the pinned revision of
`Systran/faster-whisper-base.en` recorded in each artifact. This speech model is
separate from the approved BERT text checkpoint and does not change model-release
gates. Processing uses CPU int8, beam size 5, voice-activity detection and no
previous-text conditioning. Long-recording jobs checkpoint 30-minute chunks.
All outputs say **UNREVIEWED MACHINE TRANSCRIPTION**. They carry timestamps,
audio hashes and model revision; speaker names and diplomatic positions are not
inferred. Automatic transcription may omit or mistranscribe material. A draft
without the word Cuba is not evidence that Cuba was never discussed.
The report flags cues with average log probability below -1 or compression
ratio above 2.4 for audio review. These are triage heuristics, not an accuracy
estimate. An English track label does not independently establish that every
speaker is speaking English or that interpretation is audible throughout.

Priority 1 covers Latin American/regional dialogue and selected humanitarian,
health, demographic and multilateral discussions adjacent to the Cuba inquiry.
Priority 2 covers other related regional and development events; Priority 3
covers the remaining events. This is editorial work ordering, not a model score
or assertion that an event contains Cuba-related material. All 41 remain in scope.

## Reproduce

Use a separate environment with `tools/hlw-recovery-requirements.txt`. From the
repository root, with the original local collection present:

```powershell
python tools/collect_hlw_written.py review-work/hlw-recovery/written
python tools/recover_hlw.py review-work/hlw/coverage.json review-work/hlw-recovery
python tools/transcribe_hlw.py review-work/hlw-recovery ../recovery-models EVENT_ID
python tools/report_hlw_recovery.py review-work/hlw review-work/hlw-recovery reports/hlw-cuba
python tools/check_hlw_recovery.py reports/hlw-cuba
python tools/package_hlw_recovery.py review-work/hlw-recovery reports/hlw-cuba C:\short\hlw-recovery.zip
```

`EVENT_ID` is the stable 12-character archive identifier in the ledger. Pass
multiple identifiers to process a sequence. Finished ASR artifacts are reused;
to change model settings, use a fresh recovery directory. Written-source raw
pages, searches, captions, audio, and intermediate records stay in the ignored
`review-work/hlw-recovery` directory. The supplement exposes readable source
texts and provenance, while the delivery package preserves raw caption and ASR
records. It excludes audio, model weights, and temporary signed media URLs.

Validation checks hashes, nonempty timestamped text, timestamp bounds, source
types, complete 41-ID accounting, and local report links. It does not constitute
human review or measure transcription accuracy. The supplement's Cuba screen
is a literal candidate check for Cuba/Cuban/Havana/Helms–Burton, separate from
the original eight-topic R workflow; it does not release a revised policy brief.

## Recommended next steps

1. Review any new Cuba candidate cues against the linked recording and prefer
   published speaker text where available.
2. Reconcile duration and date discrepancies and verify clip-to-parent coverage.
3. Merge only distinct, appropriately labeled passages into a new analysis run;
   keep the original baseline and its audit records intact.
