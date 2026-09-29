# Figure 3 — issue co-occurrence network

**Script:** `R/Figure_3_Issue_Network.R`.

```sh
Rscript --vanilla R/Figure_3_Issue_Network.R output/2026-09-23/r_2_1_validated
```

Inputs under that run: `data/country_issue_long.csv`, `data/countries.csv`, `data/issues.csv`, `data/plot_settings.csv`.

Outputs: `data/issue_cooccurrence_all.csv`, `data/issue_network_nodes.csv`, `data/issue_network_edges.csv`, `figures/Figure_3_Issue_Cooccurrence_Network.png`.

For each pair, require known decisions for every country in the corpus. Otherwise set display Jaccard to missing and exclude the edge; write `unresolved_pair_excluded` in the audit. For fully coded pairs, Jaccard = countries with both present / countries with either present. A zero union produces missing overlap, not an invented similarity. Node area encodes issue prevalence, not influence. Fixed circle positions support visual consistency, not an inferred geopolitical geometry.

Default edge eligibility: complete decisions across the entire corpus, Jaccard >= 0.35 and at least two jointly present countries. Select a maximum-spanning forest of eligible edges, then additional high-overlap edges, capped at 14. Disconnected issues remain disconnected; connectivity is not forced through zero or ineligible edges. The full pair table includes nonselected relationships and the selection reasons. An edge is co-mention, not agreement, direction of influence, causation or alliance. Changes in the daily country population and coding versions can change the map.

Additional required input: `data/plot_context.csv` provides the source/review label printed on the image. Issue metadata includes `fixed` and `fixed_order`.
All topic nodes remain visible, including fixed topics with zero observed presence. A gray minimum-size marker denotes a zero, not estimated positive area. An asterisk denotes unresolved decisions; those topics cannot contribute edges until all their country decisions are known. Parent/subtopic overlap (AI and AI & digital; Iran and Middle East) is partly definitional.
