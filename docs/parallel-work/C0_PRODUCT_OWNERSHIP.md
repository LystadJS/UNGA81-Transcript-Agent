# C0 additive ownership reconciliation — 15 October 2026

**Authority:** the owner's instruction to implement C0 contracts, reconcile ownership and prepare parallel handoffs. **Scope:** source-free UI-migration engineering only. Base `691f13bb53232f72a40461855c8e08a78b21befe`; original `OWNERSHIP.md` Git blob `70a47e4c109d6fc719271527511d619569735cfa` is preserved unchanged. This scoped coordinator addendum and `c0-ownership.json` record new reservations without rewriting historical worker or scientific decisions. No merge/deployment authority is added.

## Exclusive allocations

| Lane | Branch | Exclusive implementation path | Branch/PR rule |
|---|---|---|---|
| C0 | coord/c0-product-contracts | research/integration/product_contracts/** | New coordinator draft based on inspected main |
| U1 = existing W7 | feat/parallel-w07-diplomat-ux | site/parallel/w07-diplomat-ux/** | Reuse W7 reservation, not a competing interface lane |
| U2 | feat/question-first-router | research/integration/question_router/** | New carve-out in coordinator integration area |
| M1 | feat/task-model-selection | research/model_selection/** | New research-only task policy namespace |
| V1 | coord/us-relative-phase1 | research/integration/w2_w4_w6/waggoner/** | Continue open PR82; no second producer |
| R1 | feat/evidence-first-research-readouts | research/diplomatic_readouts/** | Continue open PR70 |
| Q1 | feat/c0-product-security | research/reproducibility_audit/** | New follow-up from merged PR71; never reopen its old PR |

C0 also owns exactly the four new files `docs/parallel-work/C0_PRODUCT_OWNERSHIP.md`, `C0_WORKER_HANDOFFS.md`, `C0_IMPLEMENTATION_ACCEPTANCE_2026-10-15.md`, `c0-ownership.json`, and one new read-only `.github/workflows/c0-product-contracts.yml`. No other shared file is edited. Workers own no workflows or common docs. Their documentation, synthetic fixtures and tests stay within their prefix.

Reservations are not claims that worker branches/PRs have been created. Only C0 is implemented by this request. Before acting on a worker prompt, refresh main, the exact C0 candidate and active PRs; stop on an actual ownership collision rather than overwriting concurrent work.

## Preserved ownership and actual namespaces

Existing W1 `research/validation_framework/**`, W3 `research/graph_methods/**`, W4 `research/longitudinal/**`, W5 `site/parallel/w05-browser/**` and W6 `site/experimental/evidence-viz/**` remain their established workers' responsibility. Main's canonical W2 `research/consensus/**` and coordinator W1/W2 bridges are read-only dependencies for C0; the old W2 reservation is not a reason to create a duplicate engine. No new worker receives them.

PR66 `research/semantic_representations/**`, PR67 `research/null_calibration/**`, PR68 `research/longitudinal/temporal_calibration_v2/**` and PR69 `site/experimental/research-validation-v2/**` remain in their existing branches. M1 consumes their versioned evidence and does not own their code. PR87's independent probes in `research/integration/w2_w4_w6/pr82_review/**` and its workflow are coordinator review assets, not V1 worker files. V1 preserves those failure cases and requests a repinned independent rerun; it must not edit the independent tests to pass.

The existing PR82 change to `research/integration/w2_w4_w6/test_w4_bridge.py` remains an already-recorded coordinator change. The new V1 handoff grants no additional shared-file edits. C0's new paths do not overlap PR82 or PR87.

## Dependency strategy without merging

For new U1/U2/M1/Q1 branches, use a reviewed immutable C0 head as their starting commit and target the C0 branch in a stacked draft PR. Record the actual C0 dependency SHA. The worker's effective diff must contain only its own prefix; no copied C0 source or independent workflow. Reconcile any already-created branch before using its reserved name.

Existing PR70/82 remain on their current branches. Read C0 interfaces by exact SHA and test an isolated composed tree when needed; do not rebase, cherry-pick, merge branches, or insert copied C0 files into those worker diffs under this handoff. A coordinator can supply dependency-aware synthetic CI separately. An unavailable dependency is NOT RUN, not permission to replace a validator.

C1 remains a **future coordinator-only integration task**. Shared site entry points, global styles/loaders, build allowlists, release manifests, frozen registries, `un/**`, existing workflows and the portfolio mirror are not transferred to workers. No source/browser wiring or C1 implementation is authorized by C0's completion.

## Immutable boundaries

Keep all 37 October 5–6 reserved transcript contents unopened; original hashes, evaluation locks, completed owner decisions, W1/W2 G01–G13 and null study requirements, temporal v2 negative results and v3 holdout, and D1 O1–O5 unchanged. No new public original text, private source-linked data, vectors or credentials. Keep the declared single-reviewer operational pilot; do not invent independent human review or add routine owner work. Scientific approval requirements already imposed by a separate protocol remain separate.
