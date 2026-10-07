# Development priorities after saved-run comparison

**The next useful gain is a defensible observation population and representation,
followed by evidence that discovered structure survives independent sources.**
The current browser already compares PCA/LSA, k-means, PAM, hierarchical clustering,
HDBSCAN, Gaussian mixtures and NMF; UMAP and metric MDS provide diagnostic displays.
Adding algorithms alone does not resolve selection, dependence or policy meaning.

## 1. Expand reviewed development observations

Use the frozen [corpus contract](PASSAGE_CORPUS.md): 21 development meetings from
1–4 October 2026, with 37 meetings from 5–6 October reserved for temporal evaluation.
Complete the prepared [boundary and attribution review](BOUNDARY_REVIEW.md) and record
complete or near-complete speech partitions, original offsets, omitted text,
speaker/genre/language metadata and uncertain attribution. The reserved transcript
text remains unopened until the evaluation protocol is frozen.

Keep each speech and meeting together when splitting or resampling. Compare
equal-passage and equal-parent summaries before choosing any weighted objective.
Four parents is only the current engine's minimum, not an adequate study size.
New review applies to new sources; the original 24 owner decisions are complete.

**Deliverable:** a coverage matrix by source group and date, an exclusion ledger,
and a frozen development population with enough distinct sources to assess
leave-group-out behavior. Set adequacy criteria in that protocol rather than
inventing a universal sample threshold.

## 2. Compare one semantic encoder with the lexical baseline

Retain TF-IDF with PCA/LSA as the transparent baseline. A practical candidate is
[`sentence-transformers/all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2),
subject to checkpoint/license review, a pinned revision and measured local resource
use. It is a candidate, not newly approved or installed. Its model card specifies
default truncation beyond 256 wordpieces: preserve offset-linked chunks and define
aggregation explicitly rather than silently discarding speech endings.

Sentence encoders are designed for similarity retrieval and clustering; the
[Sentence-BERT paper](https://aclanthology.org/D19-1410/) motivates this distinction
from an ordinary BERT relevance classifier. Compare lexical and semantic fits on
the exact same observations. Use source-linked tests of paraphrases, negation,
boilerplate and opposing positions on the same issue. Similarity is not agreement.

**Deliverable:** a representation comparison with neighborhood retention, grouped
refit stability, coverage and contrary examples. Separate representation choice
from the choice of a two-dimensional display.

## 3. Test structure against a declared reference, then fresh sources

Define the claim before the null model: recurring language patterns, separation
beyond genre/length effects, or reproducibility in new meetings are distinct
questions. Develop nuisance-preserving reference data and known-structure controls,
record the settings searched, and calibrate diagnostics before accessing holdout
text. Random row permutations leave pairwise text geometry unchanged and provide
no cluster-null test.

The [gap statistic](https://statistics.stanford.edu/technical-reports/estimating-number-clusters-dataset-gap-statistic)
illustrates comparison with a reference distribution; its basic reference model
must not be transplanted into sparse diplomatic text without justification.
[Prediction strength](https://statistics.stanford.edu/technical-reports/cluster-validation-prediction-strength)
offers a motivation for out-of-sample partition checks. For this project, splits
must respect the declared source dependence. Stability across seeds measures
computational sensitivity; it is not a significance test.

**Deliverable:** a frozen validation plan, negative controls, recorded failed fits,
and later held-out-source evaluation. Only then consider a consensus association
matrix, with method-family weights and pairwise assignment denominators. Repeated
UMAP seeds must not give one partition additional votes.

## 4. Add graph methods when their diagnostic question is clear

After representation validation, expose **spectral clustering** under an explicit
nearest-neighbor affinity contract, reusing and validating existing research/D1
work where appropriate. Inspect disconnected components, degree extremes, duplicate
effects, neighborhood size and source-group sensitivity. The
[official implementation reference](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.SpectralClustering.html)
documents affinity choices; these project-specific diagnostics remain to be built.

Test **diffusion maps** later as a representation experiment with explicit kernel,
normalization and scale sensitivity. The
[original diffusion-maps paper](https://www.sciencedirect.com/science/article/pii/S1063520306000546)
describes geometric diffusion through a data graph. That is not a model of political
influence or transmission between states. Keep policy diffusion in its separate
event-data and causal-design branch.

**Deliverable:** source-linked neighbor graphs and a sensitivity report that shows
when graph construction, rather than substantive content, determines the result.

## 5. Build leadership views around evidence and uncertainty

Prioritize these views as reviewed coverage and representation support them:

| View | Useful question | Required context |
|---|---|---|
| Actor × component heatmap | Which issues recur across represented actors? | Reviewed attribution, component terms, actual examples, coverage and declared weights |
| Stable/ambiguous/unassigned evidence panel | Which patterns warrant an analyst's attention? | Grouped refit denominators, alternate fits and contrary passages |
| Coverage-aware theme composition | Does apparent emphasis survive equal-speech weighting? | Missing versus zero, defined shares, within-speech coverage; no automatic stance labels |
| Actor profiles across time | Has language changed on a comparable basis? | Frozen reference transform, comparable rosters/genres, held-out periods and uncertainty |

The current release supplies coverage bars and fit-specific component profiles;
these broader actor/time products remain planned. Avoid thematic labels based
only on high-weight terms. An analyst should inspect representative and contrary
passages before a finding enters a leadership report. Statistical nonrandomness,
substantive meaning and policy relevance require separate evidence.

**Recommended next implementation:** validate returned development boundary
choices, freeze the observation and evaluation contract, then add the pinned local
semantic representation. This sequence improves the foundation for later graph
methods and decision-facing visualizations without weakening the daily publication
gates.
