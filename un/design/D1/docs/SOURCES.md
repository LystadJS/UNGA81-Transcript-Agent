# Source register

**Checked 25 September 2026.** Package documentation supports the proposed mechanism or API family, not installation or production validation on the user's computer. Cadences, display caps and release rules in D1 are design choices.

| ID | Source | Relevance |
|---|---|---|
| S1 | User-provided `UN_Daily_Briefing_R_2.1.0.zip`, `docs/UPDATE_2_1.md`, `config/config.json`, `R/03_pipeline.R`, `R/04_email.R`, `R/05_validate.R`, `R/06_policy.R`, `run_daily.R` | Exact current interfaces, fixed-topic order, regional group order, mixed-version replay caveat, immutable output/MIME checks. Original hashes recorded in `validation/source_provenance.json`. |
| S2 | rOpenSci targets manual and CRAN `tar_target` documentation | Dependency-aware execution, dynamic branching, reproducible target seeds and reuse. |
| S3 | tidymodels rsample time-based-resampling vignette and `group_vfold_cv` documentation | Chronological assessment and grouped repeated-observation resampling. Combining these constraints remains an implementation obligation. |
| S4 | CRAN quanteda.textstats `textstat_simil` documentation | Sparse document-feature similarity and cosine/Jaccard definitions. |
| S5 | uwot `umap_transform` documentation | Transforming new observations into an existing reference embedding; reproducibility settings. |
| S6 | CRAN dbscan `hdbscan` documentation | Noise labels, density-based clustering, hierarchy/stability and new-observation assignment. |
| S7 | igraph `cluster_leiden` and `cluster_louvain` documentation | Graph/community methods and compatible edge-weight conventions. |
| S8 | CRAN stm reference and project documentation | Topic models with document-level covariates and new-document inference. |
| S9 | remstimate project documentation | Tie-oriented and actor-oriented relational-event estimation; not a substitute for observed relational-event data. |
| S10 | CRAN blockmodels package documentation | Stochastic/latent block models and explicit distributional choices. |
| S11 | CRAN glmnet `glmnet` documentation | Penalized logistic/multinomial and other GLM families; one-vs-rest multilabel task construction is separately specified. |
| S12 | CRAN depmixS4 package documentation | Hidden/latent Markov and dependent-mixture model framework. |

Machine-readable public source locations:

```json
{
  "S2": ["https://books.ropensci.org/targets/dynamic.html", "https://search.r-project.org/CRAN/refmans/targets/html/tar_target.html"],
  "S3": ["https://rsample.tidymodels.org/reference/group_vfold_cv.html", "https://github.com/tidymodels/rsample/blob/main/vignettes/Common_Patterns.Rmd"],
  "S4": ["https://search.r-project.org/CRAN/refmans/quanteda.textstats/html/textstat_simil.html"],
  "S5": ["https://jlmelville.github.io/uwot/reference/umap_transform.html"],
  "S6": ["https://search.r-project.org/CRAN/refmans/dbscan/html/hdbscan.html"],
  "S7": ["https://r.igraph.org/reference/cluster_leiden.html", "https://r.igraph.org/reference/cluster_louvain.html"],
  "S8": ["https://stat.ethz.ch/CRAN/web/packages/stm/refman/stm.html", "https://www.structuraltopicmodel.com/"],
  "S9": ["https://tilburgnetworkgroup.github.io/remstimate/"],
  "S10": ["https://cran.nics.utk.edu/cran/web/packages/blockmodels/index.html"],
  "S11": ["https://search.r-project.org/CRAN/refmans/glmnet/html/glmnet.html"],
  "S12": ["https://search.r-project.org/CRAN/refmans/depmixS4/html/depmixS4-package.html"]
}
```

`driftmapR` is treated under the user's previously established experimental-adapter and supported-regime constraints. This design did not re-audit the package, restore its scientific runtime, or establish a new production-readiness result. The R runtime used for these design-contract checks is not represented as the pinned runtime of any separate calibration study.
