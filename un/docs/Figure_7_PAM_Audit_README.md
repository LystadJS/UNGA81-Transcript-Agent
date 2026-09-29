# Figure 7 — PAM clustering audit

`R/Figure_7_PAM_Audit.R` renders a stored M09 audit artifact. It does **not** fit PAM, collect data, call an API, or modify the email.

The figure shows:

1. mean silhouette across the frozen k=2..6 candidate grid;
2. selected cluster sizes and the minimum-size engineering screen;
3. mean roster-deletion adjusted Rand stability by k; and
4. selected cluster sizes, medoids, minimum clusterwise Jaccard, and medoid-retention fraction.

Detailed country assignments are deliberately kept in `audit/pam/country_assignments.csv` rather than squeezed into the figure. The footer states that the result is audit-only and that stability diagnostics are not confidence intervals.

Run:

```sh
Rscript --vanilla R/Figure_7_PAM_Audit.R PATH_TO_COMPLETED_RUN
```
