# W2 — Source-aware consensus clustering

**Status:** engineering-only, synthetic-first. Not a country-position, coalition, agreement-probability, or significance estimator. The 37 reserved evaluation transcripts are excluded from all W2 operations.

## Implementation

- **consensus.cjs** ingests one or more structurally and relationally checked **un.parallel-analysis.v1** fit envelopes. Inputs must match by observation ID + text SHA, source/selection hash basis, eligible population, provenance, unit, and split. No text, embeddings, browser kernels or held-out sources are imported. Mixed representation IDs require the explicit **identity_join_hard_partition_v1** descriptive protocol.
- Labels are only compared **within** a fitted model. Cluster-label permutations change nothing. Cluster 0 is noise/unassigned; a null cluster is not fitted or excluded. Neither contributes as a matched assignment. GMM responsibilities, NMF shares and HDBSCAN strengths are type-checked but never interpreted as diplomatic probabilities.
- Every pair, including diagonals, has raw and weighted **co-assigned numerators, assigned-both denominators, and planned-fit denominators**, plus noise, missing, failed-fit, and different-cluster tallies. Zero denominator produces null association, not 0.
- Planned weight is distributed **family → method → pinned configuration → source-group resample → seed**. Each method family contributes equal total planned weight. Adding k-means seeds or similar configurations cannot give its family extra weight; failed runs remain in planned denominators. Repeated declared seed/configuration/resample combinations are rejected.
- Whole-group leave-one-out and source-group bootstrap diagnostics use the **supplied refitted models**. Omitted source groups must be not_fitted. At least three assessable leave-group-out or five assessable bootstrap refits produce descriptive empirical 5th–95th percentiles; **these are not confidence intervals**.
- Deterministic **complete-link** grouping requires every within-group pair to meet conditional association, coverage, and family diversity thresholds. Same-source-only candidates are withheld from reproducible groups by default; ambiguous members and unsupported pairs remain explicit.
- Individual-method ARI is calculated conditional on shared hard assignments. Leave-one-method-family-out sensitivity is shown separately. There is no universal best-model score or statistical significance claim.

## Reproduction

Requires Node.js 22. All fixtures use fictional observation identities and no original transcript text.

~~~bash
node research/consensus/test_consensus.cjs
node docs/parallel-work/validate-contract.cjs
node research/consensus/run_synthetic.cjs /tmp/consensus-synthetic
~~~

The synthetic exporter writes these artifacts to the explicitly supplied local output directory:

| File | Content |
| --- | --- |
| consensus-v1.json | Source-identified engineering-only W2 report |
| association-matrix.csv | ID-indexed conditional co-assignment matrix; null shown blank |
| pairwise-denominators.csv | Numerators, assigned/planned denominators, model failures and noise |
| method-family-weight-audit.json | Family/method/configuration/seed and fit weights |
| grouped-uncertainty.json | Leave-group-out and bootstrap refit spreads and withheld cases |
| sensitivity-report.json | Family removals and baseline-only changes |
| unsupported-pair-ledger.csv | Pair-specific reasons for withholding support |
| standardized-interchange-v1.json | W2 export with original observations and source pointers, typed group assignments and inferential abstention |
| nuisance-only-control.json | Known meeting-dependent, no-latent-structure negative control |
| validation-receipt.json | Synthetic counts and privacy declaration |

The output structure is versioned by **consensus-v1.schema.json**, and validated with both structural and pairwise relational checks. The original coordinator **docs/parallel-work/interchange-v1.schema.json** remains the authoritative W1–W7 interchange input/export schema.

## API

~~~js
const {runConsensus, validateConsensus, toInterchangeV1} =
  require('./research/consensus/consensus.cjs');

const output = runConsensus(versionedFitEnvelopes, {
  fit_plan: {
    'model-a': {configuration_id:'k2_lsa_fixed',seed:101},
    'model-b': {
      configuration_id:'k2_lsa_fixed',seed:102,
      resample_type:'leave_group_out',resample_id:'loo-meeting-1',
      sampled_groups:['verified-meeting-2','verified-meeting-3','verified-meeting-4']
    }
  },
  min_association:0.8,
  min_coverage:0.4,
  min_families:2,
  min_source_groups:2
});
validateConsensus(output);
const adapter = toInterchangeV1(versionedFitEnvelopes[0], output);
~~~

The code sample illustrates the shape, not valid real data or a complete resampling panel. Fit-plan keys are globally unique model IDs. The **configuration_id** must encode the intended nonrandom settings and version without the seed. If not supplied, the method, representation, and parameter digest are used, but near-identical configurations cannot be detected. Internal optimizer attempts/failures remain in each incoming fit's coverage ledger.

The reported pair statistic and assignment coverage are:

\[
A_{ij} = \frac{\sum_f w_f\, I(i,j\text{ both assigned in }f)\,I(c_{if}=c_{jf})}
{\sum_f w_f\,I(i,j\text{ both assigned in }f)}, \quad
Q_{ij} = \frac{\sum_f w_f\,I(i,j\text{ both assigned in }f)}{\sum_f w_f}.
\]

A is conditional **descriptive** co-assignment; Q is assigned-both weight over planned weight. Co-assignment is null if its assigned-both denominator is zero. Weights are allocated before missing and failed outcomes, never by silently dropping failed method families.

## Limitations and coordinator dependencies

1. **Statistical limits.** Known-structure recovery and a nuisance-only meeting partition are engineering checks, not a valid reference distribution for nonrandom text clusters. Row permutations are not a cluster-significance test. A source-group bootstrap assumes the input refits were actually performed under a declared group-resampling plan; it does not establish independent source replication. Few source groups, text genre/role, source concentration, repeated actors, and parameter-search effects remain potential confounders.
2. **W1 dependency.** Production ingestion requires W1's standardized fit records, pinned model/config/representation identities, original source and selection SHA checks, source-group lineage, failure ledgers, and dependence/duplicate analysis. Country affiliation is not verified speaker identity. Source-linked private row-level outputs must remain private.
3. **Interpretation boundary.** Descriptive linguistic similarities and stable groups are not diplomatic agreement, authenticated government positions, coalitions, influence, or causal effects. No inferential null, reserved holdout, or publication gate is unlocked.
4. **Privacy boundary.** No original transcripts, embeddings, saved vectors, annotation ledgers or private review content are stored in this public module. All 37 reserved October 5–6 meeting transcripts, frozen review decisions, original source hashes, and O1–O5 gates remain untouched.
5. **Coordinator ownership exception.** The 8 October coordinator document instead reserves **research/parallel/w02-consensus/** and the branch **feat/parallel-w02-consensus**, and restricts workflows to the coordinator. This work uses the user-requested **research/consensus/** on **feat/consensus-clustering**, plus one new W2-only synthetic workflow. Coordinator must explicitly accept or relocate those paths before merging. No shared roadmap or active source file has been changed.

**Release status:** engineering-only PR; browser wiring, W1 production integration, deployment and merge are deferred to the coordinator.
