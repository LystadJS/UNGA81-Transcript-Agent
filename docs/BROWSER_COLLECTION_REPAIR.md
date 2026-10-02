# Optional-topic collection and zero-result diagnostics

## Behavior

Leave **Topic** empty (or whitespace-only) to include every available English
passage within the selected dates, meeting scope, and speaker-region filter.
Related phrases and exclusions are disabled and ignored in this mode; their
previous contents cannot silently narrow the collection. Enter a topic to restore
phrase matching and exclusions.

**Save transcripts** preserves every original collected segment, including any
exact duplicates. Analysis, included-passage CSV, and charts use the eligible
unique passages after the existing exact-text deduplication. Analysis JSON retains
the duplicate-to-retained-record mapping. The collector always retrieves by dates
and meeting scope; topic and region filters are applied locally afterward.

## Committee dates and diagnostics

Selecting a committee changes untouched September 22–28 General Debate defaults
to the last seven calendar days in New York, with a visible explanation. Custom
dates are never automatically changed. Explicit **Last 7 days** and **General
Debate dates** buttons make the choice reversible. No request silently expands
its date range or substitutes a different committee.

The output distinguishes passages collected, unique eligible passages, and topic
matches. Daily inventory counts are included in coverage. Failed inventory,
failed downloads, pending/unavailable transcripts, empty transcript text,
non-English tracks, no in-scope meetings, and zero phrase matches are separate
states. Failed collection is not labeled a successful zero-match result.

## Evidence and limitation

An unmodified-collector live diagnostic on October 2, 2026 retrieved 92 source
segments from the two October 1 Third Committee meetings (36 and 56 segments).
All three UN requests returned HTTP 200 and Access-Control-Allow-Origin: *.
This shows that committee collection was not universally broken. The user's
specific failing dates, browser state, and network response were not provided,
so their exact cause remains unconfirmed. Historic date defaults and ambiguous
zero-result reporting were confirmed usability problems and are addressed here.

The repair keeps the browser-only architecture and existing size/date limits.
Versioned script URLs reduce mixed old/new browser-cache loading. No AI API,
proxy, additional production host, credential, or end-user installation is added.

## Reproduce validation

Run `node tools/test_browser_analysis.cjs` for existing analysis tests, all 23
committee tests, and eight optional-topic/collection-diagnostic tests.

For browser acceptance, install the **developer-only** test dependency:

```sh
python -m pip install playwright==1.57.0
python -m playwright install chromium
python tools/test_live_browser.py --site site --live --output live-check/browser
```

The browser test exercises actual UN fetching, all five methods, JSON/CSV/HTML
exports, saved-file reimport, topic and region filters, date controls, stale export
protection, 1440/390-pixel layouts, and controlled network/empty-inventory failures.
Downloaded corpus and test result JSON are retained. Fixture replay is supported
with `--fixtures DIRECTORY` instead of `--live`; do not label replay as live testing.
