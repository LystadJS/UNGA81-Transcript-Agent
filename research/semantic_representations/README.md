# Semantic representation research — source-bound offline adapter

**Status:** engineering-only draft; no new UN transcript inference, publication, or holdout evaluation. Everything added by this PR lives in `research/semantic_representations/**`. The earlier four-file scaffold was replaced because its character-boundary tokenization, unverified model selection, and weak comparison/cache identity were not release-safe.

## Model selection: reuse the existing verified local encoder

The project's existing `research/semantic_review/` implementation already supplies a reviewed, hash-pinned **`sentence-transformers/all-MiniLM-L6-v2`** ONNX CPU encoder. Reuse it rather than downloading an unverified multilingual checkpoint or mutating its source. Exact revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; Apache-2.0; 384 output dimensions; English-only comparison policy; 256-token model sequence limit (254 WordPieces plus CLS/SEP). The full ten-file manifest and tokenization configuration reside in the immutable upstream `research/semantic_review/model-lock.json` (Git blob `04eb74595d88f82c13fc8d3d66e2e0962d1d2156`). Key artifacts:

| Artifact | SHA-256 | Bytes |
|---|---|---:|
| `onnx/model.onnx` | `6fd5d72fe4589f189f8ebc006442dbb529bb7ce38f8082112682524616046452` | 90,405,214 |
| `tokenizer.json` | `be50c3628f2bf5bb5e3a7f17b1f74611b2561a3a27eeab05e5aa30f411572037` | 466,247 |
| `config.json` | `953f9c0d463486b10a6871cc2fd59f223b2c70184f49815e7efbcab5d8908b41` | 612 |

The adapter verifies Git blob identities for `encoder.py`, `model-lock.json`, and `requirements.txt` before using the upstream implementation and validates *every* listed model file through the upstream verifier. Runtime packages are fixed in `requirements-local.txt` and independently checked for exact versions. The upstream tokenizer has unsafe 128-token defaults: the verified encoder disables both padding and truncation and partitions all original WordPieces into at most 254-token windows. Masks, CLS/SEP pooling, chunk normalization, length-weighted aggregation, final L2 normalization, source offsets, and chunk hashes use the existing implementation unchanged. This workstream neither modifies that encoder nor adds an inference endpoint.

**Limits:** this English-biased model has not been validated for general multilingual diplomatic text, negation, stance, or source/protocol dependence. Synthetic code-point handling does not constitute learned tokenizer testing. Existing historical execution evidence and benchmarks in `docs/SEMANTIC_COMPARISON.md` are **inherited**, not newly executed by this PR. Prior measured peak memory (~1,009 MiB) is environment-specific; 90.4 MB is only the ONNX artifact size. Local mode requires Python 3.13, a pinned CPU runtime, an authenticated local model directory, and provisioned private storage.

The earlier concurrent branch changes introduced `controls.py`, `test_controls.py` (three deterministic integrity/rank checks), `cluster_sensitivity.py` and `test_cluster_sensitivity.py` (four independent fixture-only tests). These files are retained unmodified by this continuation. The second medoid implementation operates on Euclidean fixture geometry, while the source-validated `comparison.py` uses cosine distances; do not combine their results as separate model-family votes. Their generic SentenceTransformer candidate remains **unselected**: the executable CLI uses the already-pinned ONNX implementation, which has an upstream validated source hash and exact runtime pins. `controls.py` is an auxiliary synthetic-only diagnostic and does not bypass the locked `LocalEncoder` verification.

## Distinct components

