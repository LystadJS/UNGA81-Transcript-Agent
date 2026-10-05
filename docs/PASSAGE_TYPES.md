# Passage-type review and substantive-subset comparison

**The substantive subset has much weaker separation than the complete corpus.**
The high full-corpus agreement scores do not establish thematic groups among
speeches. This comparison keeps the original collection unchanged and records
source-type decisions in a separate mask. On October 5, 2026, the owner completed
all 460 explicit decisions; the fixed comparison was rerun without provisional opt-in.

Open the [visual comparison](https://lystadjs.github.io/un/transcript-agent/passage-audit.html).
The [reviewed inclusion mask](passage-type-reviewed-mask.json), [inspection notes](passage-type-inspections.json)
and [reviewed comparison data](passage-type-reviewed-comparison.json) preserve source IDs, hashes,
proposed types, exclusions, settings and denominators. No new thematic labels,
supervised model training or daily publication gate was introduced. [NMF is now implemented](NMF.md).
The original [provisional mask](passage-type-mask.json) and [comparison](passage-type-comparison.json) remain unchanged as historical evidence.

## Review status and source units

**All 460 passage types have explicit reviewer-declared confirmations.**
The review changes `asset/k17/k17s3dutob#2` from uncertain to possible extraneous
transcription. Its complete text is “Try again.” No inclusion membership changes.
This is source-type review, not validated thematic labels or audio authentication.
The owner remains the sole reviewer/finalizer; no independent agreement is claimed.
Every record received a reproducible structural screen. Additional text inspection
covered 319 records: 201 opening/middle/closing-window checks, 85 full short-text
checks and 33 boundary/context checks. The other 141 short procedural candidates
remain rule-screened. All 204 records of at least 500 whitespace-separated words
received structural or boundary inspection. Long speeches were not exhaustively
fact-checked. Audio was not verified.

The fixed input is the saved September 22–28, 2026 General Debate collection:
460 original source segments, six meeting assets, no exact-text duplicates in the
existing eligibility/deduplication step. Two one-word records have zero usable
TF-IDF terms, leaving 458 clustering observations in the complete corpus.
Source dates and affiliations are retained as recorded; this exercise does not
authenticate them. A segment is not necessarily a complete national address.
The substantive subset includes institutional addresses as well as national ones;
194 segments must not be described as 194 countries or independently verified speeches.

| Confirmed type | Segments | Strict subset | Broader boundary check |
| --- | ---: | --- | --- |
| Substantive address segment | 194 | Included | Included |
| Chair/introduction/procedure | 229 | Excluded | Excluded |
| Right of reply | 26 | Excluded | Excluded |
| Mixed substantive/procedural segment | 3 | Excluded | Included |
| Address fragment | 1 | Excluded | Included |
| Possible extraneous transcription | 4 | Excluded | Excluded |
| Uncertain/insufficient text | 3 | Excluded | Excluded |

Replies can contain substantive positions. Their exclusion defines the address
comparison, not a judgment of irrelevance. Review them as a separate population
for questions about exchanges between delegations.

## Consequential boundary decisions

- [Assembly president's opening remarks](https://transcripts.un.org/en/asset/k17/k17s3dutob?t=56:19)
  are stored in `asset/k17/k17s3dutob#5`. The segment combines substantive remarks,
  agenda management and the introduction of Brazil. The exact saved source link is
  retained in the mask; no text was trimmed.
- Ecuador's `asset/k1b/k1b5jwwa58#30` combines a chair introduction with Ecuador's
  substantive address. A country affiliation alone would miss that mixture.
- The Assembly president's closing `asset/k1k/k1kfcwu5kc#40` combines substantive
  remarks with reply procedure and a floor call.
- Egypt's `asset/k1u/k1ukg04uyo#42` is a 39-word closing continuation of `#41`,
  which ends mid-sentence. It is retained separately; no merging was performed.
- Palestine's `asset/k18/k18iyhzwip#7` introduces a prerecorded statement; the
  substantive address follows in `#8`. Cabo Verde's `asset/k16/k16g777u83#9`
  announces a language switch. These short segments are procedural candidates.
- `asset/k17/k17s3dutob#0`, `#10` and `asset/k18/k18iyhzwip#33` contain song/show
  playback wording. The last also contains legitimate chair language. These are
  **possible** transcription problems, not verified errors. Original text and
  source links remain available for audio/context review.

The fixed screening rules use chair wording and neighboring reply announcements,
not just affiliation or length. Long greetings of thanks are not chair procedure.
Short floor calls are inspected with neighboring segments. Unknown cases stay
explicit. The saved inspection overrides are hash-bound to this collection;
they cannot be silently applied to changed text or another corpus.

## Fixed comparison protocol

The three inclusion policies are complete corpus (460 records / 458 usable),
strict substantive (194 / 194), and broader boundary check (198 / 198). Included
records preserve original text, IDs, hashes and order. Vocabulary, IDF and PCA/LSA
are refitted for each policy, as they would be for a new analysis population.
This changes both source composition and sample size; it does not isolate a
causal effect of removing procedure.

Every policy uses 20 retained components, both representations and all five
methods: k-means, PAM, Ward, average linkage and HDBSCAN. Fixed partitions use
`k=4`; HDBSCAN uses EOM, minimum group size 15 and density neighbors 5, including
self. Seeds remain 42 for k-means/UMAP and 31415 for resampling. No settings were
tuned to improve these results.

Each of the **30 full fits** has 30 full-refit, whole-meeting samples, for
**900 sampled fits**. All samples completed. The same six meeting keys and the
same 30 omission schedules are used across policies and representations; five
meetings enter each sample. Repetition reuses six unique omissions, not additional
independent evidence. UMAP stays outside the stability loop.

### Separation and stability on the strict subset

| Method | Full PCA / LSA mean ARI | Substantive PCA / LSA mean ARI | Substantive PCA / LSA silhouette |
| --- | ---: | ---: | ---: |
| k-means | 0.959 / 0.961 | 0.597 / 0.430 | 0.109 / 0.102 |
| PAM | 0.834 / 0.836 | 0.453 / 0.603 | 0.064 / 0.071 |
| Ward | 0.963 / 0.902 | 0.511 / 0.570 | 0.093 / 0.097 |
| Average | 0.937 / 0.546 | 0.664 / 0.419 | 0.092 / 0.067 |

Average linkage remains highly uneven: PCA sizes **184, 3, 4, 3** and LSA sizes
**189, 1, 3, 1**, out of 194. More balanced partitions do not by themselves
establish useful themes; the other methods' separation and stability also need
cautious interpretation.

### HDBSCAN: coverage before agreement

| Policy | PCA groups / unassigned | LSA groups / unassigned | PCA / LSA samples with assessable ARI |
| --- | --- | --- | ---: |
| Complete | 219, 61, 29, 50 / **99** | 221, 61, 31, 50 / **95** | 30 / 30 |
| Substantive | 27, 22 / **145** | 32, 26 / **136** | 23 / 13 |
| Broader boundary check | 28, 21 / **149** | 30, 24 / **144** | 19 / 13 |

Only **49/194 (25.3%)** substantive passages are assigned under PCA and
**58/194 (29.9%)** under LSA. Seven PCA samples and 17 LSA samples contain no
selected groups. They are valid all-unassigned fits and still contribute pair
exposure. Conditional mean ARI is 0.972 / 0.983 on the assessable samples, not
on all 30. Those high conditional values must not be presented without the low
coverage and all-unassigned sample counts. The broader boundary check does not
restore broad assignment coverage.

All strict-subset passages belonged to one full-corpus HDBSCAN group. Therefore
full-versus-subset HDBSCAN ARI is unassessed under the requirement for two
represented groups in both fits; the JSON records this reason and transitions.
The fixed-partition comparisons also report the number of full-corpus groups
represented in the shared subset. Restricting a full fit and refitting a subset
are different operations.

## Unassigned passage inspection

The complete-corpus PCA unassigned set contains **86 procedural candidates,
9 replies, 3 possible transcription problems and 1 mixed closing segment**.
The LSA set contains 85 procedural candidates, the same nine replies and the mixed
segment. No strict substantive candidate is unassigned in either complete-corpus
fit. The union of those sets is 99 records and received focused text/context checks.

After refitting the substantive subset, many clear address candidates become
unassigned in both representations, including Brazil, the United States, Jordan,
Türkiye, Kyrgyzstan and Qatar. Their structural windows still show addresses;
noise status supplies no basis for excluding them as irrelevant. Angola, Honduras,
Bolivia, Senegal, Slovenia and Australia illustrate assignment changes between
PCA and LSA. The packet can filter specifically to passages unassigned in the
substantive subset, and the visual report links every such source.

Assigned examples are also broad: the PCA representatives are Finland and
Mozambique; the LSA representatives are Norway and Mozambique. Their source
windows address several issues. Common terms include general institutional and
development language. No thematic names were assigned to those groups.

## Review and reproduce

The local `review.html` packet is a self-contained file with original full text,
neighboring source segments, suggested type, source links and full/subset
HDBSCAN status. It needs no server. Its default view prioritizes boundary cases
and unassigned passages. Select a type, enter the reviewer name/role and choose
**Record decision and next**. **Next without recording** leaves it pending.
Save the review JSON before closing; **Resume saved choices** restores it.
Suggestions never become human confirmations merely by opening or saving the page.

```sh
python tools/passage_type_audit.py prepare corpus.json review-output \
  --inspections docs/passage-type-inspections.json \
  --analysis full-analysis.json --subset-analysis subset-analysis.json
node tools/compare_passage_types.cjs corpus.json review-output/mask.json comparison-output --allow-provisional
python tools/render_passage_comparison.py comparison-output/comparison.json comparison.html
python tools/passage_type_audit.py import corpus.json review-output/mask.json passage-review.json reviewed-mask.json
```

The comparison rejects incomplete confirmation by default. `--allow-provisional`
explicitly permits exploration using proposals plus any recorded human decisions;
it cannot convert proposals into human labels. Once all decisions are confirmed,
rerun without that flag. Imports reject duplicate/unknown IDs, changed text,
wrong corpus hashes, missing explicit decisions and invalid reviewer/timestamp
fields. Reviewer identity is declared, not authenticated. Import writes a new
mask and leaves the corpus, previous mask and review file intact.

## Validation and limits

[Validation evidence](passage-type-validation.json) includes six Python tests for
source integrity and review import, Node comparison checks, and offline browser
acceptance of saving/resuming a synthetic decision, rejecting a mismatched file,
source filters and desktop/mobile presentation. Those historical tests used a provisional mask. The [reviewed validation](passage-type-reviewed-validation.json) records the new completed import and rerun. All 15 detailed numerical fit files (30 representations, 900 grouped refits) exactly match the earlier fit files; only type metadata changes. Both GitHub deployments passed, and the same browser
checks passed against the published comparison. Original corpus bytes, each text hash, exact ordered subset
membership, assignment totals and the shared meeting schedule were checked.

Independent Python reconstruction reproduced all ARI/Jaccard and pair counts
across the 20 subset fits (600 sampled fits). HDBSCAN's single-linkage geometry
and selection on the identical tree pass the existing independent checks.
An independent scikit-learn PCA fit assigns Monaco to the other selected group
under a tied merge resolution; its noise mask is unchanged. The LSA strict fit
matches fully. This is the documented cross-library tie sensitivity, not evidence
of a reviewed thematic distinction.
The broader PCA fit also matches fully; the broader LSA independent fit has a
tied-order membership difference with the same noise mask. Both reference
records preserve those differences rather than claiming universal label identity.

**Share with caveats:** the comparison is reproducible exploratory evidence.
Source types are now confirmed by the owner; excerpts do not verify the full factual content
or audio. The smaller corpus, refitted representation, few meetings and conditional
density agreement all limit interpretation. Consider replies separately and retain
representative unassigned examples. Inspect the [NMF comparison](NMF.md) before
assigning component names; passage-type confirmation does not approve themes.

## Use the confirmed choices remotely

In the browser workspace, choose **Saved collection**, load the original collection,
then choose **Reviewed substantive addresses** (194) or the broader reviewed policy
(198). Load the completed `passage-review.json`. The browser validates the exact
collection hash, every ID/text hash, explicit decisions and reviewer timestamps.
Incomplete or mismatched reviews stop the run. Save transcripts retains all 460
original records; the analysis records excluded IDs separately.
