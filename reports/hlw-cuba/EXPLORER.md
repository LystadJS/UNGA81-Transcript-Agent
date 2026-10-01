# Embargo candidate lexical explorer

This is a new, audit-only selected-passage experiment. It does not replace the
frozen D1 models, remove the original 500-text research gate, or establish stance.
The existing interface and theme are preserved. No encoder or hosted service is used.

## Reproduce

Install `tools/hlw-explorer-requirements.txt` in a Python environment, then run:

```powershell
python tools/analyze_hlw_explorer.py reports/hlw-cuba
python -m unittest discover -s tools -p test_hlw_explorer.py
```

The ordinary `tools/report_hlw.py` build also generates this analysis and copies
the explorer assets through `tools/hlw_presentation.py`. Its original verified
input corpus is required for the complete report rebuild.

## Scope and units

- General Debate and broader HLW, 21–28 September 2026; background proceedings excluded.
- Four restriction topics, limited to source segments with a Cuba-topic match.
- Repeated topic hits at the same statement/start/end character offsets collapse
  into one point. Distinct passages, including repeated wording from different
  sources, remain. All input passages are retained; no sampling or truncation.
- This is candidate screening. Co-occurrence within a segment is not confirmed
  Cuba-embargo relevance. Recovered ASR/caption drafts have not been merged.
- PCA and clustering use passage text, not country identities or topic labels.
  Cluster sizes count passages, not independent countries or supporting states.
- Overview filters do not refit or filter this fixed experiment. The explorer's
  cluster-count selector and group buttons affect its scatter/inspector only;
  quality comparison and issue-overlap statistics retain their stated populations.

## Methods and interpretation

English unigram TF-IDF uses the installed sklearn English stop list, lowercase,
sublinear term frequency, smooth IDF, and L2 normalization. PCA uses centered full
SVD. The two retained variance ratios are shown, because projected distances lose
information. Clustering uses full-vector cosine distance with average linkage.
Five partitions (k=2..6) are compared by mean cosine silhouette. The default takes
the largest observed score, breaking ties toward smaller k. This is a convenience
for exploration, not out-of-sample model selection. Smallest cluster sizes are shown.

Descriptors are highest mean TF-IDF terms per cluster. Words such as embargo can
dominate because the corpus was selected for restrictions. Repeated speakers,
formulaic wording, English interpretation, ASR errors and length affect patterns.
No significance, causality, legal status, sentiment, alliance or stance is inferred.

The overlap heatmap operates at source-segment grain, distinct from passage grain.
It shows `|A intersection B| / |A union B|` with both counts. Diagonals have 100%
overlap when present. Missing/empty unions are null, not zero. Passage word counts
use Unicode word tokens; quartiles use NumPy's default linear interpolation.

## Provenance

`explorer.json` contains the evidence CSV SHA-256, exact software versions,
selection and methods, all point quotations, original raw hashes/JSON pointers,
statement character offsets, all partitions, and matrix numerators/denominators.
`explorer-data.js` is the same payload for offline rendering. Original evidence,
topic definitions, source corpus and frozen model artifacts are unchanged.

Method references: [PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html),
[hierarchical clustering](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.AgglomerativeClustering.html),
[silhouette](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html).
