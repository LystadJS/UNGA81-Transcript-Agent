# Meeting-first reporting

The immediate product target is a PowerTranscript-like reporting workflow, implemented independently: select proceedings, search their evidence, apply mission report templates, and export documented results. Research CSVs and evaluated stance tracking remain distinct capabilities. This is not a claim of equivalent vendor performance or access to proprietary code or weights.

## Choose the right export

Prepared-report downloads are grouped by purpose. **Save work to reopen** keeps
JSON, ZIP and device saves together; JSON/ZIP provide portable resumable copies,
while device saves stay in the current browser profile. **Read or share** contains
print/PDF, Word and standalone HTML, with a reminder to retain JSON/ZIP separately.
**Evidence spreadsheets** contains the full original-evidence CSV and the separate
passage-notes CSV. Calendar review entries remain a separate optional download.

All controls retain their existing preparation, stale-work, file-size and
unsaved-work protections. The grouping changes navigation and guidance; source
scope, report content, original ZIP files and saved formats remain unchanged.
Actual diplomat comprehension and work-browser acceptance still need user sessions.

## Remove loaded source collections

Expand **Manage loaded source collections** to see each original collection's
meetings, segment count and JSON byte size. Unchecking a meeting keeps its source
data in saved JSON. **Remove collection** removes that whole original bundle.
The confirmation lists the affected meetings and the number of passage notes and
appendix choices that will be removed. **Keep sources** is the default; Escape
also keeps current work. Save report JSON first if you need this version later.

Remaining source bytes, selections, annotations, mission settings and questions
stay intact. Prepare again before exporting the reduced report. Removing the last
collection also clears the current assessment, as the confirmation explicitly
warns; reusable mission settings and questions stay. Downloaded files, saved device
copies and the canonical archive are unchanged. A newer edit or source operation
invalidates an older removal confirmation.

## Add transcripts from the meeting inventory

Open or load a report, find a meeting date, and check up to five new meetings.
Choose **Add selected transcripts to this report** to retrieve them while keeping
current sources, notes, appendix choices, questions and existing meeting selections.
Unchecked loaded meetings stay unchecked; new meetings are included. Prepare the
report again, then save JSON or ZIP to retain the addition. Nothing is saved
automatically. The request checkboxes clear after a successful addition.

An already loaded meeting, including an unchecked one or a newer source revision,
is refused before retrieval. The ten-bundle/100-meeting limit and reserved or
unavailable metadata are checked before requests. Retrieved sources and the full
saved-JSON budget are checked before applying anything. Failed, incomplete,
cancelled or stale retrieval leaves current work intact; a completed first bundle
is not applied when a later bundle fails. Use a separate report to inspect
incomplete sources. Edits or newer source operations supersede pending additions.

**Load selected transcripts** keeps its separate replacement workflow and asks
before discarding unsaved source-bound work. Inventory search alone does not
retrieve transcripts. Both retrieval actions are explicit browser requests.

## Add sources while keeping current work

Open a collection or report first, then use **Add sources from JSON or report-package ZIP to this
report**. The file may be an original-bound collection or a supported saved report.
An original report-package ZIP also works. Its ZIP structure, CRCs, SHA-256 file
checksums and metadata are checked first. Original source bytes, identities and
metadata are then checked before any change.
Your mission settings, briefing questions, notes, appendix choices and existing
meeting selections stay in place. Unfinished question fields remain editable.

Only sources are added. Notes, settings and appendix choices from the added
report are not copied. All its loaded source bundles are retained, including
unselected meetings; its selected meetings are checked in the combined workspace.
Existing unchecked meetings remain unchecked. Review the loaded meeting list,
then prepare the report again before exporting or saving on this device.

Any overlapping meeting identity is refused, including an unselected meeting or
another revision of the same meeting. No source revision is silently replaced,
no partial merge is applied and no current annotation is discarded. Use a
nonoverlapping file, or open the other report separately to inspect its revision.
Invalid/reserved/corrupt files leave current sources, notes, preview and exports
intact. Editing or starting a newer source operation during validation prevents
an older addition from overwriting that work. This action makes no source request.

