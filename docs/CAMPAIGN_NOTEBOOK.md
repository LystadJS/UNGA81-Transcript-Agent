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
removing it. Dated interaction logs can name different contacts; reusable profiles keep
current details separately. Automatic change history is not provided. Keep dated JSON snapshots
separately if you need previous versions. New/Open also ask before
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
They do not reduce summary counts or downloads, including contact transfers. Empty follow-up dates do not match
a dated follow-up filter. Clear filters to recover the full list.

## Reusable contact profiles

Open **Reusable contact profiles** while adding or editing a country. Enter a
required name and optional role, address and notes. Add or Update stages the
profile in the country form; Apply commits the country form in this session;
JSON saves it. Unapplied profile fields must be added, updated or cleared first.
Keep/Escape preserves those fields. Country-form cancellation discards all its
unapplied changes, including staged profiles.

Profiles have stable local IDs, not verified personal identities. Different
profiles may share a name. Each place supports up to 25 profiles; the notebook
supports 1,000 total within the same 1 MiB budget. Profiles are not automatically
created from an old lead field or conversation; no identities are inferred.

**Use as lead** copies name, role and address into the country form. **Use for
interaction** copies name and address into the new interaction fields, keeping
its date, notes and reference. Both ask before overwriting populated destination
fields. These are copies, not live links. Later profile edits/removal do not
rewrite lead fields or earlier interaction snapshots and do not change status
counts. Remove asks before removing the profile and clearing its own editing
fields; copied details remain elsewhere. Apply and save JSON to keep removals.
No contact is messaged, authenticated or synchronized with an external directory.

## Calendar copy of country follow-ups

Open **Calendar copy of country follow-ups** under campaign files. Download the
`.ics` file and import it yourself into a permitted calendar. Each country with
an explicit follow-up date contributes one all-day entry. Undated records are
excluded; the optional on-or-before cutoff narrows that calendar scope. List
search, status and due-date filters do not change it. Dates are not invented,
rescheduled or inferred from contact/status dates; past dates remain past dates.

The default copy includes the campaign title, country and follow-up date, not
lead/profile fields, conversations, campaign-level notes, country notes or source
references. **Include country notes and source references** adds only those two
fields. They can contain private details; review before importing or sharing.
The calendar file contains no attendees, organizer, invitations or alarms. It
marks entries private/transparent, but the receiving client controls visibility,
alerts, duplicates and import behavior. Actual government calendar-client
acceptance remains unrecorded.

This is a reading copy, not calendar synchronization or a notebook save. Later
notebook edits/removals do not update/delete imported entries. A repeated import
can duplicate entries; IDs are stable within one prepared notebook snapshot,
not a cross-version synchronization contract. Retain full notebook JSON to
resume work. Calendar options are excluded from saved JSON and reset on New/Open.

Apply/discard pending country forms before export. Changes to notebook data,
calendar options or newer source actions supersede asynchronous preparation;
failed starts keep current work and its unsaved protection. Calendar downloads
never mark the notebook saved. The complete encoded file shares the 1 MiB bound
without truncation. Missing/older calendar modules disable only this reading
copy, leaving ordinary saves and CSV exports available. The existing report-review
calendar keeps its separate source-bound scope and 25 MB budget.

## Reviewed contact transfer

Open **Transfer contact profiles between notebooks** under campaign files.
Download **contact-only JSON** from the source notebook, then import it into the
target notebook. This separate format contains country labels and complete
profiles (including contact notes); it excludes campaign title/notes, current
lead/status fields, country notes and conversation history. It does not save
resumable campaign work. Keep full notebook JSON separately. No upload or account
connection occurs; review contact details/notes before sharing the file.

Apply or discard pending country-form changes first. Import checks the complete
file and resulting notebook before offering a preview grouped by country. Expand
each group to inspect names, roles, addresses and contact notes. Keep/Escape
cancels without changing work; proceeding adds only the reviewed new profiles.
Identical saved IDs within a country are skipped. Different contents under an
existing ID refuse the whole import; resolve that contact manually. Matching
names/addresses under different IDs are not merged or treated as verified identity.

New country records start **Not assessed**, with empty lead fields and no invented
history. Existing statuses, leads, notes, conversations, filters and campaign
settings stay intact. An unchanged country edit form refreshes its profiles so a
later Apply retains additions. No-op replays do not mark work dirty. Imports that
exceed per-country, total or complete-state 1 MiB limits refuse without partial
changes. Newer edits, file selections, cleared selections and source actions
supersede old reads/preview decisions. Malformed files retain current work.

Contact transfers use `un.campaign-contacts.v1`: exactly `schema` and `entries`,
with exactly `country` and `contacts` per group. Profiles use the same strict
fields as notebook v3. Both raw file and normalized transfer are bounded to 1 MiB;
the full resulting notebook must also fit its own 1 MiB budget. Complete notebooks,
CSV reading copies and HTML are not contact-transfer inputs. Import is an explicit
append operation, not synchronization, authentication or automatic overwriting.
The contact-only filename ends `-contacts.json`; full notebook files do not.

## Dated outreach log

