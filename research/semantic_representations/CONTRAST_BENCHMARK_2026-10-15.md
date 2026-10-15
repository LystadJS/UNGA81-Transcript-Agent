# Pinned MiniLM synthetic contrast benchmark — 2026-10-15

**Status: executable checkpoint reproducibility PASS; meaning-sensitive ordering FAIL (0/4). Engineering-only synthetic receipt.** Do not merge or interpret these authored fixtures as empirical diplomatic evaluation.

## Exact provenance

- Model: `sentence-transformers/all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; ten upstream original files verified against pinned byte sizes/SHA-256. ONNX CPU, Python 3.13 and six exact dependency pins.
- Independent GitHub-hosted complete checkout [Actions run 38768653323](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38768653323), coordinator-only `coord/pr66-effective-tree-20261015` commit `6ed7eee507030594c25f658e1c21d2e99146d761`. Worker implementation source blobs unchanged.
- Two separate Python processes independently loaded real checkpoint, encoded sixteen synthetic observations, performed a cold-cache calculation, and produced identical rounded vector receipts and synthetic similarity summaries. Each process: attempted cases 4, encoded observations 16, failed batches 0. Rounded-vectors SHA-256 `933bb4a90ee284e3cb619885e027822817a66ecaf2389c33cb0be9e685a114ec`. This is within-host two-process replay, not bitwise cross-platform portability.
- Long-input/no-truncation and cold/warm 16/16 cache verification PASS in prior step. All ten model artifacts verified again.

## Synthetic cosine similarity audit

| Synthetic case | Intended paraphrase | Contradiction | Protocol-prefixed contradiction | Paraphrase closer than contradiction? |
|---|---:|---:|---:|---|
| Policy | 0.44782889 | 0.89748404 | 0.76274210 | **FAIL** |
| Ceasefire | 0.59401854 | 0.79671555 | 0.76615820 | **FAIL** |
| Climate | 0.60533271 | 0.93734671 | 0.84360493 | **FAIL** |
| Inspection | 0.64515583 | 0.86819766 | 0.83238784 | **FAIL** |

The four examples are authored, purposive, synthetic contrast cases. Failure of paraphrase-versus-opposition ordering on all four is a concrete **semantic discrimination limitation**, not a statistically calibrated error rate or a basis to infer country positions. The model may still represent topical similarity. No threshold or untested correction may be silently retrofitted; keep contradiction and protocol cases visible as counterevidence.

## Exact downloaded dependency wheels — SHA-256 on GitHub Linux x86-64 Python 3.13

| File | SHA-256 |
|---|---|
| `numpy-2.3.5-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl` | `11e06aa0af8c0f05104d56450d6093ee639e15f24ecf62d417329d06e522e017` |
| `scipy-1.17.0-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl` | `6680f2dfd4f6182e7d6db161344537da644d1cf85cf293f015c60a17ecf08752` |
| `scikit_learn-1.8.0-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl` | `8fdf95767f989b0cfedb85f7ed8ca215d4be728031f56ff5a519ee1e3276dc2e` |
| `threadpoolctl-3.6.0-py3-none-any.whl` | `43a0b8fd5a2928500110039e43a5eed8480b918967083ea48dc3ab9f13c4a7fb` |
| `onnxruntime-1.23.0-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl` | `e2dc1993aa91d665faf2b17772e4e29a2999821e110c0e3d17e2b1c00d0e7f48` |
| `tokenizers-0.22.1-cp39-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` | `e2ef6063d7a84994129732b47e7915e8710f27f99f3a3260b8a38fc7ccd083f4` |

These record exact downloaded wheel identities. No assertion of all transitive dependency hashes or independent OS/platform reproducibility is made. No wheel, source text, embedding, original UN document, transcript, key or private row was uploaded to GitHub.

**Gates retained:** research and statistical identification NOT ESTABLISHED; 37 reserved Oct 2026 transcripts unopened; original source provenance and human decisions unchanged; D1 O1–O5 and empirical publication WITHHELD.

**Recommended engineering next step:** preregister synthetic contrast strata and explicit stance-sensitive follow-on evaluation without selecting thresholds from these four development cases. Retain topical-similarity use with a strong no-stance inference warning.
