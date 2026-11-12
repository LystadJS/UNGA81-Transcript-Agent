# Meeting-first reporting

The immediate product target is a PowerTranscript-like reporting workflow, implemented independently: select proceedings, search their evidence, apply mission report templates, and export documented results. Research CSVs and evaluated stance tracking remain distinct capabilities. This is not a claim of equivalent vendor performance or access to proprietary code or weights.

## First delivery

[Open the reporting workspace](https://lystadjs.github.io/un/transcript-agent/meeting-reports.html). Deployment and verified engineering evidence are recorded in [the current checkpoint](OVERNIGHT_WORK.md). Diplomat usability and scientific acceptance remain separate.

`site/meeting-reports.html` is a focused browser workspace. A date search verifies the complete official inventory without downloading transcripts. Users explicitly select up to five meetings per load; only those transcripts are requested. The 37 reserved identities and both reserved dates are blocked before collection. A synthetic regression binds the browser exclusions to the production collector's exact policy.

Users can also reopen source-bound `un.browser.corpus.v1` collections and versioned `un.meeting-report.v1` and `un.meeting-report.v2` reports. Imported text must match original response bytes, source identity, date, language, JSON pointer, and hashes. Meeting titles, passage identifiers and evidence links must match the original inventory and source; renaming a repeated passage cannot inflate its count. Country and speaker metadata must agree with the original source and current country registry. Unsupported or corrupt inputs leave the existing collection intact. Legacy hash-only collections remain readable in the original advanced workspace; this new workflow requires original response bytes.

The maintained public archive is deliberately source-free. The archive can hand off up to five selected public meeting identities across dates. Selection survives filters and pagination. The versioned link carries only dates, meeting IDs and the public snapshot ID; no transcript, notes, source URL or credentials. In the reporting workspace, users explicitly check those identities against the current official inventory before loading available sources. Missing and unavailable meetings remain visible; the tool never substitutes another meeting. Invalid/reserved selections are rejected, and missing exclusion policy disables handoff while preserving archive browsing. This does not transfer private warehouse text or change publication allowlists. Fresh browser collection is user-triggered, local, English-only and separate from the scheduled warehouse. A browser can show a newer revision than the last warehouse snapshot; report provenance identifies the actual loaded revision.

## Templates and interpretation

- **Mission briefing:** meeting overview, subjects, all recorded country affiliations, source-linked expressions, U.S. comparison coverage, analyst notes, and limitations.
- **Negotiation record:** the same evidence, with recorded expressions before subject coverage. It does not invent negotiation outcomes, consensus, decisions, or commitments.
- **Evidence digest:** includes all passages from selected meetings by default; an explicit custom appendix can narrow the supporting passages.

Mission name, title, priority words, and analyst notes are configurable. Priority search requires every word somewhere in the passage or recorded metadata; it does not perform semantic inference or change the all-meeting overview. Evidence search is bounded to loaded, selected meetings and paginated for readability. An empty match set does not establish absence or neutrality.

Summaries reuse the existing deterministic quick reader. Country expressions are provisional source-linked rule extracts, not accepted five-class model predictions. Collective statements remain separate from national expressions. U.S. comparison coverage uses matching issue and exact policy-object wording in the same meeting; it assigns no agreement score. Any textual disagreement, conditions, or missing comparable extract must be interpreted through the evidence. User notes are visibly separate from source statements.

## Selecting an evidence appendix

Check supporting passages while searching. Selections persist across searches, and “Show selected passages only” makes them easy to revisit. Any template can use a custom appendix; its heading identifies the passages as analyst-selected and reports their count against the full selected-meeting denominator. Clearing the selection leaves an explicit empty appendix. Returning to “Template default” clears custom selections. Removing a meeting removes its appendix selections.

Appendix selection never changes meeting overviews, country expressions, U.S. comparison coverage, priority-query results or the full evidence CSV. Original passages and source locators remain unchanged. Analyst notes remain a separate user-authored section. Search results and selected passages do not establish absence of other relevant evidence.

The v2 saved-report object requires `appendix: {mode, record_ids}`. `mode` is `template` (with an empty ID list) or `selected`; selected IDs must be unique and belong to the loaded, selected meetings. Unknown, duplicate, out-of-scope and malformed IDs are rejected before modifying the workspace. Rendering follows original source order. Existing v1 reports reopen with template defaults. Both versions revalidate original sources and rebuild summaries rather than trusting saved derived claims. Appendix edits disable prepared exports until the report is rebuilt. Reusable mission preferences exclude appendix selections.

## Reusable mission preferences

Save or open `un.mission-preferences.v1` JSON before or after loading meetings. The file contains only `schema` and `settings`; settings contains exactly `template`, `mission`, `title` and `priorities`. Templates retain the three supported report formats. Mission/title/priority strings retain the existing 160/200/300-character bounds, and the file is limited to 8 KiB.

This reusable format excludes source text, meeting identities and analyst notes. Import rejects unknown fields, unsupported schemas, invalid types and oversized files before changing the workspace. Applying valid preferences preserves loaded sources, selected meetings and current analyst notes, but clears the prepared preview and disables stale report exports until the report is prepared again. Invalid files leave the existing report intact. Nothing is saved or uploaded automatically. The source-bearing report JSON below remains a separate format.

## Export contract

| Export | Contents and use |
| --- | --- |
| HTML | Script-free, standalone report suitable for browser reading and printing. Includes settings, preparation time, source checks, selected coverage, evidence links, and limitations. |
| JSON | `un.meeting-report.v2`: engine, preparation time, preferences, selected meeting identities, appendix mode/passage identities, and original source-bound browser corpora. Reopening verifies sources and rebuilds derived claims; it does not trust saved computed summaries. |
| Evidence CSV | One row per original segment in the selected meetings: `id`, `meeting_slug`, `date`, `country`, `text`, `source_url`, `source_id`, `source_version`, `raw_sha256`, `text_sha256`, `json_pointer`. Includes every passage from the selected meetings, independently of search and appendix selection. |

CSV uses UTF-8, quoted cells and CRLF. Potential spreadsheet formulas are prefixed with an apostrophe; JSON preserves exact strings. Source versions use exact response SHA-256, not an official publication-version number. Hash consistency does not authenticate a speaker or establish source truth. Exports may contain source text and analyst notes and are never committed to the public repository. Nothing is uploaded or stored automatically; save JSON before closing. The 25 MB import/export bound and 100-meeting imported-collection bound prevent unbounded browser work.

## Next deliveries and acceptance

1. Test representative diplomat tasks against the first workflow; retain actual usability feedback separately from synthetic engineering tests.
2. Extend the implemented archive-selection handoff only through approved source access, without broadening the public text allowlist implicitly.
3. Extend source-linked report editing with evidence-specific analyst notes, preserving originals, coverage, versioned readers and the distinction between source evidence and user interpretation.
4. Evaluate an optional local generative reporting model separately from the stance classifier. Fluent generation, factual coverage and citation correctness need their own acceptance evidence.
5. Complete the owner-label pilot and untouched stance evaluation. Reporting remains useful while model estimates stay withheld.

No real-time transcription, multilingual parity, secure multi-user collaboration, fourteen-day operational acceptance, or accepted neural stance model is established by this release.