The combined sources retain the existing limits: ten source bundles, 100 meetings,
15,000 passages and 25 MB encoded source JSON. Before applying an addition, the
application also measures the complete resumable report JSON, including all loaded
sources, current notes, settings and selections. It refuses a result above 25 MB
without truncation. Later edits can still enlarge exports, which keep their own
bounds. Nothing is saved or uploaded automatically; report v4, preferences v2 and
the eight-report/25 MB device-library limit are unchanged.

## Country expressions across selected meetings

Preparing more than one meeting automatically adds a combined country/affiliation
overview. Every recorded affiliation appears, grouped by label and source date.
Each dated row links to its meeting and shows existing object-specific extracts,
collective/no-extract gaps and matching U.S. extracts from that same meeting.
The individual meeting tables also show matched U.S. wording directly.

A match requires the same issue identifier and case-insensitive displayed policy
object wording. It does not establish policy agreement: both countries' original
verbs and cited excerpts remain visible, including opposing wording. U.S. evidence
from another meeting is never carried forward, even on the same date. Same-date
meetings are ordered by title without claiming their actual within-day order.
Dates and different expressions are not verified government policy changes.

Affiliation coverage counts describe loaded evidence. A country missing from a
selected meeting remains a source gap, not neutrality or silence. Collective-only
observations never become national positions. Repeated quoted wording appears
once per extract and adds no weight; original records remain in the full CSV.
Search filters, appendix choices and priority questions do not narrow the overview.

The view is rebuilt from original source bundles on import. Saved report v4 and
mission preferences v2 remain unchanged; derived chronology is not trusted from
saved files. HTML, Word, print/PDF and report-package HTML include the view, without
an additional model, dependency, upload or server. Existing provisional-extraction
and publication boundaries still apply; actual diplomat usability is unaccepted.

## Print or save a PDF

Prepare a report, then choose **Print / Save as PDF**. Select your printer or the
PDF destination in the browser's own dialog. Printing uses the complete report,
including evidence beyond the screen preview limit, source identities, questions,
selected appendices and separately labeled notes. Workspace controls are excluded.
Filters do not narrow the output. Meeting links point to headings within the
printable copy; original source hyperlinks remain intact.

Closing the dialog restores the workspace. If a browser does not reset the print
controls, choose **Return to report**. The application cannot tell whether you
printed, saved a PDF or cancelled, so it never reports a PDF as saved. Printing
keeps unsaved-work protection. Save JSON or ZIP separately to reopen verified
sources and notes; a PDF is a reading copy.

The printable HTML is bounded to 25 MB without truncation. The browser controls
final PDF size, destination, paper settings, headers and footers. If printing is
disabled, download HTML and print it separately. Editing a report disables its
print button until preparation; browser-menu printing without a prepared report
shows an explicit preparation message instead of an old report. No PDF library,
server, upload or new model is used. Synthetic Chromium PDF output and browser
state have engineering checks; actual government-browser printer/PDF dialogs and
participant usability remain unaccepted.

## Editable Word reading copy

After preparing a report, choose **Download Word report (.docx)**. The browser
creates native headings, editable country tables, lists, source hyperlinks and
meeting-index bookmarks from the complete report, including selected evidence,
briefing questions, visible gaps and separately labeled analyst notes. Passage-list
filters do not narrow the download. No source request, upload, external model,
macro, embedded source bundle or remote image is added.

The Word copy is for reading and editing outside this application. Word edits
cannot be imported here. Save JSON or the report ZIP separately to reopen verified
sources and resume work; downloading Word alone keeps unsaved-work protection.
The ZIP still contains HTML, JSON, CSV, its guide and checksums; it does not include
Word. Word uses the prepared report's timestamp, matching the other filenames.

The complete `.docx` is limited to 25 MB, including its ZIP/XML container. Size
or unsupported XML-character failures refuse the download without truncating
sources, changing the report or disabling its other exports. Changing report
settings or evidence selections disables stale Word exports until preparation.
Native package structure, text coverage, hyperlinks and browser behavior have
synthetic engineering tests. Desktop Word rendering and actual diplomat usability
still need user acceptance; JSON remains the exact source-preserving format.

## Passage-list filters

Choose an exact **Recorded country / affiliation** or **Recorded speaker name**
to narrow the evidence list. Both filters combine with all-word search and
**Show selected passages only**. Choices come from all passages in the currently
selected meetings, independently of the current query. A zero-match result stays
visible; **Clear search and filters** restores the full passage list without
removing appendix choices or notes.

