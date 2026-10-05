# Source inspection and clustering sensitivity

**Average linkage's uneven groups persist across the tested settings.** On the
saved September 22–28, 2026 General Debate collection, changing dimensions and
cluster counts sometimes splits the dominant group, but it does not establish
useful diplomatic categories. Source examples show that procedural language is
part of the structure being recovered.

## What was inspected

The collection contains 460 source segments from six meeting assets; 458 have
usable TF-IDF vectors. No source text, affiliation, date or topic label was changed.
The checks below inspect representative text, not every member of each group.
Affiliations such as `GA` are recorded metadata, not reviewed speaker identities.
Audio was not checked, and these observations are not human-reviewed labels.

| Fit at 20 components, four groups | Source example | Reading of that example |
| --- | --- | --- |
| PAM, PCA/LSA; groups of 84, 47 and 61 | [France/Angola transition](https://transcripts.un.org/en/asset/k17/k17s3dutob?t=6:11:35), [Papua New Guinea/Niger transition](https://transcripts.un.org/en/asset/k1u/k1ukg04uyo?t=5:53:17), [Norway/Guatemala transition](https://transcripts.un.org/en/asset/k1u/k1ukg04uyo?t=11:58:52) | The actual medoids are chair introductions and thanks. Every member of these three groups has recorded affiliation `GA`; that alone does not verify its source type. |
| PAM, remaining group of 266 | [Costa Rica passage](https://transcripts.un.org/en/asset/k1k/k1kfcwu5kc?t=6:00:52) | A long address covers multiple issues. This group is not a single reviewed topic. |
| Ward, PCA group of 82 | [Short opening remark](https://transcripts.un.org/en/asset/k17/k17s3dutob?t=18:48) | The nearest passage to the centroid is only two words. A geometric exemplar can be a poor substantive summary. |
| Ward, group of 196 under both representations | [Guatemala passage](https://transcripts.un.org/en/asset/k1u/k1ukg04uyo?t=11:59:33) | A substantive, multi-issue address sits apart from groups whose examples are introductions. |
| Average, PCA group of 2 | [Opening source segment](https://transcripts.un.org/en/asset/k17/k17s3dutob?t=7:49) | The text refers to songs and a television show. It warrants source/audio review; it is not a verified transcription error. |
| Average, dominant group: PCA 445 / LSA 435 | [Eritrea passage](https://transcripts.un.org/en/asset/k1k/k1kfcwu5kc?t=41:45) | A long speech is the example for a group containing almost the entire collection. |
| Average, small groups of 4 and 7 | [Right-of-reply instructions](https://transcripts.un.org/en/asset/k17/k17s3dutob?t=12:27:26), [Second-intervention call](https://transcripts.un.org/en/asset/k1k/k1kfcwu5kc?t=8:03:37) | Repeated procedural wording forms small groups. |

## Cluster count and component comparison

The fixed grid contains **96 full fits**: PCA/LSA × 10/20/40 components ×
3/4/6/8 groups × k-means/PAM/Ward/average. Each fit was compared with six
leave-one-meeting-out fits, for **576 omission fits**. TF-IDF and the representation
were refitted for every omitted-meeting cohort. These are six distinct omissions,
not 30 independent repetitions. UMAP was not needed to compare partitions.

The full settings, sizes, silhouettes, omission agreement and source IDs are in
[the settings audit](cluster-settings-audit.json). Its input SHA-256 identifies
the saved collection. Deterministic methods consume no clustering seed; k-means
uses seed 42 for full fits and the recorded tool's fixed seed schedule for omissions.
This grid describes sensitivity; it does not select a winner or optimize on labels.

Average linkage's largest group, as a share of all 458 usable passages:

| Components | k=3, PCA / LSA | k=4, PCA / LSA | k=6, PCA / LSA | k=8, PCA / LSA |
| --- | ---: | ---: | ---: | ---: |
| 10 | 93.7% / 93.7% | 93.7% / 90.0% | 50.9% / 50.9% | 50.9% / 50.9% |
| 20 | 97.6% / 97.6% | 97.2% / 95.0% | 94.5% / 92.8% | 89.5% / 90.0% |
| 40 | 98.3% / 97.8% | 97.8% / 97.8% | 96.5% / 96.5% | 93.9% / 93.9% |

Across that same grid, the largest-group share ranges from 23.4–51.7% for PCA
k-means, 20.1–58.3% for PCA PAM, and 42.1–43.0% for PCA Ward. Corresponding LSA
ranges are 26.6–48.9%, 18.8–58.3%, and 42.4–43.0%. More even groups are not
necessarily more meaningful. Ward's persistent large group and PAM's procedural
medoids remain reasons to inspect the sources.

## HDBSCAN density comparison

[HDBSCAN](HDBSCAN.md) does not require `k`. A second fixed grid contains **36 full
fits and 216 omission fits**: PCA/LSA × 10/20/40 components × minimum group size
5/15/30 × density-neighbor count 5/10, using EOM selection. Neighbor counts include
the observation itself. [The density audit](hdbscan-density-audit.json) retains
assignment counts, shared-assigned ARI denominators and status transitions.

At 20 components:

| Minimum group size | Density neighbors | PCA groups / unassigned | LSA groups / unassigned |
| --- | ---: | ---: | ---: |
| 5 | 5 | 9 / 87 | 9 / 83 |
| 5 | 10 | 4 / 114 | 4 / 114 |
| 15 | 5 | 4 / 99 | 4 / 95 |
| 15 | 10 | 4 / 114 | 4 / 114 |
| 30 | 5 | 3 / 73 | 4 / 95 |
| 30 | 10 | 3 / 82 | 3 / 84 |

Across all tested dimensions and density settings, PCA leaves 54–148 passages
unassigned and selects 3–13 groups; LSA leaves 57–138 unassigned and selects
3–11 groups. Raising minimum group size need not increase the unassigned count:
EOM can select a larger parent branch instead of its smaller children.

The default EOM fit (20 components, minimum size 15, density neighbors 5) gives
PCA sizes **219, 61, 29, 50**, with **99 unassigned**, and LSA sizes
**221, 61, 31, 50**, with **95 unassigned**. The source examples still include a
large multi-issue speech and three procedural passages. HDBSCAN does not identify
substantive speeches automatically.

With the same settings except **leaf selection**, PCA instead gives sizes
21, 61, 18, 29, 50 and **279 unassigned**. LSA retains the same full-data groups
and 95 unassigned, but its sampled fits change. Default 30-sample mean stability
ARI is 0.986/0.985 for PCA/LSA EOM versus 0.916/0.827 for leaf. Those ARIs use
only passages assigned in both compared fits; changing coverage can change the
score. A high score on a smaller retained subset is not evidence of better coverage
or a validated classification.

## Recommended next step

Review source type before adding thematic interpretations: substantive address,
chair/procedure, reply, uncertain, or apparent transcription problem. Keep the raw
collection intact and record a separate reviewed inclusion mask with source IDs
and reasons. Compare the present full-corpus run with a reviewed substantive-only
run, including what was excluded and how sizes, assignment coverage and stability
changed. Review both assigned and unassigned passages; neither membership nor
noise status establishes relevance. NMF remains the next planned statistical
method, after this source-composition check.

Reproduce both grids with `tools/inspect_cluster_settings.cjs`; supply the saved
collection and an output JSON path, adding `--density` for the second grid. These
are engineering and source-inspection results, suitable to share with the stated
caveats, not a released decision rule or reviewed diplomatic categorization.
