# Pinned local semantic comparison — 8 October 2026

## Delivered and executed

`research/semantic_review/` adds a source-bound, offline semantic representation
alongside the saved lexical baseline. It is the owner-authorized provisional
machine path: no human upload is required, and no machine choice is relabeled as
a human approval. Browser/site assets, the frozen corpus contract, `un/`, earlier
owner decisions, original source bytes and production publication gates are unchanged.

The official `sentence-transformers/all-MiniLM-L6-v2` ONNX float32 CPU export is
pinned to revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Ten upstream artifacts,
including tokenizer/configuration and model-card metadata declaring Apache-2.0,
are individually SHA256-bound in `model-lock.json`. The ONNX SHA256 is checked
against the upstream LFS digest. No unpinned revision, custom model code, remote
inference API, pickle, model fine-tuning, or quantized approximation is used.

Model reference:
https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/1110a243fdf4706b3f48f1d95db1a4f5529b4d41

## Population and complete token coverage

The prior development checkpoint's 92 file hashes and raw-source re-derivation
passed. Every machine annotation and source identity is unchanged. All **2,057**
baseline-eligible passages were encoded, in **2,059 chunks** covering **318,447
WordPieces**. Two passages exceed 254 content tokens; the longest has 260.
No passage or wordpiece is silently dropped. Strict/inclusive/baseline populations
remain **1,641 / 1,910 / 2,057**. The strict population remains 523 observed source
segments in 16 meetings, not 523 human-verified complete speeches.

The upstream tokenizer JSON has 128-token truncation and padding settings. Both
are explicitly disabled. Full token sequences are partitioned into at most 254
content tokens plus CLS/SEP. All original code-point spans and per-token offsets
are retained. Use mask-aware mean pooling including CLS/SEP, normalize each chunk,
combine with content-token-count weights, and normalize the passage. This declared
long-text aggregation is not a separately validated semantic model. The pinned
uncased WordPiece normalizer is recorded; original text is not edited.

The reserved **37 temporal-holdout meetings remain unopened**. No holdout transcript
was requested, inspected, encoded, fitted or scored. Metadata separation is not
proof of statistical independence or globally unseen pretraining evidence.

## Completed comparison

Six semantic configurations completed: strict raw384/k-means10, PCA32/k-means10,
PCA64/k-means10, PCA64/Ward10, and inclusive/baseline PCA64/k-means10. The fixed
selection and model settings are in `plan.json`; no best-looking configuration was
chosen. Fitting uses normalized high-dimensional geometry, not the display axes.

Pairs retain the exact same usable IDs, order and source hashes. Reduced semantic
fits match saved lexical dimension and algorithm. Raw384 versus LSA64 explicitly
differs in dimension. The existing TF-IDF/LSA arrays are loaded, not silently
refitted. Their reconstruction from frozen vocabulary/IDF/components agreed to
maximum absolute error **4.44e-16**.

| Diagnostic | Result | Interpretation |
|---|---:|---|
| Strict LSA64 vs semantic PCA64, k-means10 | ARI **0.405** | Different, partly overlapping partitions |
| Strict LSA32 vs semantic PCA32, k-means10 | ARI **0.385** | Same-dimensional comparison |
| Strict LSA64 vs semantic PCA64, Ward10 | ARI **0.228** | Representation sensitivity persists under Ward |
| Strict semantic PCA32 vs PCA64, k-means10 | ARI **0.769** | Dimensionality sensitivity, not independent replication |
| Lexical vs raw semantic, 15-neighbor overlap excluding same meeting | **27.9%** | New representation changes cross-meeting neighborhoods |
| Semantic vs lexical meeting-omission refit median ARI | **0.609 / 0.626** | No demonstrated stability advantage |
| Opposite position closer than paraphrase, authored semantic probes | **8/8** | Semantic proximity must not become a stance label |
| Primary 2-D projection, 15-neighbor retention | **7.96%** | Poor local display fidelity; not a coalition map |

All **16** strict-development meeting-omission refits completed. The fixed encoder
is reused; PCA and k-means are refitted without each entire meeting. ARIs concern
overlapping training observations, not prediction for omitted meetings. The lexical
refit values are inherited from the saved prior run and clearly distinguished from
new semantic executions. Semantic refit ARI range is **0.536–0.839**.

Source/agenda dependence remains visible: same-meeting shares among 15 nearest
neighbors are **55.8% lexical**, **57.5% raw semantic**, and **57.8% semantic PCA64**.
These are descriptive diagnostics without a calibrated nuisance null. Eight
synthetic paraphrase/opposition/boilerplate sets are stress cases, not independently
sampled accuracy estimates. All 1,641 cross-meeting neighbor pairs have checked
source links and exact text hashes; excerpts are supplied only in the local package.

## Validation and delivery boundaries

**47 new tests**, **57 previous machine tests**, **53 corpus checks**, and **15 existing
analytical/source suites** passed locally. Two complete CPU inference executions
produced bitwise-identical embeddings and all seven fit/probe archives in the same
runtime. Reusing the source-bound cache reproduced the full numerical comparison.
Independent contingency and pairwise-distance calculations reproduced the primary
ARI and cross-meeting neighborhood overlap. Tests include Unicode/long-tail input,
padding invariance, cache mutation, revision mismatch, network attempts, and
held-out row rejection. Invalid/incomplete executions preserve failure records and
return nonzero status. Cross-runtime bitwise equivalence is not claimed.

The second full run encoded the corpus in **114.4 seconds**, with approximately
**1,009 MiB peak process memory** for the full comparison. These are measurements
from this environment, not guaranteed performance on government computers.

The notebook executes top to bottom and contains five source-backed figures. Its
script-free HTML reading copy is rendered in memory at desktop/mobile widths;
this is not a claim of direct-file browser navigation acceptance. Text-bearing
reports, original data, source examples, caches, and real screenshots are delivered
as conversation artifacts, not committed to this public repository. Model weights
are not in the result ZIP; the downloader retrieves the exact pinned files before
disconnected inference. No public website deployment is needed for this research CLI.

## Reproduction

From the delivered package (Python 3.13 and Node 22):

```sh
python -m pip install -r runtime/research/semantic_review/requirements.txt
python runtime/research/semantic_review/download_model.py model
python runtime/research/semantic_review/compare.py checkpoint/UN_machine_review_results model new-results
```

After model acquisition, inference is offline. To replay the validated vectors
without another encoder pass, append `--cache results/embedding-cache`; all cache
hashes, row identities/order and encoder implementation must match. Check the
saved input lock and `RUN_CONTRACT.md` before changing any settings. The old
machine ledger is not replaced by these outputs.

## Next phase

Develop nuisance-preserving reference tests and freeze a model-specific evaluation
protocol before any separate authorization to open the 37 reserved transcripts.
Continue provisional work without waiting for human adjudication. Keep stance
assessment separate from topic similarity, and do not promote these outputs as
nonrandom diplomatic alignment or as validated coalition/bridge-actor findings.
