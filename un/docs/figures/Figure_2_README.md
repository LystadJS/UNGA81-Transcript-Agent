# Figure 2 — regional issue heatmap

**Script:** `R/Figure_2_Regional_Heatmap.R`.

```sh
Rscript --vanilla R/Figure_2_Regional_Heatmap.R output/2026-09-23/r_2_1_validated
```

Inputs under that run: `data/country_issue_long.csv`, `data/countries.csv`, `data/issues.csv`.

Outputs: `data/regional_issue_matrix.csv`, `figures/Figure_2_Regional_Issue_Heatmap.png` (840 pixels wide; height expands with issue count).

Share = present countries / all countries in that region in this run. Each cell includes the raw numerator/denominator; an asterisk marks unresolved codes. These percentages are observed presence, not a claim that unknown cases are confirmed absent. No-country groups are not silently represented as measured zeros. Small regional counts make the figure descriptive, not evidence of a population-level regional difference. Administrative regional mapping is versioned in `config/countries.csv`; this is not a UN diplomatic-bloc map.

Additional required input: `data/plot_context.csv` provides the source/review label printed on the image. Issue metadata includes `fixed` and `fixed_order`.
`data/region_order.csv` fixes columns to the same regional order as the email. The four permanent topics always lead the rows.
