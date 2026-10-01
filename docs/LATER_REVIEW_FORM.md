# Later-date development review form

## Completed review

The owner saved the packet at 2026-10-01 03:49 UTC (September 30 in New York).
Fresh loader verification passed: 24 passages from 22 source records, with 15
relevant and nine not relevant. All 24 were marked as belonging to national
addresses by the owner. The private validated export is
`review-work/ai-later-review/validated-import.json`.

No September 28 passage is included. Neither countries nor exact source hashes
overlap the revised first pilot. Across both development packets there are now
48 reviewed passages: 27 relevant and 21 not relevant. These enriched samples
are not a representative accuracy test. Near-duplicate checks remain necessary.
No model has been trained or released, and this packet was not attached to the
different September 23 daily corpus.

See [completion evidence](../research/validation/i9/later-review-completion.json).
Next: prepare a separate random September 28 review packet, check duplicates
against both development sets, freeze the test labels and evaluate a simple
baseline before fine-tuning BERT. The original preparation instructions follow.

The prepared private form is `review-work/ai-later-review/index.html`, served
locally at http://127.0.0.1:8772/ while its server is running. It contains 24
passages from September 24–26: 12 lexical AI candidates and 12 non-hits.
September 28 and candidates overlapping pilot countries are excluded.

Read each passage, expand the surrounding context and check whether it belongs
to a national address. Other or uncertain interventions must receive the
insufficient-context label; their intervention classification is retained in
the review rationale. This is a human boundary check, not a claim that automated
segmentation already established national-address eligibility.

Then choose relevant, not relevant or insufficient context, optionally add a
note, and confirm the completed review. Browser draft storage survives refreshes
where local storage is available. Download review backup saves a local JSON
copy. Directly opening the HTML supports reading and downloading choices;
final submission requires the local server. No choices are preassigned.

Saving invokes the existing owner-review validator and writes annotations,
finalizations and `pilot-check.json` locally. This packet is not attached to the
September 23 daily run because its source corpus differs. After completion,
validate/export it with the reviewed loader before any downstream use. No model
training or accuracy estimate follows automatically.

To create a new packet from the recovered private candidates:

```powershell
python tools/later_review.py review-work/ai-evaluation-recovered/candidates.json review-work/new-later-review
python tools/pilot_review.py serve review-work/new-later-review --port 8772
```

Use an available port and keep the server running. Existing packet directories
are not overwritten. Raw passages, labels and form tokens remain outside Git.

Validation: 23 existing loader regression tests passed; a copied engineering
fixture rejected an invalid intervention/label combination and successfully
saved and loaded 24 insufficient labels without asserting human review. The
real packet remains unreviewed. Desktop/mobile browser checks verify 24 cards,
blank choices, unchecked confirmation and no horizontal overflow.

Recommended next step: complete this development packet, then prepare a separate
randomly sampled September 28 test packet after checking source boundaries and
cross-partition duplicates.
