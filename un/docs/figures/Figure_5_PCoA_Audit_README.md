# PCoA — standalone figure

```sh
Rscript --vanilla R/Figure_5_PCoA_Audit.R output/2026-09-23/d1_i2_reference
```

Input: `data/pcoa_country_coordinates.csv` from its validated R adapter. Output: `audit/figures/Figure_5_PCoA_Audit.png`, 840 × 720 pixels, and `data/pcoa_label_layout.csv`. No external plotting package is needed. The script never changes numerical coordinates, infers alignment labels, or publishes the plot by itself.

Points use the existing regional groups with both shape and color. ISO3 labels are placed deterministically with leader lines. A label-placement failure returns exit 2; the audit PNG may remain, but it is not eligible for email. The reference/current definition, fit spectrum, policy, source identities and diagnostics are in the same run's `audit/analytics` and `data` directories.

These are lexical projections. Do not interpret a two-dimensional distance as full feature distance, a coalition, an influence score or a policy stance. The source example is explicitly audit-only. PCoA always remains an audit challenger; it cannot replace PCA automatically.
