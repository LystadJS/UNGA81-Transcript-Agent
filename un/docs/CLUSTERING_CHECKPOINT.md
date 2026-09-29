# D1-I4 clustering checkpoint

## Frozen common geometry

M07 hierarchical clustering and M09 PAM consume the same country-level L2-normalized TF-IDF matrix produced by M02. Pairwise distance is the Euclidean chord distance on that full feature matrix. Neither method clusters PCA or PCoA coordinates.

The feature reference, vocabulary, IDF, tokenization policy, source snapshot identity and M02 artifact hash are unchanged. The source-backed M07 and M09 audits both bind to feature SHA-256:

`3235a50c3d5b9853887ce7da9058d636f963666ca885fcb82cf27175d54f7782`

Their archived distance matrices are bytewise/numerically identical after loading.

## M07 hierarchical clustering

Primary linkage remains average; complete and Ward.D2 are sensitivity variants. Candidate cuts are k=2..6. The source-backed selected average-linkage audit cut is k=2 with cluster sizes 38 and 1, mean silhouette 0.04397 and mean subset ARI 0.573. It fails size, separation and stability screens.

## M09 PAM / k-medoids

PAM evaluates k=2..6 directly from the same dissimilarity matrix. Selection maximizes mean silhouette among size-admissible candidates; if none are admissible, the best audit candidate is retained without becoming eligible for publication.

For each candidate the checkpoint retains:

- full-data memberships and medoids;
- mean silhouette and cluster-size diagnostics;
- 100 fixed-seed country-roster deletions retaining 80% of countries;
- adjusted Rand agreement against the restricted full-data partition;
- clusterwise best-match Jaccard and evaluability;
- pairwise coassignment/opportunity matrices; and
- medoid retention across successful resamples.

The source-backed PAM audit selected k=2 with cluster sizes 22 and 17, medoids POL and BDI, mean silhouette 0.01498, mean subset ARI 0.71733, minimum clusterwise mean Jaccard 0.84474, and medoid retention 0.695. It fails the predeclared silhouette and ARI gates, plus inherited source-scope/quality gates. It remains audit-only.

## Cross-method audit

The selected M07 and M09 partitions have adjusted Rand agreement about -0.0117 despite sharing the exact same feature representation and distance matrix. This is evidence of method sensitivity in a weakly separated corpus, not independent evidence for two competing geopolitical bloc structures.

No political or diplomatic meaning is assigned to a cluster solely from these algorithms. Country labels and medoids identify source observations, not quality, loyalty, influence, or policy desirability.

## Publication firewall

Both M07 and M09 explicitly set `publication_eligible = FALSE`. There is no M07 or M09 ready producer in the five-output renderer. Passing engineering screens would still leave the clustering artifacts audit-only pending a separately reviewed release design.
