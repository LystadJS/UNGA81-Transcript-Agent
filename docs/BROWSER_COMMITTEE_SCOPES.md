# Committee-specific browser reports

## Using the control

Under **Meeting scope**, select General Debate, all inventoried UN meetings, or
one of the six General Assembly main committees. Third Committee has its own
option: **Third Committee — Social, Humanitarian and Cultural**.

Choose dates when the selected committee met. The historical default General
Debate dates are not automatically changed when a committee is selected. A topic
and any related phrases still determine which eligible passages are matched.
The interface analyzes available English transcripts, not every UN record.

## How filtering works

`site/meeting-scopes.js` is shared by live collection and saved-file analysis.
Canonical UN paths such as `/en/ga/c3/81/1` identify the committee first.
Recognized ordinal or full committee labels in meeting titles are a fallback;
full thematic names require General Assembly context or an explicit committee
number. A press briefing about a committee is not automatically a committee
meeting. Conflicting canonical committee paths remain unclassified.

Transcript text, topic mentions, and speaker affiliation do not determine which
committee held a meeting. A committee's own general debate remains within its
committee scope, rather than being treated as the GA General Debate.

Live collection filters the meeting inventory before downloading transcripts.
Analysis applies the same scope before deduplication, matching, and denominators.
The report identifies the requested scope; JSON and CSV retain each passage's
scope. The original collection's coverage remains available separately.

## Saved collections

The schema remains `un.browser.corpus.v1`. Older records labeled `other` can be
classified from their retained UN source paths or recognized meeting titles.
Reclassified analysis records retain `scope_original`; the original imported
collection and text hashes are not modified.

An all-meetings collection can be narrowed to a committee. A General Debate-only
collection cannot supply committee proceedings, and a Third Committee-only
collection cannot supply another committee. Incompatible dates or scope produce
an explicit coverage warning. Imported metadata remains author-supplied; text
hashes establish integrity, not authenticity or completeness.

Unrecognized titles may remain unclassified when there is no canonical committee
path. Missing, unavailable, non-English, and failed sources are not counted as
negative topic matches. Empty results do not prove that no relevant meeting or
statement occurred.

## Code organization

Author HTML and JavaScript with two-space indentation, separate logical blocks,
blank lines between functions, and brief section comments. Keep form controls on
separate lines. Do not minify the maintained source files. Preserve truly empty
status containers: whitespace inside them changes CSS `:empty` behavior.

The user's masthead, controls, styling, and existing review workflow are retained.
No external library, API key, server, or end-user installation is introduced.
This remains descriptive browser-side analysis, not an LLM summarizer.

## Validation

Run the deployment gate with Node.js 22:

```sh
node tools/test_browser_analysis.cjs
```

It runs the existing regression checks and the 23 added committee tests.
The committee suite can also run independently:

```sh
node --test tools/test_browser_committees.cjs
```

Additional local validation compared 150 seeded legacy-scope fixtures against
the previous engine and ran 19 offline DOM checks, including scoped collection,
export content, imports, warnings, cancellation, and 1440/390-pixel layouts.
Offline DOM checks used adapters for fetch, hashing, and download handoff; they
are not live-network or original-CSP execution tests. The current sandbox blocked
browser navigation, so live UN collection was not revalidated in this update.

## Source references

- UN main committees: https://www.un.org/en/ga/maincommittees/
- Verified Third Committee title/path example: https://transcripts.un.org/en/ga/c3/81/1
- Broader methods and limits: [BROWSER_ANALYSIS.md](BROWSER_ANALYSIS.md)

Engine: `browser-descriptive-1.1.0`.
