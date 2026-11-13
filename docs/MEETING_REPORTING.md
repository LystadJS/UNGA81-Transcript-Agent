# Meeting-first reporting

The immediate product target is a PowerTranscript-like reporting workflow, implemented independently: select proceedings, search their evidence, apply mission report templates, and export documented results. Research CSVs and evaluated stance tracking remain distinct capabilities. This is not a claim of equivalent vendor performance or access to proprietary code or weights.

## First delivery

[Open the reporting workspace](https://lystadjs.github.io/un/transcript-agent/meeting-reports.html). Deployment and verified engineering evidence are recorded in [the current checkpoint](OVERNIGHT_WORK.md). Diplomat usability and scientific acceptance remain separate.

`site/meeting-reports.html` is a focused browser workspace. A date search verifies the complete official inventory without downloading transcripts. Users explicitly select up to five meetings per load; only those transcripts are requested. The 37 reserved identities and both reserved dates are blocked before collection. A synthetic regression binds the browser exclusions to the production collector's exact policy.

Users can also reopen source-bound `un.browser.corpus.v1` collections and versioned `un.meeting-report.v1`, `un.meeting-report.v2` and `un.meeting-report.v3` reports. Imported text must match original response bytes, source identity, date, language, JSON pointer, and hashes. Meeting titles, passage identifiers and evidence links must match the original inventory and source; renaming a repeated passage cannot inflate its count. Country and speaker metadata must agree with the original source and current country registry. Unsupported or corrupt inputs leave the existing collection intact. Legacy hash-only collections remain readable in the original advanced workspace; this new workflow requires original response bytes.

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

Navigation does not request sources, select evidence, change notes or alter country expressions and coverage. Meeting order, original source links and the full evidence CSV remain unchanged. The index is rebuilt from verified sources when a saved report reopens; all three saved-report versions remain supported.

## Selecting an evidence appendix

Check supporting passages while searching. Selections persist across searches, and “Show selected passages only” makes them easy to revisit. Any template can use a custom appendix; its heading identifies the passages as analyst-selected and reports their count against the full selected-meeting denominator. Clearing the selection leaves an explicit empty appendix. Returning to “Template default” clears custom selections. Removing a meeting removes its appendix selections.

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

“Download report package (ZIP)” saves one local, unencrypted archive containing `report.html`, `report.json`, `evidence.csv`, `README.txt` and `manifest.json`. Extract the archive and open `report.json` in the workspace to continue editing. HTML, JSON and CSV use the same preparation and exact content as their individual downloads. JSON retains all loaded source bundles, including unselected meetings; the package can contain source text and analyst notes. Review the contents before sharing. No upload or additional source request occurs.

The field guide explains the CSV grain, columns, formula escaping, source/user/model distinctions and saved-work scope. Manifest schema `un.meeting-report-package.v1` records preparation time, method, selected meeting IDs and segment count, original response revisions, and each other file's encoded byte count and SHA-256. The manifest has no self-checksum. Hashes detect changed bytes; they do not authenticate the source or speaker. ZIP entries use uncompressed storage and a fixed 1980 container timestamp; the preparation date is in the manifest and outer filename.

The complete package, including ZIP headers and manifest, must fit within 25,000,000 bytes. A refusal preserves work and leaves individual exports available. Changing or re-preparing the report while packaging cancels that download, preserving the newer work and unsaved warning. A completed package download counts as saving the report because it contains the full reopenable JSON. Existing individual exports and v1/v2/v3 saved-report readers remain available. The app imports extracted JSON, not ZIP files.

## Export contract

| Export | Contents and use |
| --- | --- |
| HTML | Script-free, standalone report suitable for browser reading and printing. Includes settings, preparation time, source checks, selected coverage, evidence links, and limitations. |
| JSON | `un.meeting-report.v3`: engine, preparation time, preferences, selected meeting identities, appendix mode/passage identities, source-bound analyst notes, and original browser corpora. Reopening verifies sources and rebuilds derived claims; it does not trust saved computed summaries. |
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