These filters do not select report countries, verify personal identity or turn a
collective statement into a national position. The mandatory country overview,
prepared report and full evidence CSV retain all passages from selected meetings.
Neighboring context retains other speakers even when they do not match the filter.
Filtering does not invalidate a prepared report or change saved-report JSON.
Names are exact recorded strings, not a deduplicated person directory. Missing
names have a separate option. Opening different sources resets both filters;
removing a meeting resets a filter if its value is no longer available. Filters
are temporary view choices and are not saved in report or preference files.

## Optional reports saved on this device

After preparing a report, choose **Save on this device** for the first copy.
**Save as another device report** keeps an additional report; **Replace selected
device report** replaces the copy selected in the library after confirmation.
The library holds up to eight reports and 25,000,000 UTF-8 bytes of report JSON
in total. A replacement counts the new copy instead of the old one. Count and
byte checks share the write transaction, so concurrent tabs cannot exceed either
limit. IndexedDB's internal metadata/overhead is outside this JSON payload budget.
No model, dependency, server or Hugging Face data is added.

Open **Saved reports on this device** to select, refresh, reopen or remove a copy.
The list displays titles, save times and encoded JSON sizes, without opening a
report automatically. Reports retain all loaded original source bundles, notes,
questions and selections. Reopening checks original sources through the same
importer as downloaded JSON; it rebuilds derived summaries rather than trusting
saved claims. Library selection does not change the current report or exports.

Opening over unsaved work requires an explicit replacement decision. Removal
preserves open work and downloaded files, and marks open work unsaved. A delayed
save never marks newer edits saved. Opening, replacing or removing a copy using
stale metadata fails with a request to refresh, rather than acting on another
tab's newer version. Storage failures preserve existing copies and current work.
Report JSON schema v4 and mission preference schema v2 remain unchanged.

The database upgrade moves the earlier single slot into the library atomically,
without keeping a duplicate source store. A failed upgrade rolls back to the
earlier data. After a failed upgrade, **Download earlier device copy** can export
the retained JSON unchanged without upgrading or deleting it. This recovery file
is unverified until opened through the source-checking importer. A tab that prevents the upgrade can be closed before **Refresh
library** retries it. Browser versions still running the earlier storage module
cannot write its old database version after the upgrade; file-based reporting
remains available.

Nothing is saved automatically or uploaded. This is browser-profile storage,
not authenticated mission collaboration. Other users of the same browser profile
may access saved reports, and browser cleanup may remove them. Keep downloaded
JSON or ZIP for portability. A browser that disables storage retains file-based
reporting. These guarantees concern engineering behavior, not summary accuracy.

## Briefing questions

Add up to eight briefing questions in mission preferences. Each has a heading
(up to 160 characters) and search words (up to 300 characters). All search words
must occur in a passage or its recorded metadata. Prepared reports show matching
original passages with source identities, or an explicit unanswered-question gap.
These searches do not generate answers, infer positions or change the mandatory
meeting overview, country comparison coverage, evidence appendix or full CSV.

Questions are retained in v4 saved reports and v2 mission preferences. Existing
v1–v3 reports and v1 preferences reopen with no questions; legacy schemas carrying
questions are rejected rather than silently dropping them. Imports rebuild results
from verified sources. Editing, adding or removing a question invalidates prepared
exports. HTML and ZIP contain the question sections; evidence CSV remains unchanged.
No model, new dependency, automatic storage or external AI request is added.

## First delivery

