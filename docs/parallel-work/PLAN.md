# Shared development plan

## Baseline and order of operations

Reference `main` at `f8d1c239e163c5167e44d97ddb42c2c07562a3a9`. All work is **development-only / synthetic engineering** until distinct source, statistical and release acceptance exists. The existing D1 has 12 executable daily adapters; 29 separate research engineering kernels do not represent production integration. Preserve the frozen 37-meeting reserved evaluation and all published O1–O5 gates.

### Work packages

| ID | Workstream | Independent deliverable | Minimum acceptance | Direct prerequisites |
| --- | --- | --- | --- | --- |
| W1 | Source-aware statistical validation | Source/meeting-grouped nuisance-preserving nulls; explicit missing/failure denominators and selection sensitivity | Whole-meeting split; seeded negative/positive controls; no row permutations called independent; calibration limits declared | Contract v1, development-only hashes |
| W2 | Consensus clustering | Family-balanced eligible-pair co-assignment and ambiguity/noise audit, with fit ledger | Balanced family contribution, pair opportunities, zero-denominator abstention, failed-fit accounting, sensitivity to family duplication | Contract v1; W1 null contract for significance claims (not needed for descriptive prototypes) |
| W3 | Spectral clustering and diffusion maps | Independent graph construction, kernel, normalization and eigensolver adapters | Disconnected/degenerate graph fixtures, sign/rotation indeterminacy, neighborhood and parameter sensitivity; no influence claim | Contract v1; W1/W2 only for promotion/comparison |
| W4 | Longitudinal latent structure | Comparable source/actor-period panel, frozen-transform projection, correspondence and uncertainty audit | Composition/missingness ledger, source-level temporal split, stable anchors, matched/unmatched units, high-dimensional diagnostics | Contract v1, selected W1 controls; optional W2/W3 comparisons |
| W5 | Browser analytical integration | Additive standalone browser adapter and contract import/export preview; shared-entry-point patch **proposal only** | Source-hash/replay validation, bounded runtime and cancellation, no network transfer or silent refit, no new publication gate | Contract v1 and stable accepted W1–W4 outputs; actual integration is coordinator-owned |
| W6 | Research visualizations | Isolated view modules for aligned sensitivity/cluster/diffusion/time comparisons | Stable IDs, uncertainty and missingness visible; source links trace to source lineage; numerical charts not inferred from UMAP coordinates | Contract v1; accepted outputs from W1–W4; UI interface with W5 |
| W7 | Diplomat-facing UX | Isolated copy/interaction prototypes and accessible empty/abstain/error states | Plain-English caveats, source/context drilldown, accessible keyboard/mobile interactions, no automatic stance inference | Contract v1; handoff with W5/W6; final entry-point changes coordinator-only |

### Stages and decision gates

1. **C0 — Contract freeze:** coordinator merges this documentation and structural schema once checked. Changes thereafter require `1.x` backward-compatible evolution, or a separately named v2.
2. **C1 — Independent statistical work:** W1, W2, W3 and W4 work in parallel in exclusive namespaces, using cached **development** material privately or synthetic fixtures publicly. They export v1 envelopes without modifying their upstream source schemas.
3. **C2 — Evidence gate:** assess source lineage, group dependence, null design, model sensitivity, failure/non-delivery and cross-method comparability. Do not promote statistical/nonrandomness claims without a separately specified valid reference design.
4. **C3 — Presentation prototypes:** W5, W6 and W7 can prototype in parallel against the synthetic contract; integrate real approved analytics only after their upstream C2 gates pass. Workers may submit proposed integration diffs as PR notes, not changes to protected coordinator paths.
5. **C4 — Coordinator integration:** rebase or merge from fresh main without force-push, inspect changed paths, run numerical/source/browser/replay tests; make one coordinator-only entry-point PR at a time. Maintain the 600-passage browser fit envelope unless independent scalability acceptance justifies revising it.
6. **C5 — Public release and mirror:** publish only approved text-free/code/frontend assets after CI and source review; run `tools/build_pages.py`, mirror using the website repo's `scripts/sync_un_project.py`, verify live assets. Do not do this for planning docs.

### Common handoff per worker

Submit a PR with its `workstream_id`, base SHA, changed-path list, upstream schemas/versions, a synthetic-only example envelope, deterministic tests, environment/seed notes, signed-off limitations, all attempted/failed runs, and a plain-English source-privacy statement. Unfinished fits, unavailable sources, ambiguous membership and unreviewed attribution must be explicit, never silently removed.

A passing fixture is **engineering readiness only**, not a scientific release. The coordinator does not track other chats automatically; request a fresh integration review when each PR exists.
