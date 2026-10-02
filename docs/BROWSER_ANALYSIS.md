# Live transcript report builder

Open https://lystadjs.github.io/un/transcript-agent/#analyze.

1. Enter a topic and optional comma-separated alternative phrases. A source
   segment matches any phrase; optional exclusion phrases remove the entire
   segment. Matching is case-insensitive over Unicode word tokens. It does not
   infer relevance, sentiment or stance. Abbreviations need human checking.
2. Select inclusive start/end dates, speaker region and meeting scope.
3. Choose descriptive methods and select **Collect transcripts & generate report**.
4. Inspect collection coverage, denominators and source evidence before sharing.
5. Download the standalone visual HTML report, analysis JSON, collected transcript
   JSON or matched-segment CSV. Use Print / save PDF for a printable copy.

## Collection

The browser requests the official `transcripts.un.org/en/meetings.json` inventory
for each date, checks pagination counts and dates, then retrieves the selected
meetings' transcript JSON. Both inventory and transcript endpoints returned
`Access-Control-Allow-Origin: *` in the October 2, 2026 acceptance check; a live
browser test confirmed collection without a proxy or separately hosted service.
If that policy changes, or a managed network blocks the service, live collection
will show failures. Exported collections can still be imported locally.

Only dates and source paths are sent to UN endpoints. Topic and regional filtering,
analysis and export run on the user's device. This is on-demand collection, not
a scheduled crawler, a complete search of all UN websites, or an authenticated
shared workspace. No secrets, account or paid backend is required.

Each observation is an original source segment from the transcript service,
not automatically a complete national address. Procedural interventions remain.
Only English transcript tracks are used; these may be interpretation or automatic
transcription. Non-English, unavailable and failed sources are recorded. Unmapped
affiliations are retained under All regions / Unmapped, rather than guessed from
text. Speaker region is the existing analytical geography in
`un/config/countries.csv`, not official UN group membership or topic geography.

Limits: 31 inclusive days, 300 selected meetings, 15,000 segments, 20 million text
characters, 25 MB per source response, 45-second request timeout. A failed daily
inventory or failed meeting is explicit in coverage. Data collected within limits
may still produce a partial report, with a coverage warning. No missing source is
treated as a non-match. Cancel releases no partial report. Transcript publication
can lag proceedings; an empty inventory is not evidence that no meeting occurred.

## Methods and denominators

Date, scope, English language and region filters precede deduplication and matching.
NFKC-normalized text with whitespace collapsed is deduplicated within that eligible
corpus, preserving a duplicate-to-retained-ID mapping. Case is preserved for this
exact-text operation. Near duplicates are not detected or removed. All matching
uses NFKC, lowercase Unicode letter/number tokens and contiguous phrase boundaries.

| Selectable method | Calculation |
| --- | --- |
| Regional frequency | Matched unique segments / eligible unique segments, by speaker region |
| Daily frequency | The same denominator by date; dates with no eligible collected segments are omitted |
| Length distribution | Unicode token counts in matched segments, in four displayed bins |
| TF-IDF | Lowercase unigrams longer than two characters, fixed English stop list; TF = 1 + ln(count), IDF = 1 + ln((1 + N)/(1 + df)); L2-normalized vectors; top 20 mean weights across matched segments |
| Cosine similarity | All pairs of matched TF-IDF vectors, top 10 reported; skipped with an explanation above 300 matched segments |

These are descriptive summaries of an observed corpus with dependent segments.
No population confidence intervals, significance, causality, diffusion, coordination,
or inferred stance is claimed. BERT and frozen D1 methods are not ported or run here.
The browser engine (`browser-descriptive-1.0.0`) does not change their gates,
full-corpus representations, source artifacts, or reviewed-model evaluations.

## Reuse, provenance and privacy

Collection export schema is `un.browser.corpus.v1`. Required record fields are
`id`, `date` (YYYY-MM-DD), `country`, `region`, `language`, `scope`, `meeting`,
`text`, `source_url` (HTTPS), and `text_sha256` (SHA-256 of UTF-8 text).
The top-level `records` and `coverage` arrays are required. Live exports also
include source response hashes, JSON pointers, timestamps and collection scope.
Imported hashes are recomputed before analysis; metadata and identity are still
user-supplied, not authenticated. An imported collection cannot supply dates or
scope it never collected; a mismatch is prominently reported.

Analysis JSON retains exact parameters, method outputs, coverage, duplicates and
all matched evidence. HTML previews the first 100 matched segments with expandable
full text. JSON and CSV include all matches. Keep collected transcript files on
your own device or approved storage; they are not automatically published or
submitted. The public repository contains only code and country metadata.

The content security policy permits same-origin assets and the UN transcript
origin. No third-party chart library, tracking service, arbitrary URL proxy or
central review submission is introduced. Existing review-packet functions remain.

## Validation

Run `node tools/test_browser_analysis.cjs` for deterministic calculations and
collector failure/cancellation tests. Browser acceptance checked a real September
22, 2026 General Debate collection, all five methods, downloadable HTML/JSON,
region filtering on reimport, hash-tamper rejection, cancellation, stale-result
export disabling, existing practice review and 1440/390-pixel layouts. Test
queries are engineering checks, not human-reviewed substantive findings.

Recommended next step: run one narrow substantive query, inspect the full source
segments for false matches and missing affiliations, then decide whether additional
browser methods or an authenticated backend for D1 are warranted.
