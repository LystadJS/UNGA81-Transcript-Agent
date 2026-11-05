# Day-summary development repair

The owner-confirmed three-day development review identified four related failures in the deterministic day-summary engine: literal source-derived topic fragments, broad catalog labels that joined different policy questions, meeting administration entering substantive output, and collective statements inheriting the spokesperson's national affiliation.

The repaired engine is `un.day-summary.v1.2-reviewed-policy-questions`. It uses the development review only for repair and does not open or inspect the reserved 5–6 October meetings or any untouched test sample.

## Implemented changes

- Source-derived candidates now require a self-contained action object. Anaphoric, incomplete, generic and administrative objects are withheld. Reviewed phrases route to stable policy-question identifiers instead of retaining transcript fragments.
- Broad subjects are split into narrower policy questions. The splits cover peace-operation mandates versus troop participation, human trafficking versus treaty-review mechanisms, conflict spillovers versus peaceful nuclear applications, and occupied-territory business accountability versus statehood or settlement policy.
- Procedural filtering now recognizes document edits, footnotes, credentials, speaking limits, floor requests, debate scheduling, meeting formats and similar administration even in long automatically punctuated sentences.
- Explicit speaker-group metadata creates a collective attribution. Claims and evidence display the group, retain the recorded national affiliation as provenance, and exclude the statement from country participation and country-topic cells.
- Proposal and disagreement cues no longer treat organizational names, biographical descriptions, reported advocacy, or requested condemnation as a second independent claim type.

## Development replay

The replay used the same 12 registered meetings, 439 retained source segments and source hashes as the owner review.

| Check | Before repair | After repair |
|---|---:|---:|
| Generated topics | 114 | 65 |
| Literal source-derived topics | 84 | 0 |
| Owner-marked missed/misrepresented evidence routed to named topics | — | 57 of 59 |
| Reviewed erroneous same-topic merges separated | 0 of 4 | 4 of 4 |
| Reviewed collective attribution errors retained as collective | 0 of 21 | 20 of 21 |
| Reviewed unsupported claim passages removed from displayed claims | — | 23 of 27 |

The remaining collective-attribution case is removed as non-substantive. Of the four previously unsupported passages that remain as claims, three now use named topics and corrected claim types or collective labels, while one is a source-bound proposal whose former topic label was malformed. Two owner-marked topic passages are withheld: one is same-meeting programme-budget administration and one is an anaphoric clause that cannot identify its policy object without cross-sentence context.

These are development-replay diagnostics, not new owner labels or a replacement acceptance result. The repaired output requires another owner review before any empirical rate can be reported. The untouched test remains sealed until the repaired development output is reviewed and the one-action browser receipt is produced.

## Validation

- `node tools/test_day_summary.cjs`: 23 synthetic checks pass, including dedicated fragment, policy-boundary, procedural and collective-attribution cases.
- Registered development replay: 3 days, 6 bodies, 8 meeting types, 12 meetings and 439 retained source segments; reserved transcripts opened: 0.
- Public repository content contains rules, synthetic tests and source-free aggregate diagnostics only. Source-bearing owner review and replay files remain private.
