# Expanded synthetic meaning-contrast benchmark — 2026-10-15

**Decision:** ENGINEERING EXECUTION PASS; MEANING-SENSITIVE VECTOR ORDERING FAIL. Draft-only, never empirical/release evidence.

## Scope, method, evidence

Exactly 16 authored families (original 4 plus 12 prospectively written in `expanded_contrast.py`), each with anchor, paraphrase, contradiction and protocol-prefixed contradiction: 64 distinct synthetic input IDs. Source-matched lexical baseline = a single `sklearn.feature_extraction.text.TfidfVectorizer(ngram_range=(1,2), norm="l2")` fitted to these exact 64 authored synthetic texts. **It is not the historical archived TF-IDF/LSA reference fit.** MiniLM source checkpoint: `sentence-transformers/all-MiniLM-L6-v2` revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, original 10 files verified by immutable hashes, pinned CPU ONNX inference, no external network access during encoding.

Full checkout [Actions #38769887728](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38769887728), job `116542614717` on coordinator test SHA `e0afb8537b3178b0aae320b2ae35b29d1580a620`: SUCCESS. Code from PR #66 is executed in a coordinator-only test tree; original worker source and frozen gates unchanged. Two independent Python processes returned exactly matching full JSON summaries and digest `f84cfce5bb0a2d61bc1ef61d78997942819249be6b33d24f8db3e7fff50ef539`. Source/selection fixture SHA-256 `cfb0208cc0e0d43525904b3bbbda46930b5f03d5b2c0367008f9a19862de2fa8`. All 64 synthetic observations encoded, zero failed batches.

| Readout | MiniLM | Source-matched TF-IDF | Explicit polarity cue (NOT a trained representation) |
|---|---:|---:|---:|
| Paraphrase cosine > contradictory cosine | **0/16** | **0/16** | N/A |
| Hand-coded direction preserved | N/A | N/A | **16/16** authored cases |
| Failed model batches | 0 | 0 | N/A |

**Adverse result preserved:** all 16 MiniLM and all 16 TF-IDF source-matched comparisons ranked contradiction closer than paraphrase. Topic/word overlap dominates both tests. The polarity-cue diagnostic is deliberately constructed using words in these cases (support, endorse, welcome, favors, oppose, reject); its 16/16 is a fixture implementation check with no generalization claim. No model was selected or threshold tuned to this development data. Protocol contamination scores are recorded per case in Actions logs.

## Interpretation and acceptance boundaries

- **PASS engineering:** test implementation, actual pinned checkpoint, hash identity, source-matched input IDs, independent-process replay, result denominators, zero fit failures.
- **FAIL the descriptive meaning-sensitive objective:** these cosine representations must not be used alone for policy agreement, opposition, stance, alliances, government positions or inferential classification. A positive cosine is primarily a descriptive relatedness score.
- **NOT RUN:** archive-frozen real historical lexical transform, independently sampled negative control benchmark, alternative actual stance-trained checkpoint, external language/translation checks, multi-platform wheels/transitive dependency closure, country/source-specific empirical fitting.
- All 37 reserved October 2026 meetings remain unopened. Original source identity, frozen D1 O1–O5, human choices, statistical calibration, release and publication remain unchanged.
- PR #66 stays **DRAFT/UNMERGED**. Next methodological task: freeze a structurally richer development/test distinction, additional stance contrast methods and predeclared metrics before an independent holdout; do not relabel these synthetic examples as a blinded external holdout.