- `pipeline.py`: validates immutable original UTF-8 text hashes *without rewriting source text*; requires declared source schema/hash basis, original source IDs, selection, frame, Unicode parent bounds, split, availability/exclusion/missingness, unit of analysis, and provenance. Rejects holdout rows, unverified speech attribution, duplicate IDs, missing sources treated as negatives, and incompatible model/encoder code. Per-observation, atomic vector caches allow partial restart; corruption fails closed. Vector SHA-256 and all attempted/failed batches are recorded.
- `local_model.py`: read-only, exact-Git-blob-checked bridge to the existing pinned ONNX/WordPiece implementation, installed dependency checks and offline socket guard. No download function is called.
- `fixtures.py`: openly labeled deterministic, **non-neural** tokenizer/vectorizer test doubles. Authored synthetic paraphrase, negation, same-issue/opposite-position, shared procedural wording, and long-text cases. Their scores do not measure MiniLM quality.
- `comparison.py`: refuses incompatible source hashes, hash bases, selection, units, population, order or representation bases; counts failed/unpaired cases; compares cosine neighborhoods with optional same-source-group exclusions; deterministic medoid diagnostic, label-invariant ARI, seed sensitivity and failed-fit accounting. Geometry is descriptive, not inference.
- `interchange.py`: read-only saved lexical TF-IDF/PCA/LSA adapter with exact fitted-transform hashes (never implicit refit); synthetic structural and relational checks for `un.parallel-analysis.v1`; `un.semantic-readonly.v1` metadata-only export with **no vectors or text**. Public export refuses any development source metadata. This is an experimental *consumer*, **not** an unregistered W8 producer of `un.parallel-analysis.v1`.
- `cli.py`: explicit synthetic or pinned-local mode, private cache/output **outside the public repo**, immutable outputs and no network access.

## Run

```sh
cd research/semantic_representations
python3 -m unittest discover -v -p 'test_*.py'
python3 -m compileall -q pipeline.py local_model.py comparison.py interchange.py fixtures.py cli.py controls.py test_pipeline.py test_controls.py
python3 cli.py synthetic --cache /tmp/unga81-semantic-cache --output /tmp/unga81-semantic-fixture.json --k 3
```

To perform actual checkpoint inference **only on authenticated and authorized local development inputs**, first provision the existing exact model using the upstream public-only downloader and its ten-file manifest. Then (Python 3.13):

```sh
python3 -m pip install -r research/semantic_representations/requirements-local.txt
python3 research/semantic_representations/cli.py local \
  --frame /private/development-frame.json \
  --model-dir /private/verified-minilm \
  --lexical /private/archived-lexical-fit.json \
  --cache /private/semantic-cache \
  --output /private/semantic-readout.json --k 3
```

`/private/...` paths are placeholders, not provisioned files. Do not run against original or reserved sources without upstream W1 source and split authorization. CLI output is private read-only metadata; vector files are private under the cache. Existing `site/analysis-core.js`, `site/latent-core.js`, `research/corpus/contract.cjs`, and W1 validation remain authoritative. The interface intentionally cannot claim independent source validation merely by receiving user-authored SHA strings.

## Engineering acceptance and limitations

See `VALIDATION.md` for run-specific evidence and `RUN_CONTRACT.md` for data schema and integration prerequisites. Unit tests and restart smoke run on wholly synthetic data. Real checkpoint execution in **this new workstream** remains **NOT RUN**, since the authenticated local model files and private development-source package are unavailable to this environment. The existing repo's earlier pinned inference is acknowledged but not reused as a new result. Dependency wheel hashes and transitive lock state remain external to this adapter; exact versions are enforced, not independently reproduced. Historical CI for `research/semantic_review/**` is not same-head CI for this new subtree.

The 37 reserved 5–6 October transcripts, original source hashes, owner decisions, D1 O1–O5, research publication manifests and all shared browser entry points remain untouched. Similarity ≠ stance/agreement; cluster stability ≠ significance; clusters ≠ coalitions; graph proximity ≠ influence; absent or missing source ≠ negative issue mention.

**Coordinator request:** independently compare this PR's exact head and exclusive paths with latest `main`; run its synthetic suite and the official v1 relational validator on synthetic exports; inspect independent CI on that head; verify original development source and selection receipts privately before enabling any real comparison. Coordinator alone may assign a new analytical producer ID/schema or wire a browser consumer. Do not merge based solely on an attractive fixture geometry.
