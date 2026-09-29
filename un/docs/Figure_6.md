# Standalone hierarchical figure

Run from the release directory:

```sh
Rscript --vanilla R/Figure_6_Hierarchical_Audit.R output/2026-09-23/hc_final_reference
```

Inputs: the trusted, source-bound M07 RDS plus the corresponding M02 RDS under `audit/analytics/artifacts/`. Matrix is needed to read the sparse feature dimensions; R graphics draws the figure. The script does not fit a model, change assignments or use Python.

Output: `audit/figures/Figure_6_Hierarchical_Clustering_Audit.png` (1120 × 960 pixels), containing the average-linkage dendrogram, linkage/k silhouette diagnostics and selected-cut clusterwise subset stability. The point estimates are sensitivity diagnostics, not confidence intervals. A singleton or otherwise underrepresented cluster is labeled not evaluable. Side labels give actual evaluable/total repeats.

ISO3 leaf labels match `audit/hierarchical/country_assignments.csv`, which includes full country names, regions, source observation identities and exclusions. Dendrogram cluster numbers are not longitudinal states. The full-data assignments and all candidate cuts remain in CSV even when the displayed audit cut fails quality screens.

An existing nonidentical image is not overwritten. Reproduce using its matching release/R/graphics environment or choose a new run directory. The image is not embedded in Outlook by this release.
