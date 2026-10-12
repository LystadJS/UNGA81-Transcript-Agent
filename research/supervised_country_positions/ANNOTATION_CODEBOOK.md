# Supervised country positions — first human annotation round

**Status:** Draft annotation instructions, versioned under pilot_protocol.v1.json. The operative classifiers remain unpublished and do not run on these materials.

## Annotation unit

A single **original-source-backed passage** is reviewed against **one precise proposition**. A source ID identifies a versioned General Debate speech and a recorded country affiliation; it does not authenticate a real-world speaker as a person or establish the government's overall policy.

First record **issue relevance**; then record **stance on that exact proposition** only if relevant. Look at the quoted passage and its adjacent original-source context. Use the source link to check who actually speaks, whether the speaker speaks for a collective grouping, and whether language quoted from a different state is adopted by this speaker. If this cannot be established, code *insufficient*, not neutral.

## First two propositions

| Proposition ID | Question | Do not treat as equivalent |
| --- | --- | --- |
| **cub_embargo** | Does the speaker explicitly support ending the **U.S. economic embargo against Cuba**? | A general comment about Cuba, unilateral sanctions, trade restrictions affecting a different state, or humanitarian concerns without a Cuba-embargo action/object link |
| **ukr_sovereignty** | Does the speaker explicitly support **respect for Ukraine's sovereignty and territorial integrity**? | Generic peace language, mention of a ceasefire, quotation of a Security Council document without endorsement, or unrelated uses of “territorial integrity” |

Other draft propositions in propositions.v1.json remain outside this initial pilot. A statement mentioning the issue can support, oppose, qualify or merely discuss it. Each assessment must identify the *target*, *action* and *speaker attribution*. This is **not** a forced U.S.-versus-China alignment coding scheme.

## Label meanings

| Task | Label | Reviewer test |
| --- | --- | --- |
| Issue | relevant | Passage genuinely addresses the specific proposition or its directly related policy object, even if no position is adopted |
| Issue | not_relevant | Passage does not discuss this proposition; a keyword hit alone is insufficient |
| Issue | insufficient | Source span, policy object, translation or attribution cannot be resolved |
| Stance | support | The speaker **adopts** a clear supporting position on the exact proposition |
| Stance | oppose | The speaker **adopts** a clear opposing position on the exact proposition |
| Stance | conditional | The stated position depends on an explicit condition or qualification |
| Stance | descriptive | The issue is discussed with no clear adopted position |
| Stance | insufficient | A position cannot responsibly be determined |

**Important:** Issue non-relevance is a negative *passage-level relevance* decision, not a negative country-level position. Missing text, an unspoken issue and an unavailable original do not imply an opposing stance.

## Fictional training examples only

The examples below are invented teaching sentences, **not UN quotations or human gold labels**.

| Fictional utterance | For proposition | Correct illustrative coding | Rationale |
| --- | --- | --- | --- |
| “Our delegation calls for an end to the United States embargo on Cuba.” | Cuba embargo | Relevant; support | Explicit policy action and object |
| “Our delegation favors maintaining the existing embargo on Cuba.” | Cuba embargo | Relevant; oppose | Explicit continued restriction |
| “Cuba has faced several economic challenges.” | Cuba embargo | Not relevant; no stance | No embargo action/object |
| “The ambassador quoted a third country calling for an end to the embargo.” | Cuba embargo | Relevant; descriptive or insufficient | Quotation cannot automatically be attributed as the speaker's endorsement |
| “We reaffirm that Ukraine's sovereignty and territorial integrity must be respected.” | Ukraine sovereignty | Relevant; support | Directly adopts the proposition |
| “We discuss possible ceasefire procedures for Ukraine.” | Ukraine sovereignty | Relevant; descriptive | Mentions the crisis but not the named sovereignty position |
| “We would support Ukraine's territorial arrangements only after a negotiated agreement.” | Ukraine sovereignty | Relevant; conditional | Explicit qualification |

## Instructions to the sole human reviewer

1. Confirm the source passage and its surrounding original context. Reject collective or unclear attribution rather than treating a country's metadata label as authenticated policy.
2. Select issue relevance **without** referring to a lexical-sampling route, machine suggestion, reference-actor alignment or estimated country position.
3. Select a stance if warranted and write a rationale identifying the exact action, target, who asserts it and any contrary language. Record contextual ambiguity explicitly.
4. Export the private review draft. Check the voluntary **“I personally reviewed”** box only if you actually made those decisions; unconfirmed exports are draft backups, not reviewed evidence. An owner-attested record is **not independent reviewer agreement or adjudicated external gold**.
5. Do not open the reserved October 5–6, 2026 meeting contents. Store every original excerpt, human choice and review JSON outside the public checkout.

## Pilot and statistical boundaries

The first round targets 96 development, 32 calibration and 32 untouched test proposition–passage pairs: 48/16/16 per proposition respectively, subject to actual source availability. The test packet remains sealed until an explicit review decision, and creating it requires the --authorize-test-review flag. Lexical screening selects roughly 70% of each sampling packet for coverage of likely mentions, with 30% unfiltered controls to detect recall loss. **These sampling routes are not labels or population prevalence weights.**

The country/source-family grouped, chronological split is frozen *before* reviewing substantive labels and is a stringent transfer test. Only eligible 2016–2023 original-PV-strong English General Debate source versions are considered; unverified sources, inconsistent speaker capacities and 2024–2025 modality changes are withheld. The original-PV source-quality manifest must come from a real private audit, not a fabricated verifier.

An issue-specific baseline or M12/M17 real fit is **not enabled** by collecting annotations. Separate human-label and source-dependence validation, calibration, untouched evaluation and release approval remain mandatory.
