# Individual-meeting analysis

The report builder now offers **Choose what to analyze → One individual meeting**.
The user needs only the date, not a meeting URL, committee code or transcript ID.

## User workflow

1. Select **One individual meeting** and enter its date.
2. Select **Find meetings**. The complete paginated UN transcript inventory for
   that date is listed by meeting title. Meetings whose transcripts are not yet
   listed remain visible but cannot be selected for analysis.
3. Choose a meeting. The form sets the reporting date, unrestricted meeting scope
   and all speaker regions. Leave Topic blank to analyze all available English
   passages from that meeting, or add a topic to narrow them explicitly.
4. Select the existing descriptive, clustering or NMF methods, then use
   **Collect transcripts & generate report**. Review the source coverage and
   download the existing HTML report, transcript JSON, analysis JSON and CSVs.

The date defaults to the current New York date. Selecting a meeting does not
submit a request until the user runs the report. Meeting discovery downloads
inventory metadata only. Collection rechecks the complete inventory, then
retrieves only the selected meeting's transcript; it does not download all
meetings and merely hide the others afterward.

## Source contract

`meeting-picker-core.js` validates the calendar date, each returned meeting ID,
source URLs, pagination, total counts, dates, duplicate IDs and transcript flags.
An incomplete or failed inventory is an error, not an empty list. An actual empty
inventory is described as “no meetings listed”; publication can lag proceedings.

The selected meeting is represented by `meeting_slug` and `meeting_date` in the
analysis parameters. A single-meeting request requires one exact date. The
collector verifies that the selected ID still exists once and only once in the
complete inventory. If the source changes, it stops and asks the user to search
again. No different meeting is substituted.

Only the selected meeting is downloaded. Collection metadata records
`selection_mode: single_meeting`, the selected ID, title and date, the full daily
inventory count, and the selected-meeting count. Every collected segment carries
`meeting_slug`. Analysis filters the exact identity before deduplication and topic
matching, so another same-day meeting cannot affect the denominator. Reports
identify the meeting explicitly, and exported transcript/analysis JSON retains
its provenance and coverage.

A transcript-present inventory flag is not a guarantee of usable English text.
The existing collector still checks transcript identity/date, availability,
language, empty text and failed responses. Those statuses remain visible. The
interface does not infer availability from a meeting title or claim to cover UN
meetings absent from this transcript service.

## Analytical limitations

An individual meeting is one source group, even when it contains many passages
or speakers. Existing meeting-group refit stability therefore remains withheld
when fewer than three groups exist. This does not block descriptive summaries or
an otherwise supported clustering/NMF fit. Too few usable passages still withhold
the model under its original bounds. Neither source segmentation nor adding more
iterations creates independent meetings or validates a diplomatic grouping.

The saved single-meeting corpus can be opened in the latent comparison workspace.
It contains only that meeting's collected records; optional settings comparisons
remain exploratory. The new chooser does not activate daily scheduling, send
email, modify the frozen R pipeline, apply audio corrections, or supply stance
labels.

## State and privacy

Changing the date or selection clears the previous meeting choice and invalidates
completed report exports. Cancelled discovery releases no partial list. The
existing report cancellation and stale-result safeguards continue to apply.
Imported-file mode returns to date/scope selection rather than silently claiming
that an imported corpus has been freshly verified against a live meeting.

Only date queries and selected public source paths are sent to the UN service.
Topic filtering and numerical analysis remain on the user's device. No account,
proxy, model API or new hosted processing service is introduced.

## Validation

```sh
node tools/test_meeting_picker.cjs
NODE_PATH=/path/to/qa/node_modules PW_CHANNEL=chrome node tools/test_meeting_picker_ui.cjs _site new-meeting-validation
```

The deterministic suite checks complete pagination, no premature transcript
retrieval, single-ID filtering before deduplication, missing/replaced meetings,
invalid dates, changed counts, duplicate IDs, external URLs, cancellation,
unavailable/empty/non-English transcripts and source metadata. Browser acceptance
uses clearly labeled synthetic inventory responses to exercise the actual UI,
collector, numerical worker and exports, including desktop/mobile overflow.

A mocked browser run verifies software behavior, not live UN service availability.
Any live source check is recorded separately with its actual date and outcome.

## Live source route correction — 7 October 2026

The live inventory includes canonical routes such as `hrc/63/25` and `ced/593`,
not only `asset/...` video routes. Browser 1.12.1 accepts safe multi-segment IDs
from the verified UN inventory, still rejects traversal/queries/arbitrary URLs,
and rechecks the exact selected ID at collection. The regression fixtures now
include HRC and treaty-body routes. The initial asset-only assumption was found
by the separate live check, not silently classified as missing transcript data.

## Opening quick reader — October 2026

A selected individual meeting now opens with **At a glance** before the model
figures.  The section is computed on-device from all retrieved English source
segments of that exact meeting, even if an optional Topic narrows the deeper
statistical analysis.  The HTML export, print view, and analysis JSON retain
the same opening synopsis.  Range reports are unaffected.

The opening prose is deterministic, intentionally concise, and calibrated to the
JSL Writing Voice requirements: one clear claim per paragraph, concrete evidence,
and immediate limitations.  No third-party generative AI API, remote classifier,
or token-billed service is required.  Fixed categories count source segments,
not unique speakers or verified speeches, and direct source links permit rapid
checking.  These subject categories are **not** the official meeting agenda.

The snapshot reports recorded source segments, median segment length, distinct
registry-mapped country labels, and unresolved country segments.  Country-linked
expressions are classified conservatively as *support or advocacy expressed*,
*concern or opposition expressed*, or *mixed or qualified*, only when a recorded
country-affiliated source contains a first-person evaluative clause about the
subject.  A country name in a third-party statement, a topic keyword, a speech
by a presiding official, or an unmapped affiliation cannot establish a country
position.  The wording remains provisional and must be inspected in context.

The collector now retains bounded **original speaker function, group,
affiliation, and optional source-provided name/ID** fields.  It never derives a
person ID or confirms the authority of a speaker.  Affiliation + function is a
coarse research proxy, not person identity.  Canonical meeting paths support
institutional *series* identification, not formal agenda verification.  Older
imported data lacking these fields remains usable; its country positions may
be withheld for missing attribution.

Engineering tests cover all-matching and topic-filtered report pathways, source
links, no-attribution and procedural cases, role and genre cautions, empty
transcripts, mixed statements, quote/third-party resistance, and HTML escaping.
The **development-only speaker/agenda audit** uses cached 1–2 October records,
rejects all reserved dates, and keeps source-linked individual records private;
only anonymized aggregate coverage may enter the public repository.  All
37 reserved 5–6 October transcripts remain unopened and the SHA256-sealed
evaluation protocol unchanged.
