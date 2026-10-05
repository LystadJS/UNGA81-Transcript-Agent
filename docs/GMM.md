# Regularized Gaussian mixtures

[Open the source-linked comparison](https://lystadjs.github.io/un/transcript-agent/gmm-audit.html)
or [run a collection](https://lystadjs.github.io/un/transcript-agent/#analyze).
Browser engine **1.9.0** adds Gaussian mixtures to **Text clusters and stability**.
Select PCA, LSA or paired comparison, then **Gaussian mixtures**. Choose diagonal
or spherical covariance, component count, variance regularization and starting
points. Enable stability to refit entire source groups.

## What memberships mean

Every usable passage receives one conditional membership per component, summing
to one. These are model responsibilities, not calibrated confidence in a topic,
stance or diplomatic alignment. Highest-membership labels color the existing
maps and feed hard ARI/Jaccard/consensus summaries. No passage is removed by the
ambiguity threshold; GMM does not have HDBSCAN's unassigned/noise status.

The report exposes maximum membership, the gap between the largest two values,
and normalized entropy. The default inspection threshold is maximum membership
below 0.6. Entropy ranges from zero (concentrated) to one (uniform). With one
component, membership 1 and entropy 0 are structural: this is a single-Gaussian
reference, not evidence of a shared theme. Hard ARI and silhouette are withheld
when fewer than two highest-membership groups are represented.

Component summaries retain both hard counts and soft counts (summed memberships),
membership-weighted TF-IDF terms, high-membership source examples and least decisive
passages. Components with no hard members remain in the model. Neither top terms
nor examples supply a human-approved thematic label. Complete vectors, model
parameters, likelihood histories, restart diagnostics and stability denominators
are saved in JSON; Cluster data CSV adds every membership and per-passage refit
sensitivity. Exported visual HTML is standalone and contains no scripts.

## Estimation and limits

The input is the existing L2-normalized unigram TF-IDF representation with
unwhitened retained PCA or LSA scores, not UMAP coordinates. Defaults are four
components, 20 requested dimensions (capped at available rank), five seeded
k-means++/Lloyd starts, 300 EM iterations, seed 42 and additive covariance
regularization 0.0001. UMAP uses separate random state and affects only display.

EM uses log-sum-exp responsibilities and centered weighted variance accumulation.
Diagonal covariance estimates separate spread on every retained axis; spherical
covariance uses one shared variance per component. Diagonal fits depend on axis
orientation, and either family can misrepresent non-Gaussian text geometry. Full
and tied covariance are not implemented. Variance regularization is in squared
retained-score units; changing representations or dimensions changes its meaning.

A start converges when the absolute change in average observed log likelihood is
below 0.00001. Select the largest final likelihood among converged starts only.
A collapsed component (soft mass below 1e-8), nonfinite likelihood or iteration
limit does not silently produce a released fallback. If no start converges, the
fit is skipped with diagnostics. This criterion does not prove a global optimum;
additive regularization can reduce unpenalized likelihood, so no monotonicity claim
is made. Alternate converged starts are aligned and compared separately.

Warnings identify small soft counts (below max(5, dimensions+1)), variances within
10% of the regularization floor, components without hard members, failed starts,
and parameter counts at least as large as the passage count. Limits are 600 usable
passages, 50 dimensions, 1–12 components (fewer than passages), 1–10 starts and
10–1,000 iterations. Existing corpus/filter/review checks still apply.

For k components and d dimensions, parameter counts are 2kd+k−1 (diagonal) and
kd+2k−1 (spherical). AIC = 2p−2 logL; BIC = p log(n)−2 logL, using final regularized
fit likelihood. Compare these only for the same rows, dimensions and representation.
Never use them to choose PCA over LSA, different retained dimensions, or different
inclusion policies. Local fits, variance constraints, dependent passages and
unverified model assumptions limit formal selection claims. No automatic winner
is chosen from the sensitivity grid.

## Shared stability protocol

Thirty whole-meeting refits use the existing schedule (seed 31415, retain 80% of
groups), independently refitting vocabulary, IDF, representation and mixture.
PCA/LSA and covariance alternatives receive the same group samples. Initialization
also varies by refit, so the result combines source omission and optimizer sensitivity.
Six available meeting assets yield five retained meetings per sample and only six
distinct omission sets. Repeated fits are not independent meetings or confidence
intervals. Affiliation grouping is also available in the interactive workspace.

Soft components are aligned one-to-one by maximizing summed posterior overlap
on shared passage IDs. An exact assignment solver handles up to 12 components;
means are never directly matched across independently refitted score coordinates.
Total variation is half the L1 distance between aligned membership vectors: zero
means unchanged, one means disjoint. Reported mean TV averages within each fitted
sample and then across fitted samples. Per-passage summaries retain their own
number of sampled fits. This alignment is descriptive and does not establish
semantic equivalence. Hard ARI/Jaccard/consensus remain separate, with the existing
shared-observation denominators and no two-group ARI for degenerate partitions.

## Reviewed-corpus results, October 5, 2026

The original 460 records remain unchanged. The completed single-reviewer mask
retains 194 substantive records, or 198 when mixed remarks and the speech fragment
are included. The complete policy has 458 nonzero TF-IDF rows after two one-word
records are excluded by the existing vectorization rule. See [passage review](PASSAGE_TYPES.md).

The fixed grid contains **96 fits**: three inclusion policies × two representations
× two covariance models × two variance settings (0.0001/0.001) × four component
counts (1/2/4/6). All produced converged selected fits. Twelve detailed four-component,
0.0001-regularization fits each received 30 successful grouped refits (**360/360**).
These descriptive checks use 20 retained dimensions throughout; they do not select
or validate a deployment model.

| Inclusion | Representation | Covariance | Max membership <0.6 | Mean entropy | Mean hard ARI | Mean soft TV |
|---|---|---|---:|---:|---:|---:|
| Complete | PCA | diag | 0 | 0.005 | 0.876 | 0.076 |
| Complete | LSA | diag | 0 | 0.007 | 0.874 | 0.106 |
| Complete | PCA | spherical | 4 | 0.016 | 0.843 | 0.095 |
| Complete | LSA | spherical | 3 | 0.015 | 0.860 | 0.085 |
| Substantive | PCA | diag | 12 | 0.129 | 0.230 | 0.433 |
| Substantive | LSA | diag | 8 | 0.088 | 0.346 | 0.388 |
| Substantive | PCA | spherical | 0 | 0.033 | 0.406 | 0.291 |
| Substantive | LSA | spherical | 5 | 0.113 | 0.523 | 0.253 |
| Broader subset | PCA | diag | 2 | 0.046 | 0.448 | 0.277 |
| Broader subset | LSA | diag | 1 | 0.077 | 0.312 | 0.381 |
| Broader subset | PCA | spherical | 5 | 0.122 | 0.337 | 0.347 |
| Broader subset | LSA | spherical | 5 | 0.115 | 0.378 | 0.322 |

The substantive PCA/spherical fit has no below-threshold memberships, but its
mean refit TV is 0.291 and hard ARI is 0.406. Sharp memberships within one fit
therefore do not imply robust groups. Full-corpus mean TV is 0.076–0.106, versus
0.253–0.433 for the substantive subset. These compare different populations and
refitted geometries; they do not show that including procedure improves thematic
validity. Small component-support warnings remain visible for all subset fits.
The full/subset comparison and sources are in the linked report; component names
remain unreviewed.

## Validation and reproduction

```text
node tools/test_browser_gmm.cjs
node tools/compare_gmm.cjs corpus.json reviewed-mask.json gmm-output
node tools/render_gmm_comparison.cjs gmm-output/comparison.json site/gmm-audit.html
python tools/check_gmm_reference.py --node node --fits gmm-output
python tools/check_stability_reference.py gmm-output/substantive-diag.json pca
node tools/test_gmm_ui.cjs site corpus.json completed-review.json ui-output
```

The independent check uses NumPy/SciPy and scikit-learn 1.7.2. Two fixed-initialization
25-step EM fixtures match scikit-learn; all twelve actual selected fits match its
EM responsibilities within 7.75e-14 maximum absolute error. Initialization labels
are shared from the project's k-means implementation; subsequent Gaussian estimation
is independent. NumPy separately reconstructs densities, posterior vectors, entropy,
hard labels and information criteria. SciPy assignment checks all 360 soft refits;
NumPy/scikit-learn reconstruct every hard ARI/Jaccard and pair denominator.
This validates calculations, not source authenticity or diplomatic interpretation.

Browser acceptance exercises worker execution, both representations, the reviewed
subset, soft exports, original byte preservation, stale results, cancellation,
wrong-review rejection, a one-component spherical reference and mobile layout.
Existing numerical suites remain regression checks. See [validation](gmm-validation.json)
and [comparison data](gmm-comparison.json). New checks apply to the browser workflow;
the frozen R D1 pipeline, labels and release gates are unchanged.

## Recommended next steps

1. Inspect the passages with the largest membership changes and compare the saved
   covariance/component/floor alternatives before interpreting a component.
2. Audit UMAP seed and neighborhood sensitivity with the existing trustworthiness,
   continuity and neighbor-overlap diagnostics. Preserve fitted memberships across
   display changes; metric MDS can follow as a separately validated display.
3. Add independently sourced meetings and comparable material before stronger
   claims. Continue to separate source verification and component naming from
   numerical fitting; neither is inferred from convergence.

Primary references: [scikit-learn Gaussian mixtures](https://scikit-learn.org/stable/modules/mixture.html)
and [GaussianMixture API](https://scikit-learn.org/stable/modules/generated/sklearn.mixture.GaussianMixture.html).
