# Figure routing — D1-I4 checkpoint

The original issue figures (1–3), PCA/PCoA figures (4–5), hierarchical figure (6), and PAM figure (7) are generated through separate R scripts. Audit figures do not become reader-facing simply because their PNG exists.

- `Figure_1_Issue_Frequency.R` — audit-only issue prevalence.
- `Figure_2_Regional_Heatmap.R` — audit-only regional issue matrix.
- `Figure_3_Issue_Network.R` — audit-only issue co-occurrence.
- `Figure_4_Country_Discourse_Map.R` — conditional O3 PCA display; only the O3 evidence factory can release exact validated bytes.
- `Figure_5_PCoA_Audit.R` — audit-only PCoA challenger.
- `Figure_6_Hierarchical_Audit.R` — audit-only M07 hierarchy/stability diagnostics.
- `Figure_7_PAM_Audit.R` — audit-only M09 k-medoids/stability diagnostics.

Every figure script consumes a completed run directory. M07/M09 figures never add an email section and are not political or geopolitical group labels. Reproducible image bytes additionally depend on the recorded R/graphics/font environment.
