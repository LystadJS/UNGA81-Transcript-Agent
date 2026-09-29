# Figure 1 — issue frequency

**Script:** `R/Figure_1_Issue_Frequency.R`.

```sh
Rscript --vanilla R/Figure_1_Issue_Frequency.R output/2026-09-23/r_2_1_validated
```

Inputs under that run: `data/country_issue_long.csv`, `data/countries.csv`, `data/issues.csv`.

Outputs: `data/issue_frequency.csv`, `figures/Figure_1_Issue_Frequency.png` (840 pixels wide; height expands with issue count).

Counts one country per issue. Present = 1, absent = 0, uncertain = missing. Non-exclusive categories; no summing to 100%. Share = present / total countries, with unresolved count reported. This measures observed issue presence, not agreement or policy alignment. The first four rows are always Iran, Cuba, Ukraine and AI, including zeros. Remaining rows sort by decreasing presence count with a deterministic label tie-break. Original source/coding evidence stays in the run audit.

Additional required input: `data/plot_context.csv` provides the source/review label printed on the image. Issue metadata includes `fixed` and `fixed_order`.
