# Development sequence — 6 October 2026

This is a proposed implementation sequence, not a record of implemented features.
The immediate priority is connecting reviewed source units to reproducible
analysis and interpretation. The existing browser already has PCA/LSA, k-means,
PAM, hierarchical clustering, HDBSCAN, NMF, Gaussian mixtures, UMAP and metric MDS,
with method-specific stability or display diagnostics.

The [audio and passage pilot](SPEECH_PILOT.md) has twelve audio concerns and twelve
boundary proposals awaiting owner decisions. Its exporter preserves original
source IDs and offsets, but `un.reviewed-speech-units.v1` is not yet an analysis
workspace input. Completing this review does not create relevance or stance labels.

## 1. Connect reviewed units and correction records

Build an explicit reviewed-unit import path, alongside the preserved full-source
corpus. Validate parent IDs, corpus and text hashes, offsets, review provenance,
overlap exclusions and unit identity. Reports must distinguish passage counts
from parent-speech and meeting counts. Keep children of the same parent/meeting
together in resampling and evaluation splits.

Add a separate correction record for confirmed audio discrepancies: original span,
proposed wording, recording/clip reference, reviewer and decision. Applying a
correction must produce a new version and an explicit alignment to the original;
it must not invalidate existing offsets or silently replace the original corpus.

Engineering can proceed with fixtures now. Real imports and corrections require
the owner's saved decisions. Acceptance means exact source round trips and
rejection of changed parents, unresolved spans and invalid review records.

## 2. Add saved-run and paired-comparison controls

Expose a compact browser comparison workflow for existing methods, with immutable
input/selection hashes, representation settings, seeds, runtime versions, outputs
and saved coordinates. Compare runs on shared source identities; do not infer
agreement from matching cluster numbers. Changing the representation refits the
clusters, while a display-only change preserves them.

Add an explicit full-parent versus reviewed-unit comparison, recording coverage
and omissions and accounting for long speeches contributing more units. Report
within-parent inspection separately from pooled statistical comparisons. The
current twelve purposive excerpts cover only three speeches and are not complete
partitions; they can validate the workflow, not establish superior clustering or
representative performance. Broader comparisons need more reviewed sources and
independent meetings under a declared selection policy.

Acceptance: replay a saved run without changing its inputs or maps; compare
matching populations with correct denominators; expose changed coverage.

## 3. Turn the existing audits into a reusable settings comparison

Make the current representation/component, cluster-count, density, covariance and
display sweeps reusable in the interface. Use the same group samples for paired
comparisons. Show cluster-size imbalance, assignment coverage, hard/soft membership
stability, source examples and representation/display fidelity together, each with
its own denominator and limitations. Do not collapse unlike diagnostics into an
automatic best-method score or select a model because its plot looks separated.

This work can proceed before the pending reviews, using the already reviewed
parent corpus and synthetic engineering fixtures. Larger claims still need more
independent source groups than the current six-meeting collection.

## 4. Extend graph-based methods in a controlled order

First port the existing audit-only D1 spectral-clustering method into the browser
comparison workflow. Define the graph from retained PCA/LSA scores, record the
neighbor and affinity policies, and disclose disconnected components and isolated
points. Cluster in the defined representation/graph, not in UMAP or MDS plot
coordinates. Add source-linked examples and the same group-based sensitivity
checks. Use an independent numerical reference and known-geometry fixtures.

Then consider diffusion maps as another representation experiment, with a fixed
kernel/normalization contract, eigenvalue diagnostics and neighborhood/bandwidth
sensitivity. This geometric method is separate from claiming that diplomatic
positions or ideas diffuse between states. Neither addition receives substantive
theme names automatically. These are proposed next browser methods, not new
implementations delivered by this planning update.

## 5. Complete the evidence-to-report workflow

Let the owner attach tentative thematic descriptions to stable groups/components
after inspecting representative passages, ambiguous cases, contrary examples and
unassigned material. Record the supporting IDs and reviewer decision. Carry
unresolved text, missing source coverage and ambiguity into the report. A cluster
label is neither a stance label nor a validated diplomatic relationship.

Validate the complete collect → review → analyze → inspect → export workflow with
realistic inputs and failure cases. Add a hosted worker only if measured workloads
exceed browser limits; the existing Pages workflow remains useful for local-in-
browser processing.

## 6. Integrate accepted methods into the daily pipeline one at a time

Browser features, research kernels and daily adapters are distinct implementation
layers. D1 still has twelve executable adapters; the separate research layer has
29 engineering kernels toward its original thirty-method backlog. A new browser
control does not increase that adapter count. Audit-only integration should verify
input contracts, reproducibility, missing-data refusal and replay compatibility
before any change to the O1–O5 publication gates. Complete relevant Shiny and
Outlook acceptance for any changes to those delivery paths.

The unresolved driftmapR/M26 dependency still needs its actual source, interface
and supported-regime evidence. It need not block the browser work above.

## Separate data-dependent branches

- **AI relevance:** TF-IDF/logistic and the selected small BERT have already been
  compared. Their next step is the [random development/fresh test round](NEXT_REVIEW_ROUND.md),
  development-only tuning and a frozen subsequent test. The audio/boundary packet
  supplies none of those relevance labels.
- **Stance:** define explicit propositions and collect stance-specific decisions,
  retaining insufficient evidence. Evaluate a simple baseline and abstention
  behavior before promoting a learned model.
- **Historical change:** assemble comparable country/genre/language observations
  across dates, preserve availability and source versions, and establish a common
  representation before interpreting movement.
- **Event or network diffusion:** define time-stamped events, exposure/risk sets
  and observation rules. Similar wording or an attractive map is not evidence of
  influence or causation.

The recommended next implementation is step 1's reviewed-unit import and correction
provenance, followed by step 2's saved-run comparison. Owner review remains a
separate required input for applying those paths to the current pilot.
