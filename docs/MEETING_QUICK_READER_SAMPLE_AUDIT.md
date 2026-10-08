# Development-only single-meeting quick-reader validation — 8 October 2026

## Decision

**The original quick-reader rules required correction before diplomat use.** A seven-meeting, metadata-stratified development review found missing statements and misleading country-linked summaries. The revised code restores substantive coverage, adds source-linked procedural agenda cues, and deliberately withholds broad or group-attributed stance claims that it cannot establish. The output remains a provisional **rule-based orientation**, not certified speaker attribution, transcript accuracy, or official national positions.

The original 37 reserved temporal meetings from 5–6 October 2026 are metadata-only; **zero held-out transcript requests, text reads, model fits, or scores occurred**. No external generative AI API was used. The frozen evaluation lock and daily release gates are unchanged. The previously completed human pilot is also unchanged.

## Selection and evidence discipline

Using the original SHA256-bound development corpus `e8fb980cf638e2aef39d0ca3564836c6120201a059e806ccaaee3fd5cc4f593e`, select the lowest SHA256 of `quick-reader-check-2026-10-08-pre-output|<stratum>|<meeting_id>` among transcript-present development meetings in each **predeclared** stratum: GA plenary, Third Committee, Fourth Committee, Human Rights Council, press briefings, conferences, and treaty bodies. Selection uses no transcript text or quick-reader outputs.

The resulting **seven meetings and 370 source segments** are `ga/81/16`, `ga/c3/81/2`, `ga/c4/81/1`, `hrc/63/37`, `briefing/sg/2026-10-02`, `asset/k1o/k1o86tmojq`, and `asset/k1y/k1yeh656yd`. All dated October 1–2, within the October 1–4 development window. These meetings were not a random sample of all UN meetings; small treaty and conference proceedings cannot estimate general accuracy. The automated corpus check revalidates each segment's SHA256, exact meeting identity, original provenance link, and mapped/unmapped country accounting. The private source excerpts and reviewer notes are **not committed**.

## Material source-linked findings and corrections

1. **Courtesy prefixes excluded substantive national speeches.** Of 370 source segments, **108 segments of at least 40 whitespace words** would have been excluded by the original prefix-only `Thank you`/`Good morning` rule. Some exceeded 1,000 words and contained substantive country remarks. The repaired rule examines the rest/length of the segment; all 108 now enter the provisional substantive-looking pool. It does not pretend every long procedural intervention is substantive or a complete speech.
2. **An explicit group spokesperson could be misattributed to one country.** Original provisional entries attributed collective remarks in `ga/c4/81/1#25` to Iran individually, and `hrc/63/37#85` to Finland individually, despite recorded group affiliation/on-behalf wording. Group-statement metadata and direct first-person group representation now withhold individual-country classifications. A speaker **mentioning** someone else's group statement while expressly adding remarks in a national capacity is not automatically withheld (`ga/81/16#45`). The underlying recorded country affiliation remains in the source layer.
3. **A broad issue word was not necessarily the object of support/opposition.** Several former entries combined a first-person evaluative verb with a distant reference to international law, human rights mechanisms, development, or the Security Council and then described support for the entire issue. The new rule requires a nearby object, checks whether another issue is the closer object, and retains the exact supporting sentence for later contextual review. It errs toward false negatives instead of unsupported country positions.
4. **Contradictions and qualifications must refer to the same proposition.** Synthetic adversarial tests show `support humanitarian assistance` followed by `oppose humanitarian assistance` is described as mixed, whereas support for humanitarian assistance alongside opposition to sanctions is **not** a humanitarian contradiction merely because the sanctions clause mentions food security. Explicit conditions such as `provided that` are marked qualified. Cross-speech divergent wording within a broad issue still cannot establish that positions conflict on the **same measure**.
5. **The original synopsis lacked important named agenda context.** The 37th HRC meeting's presiding record introduces an oral update on **Haiti** and later an interactive dialogue about **Cambodia**. The previous prose described generic human-rights language without identifying either discussion. Source-linked procedural introductions now appear before the theme counts. The Fourth Committee's **decolonization and self-determination** discussion and the Crime Congress's **crime-prevention and justice** language receive explicit issue families; these are text labels, not authenticated formal agenda/outcome classifications.
6. **One country coverage denominator was inconsistent.** A registry-mapped segment with an unresolved region could be in neither mapped nor unresolved count. The repaired classification reconciles `mapped + unresolved = all English segments` for every sampled meeting.

## Observed before and after, same predeclared seven meetings

| Audit diagnostic | Original | Revised | Meaning |
|---|---:|---:|---|
| Source segments checked | 370 | 370 | Same exact source records |
| Long segments excluded for a procedural prefix | 108 | 0 | Lost substantive material restored to eligibility |
| Broad country–issue entries | 9 | 3 | More conservative; **not** an estimate of improved precision |
| Group spokespersons shown as individual country entries | 2 | 0 | Specific observed misattributions withheld |
| HRC Haiti/Cambodia source agenda cues visible | 0 | 2 | Separate discussion contexts recovered from presiding remarks |

All nine original entries were inspected against the full parent intervention and adjacent speaker context. **Two were clearly collective-spokesperson misattributions, six described a narrower policy action as broad support for an issue, and one was a defensible direct expression about the specific sanctions measure.** The revised three entries are source-linked wording indicators about specified actions; they do not establish official country-wide policy. The revised entries include statements newly accessible after the courtesy-prefix correction. These observations are *assistant-conducted source review*, not owner human confirmation, a blind independent adjudication, or a statistical accuracy estimate.

## Automated and browser acceptance

- `node tools/test_meeting_quick_reader.cjs`: original 25 synthetic contract checks.
- `node tools/test_meeting_quick_reader_context.cjs`: 25 new adversarial tests for courtesy, groups, contradictory subjects, direct-object proximity, source pointers and agenda introductions.
- `node research/reference_tests/test_meeting_attribution.cjs`, `node tools/test_meeting_picker.cjs`, and `node tools/test_browser_analysis.cjs`: unchanged regression envelopes.
- `node research/reference_tests/quick_reader_sample_audit.cjs PRIVATE_DEVELOPMENT_CORPUS.json NEW_OUTPUT_DIR`: deterministic development review (private source text and aggregate receipt are kept apart; do not publish private evidence).
- `node tools/preview_meeting_quick_reader.cjs NEW_HTML_FILE` plus `python tools/test_meeting_quick_reader_static.py NEW_HTML_FILE NEW_OUTPUT_DIR`: script-free desktop and mobile browser checks on **synthetic source text only**.

The local full interactive browser harness encountered `ERR_BLOCKED_BY_ADMINISTRATOR` for localhost. An in-memory script-free Chrome render did pass; **it is not a replacement for live browser interaction acceptance**. Run the existing mocked single-meeting UI workflow through GitHub Actions after source changes; distinguish that result from live UN transcript availability.

## Scientific and editorial release boundary

The quick-reader language follows the user's JSL voice principles through a direct anchor, source-linked explanation and immediately adjacent caveat. This is a deterministic template, not a language-model prose rewrite. Country classifications concern only **recorded expressions about nearby subject terms**, not political alliances, general government endorsement, verified speaker identity, stance toward a precise proposition in all contexts, or unanimous meeting decisions. Original source text is never changed. Human adjudication remains advisable before senior policy-facing statements. No 37-meeting held-out protocol parameters were revised.
