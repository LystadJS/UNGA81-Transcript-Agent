# Semantic comparison execution contract

Scope: same machine-only October development corpus; 37 holdout transcripts unopened.
The original corpus, machine ledger, and saved lexical arrays must pass their
checkpoint hashes and the existing raw-source re-derivation validator. The saved
baseline is loaded, not silently refitted. This is neither human adjudication nor
an independent test of the selected themes.

Model: official all-MiniLM-L6-v2 ONNX float32 CPU export at the pinned revision in
model-lock.json, with upstream license declaration and independently checked LFS
SHA256. No custom model code, API inference, GPU, fine-tuning, quantization or
future-corpus training. The upstream tokenizer's 128-token defaults are disabled.
All WordPieces are covered by nonoverlapping chunks of at most 254 content tokens
plus CLS/SEP. Preserve all original code points, source offsets, token spans and
per-chunk digests. Use attention-mask mean pooling including CLS/SEP, normalize
each chunk, take a content-token-count-weighted mean, then normalize each passage.
This long-text aggregation is a declared engineering choice, not a learned model.

Inference includes all 2,057 baseline-eligible passages once, with strict 1,641
and inclusive 1,910 populations selected by the unchanged ledger. Six settings
are enumerated in plan.json. No observation sampling, dimension clamping, weighted
fitting or best-model selection is permitted. Full 384-dimensional vectors and
centered PCA32/PCA64 geometries are distinct representations. Normalize each
retained row before k-means/Ward; cluster labels are arbitrary within each fit.

Compare only exact identical usable IDs, source hashes and order. Pair reduced
semantic fits with saved lexical settings of matching dimension and algorithm.
The unreduced384-versus-LSA64 contrast explicitly differs in dimension. Report
ARI, nearest-neighbor intersection/k at 5/15/30, same-parent/meeting exclusions,
meeting/genre adjusted mutual information, and source-linked neighbor examples.
Do not compare raw distances across representations as a common calibrated scale.

Refit PCA and k-means after omitting each of the 16 strict-development meetings.
The pretrained encoder is fixed and is not adapted. Compare labels on overlapping
training observations. Lexical reference values are inherited from saved refits,
not newly executed lexical fits. Distinguish this from prediction on omitted
meetings and from the unopened 37-meeting temporal holdout.

Eight authored synthetic topic/negation/paraphrase/boilerplate probe sets are
frozen in probes.json before final execution. They are stress diagnostics, not
independent accuracy estimates. They must not be used to tune this model.

Cache replay requires identical passage identity/order, model, encoder code,
array/chunk file hashes, finite unit vectors and pickle-free arrays. Saved outputs
are portable; bitwise reproduction is claimed only when actually checked in the
same runtime and thread configuration. No-overwrite output directories preserve
past attempts. Logs distinguish implementation validation from substantive evidence.

Two-dimensional PCA maps are display-only, with distance and neighbor preservation
measured in the fitted high-dimensional geometry. Poor display fidelity is visible
and does not change the fixed clustering. No deployment or publication gate changes.
