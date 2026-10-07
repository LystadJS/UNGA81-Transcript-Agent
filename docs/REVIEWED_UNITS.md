# Reviewed speech excerpts — 7 October 2026

The owner completed all 24 pilot choices. Twelve excerpts from three speeches
were included with unchanged boundaries. Six audio readings were supported, five
were marked as discrepancies and one was unclear. No included excerpt overlaps
a disputed or unclear interval, so none is withheld in this pilot. These are one
owner's recorded decisions, not independent agreement or blanket audio verification.

## Use the reviewed input

1. Open the [report builder](https://lystadjs.github.io/un/transcript-agent/#analyze).
2. Expand **More options** and choose **Reviewed speech excerpts** as the transcript
   source. Select the prepared `reviewed-analysis.json` on your device.
3. Leave Topic blank for all approved excerpts, use September 22–28 and General
   Debate, then choose the methods and settings to inspect. The acceptance example
   uses PCA, three k-means clusters, three UMAP neighbors, ten meeting-group refits
   and three NMF components. These are workflow checks, not optimized settings.
4. Generate the report. Inspect parent coverage, group counts, source offsets and
   the small-sample warning before interpreting a plot.
5. Download the report, analysis JSON or CSVs. **Save reviewed bundle** preserves
   exact input bytes for re-import. **Audio review record** saves the separate ledger.

The bundle includes the original full collection, packet text/audio and saved
choices. It stays local; it is not part of either public Git repository. Treat an
export as containing those materials. The browser needs no upload or additional
service for this import. A plain derivative file alone does not carry enough
source/review evidence to validate its lineage; the separate bundle is intentional.

## Provenance and refusal conditions

`un.reviewed-speech-analysis.v1` stores the three exact UTF-8 input strings plus
the `un.reviewed-speech-units.v1` derivative. On every import the browser checks
the original collection's byte hash and individual text hashes, the packet hash
and audio clip hashes, parent IDs/text/metadata, every review identity and choice,
and the complete regenerated derivative. Unknown/duplicate choices, incomplete
reviews, changed parents, invalid/future review times, overlapping approved spans,
changed offsets or derivative text all fail validation. Disputed/unclear audio
overlaps are withheld. Hashes establish consistency, not reviewer authentication.

The analysis adapter restores meeting scope, language and meeting title from
each original parent; review scope is kept separately. It freezes the validated
collection and refuses direct use of unvalidated derived records. No correction,
normalization or offset conversion changes stored excerpt text. Feature extraction
and deduplication retain their existing documented normalization policy.

The report records input, eligible-before-deduplication, eligible-unique and
included passage/parent/meeting counts separately. Its coverage table describes
the imported windows before query filters. Removed duplicate IDs retain their
parent and offset mapping. Source, cluster, NMF and hierarchical-leaf exports
retain original parent IDs and offsets; full lineage is in analysis JSON.
Meeting/affiliation resampling inherits original parent metadata, keeping a
parent's children together. No row-level split is introduced.

| Parent speech | Approved excerpts | Original text covered |
|---|---:|---:|
| Palau | 4 | 39.7% |
| Fiji | 4 | 27.9% |
| Vanuatu | 4 | 17.3% |

Coverage measures Unicode code points, not audio duration or sentence accuracy.
These twelve purposive windows are not complete partitions or a representative
sample. Each unique retained excerpt has equal analytical weight; a parent with
more retained excerpts contributes more observations. Three source meetings remain
three source meetings regardless of how many refits are run. This pilot validates
the import, calculation and export workflow; it does not select a winning model.

## Correction provenance

`un.audio-review-ledger.v1` records the original parent/span/text, recording link,
clip hash and time range, owner decision, listening attestation, reviewer, review
time and verbatim note. It records all twelve outcomes, including the five
discrepancies. Notes can cover partial spans or describe a problem instead of
providing final wording, so `replacement_text` remains null and no wording is
applied. The packet and choice hashes connect the ledger to its evidence.

Applying a correction requires an explicit original span and replacement text,
then a new corrected version with alignment to the original. That editor/version
operation is still future work. Do not substitute a machine transcript, inferred
name or plausible date. The original corpus and prior 460 type choices are
unchanged, including the earlier suspected-transcription classification.

## Reproduce

```text
node tools/prepare_reviewed_analysis.cjs original-corpus.json speech-pilot.json speech-pilot-review.json new-private-output
node tools/test_browser_reviewed_units.cjs
node tools/test_reviewed_units_ui.cjs built-site new-private-output/reviewed-analysis.json new-private-browser-output
```

Preparation refuses to overwrite an output directory. The browser test also
accepts the deployed site URL. Engineering fixtures explicitly identify themselves;
the real run uses only saved owner choices. See the
[validation record](reviewed-units-validation.json).

Next: saved-run and full-parent/excerpt comparison with coverage and weighting
shown explicitly. Broader performance claims need more reviewed speeches and
independent meetings. The remaining unclear audio and precise correction wording
can be resolved separately; this packet's review is complete.
