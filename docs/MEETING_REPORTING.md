# Meeting-first reporting

The immediate product target is a PowerTranscript-like reporting workflow, implemented independently: select proceedings, search their evidence, apply mission report templates, and export documented results. Research CSVs and evaluated stance tracking remain distinct capabilities. This is not a claim of equivalent vendor performance or access to proprietary code or weights.

## First delivery

`site/meeting-reports.html` is a focused browser workspace. A date search verifies the complete official inventory without downloading transcripts. Users explicitly select up to five meetings per load; only those transcripts are requested. The 37 reserved identities and both reserved dates are blocked before collection. A synthetic regression binds the browser exclusions to the production collector's exact policy.

Users can also reopen source-bound `un.browser.corpus.v1` collections and versioned `un.meeting-report.v1` reports. Imported text must match original response bytes, source identity, date, language, JSON pointer, and hashes. Country and speaker metadata must agree with the original source and current country registry. Unsupported or corrupt inputs leave the existing collection intact. Legacy hash-only collections remain readable in the original advanced workspace; this new workflow requires original response bytes.

The maintained public archive is deliberately source-free. This first delivery links to that archive but does not transfer private warehouse text or change publication allowlists. Fresh browser collection is user-triggered, local, English-only and separate from the scheduled warehouse. A browser can show a newer revision than the last warehouse snapshot; report provenance identifies the actual loaded revision.

## Templates and interpretation

- **Mission briefing:** meeting overview, subjects, all recorded country affiliations, source-linked expressions, U.S. comparison coverage, analyst notes, and limitations.
- **Negotiation record:** the same evidence, with recorded expressions before subject coverage. It does not invent negotiation outcomes, consensus, decisions, or commitments.
- **Evidence digest:** includes the full selected source-segment appendix.

Mission name, title, priority words, and analyst notes are configurable. Priority search requires every word somewhere in the passage or recorded metadata; it does not perform semantic inference or change the all-meeting overview. Evidence search is bounded to loaded, selected meetings and paginated for readability. An empty match set does not establish absence or neutrality.

Summaries reuse the existing deterministic quick reader. Country expressions are provisional source-linked rule extracts, not accepted five-class model predictions. Collective statements remain separate from national expressions. U.S. comparison coverage uses matching issue and exact policy-object wording in the same meeting; it assigns no agreement score. Any textual disagreement, conditions, or missing comparable extract must be interpreted through the evidence. User notes are visibly separate from source statements.

## Export contract

| Export | Contents and use |
| --- | --- |
| HTML | Script-free, standalone report suitable for browser reading and printing. Includes settings, preparation time, source checks, selected coverage, evidence links, and limitations. |
| JSON | `un.meeting-report.v1`: engine, preparation time, preferences, selected meeting identities, and original source-bound browser corpora. Reopening verifies sources and rebuilds derived claims; it does not trust saved computed summaries. |
| Evidence CSV | One row per selected original segment: `id`, `meeting_slug`, `date`, `country`, `text`, `source_url`, `source_id`, `source_version`, `raw_sha256`, `text_sha256`, `json_pointer`. Includes all selected passages, independently of search. |

CSV uses UTF-8, quoted cells and CRLF. Potential spreadsheet formulas are prefixed with an apostrophe; JSON preserves exact strings. Source versions use exact response SHA-256, not an official publication-version number. Hash consistency does not authenticate a speaker or establish source truth. Exports may contain source text and analyst notes and are never committed to the public repository. Nothing is uploaded or stored automatically; save JSON before closing. The 25 MB import/export bound and 100-meeting imported-collection bound prevent unbounded browser work.

## Next deliveries and acceptance

1. Test representative diplomat tasks against the first workflow; retain actual usability feedback separately from synthetic engineering tests.
2. Add archive-selection handoff using approved source access, without broadening the public text allowlist implicitly.
3. Add reusable mission templates and richer report editing while preserving source/user/model distinctions.
4. Evaluate an optional local generative reporting model separately from the stance classifier. Fluent generation, factual coverage and citation correctness need their own acceptance evidence.
5. Complete the owner-label pilot and untouched stance evaluation. Reporting remains useful while model estimates stay withheld.

No real-time transcription, multilingual parity, secure multi-user collaboration, fourteen-day operational acceptance, or accepted neural stance model is established by this release.
