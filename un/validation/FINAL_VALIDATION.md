# Final validation — 2.5.0 D1-I4 clustering checkpoint

**Result:** M09 PAM / k-medoids is implemented on the existing frozen M02 feature space and audited together with M07 hierarchical clustering. Both clustering methods remain **audit-only**. The five-output email firewall is unchanged.

## Runtime actually used

- R 4.6.1
- Matrix 1.7.5
- cluster 2.1-8.2
- Linux/Debian checkpoint environment
- Explicit offline/minimal source profile for replay and engineering validation

Parent checkpoint ZIP SHA-256: `bf41c2f63f27f6a94c55b8b553fd2a26fa513262127cd67a4d26d157d573c1d9`

## Executed validation

| Suite | Result |
|---|---:|
| Base workflow regression | **85 tests; 0 failures** |
| D1 foundation regression | **94 tests; 0 failures** |
| Frozen TF-IDF / PCA / PCoA regression | **101 tests; 0 failures** |
| Hierarchical clustering regression | **58 tests; 0 failures** |
| New PAM regression | **33 tests; 0 failures** |
| **Combined** | **371 tests; 0 failures** |

**34 R scripts parsed successfully** after the PAM addition, including workflow, standalone, rebuild, and audit entry points. The normal Windows acceptance script now invokes all five suites.

## Source-backed clustering audit

Both M07 and M09 were evaluated against the exact same archived frozen M02 artifact:

`3235a50c3d5b9853887ce7da9058d636f963666ca885fcb82cf27175d54f7782`

The independently loaded M07 and M09 distance matrices are identical.

| Diagnostic | M07 hierarchical | M09 PAM |
|---|---:|---:|
| Selected audit k | 2 | 2 |
| Cluster sizes | 38 / 1 | 22 / 17 |
| Mean silhouette | 0.04397 | 0.01498 |
| Mean roster-deletion ARI | 0.573 | 0.71733 |
| Engineering quality gate | Failed | Failed |
| Publication eligibility | No | No |

PAM medoids are **POL** and **BDI**. PAM minimum clusterwise mean Jaccard is 0.84474 and medoid-retention fraction is 0.695. The frozen silhouette gate is 0.15 and mean-ARI gate is 0.75, so the source-backed PAM fit is withheld. It also inherits the replay's source-scope/language/quality restrictions.

Adjusted Rand agreement between the selected M07 and M09 partitions is approximately **-0.0117**. Because both algorithms operate on the same lexical geometry, this disagreement is treated as method sensitivity under weak separation—not as evidence for competing political blocs.

## Publication and email boundary

- Exactly five analytical output slots remain permitted.
- M07 and M09 have no ready producer and cannot populate an email slot.
- Clustering figures, assignments, medoids, candidate cuts, and stability records remain in the audit package only.
- Iran, Cuba, Ukraine, and AI remain fixed watchlist topics.
- Country readouts remain region-first and alphabetical within region.
- No email was sent and no scheduled task was installed.

## Reproducibility

`pam_only.R` recomputes M09 from a trusted frozen M02 artifact without collection, model/API calls, or feature refitting. The reference PAM run executed 500 candidate-replicate fits (5 k values × 100 roster-deletion subsets), with 500 delivered fits and explicit archived stability records.

The prior M07 source audit remains preserved unchanged. The checkpoint comparison script verifies the common M02 identity, common distance geometry, selected partitions, and cross-method ARI.

## Audit incident retained

A full 39-speech end-to-end replay of the expanded checkpoint exceeded the interactive execution window after source preparation. It is recorded in `validation/incidents/d1_i4_full_replay_timeout.log` and is **not** counted as a successful acceptance run. The integrated analytical routing is exercised by the regression fixtures, while M09's complete 39-country numerical audit is independently executed from the frozen M02 artifact. This distinction is preserved rather than represented as a completed full replay.

## Not established here

- Native Microsoft Outlook rendering.
- Windows DPAPI / Task Scheduler behavior.
- Live UN collection or paid model/API execution.
- Production package installation / `renv` restore on the user's Windows system.
- Semantic or geopolitical validity of either clustering method.
- Confidence intervals, causal inference, or independent-country sampling from the roster-deletion diagnostics.

A nonempty live-day Windows acceptance run remains required before replacing an existing scheduled deployment.
