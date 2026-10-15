# Source-bound semantic representation research (engineering-only)

Chosen candidate: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (Apache-2.0; 384-dimensional multilingual sentence embeddings; nominal 128-token input truncation). It is a practical CPU-capable baseline, **not** a diplomatic stance model. Cross-language quality, negation and issue-position discrimination require separate validation. Exact checkpoint revision, tokenizer and all file hashes **NOT VERIFIED**: do not execute empirical comparisons until a local immutable checkpoint manifest with revision and SHA-256 for every model/tokenizer artifact is supplied. Never use a moving `main` checkpoint. CPU memory and latency are hardware- and batch-dependent; benchmark before production use.

Local inference is opt-in and strictly offline (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `local_files_only=True`). The local loader verifies `config.json` against a supplied SHA-256; complete artifact hash verification is a prerequisite for scientific runs. No download or remote inference is performed.

Core pipeline: NFC normalization, deterministic fixed-character segmentation (fixture path only), batched inference, length-weighted mean pooling, L2 normalization, atomic SHA-256 verified cache replay and read-only metadata adapter. **Production segmentation must instead use the pinned tokenizer with <=128 token windows and explicit overlap policy**; the character segmentation is not checkpoint-safe. Cached vectors and text are private local artifacts; do not commit them. Cache identity includes source and selection hashes. Comparison refuses different source IDs, source hashes, text hashes, units, order or missing observations. Cross-model comparison intentionally uses distinct representation IDs; within-model replay must preserve identity.

Synthetic contrast design: paraphrase; explicit negation; common diplomatic protocol with different substantive positions; same issue/opposite policy; short versus long restatement. These are *test requirements*, not verified checkpoint performance. No accuracy or clustering-stability claim is made by the deterministic fixture test double. Clustering/ARI, multilingual tests, tokenizer-length handling, pinned dependency lock and complete checkpoint hash manifest remain NOT RUN / NOT IMPLEMENTED.

Run: `cd research/semantic_representations && python3 -m unittest -v test_pipeline.py`. Standard-library tests require Python 3.11+. Optional local inference requires an independently pinned `sentence-transformers`/PyTorch/Transformers environment; no dependency reproducibility claim is made until lockfiles and artifact checks are established.

Coordinator: review only this namespace; validate source schema lineage and eligibility with W1; compare same-observation TF-IDF/PCA/LSA outputs via an explicit lexical adapter before any browser integration. Do not merge on fixture-only results as evidence of empirical semantic performance. Never publish source-bearing vectors, private text, withheld October 5–6 material or empirical comparisons. Similarity is not agreement, stance, influence or causality.


## October 15 continuation: verified local controls

Additional files: `controls.py` and `test_controls.py`. The checkpoint manifest must have an exact 40-hex Git revision and enumerate **every** local checkpoint file (including tokenizer artifacts); changed, extra or symlinked files fail verification. `local_model.load_local(checkpoint_path, manifest)` now calls this verifier before importing Sentence Transformers and forces offline environment flags. `encode_local` applies bounded tokenizer-aware windows and reports manifest identity; it does not silently truncate. Do not use the original character-window `pipeline.encode` as a production checkpoint executor.

On a separate synthetic local runtime, `python -m unittest discover -v` on the new `controls.py` and `test_controls.py` returned **3 tests passed**. The published repository's full six-file suite, latest-head CI and actual-model execution remain **NOT RUN**. The fixture-only case called `negation` validates abstention metadata and rank accounting, **not** model negation competence. Full synthetic scenario corpus (paraphrase/protocol/opposite position/length), cluster comparison, all attempted-fit denominators, pinned dependency lock and W1 interoperability are still pending.

Commands:

```bash
cd research/semantic_representations
python3 -m unittest discover -v -p 'test_*.py'
```

Checkpoint assets remain private and must not be committed. Training and test partitions must be declared before testing representation-dependent clustering. Local-source hashes cannot substitute for official upstream source selection receipts.