[Open the reporting workspace](https://lystadjs.github.io/un/transcript-agent/meeting-reports.html). Deployment and verified engineering evidence are recorded in [the current checkpoint](OVERNIGHT_WORK.md). Diplomat usability and scientific acceptance remain separate.

`site/meeting-reports.html` is a focused browser workspace. A date search verifies the complete official inventory without downloading transcripts. Users explicitly select up to five meetings per load; only those transcripts are requested. The 37 reserved identities and both reserved dates are blocked before collection. A synthetic regression binds the browser exclusions to the production collector's exact policy.

Users can also reopen source-bound `un.browser.corpus.v1` collections and versioned `un.meeting-report.v1`, `un.meeting-report.v2`, `un.meeting-report.v3` and `un.meeting-report.v4` reports. Imported text must match original response bytes, source identity, date, language, JSON pointer, and hashes. Meeting titles, passage identifiers and evidence links must match the original inventory and source; renaming a repeated passage cannot inflate its count. Country and speaker metadata must agree with the original source and current country registry. Unsupported or corrupt inputs leave the existing collection intact. Legacy hash-only collections remain readable in the original advanced workspace; this new workflow requires original response bytes.

The maintained public archive is deliberately source-free. The archive can hand off up to five selected public meeting identities across dates. Selection survives filters and pagination. The versioned link carries only dates, meeting IDs and the public snapshot ID; no transcript, notes, source URL or credentials. In the reporting workspace, users explicitly check those identities against the current official inventory before loading available sources. Missing and unavailable meetings remain visible; the tool never substitutes another meeting. Invalid/reserved selections are rejected, and missing exclusion policy disables handoff while preserving archive browsing. This does not transfer private warehouse text or change publication allowlists. Fresh browser collection is user-triggered, local, English-only and separate from the scheduled warehouse. A browser can show a newer revision than the last warehouse snapshot; report provenance identifies the actual loaded revision.

## Keeping current work when replacing sources

Opening another valid file or loading new transcripts asks before replacing unsaved work. “Keep current report” is the default; Escape also keeps it. This preserves loaded sources, notes, appendix selections, the prepared preview and available exports. Save report JSON before choosing “Replace report” if you need the current work later. Invalid imports show their validation error and leave the workspace unchanged, without a replacement prompt.

New transcript loading asks before making source requests. Cancelling a load keeps the current workspace even if some bundles have completed. A partial result requires a separate replacement decision when a collection is already loaded; a complete failure preserves it. Edits or report preparation during retrieval or file validation invalidate that pending replacement. An older import cannot overwrite a newer one.

Confirmed fresh collection replaces source-bound notes and appendix choices while retaining reusable mission preferences. A saved-report import restores that file's validated notes and selections. Nothing is uploaded or stored automatically. Close/reload warnings remain separate from these replacement controls.

## Templates and interpretation

- **Mission briefing:** meeting overview, subjects, all recorded country affiliations, source-linked expressions, U.S. comparison coverage, analyst notes, and limitations.
- **Negotiation record:** the same evidence, with recorded expressions before subject coverage. It does not invent negotiation outcomes, consensus, decisions, or commitments.
- **Evidence digest:** includes all passages from selected meetings by default; an explicit custom appendix can narrow the supporting passages.

Mission name, title, priority words, and analyst notes are configurable. Priority search requires every word somewhere in the passage or recorded metadata; it does not perform semantic inference or change the all-meeting overview. Evidence search is bounded to loaded, selected meetings and paginated for readability. An empty match set does not establish absence or neutrality.

Summaries reuse the existing deterministic quick reader. Country expressions are provisional source-linked rule extracts, not accepted five-class model predictions. Collective statements remain separate from national expressions. U.S. comparison coverage uses matching issue and exact policy-object wording in the same meeting; it assigns no agreement score. Any textual disagreement, conditions, or missing comparable extract must be interpreted through the evidence. User notes are visibly separate from source statements.

## Source context and recorded capacity

“Read neighboring source passages” opens the selected segment and, when loaded, the immediately preceding and following source indices. Neighbors must match the same meeting, date, language, source locator, version and raw-response hash. Missing indices remain explicit gaps; the reader never skips over an unloaded segment or treats the last loaded segment as proof of a complete transcript. This is bounded local inspection, with no additional source request.

Each passage retains its own source identity, exact text and recorded speaker, role and group. Affiliation is labeled as recorded metadata, not verified national capacity. The existing quick-reader collective safeguard supplies a visible provisional collective indication; national attribution remains withheld for that passage. Absence of a collective indication does not verify national capacity or the person's identity. The contextual neighbor may have a different speaker and must not be attributed to the selected speaker.

Opening context does not select appendix passages, copy notes, change search counts, alter country summaries or invalidate a prepared report. The browser context panel is not automatically added to HTML appendices or saved as a new selection. HTML evidence and note sections retain the speaker/capacity details; JSON retains original source records, and the full evidence CSV is unchanged. Report schemas v1/v2/v3 remain supported.

Country-expression tables offer “Read source context” in the prepared browser report. The control appears only when the extract's segment ID, text hash, original pointer and source URL match one loaded record from that meeting. A local dialog opens that exact segment and its bounded original neighbors, with separate speaker metadata and visible gaps. Keyboard activation, Escape and the close button return focus to the invoking control. The view preserves search filters, appendix choices, notes, comparison gaps and prepared exports; editing the report closes it. HTML downloads remain script-free and retain the original external source links, without inactive browser controls.

## Navigating a report

Reports containing multiple meetings open with a selected-meeting index. Each dated title links to its meeting section, alongside the loaded source-segment count and collection outcome. These describe available evidence, not source completeness or policy importance. Each section links back to the index. Keyboard navigation moves focus to the destination heading; the same links work in the script-free HTML download. A single-meeting report opens directly with its meeting overview.

Navigation does not request sources, select evidence, change notes or alter country expressions and coverage. Meeting order, original source links and the full evidence CSV remain unchanged. The index is rebuilt from verified sources when a saved report reopens; all four saved-report versions remain supported.

## Jump between recorded affiliations

Reports with more than one recorded affiliation include an alphabetical
**Recorded affiliations** index. Each link jumps to that affiliation's first row
in the collection overview, or its country row in a single-meeting report.
Single-meeting reports keep their summary and source statistics ahead of the index.
**Back to affiliations** returns to the index. Keyboard activation moves focus
to the destination row or heading. Every affiliation and comparison gap remains
visible; no country selection is required to receive the overview.

These links change only navigation. They preserve the prepared report, source
scope, search filters, notes, appendix and full CSV. They make no source request.
The same native links work in the script-free HTML export, Word bookmarks and
browser-generated PDF. Unresolved or collective-only evidence remains a gap;
these source labels do not establish national capacity or verified policy.
An empty or single-affiliation report omits the unnecessary index. Saved reports
rebuild it from verified original sources rather than trusting a saved index.

## Passage-note spreadsheet

After preparing a report, expand **Passage notes for spreadsheet follow-up** and
choose **Download passage notes CSV**. It exports one row per passage note in the
prepared report's selected meetings, in original source order. Each row identifies
the note as user-authored interpretation and retains the report timestamp, record
identity, meeting, recorded affiliation, source URL, source revision, hashes and
JSON pointer. Affiliation remains a source label, not verified national capacity.

Search and appendix choices do not narrow these notes. Original transcript text
and the report-level assessment are excluded. The separate full evidence CSV is
unchanged and excludes analyst notes. Spreadsheet-formula prefixes receive an
apostrophe, while quoted cells preserve commas, quotes, line breaks and Unicode.
Save report JSON for exact original text and to resume editing; CSV changes cannot
be imported. The notes CSV is separate from the existing five-file ZIP.

The control stays disabled until a prepared report contains passage notes. Changing
report inputs invalidates it with other exports. A failed or oversized download
keeps current work; downloading notes does not clear unsaved-work protection.
The existing 25 MB encoded download limit applies. Nothing is uploaded or saved
automatically; no schema, dependency, storage or personal-runtime change is added.
Actual spreadsheet-client and diplomat usability acceptance remains outstanding.

## Personal calendar review entry

Prepare the report, expand **Calendar entry for a report review**, and choose your
personal all-day review date. **Download review entry (.ics)** saves one calendar
entry with the report title, preparation time and selected source meeting
references. Review dates are chosen independently of source meeting dates. The
calendar application controls import, visibility and alerts; check them after
importing. There is no calendar account connection or invitation sending.

The assessment checkbox starts off. Enabling it copies the report-level assessment
into the calendar description. Passage notes and transcript text are excluded.
The entry carries a private-class hint; review its contents before importing into
your selected calendar. No source request or automatic upload occurs.

ICS is a separate reading copy. It preserves neither original corpora nor resumable
report state. Calendar date/assessment options belong to this browser session,
are excluded from saved report JSON/preferences and reset when another report
replaces the workspace. Save the ICS to retain the entry and JSON/ZIP to resume
editing. Calendar export does not clear unsaved-report protection or change other
prepared exports. Word and calendar copies remain separate from the report ZIP.

The date range is 1900–9998. Entries use date-only start and exclusive next-day
end, UTC preparation stamps, escaped text and UTF-8 folding at 75 octets. Missing
or invalid dates, unsupported text, oversized output and changes during export
are refused without modifying current work. Engineering checks validate the file
and browser behavior; actual calendar-client and work-browser acceptance remains
outstanding.

## Selecting an evidence appendix

Check supporting passages while searching. Selections persist across searches, and “Show selected passages only” makes them easy to revisit. Any template can use a custom appendix; its heading identifies the passages as analyst-selected and reports their count against the full selected-meeting denominator. Clearing the selection leaves an explicit empty appendix. Returning to “Template default” clears custom selections. Removing a meeting removes its appendix selections.

Use **Add … new matches** or **Remove … selected matches** to change every
current match, including results beyond the visible page. The buttons show how
many new or already selected passages the action affects. Literal search,
recorded-affiliation/name filters and “Show selected passages only” define the
matching set. Other explicit selections stay intact. These actions switch to
**Selected passages only**; template-default contents are not implicit selections.

**Undo last bulk appendix change** restores the previous appendix mode and exact
explicit choices, including after Clear passage selection. It keeps subsequent
assessment and passage-note edits. Changing a search filter does not erase undo;
manual passage choices, appendix-mode changes, selected-meeting changes and source
replacement/addition/removal do. Undo is session-only and is not saved in JSON,
ZIP or reusable preferences. Every applied or undone appendix change requires
preparing the report again before exporting. No source request occurs.

Appendix selection never changes meeting overviews, country expressions, U.S. comparison coverage, priority-query results or the full evidence CSV. Original passages and source locators remain unchanged. Analyst notes remain a separate user-authored section. Search results and selected passages do not establish absence of other relevant evidence.

The v2 and v3 saved-report objects require `appendix: {mode, record_ids}`. `mode` is `template` (with an empty ID list) or `selected`; selected IDs must be unique and belong to the loaded, selected meetings. Unknown, duplicate, out-of-scope and malformed IDs are rejected before modifying the workspace. Rendering follows original source order. Existing v1 reports reopen with template defaults. All supported versions revalidate original sources and rebuild summaries rather than trusting saved derived claims. Appendix edits disable prepared exports until the report is rebuilt. Reusable mission preferences exclude appendix selections.

## Notes on individual passages

Open “Your note on this passage” beside a search result to record interpretation or follow-up. Up to 100 nonempty passage notes of 2,000 characters each can be retained. Notes persist across searches and reusable-preference imports, and appear in a separate report section beside their original evidence and source identifiers. They are independent of appendix selection; clearing the appendix leaves notes intact. Removing a meeting removes its notes, as the workspace explains. Blank notes are removed. Save report JSON to retain this work locally.

Version 3 requires `passage_notes`, a bounded array of exact `{record_id, text}` objects. IDs must be unique and belong to the selected, verified source meetings. Imports reject extra fields, unknown or duplicate IDs, invalid types, blank notes and limit violations before changing existing work. V1 and v2 files reopen with no passage notes; notes in an older schema are rejected rather than silently discarded. Source order determines presentation. Note edits invalidate prepared exports, and HTML escapes user text. Reusable mission preferences and the full evidence CSV exclude all analyst notes.

Report notes do not alter source text, country expressions, coverage, comparisons, research datasets or model training labels. They are distinct from the private owner-reviewed pilot annotation contract. No report note is promoted into human gold or an accepted stance estimate.

## Reusable mission preferences

Save or open `un.mission-preferences.v1` JSON before or after loading meetings. The file contains only `schema` and `settings`; settings contains exactly `template`, `mission`, `title` and `priorities`. Templates retain the three supported report formats. Mission/title/priority strings retain the existing 160/200/300-character bounds, and the file is limited to 8 KiB.

This reusable format excludes source text, meeting identities and analyst notes. Import rejects unknown fields, unsupported schemas, invalid types and oversized files before changing the workspace. Applying valid preferences preserves loaded sources, selected meetings and current analyst notes, but clears the prepared preview and disables stale report exports until the report is prepared again. Invalid files leave the existing report intact. Nothing is saved or uploaded automatically. The source-bearing report JSON below remains a separate format.

## Report package

“Download report package (ZIP)” saves one local, unencrypted archive containing `report.html`, `report.json`, `evidence.csv`, `README.txt` and `manifest.json`. Open the ZIP directly in the workspace to continue editing, or extract and open `report.json` separately. HTML, JSON and CSV use the same preparation and exact content as their individual downloads. JSON retains all loaded source bundles, including unselected meetings; the package can contain source text and analyst notes. Review the contents before sharing. No upload or additional source request occurs.

The field guide explains the CSV grain, columns, formula escaping, source/user/model distinctions and saved-work scope. Manifest schema `un.meeting-report-package.v1` records preparation time, method, selected meeting IDs and segment count, original response revisions, and each other file's encoded byte count and SHA-256. The manifest has no self-checksum. Hashes detect changed bytes; they do not authenticate the source or speaker. ZIP entries use uncompressed storage and a fixed 1980 container timestamp; the preparation date is in the manifest and outer filename.

The complete package, including ZIP headers and manifest, must fit within 25,000,000 bytes. A refusal preserves work and leaves individual exports available. Changing or re-preparing the report while packaging cancels that download, preserving the newer work and unsaved warning. A completed package download counts as saving the report because it contains the full reopenable JSON. Existing individual exports and v1/v2/v3 saved-report readers remain available. Direct ZIP opening accepts the app’s original uncompressed five-file package format only. ZIPs compressed or repacked outside this format are refused; use their extracted `report.json` instead. Before any replacement prompt, the reader checks contiguous local/central ZIP headers, CRCs, SHA-256 file checksums and manifest metadata, then revalidates original sources. Imported HTML is never rendered or executed; every derived report is rebuilt. Invalid packages and stale operations leave current work intact. The existing Keep/Replace confirmation applies to valid package opening. Add sources also accepts packages, keeping current annotations and excluding incoming report annotations.

## Export contract

| Export | Contents and use |
| --- | --- |
| HTML | Script-free, standalone report suitable for browser reading and printing. Includes settings, preparation time, source checks, selected coverage, evidence links, and limitations. |
| JSON | `un.meeting-report.v4`: engine, preparation time, preferences, selected meeting identities, appendix mode/passage identities, source-bound analyst notes, and original browser corpora. Reopening verifies sources and rebuilds derived claims; it does not trust saved computed summaries. |
| Evidence CSV | One row per original segment in the selected meetings: `id`, `meeting_slug`, `date`, `country`, `text`, `source_url`, `source_id`, `source_version`, `raw_sha256`, `text_sha256`, `json_pointer`. Includes every passage from the selected meetings, independently of search and appendix selection; excludes analyst notes. |

The three downloads share a basename containing the report preparation timestamp in UTC, for example `un-meeting-report-20261113T023000123Z.html`, the corresponding `.json`, and `-evidence.csv`. Repeated exports from one prepared report retain that timestamp; preparing again creates a new report time. Filenames contain no mission name, notes or source text. The timestamp identifies a preparation, not the source publication date or a cryptographic checksum.

CSV uses UTF-8, quoted cells and CRLF. Potential spreadsheet formulas are prefixed with an apostrophe; JSON preserves exact strings. Source versions use exact response SHA-256, not an official publication-version number. Hash consistency does not authenticate a speaker or establish source truth. Exports may contain source text and analyst notes and are never committed to the public repository. Nothing is uploaded or stored automatically; save JSON before closing. HTML, JSON and CSV downloads share a 25 MB bound measured in encoded bytes. Oversized output is refused without truncating evidence or changing the prepared report; a refused JSON download does not clear the unsaved-work warning. Reduce the selected meetings or note length and prepare again. The import bound is also 25 MB, with at most 100 meetings in imported collections.

## Next deliveries and acceptance

1. Run the [representative-diplomat usability session](REPORTING_USABILITY.md); retain actual participant findings separately from synthetic engineering tests. The guide is prepared, and actual sessions remain uncompleted.
2. Extend the implemented archive-selection handoff only through approved source access, without broadening the public text allowlist implicitly.
3. Validate the deployed country-expression evidence navigation with representative diplomats; retain exact segment identifiers and comparison gaps.
4. Evaluate an optional local generative reporting model separately from the stance classifier. Fluent generation, factual coverage and citation correctness need their own acceptance evidence.
5. Complete the owner-label pilot and untouched stance evaluation. Reporting remains useful while model estimates stay withheld.

No real-time transcription, multilingual parity, secure multi-user collaboration, fourteen-day operational acceptance, or accepted neural stance model is established by this release.
