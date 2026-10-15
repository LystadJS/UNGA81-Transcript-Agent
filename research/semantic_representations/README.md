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

## Current committed implementation

- `pipeline.py`: deterministic fixture segmentation, restartable SHA-checked vector
  caching, source/selection/schema identity and same-observation overlap safeguards.
  **Character-window segmentation is fixture-only**, not a model-safe production token policy.
- `controls.py`: synthetic-only complete-artifact inventory checker, bounded tokenizer
  window checker and negative-control rank ledger.
- `local_model.py`: opt-in offline SentenceTransformers loader with artifact inventory
  check; this early adapter is **not** wired to the accepted upstream ONNX implementation.
  Do not run it on empirical sources.
- `cluster_sensitivity.py`: seeded synthetic medoid partitions, label-invariant ARI,
  denominator and failed-fit accounting. Descriptive diagnostics only.
- `test_pipeline.py`, `test_controls.py`, `test_cluster_sensitivity.py`:
  synthetic unit tests, no private transcript inputs.

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

1. Replace the early local loader and character fixture-only inference path with
   the upstream exact-blob-pinned ONNX adapter; verify model artifact hashes and
   runtime package identity. Do not invent checkpoint execution.
2. Integrate complete authored contrast corpus, read-only archived lexical baseline
   adapter and full source-relational checks under this owned namespace.
3. Run the **committed head** test suite, existing applicable upstream regressions
   and exact-head CI. No workflow currently validates this worker namespace.
4. Authenticate eligible original development source receipts independently before
   real source comparison. Missing/withheld inputs are unknown, not negative findings.
5. Keep PR draft, no empirical publication, no D1 O1–O5 gate changes, and no
   access to the 37 reserved October 5–6 transcripts.

The coordinator owns shared interfaces, registry schemas, site loaders, workflows,
release manifests and portfolio deployment. Similarity is not agreement; cluster
stability is not significance; missing evidence is not zero issue occurrence.
