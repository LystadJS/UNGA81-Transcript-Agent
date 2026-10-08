# Offline single-meeting quick reader and development-only attribution

## Purpose

Give diplomats an accurate short orientation before technical meeting analysis.
The automatic opening section appears only for an individually selected meeting.
It covers the entire retrieved English meeting transcript, independently of the
optional detailed-analysis topic filter.  It uses no remote generative AI API.

## Source and writing contract

- Use the meeting identifier, date, official returned title, and exact collected
  English source segments; never fetch other meetings to prepare the overview.
- Write two complete direct paragraphs: recurring subjects and (if supported)
  broad evidence-based country-linked expressions.  Template prose follows the
  JSL writing voice's short anchor/qualification structure.  It is not an
  adaptive or AI-written essay.
- Count **source segments**, mapped country labels, unresolved affiliation
  segments, and median whitespace words.  These are not unique speakers or
  independent speeches.  Empty/missing text is **not** a zero-interest finding.
- List leading broad text categories and source-linked excerpts.  Keywords are
  descriptive; neither frequency nor institutional series identifies a formal
  agenda item or outcome.
- A broad expression is recorded only with a registry-mapped country-affiliated
  intervention and an explicit first-person evaluative clause **on the same
  subject**.  Withhold absent evidence, procedural presiders, unverified
  affiliation, quotations, descriptions of others, and bare co-occurrence.
  Classifications apply to the recorded wording, not an official government-wide
  position, support for a country's policies, or policy agreement among states.
- Retain original speaker function, group and affiliation when supplied.  A
  name or ID exists only when the original record supplies it.  Affiliation plus
  function is an imperfect recurrence proxy, not a unique human identifier.

## Integration

`site/meeting-quick-reader.js` is a deterministic local-only module reused by
`site/analysis-core.js` and the separate development attribution audit.
`site/analysis-ui.js` renders the synopsis first and includes it in HTML, JSON,
and print views.  `site/collector.js` retains source speaker metadata and
registry-mapping status with the original passage hashes and source URL.
`site/index.html` loads the new module before the analysis engine.  The existing
source fetch and clustering/NMF algorithms are unchanged.

## Reproduce and audit

```bash
node tools/test_meeting_quick_reader.cjs
node research/reference_tests/test_meeting_attribution.cjs
node tools/test_meeting_picker.cjs
# Development-only; requires the original private development corpus, never holdout:
node research/reference_tests/meeting_attribution_audit.cjs CACHED_DEVELOPMENT_CORPUS.json NEW_OUTPUT_DIR
```

Public validation contains aggregate coverage only.  Private evidence ledgers
contain original source IDs and remain in the local checkpoint, not in GitHub.
The frozen 37-meeting evaluation roster, original source bytes, and all D1
publication controls are unaffected.
