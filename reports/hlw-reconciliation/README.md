# General Debate transcript reconciliation

The 1 October 2026 upload contains 196 DOCX files representing 195 distinct
addresses already present in the repository's six General Debate transcripts.
It adds no previously missing address. Every filename's resolved entity and
stated date agree with its independently selected text match. All six retrieved
source JSON files exactly match the repository's historical SHA-256 hashes at
baseline commit `80dadf647e4c7ef82bd0ee5246498e3e67ff40d8`.

## Coverage and reconciliation

| Item | Result |
|---|---:|
| Uploaded Word documents | 196 |
| Distinct matched addresses | 195 |
| Member-state addresses | 191 |
| Observer-state addresses | 2 |
| EU address | 1 |
| Secretary-General address | 1 |
| Newly recovered addresses | 0 |
| Duplicate U.S. address variant | 1 |
| Exact extracted-text matches | 0 |
| Equal after case, punctuation and whitespace normalization | 1 (Switzerland) |
| Variants with token-level differences | 195 |
| Files with under 80% five-word sequence overlap | 22 |

These are General Debate address counts, not counts of all HLW interventions.
Coverage is reconciled against this uploaded set and the six archived meetings;
it is not independent proof of the complete official speaker roster.

The private delivery contains one source-backed record per address, 196 archived
upload text variants, per-file comparisons and token diffs, and a 195-row Shiny
CSV. The existing meeting corpus and published Cuba analysis remain unchanged.
Uploaded summaries, priority-theme counts and the data-center footer are excluded
from the source-backed corpus. Editorial material remains separately preserved.

## Material differences

- **United States:** two documents refer to the same source address. Their speech
  bodies are not identical (97.1% normalized token sequence similarity), and their
  summaries/theme counts also differ. Both variants are retained; the source-backed
  dataset counts the address once. Neither editorial variant is silently preferred.
- **Egypt:** the uploaded body ends at “Mr.” before the closing acknowledgement.
  The archived source supplies 59 subsequent normalized tokens in the main segment
  and a further 39-token adjacent continuation. The reconciled source-backed address
  includes both original segments, without rewriting the uploaded document.
- **Wording changes:** 195 uploads differ at the token level, beyond punctuation
  and formatting alone. These include small edits, apparent transcription repairs,
  added headings and more extensive rephrasing. Mauritania and Mozambique have
  the lowest normalized sequence similarities, 88.0% and 89.8%. Similarity measures
  do not establish which wording is correct; changed wording is not certified verbatim.
- **Separate interventions:** the 460 source segments reconcile to 196 segments
  used in 195 addresses (Egypt uses two), plus 26 replies, 230 procedural segments,
  six unattributed segments, a Palestine video introduction and a Cabo Verde
  language-switch fragment. All remain available, separately classified. The
  Cabo Verde fragment signals Creole speech but does not itself recover that speech.

The original sources are automatic transcripts, not official verbatim records.
Keeping them as the quotation baseline preserves auditability; it does not prove
that they are more accurate than an edited upload. Consequential wording should
be checked against audio or a submitted written statement before substitution.
Speaker names in the derived CSV come from uploaded metadata and are not
independently verified. Text provenance remains tied to original source segments.

## Method and validation

`tools/reconcile_addresses.py` uses only the Python standard library. It extracts
only content after the unique `Full Speech Text` heading, then matches against all
460 source segments using shared five-token sequences. Each accepted match must
have more than 50% upload five-gram overlap, exceed the runner-up overlap count
by more than twofold, and agree with separately resolved country and date metadata.
Exact text equality, normalized token equality, five-gram overlap and
`SequenceMatcher(autojunk=False)` similarity are reported separately. Token offsets
in the private diffs refer to normalized token arrays, not source character offsets.
The threshold is an identity-screening rule, not an accuracy or completeness claim.

Executed checks verified ZIP CRC, unique speech boundaries, nonempty bodies,
196 resolved country/date matches, six original source hashes, unique output IDs,
195 CSV rows, byte-for-byte source preservation after the documented Egypt join,
full 460-segment accounting, and output checksums. No R runtime is available in
this session, so Shiny acceptance and existing analytical outputs were not rerun.
The CSV was checked structurally against `un/ui/R/sources.R`.

Reproduce from the repository root, with the supplied archive and the six original
JSON files from the existing corpus archive (or public downloads matching the
recorded hashes):

```bash
python tools/reconcile_addresses.py /path/OneDrive_1_10-1-2026.zip \
  /path/raw review-work/reconciled
```

Use `shiny.csv` from the private output as the Shiny upload, with 22–28 September
2026 selected. Do not upload the entire delivery ZIP: it contains alternate text
versions that would duplicate addresses. For country-only analyses, filter
`canonical.json` to `entity_type == "member_state"`, or use the provided
`national.csv` containing 191 rows. Keep replies separate unless the question
explicitly covers them.

Uploaded source documents and full text variants are not committed to Git.
The private delivery includes the original ZIP, derived corpus, diffs, and hashes.
`comparison.csv` here contains metadata and metrics only. Prior frozen outputs
and manifests have not been changed.
