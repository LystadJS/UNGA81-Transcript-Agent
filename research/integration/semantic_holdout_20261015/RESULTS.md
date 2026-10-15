# Separate coordinator-authored synthetic stance holdout — adverse results, 2026-10-15

**Disposition: FAIL promotion criteria for S1 and S2.** Research model head **not merged**. This is a source-free, explicitly synthetic test, not a human-adjudicated or representative external holdout.

## Frozen-before-test provenance

- Design protocol committed `7555ab4265988845cf1358c13493266d6847fca8`, before the 42 synthetic family/label manifest, evaluator or any observed scores.
- Original invented fixture and labels committed at `28b9046265932cc9744152f2c0ba3ee67a049298`, before evaluation. Exact fixture SHA-256: `981585bb38bbc0308311684a19b4ebde986c720c42712caf40783de7a8c08933`.
- Original PR #66 worker head `e79c5ba8f53a651bc56b78a36b09d71a0d743854`, all worker source blobs copied *unchanged* into a coordinator-owned full-repository effective tree. No code or threshold tuning was undertaken after holdout inspection.
- Native GitHub Actions [run #38814221353](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38814221353), job `116694713947`, effective-tree SHA `35c7b7f63e3d5cd58a388f3ee8ac7b7717b15673`: SUCCESS, Python 3.13, pinned original MiniLM/ONNX artifacts and dependencies, prior 108 worker native tests, four fixture-corruption negative controls, original 120-row development example replay, and two fresh independent-process holdout evaluations.

## Full denominators, including adverse cases

Exactly 42 constructed synthetic families, four variants each: 168 unique text observations. **18 evaluable** families (6 direct, 6 indirect, 6 nested negation); **24 guard** families (6 attributed/third-party, 6 conditional, 6 changed proposition scope, 6 cue-free). Guard opportunities: **72** pair scores across 24 families × 3 candidate comparisons. All **168/168** text observations encoded; **0** failed model batches, missing encoded rows, or not-fitted rows.

| Method | Correct / 18 evaluable | Incorrect reversed / 18 | Abstained / 18 evaluable | Complete guard family abstentions / 24 | Unsupported confident guard-pair scores / 72 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pinned MiniLM cosine (M0) | 1 | 17 | 0 | N/A (always computes relatedness) | N/A (relatedness, not a stance claim) |
| Synthetic-source-matched TF-IDF cosine (L0) | 0 | 18 | 0 | N/A (always computes relatedness) | N/A (relatedness, not a stance claim) |
| S1 polarity-gated MiniLM | **6** | 0 | **12** | **18** | **18** |
| S2 signed-lexical representation | **6** | 0 | **12** | **18** | **18** |

On the 6 **direct** families S1/S2 ordered correctly. On the **6 indirect** and **6 nested-negation** evaluable families S1/S2 abstained, so no correct score may be imputed. On the attributed, conditional and cue-free guard families S1/S2 appropriately abstained (18 families × 3 comparisons = 54 pair abstentions); on **6 changed-proposition-scope families they improperly emitted 18 confident scores**. This falsifies the required guard behavior. These errors must not be erased by assuming proposition IDs or renaming the holdout strata.

The preregistered advancement requirements were **≥16/18 correct**, **≥23/24 complete guard-family abstentions**, **0 unsupported confident guard-pair scores**, zero silent failures, all negative controls passing and identical cross-process output. **Both S1/S2 FAIL promotion**; they do not merit a subsequent independent synthetic validation or any authentic diplomatic stance evaluation in their current form.

## Replay, trace and limitations

Two separate Python processes returned byte-identical full JSON receipts. Exact full-receipt SHA-256:

`d30195d26198dfb71d7a5d2e2fa555bcce9f5842cba276c43b0d1e29f739b1cf`

Fixture/label SHA-256:
`981585bb38bbc0308311684a19b4ebde986c720c42712caf40783de7a8c08933`

The coordinator CI run logs contain per-stratum counts and overall status; a subsequent identical pinned re-run includes a full per-case receipt artifact containing **only invented observation identities and numerical scores**, no text or real source artifacts. The artifact run and ID are recorded separately once verified.

**Limitations:** coordinator-separated authorship does not equal independent human labeling or a representative holdout; authored same-direction paraphrases have not undergone third-party semantic equivalence adjudication. S1 and S2 share one parser and synthetic proposition identifiers. Source-matched L0 was newly fitted to the synthetic 168-row holdout, not to the historical archived TF-IDF/LSA reference. Raw M0/L0 cosines are relatedness, not stance classification, so their 72 guard numeric scores are not counted as 72 false stance assertions. Cross-platform reproducibility and real-world transfer remain unestablished. No post-hoc candidate revisions made.

**Privacy and scientific controls unchanged:** no original UN PDFs, Harvard speech member bytes, private source-linked passage rows, held-out meeting text, sealed 37 October 2026 transcripts, human-reviewed labels, empirical model fits, publication, website mirror or D1 O1–O5 modifications. PR #66 remains draft and unmerged.

## Durable complete per-case receipt

Independent repeat [Actions #38814466662](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38814466662) SUCCESS, job `116695540077`; 108/108 existing worker tests, four holdout corruption refusals, pinned MiniLM checkpoint and two-process holdout replay PASS. The unchanged fixture SHA-256 `981585bb38bbc0308311684a19b4ebde986c720c42712caf40783de7a8c08933` and full numerical result SHA-256 `d30195d26198dfb71d7a5d2e2fa555bcce9f5842cba276c43b0d1e29f739b1cf` reproduced across the independent GitHub-hosted run.

**All 42 per-case scores, family strata, incorrectly confident outputs, and abstentions** were preserved in GitHub Actions artifact `pr66-separate-synthetic-holdout-ledger`, [artifact ID 12009717529](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38814466662/artifacts/12009717529). It contains only source-free invented observation IDs and scalar/aggregate evaluation fields; no original text, embedding vectors, private rows or credentials. Artifact has finite retention (30 days); full evaluator and frozen fixture remain committed indefinitely on this coordinator test branch, with immutable hash commitments above.