While adding or editing a country record, open **Dated outreach log**. Enter the
interaction date, channel, contact/address if known, required notes and optional
source reference. **Add to country form** stages that interaction. Then **Apply
country record** commits the form in this session; download JSON to save it.
Unadded interaction fields must be added or discarded before applying. Discarding
those fields keeps already added interactions; discarding the country form drops
all its unapplied changes. Existing records are kept until Apply succeeds.

Interactions are sorted by user-entered date and stable ID, not insertion order.
Up to 100 interactions per place and 1,000 per notebook share the existing 1 MiB
budget. The contact fields are snapshots for that interaction, not authenticated
or live links to profiles. Logging a conversation does not change the current
outreach status, status date, lead contact, follow-up date or status counts.
Search includes logged contacts and notes; list filters still do not reduce exports. Choose **Earliest follow-up first** to work through dated records before undated ones, or **Most recent interaction first** to order by each country's latest manually logged interaction date. Countries A–Z break ties. **Follow-up date** can show only dated or undated records; combining undated with a cutoff yields no matches. These controls change only the list, preserve unapplied edits and do not mark work unsaved. New/Open/Clear restore all records in country order. No date, reminder, status change or outreach history is inferred.

Remove asks before removing an interaction from the country form. Keep/Escape and
newer edits preserve it. Apply and save JSON to keep a removal. To correct a log,
remove it explicitly and add the corrected entry; this is a manual notebook, not
an immutable audit trail. Deleting a whole country also deletes its logs from this
session. Downloaded versions remain separate. No earlier conversations or edits
are reconstructed from status dates or old files; an empty log means history is
unknown, not that no outreach occurred.

## Portable files

JSON writes `un.campaign-notebook.v3`, with campaign details, country entries,
`contacts` and `interactions` arrays. It reads strict v1 and v2 files: v1 gains empty
logs and profiles; v2 retains exact logs and gains empty profiles. No past events
or identities are invented. Contact fields are `id`, `name`, `role`, `email`, and
`notes`. The migrated v3 state must also fit 1 MiB; a densely filled older file can
exceed that bound after adding empty arrays and is refused
without changing current work. Shorten such a file in its original version before
migrating. New saves use v3; older application versions cannot read
them. Interaction fields are `id`, `date`, `kind`, `contact`, `email`, `summary`, and
`reference`. IDs identify records within a country; they do not authenticate events.
Imports and compact JSON exports share a **1 MiB UTF-8** bound. Up to 250 distinct
registry labels are supported; the current catalog has 249. Required fields,
unique geography, status/date values, field limits, unsupported controls and
invalid UTF-8 are checked before replacement. A malformed or oversized file keeps
current work; later edits, source actions and cleared/newer file selections
supersede older reads and confirmations. No file authenticates its author.

Notebook exports share a timestamp while the current preparation is unchanged.
Names omit campaign names and contact details. The timestamp is a preparation
marker, not a source date or integrity signature.

- **JSON** preserves complete campaign details and records for reopening. Check
  your browser's downloads before closing. A failed download start keeps dirty-work
  protection active.
- **Country CSV** contains every geographic row, campaign identifiers, contact
  details, status/date, follow-up, source reference and country notes. Campaign-level
  notes are excluded. Formula-shaped cells receive an apostrophe; JSON retains
  exact strings. Country CSV excludes profiles and interaction logs. Reading/exporting CSV does
  not save resumable work.
- **Contact CSV** contains every profile across all countries, with campaign title,
  country, stable profile ID, name, role, address and contact notes. It excludes
  country/campaign notes, statuses and interaction history. Empty profile lists
  contribute no rows; formula protection applies.
- **Interaction CSV** contains every logged interaction across all country records,
  with campaign title, country, ID, date, channel, contact/address, notes and source
  reference. It excludes campaign-level notes, current country status and country
  notes; use the country CSV separately. A country with no logs has no interaction
  row. Formula protection applies; these are user-entered events, not verified facts.
- **Reading HTML** contains complete campaign notes, status counts, all records, profiles and their complete interaction logs,
  independently of filters. It is script-free and can be opened and printed without
  this application. Keep JSON separately; HTML cannot resume work. The workspace's
  native print view directs you to this full reading copy.

All CSV formats and HTML also have a 1 MiB encoded-output bound. Refusals preserve work without
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
round-trips, all CSV formats with independent parsing/formula escaping, safe HTML,
v1/v2-to-v3 migration without fabricated logs/profiles, profile identity/limits, interaction dates/IDs/limits and immutable updates, private-scope contact transfers, same-ID conflict refusal,
no-op replay and complete-state merge budgets.
Browser checks cover adding/editing/removing, file replay, unapplied/dirty work,
Keep/Escape, invalid UTF-8, stale/latest reads and confirmations, download failure,
complete exports versus filters, pending interaction fields, Keep/remove/stale
interaction confirmations, multiple contact snapshots, the full registry and mobile layout. They are
engineering tests, not actual diplomat, government-browser or spreadsheet-client
acceptance. Authenticated collaboration, cross-notebook contact synchronization, automatic change
history, connected calendar synchronization, authoritative election eligibility/results and full
PowerElection CRM parity remain separate work. The transcript reader, model gates
and all 37 unopened reserved meetings remain unchanged.
