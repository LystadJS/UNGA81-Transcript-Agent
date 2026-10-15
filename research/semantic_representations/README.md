# Semantic representation validation — engineering-only draft

This is an offline, source-bound research namespace. No empirical UN transcript outputs,
private vectors, browser changes or publication authority are provided.

## Repository-pinned model decision

The preferred future production backend is the already accepted local CPU ONNX encoder
in `research/semantic_review/**`, **not** a separately downloaded multilingual model.
It uses `sentence-transformers/all-MiniLM-L6-v2` at immutable revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, Apache-2.0, 384 output dimensions,
256-token input (254 original WordPieces plus special tokens). Check its independent
ten-artifact `model-lock.json` and dependency pins before any actual use.
The selected encoder is English-biased and cannot substantiate multilingual quality,
negation competence, diplomatic agreement, stance or influence. Actual checkpoint
execution **in this PR**: NOT RUN. Do not perform a remote inference call.

## Committed implementation

- `pipeline.py`: fail-closed original-source identity, UTF-8 hash-basis and split/selection
  checks, deterministic restartable SHA-checked vector caching, denominator accounting
  and strict mismatch refusal; the production tokenizer is inherited from pinned ONNX.
- `controls.py`: synthetic-only complete-artifact inventory checker, bounded tokenizer
  window checker and negative-control rank ledger.
- `local_model.py`: read-only exact-Git-blob-verified bridge to the accepted upstream
  ONNX encoder, with exact runtime dependency checks and offline networking guard.
- `comparison.py`: read-only same-observation lexical-versus-semantic neighborhood
  comparisons, seeded medoid sensitivity, ARI, failure ledger and missingness denominators.
- `interchange.py`: metadata-only browser adapter and relational checks; does not
  register an unauthorized W8 producer or export private text/vectors.
- `fixtures.py`, `cli.py`: deterministic synthetic contrast cases and offline CLI
  with independent-process replay.
- `cluster_sensitivity.py`: additional seeded synthetic medoid partition diagnostics,
  label-invariant ARI, denominator and failed-fit accounting.
- `test_pipeline.py`, `test_controls.py`, `test_cluster_sensitivity.py`:
  83 synthetic tests, no private transcript inputs.

To run committed tests:

```sh
cd research/semantic_representations
python3 -m unittest discover -v -p 'test_*.py'
python3 -m compileall -q .
```

**Execution distinction:** local worktree includes a larger prepared, independently
tested integration (83/83 Python 3.13.5 synthetic tests; CLI fixture replay PASS),
but that entire worktree has **not yet been committed to this PR**. Do not attribute
those 83 tests or its imported ONNX adapter to the current GitHub head.
The newly committed `cluster_sensitivity.py` plus its test module were independently
run locally: **4/4 tests PASS**.

## Current acceptance blocks

1. Run existing applicable upstream regressions and exact-head CI. No workflow
   currently validates this worker namespace. Full multi-host dependency wheel hashes
   and actual ONNX inference in this workstream remain NOT RUN.
2. Independently validate the official parallel JSON schema and source-relational
   integrity against coordinator-approved synthetic interchange envelopes.
4. Authenticate eligible original development source receipts independently before
   real source comparison. Missing/withheld inputs are unknown, not negative findings.
5. Keep PR draft, no empirical publication, no D1 O1–O5 gate changes, and no
   access to the 37 reserved October 5–6 transcripts.

The coordinator owns shared interfaces, registry schemas, site loaders, workflows,
release manifests and portfolio deployment. Similarity is not agreement; cluster
stability is not significance; missing evidence is not zero issue occurrence.
