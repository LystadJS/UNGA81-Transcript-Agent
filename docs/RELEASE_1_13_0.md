# Browser 1.13.0 — reliable briefing workflow

The browser remains the primary application. Open the [report builder](https://lystadjs.github.io/un/transcript-agent/), choose proceedings, collect public transcripts, inspect the source-linked briefing and descriptive statistics, then save the collection for later import. No installation, coding or external AI endpoint is required.

## Changes

- Conservative country-expression handling expands abstention around negation and ambiguous policy objects.
- Meeting summaries retain their declared source scope when analytical region filters are applied. Saved single-meeting collections recover their meeting identity on import.
- Date-range and topic reports receive an opening descriptive briefing grounded in retained source counts and evidence.
- Collection recovery preserves collected material independently of successful analysis.
- README, browser guidance and reproduction instructions consistently lead with the browser workflow and current release.

## Release checks

Pages deployment now requires the offline quick-reader acceptance workflow, including the browser briefing regression suite and synthetic browser checks. These checks use artificial source responses; they do not establish live UN availability or general classifier accuracy.

Live collection monitoring runs separately every Monday at 11:17 UTC and on manual dispatch, using the harness's fixed October 1 development date. A service failure remains visible in that workflow without blocking deterministic release acceptance. This does not schedule collection on users' computers. The reserved October 5–6 transcripts remain unopened.

This release record describes the implementation and required checks. Newly executed results and deployment URLs belong in the release handoff or linked CI run; historical acceptance records are not fresh validation.

## Validation executed on 16 October 2026

Sixteen Node regression entry points passed, including the new briefing and collection recovery suites, the existing quick-reader context tests, and all main browser numerical method suites. Synthetic Edge acceptance passed 13 recovery/reopen checks and 12 meeting-reader checks. A fresh live Edge run against the fixed October 1 development meetings passed 27 checks, collected 92 passages from two meetings, and reported no page errors. Desktop and 390-pixel layouts, local analysis, source exports and reimport were exercised. These are engineering checks, not accuracy estimates or independent human review.

The public build passed its numerical bundle and country registry integrity checks. The existing public artifact scanner returned no findings after canonical LF checkout handling; `.gitattributes` now preserves consistent public text bytes across Windows and Linux while retaining the existing frozen byte rules. No original source downloads or private browser outputs were added to the repository, and the reserved 37 meetings remained unopened. GitHub CI and deployment results must be verified separately from these local checks.

## Remaining limits

The briefings are deterministic orientation templates, not unrestricted generative summaries. Counts describe observed transcript segments, not complete national speeches or diplomatic intent. Local expression cues require inspection of their source wording and do not establish official votes, adopted agendas or government positions. Exploratory statistics retain their existing publication and interpretation gates.
