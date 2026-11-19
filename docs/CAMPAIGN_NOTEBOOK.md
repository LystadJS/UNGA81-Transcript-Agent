# Campaign outreach notebook

Open the [campaign notebook](https://lystadjs.github.io/un/transcript-agent/campaign-notebook.html)
from Meeting reports, the archive or Advanced analysis. This first campaign module
keeps user-entered outreach records in a browser session. It does not derive
campaign intentions from transcripts or infer votes from language.

## Work and save

Name the campaign and optionally enter its candidate/purpose, target body/seat,
user-entered date and campaign notes. Choose a country/territory, enter a lead
contact and apply its outreach record. Applying changes this session; **download
notebook JSON to save work**. Open that JSON to continue on another permitted
browser. There is no account, shared workspace, automatic device save or upload.
Closing, navigation or refresh can discard unsaved work; browser-supported
unsaved-work prompts are a last reminder, not a substitute for saving.

Each campaign file keeps one current record per registered place and one lead
contact field. Use notes for context. Edit updates that record; Remove asks before
removing it. It is not a multi-contact CRM or automatic history ledger. Keep dated
JSON snapshots separately if you need previous versions. New/Open also ask before
replacing unsaved applied changes or an unapplied country form. Keep and Escape
retain work. Unapplied form changes must be applied or discarded before export.

The existing geographic registry includes countries and territories, not an
eligible-voter roster. A record does not establish voting eligibility, verified
personal identity, an official government position or an actual ballot. Reported
support and conditional support remain user-entered accounts. There are no vote
predictions, majority calculations, invitations, messages or automatic reminders.
Follow-up dates are notebook fields only.

## Statuses and views

| Status | Meaning in this notebook |
| --- | --- |
| Not assessed | No outreach assessment entered; not neutrality or opposition |
| Outreach planned | User-recorded plan |
| Contacted | User-recorded contact |
| Support reported | Support reported to the user, not a verified vote |
| Conditional support reported | A conditional account requiring its context |
| Support declined | User-recorded decline, not an observed ballot |
| Unclear | Unresolved account |

Every status except Not assessed requires a status date. Dates are entered by the
user, from 1900 through 9998; past follow-ups can represent overdue work. Source /
conversation reference and country notes preserve context without authenticating
it. Counts describe complete geographic records, one per place, not votes or an
electorate. No missing country receives a default position.

Literal search, status and follow-up-on-or-before filters change the visible list.
They do not reduce summary counts or downloads. Empty follow-up dates do not match
a dated follow-up filter. Clear filters to recover the full list.

## Portable files

JSON uses `un.campaign-notebook.v1`, with campaign details and country entries.
Imports and compact JSON exports share a **1 MiB UTF-8** bound. Up to 250 distinct
registry labels are supported; the current catalog has 249. Required fields,
unique geography, status/date values, field limits, unsupported controls and
invalid UTF-8 are checked before replacement. A malformed or oversized file keeps
current work; later edits, source actions and cleared/newer file selections
supersede older reads and confirmations. No file authenticates its author.

All three downloads share a timestamp while the current preparation is unchanged.
Names omit campaign names and contact details. The timestamp is a preparation
marker, not a source date or integrity signature.

- **JSON** preserves complete campaign details and records for reopening. Check
  your browser's downloads before closing. A failed download start keeps dirty-work
  protection active.
- **Country CSV** contains every geographic row, campaign identifiers, contact
  details, status/date, follow-up, source reference and country notes. Campaign-level
  notes are excluded. Formula-shaped cells receive an apostrophe; JSON retains
  exact strings. Reading/exporting CSV does not save resumable work.
- **Reading HTML** contains complete campaign notes, status counts and all records,
  independently of filters. It is script-free and can be opened and printed without
  this application. Keep JSON separately; HTML cannot resume work. The workspace's
  native print view directs you to this full reading copy.

CSV/HTML also have a 1 MiB encoded-output bound. Refusals preserve work without
truncation. Files contain contact details and notes; review before sharing or
transferring under your organization's rules. Generated files belong in private
storage, not this public code repository or its Hugging Face archive.

## Personal R / Python use

These are ordinary UTF-8 CSV and JSON files, separate from the transcript pipeline.
For example, base R can read CSV with `read.csv("countries.csv", colClasses =
"character", check.names = FALSE, fileEncoding = "UTF-8")`; Python can use
`csv.DictReader` with `open("countries.csv", encoding="utf-8", newline="")`, or
`json.load` for exact JSON values. Treat spreadsheet-safety apostrophes as export
formatting; do not turn manual statuses into observed-vote labels or accepted
stance-model targets.

## Validation and remaining scope

Fictional contracts cover strict fields, duplicate identity, dates, exact 1 MiB
round-trips, CSV parsing/formula escaping, safe HTML and immutable updates.
Browser checks cover adding/editing/removing, file replay, unapplied/dirty work,
Keep/Escape, invalid UTF-8, stale/latest reads and confirmations, download failure,
complete exports versus filters, the full registry and mobile layout. They are
engineering tests, not actual diplomat, government-browser or spreadsheet-client
acceptance. Authenticated collaboration, multiple contacts per place, automatic
history, calendar integration, authoritative election eligibility/results and full
PowerElection CRM parity remain separate work. The transcript reader, model gates
and all 37 unopened reserved meetings remain unchanged.
